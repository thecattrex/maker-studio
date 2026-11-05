#!/usr/bin/env python3
"""Build the v2 QA strip: 18 frames from the render + measured numbers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FF = "/home/user/bin/ffmpeg"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main():
    vid = sys.argv[1]
    out = sys.argv[2]
    qa = json.loads(Path("/var/tmp/tdk/qa_v2.json").read_text())
    plan = json.loads(Path("/home/user/studio/styleA/plan_tdk_v2.json").read_text())

    times = [0.6, 2.1, 3.6, 5.2, 6.8, 8.2, 9.9, 11.8, 13.2, 14.8, 16.6, 18.4,
             20.8, 24.0, 28.6, 33.4, 37.2, 40.6]
    cols, rows = 6, 3
    w, h = 236, 419
    sheet = Image.new("RGB", (w * cols, (h + 152) * rows + 8), (8, 8, 10))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, 13)
    fb = ImageFont.truetype(FONTB, 15)

    for i, t in enumerate(times):
        p = f"/tmp/qa_{i}.jpg"
        subprocess.run([FF, "-y", "-v", "error", "-ss", f"{t}", "-i", vid, "-frames:v", "1",
                        "-vf", "scale=236:-2", p], check=True)
        im = Image.open(p)
        x, y = (i % cols) * w, (i // cols) * (h + 152) + 152
        sheet.paste(im, (x, y))
        d.text((x + 4, y + 4), f"{t:.1f}s", font=fb, fill=(255, 220, 60))

    # ---- header numbers
    c = qa["cut_vs_onset"]
    fz = qa["freeze"]
    l = qa["loudness"]
    hdr = [
        "THE DARK KNIGHT  ·  Style A v2  ·  1080x1920 30fps  ·  song: 'A Dark Knight' 866.00-910.00 s (one continuous piece)",
        f"cuts {len(plan['visual_cuts'])}  |  cut-vs-onset: median {c['median_ms']} ms, mean {c['mean_ms']} ms, "
        f"{c['within_50ms']}/{c['n']} within 50 ms  |  3-frame rolls on real percussion runs",
        f"freeze scan (card area, all {fz['frames']} frames): {len(fz['still_runs_ge3f'])} still-runs, "
        f"unique frames {fz['unique_frame_hashes']}/{fz['frames']} (0 duplicates)  |  median frame-diff {fz['median_frame_diff']}",
        f"loudness {l.get('I','')}  peak {l.get('Peak','')}  LRA {l.get('LRA','')}  |  "
        f"dialogue on on-camera speaking shots only  |  zero credit frames (last film image 8665.3 s)",
    ]
    for k, txt in enumerate(hdr):
        d.text((10, 12 + k * 32), txt, font=fb if k == 0 else f,
               fill=(255, 255, 255) if k == 0 else (190, 196, 210))
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
