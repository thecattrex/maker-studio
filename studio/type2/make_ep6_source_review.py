#!/usr/bin/env python3
"""Create a full-length, audio-preserving review reel for EP6 shortlist sources.
No editorial trims, speed changes, captions, logos, or SFX; only format normalization
and brief silent separators so every original source can be reviewed in sequence.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from util import ensure_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "review", "ep6_source_full_review.mp4")
SRC = [
    ("#3 missed car jump", "/home/user/dl/src/tiktok/tt_6863209571322744070.mp4"),
    ("#5 porch slip", "/home/user/dl/src/tiktok/tt_7418606752553356587.mp4"),
    ("#2 lasso misfire", "/home/user/dl/src/imgur/b0wKmlw.mp4"),
    ("#4 obstacle wipeout", "/home/user/dl/src/tiktok/tt_7464233129004502318.mp4"),
    ("#1 pool collapse", "/home/user/dl/src/tiktok/tt_6702952481954991366.mp4"),
]
for label, p in SRC:
    if not os.path.isfile(p) or os.path.getsize(p) < 100_000:
        raise SystemExit(f"Missing source for {label}: {p}")
ff = ensure_ffmpeg()
args = [ff, "-hide_banner", "-nostdin", "-y"]
for _, p in SRC:
    args += ["-i", p]
filt = []
for i in range(len(SRC)):
    filt.append(f"[{i}:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,setsar=1,format=yuv420p[v{i}]")
    filt.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
concat = "".join(f"[v{i}][a{i}]" for i in range(len(SRC)))
filt.append(f"{concat}concat=n={len(SRC)}:v=1:a=1[v][a]")
args += ["-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
r = subprocess.run(args, capture_output=True, text=True)
if r.returncode:
    raise SystemExit((r.stderr or "")[-3000:])
print(OUT)
