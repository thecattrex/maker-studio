"""build.py — type-2 reel, ek command me: render -> chicken -> mix -> mux -> QA.

    python3 build.py --ep 1                    # -> ../dl/type2_ep1.mp4
    python3 build.py --ep 2 --out /tmp/x.mp4

Sab numbers config.json me. Timing **video se measure** hoti hai (black gaps
detect karke), plan ke numbers pe bharosa nahi — isi wajah se audio kabhi
0.2 s shift nahi hoga.
"""
import argparse, json, os, re, subprocess, sys, tempfile, time

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.dirname(ROOT)
sys.path.insert(0, STUDIO)
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-2000:]); print(r.stderr[-2000:])
        sys.exit(f"FAILED: {' '.join(cmd[:6])} ...")
    return r


def dur(path):
    return float(probe(path)["duration"])


def luma_profile(path, cfg):
    """Per-frame mean luma of the clip area (ladder column chhod ke)."""
    W, H = cfg["frame"]["w"], cfg["frame"]["h"]
    x, y = int(W * 0.30), int(H * 0.20)
    cw, ch = W - x - int(W * 0.05), int(H * 0.60)
    r = subprocess.run([FF, "-v", "error", "-i", path, "-vf",
                        f"crop={cw}:{ch}:{x}:{y},scale=76:56", "-f", "rawvideo",
                        "-pix_fmt", "gray", "-"], capture_output=True)
    if r.returncode:
        sys.exit("luma decode fail: " + r.stderr.decode()[-500:])
    raw = r.stdout
    a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 56, 76).mean(axis=(1, 2))
    return a


def detect(path, cfg):
    """Return (clip_starts, clip_ends, gap_len). Black gap runs se."""
    a = luma_profile(path, cfg)
    fps = 30.0
    # gap = pure black frame. Threshold config se (default 15) — dark scene
    # (jaise raat/forest clip, mean ~34) ko gap na samjhe.
    dark = a < float(cfg.get("gap_luma", 15.0))
    runs, i = [], 0
    while i < len(dark):
        if dark[i]:
            j = i
            while j < len(dark) and dark[j]:
                j += 1
            if j - i >= 3:
                runs.append((i / fps, j / fps))
            i = j
        else:
            i += 1
    if len(runs) < len(cfg["clips"]) - 1:
        sys.exit(f"gap detect fail: only {len(runs)} black runs mila")
    gl = float(np.median([b - a_ for a_, b in runs])) or cfg["gap"]
    ends = [r[0] for r in runs]
    starts = [0.0] + [r[0] + gl for r in runs]
    return starts, ends, gl


def transitions(path, cfg, thresh=14.0, merge=0.12):
    """Clip boundaries output video se (frame diff peaks). Chicken ke dark
    frames se confuse nahi hota."""
    a = luma_profile(path, cfg)
    d = np.abs(np.diff(a))
    out = []
    for i in np.where(d > thresh)[0]:
        t = (i + 1) / 30.0
        if not out or t - out[-1] > merge:
            out.append(t)
    return out


def assemble(base, chicken, clip4_end, tramp_start, gap, out, cfg):
    W, H = cfg["frame"]["w"], cfg["frame"]["h"]
    fc = (
        f"[0:v]trim=start=0:end={clip4_end:.4f},setpts=PTS-STARTPTS,fps=30,format=yuv420p[a];"
        f"[1:v]trim=start=0:end={cfg['chicken']['dur']:.4f},setpts=PTS-STARTPTS,fps=30,format=yuv420p[b];"
        f"[2:v]trim=start=0:end={gap:.4f},setpts=PTS-STARTPTS,fps=30,format=yuv420p[c];"
        f"[0:v]trim=start={tramp_start:.4f},setpts=PTS-STARTPTS,fps=30,format=yuv420p[d];"
        f"[a][b][c][d]concat=n=4:v=1:a=0,format=yuv420p[v]"
    )
    return fc


def boomerang_gap(base, clip4_end, tramp_start, chicken_dur, gap, out, cfg):
    """[base 0..clip4_end] [black gap] [chicken] [black gap] [base tramp..end]"""
    W, H = cfg["frame"]["w"], cfg["frame"]["h"]
    fc = (
        f"[0:v]trim=start=0:end={clip4_end:.4f},setpts=PTS-STARTPTS,fps=30[a];"
        f"[2:v]fps=30,setsar=1[c1];"
        f"[1:v]trim=start=0:end={chicken_dur:.4f},setpts=PTS-STARTPTS,fps=30,setsar=1[b];"
        f"[3:v]fps=30,setsar=1[c2];"
        f"[0:v]trim=start={tramp_start:.4f},setpts=PTS-STARTPTS,fps=30[d];"
        f"[a][c1][b][c2][d]concat=n=5:v=1:a=0,format=yuv420p[v]"
    )
    cmd = [
        FF, "-v", "error",
        "-i", base, "-i", cfg["chicken"]["video"],
        "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={gap:.4f}",
        "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={gap:.4f}",
        "-filter_complex", fc, "-map", "[v]", "-an",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", out,
    ]
    sh(cmd)


def loudness(path):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path, "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?\d+\.\d+) LUFS", r.stderr)
    return float(m[-1]) if m else float("nan")


def qa_sheet(video, out, ts):
    from PIL import Image, ImageDraw, ImageFont
    tmp = tempfile.mkdtemp()
    ims = []
    for i, t in enumerate(ts):
        f = os.path.join(tmp, f"f{i}.jpg")
        sh([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "3", f, "-y"])
        ims.append(Image.open(f).resize((324, 576)))
    rows = (len(ims) + 3) // 4
    c = Image.new("RGB", (324 * 4 + 18 * 5, (576 + 30) * rows + 18), "#111")
    d = ImageDraw.Draw(c)
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    for i, (t, im) in enumerate(zip(ts, ims)):
        r_, cc = divmod(i, 4)
        x, y = 18 + cc * (324 + 18), 18 + r_ * (576 + 48)
        c.paste(im, (x, y)); d.text((x + 4, y + 578), f"t={t:.2f}s", font=F, fill="#9aa0aa")
    c.save(out, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", type=int, default=1)
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"),
                    help="episode config; default remains config.json")
    ap.add_argument("--source", default=os.path.join(ROOT, "assets/rc5_src.mp4"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep", action="store_true", help="intermediate files rakho")
    a = ap.parse_args()

    cfg = json.load(open(os.path.abspath(a.config)))
    out = a.out or os.path.join(os.path.dirname(ROOT), "..", "dl", f"type2_ep{a.ep}.mp4")
    out = os.path.abspath(out)
    tmp = tempfile.mkdtemp(prefix="type2_")
    t0 = time.time()

    print(f"[1/5] render base (ep{a.ep})")
    r = sh(["python3", os.path.join(STUDIO, "run.py"), "ranking",
            "--source", a.source, "--plan", a.plan,
            "--name", f"type2_ep{a.ep}_base", "--watermark", ""],
           cwd=STUDIO, env={**os.environ, "NORM": "0"})
    base = r.stdout.strip().splitlines()[-1].strip()
    print(f"      {base}  ({dur(base):.3f}s)")

    print("[2/5] timing detect (video se)")
    starts, ends, gl = detect(base, cfg)
    print(f"      gap={gl:.3f}s  starts={[round(s,3) for s in starts]}  ends={[round(e,3) for e in ends]}")

    ch_t = ends[-1] + gl                     # chicken: 4th clip ke baad
    tramp_t = ch_t + cfg["chicken"]["dur"] + gl
    vid = os.path.join(tmp, "video.mp4")
    print(f"[3/5] chicken insert @ {ch_t:.3f}  (rank-1 clip -> {tramp_t:.3f})")
    boomerang_gap(base, ends[-1], starts[-1], cfg["chicken"]["dur"], gl, vid, cfg)

    total = dur(vid)

    # timing FINAL video se — black gaps (chicken ke aas-paas wale do gap bhi)
    starts, ends, gl = detect(vid, cfg)
    n = len(cfg["clips"])
    if len(starts) < n + 1:
        sys.exit(f"gap detect fail: {len(starts)} blocks mile (chahiye {n+1})")
    c_starts = [round(s, 4) for s in starts[:n - 1]] + [round(starts[n], 4)]
    c_ends = [round(e, 4) for e in ends[:n - 1]] + [round(total, 4)]
    ch_t, ch_end = round(starts[n - 1], 4), round(ends[n - 1], 4)
    tramp_t = c_starts[-1]
    print(f"      blocks={[round(s,3) for s in starts]}  gap={gl:.3f}")
    print(f"      clip starts={c_starts}  ends={c_ends}  chicken {ch_t}-{ch_end}")

    clips = []
    for i, c in enumerate(cfg["clips"]):
        clips.append({"n": c["n"], "t": round(c_starts[i], 4), "file": c["audio_file"],
                      "ss": round(float(c["ss"]), 4), "sfx": c.get("sfx")})
    timeline = {
        "total": round(total, 4),
        "clips": clips,
        "chicken_t": round(ch_t, 4),
        # voice: pehla 0 pe + har clip-cut se 0.35 s pehle (chicken wale gap me nahi)
        "voice": [cfg["voice"]["first_at"]] + [round(e - cfg["voice"]["before_cut"], 4) for e in c_ends[:-2]],
    }
    tl_path = os.path.join(tmp, "timeline.json")
    json.dump(timeline, open(tl_path, "w"), indent=1)

    print("[4/5] mix")
    wav = os.path.join(tmp, "mix.wav")
    sh(["python3", os.path.join(ROOT, "mix.py"), tl_path, wav,
        "--config", os.path.abspath(a.config)])

    print("[5/5] mux + QA")
    tgt = cfg.get("master", {}).get("lufs")
    af_chain = []
    if tgt is not None:
        wl = loudness(wav)
        g = max(-9.0, min(9.0, tgt - wl))
        if abs(g) > 0.3:
            af_chain.append(f"volume={g:+.2f}dB")
            print(f"      loudness {wl:.1f} -> {tgt:.1f} LUFS  ({g:+.2f} dB)")
    # The mix WAV has already been peak-capped, but LUFS gain can raise peaks
    # afterwards. Re-limit at mux so true peak stays comfortably below -4 dBFS.
    af_chain.append("alimiter=limit=0.58:attack=5:release=50:level=0")
    af = ["-af", ",".join(af_chain)]
    sh([FF, "-v", "error", "-i", vid, "-i", wav, *af, "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", "-y", out])

    size = os.path.getsize(out)
    lufs = loudness(out)
    ts = [round(s + 0.55, 2) for s in c_starts] + [round(ch_t + 0.20, 2)]
    stem = os.path.splitext(os.path.basename(out))[0]
    sheet = os.path.join(os.path.dirname(out), f"{stem}_sheet.jpg")
    qa_sheet(out, sheet, ts)

    print(f"""
========== DONE  ep{a.ep} ==========
file    {out}
size    {size:,} B
dur     {total:.3f} s
lufs    {lufs:.1f}
sheet   {sheet}
clips   {[c['n'] for c in clips]}   chicken @ {ch_t:.3f}  rank1 @ {tramp_t:.3f}
voice   {timeline['voice']}
time    {time.time()-t0:.0f}s
===================================""".strip())
    if not a.keep:
        pass
    print(f"\n(tmp {tmp})")


if __name__ == "__main__":
    main()
