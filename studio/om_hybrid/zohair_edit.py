"""zohair_edit.py — Style 1 (`@thisiszohair` `S02`+`S04` + Drive `Sample` `S01..S10` Pro VFX) Engine.

Combines `@thisiszohair`'s exact Jigsaw Vocal-Song Pocket Rhythm architecture (`65460EFC...mov` + `7f2...mp4`)
with the full arsenal of non-plain visual effects from the Drive `Sample` collection (`a4b9dd5d...mp4`,
`S01`, `S05`, `S07`, `S08`, `S09`, `S10`):

1. **Exact Visual Canvas & Rounded `16:9` Cinema Card (`1080x1920` @ `30fps`):**
   - Pure `#000000` portrait canvas (`1080x1920`) with centered `1036x584` (`16:9`) `24px` rounded card.
   - Top-right minimalist live countdown timer (`0:24 -> 0:00`) + dead-center `Playfair Display` editorial
     serif subtitles (`29px` mixed-case) during the sparse Jigsaw dialogue pockets.

2. **8 Non-Plain Pro Drive-Sample VFX & Transition Modes (Zero Flat/Plain Cuts!):**
   - `transition_in`: `"whip_zoom"` | `"whip_left"` | `"whip_right"` | `"flash_gold"` | `"flash_white"` | `"invert_2f"`
   - `vel_curve`: Farneback Optical-Flow `2.7x -> 0.36x` smooth velocity speed-ramp (`S07` + `S09`)
   - `vfx="masking_hook_flash"`: AI-roto foreground + `2f` saffron/crimson & white aura strobes (`a4b...` #1 + `S08`)
   - `vfx="z_depth_text"`: Giant glowing 3D hero title (`RAMA`, `AVATAR`) BEHIND AI-rotoscoped actor (`S05`)
   - `vfx="roto_clones"`: Beat-pop `1-2-3` left/right AI-rotoscoped hero clones + `1f` flashes (`a4b...` #4 + `S05`)
   - `vfx="difference_text"`: True mathematical `Blending Mode: DIFFERENCE` (`|255 - BaseRGB|`) slam (`S07`)
   - `vfx="bento_3x3"`: Live 9-tile moving `3x3` Bento Grid popping in on beats -> `zoom_through` center (`S05`)
   - `vfx="bw_tension"` & `vfx="divine_shockwave"`: Monochrome B&W pre-drop -> `138%` color + radial bass wave (`S10` + `S09`)

3. **Authentic Vocal-Song + Sparse Natural-Pocket Jigsaw Audio (`A1` + `A2` + `A3`):**
   - Designed for a REAL vocal anthem where 80%+ of the timeline plays at `0.0 dB` untouched studio power,
     weaving only 3–4 crystal-clear `HDemucs` lines into natural vocal pauses with silky `130ms` Premiere cosine ramps.
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ._ffmpeg import get_ffmpeg
from .aura_edit import _slice_audio_segment, _slice_clip_frames_30fps, _velocity_resample_optical
from .ironman_edit import isolate_clean_vocal_slice
from .viral_vfx import PersonSegmenter

_REPO_ROOT = Path(__file__).resolve().parents[2]

SERIF_FONT_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "PlayfairDisplay-Regular.ttf"),
    "/home/user/assets/fonts/PlayfairDisplay-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]

SANS_FONT_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "Inter-Regular.ttf"),
    "/home/user/assets/fonts/Inter-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

IMPACT_FONT_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf"),
    str(_REPO_ROOT / "assets" / "fonts" / "Anton-Regular.ttf"),
    "/home/user/assets/fonts/ArchivoBlack-Regular.ttf",
    "/home/user/assets/fonts/Anton-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(candidates: list[str], px: int) -> ImageFont.FreeTypeFont:
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def _hex_bgr(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return b, g, r


def _build_rounded_mask_3ch(w: int, h: int, radius: int = 24) -> np.ndarray:
    ss = 4
    img = Image.new("L", (w * ss, h * ss), 0)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=radius * ss, fill=255)
    img_small = img.resize((w, h), Image.Resampling.LANCZOS)
    return (np.array(img_small, dtype=np.float32) / 255.0)[:, :, None]


def _trim_and_fit_16x9_card(
    frames_bgr: list[np.ndarray],
    card_w: int = 1036,
    card_h: int = 584,
    zoom_start: float = 1.01,
    zoom_end: float = 1.07,
    cy_bias: float = 0.50,
    dark_lift: bool = True,
    sat_mult: float = 1.12,
) -> list[np.ndarray]:
    """Strip baked-in 2.39:1 black bars and fit cleanly into `1036x584` (`16:9`) card with smooth push/pull."""
    if not frames_bgr:
        return []
    h0, w0 = frames_bgr[0].shape[:2]
    probe_idxs = sorted(set([0, len(frames_bgr) // 2, len(frames_bgr) - 1]))
    row_max = np.zeros(h0, dtype=np.float32)
    for pidx in probe_idxs:
        g = cv2.cvtColor(frames_bgr[pidx], cv2.COLOR_BGR2GRAY)
        row_max = np.maximum(row_max, np.percentile(g[:, int(w0 * 0.22):int(w0 * 0.78)], 92, axis=1))
    max_trim = int(h0 * 0.28)
    yt = 0
    while yt < max_trim and row_max[yt] < 15.0:
        yt += 1
    yb = h0
    while (h0 - yb) < max_trim and row_max[yb - 1] < 15.0:
        yb -= 1
    if (yt > 4 or (h0 - yb) > 4) and (yb - yt) >= int(h0 * 0.44):
        frames_bgr = [fr[yt:yb, :] for fr in frames_bgr]

    sh, sw = frames_bgr[0].shape[:2]
    target_ar = card_w / float(card_h)
    n = max(1, len(frames_bgr) - 1)
    out: list[np.ndarray] = []

    for i, fr in enumerate(frames_bgr):
        u = i / float(n)
        # Smooth ease-out camera push/pull so every cut feels alive
        u_ease = 1.0 - (1.0 - u) ** 1.8
        z = zoom_start + (zoom_end - zoom_start) * u_ease
        if (sw / float(sh)) >= target_ar:
            crop_h = sh / z
            crop_w = crop_h * target_ar
        else:
            crop_w = sw / z
            crop_h = crop_w / target_ar
        cx = sw * 0.5
        cy = float(np.clip(sh * cy_bias, crop_h * 0.5, sh - crop_h * 0.5))
        sx = card_w / crop_w
        sy = card_h / crop_h
        M = np.array([[sx, 0.0, card_w * 0.5 - cx * sx], [0.0, sy, card_h * 0.5 - cy * sy]], dtype=np.float32)
        warped = cv2.warpAffine(fr, M, (card_w, card_h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT_101)

        f = warped.astype(np.float32)
        if dark_lift and float(np.mean(f)) < 30.0:
            f = (np.clip(f / 255.0, 0.0, 1.0) ** 0.84) * 255.0
        blur = cv2.GaussianBlur(f, (0, 0), 1.05)
        f = f + 0.40 * (f - blur)
        graded = np.clip(f, 0, 255).astype(np.uint8)
        if abs(sat_mult - 1.0) > 0.02:
            hsv = cv2.cvtColor(graded, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_mult, 0, 255)
            graded = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        out.append(graded)
    return out


def _apply_entry_transition(frames: list[np.ndarray], mode: str) -> list[np.ndarray]:
    """Apply crisp AE-style entry motion transition across the first 3–5 frames of a cut."""
    if not frames or not mode or mode == "none":
        return frames
    h, w = frames[0].shape[:2]
    cx, cy = w * 0.5, h * 0.5
    out = list(frames)

    if mode == "whip_zoom":
        for i in range(min(5, len(out))):
            decay = math.exp(-0.95 * i)
            s = 1.0 + 0.24 * decay
            M = np.array([[s, 0.0, (1.0 - s) * cx], [0.0, s, (1.0 - s) * cy]], dtype=np.float32)
            z_fr = cv2.warpAffine(out[i], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
            if i < 2:
                s2 = 1.0 + 0.34 * decay
                M2 = np.array([[s2, 0.0, (1.0 - s2) * cx], [0.0, s2, (1.0 - s2) * cy]], dtype=np.float32)
                z_fr2 = cv2.warpAffine(out[i], M2, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
                z_fr = cv2.addWeighted(z_fr, 0.62, z_fr2, 0.38, 0.0)
            out[i] = z_fr

    elif mode in ("whip_left", "whip_right"):
        sign = -1.0 if mode == "whip_left" else 1.0
        for i in range(min(4, len(out))):
            decay = math.exp(-1.1 * i)
            dx = sign * 150.0 * decay
            M = np.array([[1.04, 0.0, (1.0 - 1.04) * cx + dx], [0.0, 1.04, (1.0 - 1.04) * cy]], dtype=np.float32)
            slid = cv2.warpAffine(out[i], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
            ksize = max(3, int(round(25 * decay)) | 1)
            if ksize >= 5:
                kern = np.zeros((1, ksize), dtype=np.float32)
                kern[0, :] = 1.0 / ksize
                slid = cv2.filter2D(slid, -1, kern)
            out[i] = slid

    elif mode == "flash_white":
        for i in range(min(4, len(out))):
            fl = 0.58 * math.exp(-0.95 * i)
            out[i] = np.clip(out[i].astype(np.float32) * (1.0 + 0.25 * fl) + 255.0 * (0.65 * fl), 0, 255).astype(np.uint8)

    elif mode == "flash_gold":
        gold = np.array([45.0, 165.0, 255.0], dtype=np.float32)  # BGR warm divine saffron-gold
        for i in range(min(5, len(out))):
            fl = 0.56 * math.exp(-0.85 * i)
            out[i] = np.clip(out[i].astype(np.float32) * (1.0 - 0.35 * fl) + gold * (0.72 * fl), 0, 255).astype(np.uint8)

    elif mode == "invert_2f":
        # S01 & a4b... iconic 2-frame luma/color negative impact flash!
        for i in range(min(2, len(out))):
            inv = 255 - out[i]
            out[i] = cv2.addWeighted(inv, 0.85, out[i], 0.15, 0.0)
        if len(out) > 2:
            out[2] = np.clip(out[2].astype(np.float32) * 1.18 + 30.0, 0, 255).astype(np.uint8)

    return out


def _apply_clip_vfx(
    frames: list[np.ndarray],
    vfx: str,
    vc: dict[str, Any],
    segmenter: PersonSegmenter,
    bento_tiles: list[list[np.ndarray]] | None = None,
) -> list[np.ndarray]:
    """Execute Drive `Sample` (`S01..S10` + `a4b...`) non-plain visual effects on a 16:9 card clip."""
    if not frames or not vfx or vfx == "none":
        return frames
    h, w = frames[0].shape[:2]

    if vfx == "masking_hook_flash":
        # a4b... #1 ('sick masking hook with red/gold and white flashes' behind AI-roto hero!)
        out = []
        saffron_bg = np.full((h, w, 3), _hex_bgr(vc.get("accent_hex", "#FF5500")), dtype=np.float32)
        white_bg = np.full((h, w, 3), (250.0, 248.0, 255.0), dtype=np.float32)
        for i, fr in enumerate(frames):
            if i in (1, 2, 7, 8, 14, 15):
                a3 = segmenter.mask(fr, feather_px=5)
                bg_flash = white_bg if (i in (2, 14)) else saffron_bg
                blended_bg = 0.72 * bg_flash + 0.28 * fr.astype(np.float32)
                comp = blended_bg * (1.0 - a3) + fr.astype(np.float32) * a3
                out.append(np.clip(comp, 0, 255).astype(np.uint8))
            else:
                out.append(fr)
        return out

    if vfx == "z_depth_text":
        # S05 (@cashworthclipz) giant glowing 3D title BEHIND AI-rotoscoped hero!
        title = str(vc.get("vfx_text", "RAMA")).upper()
        accent_hex = str(vc.get("accent_hex", "#FFB020"))
        ab, ag, ar = _hex_bgr(accent_hex)
        fnt = _load_font(IMPACT_FONT_CANDIDATES, int(vc.get("font_px", 168)))
        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        tw = dummy.textlength(title, font=fnt)
        if tw > w * 0.88:
            fnt = _load_font(IMPACT_FONT_CANDIDATES, int(168 * (w * 0.88) / tw))
            tw = dummy.textlength(title, font=fnt)
        tx = int((w - tw) * 0.5)
        ty = int(h * float(vc.get("text_y_frac", 0.14)))

        glow_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        fg_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_img)
        fd = ImageDraw.Draw(fg_img)
        gd.text((tx, ty), title, font=fnt, fill=(ar, ag, ab, 240), stroke_width=8, stroke_fill=(ar, ag, ab, 195))
        for d in range(7, 0, -2):
            fd.text((tx + d, ty + d), title, font=fnt, fill=(25, 12, 4, 200))
        fd.text((tx, ty), title, font=fnt, fill=(255, 246, 224, 252))
        glow_blurred = glow_img.filter(ImageFilter.GaussianBlur(radius=14))

        out = []
        for i, fr in enumerate(frames):
            a3 = segmenter.mask(fr, feather_px=6)
            base = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert("RGBA")
            with_t = Image.alpha_composite(base, glow_blurred)
            with_t = Image.alpha_composite(with_t, fg_img)
            bg_bgr = cv2.cvtColor(np.array(with_t.convert("RGB")), cv2.COLOR_RGB2BGR).astype(np.float32)
            # Hero silhouette passes cleanly IN FRONT of the giant 3D text!
            comp = bg_bgr * (1.0 - a3) + fr.astype(np.float32) * a3
            out.append(np.clip(comp, 0, 255).astype(np.uint8))
        return out

    if vfx == "roto_clones":
        # a4b... #4 & S05: Beat-pop 1-2-3 Left & Right AI-rotoscoped hero clones with 1f micro-flashes!
        out = []
        n = len(frames)
        t1 = max(2, n // 4)
        t2 = max(4, n // 2)
        for i, fr in enumerate(frames):
            if i < t1:
                out.append(fr)
                continue
            a3 = segmenter.mask(fr, feather_px=5)
            base = fr.astype(np.float32)
            # Left clone (-170px)
            M_l = np.array([[1.0, 0.0, -170.0], [0.0, 1.0, 0.0]], dtype=np.float32)
            fr_l = cv2.warpAffine(base, M_l, (w, h), borderMode=cv2.BORDER_CONSTANT)
            a_l = cv2.warpAffine(a3, M_l, (w, h), borderMode=cv2.BORDER_CONSTANT)[:, :, None] if a3.ndim == 2 else cv2.warpAffine(a3, M_l, (w, h), borderMode=cv2.BORDER_CONSTANT)
            if a_l.ndim == 2:
                a_l = a_l[:, :, None]
            comp = base * (1.0 - 0.82 * a_l) + fr_l * (0.82 * a_l)

            if i >= t2:
                # Right clone (+170px)
                M_r = np.array([[1.0, 0.0, 170.0], [0.0, 1.0, 0.0]], dtype=np.float32)
                fr_r = cv2.warpAffine(base, M_r, (w, h), borderMode=cv2.BORDER_CONSTANT)
                a_r = cv2.warpAffine(a3, M_r, (w, h), borderMode=cv2.BORDER_CONSTANT)
                if a_r.ndim == 2:
                    a_r = a_r[:, :, None]
                comp = comp * (1.0 - 0.82 * a_r) + fr_r * (0.82 * a_r)

            # Center hero always strictly on top!
            comp = comp * (1.0 - a3) + base * a3
            if i in (t1, t2):
                comp = comp * 1.18 + 38.0  # crisp 1f beat-pop flash!
            out.append(np.clip(comp, 0, 255).astype(np.uint8))
        return out

    if vfx == "difference_text":
        # S07 (@technocraftss) True mathematical Blending Mode: DIFFERENCE (|255 - BaseRGB|)!
        word = str(vc.get("vfx_text", "DHARMA")).upper()
        out = []
        for i, fr in enumerate(frames):
            u = min(1.0, i / 5.0)
            scale = 1.15 - 0.15 * (1.0 - (1.0 - u) ** 2.2)
            px = int(round(138 * scale))
            fnt = _load_font(IMPACT_FONT_CANDIDATES, px)
            mask_img = Image.new("L", (w * 2, h * 2), 0)
            md = ImageDraw.Draw(mask_img)
            tw = md.textlength(word, font=_load_font(IMPACT_FONT_CANDIDATES, px * 2))
            fnt2 = _load_font(IMPACT_FONT_CANDIDATES, px * 2)
            if tw > (w * 2) * 0.88:
                px2 = int((px * 2) * ((w * 2) * 0.88) / tw)
                fnt2 = _load_font(IMPACT_FONT_CANDIDATES, px2)
                tw = md.textlength(word, font=fnt2)
            bb = md.textbbox((0, 0), word, font=fnt2)
            th = bb[3] - bb[1]
            md.text((int((w * 2 - tw) * 0.5), int((h * 2 - th) * 0.5) - bb[1]), word, font=fnt2, fill=255)
            m_aa = (np.array(mask_img.resize((w, h), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0)[:, :, None]
            base_f = fr.astype(np.float32)
            diff_f = np.abs(255.0 - base_f)
            out.append(np.clip(base_f * (1.0 - m_aa) + diff_f * m_aa, 0, 255).astype(np.uint8))
        return out

    if vfx == "bw_tension":
        # S10 (@astroospace) Stark silver-noir monochrome tension before color drop!
        out = []
        for fr in frames:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
            norm = np.clip((g - 12.0) / 230.0, 0.0, 1.0)
            sc = (norm * norm * (3.0 - 2.0 * norm)) * 255.0
            bw = np.clip(0.55 * g + 0.45 * sc, 0, 255).astype(np.uint8)
            out.append(cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR))
        return out

    if vfx == "divine_shockwave":
        # S10 + S09: 138% golden-saffron color bloom + concentric radial bass refraction wave!
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w * 0.5, h * 0.5
        rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) + 1e-4
        max_r = math.hypot(cx, cy)
        out = []
        for i, fr in enumerate(frames):
            cur = fr
            t = i / 30.0
            if t < 0.45:
                p = t / 0.45
                ring_r = p * max_r * 0.94
                band = np.exp(-((rr - ring_r) ** 2) / (2.0 * (36.0 ** 2)))
                amp = 26.0 * (1.0 - p) * band
                mx = np.clip(xx - ((xx - cx) / rr) * amp, 0, w - 1)
                my = np.clip(yy - ((yy - cy) / rr) * amp, 0, h - 1)
                cur = cv2.remap(cur, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
            hsv = cv2.cvtColor(cur, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.32, 0, 255)
            out.append(cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR))
        return out

    if vfx == "bento_3x3" and bento_tiles and len(bento_tiles) >= 9:
        # S05 (@cashworthclipz) Live 3x3 9-tile moving Bento Grid popping in -> zoom_through center tile!
        tw = w // 3
        th = h // 3
        n = len(frames)
        # Pop-in order leaving center (#4) strong from frame 0!
        pop_order = [4, 0, 8, 2, 6, 1, 7, 3, 5]
        out = []
        for i in range(n):
            board = np.zeros((h, w, 3), dtype=np.uint8)
            visible_count = min(9, 2 + int((i / max(1.0, n * 0.52)) * 8))
            active_slots = set(pop_order[:visible_count])
            for slot in range(9):
                if slot not in active_slots:
                    continue
                r_idx, c_idx = divmod(slot, 3)
                t_frames = bento_tiles[slot]
                src_f = t_frames[min(i, len(t_frames) - 1)]
                tile_rs = cv2.resize(src_f, (tw - 4, th - 4), interpolation=cv2.INTER_AREA)
                y0 = r_idx * th + 2
                x0 = c_idx * tw + 2
                board[y0:y0 + th - 4, x0:x0 + tw - 4] = tile_rs

            # Final 28% of clip: smooth zoom_through into center tile (3.0x zoom)!
            zoom_start_f = int(n * 0.70)
            if i >= zoom_start_f:
                uz = (i - zoom_start_f) / float(max(1, n - 1 - zoom_start_f))
                s = 1.0 + 2.02 * (uz ** 1.9)
                M = np.array([[s, 0.0, (1.0 - s) * (w * 0.5)], [0.0, s, (1.0 - s) * (h * 0.5)]], dtype=np.float32)
                board = cv2.warpAffine(board, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
            out.append(board)
        return out

    return frames


def _overlay_zohair_card_hud(
    card_bgr: np.ndarray,
    *,
    rem_sec: int,
    subtitle: str | None,
    serif_font: ImageFont.FreeTypeFont,
    timer_font: ImageFont.FreeTypeFont,
) -> np.ndarray:
    ch, cw = card_bgr.shape[:2]
    base_rgba = Image.fromarray(cv2.cvtColor(card_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    hud_glow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    hud_txt = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    gd = ImageDraw.Draw(hud_glow)
    td = ImageDraw.Draw(hud_txt)

    mins = max(0, rem_sec) // 60
    secs = max(0, rem_sec) % 60
    t_str = f"{mins}:{secs:02d}"
    tw_t = td.textlength(t_str, font=timer_font)
    tx_t = int(cw - tw_t - 24)
    ty_t = 18
    td.text((tx_t + 1, ty_t + 1), t_str, font=timer_font, fill=(0, 0, 0, 180))
    td.text((tx_t, ty_t), t_str, font=timer_font, fill=(246, 248, 250, 222))

    if subtitle and subtitle.strip():
        sub = subtitle.strip()
        fnt = serif_font
        sw_px = td.textlength(sub, font=fnt)
        if sw_px > cw * 0.84:
            fnt = _load_font(SERIF_FONT_CANDIDATES, max(20, int(29 * (cw * 0.84) / sw_px)))
            sw_px = td.textlength(sub, font=fnt)
        bbox = td.textbbox((0, 0), sub, font=fnt)
        sh_px = bbox[3] - bbox[1]
        sx = int((cw - sw_px) * 0.5)
        sy = int((ch - sh_px) * 0.5) - 2
        gd.text((sx, sy), sub, font=fnt, fill=(0, 0, 0, 225), stroke_width=5, stroke_fill=(0, 0, 0, 205))
        td.text((sx, sy), sub, font=fnt, fill=(252, 252, 250, 255), stroke_width=2, stroke_fill=(0, 0, 0, 238))

    comp = Image.alpha_composite(base_rgba, hud_glow.filter(ImageFilter.GaussianBlur(radius=4.5)))
    comp = Image.alpha_composite(comp, hud_txt)
    return cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)


def mix_zohair_multitrack_audio(
    song_path: str | Path,
    *,
    song_offset_s: float,
    active_dur_s: float,
    total_dur_s: float,
    dialogue_tracks: list[tuple[float, np.ndarray]],
    sfx_tracks: list[tuple[float, np.ndarray, float]],
    sr: int = 44100,
) -> np.ndarray:
    """Premiere Pro 3-Track Vocal-Song Jigsaw Mixer (`A1` Vocal Anthem + `A2` Sparse Pocket Dialogue + `A3` SFX)."""
    from scipy.signal import butter, sosfiltfilt

    n_total = int(round(total_dur_s * sr))
    n_active = min(n_total, int(round(active_dur_s * sr)))

    song = _slice_audio_segment(song_path, song_offset_s, total_dur_s, sr=sr)
    pk_s = float(np.max(np.abs(song))) + 1e-8
    song = song * (0.84 / pk_s)

    vox_bus = np.zeros((n_total, 2), dtype=np.float32)
    sfx_bus = np.zeros((n_total, 2), dtype=np.float32)

    sos_hp_vox = butter(2, 100.0 / (sr * 0.5), btype="high", output="sos")
    sos_pres = butter(2, [1850.0 / (sr * 0.5), 4600.0 / (sr * 0.5)], btype="band", output="sos")
    sos_hp_sfx = butter(2, 65.0 / (sr * 0.5), btype="high", output="sos")

    for t_start, raw_v in dialogue_tracks:
        if len(raw_v) < 64:
            continue
        v64 = raw_v.astype(np.float64)
        v_clean = sosfiltfilt(sos_hp_vox, v64, axis=0)
        v_clean = v_clean + 0.65 * sosfiltfilt(sos_pres, v_clean, axis=0)
        mono = np.mean(np.abs(v_clean), axis=1)
        p95 = float(np.percentile(mono, 95))
        floor = max(0.005, min(0.015, p95 * 0.20))
        act = mono[mono > floor]
        if len(act) > 40:
            scale = 0.35 / (float(np.sqrt(np.mean(act ** 2))) + 1e-6)
            v_clean = np.tanh(v_clean * min(4.6, scale) * 1.15) * 0.90
        fn = min(len(v_clean) // 4, int(0.025 * sr))
        if fn > 4:
            ramp = np.linspace(0.0, 1.0, fn)[:, None]
            v_clean[:fn] *= ramp
            v_clean[-fn:] *= ramp[::-1]
        i0 = max(0, int(round(t_start * sr)))
        i1 = min(n_total, i0 + len(v_clean))
        if i1 > i0:
            vox_bus[i0:i1] += v_clean[:i1 - i0].astype(np.float32)

    for t_start, raw_s, gain in sfx_tracks:
        if len(raw_s) < 64 or gain <= 0.0:
            continue
        s64 = sosfiltfilt(sos_hp_sfx, raw_s.astype(np.float64), axis=0)
        pk = float(np.max(np.abs(s64))) + 1e-8
        s_norm = (s64 / pk) * float(gain)
        fn = min(len(s_norm) // 4, int(0.03 * sr))
        if fn > 4:
            ramp = np.linspace(0.0, 1.0, fn)[:, None]
            s_norm[:fn] *= ramp
            s_norm[-fn:] *= ramp[::-1]
        i0 = max(0, int(round(t_start * sr)))
        i1 = min(n_total, i0 + len(s_norm))
        if i1 > i0:
            sfx_bus[i0:i1] += s_norm[:i1 - i0].astype(np.float32)

    # Silky 130ms Premiere rubberband ONLY inside the 3 sparse natural pockets!
    win = max(64, int(0.025 * sr))
    vox_rms = np.sqrt(np.convolve(np.mean(vox_bus ** 2, axis=1), np.ones(win) / win, mode="same") + 1e-12)
    gate = np.clip((vox_rms - 0.015) / 0.045, 0.0, 1.0)
    dil_k = max(32, int(0.055 * sr))
    gate_dil = np.minimum(1.0, np.convolve(gate, np.ones(dil_k) / max(1, dil_k * 0.38), mode="same"))
    sm_k = max(64, int(0.13 * sr))
    kern = np.hanning(sm_k)
    rubber = np.clip(np.convolve(gate_dil, kern / np.sum(kern), mode="same"), 0.0, 1.0)[:, None]

    sos_mid = butter(3, [260.0 / (sr * 0.5), 5200.0 / (sr * 0.5)], btype="band", output="sos")
    song64 = song.astype(np.float64)
    mids = sosfiltfilt(sos_mid, song64, axis=0)
    lows_highs = song64 - mids

    # Outside the 3 sparse pockets, rubber == 0 -> 100.0% UNTOUCHED 0 dB STUDIO VOCAL SONG!
    # Inside a pocket -> mids=0.20 (-14 dB) while warm low/high groove stays smooth at 0.38 (-8.4 dB)!
    g_mid = 1.00 * (1.0 - rubber) + 0.20 * rubber
    g_gro = 1.00 * (1.0 - rubber) + 0.38 * rubber
    shaped_song = (mids * g_mid + lows_highs * g_gro).astype(np.float32)
    sfx_bus *= (1.0 - 0.75 * rubber).astype(np.float32)

    fi_n = min(n_total, int(0.08 * sr))
    if fi_n > 8:
        shaped_song[:fi_n] *= np.linspace(0.35, 1.0, fi_n, dtype=np.float32)[:, None]
    outro_fade_start = max(0, n_active - int(0.15 * sr))
    if n_total > outro_fade_start + 16:
        fade_len = n_total - outro_fade_start
        shaped_song[outro_fade_start:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)[:, None]

    mix = vox_bus + shaped_song + sfx_bus
    pk_mix = float(np.max(np.abs(mix))) + 1e-8
    if pk_mix > 0.95:
        mix *= 0.95 / pk_mix
    return mix.astype(np.float32)


def render_zohair_jigsaw_edit(
    out_mp4: str | Path,
    *,
    sources: dict[str, str | Path],
    song_path: str | Path,
    song_offset_s: float,
    visual_cuts: list[dict[str, Any]],
    dialogue_events: list[dict[str, Any]],
    sfx_events: list[dict[str, Any]] | None = None,
    outro_black_s: float = 0.65,
) -> dict[str, Any]:
    """Render a full Style 1 (`@thisiszohair` Jigsaw + Drive `Sample` `S01..S10` Pro VFX) Edit."""
    ff = get_ffmpeg()
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    sfx_events = sfx_events or []

    fps = 30
    sr = 44100
    canvas_w, canvas_h = 1080, 1920
    card_w, card_h = 1036, 584
    card_x = (canvas_w - card_w) // 2
    card_y = (canvas_h - card_h) // 2

    round_mask = _build_rounded_mask_3ch(card_w, card_h, radius=24)
    serif_font = _load_font(SERIF_FONT_CANDIDATES, 29)
    timer_font = _load_font(SANS_FONT_CANDIDATES, 23)
    segmenter = PersonSegmenter()

    vfx_used: list[str] = []

    with tempfile.TemporaryDirectory(prefix="zohair_v2_") as td:
        tmp_dir = Path(td)
        raw_vid = tmp_dir / "video_raw.mp4"
        mix_wav = tmp_dir / "audio_mix.wav"

        active_cards: list[np.ndarray] = []
        for c_idx, vc in enumerate(visual_cuts):
            sk = vc["src"]
            s0 = float(vc["start_s"])
            dur = float(vc["dur_s"])
            target_f = max(2, int(round(dur * fps)))
            use_vel = bool(vc.get("vel_curve", False))
            src_dur = float(vc.get("src_dur_s", dur * 1.45 if use_vel else max(dur + 0.06, 0.18)))

            raw_frames = _slice_clip_frames_30fps(sources[sk], s0, src_dur, tmp_dir, f"vc_{c_idx}")
            fitted = _trim_and_fit_16x9_card(
                raw_frames,
                card_w=card_w,
                card_h=card_h,
                zoom_start=float(vc.get("zoom_start", 1.01)),
                zoom_end=float(vc.get("zoom_end", 1.07)),
                cy_bias=float(vc.get("cy_bias", 0.50)),
                dark_lift=bool(vc.get("dark_lift", True)),
                sat_mult=float(vc.get("sat_mult", 1.14)),
            )

            if use_vel and len(fitted) >= 3:
                fitted = _velocity_resample_optical(fitted, target_f)
                vfx_used.append("optical_velocity")
            else:
                while len(fitted) < target_f and fitted:
                    fitted.append(fitted[-1].copy())
                fitted = fitted[:target_f]

            # Optional 3x3 Bento Grid tiles
            vfx_name = str(vc.get("vfx", "none"))
            bento_tiles: list[list[np.ndarray]] | None = None
            if vfx_name == "bento_3x3" and vc.get("grid_clips"):
                bento_tiles = []
                for g_idx, gc in enumerate(vc["grid_clips"][:9]):
                    g_raw = _slice_clip_frames_30fps(sources[gc["src"]], float(gc["start_s"]), max(dur, 0.9), tmp_dir, f"bg_{c_idx}_{g_idx}")
                    g_fit = _trim_and_fit_16x9_card(g_raw, card_w=card_w // 3, card_h=card_h // 3, zoom_start=1.0, zoom_end=1.04)
                    bento_tiles.append(g_fit if g_fit else fitted)

            if vfx_name != "none":
                fitted = _apply_clip_vfx(fitted, vfx_name, vc, segmenter, bento_tiles=bento_tiles)
                vfx_used.append(vfx_name)

            tr_in = str(vc.get("transition_in", "none"))
            if tr_in != "none":
                fitted = _apply_entry_transition(fitted, tr_in)
                vfx_used.append(f"tr:{tr_in}")

            active_cards.extend(fitted)

        active_frames_n = len(active_cards)
        active_dur_s = active_frames_n / float(fps)
        outro_frames_n = max(0, int(round(outro_black_s * fps)))
        total_frames_n = active_frames_n + outro_frames_n
        total_dur_s = total_frames_n / float(fps)

        # Isolate sparse natural-pocket dialogue via HDemucs
        dialogue_tracks: list[tuple[float, np.ndarray]] = []
        sub_windows: list[tuple[float, float, str]] = []
        v_methods: list[str] = []
        for d_idx, de in enumerate(dialogue_events):
            sk = de["src"]
            s0 = float(de["start_s"])
            dur = float(de["dur_s"])
            tl_s = float(de["timeline_s"])
            vox_wav = tmp_dir / f"dvox_{d_idx}.wav"
            m_used = isolate_clean_vocal_slice(str(sources[sk]), s0, s0 + dur, str(vox_wav), sr=sr)
            v_methods.append(m_used)
            v_arr, _ = sf.read(str(vox_wav), dtype="float32", always_2d=True)
            dialogue_tracks.append((tl_s, v_arr))
            if de.get("subtitle"):
                sub_t0 = float(de.get("sub_t0", tl_s))
                sub_t1 = float(de.get("sub_t1", tl_s + dur))
                sub_windows.append((sub_t0, sub_t1, str(de["subtitle"])))

        sfx_tracks: list[tuple[float, np.ndarray, float]] = []
        for s_ev in sfx_events:
            s_arr = _slice_audio_segment(sources[s_ev["src"]], float(s_ev["start_s"]), float(s_ev["dur_s"]), sr=sr)
            sfx_tracks.append((float(s_ev["timeline_s"]), s_arr, float(s_ev.get("gain", 0.26))))

        enc = subprocess.Popen(
            [
                ff, "-y",
                "-f", "rawvideo", "-pix_fmt", "bgr24",
                "-s", f"{canvas_w}x{canvas_h}", "-r", str(fps), "-i", "-",
                "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
                "-pix_fmt", "yuv420p",
                str(raw_vid),
            ],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        assert enc.stdin is not None
        canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        for fi in range(total_frames_n):
            t_cur = fi / float(fps)
            rem_sec = max(0, int(math.ceil(active_dur_s - t_cur)))
            canvas.fill(0)
            if fi < active_frames_n:
                sub_txt: str | None = None
                for st0, st1, stxt in sub_windows:
                    if st0 <= t_cur <= st1:
                        sub_txt = stxt
                        break
                card_hud = _overlay_zohair_card_hud(
                    active_cards[fi],
                    rem_sec=rem_sec,
                    subtitle=sub_txt,
                    serif_font=serif_font,
                    timer_font=timer_font,
                )
                rounded_card = (card_hud.astype(np.float32) * round_mask).astype(np.uint8)
                canvas[card_y:card_y + card_h, card_x:card_x + card_w] = rounded_card
            enc.stdin.write(canvas.tobytes())
        enc.stdin.close()
        enc.wait()

        master_audio = mix_zohair_multitrack_audio(
            song_path,
            song_offset_s=song_offset_s,
            active_dur_s=active_dur_s,
            total_dur_s=total_dur_s,
            dialogue_tracks=dialogue_tracks,
            sfx_tracks=sfx_tracks,
            sr=sr,
        )
        sf.write(str(mix_wav), master_audio, sr, subtype="PCM_16")

        subprocess.run(
            [
                ff, "-y",
                "-i", str(raw_vid), "-i", str(mix_wav),
                "-c:v", "copy",
                "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=9,alimiter=limit=-1.5dB:level=false",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                "-movflags", "+faststart",
                str(out_mp4),
            ],
            check=True,
            stderr=subprocess.DEVNULL,
        )

    segmenter.close()
    return {
        "out_mp4": str(out_mp4),
        "style": "zohair_jigsaw_style1_pro_vfx_v2",
        "resolution": f"{canvas_w}x{canvas_h}",
        "active_card": f"{card_w}x{card_h} rounded-24px (16:9)",
        "visual_cuts": len(visual_cuts),
        "dialogue_pockets": len(dialogue_events),
        "sfx_accents": len(sfx_events),
        "vfx_arsenal_applied": sorted(set(vfx_used)),
        "active_dur_s": round(active_dur_s, 3),
        "duration_s": round(total_dur_s, 3),
        "vocal_isolation": sorted(set(v_methods)),
        "size_mb": round(out_mp4.stat().st_size / (1024 * 1024), 2),
    }
