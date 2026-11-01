"""
redthread_edit.py — "ONE THREAD" brand-film engine (spec / commercial work).

Format
------
A single brand-red filament travels through a 1080x1920 frame and re-shapes
itself on the beat:  spark -> signal wave -> highway -> rosette -> network ->
smile -> swoosh lock-up.  Nothing else on screen except optional kinetic
typography.  Built for brand films where there is no footage at all.

Why parametric
--------------
Every shape is a function of u in [0,1] -> (x, y).  Morphing is therefore a
plain lerp between two point sets (same N), so a shape can twist into any
other shape continuously - no clipping, no cross-fade cheat.

Dependencies: numpy + PIL only (line, glow, grain).  Deterministic.
"""
from __future__ import annotations

import math
import os
import subprocess
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1080, 1920
SS = 2                      # supersample factor for line drawing
N = 720                     # points per thread

BRAND_RED = (226, 20, 24)
BRAND_RED_DEEP = (128, 6, 10)
WHITE = (245, 243, 240)


def ease(t: float, kind: str = "inout") -> float:
    t = max(0.0, min(1.0, t))
    if kind == "inout":
        return t * t * (3 - 2 * t)
    if kind == "out":
        return 1 - (1 - t) ** 3
    if kind == "in":
        return t ** 3
    if kind == "outback":
        c1, c3 = 1.30, 2.30
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
    return t


# --------------------------------------------------------------------------- #
# shape library — each returns (xs, ys) in full-frame coordinates
# --------------------------------------------------------------------------- #
def shape_spark(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """A single hot point that hasn't moved yet (a 12px dash)."""
    x = W / 2 + (u - 0.5) * 26
    y = np.full_like(u, H * 0.50)
    return x, y


def shape_wave(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Signal / sound wave across the frame."""
    x = 70 + (W - 140) * u
    y = H * 0.50 + 132 * np.sin(2 * math.pi * 2.6 * u) * (0.55 + 0.45 * np.sin(math.pi * u))
    return x, y


def shape_highway(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Long S-curve road: enters bottom-left, exits top-right, with a
    converging perspective pinch in the middle."""
    y = H * 0.70 - (H * 0.58) * u
    x = W * 0.14 + (W * 0.72) * u + 190 * np.sin(2 * math.pi * 0.92 * u + 0.55)
    return x, y


def shape_rosette(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Rangoli-ish rosette: two and a half petals around the centre."""
    ang = 2 * math.pi * u - math.pi / 2
    r = 300 + 118 * np.cos(5 * ang)
    x = W / 2 + r * np.cos(ang) * 0.82
    y = H * 0.47 + r * np.sin(ang)
    return x, y


def shape_network(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Connectivity spine: a long horizontal trunk with symmetric service
    drops — reads as a network, not as noise."""
    x = 80 + (W - 160) * u
    trunk = H * 0.44
    drop = np.abs(np.sin(2 * math.pi * 1.5 * u)) ** 0.7   # 3 rounded drops
    y = trunk - 165 * drop + 70 * np.sin(math.pi * u)
    return x, y


def shape_smile(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """One wide smile."""
    x = 110 + (W - 220) * u
    s = (2 * u - 1)
    # ends HIGH on screen, middle LOW -> reads as a smile
    y = H * 0.42 + 300 * (1 - s ** 2)
    return x, y


def shape_swoosh(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Brand swoosh: a rising arc that sweeps to the right."""
    # asymmetric brand swoosh: enters bottom-left, sweeps right and up,
    # tapering away above the wordmark
    x = 90 + 900 * u
    y = H * 0.46 - 250 * (u ** 2.0) + 34 * np.sin(2 * math.pi * u)
    return x, y


SHAPES = {
    "spark": shape_spark,
    "wave": shape_wave,
    "highway": shape_highway,
    "rosette": shape_rosette,
    "network": shape_network,
    "smile": shape_smile,
    "swoosh": shape_swoosh,
}

# how many node dots to stamp on a shape (network / rosette get dots)
NODES = {"network": 9, "rosette": 12, "smile": 2, "swoosh": 1}


@dataclass
class Beat:
    """One 'state' of the thread: which shape, from which beat to which beat."""
    b0: float
    b1: float
    shape: str
    width: float = 22.0
    glow: float = 1.0
    dots: bool = False
    caption: Optional[str] = None
    kicker: Optional[str] = None
    pulse: bool = True


class ThreadFilm:
    def __init__(self, beats: Sequence[Beat], beat_len: float, duration: float,
                 fps: int = 30, workdir: str = "/var/tmp/redthread",
                 red=BRAND_RED, bg=(6, 6, 8)):
        self.beats = list(beats)
        self.bl = beat_len
        self.dur = duration
        self.fps = fps
        self.nframes = int(round(duration * fps))
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.red = np.array(red, dtype=np.float32)
        self.bg = bg
        rng = np.random.default_rng(7)
        self.grain = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        self.grain_img = Image.fromarray(
            ((self.grain * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
        ).resize((W, H), Image.BICUBIC)

    # ---------------------------------------------------------------- shapes
    def samples(self, u: np.ndarray, name: str):
        xs, ys = SHAPES[name](u)
        pts = np.stack([xs, ys], 1)
        # light smoothing so hand-rolled maths never looks spiky
        if name in ("network", "rosette", "highway"):
            k = 15
            pad = np.pad(pts, ((k, k), (0, 0)), mode="edge")
            ker = np.ones(2 * k + 1) / (2 * k + 1)
            pts = np.stack([np.convolve(pad[:, 0], ker, "same")[k:-k],
                            np.convolve(pad[:, 1], ker, "same")[k:-k]], 1)
        return pts

    def morph_points(self, t: float) -> Tuple[np.ndarray, float, float, Beat, float]:
        """Current thread polyline + shape width/glow + active beat + progress."""
        u = np.linspace(0, 1, N)
        cur = None
        prev = None
        for b in self.beats:
            if b.b0 * self.bl - 1e-6 <= t:
                prev, cur = cur, b
            else:
                break
        if cur is None:
            cur = self.beats[0]
        a = self.samples(u, cur.shape)
        if prev is None or prev.shape == cur.shape:
            return a, cur.width, cur.glow, cur, 0.0
        # transition occupies the first 55% of the beat slot
        span = (cur.b1 - cur.b0) * self.bl
        tt = (t - cur.b0 * self.bl) / max(1e-6, span * 0.55)
        k = ease(tt, "inout")
        b_pts = self.samples(u, prev.shape)
        # blend, then a little arc so the thread bows while it travels
        p = b_pts * (1 - k) + a * k
        bow = math.sin(math.pi * k) * np.sin(math.pi * u) * 46
        p[:, 1] -= bow
        return p, cur.width, cur.glow, cur, k

    # ---------------------------------------------------------------- drawing
    def draw_thread(self, pts: np.ndarray, width: float, glow: float,
                    head_u: float, alpha: float = 1.0) -> Image.Image:
        """Line + halo + travelling comet head, drawn at SS then downsampled."""
        big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        poly = [(float(x) * SS, float(y) * SS) for x, y in pts]
        col = tuple(int(c) for c in self.red) + (int(255 * alpha),)
        d.line(poly, fill=col, width=int(width * SS), joint="curve")
        # round caps
        for p in (poly[0], poly[-1]):
            r = width * SS / 2
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)

        # comet head
        i = int(head_u * (len(poly) - 1))
        hx, hy = poly[i]
        for rr, aa in ((46, 46), (30, 90), (16, 150), (7, 255)):
            d.ellipse([hx - rr * SS / 2, hy - rr * SS / 2, hx + rr * SS / 2,
                       hy + rr * SS / 2],
                      fill=(255, 245, 235, int(aa * alpha)))

        small = big.resize((W, H), Image.LANCZOS)
        # halo
        halo = small.filter(ImageFilter.GaussianBlur(18 * glow))
        halo = halo.point(lambda v: int(v * 0.85))
        wide = small.filter(ImageFilter.GaussianBlur(48 * glow))
        wide = wide.point(lambda v: int(v * 0.55))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(wide)
        out.alpha_composite(halo)
        out.alpha_composite(small)
        return out

    def nodes(self, pts: np.ndarray, count: int, t: float, alpha=1.0):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for k in range(count):
            idx = int((k + 0.5) / count * (len(pts) - 1))
            x, y = pts[idx]
            ph = math.sin(t * 6.0 + k * 1.7) * 0.5 + 0.5
            r = 5 + 5 * ph
            d.ellipse([x - r, y - r, x + r, y + r],
                      fill=(255, 240, 232, int(200 * alpha)))
            d.ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3],
                      outline=(226, 20, 24, int(90 * alpha)), width=2)
        return lay

    # ---------------------------------------------------------------- frame
    def background(self, t: float) -> Image.Image:
        """Near-black with a slow red bloom behind the thread."""
        base = Image.new("RGB", (W, H), self.bg)
        bl = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(bl)
        cx = W * 0.5 + 90 * math.sin(t * 0.6)
        cy = H * 0.47 + 60 * math.cos(t * 0.5)
        d.ellipse([cx - 260, cy - 320, cx + 260, cy + 320], fill=70)
        bl = bl.filter(ImageFilter.GaussianBlur(220))
        tint = Image.new("RGB", (W, H), (70, 6, 10))
        base = Image.composite(tint, base, bl.point(lambda v: int(v * 0.9)))
        return base

    def finish(self, frame: Image.Image, t: float, grain_amt: float = 4.0,
               vig: float = 0.50) -> Image.Image:
        a = np.array(frame.convert("RGB"), dtype=np.float32)
        # vignette
        yy = np.linspace(-1, 1, H)[:, None]
        xx = np.linspace(-1, 1, W)[None, :]
        v = np.clip(1.0 - vig * (xx ** 2 * 0.55 + yy ** 2 * 0.8), 0, 1)
        a *= v[..., None]
        # grain
        g = np.array(self.grain_img.resize((W, H)), dtype=np.float32) - 128.0
        a += g[..., None] * (grain_amt / 128.0)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    def render(self, writer=None, preview_frames=None, text_layer=None):
        os.makedirs("/var/tmp/redthread/prev", exist_ok=True)
        for f in range(self.nframes):
            t = f / self.fps
            pts, width, glow, beat, k = self.morph_points(t)
            frame = self.background(t).convert("RGBA")
            head = min(1.0, (t / max(1e-6, self.dur)) * 1.15 + 0.04)
            # the thread draws itself in over the first beat
            intr = ease(min(1.0, t / (self.bl * 1.6)), "out")
            alpha = 0.35 + 0.65 * intr
            thread = self.draw_thread(pts, width, glow, head, alpha)
            frame.alpha_composite(thread)
            if beat.dots:
                frame.alpha_composite(self.nodes(pts, NODES.get(beat.shape, 6),
                                                 t, alpha))
            # beat pulse: tiny scale flash on each beat
            bi = t / self.bl
            if beat.pulse and abs(bi - round(bi)) < (0.6 / self.fps) / self.bl:
                a = np.array(frame.convert("RGB"), dtype=np.float32)
                a = a * 1.06 + 6
                frame = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
            if text_layer is not None:
                text_layer(frame, t, beat, k)
            out = self.finish(frame, t)
            if preview_frames:
                if f in preview_frames:
                    out.save(f"/var/tmp/redthread/prev/f{f:04d}.png")
            elif writer is not None:
                writer.write(out)
        return True
