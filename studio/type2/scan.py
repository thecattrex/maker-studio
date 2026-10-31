"""select.py — source scan: 1 s thumbnail sheet + duration. Clip chunne se PEHLE poora source dekho.

    python3 select.py source.mp4 [--step 1] [--cols 10]
"""
import argparse, math, os, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--rows", type=int, default=6)
    a = ap.parse_args()
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", a.src], capture_output=True, text=True).stdout)
    n = int(d / a.step)
    print(f"{a.src}  {d:.1f}s  -> {n} thumbs (step {a.step}s)")
    per = a.cols * a.rows
    out = os.path.splitext(a.src)[0] + "_sheet%d.jpg"
    for page in range(math.ceil(n / per)):
        ss = page * per * a.step
        cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-i", a.src,
               "-vf", f"fps=1/{a.step},scale=180:-1,tile={a.cols}x{a.rows}:padding=4:color=black",
               "-frames:v", "1", "-q:v", "3", out % page, "-y"]
        subprocess.run(cmd, check=True)
        print("  ", out % page, f"(t={ss:.0f}s .. {min(d, ss+per*a.step):.0f}s)")


if __name__ == "__main__":
    main()
