#!/usr/bin/env python3
"""Shot pool analysis for the Oppenheimer Style A rebuild.

For the Trinity window we measure, per frame:
  motion   = mean |frame diff| (how much is happening)
  face     = biggest frontal face box (size / 320) and its centre
Then we cut the window at scene changes and score every shot, so cuts can be
chosen by movement + face instead of "whatever slice was lying around".
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/opp/opp1080.mp4"
T0, T1 = 6470.0, 7130.0
FPS = 6
W, H = 320, 180
OUT = Path("/var/tmp/opp/analysis")


def decode() -> np.ndarray:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "win.gray"
    if not raw.exists() or raw.stat().st_size < 1000:
        subprocess.run(
            [FF, "-v", "error", "-ss", f"{T0}", "-t", f"{T1 - T0}", "-i", SRC,
             "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-y", str(raw)],
            check=True,
        )
    buf = np.fromfile(str(raw), np.uint8)
    n = buf.size // (W * H)
    return buf[: n * W * H].reshape(n, H, W)


def main() -> int:
    frames = decode()
    n = len(frames)
    print(f"decoded {n} frames @ {FPS}fps = {n / FPS:.1f}s", flush=True)

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    motion = np.zeros(n, np.float32)
    for i in range(1, n):
        motion[i] = float(np.abs(frames[i].astype(np.int16) - frames[i - 1].astype(np.int16)).mean())

    face_sz = np.zeros(n, np.float32)
    face_cx = np.full(n, -1.0, np.float32)
    for i in range(0, n, 2):
        det = cascade.detectMultiScale(frames[i], 1.15, 4, minSize=(24, 24))
        if len(det):
            x, y, w, h = max(det, key=lambda d: d[2] * d[3])
            face_sz[i] = (w * h) / (W * H)
            face_cx[i] = (x + w / 2) / W
    # fill gaps so every frame has the last known face state
    for i in range(1, n):
        if face_sz[i] == 0 and face_sz[i - 1] > 0 and i % 2:
            face_sz[i] = face_sz[i - 1]
            face_cx[i] = face_cx[i - 1]

    # scene cuts: motion spike relative to local median
    cuts = [0]
    for i in range(2, n - 1):
        local = motion[max(0, i - 8): i]
        if motion[i] > max(6.0, float(np.median(local)) * 3.2) and motion[i] > motion[i + 1]:
            if i - cuts[-1] > FPS * 0.4:
                cuts.append(i)
    cuts.append(n)

    shots = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        seg_m = motion[a + 1: b]
        seg_f = face_sz[a: b]
        if len(seg_m) < 2:
            continue
        shots.append({
            "src_t": round(T0 + a / FPS, 2),
            "dur": round((b - a) / FPS, 2),
            "motion": round(float(seg_m.mean()), 2),
            "face": round(float(np.mean(seg_f > 0)), 2),
            "face_sz": round(float(np.max(seg_f)), 3),
            "cx": round(float(np.median(face_cx[a: b][face_cx[a: b] >= 0])) if (face_cx[a: b] >= 0).any() else -1, 2),
        })

    (OUT / "shots.json").write_text(json.dumps(shots, indent=1))
    good = [s for s in shots if s["motion"] >= 1.6 and s["dur"] >= 1.0]
    good.sort(key=lambda s: -s["motion"])
    print(f"\nshots total {len(shots)} | moving shots (motion>=1.6, >=1.0s): {len(good)}")
    print(f"\n{'src_t':>8} {'dur':>5} {'motion':>7} {'face%':>6} {'faceSz':>7} {'cx':>5}")
    for s in good[:34]:
        print(f"{s['src_t']:8.2f} {s['dur']:5.2f} {s['motion']:7.2f} {s['face']:6.2f} {s['face_sz']:7.3f} {s['cx']:5.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
