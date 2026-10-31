"""mix_v5.py — C2 25% music + properly placed SFX + got this + chicken scream."""
import numpy as np, wave, subprocess, os

SR = 48000
TOTAL = 14.3667
N = int(round(TOTAL * SR))
SPLICE = 10.15
CH = 0.5667

def rd(p, pad=True):
    w = wave.open(p); sr = w.getframerate(); n = w.getnframes(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, ch) / 32768
    if ch == 1: a = np.repeat(a, 2, axis=1)
    assert sr == SR, (p, sr)
    if not pad: return a
    a = a[:N]
    if len(a) < N: a = np.pad(a, ((0, N - len(a)), (0, 0)))
    return a

def db(x): return 20 * np.log10(x + 1e-12)
def rms(x): return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)

def sfx(key):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"/home/user/studio/trial/sfx/{key}.mp3",
                          "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768

def place(buf, sig, t, peak_db=None, rms_db=None, cut=None, fade=0.10):
    i0 = int(round(t * SR)); seg = sig
    if cut is not None:
        lim = int(round((cut - t) * SR))
        if lim < len(seg):
            seg = seg[:lim].copy(); f = min(int(fade * SR), len(seg))
            seg[-f:] *= np.linspace(1, 0, f)[:, None]
    if peak_db is not None: seg = seg * 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None: seg = seg * 10 ** ((rms_db - db(rms(seg))) / 20)
    i1 = min(i0 + len(seg), len(buf)); buf[i0:i1] += seg[:i1 - i0]

base = rd('/tmp/base_nomusic.wav')            # 13.746 s clip tape
voice = rd('/home/user/sfx/got_this_clean.wav', pad=False)
scream = rd('/tmp/scream48.wav')[:int(round(CH * SR))]

# ---------- 1. clip tape + splice ----------
clips = np.zeros((N, 2), np.float32)
g = np.ones(len(base), np.float32)
for t0, t1, gd in [(0.00, 3.45, 5.0), (3.45, 6.30, 4.0), (6.30, 10.15, 0.0), (10.15, 13.746, 4.5)]:
    g[int(t0 * SR):min(int(t1 * SR), len(base))] = 10 ** (gd / 20)
k = int(0.02 * SR); h = np.hanning(k); h /= h.sum()
g = np.convolve(g, h, mode='same').astype(np.float32)
base = base * g[:, None]
i_s = int(round(SPLICE * SR)); i_e = int(round((SPLICE + CH) * SR))
clips[:i_s] = base[:i_s]
rest = base[i_s:]
m = min(len(rest), N - i_e); clips[i_e:i_e + m] = rest[:m]
clips *= 10 ** ((-22.0 - db(rms(clips))) / 20)

# ---------- 2. music: C2 @ 25% ----------
mus = rd('/tmp/c2_48.wav')
mus *= 10 ** ((-24.0 - db(rms(mus))) / 20)
f = int(0.5 * SR); mus[-f:] *= np.linspace(1, 0, f)[:, None]
bed = clips + mus

# ---------- 3. SFX ----------
place(bed, scream, SPLICE, rms_db=-10.5)                    # chicken scream in the insert
place(bed, sfx('slap'),        3.22, peak_db=-7.0, cut=3.45)   # trampoline landing
place(bed, sfx('yeet'),        4.55, peak_db=-9.0, cut=6.10)   # roof -> bag launch
place(bed, sfx('fail'),        7.12, peak_db=-8.5, cut=9.90)   # trail crash stinger (voice ke baad)
place(bed, sfx('ba_drum_tss'), 13.12, peak_db=-5.5)            # board lands on him

# ---------- 4. duck under "I got this" ----------
duck = np.ones(N, np.float32); DEPTH = 0.20
for t in (0.00, 3.45, 6.30):
    i0 = int(t * SR); i1 = min(i0 + len(voice) + int(0.12 * SR), N); f = int(0.08 * SR)
    seg = np.full(i1 - i0, DEPTH, np.float32); f = min(f, len(seg) // 2)
    seg[:f] = np.linspace(1, DEPTH, f); seg[-f:] = np.linspace(DEPTH, 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
i0, i1 = i_s, min(i_e + int(0.03 * SR), N); f = int(0.05 * SR)
seg = np.full(i1 - i0, 0.45, np.float32); f = min(f, len(seg) // 2)
seg[:f] = np.linspace(1, 0.45, f); seg[-f:] = np.linspace(0.45, 1, f)
duck[i0:i1] = np.minimum(duck[i0:i1], seg)
hb = np.hanning(int(0.03 * SR)); hb /= hb.sum()
duck = np.clip(np.convolve(duck, hb, mode='same'), 0.15, 1.0).astype(np.float32)
bed *= duck[:, None]

# ---------- 5. voice on top ----------
v = voice * 10 ** ((-13.5 - db(rms(voice))) / 20)
out = bed.copy()
for t in (0.00, 3.45, 6.30):
    place(out, v, t)

out = np.tanh(out * 1.1) / 1.1
pk = db(np.max(np.abs(out)))
if pk > -4.5: out *= 10 ** ((-4.5 - pk) / 20)

w = wave.open('/tmp/mixed_v5.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(np.clip(out, -1, 1).__mul__(32767).astype(np.int16).tobytes()); w.close()

print("hit    voiceRMS bedRMS  diff")
for t in (0.00, 3.45, 6.30):
    i0 = int(t * SR); i1 = min(i0 + len(voice), N)
    print(f"{t:5.2f}  {db(rms(out[i0:i1])):6.1f} {db(rms(bed[i0:i1])):6.1f} {db(rms(out[i0:i1]))-db(rms(bed[i0:i1])):6.1f}")
for lab, t0, d in [("sfx slap", 3.22, 0.2), ("sfx yeet", 4.55, 0.2), ("sfx fail", 7.12, 0.2),
                   ("sfx badum", 13.12, 0.2), ("chicken", SPLICE, CH), ("ladder", 10.72, 2.3), ("tail", 13.9, 0.4)]:
    s = out[int(t0 * SR):int((t0 + d) * SR)]
    print(f"{lab:9s} rms {db(rms(s)):6.1f} peak {db(np.max(np.abs(s))):6.1f}")
print("music bed (no clip) 1.2-1.5 rms", round(db(rms(out[int(1.2*SR):int(1.5*SR)])), 1))
print("overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1))
