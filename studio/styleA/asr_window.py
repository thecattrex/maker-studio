import sys
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

path = sys.argv[1]
windows = [(4.9, 8.4), (9.0, 12.0), (28.7, 32.2)]
m = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=1)
for t0, t1 in windows:
    sr = 44100
    seg, _ = sf.read(path, start=int(t0 * sr), frames=int((t1 - t0) * sr), dtype="float32")
    if seg.ndim > 1:
        seg = seg.mean(axis=1)
    seg = np.ascontiguousarray(seg)
    segs, _ = m.transcribe(seg, beam_size=1, language="en", vad_filter=False, condition_on_previous_text=False)
    txt = " ".join(s.text.strip() for s in segs)
    print(f"  {t0:5.2f}-{t1:5.2f}: {txt[:110]!r}")
print("OK")
