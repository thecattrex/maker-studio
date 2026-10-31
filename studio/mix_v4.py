"""mix_v4.py — same reel (got this + chicken + sfx) but background music = O5 Clave Groove.
MUSIC=0 -> music ke bina wala version (v2 ke barabar).
"""
import numpy as np, wave, subprocess, os, sys

SR = 48000
TOTAL = 14.3667
N = int(round(TOTAL * SR))
SPLICE = 10.15
CH = 0.5667
MUSIC = os.environ.get("MUSIC", "1") == "1"
OUTWAV = os.environ.get("OUTWAV", "/tmp/mixed_clave.wav")
MUSIC_RMS = float(os.environ.get("MUSIC_RMS", "-25.0"))   # bed ke neeche music ka level

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
    i0 = int(round(t * SR)); seg = sig
    if cut is not None:
        lim = int(round((cut - t) * SR))
        if lim < len(seg):
            seg = seg[:lim].copy(); f = min(int(fade * SR), len(seg))
            seg[-f:] *= np.linspace(1, 0, f)[:, None]
    if peak_db is not None: seg = seg * 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None: seg = seg * 10 ** ((rms_db - db(rms(seg))) / 20)
    i1 = min(i0 + len(seg), len(buf)); buf[i0:i1] += seg[:i1 - i0]

base = rd('/tmp/base_nomusic.wav')
voice = rd('/home/user/sfx/got_this_clean.wav')
scream = rd('/tmp/scream48.wav')[:int(round(CH * SR))]

# ---------- 1. clip bed (splice: chicken between 2nd and 1st) ----------
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

bed = clips.copy()
place(bed, scream, SPLICE, rms_db=-11.5)
place(bed, sfx('slap'),        2.62, peak_db=-8.5, cut=3.45)
place(bed, sfx('yeet'),        4.40, peak_db=-9.0, cut=6.30)
place(bed, sfx('fail'),        6.55, peak_db=-9.5, cut=9.90)
place(bed, sfx('ba_drum_tss'), 12.9667, peak_db=-8.0)

# ---------- 2. background music ----------
if MUSIC:
    mus = rd('/tmp/clave48.wav')[:N]
    if len(mus) < N:
        mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
    mus *= 10 ** ((MUSIC_RMS - db(rms(mus))) / 20)
    f = int(0.6 * SR); mus[-f:] *= np.linspace(1, 0, f)[:, None]
    bed += mus

# ---------- 3. duck whole bed under "I got this" ----------
duck = np.ones(N, np.float32); DEPTH = 0.20
for t in (0.00, 3.45, 6.30):
    i0 = int(t * SR); i1 = min(i0 + len(voice) + int(0.12 * SR), N); f = int(0.08 * SR)
    seg = np.full(i1 - i0, DEPTH, np.float32); f = min(f, len(seg) // 2)
    seg[:f] = np.linspace(1, DEPTH, f); seg[-f:] = np.linspace(DEPTH, 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
# chicken ke waqt music thoda neeche
i0, i1 = i_s, min(i_e + int(0.05 * SR), N); f = int(0.06 * SR)
seg = np.full(i1 - i0, 0.55, np.float32); f = min(f, len(seg) // 2)
seg[:f] = np.linspace(1, 0.55, f); seg[-f:] = np.linspace(0.55, 1, f)
duck[i0:i1] = np.minimum(duck[i0:i1], seg)
hb = np.hanning(int(0.03 * SR)); hb /= hb.sum()
duck = np.clip(np.convolve(duck, hb, mode='same'), 0.15, 1.0).astype(np.float32)
bed *= duck[:, None]

# ---------- 4. voice ----------
v = voice * 10 ** ((-13.5 - db(rms(voice))) / 20)
out = bed.copy()
for t in (0.00, 3.45, 6.30):
    place(out, v, t)

out = np.tanh(out * 1.1) / 1.1
pk = db(np.max(np.abs(out)))
if pk > -4.5: out *= 10 ** ((-4.5 - pk) / 20)

w = wave.open(OUTWAV, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(np.clip(out, -1, 1).__mul__(32767).astype(np.int16).tobytes()); w.close()

print("hit    voiceRMS  bedRMS   diff")
for t in (0.00, 3.45, 6.30):
    i0 = int(t * SR); i1 = min(i0 + len(voice), N)
    print(f"{t:5.2f}  {db(rms(out[i0:i1])):7.1f}  {db(rms(bed[i0:i1])):6.1f}  {db(rms(out[i0:i1]))-db(rms(bed[i0:i1])):6.1f}")
for lab, t0, d in [("chicken", SPLICE, CH), ("ladder", SPLICE + CH, 2.0), ("tail", TOTAL - 0.8, 0.8)]:
    s = out[int(t0 * SR):int((t0 + d) * SR)]
    print(f"{lab:8s} rms {db(rms(s)):6.1f} peak {db(np.max(np.abs(s))):6.1f}")
print("music" if MUSIC else "no music", "| overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1))
