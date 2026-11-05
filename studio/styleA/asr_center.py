import sys
import subprocess
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/opp/opp1080.mp4"

t0, t1 = float(sys.argv[1]), float(sys.argv[2])
model_size = sys.argv[3] if len(sys.argv) > 3 else "base.en"
wav = "/var/tmp/opp/_cen_win.wav"
subprocess.run([FF, "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", SRC,
                "-af", "pan=mono|c0=c2", "-ar", "16000", wav], check=True)
a, sr = sf.read(wav, dtype="float32")
m = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=1)
segs, _ = m.transcribe(np.ascontiguousarray(a), beam_size=5, language="en",
                       word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
for s in segs:
    print(f"{t0 + s.start:9.2f}-{t0 + s.end:9.2f}  {s.text.strip()}")
    ws = [(round(t0 + w.start, 2), w.word) for w in (s.words or [])]
    print("     ", ws[:18])
print("OK")
