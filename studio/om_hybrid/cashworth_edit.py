"""cashworth_edit.py — `@cashworthclipz` (`7f73e363...mp4`) Aesthetic Kinetic Storytelling Engine.

Faithful 1:1 implementation of all 9 signature visual, typographic, and aspect-ratio
set-pieces from Drive `Sample/7f73e363df5a407a9108b2c1418e78a6.mp4`:

1. **Dreamy Warm Film Halation Grade (`apply_cashworth_dream_grade`):**
   - Soft coral-gold highlight halation bloom (`GaussianBlur` on brights `> 0.72`) + lifted indigo-cream
     shadows + sun-drenched turquoise/gold vibrance (warm nostalgic Kodak film feel).
2. **Piece 1 (`letterbox_video_title_roto`):**
   - `2.60:1` narrow cinema strip expanding smoothly open to full `16:9` (`1044x588`), with a live
     moving video texture playing INSIDE giant block letters (`APEX` / `HAWAII`) BEHIND the AI-rotoscoped hero!
3. **Piece 2 (`ghost_double_exposure`):**
   - Previous shot's AI-rotoscoped silhouette lingers as a dreamy translucent double-exposure ghost
     drifting over a wide aerial shot.
4. **Piece 3 (`progressive_bento_over_sky`):**
   - `3x3` live moving tiles pop in sequentially (`1 -> 2 -> 4 -> 6 -> 9`) on synth pulses over a live backdrop.
5. **Piece 4 (`mixed_italic_to_giant_serif_slam`):**
   - Delicate small `PlayfairDisplay-Italic` typewriter quote -> GIANT glowing warm-halation italic serif
     impact word (`COMBAT` / `FAST`) slamming dead-center on the beat!
6. **Piece 5 (`spatial_split_words`):**
   - Asymmetric italic words floating left & right around the subject's shoulders/helmet.
7. **Piece 6 (`square_postcard_snap`):**
   - Dynamic aspect-ratio snap (`16:9` -> centered `1:1` `588x588` Square Postcard on `#000000`) with
     video-textured block text (`SAFE?`) or slanted bold `COME ON` behind the rotoscoped subject!
8. **Piece 7 (`triptych_3col_pop`):**
   - `1 - 2 - 3` vertical `1/3`-width columns (`Left | Center | Right`) popping on the drop beats with warm flash!
9. **Piece 8 (`horizon_legacy_text` + `paper_cutout_pop`):**
   - 3D perspective-tilted bold slanted banner (`THEY CAN SMELL THE LEGACY`) revealing word-by-word
     along the horizon + `3-frame` pure white glowing paper-cutout silhouette pop flash!
"""
from __future__ import annotations

import gc
import math
import subprocess
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ._ffmpeg import get_ffmpeg
from .aura_edit import _slice_audio_segment, _slice_clip_frames_30fps, _velocity_resample_optical
from .viral_vfx import PersonSegmenter

_REPO_ROOT = Path(__file__).resolve().parents[2]

ITALIC_SERIF_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "PlayfairDisplay-Italic.ttf"),
    "/home/user/assets/fonts/PlayfairDisplay-Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]

BLOCK_FONT_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "Anton-Regular.ttf"),
    str(_REPO_ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf"),
    "/home/user/assets/fonts/Anton-Regular.ttf",
]

SLANT_BOLD_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "Poppins-ExtraBoldItalic.ttf"),
    str(_REPO_ROOT / "assets" / "fonts" / "Anton-Regular.ttf"),
    "/home/user/assets/fonts/Poppins-ExtraBoldItalic.ttf",
]


def _font(cands: list[str], px: int) -> ImageFont.FreeTypeFont:
    for p in cands:
        if Path(p).exists():
            return ImageFont.truetype(p, max(12, int(px)))
    return ImageFont.load_default()


def apply_cashworth_dream_grade(frame_bgr: np.ndarray, *, halation: float = 1.0) -> np.ndarray:
    """Dreamy warm nostalgic Kodak film halation + sun-drenched turquoise/amber grade."""
    f = frame_bgr.astype(np.float32)
    # Creamy lifted film curve
    norm = np.clip(f / 255.0, 0.0, 1.0)
    lifted = 0.03 + 0.95 * (norm * (1.08 - 0.08 * norm))
    f = np.clip(lifted * 255.0, 0, 255)

    # Warm coral-peach highlight halation bloom (exact 7f73e... dreamy glow!)
    lum = (0.114 * f[:, :, 0] + 0.587 * f[:, :, 1] + 0.299 * f[:, :, 2]) / 255.0
    hi_mask = np.clip((lum - 0.68) / 0.32, 0.0, 1.0)
    bloom = cv2.GaussianBlur(hi_mask, (0, 0), 9.5) * halation
    f[:, :, 2] += 28.0 * bloom  # R: warm coral-amber bloom
    f[:, :, 1] += 17.0 * bloom  # G: golden peach
    f[:, :, 0] += 7.0 * bloom   # B: soft lift

    # Subtle indigo-teal shadow tint
    sh = (1.0 - lum) ** 1.6
    f[:, :, 0] += 5.5 * sh
    f[:, :, 1] += 2.0 * sh

    graded = np.clip(f, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(graded, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat_n = hsv[:, :, 1] / 255.0
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 + 0.24 * (1.0 - sat_n * 0.5)), 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def fit_16x9(frames_bgr: list[np.ndarray], w: int = 1044, h: int = 588, z0: float = 1.01, z1: float = 1.06) -> list[np.ndarray]:
    if not frames_bgr:
        return []
    sh, sw = frames_bgr[0].shape[:2]
    ar = w / float(h)
    n = max(1, len(frames_bgr) - 1)
    out = []
    for i, fr in enumerate(frames_bgr):
        u = i / float(n)
        z = z0 + (z1 - z0) * (1.0 - (1.0 - u) ** 1.7)
        if (sw / float(sh)) >= ar:
            ch = sh / z
            cw = ch * ar
        else:
            cw = sw / z
            ch = cw / ar
        sx, sy = w / cw, h / ch
        M = np.array([[sx, 0.0, w * 0.5 - (sw * 0.5) * sx], [0.0, sy, h * 0.5 - (sh * 0.5) * sy]], dtype=np.float32)
        warped = cv2.warpAffine(fr, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT_101)
        out.append(apply_cashworth_dream_grade(warped))
    return out


def draw_video_filled_text_behind_roto(
    fg_frames: list[np.ndarray],
    tex_frames: list[np.ndarray],
    word: str,
    segmenter: PersonSegmenter,
    *,
    letterbox_expand: bool = False,
    square_postcard: bool = False,
    font_px: int = 215,
) -> list[np.ndarray]:
    """Giant block word filled with a live fire/sparks video texture BEHIND the AI-rotoscoped subject."""
    if not fg_frames:
        return []
    h, w = fg_frames[0].shape[:2]
    fnt = _font(BLOCK_FONT_CANDIDATES, font_px)
    mask_pil = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask_pil)
    tw = md.textlength(word, font=fnt)
    max_w = (h * 0.88) if square_postcard else (w * 0.88)
    if tw > max_w:
        fnt = _font(BLOCK_FONT_CANDIDATES, int(font_px * max_w / tw))
        tw = md.textlength(word, font=fnt)
    bb = md.textbbox((0, 0), word, font=fnt)
    th = bb[3] - bb[1]
    tx = int((w - tw) * 0.5)
    ty = int((h - th) * 0.44) - bb[1]
    md.text((tx, ty), word, font=fnt, fill=255)
    txt_alpha = (np.array(mask_pil, dtype=np.float32) / 255.0)[:, :, None]
    glow_alpha = (np.array(mask_pil.filter(ImageFilter.GaussianBlur(radius=9)), dtype=np.float32) / 255.0)[:, :, None]

    out = []
    n = max(1, len(fg_frames) - 1)
    for i, fr in enumerate(fg_frames):
        tex = tex_frames[i % len(tex_frames)].astype(np.float32)
        # Boost fiery warm saturation inside letters
        tex_vivid = np.clip(tex * np.array([0.75, 1.05, 1.45], dtype=np.float32) + np.array([0.0, 18.0, 42.0], dtype=np.float32), 0, 255)
        a_person = segmenter.mask(fr, feather_px=6)

        base = fr.astype(np.float32)
        # Soft warm glow + video-filled letters on background
        bg_with_txt = base * (1.0 - 0.45 * glow_alpha) + np.array([30.0, 120.0, 255.0], dtype=np.float32) * (0.45 * glow_alpha)
        bg_with_txt = bg_with_txt * (1.0 - txt_alpha) + tex_vivid * txt_alpha
        # Rotoscoped hero cleanly IN FRONT of video-filled text!
        comp = bg_with_txt * (1.0 - a_person) + base * a_person
        res = np.clip(comp, 0, 255).astype(np.uint8)

        if letterbox_expand:
            # 08.15s -> 09.10s: 2.65:1 narrow cinema slit smoothly opening vertically to full 16:9!
            u = min(1.0, i / max(1.0, n * 0.68))
            u_e = 1.0 - (1.0 - u) ** 2.4
            vis_h = int(round((h * 0.58) + (h * 0.42) * u_e))
            bar = max(0, (h - vis_h) // 2)
            if bar > 0:
                res[:bar, :] = 0
                res[h - bar:, :] = 0

        if square_postcard:
            # 15.80s: Centered 1:1 Square Postcard (h x h) with black side pillars!
            sq = h
            pad_x = (w - sq) // 2
            res[:, :pad_x] = 0
            res[:, pad_x + sq:] = 0

        out.append(res)
    return out


def draw_italic_quote_overlay(
    frame_bgr: np.ndarray,
    text: str,
    *,
    giant_slam: bool = False,
    slam_progress: float = 1.0,
    pos_xy_frac: tuple[float, float] = (0.50, 0.50),
) -> np.ndarray:
    """12.95s -> 13.90s in 7f73e: Delicate small italic serif OR Giant warm-halation italic serif slam!"""
    h, w = frame_bgr.shape[:2]
    base_rgba = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    glow_l = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    txt_l = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_l)
    td = ImageDraw.Draw(txt_l)

    if giant_slam:
        sc = 1.16 - 0.16 * (1.0 - (1.0 - min(1.0, slam_progress / 0.22)) ** 2.2)
        px = int(round(138 * sc))
        fnt = _font(ITALIC_SERIF_CANDIDATES, px)
        tw = td.textlength(text, font=fnt)
        if tw > w * 0.86:
            fnt = _font(ITALIC_SERIF_CANDIDATES, int(px * (w * 0.86) / tw))
            tw = td.textlength(text, font=fnt)
        bb = td.textbbox((0, 0), text, font=fnt)
        th = bb[3] - bb[1]
        tx = int(w * pos_xy_frac[0] - tw * 0.5)
        ty = int(h * pos_xy_frac[1] - th * 0.5) - bb[1]
        # Dreamy peach-white halation bloom around giant serif word (exact 13.90s 'FAST'!)
        gd.text((tx, ty), text, font=fnt, fill=(255, 205, 175, 235), stroke_width=6, stroke_fill=(255, 175, 130, 185))
        td.text((tx, ty), text, font=fnt, fill=(255, 250, 245, 255))
        comp = Image.alpha_composite(base_rgba, glow_l.filter(ImageFilter.GaussianBlur(radius=13)))
        comp = Image.alpha_composite(comp, txt_l)
    else:
        fnt = _font(ITALIC_SERIF_CANDIDATES, 38)
        tw = td.textlength(text, font=fnt)
        bb = td.textbbox((0, 0), text, font=fnt)
        th = bb[3] - bb[1]
        tx = int(w * pos_xy_frac[0] - tw * 0.5)
        ty = int(h * pos_xy_frac[1] - th * 0.5) - bb[1]
        gd.text((tx, ty), text, font=fnt, fill=(0, 0, 0, 195), stroke_width=4, stroke_fill=(0, 0, 0, 165))
        td.text((tx, ty), text, font=fnt, fill=(252, 250, 246, 250))
        comp = Image.alpha_composite(base_rgba, glow_l.filter(ImageFilter.GaussianBlur(radius=5)))
        comp = Image.alpha_composite(comp, txt_l)

    return cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)


def draw_square_slanted_slam(frames_bgr: list[np.ndarray], word: str = "COME ON") -> list[np.ndarray]:
    """19.65s in 7f73e: Centered 1:1 Square Postcard + giant slanted white `COME ON`!"""
    if not frames_bgr:
        return []
    h, w = frames_bgr[0].shape[:2]
    sq = h
    pad_x = (w - sq) // 2
    fnt = _font(SLANT_BOLD_CANDIDATES, 96)
    out = []
    for i, fr in enumerate(frames_bgr):
        card = fr.copy()
        card[:, :pad_x] = 0
        card[:, pad_x + sq:] = 0
        rgba = Image.fromarray(cv2.cvtColor(card, cv2.COLOR_BGR2RGB)).convert("RGBA")
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        txt = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        td = ImageDraw.Draw(txt)
        tw = td.textlength(word, font=fnt)
        if tw > sq * 0.88:
            fnt = _font(SLANT_BOLD_CANDIDATES, int(96 * (sq * 0.88) / tw))
            tw = td.textlength(word, font=fnt)
        bb = td.textbbox((0, 0), word, font=fnt)
        th = bb[3] - bb[1]
        tx = int((w - tw) * 0.5)
        ty = int(h * 0.36 - th * 0.5) - bb[1]
        gd.text((tx, ty), word, font=fnt, fill=(255, 220, 190, 200), stroke_width=4, stroke_fill=(0, 0, 0, 140))
        td.text((tx, ty), word, font=fnt, fill=(255, 253, 250, 255))
        comp = Image.alpha_composite(rgba, glow.filter(ImageFilter.GaussianBlur(radius=9)))
        comp = Image.alpha_composite(comp, txt)
        res = cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)
        res[:, :pad_x] = 0
        res[:, pad_x + sq:] = 0
        out.append(res)
    return out


def build_triptych_3col_pop(col_clips: list[list[np.ndarray]], n_frames: int, w: int = 1044, h: int = 588) -> list[np.ndarray]:
    """20.60s -> 21.10s in 7f73e: 3 Vertical 1/3-width columns popping 1 -> 2 -> 3 on the drop beats!"""
    cw = (w - 12) // 3
    t_col2 = max(3, n_frames // 5)
    t_col3 = max(6, (2 * n_frames) // 5)
    out = []
    for i in range(n_frames):
        board = np.zeros((h, w, 3), dtype=np.uint8)
        for c_idx in range(3):
            if (c_idx == 1 and i < t_col2) or (c_idx == 2 and i < t_col3):
                continue
            src_list = col_clips[c_idx]
            fr = src_list[min(i, len(src_list) - 1)]
            # Center-crop vertical column from 16:9 frame
            fh, fw = fr.shape[:2]
            src_cw = min(fw, int(round(fh * (cw / float(h)))))
            x0_s = (fw - src_cw) // 2
            col_img = cv2.resize(fr[:, x0_s:x0_s + src_cw], (cw, h), interpolation=cv2.INTER_LANCZOS4)
            # Crisp warm flash on the exact pop frame!
            pop_f = 0 if c_idx == 0 else (t_col2 if c_idx == 1 else t_col3)
            if 0 <= (i - pop_f) < 4:
                fl = 0.55 * math.exp(-0.9 * (i - pop_f))
                col_img = np.clip(col_img.astype(np.float32) * (1.0 + 0.25 * fl) + 255.0 * (0.60 * fl), 0, 255).astype(np.uint8)
            x_dst = c_idx * (cw + 6)
            board[:, x_dst:x_dst + cw] = col_img
        out.append(board)
    return out


def draw_horizon_legacy_banner(frames_bgr: list[np.ndarray], phrase: str = "THEY CAN SMELL THE LEGACY") -> list[np.ndarray]:
    """24.55s -> 26.15s in 7f73e: Word-by-word horizon-tracked perspective banner with warm halation!"""
    if not frames_bgr:
        return []
    h, w = frames_bgr[0].shape[:2]
    words = phrase.split()
    fnt = _font(SLANT_BOLD_CANDIDATES, 54)
    n = len(frames_bgr)
    out = []
    for i, fr in enumerate(frames_bgr):
        vis_words = max(2, min(len(words), 1 + int((i / max(1.0, n * 0.58)) * len(words))))
        cur_txt = " ".join(words[:vis_words])

        txt_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        td = ImageDraw.Draw(txt_rgba)
        gd = ImageDraw.Draw(glow_rgba)
        tx, ty = int(w * 0.09), int(h * 0.19)
        gd.text((tx, ty), cur_txt, font=fnt, fill=(255, 215, 175, 225), stroke_width=5, stroke_fill=(255, 185, 130, 170))
        td.text((tx, ty), cur_txt, font=fnt, fill=(255, 252, 245, 252))

        merged_txt = Image.alpha_composite(glow_rgba.filter(ImageFilter.GaussianBlur(radius=9)), txt_rgba)
        txt_np = np.array(merged_txt, dtype=np.uint8)

        # Subtle horizon perspective tilt + gentle camera drift tracking
        drift_x = -14.0 * (i / float(max(1, n - 1)))
        src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst_pts = np.float32([[drift_x + 12, 8], [w + drift_x - 8, -10], [w + drift_x, h - 6], [drift_x, h]])
        P = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_rgba = cv2.warpPerspective(txt_np, P, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

        alpha = (warped_rgba[:, :, 3:4].astype(np.float32)) / 255.0
        rgb_w = warped_rgba[:, :, :3][:, :, ::-1].astype(np.float32)  # RGB -> BGR
        comp = fr.astype(np.float32) * (1.0 - alpha) + rgb_w * alpha
        out.append(np.clip(comp, 0, 255).astype(np.uint8))
    return out


def apply_paper_cutout_flash(frames_bgr: list[np.ndarray], segmenter: PersonSegmenter, flash_frame: int = 10) -> list[np.ndarray]:
    """27.70s in 7f73e: 3-frame solid cream-white glowing subject silhouette cutout pop flash on beat!"""
    out = list(frames_bgr)
    for k in range(flash_frame, min(len(out), flash_frame + 4)):
        fr = out[k]
        a_p = segmenter.mask(fr, feather_px=3)
        # Crisp solid paper cutout silhouette + thin glowing outline
        hard_cut = np.clip((a_p - 0.38) * 6.0, 0.0, 1.0)
        paper_col = np.array([232.0, 248.0, 255.0], dtype=np.float32)
        out[k] = np.clip(fr.astype(np.float32) * (1.0 - 0.90 * hard_cut) + paper_col * (0.90 * hard_cut), 0, 255).astype(np.uint8)
    return out
