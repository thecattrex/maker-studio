"""
krishna_printrev.py — builds the Krishna devotional reel in the
"Printed Page / Sketchbook Reveal" format of the F0E2B6A9 sample.

Song-first: the bhajan (Nand Ghar Anand Bhayo) is cut on its measured beat grid
(129.2 BPM, cut at 15.87s where the groove section starts) and every visual beat
is expressed in BEATS, never in seconds.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

sys.path.insert(0, "/home/user/studio")
from om_hybrid.printrev_edit import (  # noqa: E402
    rough_text_mask,
    W, H, FPS, CARD_W, CARD_H, CARD_Y, RED, RED_DARK,
    F_DEV, F_BARLOW_XB, F_BARLOW_B, F_ANTON, F_ARCHIVO, F_BEBAS,
    PrintRevealEdit, CardSpec, FrameWriter, mux_audio,
    stamp_hud, title_slam, giant_word, sticker_inset, cursor_arrow,
    light_leak, frame_flicker, grain_flick, place_card, vignette_and_close,
)

# ---------------------------------------------------------------- song grid
BPM = 129.2
BEAT = 60.0 / BPM                 # 0.46439 s
SOURCE_START = 15.87              # measured groove start in nandghar.mp3
N_BEATS = 33
DUR = N_BEATS * BEAT              # 15.325 s
# ---------------------------------------------------------------- assets
AUDIO_SRC = "/var/tmp/kr/au/nandghar.mp3"
PLATE_HERO = "/home/user/assets/krishna/hero_ink.png"
PLATE_FLUTE = "/home/user/assets/krishna/flute_ink.png"
OUT_DIR = "/home/user/studio/samples"

WORK = "/var/tmp/kr/build"
os.makedirs(WORK, exist_ok=True)

HANDLE = "@bhakti.print"


def b(x: float) -> float:
    """beats -> seconds"""
    return x * BEAT


def _eo(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


# ---------------------------------------------------------------- plate prep
def load_plate(path, boost=1.0, contrast=1.25):
    im = Image.open(path).convert("L")
    a = np.array(im, dtype=np.float32) / 255.0
    a = np.clip((a - 0.06) * 1.10, 0, 1) ** (1.0 / max(contrast, 1e-3))
    a = np.clip(a * boost, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8)).convert("RGB")


# ---------------------------------------------------------------- renderer
class Scene:
    """One row of the beat sheet."""

    __slots__ = ("b0", "b1", "card", "title", "sticker", "cursor", "leak",
                 "grain", "zoom", "zoom_to", "flash", "card_scale", "shake",
                 "paper_flash", "slide", "pulse", "caption")

    def __init__(self, b0, b1, card="hero", title=None, sticker=None,
                 cursor=None, leak=0.0, grain=0.0, zoom=1.0, zoom_to=None,
                 flash=0.0, card_scale=1.0, shake=0, paper_flash=0.0,
                 slide=0.0, pulse=0.0, caption=None):
        self.b0, self.b1 = b0, b1
        self.card = card
        self.title = title          # (kind, colour)
        self.sticker = sticker      # (x0,y0,w,h,'red'|'grey')
        self.cursor = cursor        # (x,y,click_at_progress)
        self.leak = leak
        self.grain = grain
        self.zoom = zoom
        self.zoom_to = zoom_to
        self.flash = flash
        self.card_scale = card_scale
        self.shake = shake
        self.paper_flash = paper_flash
        self.slide = slide
        self.pulse = pulse
        self.caption = caption   # (hindi text, colour)


def build_scene_list():
    S = []
    # 01 red page slams in -------------------------------------------------
    S.append(Scene(0, 2, card="red", grain=0.35))
    # 02 small line prints ------------------------------------------------
    S.append(Scene(2, 4, card="red", title=("small", RED_DARK), grain=0.18,
                   zoom=1.0, zoom_to=1.02))
    # 03 giant name slams -------------------------------------------------
    S.append(Scene(4, 5.5, card="red",
                   title=("both", [(126, 6, 10), (152, 10, 14)]), zoom=1.02,
                   zoom_to=1.05, shake=7, grain=0.55, pulse=1.0))
    # 04 bleach to cream ---------------------------------------------------
    S.append(Scene(5.5, 8, card="red", title=("both", (243, 221, 229)),
                   zoom=1.05, zoom_to=1.07, leak=0.22))
    # 05 whip into the printed page ---------------------------------------
    S.append(Scene(8, 8.5, card="hero", grain=0.9, flash=0.10))
    # 06 ink page drift ----------------------------------------------------
    S.append(Scene(8.5, 12, card="hero", zoom=1.14, zoom_to=1.24, leak=0.08))
    # 07 red sticker window ------------------------------------------------
    S.append(Scene(12, 14, card="hero", sticker=(712, 52, 300, 208, "red"),
                   zoom=1.24, zoom_to=1.29, grain=0.22, pulse=1.0))
    # 08 bleached page ------------------------------------------------------
    S.append(Scene(14, 16.5, card="hero_white", zoom=1.29, zoom_to=1.35,
                   leak=0.28, sticker=(712, 52, 300, 208, "ember")))
    # 09 red gradient wash + idle cursor ------------------------------------
    S.append(Scene(16.5, 18.5, card="hero_red", zoom=1.35, zoom_to=1.41,
                   cursor=(150, 300, 0.72), grain=0.28, pulse=1.0))
    # 10 flute plate --------------------------------------------------------
    S.append(Scene(18.5, 21, card="flute", zoom=1.04, zoom_to=1.16,
                   paper_flash=0.40))
    # 11 giant word over the page ------------------------------------------
    S.append(Scene(21, 23.5, card="flute_red", title=("giant", (250, 238, 232)),
                   zoom=1.16, zoom_to=1.22, leak=0.26, shake=4, pulse=1.0))
    # 12 the page goes almost black ----------------------------------------
    S.append(Scene(23.5, 25, card="hero_dark", zoom=1.22, zoom_to=1.26,
                   grain=0.45))
    # 13 white flash ---------------------------------------------------------
    S.append(Scene(25, 26, card="hero_white", flash=0.55, zoom=1.08))
    # 14 pink page -----------------------------------------------------------
    S.append(Scene(26, 28, card="hero_pink", zoom=1.08, zoom_to=1.16,
                   sticker=(60, 340, 268, 190, "grey"), leak=0.20,
                   caption=("माखन चोर", (108, 10, 20))))
    # 15 hero returns in red --------------------------------------------------
    S.append(Scene(28, 30.5, card="hero_red2", zoom=1.16, zoom_to=1.24,
                   grain=0.18, leak=0.16, pulse=1.0,
                   caption=("जय श्री कृष्ण", (250, 240, 232))))
    # 16 darker, lit from the side -------------------------------------------
    S.append(Scene(30.5, 32, card="hero_dark", zoom=1.24, zoom_to=1.28,
                   leak=0.34))
    # 17 whip out to black ----------------------------------------------------
    S.append(Scene(32, 33, card="red", grain=0.7, card_scale=0.0))
    return S


CARD_STYLES = {
    # key                : (plate, wash, wash_style, contrast, light)
    "red":        ("redframe", None, "duotone", 1.0, 0.0),
    "hero":       ("hero", None, "duotone", 1.22, 0.75),
    "hero_white": ("hero", ((248, 244, 238), 0.55), "soft", 1.35, 0.9),
    "hero_red":   ("hero", ((196, 12, 16), 0.86), "gradient", 1.30, 0.8),
    "hero_red2":  ("hero", ((212, 34, 26), 0.72), "gradient", 1.28, 0.8),
    "hero_pink":  ("hero", ((236, 104, 138), 0.60), "soft", 1.24, 0.8),
    "hero_dark":  ("hero", ((24, 20, 26), 0.55), "gradient", 1.30, 0.9),
    "flute":      ("flute", None, "duotone", 1.28, 0.8),
    "flute_red":  ("flute", ((206, 40, 26), 0.62), "gradient", 1.26, 0.85),
}


def apply_card_leak(card: Image.Image, strength: float, seed: int,
                    mask: Image.Image, color=(255, 226, 208)) -> Image.Image:
    """Soft window-light bloom that lives ON the printed page."""
    if strength <= 0.01:
        return card
    rng = np.random.default_rng(seed)
    lay = Image.new("L", (CARD_W, CARD_H), 0)
    d = ImageDraw.Draw(lay)
    x = int(rng.uniform(-200, 300))
    y = int(rng.uniform(-120, 300))
    d.polygon([(x, y), (x + 700, y + 260), (x + 520, y + 700), (x - 260, y + 420)],
              fill=int(150 * strength))
    lay = lay.filter(ImageFilter.GaussianBlur(70))
    lay = Image.composite(lay, Image.new("L", lay.size, 0), mask)
    tint = Image.new("RGB", card.size, color)
    out = Image.composite(tint, card.convert("RGB"), lay.point(lambda v: int(v * 0.8)))
    out = Image.blend(card.convert("RGB"), out, 1.0)
    out = out.convert("RGBA")
    out.putalpha(mask)
    return out


def make_sticker_color(src: Image.Image, w: int, h: int, mode: str = "red"):
    """Small hot-toned window: the page art re-printed as a red sticker."""
    g = src.convert("L").resize((w, h), Image.LANCZOS)
    g = ImageEnhance.Contrast(g).enhance(2.1)
    a = np.array(g, dtype=np.float32) / 255.0
    if mode == "red":
        r = np.clip(30 + 235 * a, 0, 255)
        gg = np.clip(14 + 70 * a ** 1.4, 0, 255)
        b = np.clip(18 + 46 * a ** 1.4, 0, 255)
    elif mode == "ember":
        r = np.clip(40 + 215 * a, 0, 255)
        gg = np.clip(20 + 120 * a ** 1.2, 0, 255)
        b = np.clip(16 + 30 * a, 0, 255)
    else:
        r = np.clip(20 + 210 * a, 0, 255) * 0 + 235 * a
        gg = 235 * a
        b = 240 * a
    out = Image.fromarray(np.stack([r, gg, b], -1).astype(np.uint8))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, w - 1, h - 1], outline=(246, 238, 228), width=3)
    return out


def render(preview_frames=None):
    rng = np.random.default_rng(4)
    plates = {"hero": load_plate(PLATE_HERO), "flute": load_plate(PLATE_FLUTE)}

    # flat red "card back" for the title screen, with the art barely printed in
    red_card = Image.new("RGB", (CARD_W, CARD_H), RED)
    ra = np.array(red_card, dtype=np.float32)
    yy = np.linspace(-1, 1, CARD_H)[:, None, None]
    xx = np.linspace(-1, 1, CARD_W)[None, :, None]
    ra *= (1.0 - 0.22 * (xx ** 2 * 0.6 + yy ** 2 * 0.5))
    red_card = Image.fromarray(np.clip(ra, 0, 255).astype(np.uint8))
    ghost = plates["hero"].resize((CARD_W, CARD_H), Image.LANCZOS)
    ga = np.array(ghost.convert("L"), dtype=np.float32) / 255.0
    rc = np.array(red_card, dtype=np.float32)
    rc = rc * (0.70 + 0.62 * ga[..., None])
    red_card_ghost = Image.fromarray(np.clip(rc, 0, 255).astype(np.uint8))

    ed = PrintRevealEdit(plates=[plates["hero"]], card_styles=[], duration=DUR,
                         fps=FPS, workdir=WORK, handle=HANDLE)
    mask = ed.card_mask

    # pre-baked sticker sources
    st_src = {
        "red": make_sticker_color(plates["hero"], 300, 208, "red"),
        "ember": make_sticker_color(plates["flute"], 300, 208, "ember"),
        "grey": make_sticker_color(plates["flute"], 268, 190, "grey"),
    }

    scenes = build_scene_list()
    nframes = int(round(DUR * FPS))
    vid_path = os.path.join(WORK, "video_noaudio.mp4")
    fw = FrameWriter(vid_path, fps=FPS, crf=17, preset="medium")
    if preview_frames:
        os.makedirs("/var/tmp/kr/prev", exist_ok=True)

    card_cache = {}

    def card_for(key, t):
        if key == "red":
            return red_card_ghost.convert("RGBA")
        plate_key, wash, style, contrast, light = CARD_STYLES[key]
        spec = CardSpec(plate=plates[plate_key], wash=wash, wash_style=style,
                        seed=(abs(hash(key)) % 900) + 7, contrast=contrast,
                        light=light)
        return ed.card_image(spec, t)

    for f in range(nframes):
        t = f / FPS
        sc = None
        for s_ in scenes:
            if b(s_.b0) - 1e-6 <= t < b(s_.b1):
                sc = s_
                break
        if sc is None:
            sc = scenes[-1]

        frame = Image.new("RGBA", (W, H), (8, 8, 10, 255))
        prog = (t - b(sc.b0)) / max(1e-6, b(sc.b1) - b(sc.b0))
        prog = min(1.0, max(0.0, prog))

        # ---------------- card -------------------------------------------
        cscale = sc.card_scale
        rot = 0.0
        if sc.b0 == 0:                       # pop in
            k = min(1.0, t / 0.20)
            cscale = 0.90 + 0.10 * _eo(k)
            rot = -1.6 * (1 - _eo(k))
        if sc.b0 == 8:                       # whip in from the title
            k = min(1.0, prog / 0.22)
            cscale = 1.06 - 0.06 * _eo(k)
            rot = 2.2 * (1 - _eo(k))
        if sc.b0 == 32:                      # whip out
            k = min(1.0, prog / 0.5)
            cscale = max(0.0, 1.0 - _eo(k))
            rot = -3.0 * _eo(k)

        if cscale > 0.02:
            card = card_for(sc.card, t).convert("RGBA")
            z = sc.zoom if sc.zoom_to is None else \
                sc.zoom + (sc.zoom_to - sc.zoom) * _eo(prog)
            # beat pulse
            if sc.pulse:
                z += 0.02 * max(0.0, 1.0 - (prog * sc.pulse))
            zw, zh = int(CARD_W / z), int(CARD_H / z)
            x0 = (CARD_W - zw) // 2
            y0 = (CARD_H - zh) // 2
            x0 = max(0, min(CARD_W - zw, x0 + int(10 * math.sin(t * 0.9))))
            y0 = max(0, min(CARD_H - zh, y0 + int(6 * math.sin(t * 0.6 + 1))))
            inner = card.crop((x0, y0, x0 + zw, y0 + zh)).resize(
                (CARD_W, CARD_H), Image.BICUBIC)
            inner.putalpha(mask)
            inner = apply_card_leak(inner, sc.leak, f, mask)

            # printed Hindi caption along the bottom of the page
            if sc.caption:
                ctext, ccol = sc.caption
                cm = rough_text_mask(ctext, F_DEV, 78, seed=(f // 7) + 41,
                                     rough=0.45)
                col_rgba = Image.new("RGBA", cm.size, tuple(ccol) + (255,))
                col_rgba.putalpha(cm.point(lambda v: int(v * 0.95)))
                cx0 = CARD_W // 2 - cm.width // 2
                cy0 = CARD_H - cm.height - 26
                inner.alpha_composite(col_rgba, (max(6, cx0), max(6, cy0)))

            # sticker
            if sc.sticker:
                x0s, y0s, ws, hs, style = sc.sticker
                k2 = min(1.0, prog * 3.0)
                inner.alpha_composite(st_src[style].resize((ws, hs), Image.LANCZOS)
                                      .convert("RGBA"), (x0s, y0s))
                if k2 < 1.0:      # scale-in pop handled by 1-frame reveal
                    pass

            cw, ch = max(2, int(CARD_W * cscale)), max(2, int(CARD_H * cscale))
            card_draw = inner.resize((cw, ch), Image.BICUBIC)
            if abs(rot) > 0.05:
                card_draw = card_draw.rotate(rot, resample=Image.BICUBIC,
                                             expand=False)
            sx = sy = 0
            if sc.shake:
                sx = int(rng.integers(-sc.shake, sc.shake + 1))
                sy = int(rng.integers(-sc.shake, sc.shake + 1))
            cx = W // 2 + sx
            cy = CARD_Y + CARD_H // 2 + sy
            place_card(frame, card_draw, 1.0, cx, cy, ed.card_shadow)

            # cursor (idle mouse over the page)
            if sc.cursor:
                cxp, cyp, click_at = sc.cursor
                clk = 0.0
                if prog > click_at:
                    clk = min(1.0, (prog - click_at) / 0.16)
                cursor_arrow(frame, cxp, cyp, 0.92, 1.55, clk)

            # printed titles
            if sc.title:
                kind, col = sc.title
                if kind == "small":
                    title_slam(frame, [("जय श्री", F_DEV, 560, 150)], 1.0,
                               color=col, dy=-140, seed=f)
                elif kind == "both":
                    title_slam(frame, [("जय श्री", F_DEV, 520, 132),
                                       ("कृष्ण", F_DEV, 830, 300)], 1.0,
                               color=col, dy=-4, jitter=2, seed=f)
                elif kind == "giant":
                    giant_word(frame, "गोविंद", F_DEV, 880, CARD_Y + 60, col,
                               0.97, seed=9)

        # ---------------- global effects ---------------------------------
        # a 1-frame tick on every beat keeps the page feeling beat-locked
        bi = t / BEAT
        if abs(bi - round(bi)) < 0.5 / FPS / BEAT * 1.05:
            frame_flicker(frame, 0.045)
        if sc.grain > 0:
            grain_flick(frame, rng, sc.grain * (0.5 + 0.5 * math.sin(t * 19)))
        if sc.flash > 0:
            k = max(0.0, 1.0 - prog * 3.4)
            frame_flicker(frame, sc.flash * k)
        if sc.paper_flash > 0:
            k = max(0.0, 1.0 - prog * 4.5)
            frame_flicker(frame, sc.paper_flash * k)
        vignette_and_close(frame)

        # HUD (hidden for the first 2 frames and the whip-out)
        vis = 1.0
        if sc.b0 == 0:
            vis = min(1.0, max(0.0, (t - 0.10) / 0.25))
        if sc.b0 == 32:
            vis = max(0.0, 1.0 - prog * 3)
        stamp_hud(frame, DUR - t, HANDLE, alpha=vis, scale=max(cscale, 0.25))

        if preview_frames:
            if f in preview_frames:
                frame.convert("RGB").save(f"/var/tmp/kr/prev/f{f:04d}.png")
        else:
            fw.write(frame.convert("RGB"))
        if f % 60 == 0:
            print(f"  frame {f}/{nframes}  t={t:.2f}s", flush=True)

    if preview_frames:
        fw.close()
        return None
    fw.close()
    print("video done ->", vid_path, flush=True)
    return vid_path


def build_audio():
    """Cut the bhajan exactly on the measured groove downbeat; no processing
    beyond fades — loudness is handled at mux time."""
    from om_hybrid._ffmpeg import get_ffmpeg
    import subprocess
    ff = get_ffmpeg()
    out = os.path.join(WORK, "song.wav")
    dur = DUR
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{SOURCE_START:.3f}", "-t", f"{dur + 0.35:.3f}",
                    "-i", AUDIO_SRC,
                    "-af", "afade=t=in:st=0:d=0.06,"
                           f"afade=t=out:st={dur - 0.55:.3f}:d=0.55,"
                           f"atrim=0:{dur:.3f}",
                    "-ar", "48000", "-ac", "2", out], check=True)
    return out


if __name__ == "__main__":
    print(f"song grid: {BPM} BPM  beat={BEAT:.4f}s  dur={DUR:.3f}s "
          f"frames={int(DUR*FPS)}")
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "video"):
        v = render()
    if mode in ("all", "audio"):
        a = build_audio()
        out = os.path.join(OUT_DIR, "Krishna_PrintReveal_Bhajan_9x16.mp4")
        mux_audio(os.path.join(WORK, "video_noaudio.mp4"), a, out,
                  target_i=-14.0, target_tp=-1.5)
        print("FINAL ->", out, os.path.getsize(out) / 1e6, "MB")
