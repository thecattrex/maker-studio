"""Synthesized sound effects (no copyright, no downloads).

Every effect is a short stereo 44.1k wav written to studio/work/sfx/.
"""
import os
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "sfx")


def _w(path, x, sr=SR, fade=0.004):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    f = max(1, int(fade * sr))
    x = x.copy()
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    x /= (np.abs(x).max() + 1e-9)
    x *= 0.9
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


def _lowpass(x, k):
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, "same")


def _bandpass(x, lo, hi):
    # difference of two moving averages ~ crude band-pass
    return _lowpass(x, hi) - _lowpass(x, lo)


def whoosh(dur=0.55, direction="up", bright=1.0):
    n = int(SR * dur)
    noise = np.random.randn(n)
    # three fixed bands, crossfaded over time -> a real spectral sweep
    lo = _bandpass(noise, 3, int(18 * bright))
    mid = _bandpass(noise, int(14 * bright), int(60 * bright))
    hi = _bandpass(noise, int(45 * bright), int(200 * bright))
    p = np.linspace(0, 1, n)
    if direction == "up":
        wl, wm, wh = (1 - p) ** 2, 2 * p * (1 - p), p ** 2
    else:
        wl, wm, wh = p ** 2, 2 * p * (1 - p), (1 - p) ** 2
    out = lo * wl + mid * 1.6 * wm + hi * 2.2 * wh
    env = np.sin(np.pi * p) ** 2.2 if direction == "up" else (1 - p) ** 1.6
    y = out * env
    l = y * (1 - 0.15 * p)
    r = y * (0.85 + 0.15 * p)
    return np.stack([l, r], axis=1) * 0.55


def impact(dur=1.1, weight=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    boom = np.tanh(boom * (2.4 * weight))
    click = _bandpass(np.random.randn(n), 2, 26) * np.exp(-t * 60) * 0.5
    crack = _bandpass(np.random.randn(n), 30, 90) * np.exp(-t * 22) * 0.25
    y = boom + click + crack
    # short reverb tail
    ir_n = int(0.7 * SR)
    ir = np.random.randn(ir_n) * np.exp(-np.arange(ir_n) / (SR * 0.12))
    wet = np.convolve(y, ir, "same")[:n]
    wet /= (np.abs(wet).max() + 1e-9)
    y = y * 0.85 + wet * 0.22
    return np.stack([y, np.roll(y, int(0.006 * SR))], axis=1) * 0.95


def riser(dur=2.0, f0=180, f1=2400):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    noise = _bandpass(np.random.randn(n), 3, 40)
    env = (t / dur) ** 2.2
    y = (tone + noise * 0.8) * env
    return np.stack([y, y * 0.95], axis=1) * 0.5


def pop(dur=0.09, freq=880):
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (freq + 500 * np.exp(-t * 60)) * t) * np.exp(-t * 55)
    return y * 0.5


def tick(dur=0.05, freq=1800):
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = _bandpass(np.random.randn(n), 2, 10) * np.exp(-t * 120)
    y += np.sin(2 * np.pi * freq * t) * np.exp(-t * 90) * 0.4
    return y * 0.45


def ding(dur=1.2, freq=1318.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.2) +
         0.4 * np.sin(2 * np.pi * freq * 2.001 * t) * np.exp(-t * 5.0) +
         0.2 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 7.5))
    return np.stack([y, np.roll(y, int(0.005 * SR))], axis=1) * 0.45


def build_sfx():
    os.makedirs(OUT, exist_ok=True)
    lib = {
        "whoosh_up": whoosh(0.55, "up"),
        "whoosh_down": whoosh(0.45, "down"),
        "impact": impact(1.1, 1.0),
        "impact_soft": impact(0.9, 0.55),
        "riser": riser(2.0),
        "pop": pop(),
        "tick": tick(),
        "ding": ding(),
    }
    paths = {}
    for k, v in lib.items():
        paths[k] = _w(os.path.join(OUT, k + ".wav"), v)
    return paths


_CACHE = None


def get(name):
    global _CACHE
    if _CACHE is None:
        _CACHE = build_sfx()
    return _CACHE[name]


if __name__ == "__main__":
    for k, v in build_sfx().items():
        print(k, v)
