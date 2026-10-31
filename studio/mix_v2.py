import numpy as np, wave, subprocess

SR = 48000
TOTAL = 14.3667
N = int(round(TOTAL * SR))

def rd(p):
    w = wave.open(p); sr = w.getframerate(); n = w.getnframes(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, ch) / 32768
    if ch == 1: a = np.repeat(a, 2, axis=1)
    assert sr == SR, (p, sr)
    return a

def db(x): return 20 * np.log10(x + 1e-12)
def rms(x): return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)

def sfx(key):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"/home/user/studio/trial/sfx/{key}.mp3",
                          "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768

def place(buf, sig, t, peak_db=None, rms_db=None, cut=None, fade=0.12):
    i0 = int(round(t * SR))
    seg = sig.copy()
    if cut is not None:
        lim = int(round((cut - t) * SR))
        if lim < len(seg):
            seg = seg[:lim].copy()
            f = min(int(fade * SR), len(seg))
            seg[-f:] *= np.linspace(1, 0, f)[:, None]
    if peak_db is not None:
        seg *= 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None:
        seg *= 10 ** ((rms_db - db(rms(seg))) / 20)
    i1 = min(i0 + len(seg), len(buf))
    buf[i0:i1] += seg[:i1 - i0]

base = rd('/tmp/base_nomusic.wav')          # 13.746 s
voice = rd('/tmp/got48.wav')
scream = rd('/tmp/scream48.wav')[:int(round(0.5667 * SR))]

out = np.zeros((N, 2), np.float32)
# ---- per-clip gains on the base tape ----
gmap = [(0.00, 3.45, 5.0), (3.45, 6.30, 4.0), (6.30, 10.15, 0.0), (10.15, 13.746, 4.5)]
g = np.ones(len(base), np.float32)
for t0, t1, gd in gmap:
    g[int(t0 * SR):min(int(t1 * SR), len(base))] = 10 ** (gd / 20)
k = int(0.02 * SR); h = np.hanning(k); h /= h.sum()
g = np.convolve(g, h, mode='same').astype(np.float32)
base = base * g[:, None]

SPLICE = 10.15
CH = 0.5667
i_s = int(round(SPLICE * SR))
i_e = int(round((SPLICE + CH) * SR))
out[:i_s] = base[:i_s]                                   # clip 4,3,2
# ladder clip shifted
rest = base[i_s:]
j = i_e
m = min(len(rest), N - j)
out[j:j + m] = rest[:m]

# ---- duck under "I got this" ----
duck = np.ones(N, np.float32)
for t in (0.00, 3.45, 6.30):
    i0 = int(t * SR); i1 = min(i0 + len(voice), N); f = int(0.06 * SR)
    seg = np.full(i1 - i0, 0.55, np.float32)
    f = min(f, len(seg) // 2)
    seg[:f] = np.linspace(1, 0.55, f); seg[-f:] = np.linspace(0.55, 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
kb = int(0.03 * SR); hb = np.hanning(kb); hb /= hb.sum()
duck = np.clip(np.convolve(duck, hb, mode='same'), 0.3, 1.0).astype(np.float32)
out *= duck[:, None]

# ---- normalise base peak, add voices ----
out *= 10 ** ((-6.0 - db(np.max(np.abs(out)))) / 20)
voice *= 10 ** ((-13.0 - db(rms(voice))) / 20)
for t in (0.00, 3.45, 6.30):
    place(out, voice, t)
# chicken scream alone in the insert
place(out, scream, SPLICE, rms_db=-12.0)

# ---- meme sfx (1 per clip, on the punch) ----
place(out, sfx('slap'), 2.62, peak_db=-9.0, cut=3.45)          # trampoline landing
place(out, sfx('yeet'), 4.40, peak_db=-9.5, cut=6.30)          # roof -> bag launch
place(out, sfx('fail'), 6.55, peak_db=-11.0)                   # trail crash (under voice)
place(out, sfx('ba_drum_tss'), 12.9667, peak_db=-8.5)          # board lands on him

# ---- soft limit + headroom ----
out = np.tanh(out * 1.15) / 1.15
pk = np.max(np.abs(out))
out *= 10 ** ((-4.8 - db(pk)) / 20)

w = wave.open('/tmp/mixed_v2.wav', 'wb')
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(np.clip(out, -1, 1).astype(np.float32).__mul__(32767).astype(np.int16).tobytes()); w.close()

lbl = [("voice1", 0.0, 1.0), ("voice2", 3.45, 1.0), ("voice3", 6.30, 1.0),
       ("chicken", SPLICE, CH), ("ladder", SPLICE + CH, 2.0), ("end", TOTAL - 0.6, 0.6)]
for n_, t0, d in lbl:
    s = out[int(t0 * SR):int((t0 + d) * SR)]
    print(f"{n_:8s} {t0:5.2f} rms {db(rms(s)):6.1f} peak {db(np.max(np.abs(s))):6.1f}")
print("overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1), "dur", round(N / SR, 3))
