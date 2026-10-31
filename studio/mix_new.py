"""mix_new.py — naya type-2 reel: clip audio + C2 25% + got this + chicken + clip-fitted sfx."""
import numpy as np, wave, subprocess, os

SR = 48000
TOTAL = 9.8
N = int(round(TOTAL * SR))

# clip layout (chicken inserted between clip 2 and clip 1)
GAP = 0.25
CH = 0.5667
S_GOLF, S_SURF, S_TUBE = 0.0, 2.3163, 5.5663
S_TRAMP = 8.4157
CHICKEN_T = 7.599            # 2nd clip khatam -> chicken -> 1st clip

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

def clip_audio(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "2", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768

def sfx(key):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"/home/user/studio/trial/sfx/{key}.mp3",
                          "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768

def place(buf, sig, t, peak_db=None, rms_db=None, gain_db=0.0, fade=0.10):
    seg = sig * 10 ** (gain_db / 20)
    if peak_db is not None: seg = seg * 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None: seg = seg * 10 ** ((rms_db - db(rms(seg))) / 20)
    i0 = int(round(t * SR)); i1 = min(i0 + len(seg), len(buf))
    buf[i0:i1] += seg[:i1 - i0]

voice = rd('/home/user/sfx/got_this_clean.wav', pad=False)
scream = rd('/tmp/scream48.wav', pad=False)[:int(round(CH * SR))]

# ---------- clip bed ----------
bed = np.zeros((N, 2), np.float32)
for p, t in [("/tmp/rc/1_golf.mp4", S_GOLF), ("/tmp/rc/2_surf.mp4", S_SURF),
             ("/tmp/rc/3_tube.mp4", S_TUBE), ("/tmp/rc/4_tramp.mp4", S_TRAMP)]:
    a = clip_audio(p)
    place(bed, a, t, gain_db=2.0)
bed = np.tanh(bed * 1.2) / 1.2
clips_lvl = rms(bed)
bed *= 10 ** ((-20.0 - db(clips_lvl)) / 20)

# ---------- music (C2 @ 25%) ----------
mus = rd('/tmp/c2_48.wav')
mus *= 10 ** ((-25.5 - db(rms(mus))) / 20)
f = int(0.5 * SR); mus[-f:] *= np.linspace(1, 0, f)[:, None]
bed = bed + mus

# ---------- sfx (clip ke hisaab se) ----------
place(bed, sfx('oof'),        S_GOLF + 1.15, peak_db=-8.0)   # golf cart palat gaya
place(bed, sfx('yeet'),       S_SURF + 1.70, peak_db=-9.0)   # surfboard se gir gaya
place(bed, sfx('slap'),       S_TUBE + 1.10, peak_db=-7.5)   # tube se paani me
place(bed, sfx('ba_drum_tss'), S_TRAMP + 1.15, peak_db=-5.5)  # trampoline se neeche

# ---------- chicken scream (insert) ----------
place(bed, scream, CHICKEN_T, rms_db=-10.5)

# ---------- duck under voice / chicken ----------
duck = np.ones(N, np.float32); DEPTH = 0.15
for t in (S_GOLF, S_SURF, S_TUBE):
    i0 = int(t * SR); i1 = min(i0 + len(voice) + int(0.10 * SR), N); f = int(0.08 * SR)
    seg = np.full(i1 - i0, DEPTH, np.float32); f = min(f, len(seg) // 2)
    seg[:f] = np.linspace(1, DEPTH, f); seg[-f:] = np.linspace(DEPTH, 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
i0 = int(CHICKEN_T * SR); i1 = min(i0 + int(CH * SR) + int(0.05 * SR), N); f = int(0.05 * SR)
seg = np.full(i1 - i0, 0.45, np.float32); f = min(f, len(seg) // 2)
seg[:f] = np.linspace(1, 0.45, f); seg[-f:] = np.linspace(0.45, 1, f)
duck[i0:i1] = np.minimum(duck[i0:i1], seg)
hb = np.hanning(int(0.03 * SR)); hb /= hb.sum()
duck = np.clip(np.convolve(duck, hb, mode='same'), 0.15, 1.0).astype(np.float32)
bed *= duck[:, None]

# ---------- voice ----------
v = voice * 10 ** ((-13.0 - db(rms(voice))) / 20)
out = bed.copy()
for t in (S_GOLF, S_SURF, S_TUBE):
    place(out, v, t)

out = np.tanh(out * 1.1) / 1.1
pk = db(np.max(np.abs(out)))
if pk > -4.8: out *= 10 ** ((-4.8 - pk) / 20)

w = wave.open('/tmp/new_mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(np.clip(out, -1, 1).__mul__(32767).astype(np.int16).tobytes()); w.close()

print("hit      voiceRMS  bedRMS  diff")
for t in (S_GOLF, S_SURF, S_TUBE):
    i0 = int(t * SR); i1 = min(i0 + len(voice), N)
    print(f"{t:5.2f}   {db(rms(out[i0:i1])):6.1f} {db(rms(bed[i0:i1])):7.1f} {db(rms(out[i0:i1]))-db(rms(bed[i0:i1])):6.1f}")
for lab, t0, d in [("oof", S_GOLF+1.15, .2), ("yeet", S_SURF+1.70, .2), ("slap", S_TUBE+1.10, .2),
                   ("badum", S_TRAMP+1.15, .2), ("chicken", CHICKEN_T, CH), ("tramp", S_TRAMP, 1.5)]:
    s = out[int(t0*SR):int((t0+d)*SR)]
    print(f"{lab:8s} {t0:5.2f} rms {db(rms(s)):6.1f} peak {db(np.max(np.abs(s))):6.1f}")
print("overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1), "dur", round(N/SR, 3))
