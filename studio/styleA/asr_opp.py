#!/usr/bin/env python3
"""Transcribe fixed windows of the Oppenheimer source to locate jigsaw lines.

RAM is ~2GB here, so: whisper 'base' int8, 1 thread, 120s chunks, offsets added.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import soundfile as sf
from faster_whisper import WhisperModel

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/opp/opp1080.mp4"
OUT = Path("/var/tmp/opp/asr")
OUT.mkdir(exist_ok=True)

WINDOWS = [
    ("trinity", 7200, 8160),   # 2:00:00 - 2:16:00  post-blast / Truman
    ("speech", 8160, 8700),    # 2:16:00 - 2:25:00  aftermath
    ("early", 540, 900),       # 0:09:00 - 0:15:00  Cambridge
    ("trin2", 6480, 7220),     # 1:48:00 - 2:00:20  Trinity test + blast
    ("gym", 7600, 7790),       # 2:06:40 - 2:09:50  gym speech?
    ("early2", 620, 1120),     # 0:10:20 - 0:18:40  "hear the music"
]

CHUNK = 120.0


def main() -> int:
    model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=1)
    for tag, t0, t1 in WINDOWS:
        fout = OUT / f"{tag}.jsonl"
        if fout.exists() and fout.stat().st_size > 0:
            print(f"skip {tag}", flush=True)
            continue
        with fout.open("w") as fh:
            s = float(t0)
            while s < t1:
                dur = min(CHUNK, t1 - s)
                wav = OUT / "_chunk.wav"
                subprocess.run(
                    [FF, "-v", "error", "-ss", f"{s:.2f}", "-t", f"{dur:.2f}",
                     "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "-y", str(wav)],
                    check=True,
                )
                a, sr = sf.read(str(wav), dtype="float32")
                if len(a):
                    segs, _ = model.transcribe(
                        a, language="en", vad_filter=True, beam_size=1,
                        condition_on_previous_text=False,
                    )
                    for seg in segs:
                        fh.write(json.dumps({
                            "t0": round(s + seg.start, 2),
                            "t1": round(s + seg.end, 2),
                            "text": seg.text.strip(),
                        }) + "\n")
                        fh.flush()
                print(f"{tag} {s:.0f}/{t1}", flush=True)
                s += dur
        print(f"DONE {tag}", flush=True)
    print("ALL_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
