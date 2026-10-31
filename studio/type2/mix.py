"""mix.py — type-2 audio mixer.

Timeline JSON se chalta hai (build.py banata hai), saare levels config.json se.

    python3 mix.py timeline.json out.wav

timeline.json:
  { "total": 12.53, "clips": [{"n":3,"t":0.0,"file":"assets/2_surf.mp4","sfx":{...}}, ...],
    "chicken_t": 10.183, "voice": [0.0, 2.65, 4.95, 7.283] }
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))
from util import ensure_ffmpeg

FF = ensure_ffmpeg()


def p(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def rd(path, sr, n, ch=2, pad=True):
    w = wave.open(path)
    assert w.getframerate() == sr, (path, w.getframerate())
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    a = a.reshape(-1, w.getnchannels()) / 32768
    if a.shape[1] == 1 and ch == 2:
        a = np.repeat(a, 2, axis=1)
    if not pad:
        return a
    a = a[:n]
    if len(a) < n:
        a = np.pad(a, ((0, n - len(a)), (0, 0)))
    return a


def dec(path, sr):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768


def db(x):
    return 20 * np.log10(x + 1e-12)


def rms(x):
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)


def place(buf, sig, t, peak_db=None, rms_db=None, gain_db=0.0, fade_out=0.0):
    seg = sig * 10 ** (gain_db / 20)
    if peak_db is not None:
        seg = seg * 10 ** ((peak_db - db(np.max(np.abs(seg)))) / 20)
    elif rms_db is not None:
        seg = seg * 10 ** ((rms_db - db(rms(seg))) / 20)
    i0 = int(round(t * buf_sr))
    if 0 <= i0 < len(buf):
        available = len(buf) - i0
        if len(seg) > available:
            seg = seg[:available].copy()
            f = min(int(round(fade_out * buf_sr)), len(seg))
            if f:
                seg[-f:] *= np.linspace(1.0, 0.0, f, endpoint=True)[:, None]
        i1 = i0 + len(seg)
        buf[i0:i1] += seg


def main():
    global buf_sr
    ap = argparse.ArgumentParser(description="Type-2 audio mixer")
    ap.add_argument("timeline")
    ap.add_argument("out")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    args = ap.parse_args()
    tl = json.load(open(args.timeline))
    out_path = args.out
    cfg = json.load(open(os.path.abspath(args.config)))

    SR = cfg["audio"]["sr"]; buf_sr = SR
    N = int(round(tl["total"] * SR))

    # ---------- clip bed ----------
    bed = np.zeros((N, 2), np.float32)
    for c in tl["clips"]:
        a = dec(p(c["file"]), SR)
        k = int(round(float(c.get("ss", 0.0)) * SR))      # clip ka apna start
        place(bed, a[k:], c["t"], gain_db=cfg["bed"]["clip_gain_db"])
    bed = np.tanh(bed * cfg["bed"]["tanh"]) / cfg["bed"]["tanh"]
    bed *= 10 ** ((cfg["bed"]["rms_db"] - db(rms(bed))) / 20)

    # ---------- music ----------
    m = cfg["music"]
    mus = rd(p(m["file"]), SR, N)
    mus *= 10 ** ((m["rms_db"] - db(rms(mus))) / 20)
    f = int(m["fade_out"] * SR)
    if f:
        mus[-f:] *= np.linspace(1, 0, f)[:, None]
    bed = bed + mus

    # ---------- sfx ----------
    for c in tl["clips"]:
        s = c.get("sfx")
        if not s:
            continue
        path = os.path.join(cfg["sfx_dir"], s["key"] + ".mp3")
        if not os.path.exists(path):
            print(f"  ! sfx missing: {s['key']}")
            continue
        place(bed, dec(path, SR), c["t"] + s["at"], peak_db=s["peak_db"], fade_out=0.08)

    # ---------- chicken scream ----------
    ch = cfg["chicken"]
    scream = rd(p(ch["scream"]), SR, N, pad=False)[:int(round(ch["dur"] * SR))]
    place(bed, scream, tl["chicken_t"], rms_db=ch["rms_db"])

    # ---------- duck ----------
    duck = np.ones(N, np.float32)
    DEPTH = cfg["voice"]["duck"]; FADE = cfg["audio"]["duck_fade"]; TAIL = cfg["audio"]["duck_tail"]
    vlen = len(rd(p(cfg["voice"]["file"]), SR, N, pad=False))
    for t in tl["voice"]:
        i0 = int(t * SR); i1 = min(i0 + vlen + int(TAIL * SR), N)
        seg = np.full(i1 - i0, DEPTH, np.float32); f = min(int(FADE * SR), len(seg) // 2)
        seg[:f] = np.linspace(1, DEPTH, f); seg[-f:] = np.linspace(DEPTH, 1, f)
        duck[i0:i1] = np.minimum(duck[i0:i1], seg)
    i0 = int(tl["chicken_t"] * SR); i1 = min(i0 + int(ch["dur"] * SR) + int(0.05 * SR), N)
    seg = np.full(i1 - i0, ch["duck"], np.float32); f = min(int(0.05 * SR), len(seg) // 2)
    seg[:f] = np.linspace(1, ch["duck"], f); seg[-f:] = np.linspace(ch["duck"], 1, f)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
    hb = np.hanning(int(0.03 * SR)); hb /= hb.sum()
    duck = np.clip(np.convolve(duck, hb, mode="same"), 0.12, 1.0).astype(np.float32)
    bed *= duck[:, None]

    # ---------- voice ----------
    voice = rd(p(cfg["voice"]["file"]), SR, N, pad=False)
    v = voice * 10 ** ((cfg["voice"]["rms_db"] - db(rms(voice))) / 20)
    out = bed.copy()
    for t in tl["voice"]:
        place(out, v, t)

    out = np.tanh(out * cfg["master"]["tanh"]) / cfg["master"]["tanh"]
    pk = db(np.max(np.abs(out)))
    if pk > cfg["master"]["peak_cap"]:
        out *= 10 ** ((cfg["master"]["peak_cap"] - pk) / 20)

    with wave.open(out_path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(out, -1, 1).__mul__(32767).astype(np.int16).tobytes())

    print(f"  mix -> {out_path}  {N/SR:.3f}s  rms {db(rms(out)):.1f} dB  peak {db(np.max(np.abs(out))):.1f} dB")
    for t in tl["voice"]:
        i0 = int(t * SR); i1 = min(i0 + vlen, N)
        print(f"    voice @{t:6.3f}  diff {db(rms(out[i0:i1])) - db(rms(bed[i0:i1])):5.1f} dB")


if __name__ == "__main__":
    main()
