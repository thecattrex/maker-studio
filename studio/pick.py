#!/usr/bin/env python3
"""
pick.py — clip SELECTION by measurement, not by vibes.

Why this exists: the first Top-5 build failed because clips were picked by
"looks like something happens". Measured against 6 reference shorts, the
property that actually separates a usable fail clip from filler is:

  the human is IN FRAME and LARGE, and the event lands inside the clip.

Rules (thresholds measured from 17 reference clips, see GENRE_*.md):

  PASS  : person found in >= 60% of sampled frames
          AND best person height >= 0.22 of frame height
          AND peak motion sits between 15% and 92% of the clip
          AND 2.5s <= duration <= 9s
  WEAK  : person seen but small (< 0.22) or coverage < 60%
  REJECT: no person at all, or event already over at t=0, or too short/long

CLI
  python3 pick.py scan FILE [FILE...]            # score every segment
  python3 pick.py scan FILE --sheet out.jpg      # + visual sheet of winners
  python3 pick.py rank FILE [FILE...] --n 5      # best n across files
"""
import argparse, json, os, subprocess, sys
import numpy as np
import cv2

FF, FP = "/usr/bin/ffmpeg", "/usr/bin/ffprobe"
HOG = cv2.HOGDescriptor()
HOG.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


def _dur(p):
    return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)


def cuts(p, thr=0.30, min_gap=0.45):
    d = _dur(p)
    r = subprocess.run([FF, "-hide_banner", "-i", p, "-vf",
                        f"select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    import re
    ts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    ts = [t for t in ts if 0.2 < t < d - 0.2]
    m = []
    for t in ts:
        if m and t - m[-1] < min_gap: continue
        m.append(t)
    return [0.0] + m + [d]


def _frames(p, ss, dur, fps=6, w=640):
    tmp = "/tmp/_pick.mp4"
    subprocess.run([FF, "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", p, "-an",
                    "-vf", f"fps={fps},scale={w}:-2", "-c:v", "libx264", "-preset", "ultrafast",
                    "-crf", "26", "-y", tmp], capture_output=True)
    out = []
    r = subprocess.run([FF, "-v", "error", "-i", tmp, "-f", "rawvideo",
                        "-pix_fmt", "bgr24", "-"], capture_output=True)
    cap = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", tmp],
                         capture_output=True, text=True).stdout.strip().split(",")
    if len(cap) != 2: return []
    ww, hh = int(cap[0]), int(cap[1])
    a = np.frombuffer(r.stdout, np.uint8)
    n = a.size // (ww * hh * 3)
    for i in range(n):
        out.append(a[i * ww * hh * 3:(i + 1) * ww * hh * 3].reshape(hh, ww, 3))
    return out


def score(p, ss, dur, fps=6):
    """Return the numbers that decide whether this segment is usable."""
    fr = _frames(p, ss, dur, fps)
    if len(fr) < 4: return None
    # --- person presence / size (HOG) ---
    hs, hits = [], 0
    for img in fr:
        rects, weights = HOG.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.06)
        best = 0.0
        for (x, y, w, h), wt in zip(rects, weights):
            if wt > 0.3: best = max(best, h / img.shape[0])
        hs.append(best)
        if best > 0: hits += 1
    cover = hits / len(fr)
    # --- motion / impact position (global-motion compensated) ---
    g = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr], np.float32)
    win = cv2.createHanningWindow((g.shape[2], g.shape[1]), cv2.CV_32F)
    mo = []
    for i in range(len(g) - 1):
        (dx, dy), _ = cv2.phaseCorrelate(g[i], g[i + 1], win)
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        a2 = cv2.warpAffine(g[i], M, (g.shape[2], g.shape[1]), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE)
        mo.append(float(np.abs(g[i + 1] - a2).mean()))
    mo = np.array(mo)
    pk = int(mo.argmax())
    impact = pk / max(1, len(mo) - 1)
    salience = float(mo.max() / (np.median(mo) + 1e-4))

    r = {"file": p, "ss": round(ss, 2), "dur": round(dur, 2),
         "person_cover": round(cover, 2), "person_h": round(max(hs), 2),
         "person_h_mean": round(float(np.mean(hs)), 2),
         "impact_pos": round(impact, 2), "salience": round(salience, 2)}
    # --- verdict ---
    why = []
    if r["person_h"] == 0: why.append("no human detected")
    elif r["person_h"] < 0.22: why.append(f"subject too small ({r['person_h']:.2f})")
    if r["person_cover"] < 0.60: why.append(f"person in only {r['person_cover']*100:.0f}% frames")
    if dur < 2.5: why.append("too short")
    if dur > 9.0: why.append("too long")
    if impact > 0.92: why.append("event already over at start")
    if impact < 0.15 and dur > 4: why.append("no event in clip")
    r["verdict"] = "PASS" if not why else ("WEAK" if len(why) == 1 else "REJECT")
    r["why"] = why
    # rank score: big subject + clear event + good length
    r["score"] = round(min(r["person_h"], 0.8) * 3 + r["person_cover"] * 2
                       + min(r["salience"], 4) * 0.4 + (1 if 3 <= dur <= 7 else 0), 2)
    return r


def scan(path, min_len=2.5, max_len=9.0):
    b = cuts(path)
    out = []
    for i in range(len(b) - 1):
        ss, d = b[i], b[i + 1] - b[i]
        if not (min_len <= d <= max_len): continue
        s = score(path, ss, d)
        if s: out.append(s)
    return out


def sheet(items, out, cols=6, tw=180, th=320):
    from PIL import Image, ImageDraw, ImageFont
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    rows = max(1, (len(items) + cols - 1) // cols)
    c = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 26) + 6), (14, 14, 14))
    dr = ImageDraw.Draw(c)
    for i, it in enumerate(items):
        r, cc = divmod(i, cols)
        x, y = 6 + cc * (tw + 6), 6 + r * (th + 26)
        t = it["ss"] + it["dur"] * 0.55
        q = f"/tmp/_sh{i}.jpg"
        subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", it["file"], "-frames:v", "1",
                        "-vf", f"scale={tw}:{th}", "-y", q], capture_output=True)
        if os.path.exists(q):
            c.paste(Image.open(q).convert("RGB"), (x, y))
        col = (0, 255, 120) if it["verdict"] == "PASS" else ((255, 200, 0) if it["verdict"] == "WEAK" else (255, 80, 80))
        dr.text((x + 2, y + th + 2), f"{it['verdict']} {it['score']:.1f}", font=fs, fill=col)
        dr.text((x + 2, y + th + 13), f"h={it['person_h']:.2f} cov={it['person_cover']:.2f}", font=fs, fill=(190, 190, 190))
    c.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("files", nargs="+"); s.add_argument("--sheet")
    r = sub.add_parser("rank"); r.add_argument("files", nargs="+"); r.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    if a.cmd == "scan":
        allr = []
        for f in a.files:
            res = scan(f)
            allr += res
            for x in res:
                print(f"  {x['verdict']:6s} score={x['score']:4.1f} ss={x['ss']:6.2f} dur={x['dur']:4.1f} "
                      f"person_h={x['person_h']:.2f} cover={x['person_cover']:.2f} "
                      f"impact={x['impact_pos']:.2f} {'; '.join(x['why'])}  [{os.path.basename(f)}]")
        if a.sheet and allr:
            p = sheet([x for x in allr if x["verdict"] == "PASS"] or allr, a.sheet)
            print("sheet:", p)
        print(json.dumps(allr))
    else:
        allr = []
        for f in a.files: allr += scan(f)
        allr.sort(key=lambda x: (-x["score"]))
        top = [x for x in allr if x["verdict"] == "PASS"][:a.n]
        print(json.dumps(top, indent=1))


if __name__ == "__main__":
    main()
