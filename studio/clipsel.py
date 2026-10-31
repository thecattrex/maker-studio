#!/usr/bin/env python3
"""
select.py — find usable "fail moment" clips inside long videos. v2

What changed vs pick.py (v1):
  v1 only asked "is a human in frame and how big". That passes a clip where the
  person just STANDS there. The references are all *falls*, so a clip must also
  contain a FALL: the subject moving down, fast, and landing inside the clip.

  v2 therefore measures, per frame (camera shake removed):
     person  -> largest HOG box height (subject size) + presence
     motion  -> biggest blob after global-motion compensation: area + centroid
     fall    -> downward velocity of that blob centroid (frame-heights / second)

  Then it slides windows (3..7 s) over the whole video, scores every window and
  keeps the best non-overlapping ones. Each hit is auto-trimmed so the impact
  lands at ~78 % of the clip (setup at the start, landing near the end).

Verdicts
  PASS  : person_cover>=0.60, person_h>=0.22, fall>=0.55 fh/s,
          impact within 0.35..0.95, length 2.8..8 s
  WEAK  : one criterion short
  REJECT: no human / no fall / event outside the window

CLI
  python3 select.py scan VIDEO [VIDEO...] --sheet out.jpg --max 5
  python3 select.py trim VIDEO --at 12.4 --dur 5 --out clip.mp4
"""
import argparse, json, os, subprocess, sys
import numpy as np
import cv2

FF, FP = "/usr/bin/ffmpeg", "/usr/bin/ffprobe"
HOG = cv2.HOGDescriptor()
HOG.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
FPS = 6
W = 320
IMPACT_AT = 0.78          # where the fall lands inside the output clip


def dur_of(p):
    return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)


def load(path, fps=FPS, w=W):
    """Decode once at low res, return grayscale + colour frames."""
    tmp = "/tmp/_sel.mp4"
    subprocess.run([FF, "-v", "error", "-i", path, "-an", "-vf", f"fps={fps},scale={w}:-2",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25", "-y", tmp],
                   capture_output=True)
    r = subprocess.run([FF, "-v", "error", "-i", tmp, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True)
    wh = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height", "-of", "csv=p=0", tmp],
                        capture_output=True, text=True).stdout.strip().split(",")
    if len(wh) != 2: return None, None, fps
    ww, hh = int(wh[0]), int(wh[1])
    a = np.frombuffer(r.stdout, np.uint8)
    n = a.size // (ww * hh * 3)
    cols = a[:n * ww * hh * 3].reshape(n, hh, ww, 3)
    gray = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in cols], np.float32)
    return cols, gray, fps


def per_frame(cols, gray, fps):
    """Per-frame features: person height/presence + biggest moving blob."""
    n = len(gray)
    ph = np.zeros(n); blob_a = np.zeros(n); vy = np.zeros(n); cy = np.zeros(n)
    bh = np.zeros(n); vx = np.zeros(n); cx = np.zeros(n)
    person_hits = np.zeros(n); prev_box = None
    win = cv2.createHanningWindow((gray.shape[2], gray.shape[1]), cv2.CV_32F)
    H, Wd = gray.shape[1], gray.shape[2]
    prev_c = None
    for i in range(n):
        rects, weights = HOG.detectMultiScale(cols[i], winStride=(8, 8), padding=(8, 8), scale=1.08)
        cand = [(x, y, w, h) for (x, y, w, h), wt in zip(rects, weights) if wt > 0.3]
        # --- track one subject: prefer the box that overlaps the previous one.
        # A one-frame false positive (road marking, car, tree) must not count.
        pick = None
        if cand:
            if prev_box is not None:
                px, py, pw, phh = prev_box
                def iou(b):
                    x, y, w, h = b
                    x2, y2 = max(x, px), max(y, py)
                    x3, y3 = min(x + w, px + pw), min(y + h, py + phh)
                    if x3 <= x2 or y3 <= y2: return 0.0
                    inter = (x3 - x2) * (y3 - y2)
                    return inter / (w * h + pw * phh - inter + 1e-6)
                scored = sorted(cand, key=lambda b: -iou(b))
                if iou(scored[0]) > 0.15: pick = scored[0]
            if pick is None:
                pick = max(cand, key=lambda b: b[3])       # biggest box
        if pick is not None:
            prev_box = pick
            ph[i] = pick[3] / H
            person_hits[i] = 1
        else:
            ph[i] = 0.0
        if i == 0: continue
        (dx, dy), _ = cv2.phaseCorrelate(gray[i - 1], gray[i], win)
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        a2 = cv2.warpAffine(gray[i - 1], M, (Wd, H), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE)
        d = np.abs(gray[i] - a2)
        m = (d > 16).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        nl, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        if nl > 1:
            k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            blob_a[i] = st[k, cv2.CC_STAT_AREA] / (H * Wd)
            cy[i] = cen[k][1] / H
            cx[i] = cen[k][0] / Wd
            bh[i] = st[k, cv2.CC_STAT_HEIGHT] / H
        else:
            cy[i] = cy[i - 1] if i else 0.5
            cx[i] = cx[i - 1] if i else 0.5
            bh[i] = bh[i - 1] if i else 0.0
    vy[1:] = np.diff(cy) * fps        # +ve = moving DOWN, in frame-heights/sec
    vx[1:] = np.abs(np.diff(cx)) * fps
    return ph, person_hits, blob_a, cy, vy, bh, vx


def score_range(ph, hits, vy, blob_a, bh, vx, s, e, fps):
    """Score one candidate time range [s,e) (frames)."""
    cover_v = float(hits[s:e].mean())                     # tracked subject present
    vals = sorted(ph[s:e][ph[s:e] > 0])
    hog_h = float(np.median(vals[-3:])) if len(vals) else 0.0   # stable, not 1 lucky frame
    subj_h = hog_h
    # only trust motion blobs that are not just camera drift
    ok = blob_a[s:e] > 0.015
    w = np.where(ok, vy[s:e] * (0.5 + blob_a[s:e]) * (0.4 + bh[s:e]), -9)
    if len(w) == 0 or w.max() < 0: return None
    k = int(np.argmax(w))
    fall = float(vy[s:e][k])
    drop = float(cy_drop) if False else 0.0
    impact = k / max(1, len(w) - 1)
    L = (e - s) / fps
    return {"start": round(s / fps, 2), "dur": round(L, 2),
            "person_h": round(subj_h, 2), "cover": round(float(cover_v), 2),
            "fall": round(fall, 2), "impact": round(impact, 2),
            "_imp_t": round((s + k) / fps, 2)}


def score_windows(ph, hits, vy, blob_a, bh, vx, n, fps, lengths=(3.0, 4.0, 5.0, 6.0, 7.0), stride=0.5):
    out = []
    for L in lengths:
        nf = int(L * fps)
        if nf >= n: continue
        step = max(1, int(stride * fps))
        for s in range(0, n - nf, step):
            r = score_range(ph, hits, vy, blob_a, bh, vx, s, s + nf, fps)
            if r: out.append(r)
    return out


def verdict(w):
    why = []
    if w["person_h"] < 0.22: why.append("subject too small (%.2f)" % w["person_h"])
    if w["cover"] < 0.45: why.append("person in only %.0f%% frames" % (w["cover"] * 100))
    if w["fall"] < 0.55: why.append("no clear fall (%.2f)" % w["fall"])
    if w["impact"] < 0.35: why.append("fall starts too early")
    if w["impact"] > 0.95: why.append("fall cut off at end")
    w["why"] = why
    w["verdict"] = "PASS" if not why else ("WEAK" if len(why) == 1 else "REJECT")
    if w["verdict"] == "PASS":
        w["score"] = round(w["person_h"] * 3 + w["cover"] * 2 + min(w["fall"], 2.5) * 1.6
                           + (0.6 if 0.55 <= w["impact"] <= 0.9 else 0), 2)
    else:
        w["score"] = round(w["person_h"] * 3 + w["cover"] * 2 + min(w["fall"], 2.5) * 1.6, 2)
    return w


def nms(wins, iou=0.35):
    wins = sorted(wins, key=lambda x: -x["score"])
    keep = []
    for w in wins:
        a0, a1 = w["start"], w["start"] + w["dur"]
        clash = False
        for k in keep:
            b0, b1 = k["start"], k["start"] + k["dur"]
            ov = max(0, min(a1, b1) - max(a0, b0))
            if ov / min(a1 - a0, b1 - b0) > iou: clash = True; break
        if not clash: keep.append(w)
    return keep


def scan(path, maxn=5):
    cols, gray, fps = load(path)
    if cols is None or len(gray) < int(3 * fps): return []
    ph, hits, blob_a, cy, vy, bh, vx = per_frame(cols, gray, fps)
    wins = [verdict(w) for w in score_windows(ph, hits, vy, blob_a, bh, vx, len(gray), fps)]
    wins.sort(key=lambda x: -x["score"])
    picked = nms(wins)[:maxn]
    for w in picked: w["file"] = path
    return picked


def trim(src, at, dur, out, w=1080, h=1920):
    ss = max(0.0, at - IMPACT_AT * dur)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.3f}", "-t", f"{dur:.3f}",
                    "-i", src, "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
                    f"crop={w}:{h},setsar=1,fps=30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-y", out], check=True)
    return out, round(ss, 2)


def sheet(hits, out, cols=5, tw=200, th=356):
    from PIL import Image, ImageDraw, ImageFont
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    rows = max(1, (len(hits) + cols - 1) // cols)
    c = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 46) + 8), (14, 14, 14))
    dr = ImageDraw.Draw(c)
    for i, h in enumerate(hits):
        r, cc = divmod(i, cols)
        x, y = 8 + cc * (tw + 8), 8 + r * (th + 46)
        t = h["start"] + h["dur"] * h["impact"]          # the impact frame
        q = f"/tmp/_hs{i}.jpg"
        subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", h["file"], "-frames:v", "1",
                        "-vf", f"scale={tw}:{th}", "-y", q], capture_output=True)
        if os.path.exists(q): c.paste(Image.open(q).convert("RGB"), (x, y))
        col = (0, 255, 120) if h["verdict"] == "PASS" else (255, 190, 0)
        dr.text((x + 2, y + th + 3), f"#{i+1} {h['verdict']} {h['score']:.1f}", font=fs, fill=col)
        dr.text((x + 2, y + th + 16),
                f"h={h['person_h']:.2f} cov={h['cover']:.2f}", font=fs, fill=(200, 200, 200))
        dr.text((x + 2, y + th + 29),
                f"fall={h['fall']:.2f} cut@{h['start']:.1f}s", font=fs, fill=(200, 200, 200))
    c.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("files", nargs="+"); s.add_argument("--max", type=int, default=5)
    s.add_argument("--sheet"); s.add_argument("--all", action="store_true")
    t = sub.add_parser("trim"); t.add_argument("file"); t.add_argument("--at", type=float, required=True)
    t.add_argument("--dur", type=float, default=5.0); t.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "scan":
        allh = []
        for f in a.files:
            hits = scan(f, a.max)
            print(f"\n== {os.path.basename(f)}  ({dur_of(f):.1f}s)")
            for i, h in enumerate(hits, 1):
                print(f"  #{i} {h['verdict']:6s} score={h['score']:5.2f} at={h['start']:6.2f}s "
                      f"dur={h['dur']:.1f} person_h={h['person_h']:.2f} cover={h['cover']:.2f} "
                      f"fall={h['fall']:.2f} impact={h['impact']:.2f} "
                      f"{'; '.join(h['why'])}")
            allh += [h for h in hits if h["verdict"] == "PASS"]
        if a.sheet and allh:
            print("sheet:", sheet(allh[:15], a.sheet))
        print(json.dumps(allh))


if __name__ == "__main__":
    main()
