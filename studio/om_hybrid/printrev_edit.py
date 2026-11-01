"""
printrev_edit.py — "Printed Page / Sketchbook Reveal" edit engine.

Recreates the format of the `F0E2B6A9-...mov` sample (kevamarts "GOD'S WISDOM"):
  * 1080x1920 frame, near-black bg, one centred rounded rectangle "card"
  * card = photo of an ink-illustration printed on a spiral-bound sketchbook page,
    side-lit by a slow moving white window light, faint fingerprints / paper grain
  * a timer HUD top-right counting DOWN, an @handle top-left
  * masked title slam on the card (multi-size, ink-rough), then the art itself
    with beat-locked colour washes, red "sticker" insets, soft grain flicks,
    giant ultra-condensed words, custom cursor arrow, light leaks, one pink flash
  * card pop-in / pop-out, whip-out-into-black ending

All scene content is synthesised from generated ink plates (no stock footage),
so the engine only needs: plate PNGs + a ballad/bhajan audio file + a beat grid.

Usage (see build script krishna_printrev.py):
    from om_hybrid.printrev_edit import PrintRevealEdit, CardSpec
    ed = PrintRevealEdit(plates=[...], audio=..., workdir=...)
    ed.render('out.mp4')
"""

from __future__ import annotations

import math
import os
import random
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from om_hybrid._ffmpeg import get_ffmpeg  # noqa: E402

W, H = 1080, 1920
FPS = 30

# card geometry measured from the sample
CARD_W, CARD_H = 1080, 608
CARD_Y = 656

RED = (188, 8, 13)
RED_DARK = (120, 4, 8)
INK = (16, 14, 20)

FONT_DIR = "/home/user/assets/fonts"
F_DEV = os.path.join(FONT_DIR, "NotoSansDevanagari-Black.ttf")
F_ANTON = os.path.join(FONT_DIR, "Anton-Regular.ttf")
F_ARCHIVO = os.path.join(FONT_DIR, "ArchivoBlack-Regular.ttf")
F_BARLOW_XB = os.path.join(FONT_DIR, "BarlowCondensed-ExtraBold.ttf")
F_BARLOW_B = os.path.join(FONT_DIR, "BarlowCondensed-Bold.ttf")
F_BEBAS = os.path.join(FONT_DIR, "BebasNeue-Regular.ttf")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _ease_in_out(t: float) -> float:
    return t * t * (3 - 2 * t)


def _clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def _lerp(a, b, t):
    return a + (b - a) * t


def rough_text_mask(text: str, font_path: str, px: int, seed: int = 7,
                    rough: float = 0.55) -> Image.Image:
    """Rubber-stamp lettering: solid ink core, chipped irregular edge,
    sparse pinholes.  Returns an L mask at the text's natural size."""
    from scipy import ndimage as ndi

    font = ImageFont.truetype(font_path, px)
    dummy = ImageDraw.Draw(Image.new("L", (8, 8)))
    box = dummy.textbbox((0, 0), text, font=font)
    pad = max(6, px // 7)
    w = max(2, box[2] - box[0] + pad * 2)
    h = max(2, box[3] - box[1] + pad * 2)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad - box[0], pad - box[1]), text, font=font, fill=255)
    base = np.array(m, dtype=np.float32) / 255.0
    core = base > 0.5

    rng = np.random.default_rng(seed)
    # --- chipped edge: thin the outline with a medium-frequency field -------
    depth = max(2, int(px * 0.028 * (0.8 + rough)))
    dist = ndi.distance_transform_edt(core)
    edge_zone = dist <= depth
    n_small = max(4, int(px / 13))
    nf = rng.random((max(2, h // n_small), max(2, w // n_small))).astype(np.float32)
    nf = np.array(Image.fromarray((nf * 255).astype(np.uint8)).resize(
        (w, h), Image.BICUBIC), dtype=np.float32) / 255.0
    keep_edge = nf > (0.10 + 0.22 * (1 - rough))
    ink = core & (~edge_zone | keep_edge)

    # --- sparse pinholes inside -------------------------------------------
    holes = ndi.gaussian_filter((rng.random((h, w)) > 0.993).astype(np.float32),
                                sigma=max(1.0, px / 90.0)) > 0.06
    ink = ink & ~(holes & (dist > depth))

    # --- ink density variation (printed unevenness) ------------------------
    dens = ndi.gaussian_filter(rng.random((h, w)).astype(np.float32),
                               sigma=max(1.5, px / 40.0))
    dens = (dens - dens.min()) / (np.ptp(dens) + 1e-6)
    alpha = ink.astype(np.float32) * (0.80 + 0.20 * dens)
    alpha = ndi.gaussian_filter(alpha, sigma=0.7)
    return Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8))


def fit_font(font_path: str, text: str, target_w: int, start: int = 700) -> int:
    px = start
    while px > 10:
        f = ImageFont.truetype(font_path, px)
        box = ImageDraw.Draw(Image.new("L", (4, 4))).textbbox((0, 0), text, font=f)
        if box[2] - box[0] <= target_w:
            return px
        px -= 4
    return 10


def paste_center(canvas: Image.Image, im: Image.Image, cx: int, cy: int,
                 color: Optional[Tuple[int, int, int]] = None):
    if color is not None:
        tint = Image.new("RGB", im.size, color)
        canvas.paste(tint, (int(cx - im.width / 2), int(cy - im.height / 2)), im)
    else:
        canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def draw_halftone(size, pitch=6, angle=0.0, color=(255, 255, 255), alpha=26,
                  dot=0.42):
    """Screen-print halftone dots as an RGBA layer."""
    w, h = size
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    r = pitch * dot
    y = -pitch
    row = 0
    while y < h + pitch:
        x0 = -pitch + (pitch / 2 if row % 2 else 0)
        x = x0
        while x < w + pitch:
            d.ellipse([x - r, y - r, x + r, y + r], fill=alpha)
            x += pitch
        y += pitch * 0.85
        row += 1
    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    out = Image.new("RGBA", (w, h), color + (0,))
    out.putalpha(layer)
    return out


def paper_grain(size, rng: np.random.Generator, amount=16.0) -> Image.Image:
    w, h = size
    base = rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32)
    img = Image.fromarray(((base * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC)
    g = (np.array(img, dtype=np.float32) - 128.0) / 128.0
    out = np.clip(g * amount + 128.0, 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert("L")


# --------------------------------------------------------------------------- #
# card renderer
# --------------------------------------------------------------------------- #
@dataclass
class CardSpec:
    """What the sketchbook page should look like at a given beat."""
    plate: Image.Image                     # ink plate (RGB)
    wash: Optional[Tuple[Tuple[int, int, int], float]] = None   # colour + strength
    wash_style: str = "duotone"            # duotone | gradient | soft
    seed: int = 0
    light: float = 0.55                    # window-light strength
    contrast: float = 1.12
    paper: float = 1.0


class PrintRevealEdit:
    def __init__(self, plates: List[Image.Image], card_styles: list,
                 duration: float, fps: int = FPS, workdir: str = "/var/tmp/printrev",
                 handle: str = "@arena.ai", rng_seed: int = 11):
        self.plates = plates
        self.styles = card_styles
        self.dur = duration
        self.fps = fps
        self.nframes = int(round(duration * fps))
        self.workdir = workdir
        self.handle = handle
        self.rng = np.random.default_rng(rng_seed)
        os.makedirs(workdir, exist_ok=True)

        self.grain = paper_grain((CARD_W, CARD_H), self.rng, 18.0)
        self.grain_full = paper_grain((W, H), self.rng, 9.0)
        self.halftone = draw_halftone((CARD_W, CARD_H), pitch=5, alpha=30)

        # card corner rounding mask + soft shadow
        self.card_mask = self._rounded_mask(CARD_W, CARD_H, 34)
        self.card_shadow = self._make_shadow()

        # pre-rendered title masks
        self.slam_font = F_BARLOW_XB

    # ------------------------------------------------------------------ #
    @staticmethod
    def _rounded_mask(w, h, r, ss=4):
        m = Image.new("L", (w * ss, h * ss), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1],
                                            radius=r * ss, fill=255)
        return m.resize((w, h), Image.LANCZOS)

    def _make_shadow(self):
        pad = 80
        m = Image.new("L", (CARD_W + pad * 2, CARD_H + pad * 2), 0)
        m.paste(self.card_mask, (pad, pad))
        m = m.filter(ImageFilter.GaussianBlur(34))
        sh = Image.new("RGB", m.size, (0, 0, 0))
        return sh, m

    # ------------------------------------------------------------------ #
    def card_image(self, spec: CardSpec, t: float) -> Image.Image:
        """Print the page: plate → wash → halftone → grain → light → vignette."""
        rng = np.random.default_rng(spec.seed * 977 + 13)
        plate = spec.plate
        # centre-crop to card aspect
        pw, ph = plate.size
        target = CARD_W / CARD_H
        if pw / ph > target:
            nw = int(ph * target)
            x0 = (pw - nw) // 2
            plate = plate.crop((x0, 0, x0 + nw, ph))
        else:
            nh = int(pw / target)
            y0 = (ph - nh) // 2
            plate = plate.crop((0, y0, pw, y0 + nh))
        img = plate.resize((CARD_W, CARD_H), Image.LANCZOS).convert("L")

        # paper tint: warm off-white
        paper = np.zeros((CARD_H, CARD_W, 3), dtype=np.float32)
        base = 236.0 if spec.wash is None else 232.0
        paper[..., 0] = base
        paper[..., 1] = base - 6
        paper[..., 2] = base - 14
        # multiply ink
        ink = np.array(img, dtype=np.float32) / 255.0
        img_rgb = paper * ink[..., None]

        if spec.wash is not None:
            col, amt = spec.wash
            col = np.array(col, dtype=np.float32)
            if spec.wash_style == "gradient":
                yy = np.linspace(0, 1, CARD_H)[:, None, None]
                xx = np.linspace(0, 1, CARD_W)[None, :, None]
                ramp = np.clip(0.35 + 1.15 * (yy * 0.75 + (1 - xx) * 0.35), 0, 1.4)
                dupe = paper * (col[None, None, :] / 255.0) * ramp * 1.05
            elif spec.wash_style == "soft":
                dupe = paper * (0.45 + 0.55 * col[None, None, :] / 255.0)
            else:
                dupe = paper * (col[None, None, :] / 255.0) * 1.15
            img_rgb = img_rgb * (1 - amt) + dupe * ink[..., None] * amt + \
                (dupe * (1 - ink[..., None]) * amt * 0.10)

        arr = Image.fromarray(np.clip(img_rgb, 0, 255).astype(np.uint8))
        arr = ImageEnhance.Contrast(arr).enhance(spec.contrast)

        # halftone screen + paper grain + fingerprints
        arr = arr.convert("RGBA")
        arr.alpha_composite(self.halftone)
        g = self.grain
        arr = Image.blend(arr.convert("RGB"), Image.merge(
            "RGB", [g, g, g]), 0.07)
        arr = arr.convert("RGBA")

        fprng = np.random.default_rng(spec.seed * 31 + 5)
        fp = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fp)
        for _ in range(3):
            cx = int(fprng.uniform(0, CARD_W))
            cy = int(fprng.uniform(0, CARD_H))
            rr = int(fprng.uniform(26, 80))
            fd.ellipse([cx - rr, cy - int(rr * .7), cx + rr, cy + int(rr * .7)],
                       fill=(255, 250, 240, 16))
        fp = fp.filter(ImageFilter.GaussianBlur(22))
        arr.alpha_composite(fp)

        # slow drifting window light (two soft bands + sweep)
        lx = (_ease_in_out(_clamp(t / max(self.dur, 0.001))) * 0.6 + 0.2)
        light = Image.new("L", (CARD_W, CARD_H), 0)
        ld = ImageDraw.Draw(light)
        cx = int(_lerp(-260, CARD_W + 260, lx))
        ld.polygon([(cx - 420, 0), (cx + 40, 0), (cx + 380, CARD_H),
                    (cx - 90, CARD_H)], fill=int(150 * spec.light))
        ld.polygon([(cx + 150, 0), (cx + 300, 0), (cx + 620, CARD_H),
                    (cx + 470, CARD_H)], fill=int(85 * spec.light))
        light = light.filter(ImageFilter.GaussianBlur(40))
        white = Image.new("RGBA", (CARD_W, CARD_H), (255, 252, 244, 255))
        arr = Image.composite(Image.blend(arr.convert("RGB"), white.convert("RGB"), 0.42),
                              arr.convert("RGB"), light.point(lambda v: int(v * 0.55)))
        arr = arr.convert("RGBA")

        # spiral-binding dots down the left edge + punched holes right edge
        holes = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(holes)
        n = 15
        for i in range(n):
            yy = int((i + 0.5) * CARD_H / n)
            hd.ellipse([10, yy - 7, 26, yy + 7], fill=(150, 24, 30, 70))
            hd.ellipse([12, yy - 5, 24, yy + 5], fill=(24, 18, 22, 120))
            hd.ellipse([CARD_W - 26, yy - 6, CARD_W - 12, yy + 6],
                       fill=(120, 20, 26, 55))
        arr.alpha_composite(holes)

        # vignette + rounded corners
        vy = np.linspace(-1, 1, CARD_H)[:, None]
        vx = np.linspace(-1, 1, CARD_W)[None, :]
        vig = np.clip(1.0 - 0.16 * (vx ** 2 * 0.7 + vy ** 2), 0, 1)
        a = np.array(arr.convert("RGB"), dtype=np.float32) * vig[..., None]
        arr = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        arr.putalpha(self.card_mask)
        return arr


# --------------------------------------------------------------------------- #
# scene compositor
# --------------------------------------------------------------------------- #
@dataclass
class Beat:
    """One visual beat on the timeline."""
    t0: float
    t1: float
    kind: str
    args: dict = field(default_factory=dict)


class Timeline:
    def __init__(self, beats: List[Beat]):
        self.beats = sorted(beats, key=lambda b: b.t0)

    def at(self, t: float) -> Optional[Beat]:
        cur = None
        for b in self.beats:
            if b.t0 <= t + 1e-6:
                cur = b
            else:
                break
        return cur

    def local(self, t: float):
        b = self.at(t)
        if b is None:
            return None, 0.0, 0.0
        return b, t - b.t0, max(1e-6, b.t1 - b.t0)


# --------------------------------------------------------------------------- #
# overlay primitives (all operate on the full 1080x1920 frame)
# --------------------------------------------------------------------------- #
def _mono_font(path, px):
    return ImageFont.truetype(path, px)


def stamp_hud(frame: Image.Image, remaining: float, handle: str,
              alpha: float = 1.0, scale: float = 1.0):
    """@handle top-left + countdown top-right, sitting inside the card."""
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = _mono_font(F_BARLOW_B, max(10, int(40 * scale)))
    a = int(255 * alpha)
    m, s = divmod(int(max(0.0, remaining)), 60)
    txt = f"0:{s:02d}" if m == 0 else f"{m}:{s:02d}"
    d.text((44, CARD_Y + 28), handle, font=f,
           fill=(245, 245, 245, a))
    box = d.textbbox((0, 0), txt, font=f)
    d.text((W - 44 - (box[2] - box[0]), CARD_Y + 28), txt, font=f,
           fill=(245, 245, 245, a))
    frame.alpha_composite(lay)


def title_slam(frame: Image.Image, lines, alpha: float, color=(240, 214, 222),
               dy: int = 0, scale: float = 1.0, jitter: int = 0,
               cx: Optional[int] = None, seed: int = 0):
    """Masked, multi-size ink title centred on the card."""
    if alpha <= 0.01:
        return
    rng = np.random.default_rng(seed)
    cx = W // 2 if cx is None else cx
    cy = CARD_Y + CARD_H // 2 + dy
    # layout: compute total height first
    masks = []
    for i, (text, font_path, target_w, px_hint) in enumerate(lines):
        px = fit_font(font_path, text, int(target_w * scale), start=int(px_hint * scale))
        masks.append(rough_text_mask(text, font_path, px, seed=seed + i * 17,
                                     rough=0.6))
    total_h = sum(m.height for m in masks) + int(6 * scale) * (len(masks) - 1)
    cols = color if isinstance(color, (list, tuple)) and len(color) and \
        isinstance(color[0], (list, tuple)) else None
    y = cy - total_h // 2
    a = int(255 * alpha)
    for i, m in enumerate(masks):
        ox = int(rng.integers(-jitter, jitter + 1)) if jitter else 0
        c = cols[i % len(cols)] if cols else color
        col = Image.new("RGBA", m.size, tuple(c) + (255,))
        col.putalpha(m.point(lambda v: int(v * alpha)))
        frame.alpha_composite(col, (cx - m.width // 2 + ox, y))
        y += m.height + int(6 * scale)


def giant_word(frame: Image.Image, text: str, font_path: str, target_w: int,
               cy: int, color, alpha: float, seed: int = 3, rough: float = 0.5,
               stroke: int = 0, outline=None):
    if alpha <= 0.01:
        return
    px = fit_font(font_path, text, target_w, start=560)
    m = rough_text_mask(text, font_path, px, seed=seed, rough=rough)
    col = Image.new("RGBA", m.size, tuple(color) + (255,))
    col.putalpha(m.point(lambda v: int(v * alpha)))
    frame.alpha_composite(col, (W // 2 - m.width // 2, cy - m.height // 2))


def sticker_inset(frame: Image.Image, card: Image.Image, rect, alpha: float,
                  style: str = "red", seed: int = 1, border: int = 3):
    """Small red-toned plate window sitting on the card (the 'sticker')."""
    if alpha <= 0.01:
        return
    x0, y0, x1, y1 = rect
    w, h = max(2, x1 - x0), max(2, y1 - y0)
    crop = card.convert("RGB").crop((x0, y0, x0 + w, y0 + h))
    g = crop.convert("L")
    if style == "red":
        rr, gg, bb = 226, 34, 40
        tint = Image.merge("RGB", [g.point(lambda v: int(v * rr / 255)),
                                   g.point(lambda v: int(v * gg / 255)),
                                   g.point(lambda v: int(v * bb / 255))])
        tint = ImageEnhance.Contrast(tint).enhance(1.5)
        tint = Image.blend(tint, ImageEnhance.Color(Image.new("RGB", (w, h), (215, 24, 24))).enhance(1.0), 0.18)
    else:
        tint = ImageEnhance.Contrast(g).enhance(1.6).convert("RGB")
    if border:
        d = ImageDraw.Draw(tint)
        d.rectangle([0, 0, w - 1, h - 1], outline=(248, 240, 230), width=border)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle([0, 0, w - 1, h - 1], fill=int(255 * alpha))
    frame.paste(tint, (x0, y0), mask)


def cursor_arrow(frame: Image.Image, x: int, y: int, alpha: float = 1.0,
                 scale: float = 1.0, click: float = 0.0):
    if alpha <= 0.01:
        return
    s = scale
    pts = [(0, 0), (0, 30), (8, 23), (13, 34), (19, 31), (14, 21), (23, 21)]
    pts = [(px * s, py * s) for px, py in pts]
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if click > 0:
        r = int(26 * s * (1 + 1.5 * click))
        d.ellipse([x - r, y - r, x + r, y + r],
                  outline=(255, 255, 255, int(190 * (1 - click))), width=3)
    d.polygon([(x + px, y + py) for px, py in pts], fill=(20, 20, 22, int(255 * alpha)),
              outline=(250, 250, 250, int(255 * alpha)))
    frame.alpha_composite(lay)


def light_leak(frame: Image.Image, strength: float, seed: int = 0,
               color=(255, 214, 190), mask: Optional[Image.Image] = None):
    if strength <= 0.01:
        return
    rng = np.random.default_rng(seed)
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    x = int(rng.uniform(-200, 400))
    y = int(rng.uniform(-300, 900))
    d.polygon([(x, y), (x + 900, y + 500), (x + 700, y + 1100), (x - 300, y + 700)],
              fill=int(150 * strength))
    lay = lay.filter(ImageFilter.GaussianBlur(160))
    if mask is not None:
        lay = Image.composite(lay, Image.new("L", lay.size, 0), mask)
    tint = Image.new("RGB", (W, H), color)
    frame.paste(Image.composite(tint, frame.convert("RGB"), lay), (0, 0))


def frame_flicker(frame: Image.Image, amt: float):
    if amt <= 0.001:
        return
    a = np.array(frame.convert("RGB"), dtype=np.float32)
    a = a * (1 + amt) + 255 * max(0.0, amt) * 0.35
    frame.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (0, 0))


def grain_flick(frame: Image.Image, rng: np.random.Generator, amount: float):
    """Fast-passing vertical print streaks (the sample's 'scan' flashes)."""
    if amount <= 0.01:
        return
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(int(28 * amount)):
        x = int(rng.uniform(0, W))
        w = int(rng.uniform(1, 7))
        y0 = int(rng.uniform(0, H * 0.6))
        y1 = y0 + int(rng.uniform(H * 0.15, H * 0.55))
        d.rectangle([x, y0, x + w, y1], fill=int(rng.uniform(70, 190)))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    white = Image.new("RGB", (W, H), (245, 245, 245))
    frame.paste(Image.composite(white, frame.convert("RGB"), lay.point(
        lambda v: int(v * 0.55))), (0, 0))


def place_card(frame: Image.Image, card: Image.Image, scale: float = 1.0,
               cx: int = W // 2, cy: int = CARD_Y + CARD_H // 2,
               shadow: Optional[Image.Image] = None):
    if abs(scale - 1.0) > 1e-3:
        c = card.resize((max(2, int(CARD_W * scale)), max(2, int(CARD_H * scale))),
                        Image.BICUBIC)
    else:
        c = card
    x = int(cx - c.width / 2)
    y = int(cy - c.height / 2)
    if shadow is not None:
        sh, sm = shadow
        sc = sh.resize((int(sh.width * scale), int(sh.height * scale)), Image.BILINEAR)
        scm = sm.resize(sc.size, Image.BILINEAR)
        frame.paste(sc, (x - int(80 * scale), y - int(80 * scale)), scm)
    frame.paste(c, (x, y), c)
    return (x, y)


def vignette_and_close(frame: Image.Image):
    """Crush everything outside the card band towards black (no smear on card)."""
    arr = np.array(frame.convert("RGB"), dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    top = np.clip((y - (CARD_Y - 120)) / 220.0, 0, 1)
    bot = np.clip(((CARD_Y + CARD_H + 120) - y) / 220.0, 0, 1)
    v = np.minimum(top, bot)
    v = 0.12 + 0.88 * (v ** 0.8)
    arr *= v[:, None, None]
    frame.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), (0, 0))


# --------------------------------------------------------------------------- #
# encoder
# --------------------------------------------------------------------------- #
class FrameWriter:
    def __init__(self, path: str, fps: int = FPS, crf: int = 17,
                 preset: str = "medium"):
        self.path = path
        ff = get_ffmpeg()
        self.p = subprocess.Popen(
            [ff, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(fps), "-i", "-",
             "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", path],
            stdin=subprocess.PIPE)

    def write(self, img: Image.Image):
        if img.mode != "RGB":
            img = img.convert("RGB")
        self.p.stdin.write(img.tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()
        if self.p.returncode != 0:
            raise RuntimeError(f"ffmpeg encode failed rc={self.p.returncode}")


def measure_loudness(path: str):
    """Pass 1 of loudnorm: returns the measured_* dict."""
    import json
    import re
    ff = get_ffmpeg()
    cmd = [ff, "-hide_banner", "-nostats", "-i", path, "-af",
           "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None
    return json.loads(m.group(0))


def mux_audio(video: str, audio: str, out: str, target_i: float = -14.0,
              target_tp: float = -1.5, audio_filter: str = ""):
    """Two-pass loudness normalise + mux (video stream copied untouched)."""
    ff = get_ffmpeg()
    meas = measure_loudness(audio)
    ln = f"loudnorm=I={target_i}:TP={target_tp}:LRA=9"
    if meas:
        ln += (f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
               f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
               f":offset={meas['target_offset']}:linear=true")
    af = (audio_filter + "," if audio_filter else "") + ln + ",alimiter=limit=0.94"
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", video,
           "-i", audio, "-c:v", "copy", "-af", af,
           "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
           "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out
