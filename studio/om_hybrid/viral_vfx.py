"""viral_vfx.py — Universal 17-Weapon Viral Edit Arsenal (`S01..S11` Production Engine).

Implements every visual, rotoscoping, shader, camera-physics, musical-pocket, and
still-illustration technique reverse-engineered across all 11 `Sample` reference &
breakdown videos so they can be applied to ANY video (Type 1, Type 2, Type 3, or
standalone movie/anime/tech/art edits) locally or on the 16 GB GitHub Cloud Farm:

  AI Roto & Layering (`selfie_segmenter.tflite` Apache-2.0):
    1. `segment_person_mask`           — 30+ FPS XNNPACK human foreground alpha matte
    2. `text_behind_subject`   (S05)   — 3D Z-depth solid/video-textured title behind person
    3. `red_ribbon_roto`       (S01)   — B&W sky + `-32°` crimson B-roll ribbon + roto silhouette + katana invert flash
    4. `silhouette_double_exp` (S09)   — B-roll playing dynamically INSIDE dark human silhouette over clean backdrop
    5. `roto_clone_pop`        (S05/9) — Beat-synced left/right roto clones OR 3 freeze-frame cutouts on `#000000`
    6. `flashlight_glow`       (S06)   — Glowing white phosphor silhouette + bloom in pitch darkness

  Experimental Shaders, Print & Glitch FX (`k1sh0r/blob-tracker` MIT + custom OpenCV):
    7. `run_blob_tracking`     (S06)   — TouchDesigner bounding boxes + web lines + numeric coordinate chips
    8. `datamosh_optical`      (S06/10)— Frame-accurate Farneback optical-flow P-frame melt + 16x16 block corrupt
    9. `dither_1bit`           (S03/6) — 8x8 Ordered Bayer 1-Bit monochrome stipple dither + optional accent label
   10. `risograph_2tone`       (S03)   — Indigo/Periwinkle 2-tone posterized halftone + crimson editorial serif bars
   11. `receipt_ticket`        (S06)   — Crinkled thermal receipt paper + dithered portrait + live monospace receipt HUD
   12. `crt_phosphor`          (S03/6) — Cyan CRT / Pink Phosphor / Curved Barrel-Lens TV (`r'=r*(1+k*r^2)`)
   13. `bass_shockwave`        (S09)   — Propagating radial refraction shockwave ring on 808/bass timestamps

  Camera Physics, Musical Rhythm & Still-Art Engines:
   14. `fight_club_shake`      (S11)   — Nose/eye Match-Move Face-Locked Shake (face pinned still while room smears) + 35mm grain
   15. `center_match_strobe`   (S10)   — `(cx, cy)` focal lock + `B&W -> Full-Color` beat explosion
   16. `plan_jigsaw_music_pockets` + `write_center_serif_ass` (S02/S04) — Musical gap dialogue planner + `18pt` center serif subs
   17. `render_still_art_edit` (S08)   — Zero-footage still-drawing/poster edit (`1f` polarity flip + wiggle + radial glow + glitch slices)
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

from ._ffmpeg import get_ffmpeg, get_ffprobe
from .smart_camera import _make_face_detector

HERE = Path(__file__).resolve().parent
MODELS_DIR = HERE / "models"
STUDIO_DIR = HERE.parent
ROOT_DIR = STUDIO_DIR.parent
FONTS_DIR = ROOT_DIR / "assets" / "fonts"
BLOBTRACK_DIR = STUDIO_DIR / "skills" / "blob-tracking" / "scripts"
SELFIE_MODEL = MODELS_DIR / "selfie_segmenter.tflite"

# 8x8 Ordered Bayer Matrix normalized to [0..1]
_BAYER_8X8 = (
    np.array(
        [
            [0, 32, 8, 40, 2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44, 4, 36, 14, 46, 6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [3, 35, 11, 43, 1, 33, 9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47, 7, 39, 13, 45, 5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21],
        ],
        dtype=np.float32,
    )
    + 0.5
) / 64.0


def _hex_to_bgr(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return (b, g, r)


def _load_font(size_px: int, font_name: str = "ArchivoBlack-Regular.ttf") -> ImageFont.FreeTypeFont:
    for cand in (
        FONTS_DIR / font_name,
        BLOBTRACK_DIR / font_name,
        FONTS_DIR / "Anton-Regular.ttf",
        BLOBTRACK_DIR / "JetBrainsMono-Regular.ttf",
    ):
        if cand.exists():
            return ImageFont.truetype(str(cand), max(10, int(size_px)))
    return ImageFont.load_default()


class PersonSegmenter:
    """Fast CPU XNNPACK human foreground segmenter (`selfie_segmenter.tflite`, Apache-2.0)."""

    def __init__(self) -> None:
        self._seg = None
        if SELFIE_MODEL.exists():
            try:
                import mediapipe as mp
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision

                opts = vision.ImageSegmenterOptions(
                    base_options=mp_python.BaseOptions(model_asset_path=str(SELFIE_MODEL)),
                    output_category_mask=False,
                    output_confidence_masks=True,
                )
                self._seg = vision.ImageSegmenter.create_from_options(opts)
                self._mp = mp
            except Exception:
                self._seg = None

    def mask(self, frame_bgr: np.ndarray, feather_px: int = 7) -> np.ndarray:
        """Return soft float32 foreground alpha in `[0.0 .. 1.0]` of shape `(H, W, 1)`."""
        h, w = frame_bgr.shape[:2]
        if self._seg is not None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            res = self._seg.segment(mp_img)
            m = res.confidence_masks[0].numpy_view().astype(np.float32)
            if m.ndim == 3:
                m = m[..., 0]
            if m.shape != (h, w):
                m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            # Fallback center-weighted contrast mask if mediapipe is unavailable
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
            m = np.clip(1.0 - np.abs(gray - np.median(gray)) * 2.5, 0.0, 1.0)
        if feather_px >= 3:
            k = feather_px | 1
            m = cv2.GaussianBlur(m, (k, k), 0)
        return np.clip((m - 0.35) / 0.35, 0.0, 1.0)[..., None]

    def close(self) -> None:
        if self._seg is not None:
            try:
                self._seg.close()
            except Exception:
                pass


def segment_person_mask(frame_bgr: np.ndarray, feather_px: int = 7) -> np.ndarray:
    """One-shot convenience wrapper returning `(H, W, 1)` float32 person alpha `[0..1]`."""
    seg = PersonSegmenter()
    try:
        return seg.mask(frame_bgr, feather_px=feather_px)
    finally:
        seg.close()


# ==============================================================================
# 1. VENDORED BLOB TRACKING (`S06` @marcelgrauu / `k1sh0r/blob-tracker` MIT)
# ==============================================================================
def run_blob_tracking(
    in_mp4: str,
    out_mp4: str,
    small: int = 25,
    medium: int = 8,
    large: int = 3,
    invert: float = 0.25,
    extra_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply TouchDesigner-style Blob Tracking (`k1sh0r/blob-tracker` MIT) to `in_mp4`."""
    ffmpeg = get_ffmpeg()
    get_ffprobe()
    env = os.environ.copy()
    env["PATH"] = f"{Path(ffmpeg).parent}:{env.get('PATH', '')}"

    if str(BLOBTRACK_DIR) not in sys.path:
        sys.path.insert(0, str(BLOBTRACK_DIR))
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = env["PATH"]
    try:
        import blobtrack  # type: ignore

        Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
        bt_params = {
            "small": int(small),
            "medium": int(medium),
            "large": int(large),
            "invert": float(invert),
        }
        if extra_params:
            for k, v in extra_params.items():
                if k in blobtrack.DEFAULTS:
                    bt_params[k] = v
        blobtrack.run(str(in_mp4), str(out_mp4), params=bt_params)
    finally:
        os.environ["PATH"] = old_path

    return {
        "effect": "blob_tracking",
        "in_mp4": str(in_mp4),
        "out_mp4": str(out_mp4),
        "size_mb": round(Path(out_mp4).stat().st_size / 1048576.0, 2),
    }


# ==============================================================================
# 2. INDIVIDUAL FRAME-LEVEL VFX SHADERS & LAYER COMPOSITORS (`S01..S11`)
# ==============================================================================
def _render_word_layer_bgr(
    text: str,
    w: int,
    h: int,
    font_px: int,
    color_bgr: tuple[int, int, int] = (35, 165, 255),
    y_frac: float = 0.44,
    tex_bgr: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return `(layer_bgr, alpha_float_hw1)` for bold 3D Z-depth text (`S05`)."""
    font = _load_font(font_px, "ArchivoBlack-Regular.ttf")
    mask_pil = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_pil)
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (w - tw) // 2 - bb[0]
    ty = int(round(h * y_frac - th * 0.5)) - bb[1]
    draw.text((tx, ty), text, fill=255, font=font)
    alpha = (np.asarray(mask_pil, dtype=np.float32) / 255.0)[..., None]
    if tex_bgr is not None:
        layer = cv2.resize(tex_bgr, (w, h), interpolation=cv2.INTER_LINEAR)
    else:
        layer = np.full((h, w, 3), color_bgr, dtype=np.uint8)
    return layer, alpha


def frame_dither_1bit(
    frame_bgr: np.ndarray,
    contrast: float = 1.35,
    label: str = "",
    label_hex: str = "#D9C53B",
) -> np.ndarray:
    """`S03` (Vishnu) & `S06`: 8x8 Ordered Bayer 1-Bit monochrome stipple dithering."""
    h, w = frame_bgr.shape[:2]
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    gray = np.clip(0.5 + (gray - 0.5) * contrast, 0.0, 1.0)
    tiled = np.tile(_BAYER_8X8, (h // 8 + 1, w // 8 + 1))[:h, :w]
    bits = (gray > tiled).astype(np.uint8) * 255
    out = cv2.cvtColor(bits, cv2.COLOR_GRAY2BGR)
    if label:
        lbl_bgr, lbl_a = _render_word_layer_bgr(
            label, w, h, font_px=max(28, w // 11), color_bgr=_hex_to_bgr(label_hex), y_frac=0.52
        )
        out = np.clip(out * (1.0 - lbl_a) + lbl_bgr * lbl_a, 0, 255).astype(np.uint8)
    return out


def frame_risograph_2tone(
    frame_bgr: np.ndarray,
    dark_hex: str = "#1A2168",
    light_hex: str = "#CED8F7",
    top_caption: str = "",
    bot_caption: str = "",
    caption_hex: str = "#9E1B32",
) -> np.ndarray:
    """`S03` (@_.raajjjjjj_ Oppenheimer / Bhagavad Gita): 2-Tone Indigo Risograph print + serif bars."""
    h, w = frame_bgr.shape[:2]
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    # Quantize into 3 subtle print steps + fine Bayer halftone edge
    tiled = np.tile(_BAYER_8X8, (h // 8 + 1, w // 8 + 1))[:h, :w]
    ink = np.clip((gray - 0.34) / 0.36 + (tiled - 0.5) * 0.22, 0.0, 1.0)
    ink = np.round(ink * 2.0) / 2.0  # crisp 3-step Risograph ink tones

    # Subtle horizontal scanline/paper texture
    scan = (0.95 + 0.05 * ((np.arange(h) % 3 == 0).astype(np.float32)))[:, None]
    ink = np.clip(ink * scan, 0.0, 1.0)[..., None]

    c_dark = np.array(_hex_to_bgr(dark_hex), dtype=np.float32)
    c_light = np.array(_hex_to_bgr(light_hex), dtype=np.float32)
    out = np.clip(c_dark * (1.0 - ink) + c_light * ink, 0, 255).astype(np.uint8)

    bar_h = max(36, int(round(h * 0.095)))
    cap_col = _hex_to_bgr(caption_hex)
    if top_caption or bot_caption:
        pil = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        font = _load_font(int(bar_h * 0.48), "PlayfairDisplay-Bold.ttf")
        light_rgb = (int(c_light[2]), int(c_light[1]), int(c_light[0]))
        txt_rgb = (cap_col[2], cap_col[1], cap_col[0])
        if top_caption:
            draw.rectangle([(0, 0), (w, bar_h)], fill=light_rgb)
            bb = draw.textbbox((0, 0), top_caption, font=font)
            draw.text(((w - (bb[2] - bb[0])) // 2, (bar_h - (bb[3] - bb[1])) // 2 - bb[1]), top_caption, fill=txt_rgb, font=font)
        if bot_caption:
            draw.rectangle([(0, h - bar_h), (w, h)], fill=light_rgb)
            bb = draw.textbbox((0, 0), bot_caption, font=font)
            draw.text(((w - (bb[2] - bb[0])) // 2, h - bar_h + (bar_h - (bb[3] - bb[1])) // 2 - bb[1]), bot_caption, fill=txt_rgb, font=font)
        out = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    return out


def frame_receipt_ticket(frame_bgr: np.ndarray, frame_idx: int, fps: float, title: str = "MAKER STUDIO") -> np.ndarray:
    """`S06` (@marcelgrauu): Thermal receipt paper dithered frame + live monospace receipt print."""
    h, w = frame_bgr.shape[:2]
    # Paper background (warm thermal off-white #F3F1EC with subtle vertical fiber noise)
    rng = np.random.default_rng(101)
    paper = np.full((h, w, 3), (235, 241, 243), dtype=np.float32)
    grain = rng.normal(0.0, 4.5, size=(h, w, 1)).astype(np.float32)
    paper = np.clip(paper + grain, 215, 250).astype(np.uint8)

    # Inner receipt image area
    pad_x = int(w * 0.10)
    top_y = int(h * 0.17)
    bot_y = int(h * 0.78)
    iw, ih = w - 2 * pad_x, bot_y - top_y
    sub = cv2.resize(frame_bgr, (iw, ih), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    gray = np.clip(0.5 + (gray - 0.48) * 1.45, 0.0, 1.0)
    tiled = np.tile(_BAYER_8X8, (ih // 8 + 1, iw // 8 + 1))[:ih, :iw]
    ink_mask = (gray < tiled).astype(np.float32)[..., None]
    # faded charcoal thermal ink (#22201E)
    paper_crop = paper[top_y:bot_y, pad_x:pad_x + iw].astype(np.float32)
    paper[top_y:bot_y, pad_x:pad_x + iw] = np.clip(paper_crop * (1.0 - 0.86 * ink_mask), 0, 255).astype(np.uint8)

    pil = Image.fromarray(cv2.cvtColor(paper, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    f_hdr = _load_font(max(14, w // 28), "JetBrainsMono-Regular.ttf")
    f_sm = _load_font(max(11, w // 42), "JetBrainsMono-Regular.ttf")
    ink_rgb = (34, 32, 30)
    t_s = frame_idx / max(1.0, fps)
    draw.text((pad_x, int(h * 0.05)), f"*** {title} ***", fill=ink_rgb, font=f_hdr)
    draw.text((pad_x, int(h * 0.095)), f"DATE: 2026-11-01   TC: {t_s:06.2f}s", fill=ink_rgb, font=f_sm)
    draw.text((pad_x, int(h * 0.13)), "-" * 34, fill=ink_rgb, font=f_sm)
    draw.text((pad_x, int(h * 0.80)), "-" * 34, fill=ink_rgb, font=f_sm)
    draw.text((pad_x, int(h * 0.835)), f"FRAME #{frame_idx:05d}          QTY 01   $0.00", fill=ink_rgb, font=f_sm)
    # Barcode stripes at bottom
    bx = pad_x
    by0, by1 = int(h * 0.885), int(h * 0.945)
    for bi in range(48):
        bw_bar = 2 if (bi * 7 + frame_idx) % 3 == 0 else 4
        if bi % 2 == 0 and bx + bw_bar < w - pad_x:
            draw.rectangle([(bx, by0), (bx + bw_bar, by1)], fill=ink_rgb)
        bx += bw_bar + 3
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)


_BARREL_CACHE: dict[tuple[int, int, float], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}


def frame_crt_phosphor(
    frame_bgr: np.ndarray,
    palette: str = "cyan",
    barrel_k: float = 0.0,
) -> np.ndarray:
    """`S06` Cyan CRT / Pink Phosphor & `S03` Curved Barrel-Lens CRT TV."""
    h, w = frame_bgr.shape[:2]
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    gray = np.clip(0.5 + (gray - 0.46) * 1.32, 0.0, 1.0)

    if palette == "pink":
        # Hot magenta-pink phosphor (#FF18C8)
        b = np.clip(gray * 215.0 + (gray ** 2) * 40.0, 0, 255)
        g = np.clip((gray ** 2.2) * 145.0, 0, 255)
        r = np.clip(gray * 255.0, 0, 255)
    elif palette == "indigo_tv":
        # S03 Vishvarupa blue-violet CRT
        b = np.clip(65.0 + gray * 190.0, 0, 255)
        g = np.clip(35.0 + (gray ** 1.3) * 185.0, 0, 255)
        r = np.clip(30.0 + (gray ** 1.6) * 175.0, 0, 255)
        if barrel_k <= 0.0:
            barrel_k = 0.24
    else:
        # S06 Cyan phosphor (#00E5FF)
        b = np.clip(gray * 255.0, 0, 255)
        g = np.clip((gray ** 1.15) * 235.0, 0, 255)
        r = np.clip((gray ** 2.4) * 170.0, 0, 255)

    Phosphor = np.stack([b, g, r], axis=-1)
    # Scanlines every 3px + soft phosphor bloom
    scan = np.where((np.arange(h) % 3) == 0, 0.72, 1.05).astype(np.float32)[:, None, None]
    Phosphor = np.clip(Phosphor * scan, 0, 255).astype(np.uint8)
    bloom = cv2.GaussianBlur(Phosphor, (0, 0), sigmaX=7.0)
    out = cv2.addWeighted(Phosphor, 0.80, bloom, 0.32, 0.0)

    if barrel_k > 0.001:
        key = (h, w, round(barrel_k, 3))
        if key not in _BARREL_CACHE:
            yy, xx = np.meshgrid(np.linspace(-1.0, 1.0, h), np.linspace(-1.0, 1.0, w), indexing="ij")
            r2 = xx * xx + yy * yy
            factor = 1.0 + barrel_k * r2
            mx = ((xx * factor + 1.0) * 0.5 * (w - 1)).astype(np.float32)
            my = ((yy * factor + 1.0) * 0.5 * (h - 1)).astype(np.float32)
            inside = ((np.abs(xx * factor) <= 0.985) & (np.abs(yy * factor) <= 0.985)).astype(np.float32)
            inside = cv2.GaussianBlur(inside, (9, 9), 0)[..., None]
            _BARREL_CACHE[key] = (mx, my, inside)
        mx, my, inside = _BARREL_CACHE[key]
        warped = cv2.remap(out, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        out = (warped.astype(np.float32) * inside).astype(np.uint8)
    return out


def frame_bass_shockwave(frame_bgr: np.ndarray, progress_01: float, strength_px: float = 28.0) -> np.ndarray:
    """`S09` (@willrvail #4): Propagating concentric radial displacement shockwave on bass hit."""
    if not (0.0 < progress_01 < 1.0):
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    dx = xx - w * 0.5
    dy = yy - h * 0.5
    max_r = math.hypot(w * 0.5, h * 0.5)
    dist = np.sqrt(dx * dx + dy * dy) + 1e-4
    ring_r = progress_01 * max_r * 0.95
    band_w = max_r * 0.11
    ring = np.exp(-(((dist - ring_r) / band_w) ** 2)) * (1.0 - progress_01)
    disp = ring * strength_px * np.sin((dist - ring_r) / (band_w * 0.35))
    mx = xx + (dx / dist) * disp
    my = yy + (dy / dist) * disp
    return cv2.remap(frame_bgr, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)


# ==============================================================================
# 3. STREAMING PIPELINE ENGINE (`apply_vfx_pipeline` — Runs on ANY Video!)
# ==============================================================================
def apply_vfx_pipeline(
    in_mp4: str,
    out_mp4: str,
    effect: str,
    params: dict[str, Any] | None = None,
    windows: list[list[float]] | None = None,
) -> dict[str, Any]:
    """Stream `in_mp4` through any `S01..S11` viral VFX mode (`< 250 MB` RAM) & preserve original audio.

    Supported `effect` names:
      - `blob_tracking`           (S06)
      - `text_behind_subject`     (S05)
      - `red_ribbon_roto`         (S01)
      - `silhouette_double_exp`   (S09)
      - `roto_clone_pop`          (S05 / S09)
      - `flashlight_glow`         (S06)
      - `datamosh_optical`        (S06 / S10)
      - `dither_1bit`             (S03 / S06)
      - `risograph_2tone`         (S03)
      - `receipt_ticket`          (S06)
      - `crt_phosphor`            (S03 / S06)
      - `bass_shockwave`          (S09)
      - `fight_club_shake`        (S11)
      - `center_match_strobe`     (S10)
    """
    p = params or {}
    if effect == "blob_tracking":
        return run_blob_tracking(
            in_mp4,
            out_mp4,
            small=int(p.get("small", 25)),
            medium=int(p.get("medium", 8)),
            large=int(p.get("large", 3)),
            invert=float(p.get("invert", 0.25)),
            extra_params=p,
        )

    ffmpeg = get_ffmpeg()
    cap = cv2.VideoCapture(str(in_mp4))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {in_mp4}")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    needs_roto = effect in (
        "text_behind_subject",
        "red_ribbon_roto",
        "silhouette_double_exp",
        "roto_clone_pop",
        "flashlight_glow",
    )
    segmenter = PersonSegmenter() if needs_roto else None
    face_detect = _make_face_detector()[0] if effect == "fight_club_shake" else None

    # Optional secondary B-roll video reader (`red_ribbon_roto`, `silhouette_double_exp`, `text_behind_subject`)
    broll_cap = cv2.VideoCapture(str(p["broll_mp4"])) if p.get("broll_mp4") else None

    def _next_broll(fallback: np.ndarray) -> np.ndarray:
        if broll_cap is None:
            return cv2.flip(fallback, 1)
        ok_b, fb = broll_cap.read()
        if not ok_b:
            broll_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok_b, fb = broll_cap.read()
        if not ok_b:
            return fallback
        return cv2.resize(fb, (w, h), interpolation=cv2.INTER_LINEAR)

    work = Path(tempfile.mkdtemp(prefix="viral_vfx_"))
    vid_only = work / "vfx_video.mp4"
    enc = subprocess.Popen(
        [
            ffmpeg, "-y", "-v", "warning",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps:.4f}",
            "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-x264-params", "rc-lookahead=20",
            "-pix_fmt", "yuv420p",
            str(vid_only),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None

    # Pre-build angled ribbon mask for `red_ribbon_roto` (`S01` @sumanth.mp4 `-32°` crimson strip)
    ribbon_mask: np.ndarray | None = None
    if effect == "red_ribbon_roto":
        ang = math.radians(float(p.get("angle_deg", -18.0)))
        band_half = float(p.get("band_frac", 0.14)) * h
        yy, xx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
        dist_line = (yy - h * 0.50) * math.cos(ang) - (xx - w * 0.50) * math.sin(ang)
        ribbon_mask = np.clip((band_half - np.abs(dist_line)) / 3.0, 0.0, 1.0)[..., None]

    # Stateful trackers across frames
    prev_gray: np.ndarray | None = None
    mosh_canvas: np.ndarray | None = None
    freeze_clones: list[tuple[np.ndarray, np.ndarray]] = []
    smooth_face_xy = [0.5, 0.45]
    rng = np.random.default_rng(77)

    fi = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t_s = fi / fps
        in_win = True
        if windows:
            in_win = any(w0 <= t_s <= w1 for (w0, w1) in windows)

        if not in_win:
            out_f = frame
        elif effect == "text_behind_subject":
            assert segmenter is not None
            fg_a = segmenter.mask(frame)
            tex = _next_broll(frame) if p.get("broll_mp4") else None
            txt_bgr, txt_a = _render_word_layer_bgr(
                str(p.get("text", "LEGACY")),
                w, h,
                font_px=int(p.get("font_px", max(72, w // 5))),
                color_bgr=_hex_to_bgr(str(p.get("color_hex", "#F4A236"))),
                y_frac=float(p.get("y_frac", 0.42)),
                tex_bgr=tex,
            )
            mid = frame.astype(np.float32) * (1.0 - txt_a) + txt_bgr.astype(np.float32) * txt_a
            out_f = np.clip(mid * (1.0 - fg_a) + frame.astype(np.float32) * fg_a, 0, 255).astype(np.uint8)

        elif effect == "red_ribbon_roto":
            assert segmenter is not None and ribbon_mask is not None
            fg_a = segmenter.mask(frame)
            # 1. Desaturated moody B&W sky/background
            bw = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR).astype(np.float32)
            bw = np.clip((bw - 120.0) * 1.18 + 118.0, 0, 255)
            # 2. Crimson-tinted B-roll ribbon behind silhouette
            br = _next_broll(frame)
            br_luma = cv2.cvtColor(br, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
            crimson = np.stack([br_luma * 25.0, br_luma * 18.0, 95.0 + br_luma * 160.0], axis=-1)
            comp = bw * (1.0 - ribbon_mask) + crimson * ribbon_mask
            # 3. Darkened high-contrast foreground silhouette on top!
            sil = np.clip(frame.astype(np.float32) * 0.28, 0, 255)
            out_f = np.clip(comp * (1.0 - fg_a) + sil * fg_a, 0, 255).astype(np.uint8)
            # 4. Katana white flash (2f) + negative luma invert (8f) at `katana_flash_times`
            for kt in p.get("katana_flash_times", []):
                dt = t_s - float(kt)
                if 0.0 <= dt < 2.0 / fps:
                    out_f = np.full_like(out_f, 255)
                elif 2.0 / fps <= dt < 10.0 / fps:
                    out_f = 255 - out_f

        elif effect == "silhouette_double_exp":
            assert segmenter is not None
            fg_a = segmenter.mask(frame, feather_px=5)
            br = _next_broll(frame)
            bg_col = np.full((h, w, 3), _hex_to_bgr(str(p.get("bg_hex", "#F2F4F8"))), dtype=np.float32)
            # Crisp dark-contrasted B-roll playing strictly INSIDE the silhouette!
            br_c = np.clip((br.astype(np.float32) - 110.0) * 1.25 + 95.0, 0, 255)
            out_f = np.clip(bg_col * (1.0 - fg_a) + br_c * fg_a, 0, 255).astype(np.uint8)

        elif effect == "roto_clone_pop":
            assert segmenter is not None
            fg_a = segmenter.mask(frame)
            clone_mode = str(p.get("clone_mode", "offset_live"))
            if clone_mode == "freeze_black":
                # S05: 3 sequential rotoscoped freeze-frames popping 1->2->3 on pure #000000 black!
                snap_times = p.get("beat_times", [0.15, 0.55, 0.95])
                if len(freeze_clones) < len(snap_times) and t_s >= float(snap_times[len(freeze_clones)]):
                    freeze_clones.append((frame.copy(), fg_a.copy()))
                canvas_blk = np.zeros((h, w, 3), dtype=np.float32)
                shifts = [-int(w * 0.26), 0, int(w * 0.26)]
                for ci, (cf, ca) in enumerate(freeze_clones[:3]):
                    M = np.float32([[1, 0, shifts[ci % 3]], [0, 1, 0]])
                    wf = cv2.warpAffine(cf, M, (w, h)).astype(np.float32)
                    wa = cv2.warpAffine(ca[..., 0], M, (w, h))[..., None]
                    # Subtle bright rim glow on cutouts like S05
                    canvas_blk = canvas_blk * (1.0 - wa) + np.clip(wf * 1.18 + 18.0, 0, 255) * wa
                out_f = np.clip(canvas_blk, 0, 255).astype(np.uint8)
            else:
                # S09: Live left/right clones popping on beat hits + 1-frame flash
                off_px = int(p.get("offset_px", max(60, w // 7)))
                base_f = frame.astype(np.float32)
                for sign in (-1, 1):
                    M = np.float32([[1, 0, sign * off_px], [0, 1, 0]])
                    wf = cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT101).astype(np.float32)
                    wa = (cv2.warpAffine(fg_a[..., 0], M, (w, h)) * 0.82)[..., None]
                    base_f = base_f * (1.0 - wa) + wf * wa
                out_f = np.clip(base_f * (1.0 - fg_a) + frame.astype(np.float32) * fg_a, 0, 255).astype(np.uint8)
                for bt in p.get("beat_times", []):
                    if 0.0 <= (t_s - float(bt)) < 1.5 / fps:
                        out_f = np.clip(out_f.astype(np.float32) * 1.35 + 45.0, 0, 255).astype(np.uint8)

        elif effect == "flashlight_glow":
            assert segmenter is not None
            fg_a = segmenter.mask(frame, feather_px=9)
            dark_bg = (frame.astype(np.float32) * 0.16).astype(np.uint8)
            white_sil = np.clip(fg_a * 255.0, 0, 255).astype(np.uint8)
            white_bgr = np.repeat(white_sil, 3, axis=-1)
            bloom = cv2.GaussianBlur(white_bgr, (0, 0), sigmaX=18.0)
            out_f = np.clip(dark_bg.astype(np.float32) * (1.0 - fg_a) + white_bgr.astype(np.float32) + bloom.astype(np.float32) * 0.65, 0, 255).astype(np.uint8)

        elif effect == "datamosh_optical":
            # S06 / S10: Optical-flow P-frame melt + optional 16x16 macroblock corrupt
            cur_g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mosh_starts = p.get("mosh_times", [0.4])
            mosh_dur = float(p.get("mosh_dur_s", 1.4))
            active_mosh = any(float(ms) <= t_s < float(ms) + mosh_dur for ms in mosh_starts)
            if active_mosh and prev_gray is not None:
                if mosh_canvas is None:
                    mosh_canvas = frame.copy()
                hw, hh = max(64, w // 2), max(64, h // 2)
                fl = cv2.calcOpticalFlowFarneback(
                    cv2.resize(prev_gray, (hw, hh)),
                    cv2.resize(cur_g, (hw, hh)),
                    None, 0.5, 3, 15, 3, 5, 1.2, 0,
                )
                fl = cv2.resize(fl, (w, h), interpolation=cv2.INTER_LINEAR) * 2.1
                gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
                mosh_canvas = cv2.remap(
                    mosh_canvas, gx - fl[..., 0], gy - fl[..., 1],
                    interpolation=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP,
                )
                # S10 square 16x16 macroblock glitches
                out_f = mosh_canvas.copy()
                for _ in range(int(p.get("block_glitches", 14))):
                    bs = 16
                    bx = int(rng.integers(0, max(1, w - bs)))
                    by = int(rng.integers(0, max(1, h - bs)))
                    sx = int(np.clip(bx + rng.integers(-48, 49), 0, max(0, w - bs)))
                    sy = int(np.clip(by + rng.integers(-32, 33), 0, max(0, h - bs)))
                    out_f[by:by + bs, bx:bx + bs] = frame[sy:sy + bs, sx:sx + bs]
            else:
                mosh_canvas = None
                out_f = frame
            prev_gray = cur_g

        elif effect == "dither_1bit":
            out_f = frame_dither_1bit(
                frame,
                contrast=float(p.get("contrast", 1.35)),
                label=str(p.get("label", "")),
                label_hex=str(p.get("label_hex", "#D9C53B")),
            )

        elif effect == "risograph_2tone":
            out_f = frame_risograph_2tone(
                frame,
                dark_hex=str(p.get("dark_hex", "#1A2168")),
                light_hex=str(p.get("light_hex", "#CED8F7")),
                top_caption=str(p.get("top_caption", "")),
                bot_caption=str(p.get("bot_caption", "")),
                caption_hex=str(p.get("caption_hex", "#9E1B32")),
            )

        elif effect == "receipt_ticket":
            out_f = frame_receipt_ticket(frame, fi, fps, title=str(p.get("title", "MAKER STUDIO")))

        elif effect == "crt_phosphor":
            out_f = frame_crt_phosphor(
                frame,
                palette=str(p.get("palette", "cyan")),
                barrel_k=float(p.get("barrel_k", 0.0)),
            )

        elif effect == "bass_shockwave":
            beats = [float(b) for b in p.get("beat_times", [0.5, 1.5, 2.5])]
            wave_dur = float(p.get("wave_dur_s", 0.45))
            out_f = frame
            for bt in beats:
                if bt <= t_s < bt + wave_dur:
                    out_f = frame_bass_shockwave(out_f, (t_s - bt) / wave_dur, strength_px=float(p.get("strength_px", 28.0)))
                    break

        elif effect == "fight_club_shake":
            # S11 (@ediday.5): Track nose/eyes, lock face stationary at center while shaking + blurring room!
            assert face_detect is not None
            boxes = face_detect(frame)
            if boxes:
                cx, cy, _, _, _ = boxes[0]
                smooth_face_xy[0] = 0.72 * smooth_face_xy[0] + 0.28 * cx
                smooth_face_xy[1] = 0.72 * smooth_face_xy[1] + 0.28 * cy

            amp_x = float(p.get("shake_px", max(18.0, w * 0.032)))
            sx = amp_x * math.sin(fi * 1.85) + 0.45 * amp_x * math.cos(fi * 3.1)
            sy = 0.35 * amp_x * math.cos(fi * 2.3)
            rot = float(p.get("rot_deg", 1.8)) * math.sin(fi * 1.65)
            zoom = float(p.get("zoom", 1.18))

            # Pivot around tracked face `(fx_px, fy_px)` AND translate face to `(w/2, h/2)`!
            fx_px = smooth_face_xy[0] * w
            fy_px = smooth_face_xy[1] * h
            M = cv2.getRotationMatrix2D((fx_px, fy_px), rot, zoom)
            M[0, 2] += (w * 0.5 - fx_px) + sx * 0.12
            M[1, 2] += (h * 0.46 - fy_px) + sy * 0.12
            locked = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)

            # Violent horizontal motion-smear on outer background while keeping face center sharp!
            klen = max(5, int(abs(sx) * 0.65) | 1)
            kern = np.zeros((klen, klen), dtype=np.float32)
            kern[klen // 2, :] = 1.0 / klen
            M_bg = M.copy()
            M_bg[0, 2] += sx
            M_bg[1, 2] += sy
            shaken_bg = cv2.filter2D(
                cv2.warpAffine(frame, M_bg, (w, h), borderMode=cv2.BORDER_REFLECT101), -1, kern
            )
            yy, xx = np.ogrid[:h, :w]
            r_norm = np.sqrt(((xx - w * 0.5) / (w * 0.26)) ** 2 + ((yy - h * 0.46) / (h * 0.28)) ** 2)
            face_keep = np.clip(1.35 - r_norm, 0.0, 1.0).astype(np.float32)[..., None]
            comp = locked.astype(np.float32) * face_keep + shaken_bg.astype(np.float32) * (1.0 - face_keep)
            # Gritty 35mm Fight Club contrast + film grain
            grain = rng.normal(0.0, 11.0, size=(h, w, 1)).astype(np.float32)
            out_f = np.clip((comp - 118.0) * 1.16 + 115.0 + grain, 0, 255).astype(np.uint8)

        elif effect == "center_match_strobe":
            # S10 (@astroospace): Center focal bright mass + B&W pre-drop tension -> Full-Color explosion!
            drop_t = float(p.get("drop_s", 1.2))
            if t_s < drop_t:
                g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                out_f = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
            else:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
                hsv[..., 1] = np.clip(hsv[..., 1] * 1.45, 0, 255)
                hsv[..., 2] = np.clip(hsv[..., 2] * 1.15, 0, 255)
                vivid = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
                bloom = cv2.GaussianBlur(vivid, (0, 0), sigmaX=11.0)
                out_f = cv2.addWeighted(vivid, 0.84, bloom, 0.28, 0.0)
        else:
            raise ValueError(f"Unknown viral VFX effect: {effect}")

        enc.stdin.write(out_f.tobytes())
        fi += 1

    cap.release()
    if broll_cap is not None:
        broll_cap.release()
    if segmenter is not None:
        segmenter.close()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"FFmpeg encode failed during {effect}")

    # Remux original audio if present
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run([ffmpeg, "-hide_banner", "-i", str(in_mp4)], capture_output=True, text=True)
    has_audio = "Audio:" in probe.stderr
    if has_audio:
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "warning",
                "-i", str(vid_only), "-i", str(in_mp4),
                "-map", "0:v:0", "-map", "1:a:0?",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest",
                str(out_mp4),
            ],
            check=True,
        )
    else:
        shutil.copy2(vid_only, out_mp4)
    shutil.rmtree(work, ignore_errors=True)
    return {
        "effect": effect,
        "frames": fi,
        "resolution": f"{w}x{h}",
        "out_mp4": str(out_mp4),
        "size_mb": round(Path(out_mp4).stat().st_size / 1048576.0, 2),
    }


# ==============================================================================
# 4. JIGSAW MUSICAL GAP PLANNER + `18pt` SERIF SUBS (`S02` + `S04` @thisiszohair)
# ==============================================================================
def plan_jigsaw_music_pockets(
    music_path: str,
    min_gap_s: float = 0.50,
    rel_threshold_db: float = -5.5,
) -> list[dict[str, float]]:
    """Find low-vocal / instrumental pockets in `music_path` to weave story dialogue (`S04` rule)."""
    ffmpeg = get_ffmpeg()
    tmp_wav = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "error", "-i", str(music_path),
                "-af", "highpass=f=280,lowpass=f=3600",
                "-ar", "16000", "-ac", "1", tmp_wav,
            ],
            check=True,
        )
        audio, sr = sf.read(tmp_wav, dtype="float32")
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)

    hop = int(0.05 * sr)  # 50 ms windows
    n_w = len(audio) // hop
    if n_w < 4:
        return []
    rms = np.array([math.sqrt(float(np.mean(audio[i * hop:(i + 1) * hop] ** 2)) + 1e-12) for i in range(n_w)])
    med_db = 20.0 * math.log10(float(np.median(rms)) + 1e-9)
    db = 20.0 * np.log10(rms + 1e-9)

    is_pocket = db < (med_db + rel_threshold_db)
    pockets: list[dict[str, float]] = []
    start_i: int | None = None
    for idx, flag in enumerate(is_pocket):
        if flag and start_i is None:
            start_i = idx
        elif not flag and start_i is not None:
            dur = (idx - start_i) * 0.05
            if dur >= min_gap_s:
                pockets.append({
                    "start_s": round(start_i * 0.05, 2),
                    "end_s": round(idx * 0.05, 2),
                    "duration_s": round(dur, 2),
                    "depth_db": round(float(np.mean(db[start_i:idx]) - med_db), 1),
                })
            start_i = None
    if start_i is not None and (n_w - start_i) * 0.05 >= min_gap_s:
        pockets.append({
            "start_s": round(start_i * 0.05, 2),
            "end_s": round(n_w * 0.05, 2),
            "duration_s": round((n_w - start_i) * 0.05, 2),
            "depth_db": round(float(np.mean(db[start_i:]) - med_db), 1),
        })
    return pockets


def write_center_serif_ass(
    cues: list[dict[str, Any]],
    out_ass: str,
    width: int = 1080,
    height: int = 1920,
    font_size: int = 28,
) -> str:
    """Generate tiny dead-center cinematic serif `.ass` subtitles (`S02` @thisiszohair style)."""
    def _ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: CenterSerif,Playfair Display,{font_size},&H00FFFFFF,&H00FFFFFF,&H90000000,&H60000000,0,0,0,0,100,100,0.4,0,1,1.2,1.5,5,40,40,0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for c in cues:
        txt = str(c["text"]).replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{_ts(float(c['start_s']))},{_ts(float(c['end_s']))},CenterSerif,,0,0,0,,{{\\fad(60,80)}}{txt}")
    Path(out_ass).parent.mkdir(parents=True, exist_ok=True)
    Path(out_ass).write_text("\n".join(lines), encoding="utf-8")
    return str(out_ass)


# ==============================================================================
# 5. ZERO-FOOTAGE STILL-ILLUSTRATION MOTION EDIT (`S08` kevamarts "God's Wisdom")
# ==============================================================================
def render_still_art_edit(
    image_path: str,
    out_mp4: str,
    title_top: str = "GOD'S",
    title_main: str = "WISDOM",
    dur_s: float = 15.4,
    fps: int = 30,
    layout: str = "9:16_center_16:9",
) -> dict[str, Any]:
    """Turn a single static drawing/poster into a dynamic `kevamarts`-style edit (`S08`)."""
    from .ironman_edit import synthesize_clean_dark_edit_music

    ffmpeg = get_ffmpeg()
    src_img = cv2.imread(str(image_path))
    if src_img is None:
        raise RuntimeError(f"Cannot load image: {image_path}")

    if layout == "9:16_center_16:9":
        out_w, out_h = 1080, 1920
        vw, vh, vy0 = 1080, 608, 656
    else:
        out_w, out_h = 1920, 1080
        vw, vh, vy0 = 1920, 1080, 0

    base_art = cv2.resize(src_img, (vw, vh), interpolation=cv2.INTER_LANCZOS4)
    total_frames = int(round(dur_s * fps))
    flip_s = 2.10
    drop_s = 3.80

    work = Path(tempfile.mkdtemp(prefix="still_art_"))
    vid_only = work / "art_vid.mp4"
    enc = subprocess.Popen(
        [
            ffmpeg, "-y", "-v", "warning",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{out_w}x{out_h}", "-r", str(fps),
            "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
            str(vid_only),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None
    outer = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    rng = np.random.default_rng(88)

    # Pre-render title alpha masks (`title_top` + `title_main`)
    pil_m = Image.new("L", (vw, vh), 0)
    dr = ImageDraw.Draw(pil_m)
    f_top = _load_font(int(vh * 0.095), "Anton-Regular.ttf")
    f_big = _load_font(int(vh * 0.42), "Anton-Regular.ttf")
    bb1 = dr.textbbox((0, 0), title_top, font=f_top)
    bb2 = dr.textbbox((0, 0), title_main, font=f_big)
    dr.text(((vw - (bb1[2] - bb1[0])) // 2, int(vh * 0.14) - bb1[1]), title_top, fill=255, font=f_top)
    dr.text(((vw - (bb2[2] - bb2[0])) // 2, int(vh * 0.28) - bb2[1]), title_main, fill=255, font=f_big)
    title_a = (np.asarray(pil_m, dtype=np.float32) / 255.0)[..., None]

    yy, xx = np.meshgrid(np.linspace(-1.0, 1.0, vh), np.linspace(-1.0, 1.0, vw), indexing="ij")

    for fi in range(total_frames):
        t_s = fi / fps
        # Continuous handheld wiggle(6, 18)
        wx = 9.0 * math.sin(t_s * 17.0) + 5.0 * math.cos(t_s * 29.0)
        wy = 7.0 * math.cos(t_s * 19.0) + 4.0 * math.sin(t_s * 23.0)
        rot = 0.7 * math.sin(t_s * 13.0)

        if t_s < flip_s:
            # Darkened artwork + Crimson title (`#E50914`)
            dark = (base_art.astype(np.float32) * 0.18).astype(np.uint8)
            red_col = np.full((vh, vw, 3), (20, 9, 229), dtype=np.float32)
            inner = np.clip(dark.astype(np.float32) * (1.0 - title_a) + red_col * title_a, 0, 255).astype(np.uint8)
        elif t_s < drop_s:
            # 1-Frame Polarity Swap! Solid Crimson BG + Grunge `#FFFFFF` Title
            red_bg = np.full((vh, vw, 3), (20, 9, 229), dtype=np.float32)
            grunge = np.clip(245.0 - rng.uniform(0, 35, size=(vh, vw, 1)), 195, 255)
            inner = np.clip(red_bg * (1.0 - title_a) + grunge * title_a, 0, 255).astype(np.uint8)
        else:
            # Animated Still Artwork: slow push-in + rotating radial light sweep + glitch bars + duotone box swap!
            u = (t_s - drop_s) / max(0.2, dur_s - drop_s)
            zoom = 1.05 + 0.12 * u
            M = cv2.getRotationMatrix2D((vw * 0.5, vh * 0.5), rot, zoom)
            M[0, 2] += wx
            M[1, 2] += wy
            art_f = cv2.warpAffine(base_art, M, (vw, vh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101).astype(np.float32)

            # Rotating radial crown light flare peaking around u=0.55..0.68 (`10.2–11.2s` in S08)
            lx = 0.18 * math.cos(t_s * 2.2)
            ly = -0.18 + 0.10 * math.sin(t_s * 1.8)
            flare_amp = 75.0 + 135.0 * math.exp(-(((u - 0.60) / 0.11) ** 2))
            flare = flare_amp * np.exp(-((xx - lx) ** 2 + (yy - ly) ** 2) / 0.28)[..., None]
            art_f = np.clip(art_f + flare, 0, 255)

            # `125%` zoomed-invert horizontal glitch slice bars (`4f` bursts every ~2.4s)
            if int(t_s / 0.12) % 19 == 0:
                M_z = cv2.getRotationMatrix2D((vw * 0.5, vh * 0.5), 0.0, 1.25)
                inv_z = 255.0 - cv2.warpAffine(art_f, M_z, (vw, vh), borderMode=cv2.BORDER_REFLECT101)
                for _ in range(3):
                    gy = int(rng.integers(0, max(1, vh - 42)))
                    gh = int(rng.integers(16, 44))
                    art_f[gy:gy + gh] = inv_z[gy:gy + gh]

            # Center Red+Black Duotone Box Swap (`u in 0.68..0.77`, matching `11.82s` of S08!)
            if 0.68 <= u <= 0.77:
                luma = (0.114 * art_f[..., 0] + 0.587 * art_f[..., 1] + 0.299 * art_f[..., 2]) / 255.0
                duo = np.stack([luma * 22.0, luma * 28.0, 40.0 + luma * 215.0], axis=-1)
                inv_wings = 255.0 - art_f
                bx0, bx1 = int(vw * 0.26), int(vw * 0.74)
                out_box = inv_wings.copy()
                out_box[:, bx0:bx1] = duo[:, bx0:bx1]
                art_f = out_box

            inner = np.clip(art_f, 0, 255).astype(np.uint8)

        if t_s < drop_s:
            M_t = cv2.getRotationMatrix2D((vw * 0.5, vh * 0.5), rot * 0.5, 1.03)
            M_t[0, 2] += wx * 0.6
            M_t[1, 2] += wy * 0.6
            inner = cv2.warpAffine(inner, M_t, (vw, vh), borderMode=cv2.BORDER_REFLECT101)

        if layout == "9:16_center_16:9":
            outer.fill(0)
            outer[vy0:vy0 + vh, 0:vw] = inner
            enc.stdin.write(outer.tobytes())
        else:
            enc.stdin.write(inner.tobytes())

    enc.stdin.close()
    enc.wait()

    # Synthesize matching dark beat & mux
    sr = 48000
    music = synthesize_clean_dark_edit_music(
        total_dur_s=dur_s,
        drop_s=drop_s,
        beat_s=0.48,
        blackout_window=(drop_s - 0.16, drop_s),
        phrase_hits=[0.04, flip_s],
        sr=sr,
    )
    wav_p = work / "art_music.wav"
    sf.write(str(wav_p), music, sr, subtype="PCM_24")
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "warning",
            "-i", str(vid_only), "-i", str(wav_p),
            "-c:v", "copy", "-af", "loudnorm=I=-14.5:TP=-1.5:LRA=9",
            "-c:a", "aac", "-b:a", "224k", "-movflags", "+faststart", "-shortest",
            str(out_mp4),
        ],
        check=True,
    )
    shutil.rmtree(work, ignore_errors=True)
    return {
        "effect": "still_art_edit",
        "out_mp4": str(out_mp4),
        "layout": layout,
        "resolution": f"{out_w}x{out_h}",
        "duration_s": dur_s,
        "size_mb": round(Path(out_mp4).stat().st_size / 1048576.0, 2),
    }


def list_viral_vfx() -> list[dict[str, str]]:
    """Return catalog of all 16+ integrated viral edit tools & their source Sample blueprint."""
    return [
        {"id": "difference_velocity", "sample": "S07 (@technocraftss)", "desc": "Giant Difference-blend typography + 5f black strobes + optical-flow velocity montage"},
        {"id": "red_ribbon_roto", "sample": "S01 (@sumanth.mp4)", "desc": "B&W sky + angled crimson B-roll ribbon behind AI-rotoscoped silhouette + katana luma-invert flash"},
        {"id": "jigsaw_music_pockets", "sample": "S02+S04 (@thisiszohair)", "desc": "Finds low-energy song pockets for story dialogue + tiny 18pt center serif subs"},
        {"id": "risograph_2tone", "sample": "S03 (@_.raajjjjjj_)", "desc": "Indigo/Periwinkle 2-tone Risograph posterized print + crimson serif header/footer bars"},
        {"id": "dither_1bit", "sample": "S03 + S06", "desc": "8x8 Ordered Bayer 1-Bit monochrome stipple dithering + optional gold chest/center title"},
        {"id": "crt_phosphor", "sample": "S03 + S06", "desc": "Cyan CRT / Pink Phosphor / Curved Barrel-Lens TV (`palette=cyan|pink|indigo_tv`)"},
        {"id": "text_behind_subject", "sample": "S05 (@cashworthclipz)", "desc": "3D Z-depth giant solid or video-textured impact text behind AI-rotoscoped person"},
        {"id": "roto_clone_pop", "sample": "S05 + S09", "desc": "Beat-synced left/right roto clones (`offset_live`) OR 3 freeze-frame cutouts on black (`freeze_black`)"},
        {"id": "blob_tracking", "sample": "S06 (@marcelgrauu)", "desc": "TouchDesigner-style white bounding boxes + connecting web lines + coordinate chips (`k1sh0r/blob-tracker` MIT)"},
        {"id": "receipt_ticket", "sample": "S06 (@marcelgrauu)", "desc": "Crinkled thermal receipt paper + dithered video + live monospace receipt header & barcode"},
        {"id": "flashlight_glow", "sample": "S06 (@marcelgrauu)", "desc": "Glowing white phosphor human silhouette + bloom in darkness"},
        {"id": "datamosh_optical", "sample": "S06 + S10", "desc": "Optical-flow P-frame pixel melt + 16x16 square macroblock glitch without header corruption"},
        {"id": "still_art_edit", "sample": "S08 (kevamarts)", "desc": "Turns 1 static drawing/poster into a 15s edit (`1f` polarity flip + wiggle + radial light + glitch bars)"},
        {"id": "silhouette_double_exp", "sample": "S09 (@willrvail)", "desc": "Fast B-roll playing dynamically INSIDE dark AI-rotoscoped human silhouette over clean backdrop"},
        {"id": "bass_shockwave", "sample": "S09 (@willrvail)", "desc": "Propagating concentric radial refraction shockwave on 808/bass timestamps"},
        {"id": "center_match_strobe", "sample": "S10 (@astroospace)", "desc": "B&W pre-beat tension snapping into 145% vibrant color + glow bloom on drop"},
        {"id": "fight_club_shake", "sample": "S11 (@ediday.5)", "desc": "Nose/eye Match-Move Face-Locked Shake (face pinned still while background smears) + 35mm grain"},
    ]
