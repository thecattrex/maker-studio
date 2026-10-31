"""mix_new5.py — 5-clip reel. order 3,5,2,4,1 | chicken between 4 and 1 | music C2 17%."""
import numpy as np, wave, subprocess

SR = 48000
GAP = 0.25
CH = 0.5667
TOTAL = 11.7333 + CH          # 12.300
N = int(round(TOTAL * SR))

# clip starts (from plan)
S = {3: 0.000, 5: 3.250, 2: 5.5333, 4: 7.8166}
S[1] = 10.132 + CH            # clip 1 shifted by chicken insert
CHICKEN_T = 10.132            # right after clip 4 ends

CLIP_FILE = {3: "/tmp/rc/2_surf.mp4", 5: "/tmp/rc/5_gym.mp4", 2: "/tmp/rc/1_golf.mp4",
             4: "/tmp/rc/3_tube.mp4", 1: "/tmp/rc/4_tramp.mp4"}

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

def place(buf, sig, t, peak_db=None, rms_db=None, gain_db=0.0):
    seg = sig * 10 ** (gain_db / 20)
    if peak_db is not None: seg = seg * 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None: seg = seg * 10 ** ((rms_db - db(rms(seg))) / 20)
    i0 = int(round(t * SR)); i1 = min(i0 + len(seg), len(buf))
    if i0 >= len(buf): return
    buf[i0:i1] += seg[:i1 - i0]

voice = rd('/home/user/sfx/got_this_clean.wav', pad=False)
scream = rd('/tmp/scream48.wav', pad=False)[:int(round(CH * SR))]

# ---------- clip bed ----------
bed = np.zeros((N, 2), np.float32)
for n, t in S.items():
    place(bed, clip_audio(CLIP_FILE[n]), t, gain_db=2.0)
bed = np.tanh(bed * 1.2) / 1.2
bed *= 10 ** ((-20.0 - db(rms(bed))) / 20)

# ---------- music C2 @ 17% ----------
mus = rd('/tmp/c2_48.wav')
mus *= 10 ** ((-27.4 - db(rms(mus))) / 20)   # 17% (24% -> 25% was -24 ; 17% ≈ -27.4)
f = int(0.5 * SR); mus[-f:] *= np.linspace(1, 0, f)[:, None]
bed = bed + mus

# ---------- sfx (har clip ke event pe) ----------
place(bed, sfx('yeet'),        S[3] + 1.55, peak_db=-9.0)   # surfboard se paani me
place(bed, sfx('oof'),         S[5] + 0.82, peak_db=-7.5)   # skates slip, neeche girna
place(bed, sfx('ba_drum_tss'), S[2] + 1.55, peak_db=-8.0)   # golf cart palat
place(bed, sfx('slap'),        S[4] + 0.70, peak_db=-7.0)   # tube flip, paani
place(bed, sfx('fail'),        S[1] + 0.55, peak_db=-6.0)   # trampoline chook

# ---------- chicken ----------
place(bed, scream, CHICKEN_T, rms_db=-10.5)

# ---------- duck ----------
duck = np.ones(N, np.float32); DEPTH = 0.15
for t in (S[3], S[5], S[2], S[4], S[1]):
    i0 = int(t * SR); i1 = min(i0 + len(voice) + int(0.10 * SR), N); f = int(0.08 * SR)
    seg = np.full(i1 - i0, DEPTH, np.float32); f = min(f, len(seg) // 2)
    seg[:f] = np.linspace(1, DEPTH, f); seg[-f:] = np.linspace(DEPTH, 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
i0 = int(CHICKEN_T * SR); i1 = min(i0 + int(CH * SR) + int(0.05 * SR), N); f = int(0.05 * SR)
seg = np.full(i1 - i0, 0.45, np.float32); f = min(f, len(seg) // 2)
seg[:f] = np.linspace(1, 0.45, f); seg[-f:] = np.linspace(0.45, 1, f)
duck[i0:i1] = np.minimum(duck[i0:i1], seg)
hb = np.hanning(int(0.03 * SR)); hb /= hb.sum()
duck = np.clip(np.convolve(duck, hb, mode='same'), 0.12, 1.0).astype(np.float32)
bed *= duck[:, None]

# ---------- voice ----------
v = voice * 10 ** ((-13.0 - db(rms(voice))) / 20)
out = bed.copy()
for t in (S[3], S[5], S[2], S[4], S[1]):
    place(out, v, t)

out = np.tanh(out * 1.1) / 1.1
pk = db(np.max(np.abs(out)))
if pk > -4.8: out *= 10 ** ((-4.8 - pk) / 20)

with wave.open('/tmp/mix5.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.clip(out, -1, 1).__mul__(32767).astype(np.int16).tobytes())

print("clip  voiceRMS bedRMS  diff")
for n in (3, 5, 2, 4, 1):
    t = S[n]; i0 = int(t * SR); i1 = min(i0 + len(voice), N)
    print(f"  n{n} {t:6.3f}  {db(rms(out[i0:i1])):6.1f} {db(rms(bed[i0:i1])):6.1f} {db(rms(out[i0:i1]))-db(rms(bed[i0:i1])):6.1f}")
for lab, t0 in [("yeet", S[3]+1.55), ("oof", S[5]+0.82), ("badum", S[2]+1.55),
                ("slap", S[4]+0.70), ("fail", S[1]+0.55), ("chicken", CHICKEN_T)]:
    s = out[int(t0*SR):int((t0+0.25)*SR)]
    print(f"{lab:8s} {t0:6.3f} peak {db(np.max(np.abs(s))):6.1f}")
print("overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1), "dur", round(N/SR, 3))
