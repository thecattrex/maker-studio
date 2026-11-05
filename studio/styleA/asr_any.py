import sys
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

m = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=1)


def run(path, t0=None, t1=None):
    sr = 44100
    if t0 is None:
        a, sr = sf.read(path, dtype="float32")
    else:
        a, sr = sf.read(path, start=int(t0 * sr), frames=int((t1 - t0) * sr), dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    segs, _ = m.transcribe(np.ascontiguousarray(a), beam_size=1, language="en",
                           vad_filter=False, condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segs)


for arg in sys.argv[1:]:
    p = arg.split("@")[0]
    if "@" in arg:
        t0, t1 = [float(x) for x in arg.split("@")[1].split(":")]
        print(f"{p} {t0}-{t1}: {run(p, t0, t1)!r}")
    else:
        print(f"{p}: {run(p)!r}")
print("OK")
