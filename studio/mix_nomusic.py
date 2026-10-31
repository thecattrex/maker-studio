import numpy as np, wave, json

SR = 48000
def rd(p):
    w = wave.open(p); sr = w.getframerate(); n = w.getnframes(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, ch) / 32768
    if ch == 1: a = np.repeat(a, 2, axis=1)
    if sr != SR:
        raise SystemExit(f"{p}: {sr} != {SR}")
    return a

base = rd('/tmp/base_nomusic.wav')          # 13.746 s stereo
voice = rd('/tmp/got48.wav')
scream = rd('/tmp/scream48.wav')[:int(0.600 * SR)]

TOTAL = 13.7667
N = int(TOTAL * SR)
out = np.zeros((N, 2), np.float32)
nb = min(len(base), N)
out[:nb] = base[:nb]

def rms(x): return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)
def db(x): return 20 * np.log10(x + 1e-12)

# ---- per-clip gain balance (clip audio hi ekmatra sound hai) ----
gains = [(0.00, 3.45, 5.0), (3.45, 6.30, 4.0), (6.30, 10.15, 0.0), (10.15, 13.17, 2.0)]
env = np.ones(N, np.float32)
ramp = int(0.03 * SR)
for (t0, t1, g) in gains:
    i0, i1 = int(t0 * SR), min(int(t1 * SR), N)
    env[i0:i1] = 10 ** (g / 20)
# smooth the envelope so no clicks
k = int(0.02 * SR)
kern = np.hanning(k); kern /= kern.sum()
env = np.convolve(env, kern, mode='same').astype(np.float32)
out *= env[:, None]

# ---- ducking mask ----
duck = np.ones(N, np.float32)
def duck_at(t0, dur, depth):
    i0 = int(t0 * SR); i1 = min(int((t0 + dur) * SR), N)
    f = int(0.06 * SR)
    seg = np.full(i1 - i0, depth, np.float32)
    f = min(f, len(seg) // 2)
    if f > 2:
        seg[:f] = np.linspace(1.0, depth, f)
        seg[-f:] = np.linspace(depth, 1.0, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)

hits = [0.00, 3.45, 6.30, 10.15]
for t in hits:
    duck_at(t, len(voice) / SR, 0.55)
SCREAM_T = round(TOTAL - 0.600, 3)
duck_at(SCREAM_T, 0.600, 0.42)

# apply duck with smooth fade (blur the mask a bit)
kb = int(0.03 * SR)
kb_o = np.hanning(kb); kb_o /= kb_o.sum()
duck = np.clip(np.convolve(duck, kb_o, mode='same'), 0.3, 1.0).astype(np.float32)
out *= duck[:, None]

# ---- normalise base peak to -6 dB before adding voices ----
out *= 10 ** ((-6.0 - db(np.max(np.abs(out)))) / 20)

# ---- voices ----
V_RMS = -13.0
voice *= 10 ** ((V_RMS - db(rms(voice))) / 20)
for t in hits:
    i0 = int(t * SR); i1 = min(i0 + len(voice), N)
    out[i0:i1] += voice[:i1 - i0]

# ---- chicken scream (last clip) ----
scream *= 10 ** ((-12.5 - db(rms(scream))) / 20)
i0 = int(SCREAM_T * SR); i1 = min(i0 + len(scream), N)
out[i0:i1] += scream[:i1 - i0]

# ---- soft limit + headroom ----
out = np.tanh(out * 1.15) / 1.15
pk = np.max(np.abs(out))
out *= 10 ** ((-5.6 - db(pk)) / 20)

out16 = np.clip(out, -1, 1)
w = wave.open('/tmp/mixed_nomusic_gotthis.wav', 'wb')
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out16 * 32767).astype(np.int16).tobytes()); w.close()

# report voice RMS at each hit in final mix (voice band region)
for t in hits:
    s = out[int(t * SR):int((t + 1.0) * SR)]
    print(f"voice@{t:5.2f} rms {db(rms(s)):6.1f}")
s = out[int(SCREAM_T * SR):int((SCREAM_T + 0.6) * SR)]
print(f"scream@{SCREAM_T:.2f} rms {db(rms(s)):6.1f}")
print("overall rms", round(db(rms(out)), 1), "peak", round(db(np.max(np.abs(out))), 1), "dur", round(N / SR, 3))
