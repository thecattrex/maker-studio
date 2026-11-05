#!/usr/bin/env python3
"""Which dialogue lines have the speaker on camera with a moving mouth?

For a list of candidate lines we decode just that slice at 10 fps, find the
biggest frontal face, and measure motion inside its lower third (the mouth
band). High mouth-motion + decent face size = the line is delivered on camera.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/opp/opp1080.mp4"
OUT = Path("/var/tmp/opp/analysis")

# candidate lines pulled from the ASR pass (region B trinity + region C)
CANDIDATES = [
    ("theory", 1035.12, 1037.12),
    ("three_years", 6596.22, 6603.30),
    ("both_finished", 6603.30, 6607.30),
    ("remote_zero", 6648.74, 6654.24),
    ("theory_alone", 6654.24, 6656.74),
    ("zero_nice", 6656.74, 6661.19),
    ("hard_on_your_heart", 6866.70, 6893.30),
    ("thirty_seconds", 6893.30, 6900.50),
    ("proud_of_you", 7445.89, 7448.89),
    ("gamble_won", 7469.15, 7480.15),
]


def analyse(t0: float, t1: float) -> dict:
    dur = max(0.4, t1 - t0)
    w, h = 480, 270
    raw = subprocess.run(
        [FF, "-v", "error", "-ss", f"{t0}", "-t", f"{dur}", "-i", SRC,
         "-vf", f"fps=10,scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
        capture_output=True,
    ).stdout
    n = len(raw) // (w * h)
    if n < 4:
        return {"face": 0.0, "mouth": 0.0, "sz": 0.0}
    fr = np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w)
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    boxes = []
    for i in range(n):
        det = cas.detectMultiScale(fr[i], 1.15, 4, minSize=(40, 40))
        boxes.append(max(det, key=lambda d: d[2] * d[3]) if len(det) else None)

    hits = [b for b in boxes if b is not None]
    face = len(hits) / n
    sz = max([b[2] * b[3] / (w * h) for b in hits]) if hits else 0.0

    # mouth band = lower 45% of the biggest face box, tracked frame to frame
    mot = []
    ref = None
    for i in range(n):
        b = boxes[i]
        if b is None:
            ref = None
            continue
        x, y, bw, bh = b
        y0 = y + int(bh * 0.55)
        y1 = y + bh
        roi = fr[i][max(0, y0): y1, x: x + bw].astype(np.int16)
        if ref is not None and ref.shape == roi.shape:
            mot.append(float(np.abs(roi - ref).mean()))
        ref = roi
    return {"face": round(face, 2), "mouth": round(float(np.mean(mot)) if mot else 0.0, 2), "sz": round(sz, 3)}


def main() -> int:
    res = {}
    print(f"{'line':20s} {'t0':>8} {'dur':>5} {'face%':>6} {'mouth':>6} {'size':>6}  verdict")
    for name, t0, t1 in CANDIDATES:
        r = analyse(t0, t1)
        ok = r["face"] > 0.55 and r["mouth"] > 1.6 and r["sz"] > 0.02
        res[name] = {**r, "t0": t0, "t1": t1, "on_camera": ok}
        print(f"{name:20s} {t0:8.2f} {t1 - t0:5.2f} {r['face']:6.2f} {r['mouth']:6.2f} {r['sz']:6.3f}  "
              f"{'OK' if ok else 'reject'}")
    (OUT / "dialogue_scan.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
