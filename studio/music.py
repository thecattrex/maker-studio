"""Music: beat detection for cutting + an offline beat generator (no copyright issues)."""
import os
import wave

import numpy as np

SR = 44100


# ------------------------------------------------------------------ analysis
def load_mono(path, sr=22050):
    from util import FFMPEG, run
    tmp = "/tmp/_beats.wav"
    run([FFMPEG, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
         "-c:a", "pcm_s16le", tmp, "-y"], check=True)
    with wave.open(tmp) as w:
        y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return y.astype(np.float32) / 32768.0, sr


def detect_beats(path, bpm_range=(78, 165)):
    """Return {bpm, beat_interval, beats[], onsets[], duration}."""
    y, sr = load_mono(path)
    hop, win = 512, 1024
    n = max(1, 1 + (len(y) - win) // hop)
    frames = np.lib.stride_tricks.sliding_window_view(y, win)[::hop][:n]
    spec = np.abs(np.fft.rfft(frames * np.hanning(win), axis=1))
    flux = np.maximum(0, np.diff(spec, axis=1)).sum(axis=1)
    flux = flux - np.convolve(flux, np.ones(31) / 31, mode="same")
    flux = np.maximum(flux, 0)

    env_fps = sr / hop
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lo = int(60 * env_fps / bpm_range[1])
    hi = int(60 * env_fps / bpm_range[0])
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60 * env_fps / lag
    # fold into range
    while bpm < bpm_range[0]:
        bpm *= 2
    while bpm > bpm_range[1]:
        bpm /= 2
    beat = 60.0 / bpm

    # refine phase: pick offset maximising flux on the grid
    best_off, best_val = 0.0, -1
    grid_len = int(beat * env_fps)
    for off in range(max(1, grid_len)):
        idx = np.arange(off, len(flux), max(1, grid_len))
        v = float(flux[idx].mean()) if len(idx) else 0
        if v > best_val:
            best_val, best_off = v, off
    phase = best_off / env_fps

    dur = len(y) / sr
    beats = list(np.arange(phase, dur, beat))
    # onset list (peaks of flux)
    th = flux.mean() + 1.5 * flux.std()
    peaks = [i for i in range(2, len(flux) - 1)
             if flux[i] > th and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    thr = flux.mean() + 0.9 * flux.std()
    while len(peaks) > 400:
        thr *= 1.15
        peaks = [p for p in peaks if flux[p] > thr]
    onsets = [round(float(p / env_fps), 3) for p in peaks]
    return {"bpm": round(float(bpm), 1), "beat_interval": round(beat, 3),
            "phase": round(phase, 3), "duration": round(dur, 2),
            "beats": [round(float(b), 3) for b in beats], "onsets": onsets}


# ------------------------------------------------------------------ synthesis
def _env(n, a=0.002, d=0.12, curve=8.0):
    t = np.arange(n) / SR
    e = np.exp(-t / max(d, 1e-4) * curve / 8.0)
    atk = np.minimum(1.0, t / max(a, 1e-5))
    return e * atk


def kick(dur=0.5, f0=115, f1=46, punch=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * _env(n, 0.001, dur * 0.55, 12)
    click = np.random.randn(n) * _env(n, 0.0005, 0.006, 20) * 0.25
    return np.tanh((y + click) * (1.5 * punch)) * 0.9


def snare(dur=0.22, tone=190):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = np.random.randn(n)
    # crude band-pass around 2-6 kHz
    k = np.ones(9) / 9
    noise = np.convolve(noise, k, "same") - np.convolve(noise, np.ones(61) / 61, "same")
    body = np.sin(2 * np.pi * tone * t) * _env(n, 0.001, 0.05, 10) * 0.5
    return (noise * _env(n, 0.0008, 0.13, 11) * 0.8 + body) * 0.8


def clap(dur=0.2):
    n = int(SR * dur)
    out = np.zeros(n)
    for i, off in enumerate([0, 0.008, 0.016, 0.03]):
        s = int(off * SR)
        seg = np.random.randn(n - s) * _env(n - s, 0.0005, 0.03 + i * 0.01, 14)
        out[s:] += seg * (0.9 - i * 0.15)
    return np.convolve(out, np.ones(7) / 7, "same") * 0.55


def hat(dur=0.06, open_=False):
    n = int(SR * (dur * 4 if open_ else dur))
    noise = np.random.randn(n)
    hp = noise - np.convolve(noise, np.ones(23) / 23, "same")
    return hp * _env(n, 0.0003, dur * (2.6 if open_ else 1.0), 16) * 0.35


def sub_bass(freq, dur, glide=None):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq if glide is None else freq + (glide - freq) * np.exp(-t * 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(np.sin(ph) * 1.3) * _env(n, 0.004, dur * 0.8, 5) * 0.55


def pluck(freq, dur=0.35):
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t) +
         0.25 * np.sin(2 * np.pi * freq * 3 * t))
    return y * _env(n, 0.002, 0.12, 8) * 0.22


def pad(freqs, dur, cutoff_mix=0.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for i, f in enumerate(freqs):
        det = 1 + (i - len(freqs) / 2) * 0.0015
        y += np.sin(2 * np.pi * f * det * t) + 0.35 * np.sin(2 * np.pi * f * 2 * det * t)
    k = int(80 * cutoff_mix) * 2 + 3
    y = np.convolve(y, np.ones(k) / k, "same")
    e = np.minimum(1, np.arange(n) / (0.25 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.4 * SR))
    return y * e / (len(freqs) * 1.6) * 0.5


def _add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    end = min(len(buf), i + len(sig))
    buf[i:end] += sig[:end - i]


def _reverb(x, mix=0.18, decay=0.45):
    ir_n = int(SR * 1.1)
    ir = np.random.randn(ir_n) * np.exp(-np.arange(ir_n) / (SR * decay * 0.35))
    ir = np.convolve(ir, np.ones(9) / 9, "same")
    wet = np.convolve(x, ir, "same")[:len(x)]
    wet /= (np.abs(wet).max() + 1e-6)
    return (1 - mix) * x + mix * wet


def make_track(kind="hype", bpm=140, bars=None, seed=7,
               filename="/tmp/music.wav", min_seconds=26.0):
    """Generate an original beat. kinds: hype | chill | phonk."""
    rng = np.random.RandomState(seed)
    if bars is None:
        bars = max(8, int(np.ceil(min_seconds / (60.0 / bpm * 4))) + 1)
    beat = 60.0 / bpm
    bar = beat * 4
    total = bar * bars + 1.0
    n = int(SR * total)
    drums = np.zeros(n)
    bassb = np.zeros(n)
    mel = np.zeros(n)

    if kind == "phonk":
        bpm = 150; beat = 60 / bpm; bar = beat * 4
        prog = [55.0, 55.0, 65.4, 49.0]
        hats_step = 0.25
    elif kind == "chill":
        prog = [261.6, 220.0, 174.6, 196.0]
        hats_step = 0.5
    else:
        prog = [55.0, 55.0, 73.4, 65.4]
        hats_step = 0.25

    scale = [0, 3, 5, 7, 10, 12, 15]  # minor pentatonic-ish

    for b in range(bars):
        t0 = b * bar
        root = prog[b % len(prog)]
        # kick
        for k in ([0, 1.5, 2.5] if kind != "chill" else [0, 2]):
            _add(drums, kick(punch=1.15 if kind != "chill" else 0.9), t0 + k * beat)
        # snare / clap on 2 & 4
        for k in [1, 3]:
            if kind != "chill" or b % 2 == 1:
                _add(drums, snare() if kind != "chill" else clap(), t0 + k * beat)
        # hats
        step = 0
        while step * hats_step * beat < bar - 1e-6:
            v = 0.75 + rng.rand() * 0.35
            _add(drums, hat(open_=(abs(step % 4) == 2)) * v, t0 + step * hats_step * beat)
            step += 1
        # bass
        if kind == "chill":
            _add(bassb, sub_bass(root / 2, bar * 0.9, root / 2), t0)
        else:
            for k in [0, 1.5, 2.5]:
                _add(bassb, sub_bass(root, beat * 1.2), t0 + k * beat)
        # melody
        if kind != "phonk":
            for k in range(4):
                if rng.rand() < 0.55:
                    note = root * 4 * (2 ** (rng.choice(scale) / 12))
                    _add(mel, pluck(note), t0 + k * beat + (beat * 0.5 if k % 2 else 0))
        else:
            _add(mel, pad([root * 4, root * 6], bar * 0.95), t0)

    if kind == "chill":
        _add(mel, pad([prog[0] * 2, prog[0] * 3, prog[1] * 2], total * 0.9), 0.0)

    mix = drums * 1.0 + bassb * 0.85 + mel * (0.9 if kind != "hype" else 0.55)
    mix = _reverb(mix, 0.12 if kind != "chill" else 0.3)
    # soft limiter
    mix = np.tanh(mix * 1.25)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.92
    # edge fades
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)
    mix[-f:] *= np.linspace(1, 0, f)

    stereo = np.stack([mix, np.roll(mix, int(0.004 * SR))], axis=1)
    _write_wav(filename, stereo)
    return {"path": filename, "bpm": bpm, "beat_interval": round(60 / bpm, 3),
            "duration": round(len(mix) / SR, 2), "kind": kind}


def _write_wav(path, stereo):
    data = np.clip(stereo, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    for k in ("hype", "phonk", "chill"):
        print(make_track(k, filename=f"/tmp/music_{k}.wav"))
