"""
airtel_spec.py — SPEC brand film "एक धागा" (one thread).

Song-first, beat-locked:
  track   : "Adventure Movie Intro" (CC, archive.org) — 129.2 BPM
  anchor  : logo hit lands exactly on the measured accent at 90.08 s
  24 beats of morphing -> 8 beats of lock-up = 32 beats = 14.86 s

Visual: studion `om_hybrid/redthread_edit.py` (parametric filament morph).
Text  : kinetic Hindi supers + English kickers + wordmark lock-up.
Audio : real track (no synth music) + sfx (whoosh/riser/impact) + 2-pass loudnorm.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/studio")
from om_hybrid.redthread_edit import (  # noqa: E402
    ThreadFilm, Beat, W, H, BRAND_RED, BRAND_RED_DEEP, WHITE, ease,
    shape_swoosh,
)
from om_hybrid.printrev_edit import FrameWriter, mux_audio  # noqa: E402

FONT_DIR = "/home/user/assets/fonts"
F_DEV = os.path.join(FONT_DIR, "NotoSansDevanagari-Black.ttf")
F_DEV_MED = os.path.join(FONT_DIR, "NotoSansDevanagari-Black.ttf")
F_LAT = os.path.join(FONT_DIR, "Poppins-ExtraBold.ttf")
F_LAT_MED = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
F_COND = os.path.join(FONT_DIR, "BarlowCondensed-ExtraBold.ttf")

# ------------------------------------------------------------------ timing
BPM = 129.2
BEAT = 60.0 / BPM
N_BEATS = 32
DUR = N_BEATS * BEAT                 # 14.861 s
ANCHOR = 90.08                       # measured accent in the track
SRC_START = ANCHOR - 24 * BEAT       # 78.934 s  (logo hit on beat 24)
AUDIO_SRC = "/var/tmp/kr/au2/Adventure_Movie_Intro.mp3"
WORK = "/var/tmp/airtel"
OUT = "/home/user/studio/samples/airtel_SPEC_EkDhaaga_BrandFilm_9x16.mp4"
os.makedirs(WORK, exist_ok=True)

# ------------------------------------------------------------------ beats
BEATS = [
    Beat(0, 1.5, "spark", width=18, glow=0.9),                     # a point
    Beat(1.5, 6, "wave", width=21, glow=1.0,
         kicker="ONE THREAD", caption="एक धागा"),
    Beat(6, 10, "highway", width=23, glow=1.0,
         kicker="EVERY ROAD", caption="हर रास्ता"),
    Beat(10, 14, "rosette", width=18, glow=1.1, dots=True,
         kicker="EVERY HOME", caption="हर घर"),
    Beat(14, 18, "network", width=20, glow=1.1, dots=True,
         kicker="BILLIONS OF US", caption="करोड़ों जुड़े"),
    Beat(18, 21, "smile", width=25, glow=1.2,
         kicker="ONE SMILE", caption="एक मुस्कान"),
    Beat(21, 32, "swoosh", width=26, glow=1.35),                   # logo
]
LOGO_BEAT = 24


# ------------------------------------------------------------------ text
def tracked(draw, xy, text, font, fill, tracking=6.0, anchor_center=None):
    """Letter-spaced latin text (Devanagari me use nahi karna)."""
    x, y = xy
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if anchor_center is not None:
        x = anchor_center - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def text_layer(frame: Image.Image, t: float, beat: Beat, k: float):
    """Caption + kicker, then the wordmark lock-up after the logo hit."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    b0, b1 = beat.b0 * BEAT, beat.b1 * BEAT
    local = (t - b0) / max(1e-6, b1 - b0)
    # fade in (0..0.22) / out (0.82..1)
    a = min(1.0, max(0.0, local / 0.22)) * min(1.0, max(0.0, (1 - local) / 0.16))
    if beat.shape == "swoosh":
        a = 1.0 if t < LOGO_BEAT * BEAT else 0.0
    a = float(ease(a, "out"))
    if a > 0.01 and beat.caption:
        rise = int(34 * (1 - a))
        f_dev = ImageFont.truetype(F_DEV, 118)
        bb = d.textbbox((0, 0), beat.caption, font=f_dev)
        d.text((W / 2 - (bb[2] - bb[0]) / 2, 1330 + rise), beat.caption,
               font=f_dev, fill=WHITE + (int(255 * a),))
        if beat.kicker:
            f_k = ImageFont.truetype(F_LAT_MED, 27)
            tracked(d, (0, 1268 + rise), beat.kicker, f_k,
                    BRAND_RED + (int(240 * a),), tracking=7.5, anchor_center=W / 2)
            # hairline rule
            lw = 54
            d.line([W / 2 - lw, 1306 + rise, W / 2 + lw, 1306 + rise],
                   fill=(230, 210, 205, int(150 * a)), width=2)

    # ---- lock-up (beats 24 -> 32) -------------------------------------
    if beat.shape == "swoosh" and t >= LOGO_BEAT * BEAT - 1e-6:
        lt = (t - LOGO_BEAT * BEAT) / max(1e-6, (32 - LOGO_BEAT) * BEAT)
        # impact hit exactly on the downbeat
        flash = max(0.0, 1.0 - lt * 10.0)
        if flash > 0.01:
            d.rectangle([0, 0, W, H], fill=(255, 226, 218, int(52 * flash)))
        # wordmark rises out of the swoosh
        ap = float(ease(min(1.0, max(0.0, (lt - 0.05) / 0.30)), "outback"))
        f_wm = ImageFont.truetype(F_LAT, 176)
        wm = "airtel"
        bb = d.textbbox((0, 0), wm, font=f_wm)
        wx = W / 2 - (bb[2] - bb[0]) / 2
        wy = 918 + int(46 * (1 - ap))
        a_wm = int(255 * min(1.0, ap))
        # soft shadow so it sits over the glow
        d.text((wx + 2, wy + 4), wm, font=f_wm, fill=(0, 0, 0, int(a_wm * 0.5)))
        d.text((wx, wy), wm, font=f_wm, fill=(252, 250, 248, a_wm))
        # tagline
        ap2 = float(ease(min(1.0, max(0.0, (lt - 0.22) / 0.30)), "out"))
        if ap2 > 0.01:
            f_t = ImageFont.truetype(F_DEV_MED, 74)
            tag = "बहुत आगे है"
            bb2 = d.textbbox((0, 0), tag, font=f_t)
            d.text((W / 2 - (bb2[2] - bb2[0]) / 2, 1224), tag, font=f_t,
                   fill=(236, 232, 228, int(235 * ap2)))
            f_s = ImageFont.truetype(F_LAT_MED, 24)
            tracked(d, (0, 1338), "SPEC  FILM", f_s, (150, 145, 142, int(160 * ap2)),
                    tracking=9, anchor_center=W / 2)

    # ---- frame furniture: chapter counter + bottom progress hairline ----
    prog = min(1.0, t / DUR)
    d.rectangle([0, H - 6, int(W * prog), H], fill=BRAND_RED + (210,))
    d.rectangle([0, H - 6, W, H], outline=(60, 40, 40, 90), width=1)
    if t < LOGO_BEAT * BEAT:
        idx = min(6, 1 + sum(1 for b in BEATS if t >= b.b1 * BEAT))
        f_c = ImageFont.truetype(F_COND, 26)
        d.text((W - 74, 96), f"{idx:02d}", font=f_c, fill=(228, 224, 220, 150))
        d.text((W - 74, 126), "/06", font=f_c, fill=(150, 146, 142, 120))

    frame.alpha_composite(lay)


# ------------------------------------------------------------------ audio
def build_audio() -> str:
    import wave
    sr = 48000
    from om_hybrid._ffmpeg import get_ffmpeg
    ff = get_ffmpeg()

    bed = os.path.join(WORK, "bed.wav")
    subprocess_cut = [ff, "-hide_banner", "-loglevel", "error", "-y",
                      "-ss", f"{SRC_START:.3f}", "-t", f"{DUR:.3f}",
                      "-i", AUDIO_SRC, "-ac", "2", "-ar", str(sr),
                      "-af", "afade=t=in:st=0:d=0.05", bed]
    import subprocess
    subprocess.run(subprocess_cut, check=True)

    # --- sfx bank (studio/sfx.py) --------------------------------------
    sys.path.insert(0, "/home/user/studio")
    import sfx as S

    def rd_wav(p):
        w = wave.open(p)
        n, ch = w.getnframes(), w.getnchannels()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        if ch == 2:
            a = a.reshape(-1, 2)
        else:
            a = np.stack([a, a], 1)
        return a, w.getframerate()

    bank = {
        "whoosh_up": S.whoosh(0.62, "up"),
        "riser": S.riser(1.90, 150, 2800),
        "impact": S.impact(1.5, 1.0),
        "tick": None,
    }
    mix = rd_wav(bed)[0]
    tgt_sr = sr

    def place(sig, at_sec, gain_db):
        if sig is None:
            return
        if sig.ndim == 1:
            sig = np.stack([sig, sig], 1)
        g = 10 ** (gain_db / 20.0)
        i0 = int(at_sec * tgt_sr)
        seg = sig * g
        if i0 < 0:
            seg = seg[-i0:]
            i0 = 0
        n = min(len(seg), len(mix) - i0)
        if n > 0:
            mix[i0:i0 + n] += seg[:n]

    # whoosh on every morph, riser into the logo hit, impact on it
    for b in (4, 8, 12, 16, 20):
        place(bank["whoosh_up"], b * BEAT - 0.30, -11.0)
    place(bank["riser"], 24 * BEAT - 1.75, -15.0)
    place(bank["impact"], 24 * BEAT, -7.0)
    # node ticks
    for b in (12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5):
        place(S.tick(0.05, 2100), b * BEAT, -26.0)

    peak = np.abs(mix).max()
    if peak > 0.98:
        mix = mix * (0.98 / peak)
    out = os.path.join(WORK, "mix.wav")
    w = wave.open(out, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(tgt_sr)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()
    return out


# ------------------------------------------------------------------ main
def main(preview_frames=None):
    film = ThreadFilm(BEATS, BEAT, DUR, fps=30, workdir=WORK)
    vid = os.path.join(WORK, "video.mp4")
    writer = None
    if not preview_frames:
        writer = FrameWriter(vid, fps=30, crf=17, preset="medium")
    film.render(writer=writer, preview_frames=preview_frames, text_layer=text_layer)
    if preview_frames:
        return None
    writer.close()
    print("video ok", vid, flush=True)
    mix = build_audio()
    print("audio ok", mix, flush=True)
    mux_audio(vid, mix, OUT, target_i=-14.0, target_tp=-1.5)
    print("FINAL", OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB")
    return OUT


if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == "preview":
        fr = [int(x) for x in _s.argv[2].split(",")]
        main(preview_frames=set(fr))
    else:
        main()
