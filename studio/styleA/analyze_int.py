#!/usr/bin/env python3
"""Shot pool analyser for Interstellar (motion-ranked, scene-cut aware)."""
from __future__ import annotations

import json
import subprocess
import sys

import numpy as np

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/int/int1080.mkv"
W, H = 320, 136
FPS = 4
REGIONS = [
    (60, 210), (900, 1100), (1180, 1300),
    (2100, 2350), (2400, 2460),
    (2850, 3060), (3300, 3520),
    (4000, 4300), (4900, 5100),
    (7500, 7800), (7900, 8300), (8600, 8800),
]


def frames(t0: float, t1: float):
    raw = subprocess.run(
        [FF, "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", SRC,
         "-vf", f"fps={FPS},crop=1920:816:0:132,scale={W}:{H},format=gray",
         "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (W * H)
    return np.frombuffer(raw[: n * W * H], np.uint8).reshape(n, H, W).astype(np.float32)


def main() -> int:
    shots = []
    for t0, t1 in REGIONS:
        fr = frames(t0, t1)
        if len(fr) < 8:
            continue
        d = np.array([float(np.abs(fr[i] - fr[i - 1]).mean()) for i in range(1, len(fr))])
        ts = t0 + np.arange(1, len(fr)) / FPS
        cuts = [0] + [i for i in range(1, len(d)) if d[i] > max(6.0, np.percentile(d, 99) * 0.8)] + [len(d)]
        cuts = sorted(set(cuts))
        for a, b in zip(cuts[:-1], cuts[1:]):
            if b - a < int(0.7 * FPS):
                continue
            seg = d[a:b]
            shots.append({
                "region": [t0, t1],
                "t0": round(float(ts[a]), 2),
                "dur": round(float((b - a) / FPS), 2),
                "motion": round(float(np.mean(seg)), 2),
                "p90": round(float(np.percentile(seg, 90)), 2),
            })
    shots.sort(key=lambda s: -s["motion"])
    json.dump(shots, open("/var/tmp/int/shots.json", "w"), indent=1)
    print(f"{len(shots)} shots")
    for s in shots[:45]:
        print(f"  t{s['t0']:8.2f} d{s['dur']:5.2f} motion {s['motion']:6.2f} p90 {s['p90']:6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
