"""aura_edit.py — 2-Act 'Scene Setup -> Cross-Movie Actor Aura Drop' Engine.

Reverse-engineered from viral YouTube Shorts / After Effects edits
(`@4Kmovies_io` 'Hulk Remembered Peter Parker' & `@Proxeditz07` 'Mare Ga Ya Bhage Ga'):

1. **Exact `9:10` Portrait Cinema Box (`1080x1200`) centered inside `1080x1920` (`9:16`):**
   - `360px` pure `#000000` top bar + `1080x1200` active viewport (`y=360..1560`) + `360px` bottom bar.
   - Fills 62.5% of vertical screen height for close-up facial impact while keeping Shorts UI completely clear.
2. **4K 'After Effects CC Sharpen + Cinema Contrast' Grade:**
   - Dual-scale Unsharp Mask (fine skin/fabric micro-detail + local clarity) + S-curve contrast + Teal/Amber split-tone.
3. **Act 1 — Cohesive Scene Setup (`0.0s .. drop_s`):**
   - Clean dialogue isolated via Meta `HDEMUCS_HIGH_MUSDB_PLUS` (100% trailer music stripped).
   - BlazeFace center-tracked `9:10` framing with smooth subtle push-in.
   - `@Proxeditz07`-style bold uppercase White + Glowing Fiery Neon Keyword Captions in the lower-third of the `9:10` box.
   - Muffled low-pass (`420 Hz -> 1800 Hz` sweep) beat build-up + sub riser + `4-frame` pre-drop blackout vacuum.
4. **Act 2 — Cross-Movie Actor Aura / Velocity Drop (`drop_s .. end`):**
   - Pulls iconic shots of the actor across multiple different scenes/movies.
   - Every beat (`2 beats = 0.96s` @ `125 BPM`) fires Farneback Optical-Flow Velocity (`2.8x fast whip -> 0.36x interpolated slow-mo`),
     AE `S_Shake` damped impact shake, additive exposure flash decay, optional `bass_shockwave` ripple,
     and optional AI-rotoscoped 3D hero name (`selfie_segmenter.tflite`) behind the actor on the opening drop shot.
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
from .ironman_edit import isolate_clean_vocal_slice, optical_flow_interp
from .smart_camera import _make_face_detector
from .viral_vfx import PersonSegmenter


def _velocity_resample_optical(frames_bgr: list[np.ndarray], n_out: int) -> list[np.ndarray]:
    """Resample `frames_bgr` to `n_out` frames along an AE velocity curve (`2.7x` entry whip -> `0.38x` slow-mo)."""
    if not frames_bgr:
        return []
    if len(frames_bgr) == 1:
        return [frames_bgr[0].copy() for _ in range(n_out)]
    max_idx = len(frames_bgr) - 1
    out: list[np.ndarray] = []
    for k in range(n_out):
        u = k / float(max(1, n_out - 1))
        # Power < 1.0 advances rapidly through the first 55% of source frames, then glides in slow-mo!
        u_vel = u ** 0.44
        pos = u_vel * max_idx
        i0 = min(max_idx, int(math.floor(pos)))
        i1 = min(max_idx, i0 + 1)
        frac = float(pos - i0)
        if i0 == i1 or frac < 0.04:
            out.append(frames_bgr[i0])
        elif frac > 0.96:
            out.append(frames_bgr[i1])
        else:
            out.append(optical_flow_interp(frames_bgr[i0], frames_bgr[i1], frac))
    return out

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STUDIO_ROOT = Path(__file__).resolve().parents[1]

FONT_BOLD_CANDIDATES = [
    str(_REPO_ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf"),
    str(_REPO_ROOT / "assets" / "fonts" / "Anton-Regular.ttf"),
    "/home/user/assets/fonts/ArchivoBlack-Regular.ttf",
    "/home/user/assets/fonts/Anton-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _pick_font(size_px: int) -> ImageFont.FreeTypeFont:
    for fp in FONT_BOLD_CANDIDATES:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size_px)
    return ImageFont.load_default()


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _apply_4k_cc_grade(frame_bgr: np.ndarray, *, warm_boost: float = 1.0, sat_mult: float = 1.12) -> np.ndarray:
    """After Effects 'CC Sharpen + Micro-Contrast' 4K look."""
    f = frame_bgr.astype(np.float32)
    # Fine detail + medium local contrast unsharp mask
    blur_fine = cv2.GaussianBlur(f, (0, 0), 1.05)
    blur_mid = cv2.GaussianBlur(f, (0, 0), 3.8)
    f = f + 0.52 * (f - blur_fine) + 0.22 * (f - blur_mid)

    # Gentle cinematic S-curve around midpoint
    norm = np.clip(f / 255.0, 0.0, 1.0)
    scurve = norm * norm * (3.0 - 2.0 * norm)
    f = (0.68 * norm + 0.32 * scurve) * 255.0

    # Subtle cold-shadow / warm-highlight split tone
    lum = (0.114 * f[:, :, 0] + 0.587 * f[:, :, 1] + 0.299 * f[:, :, 2]) / 255.0
    sh = 1.0 - lum
    hi = lum
    f[:, :, 0] += 5.0 * sh - 3.0 * hi * warm_boost   # B: cool shadows
    f[:, :, 2] += 5.5 * hi * warm_boost - 2.0 * sh   # R: warm skin highlights

    out = np.clip(f, 0, 255).astype(np.uint8)
    if abs(sat_mult - 1.0) > 1e-3:
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_mult, 0, 255)
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return out


def _crop_9x10_smart(
    frames_bgr: list[np.ndarray],
    box_w: int = 1080,
    box_h: int = 1200,
    zoom_start: float = 1.0,
    zoom_end: float = 1.05,
    detect_fn: Any = None,
    cx_override: float | None = None,
) -> list[np.ndarray]:
    """Crop 16:9 frames cleanly into 1080x1200 (9:10) centered on single face or two-shot midpoint."""
    if not frames_bgr:
        return []
    sh, sw = frames_bgr[0].shape[:2]
    target_aspect = box_w / float(box_h)  # 0.900

    # Sample up to 5 frames to find median horizontal subject center (two-shot aware!)
    cx_norm = 0.5
    if cx_override is not None:
        cx_norm = float(np.clip(cx_override, 0.22, 0.78))
    elif detect_fn is not None:
        xs: list[float] = []
        sample_idxs = sorted(set([0, len(frames_bgr) // 4, len(frames_bgr) // 2, (3 * len(frames_bgr)) // 4, len(frames_bgr) - 1]))
        for idx in sample_idxs:
            faces = detect_fn(frames_bgr[idx])
            if faces:
                ranked = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)
                if len(ranked) >= 2 and abs(float(ranked[0][0]) - float(ranked[1][0])) <= 0.46:
                    # Two-shot! Center cleanly between both actors
                    xs.append(0.5 * (float(ranked[0][0]) + float(ranked[1][0])))
                else:
                    xs.append(float(ranked[0][0]))
        if xs:
            cx_norm = float(np.clip(np.median(xs), 0.24, 0.76))

    out: list[np.ndarray] = []
    n = max(1, len(frames_bgr) - 1)
    for i, fr in enumerate(frames_bgr):
        u = i / float(n)
        z = zoom_start + (zoom_end - zoom_start) * u
        crop_h = sh / z
        crop_w = crop_h * target_aspect
        if crop_w > sw:
            crop_w = sw / z
            crop_h = crop_w / target_aspect
        cx = cx_norm * sw
        cy = 0.48 * sh
        cx = float(np.clip(cx, crop_w * 0.5, sw - crop_w * 0.5))
        cy = float(np.clip(cy, crop_h * 0.5, sh - crop_h * 0.5))

        # Sub-pixel warpAffine Lanczos4 so slow push-in has zero integer-pixel jitter
        sx = box_w / crop_w
        sy = box_h / crop_h
        tx = (box_w * 0.5) - cx * sx
        ty = (box_h * 0.5) - cy * sy
        M = np.array([[sx, 0.0, tx], [0.0, sy, ty]], dtype=np.float32)
        warped = cv2.warpAffine(
            fr, M, (box_w, box_h),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        out.append(warped)
    return out


def _draw_neon_keyword_caption(
    box_bgr: np.ndarray,
    prefix_text: str,
    highlight_text: str,
    suffix_text: str = "",
    accent_hex: str = "#FF4818",
    pop_progress: float = 1.0,
) -> np.ndarray:
    """Draw @Proxeditz07 style clean bold white + glowing neon keyword caption in lower-third."""
    bh, bw = box_bgr.shape[:2]
    scale_pop = 0.94 + 0.06 * min(1.0, pop_progress / 0.18)
    font_px = max(28, int(round(44 * scale_pop)))
    font = _pick_font(font_px)

    parts = []
    if prefix_text.strip():
        parts.append((prefix_text.strip().upper() + " ", False))
    if highlight_text.strip():
        parts.append((highlight_text.strip().upper(), True))
    if suffix_text.strip():
        sp = " " if highlight_text.strip() else ""
        parts.append((sp + suffix_text.strip().upper(), False))
    if not parts:
        return box_bgr

    dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
    widths = [dummy.textlength(txt, font=font) for txt, _ in parts]
    total_w = sum(widths)
    # Auto-shrink if wider than 88% of 1080px box
    if total_w > bw * 0.88:
        font_px = max(24, int(font_px * (bw * 0.88) / total_w))
        font = _pick_font(font_px)
        widths = [dummy.textlength(txt, font=font) for txt, _ in parts]
        total_w = sum(widths)

    x0 = int((bw - total_w) * 0.5)
    y0 = int(bh * 0.77)

    glow_layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    td = ImageDraw.Draw(text_layer)
    ar, ag, ab = _hex_rgb(accent_hex)

    # Subtle dark backing gradient behind text line for readability on bright spacesuits
    pad_x, pad_y = 28, 16
    gd.rounded_rectangle(
        [x0 - pad_x, y0 - pad_y, int(x0 + total_w + pad_x), y0 + font_px + pad_y],
        radius=18,
        fill=(0, 0, 0, 120),
    )

    cur_x = float(x0)
    for (txt, is_hi), w_txt in zip(parts, widths):
        ix = int(round(cur_x))
        # Crisp black drop-shadow
        td.text((ix + 3, y0 + 4), txt, font=font, fill=(0, 0, 0, 225))
        if is_hi:
            # Multi-pass fiery neon bloom
            gd.text((ix, y0), txt, font=font, fill=(ar, ag, ab, 255), stroke_width=6, stroke_fill=(ar, ag, ab, 210))
            td.text((ix, y0), txt, font=font, fill=(255, min(255, ag + 95), min(255, ab + 70), 255))
        else:
            td.text((ix, y0), txt, font=font, fill=(248, 250, 252, 255))
        cur_x += w_txt

    glow_blur = glow_layer.filter(ImageFilter.GaussianBlur(radius=11))
    comp = Image.alpha_composite(
        Image.fromarray(cv2.cvtColor(box_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA"),
        glow_blur,
    )
    comp = Image.alpha_composite(comp, text_layer)
    return cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)


def _draw_roto_hero_text(
    box_bgr: np.ndarray,
    text: str,
    segmenter: PersonSegmenter,
    accent_hex: str = "#FF5520",
) -> np.ndarray:
    """Place giant glowing 3D hero typography BEHIND the AI-rotoscoped actor."""
    bh, bw = box_bgr.shape[:2]
    a3 = segmenter.mask(box_bgr, feather_px=7)
    font = _pick_font(176)
    dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
    tw = dummy.textlength(text, font=font)
    if tw > bw * 0.92:
        font = _pick_font(int(176 * (bw * 0.92) / tw))
        tw = dummy.textlength(text, font=font)
    tx = int((bw - tw) * 0.5)
    ty = int(bh * 0.14)

    ar, ag, ab = _hex_rgb(accent_hex)
    glow = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    fg_txt = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    fd = ImageDraw.Draw(fg_txt)
    gd.text((tx, ty), text, font=font, fill=(ar, ag, ab, 235), stroke_width=8, stroke_fill=(ar, ag, ab, 180))
    for d in range(8, 0, -2):
        fd.text((tx + d, ty + d), text, font=font, fill=(20, 10, 8, 190))
    fd.text((tx, ty), text, font=font, fill=(255, 244, 235, 250))

    base = Image.fromarray(cv2.cvtColor(box_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    with_txt = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(radius=14)))
    with_txt = Image.alpha_composite(with_txt, fg_txt)
    bg_with_txt = cv2.cvtColor(np.array(with_txt.convert("RGB")), cv2.COLOR_RGB2BGR)

    comp = bg_with_txt.astype(np.float32) * (1.0 - a3) + box_bgr.astype(np.float32) * a3
    return np.clip(comp, 0, 255).astype(np.uint8)


def _apply_impact_shake_and_flash(
    frames_bgr: list[np.ndarray],
    shake_px: float = 22.0,
    flash_peak: float = 0.55,
    shockwave: bool = False,
) -> list[np.ndarray]:
    """Apply damped AE S_Shake + white exposure flash + optional radial bass shockwave on beat entry."""
    if not frames_bgr:
        return []
    bh, bw = frames_bgr[0].shape[:2]
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    cx, cy = bw * 0.5, bh * 0.5
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) + 1e-4
    max_r = math.hypot(cx, cy)

    out: list[np.ndarray] = []
    for i, fr in enumerate(frames_bgr):
        t = i / 30.0
        cur = fr
        # First 0.28s: damped impact camera shake (1.08x overscan so zero black edges)
        if t < 0.28 and shake_px > 0:
            decay = math.exp(-11.0 * t)
            dx = shake_px * decay * math.sin(2.0 * math.pi * 19.0 * t)
            dy = shake_px * 0.85 * decay * math.cos(2.0 * math.pi * 15.0 * t)
            s = 1.06 + 0.05 * decay
            M = np.array([
                [s, 0.0, (1.0 - s) * cx + dx],
                [0.0, s, (1.0 - s) * cy + dy],
            ], dtype=np.float32)
            cur = cv2.warpAffine(cur, M, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        # Optional radial bass shockwave ripple across first 0.42s
        if shockwave and t < 0.42:
            p = t / 0.42
            ring_r = p * max_r * 0.92
            band = np.exp(-((rr - ring_r) ** 2) / (2.0 * (40.0 ** 2)))
            amp = 24.0 * (1.0 - p) * band
            mx = np.clip(xx - ((xx - cx) / rr) * amp, 0, bw - 1)
            my = np.clip(yy - ((yy - cy) / rr) * amp, 0, bh - 1)
            cur = cv2.remap(cur, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        # Crisp additive white beat-flash decaying across first 5 frames
        if i < 5 and flash_peak > 0:
            fl = flash_peak * math.exp(-0.85 * i)
            cur = np.clip(cur.astype(np.float32) * (1.0 + 0.35 * fl) + 255.0 * (0.65 * fl), 0, 255).astype(np.uint8)
        out.append(cur)
    return out


def synthesize_phonk_aura_soundtrack(
    total_dur_s: float,
    drop_s: float,
    bpm: float = 125.0,
    sr: int = 44100,
) -> np.ndarray:
    """ procedural Slowed Hypnotic / Dark Phonk soundtrack:
    - Act 1 (`0 .. drop_s - 0.14s`): muffled low-pass atmospheric pad + soft pulse + pre-drop riser
    - Pre-drop (`drop_s - 0.14s .. drop_s`): dramatic vacuum silence
    - Act 2 (`drop_s .. total_dur_s`): slowed hypnotic cowbell/lead melody + 808 sub-bass + crisp snare/hat
    """
    from scipy.signal import butter, sosfilt

    n = int(round(total_dur_s * sr))
    t = np.arange(n, dtype=np.float64) / sr
    beat_s = 60.0 / bpm  # 0.48s @ 125 BPM

    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    # --- ACT 1: Atmospheric muffled pad + subtle heartbeat + riser ---
    n_pre = max(0, int(round((drop_s - 0.13) * sr)))
    if n_pre > 0:
        tp = t[:n_pre]
        # Minor chord drone (D2 + A2 + F3)
        pad_l = 0.10 * np.sin(2 * np.pi * 73.42 * tp) + 0.06 * np.sin(2 * np.pi * 110.0 * tp + 0.3) + 0.04 * np.sin(2 * np.pi * 174.61 * tp)
        pad_r = 0.10 * np.sin(2 * np.pi * 73.42 * tp) + 0.06 * np.sin(2 * np.pi * 110.0 * tp - 0.3) + 0.04 * np.sin(2 * np.pi * 174.85 * tp)
        # Rising tension envelope in last 2.4s before drop
        riser_start = max(0.0, drop_s - 2.4)
        riser_env = np.clip((tp - riser_start) / max(0.2, (drop_s - 0.13 - riser_start)), 0.0, 1.0) ** 2.0
        sweep_freq = 140.0 + 680.0 * riser_env
        sweep_phase = 2 * np.pi * np.cumsum(sweep_freq) / sr
        riser = 0.16 * riser_env * np.sin(sweep_phase)
        sos_lp = butter(4, 520.0 / (sr * 0.5), btype="low", output="sos")
        left[:n_pre] = sosfilt(sos_lp, pad_l) + riser
        right[:n_pre] = sosfilt(sos_lp, pad_r) + riser

    # --- ACT 2: Heavy Slowed Hypnotic / Phonk Beat Drop ---
    # D-minor hypnotic motif frequencies (Hz): D4, F4, A4, Bb4, A4, F4, E4, D4
    motif = [293.66, 349.23, 440.00, 466.16, 440.00, 349.23, 329.63, 293.66]
    bass_notes = [36.71, 36.71, 43.65, 46.25, 36.71, 36.71, 41.20, 32.70]  # D1, F1, F#1/Bb0, E1, C1

    sos_lead = butter(3, 2600.0 / (sr * 0.5), btype="low", output="sos")
    rng = np.random.default_rng(42)

    beat_idx = 0
    cur_t = drop_s
    while cur_t < total_dur_s - 0.05:
        i0 = int(round(cur_t * sr))
        dur_b = min(beat_s, total_dur_s - cur_t)
        nb = int(round(dur_b * sr))
        if nb <= 16:
            break
        tb = np.arange(nb, dtype=np.float64) / sr

        # 1. Punchy 808 Kick + Pitch-Drop Sub on every beat (heavier on even beats = clip cuts!)
        is_cut_beat = (beat_idx % 2 == 0)
        f_sub = bass_notes[(beat_idx // 2) % len(bass_notes)]
        pitch_env = f_sub + (115.0 if is_cut_beat else 75.0) * np.exp(-26.0 * tb)
        sub_phase = 2 * np.pi * np.cumsum(pitch_env) / sr
        sub_env = np.exp(-3.2 * tb) if is_cut_beat else np.exp(-5.0 * tb)
        sub = (0.58 if is_cut_beat else 0.40) * np.sin(sub_phase) * sub_env
        sub = np.tanh(sub * 1.45) * 0.52

        # 2. Hypnotic Slowed Phonk Cowbell / Detuned Synth Lead (two eighth-notes per beat)
        lead_l = np.zeros(nb, dtype=np.float64)
        lead_r = np.zeros(nb, dtype=np.float64)
        for sub_step in range(2):
            s0 = int(round(sub_step * 0.5 * beat_s * sr))
            s1 = min(nb, int(round((sub_step + 1) * 0.5 * beat_s * sr)))
            if s1 <= s0:
                continue
            ts = np.arange(s1 - s0, dtype=np.float64) / sr
            f_m = motif[(beat_idx * 2 + sub_step) % len(motif)]
            env_m = np.exp(-7.5 * ts) * (1.0 - np.exp(-180.0 * ts))
            # Classic 808 cowbell / dark synth ratio (1.0 + 1.504 fifth-metallic harmonic, smoothed)
            osc_l = 0.65 * np.sin(2 * np.pi * f_m * ts) + 0.35 * np.sin(2 * np.pi * (f_m * 1.498) * ts + 0.2)
            osc_r = 0.65 * np.sin(2 * np.pi * (f_m * 1.003) * ts) + 0.35 * np.sin(2 * np.pi * (f_m * 1.502) * ts - 0.2)
            lead_l[s0:s1] += 0.24 * env_m * np.tanh(osc_l * 1.6)
            lead_r[s0:s1] += 0.24 * env_m * np.tanh(osc_r * 1.6)

        lead_l = sosfilt(sos_lead, lead_l)
        lead_r = sosfilt(sos_lead, lead_r)

        # 3. Crisp Snare/Clap on odd beats + ticked hi-hat
        perc = np.zeros(nb, dtype=np.float64)
        if beat_idx % 2 == 1:
            noise = rng.standard_normal(nb)
            sos_bp = butter(2, [900.0 / (sr * 0.5), 4800.0 / (sr * 0.5)], btype="band", output="sos")
            perc += 0.20 * sosfilt(sos_bp, noise) * np.exp(-18.0 * tb)
        # Off-beat hat
        h0 = nb // 2
        if nb - h0 > 32:
            th = np.arange(nb - h0, dtype=np.float64) / sr
            sos_hp = butter(2, 6500.0 / (sr * 0.5), btype="high", output="sos")
            perc[h0:] += 0.06 * sosfilt(sos_hp, rng.standard_normal(nb - h0)) * np.exp(-38.0 * th)

        left[i0:i0 + nb] += sub + lead_l + perc
        right[i0:i0 + nb] += sub + lead_r + perc

        cur_t += beat_s
        beat_idx += 1

    # Smooth 0.65s fade-out at end
    fade_n = min(n, int(0.65 * sr))
    if fade_n > 0:
        fade = np.linspace(1.0, 0.0, fade_n)
        left[-fade_n:] *= fade
        right[-fade_n:] *= fade

    stereo = np.stack([left, right], axis=1)
    peak = float(np.max(np.abs(stereo))) + 1e-8
    if peak > 0.88:
        stereo *= 0.88 / peak
    return stereo.astype(np.float32)


def _slice_clip_frames_30fps(src_mp4: str | Path, start_s: float, dur_s: float, tmp_dir: Path, tag: str) -> list[np.ndarray]:
    """Frame-accurate 2-stage FFmpeg slice decoded at 30fps."""
    ff = get_ffmpeg()
    pre = max(0.0, start_s - 2.5)
    rem = start_s - pre
    out_mp4 = tmp_dir / f"slice_{tag}.mp4"
    subprocess.run(
        [
            ff, "-y",
            "-ss", f"{pre:.3f}", "-i", str(src_mp4),
            "-ss", f"{rem:.3f}", "-t", f"{dur_s:.3f}",
            "-an", "-vf", "fps=30",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "15", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        check=True,
        stderr=subprocess.DEVNULL,
    )
    cap = cv2.VideoCapture(str(out_mp4))
    frames: list[np.ndarray] = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(fr)
    cap.release()
    return frames


def _slice_audio_segment(src_audio: str | Path, start_s: float, dur_s: float, sr: int = 44100) -> np.ndarray:
    ff = get_ffmpeg()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        wav_p = Path(tf.name)
    try:
        subprocess.run(
            [
                ff, "-y", "-ss", f"{start_s:.3f}", "-i", str(src_audio),
                "-t", f"{dur_s:.3f}", "-vn", "-ac", "2", "-ar", str(sr),
                str(wav_p),
            ],
            check=True,
            stderr=subprocess.DEVNULL,
        )
        data, _ = sf.read(str(wav_p), dtype="float32", always_2d=True)
        target_n = int(round(dur_s * sr))
        if len(data) < target_n:
            data = np.vstack([data, np.zeros((target_n - len(data), 2), dtype=np.float32)])
        else:
            data = data[:target_n]
        return data
    finally:
        wav_p.unlink(missing_ok=True)


def mix_real_song_jigsaw(
    song_path: str | Path,
    *,
    song_offset_s: float,
    total_dur_s: float,
    drop_s: float,
    dialogue_stereo: np.ndarray,
    sr: int = 44100,
) -> np.ndarray:
    """`@thisiszohair` (`7f2...`) Jigsaw Real-Song Amplitude & Pocket Mixer.

    - Uses a REAL song sliced from `song_offset_s` for `total_dur_s`.
    - Act 1 (`0 .. drop_s`): Splits song into Vocal-Mids (`290..5200 Hz`) vs Groove (`<290 Hz` + `>5200 Hz`).
      Follows diagonal Premiere-style rubberband keyframes around every spoken phrase:
        * During speech: ducks song mids to `-13 dB` and groove to `-7.5 dB` so cheeky punchlines are 100% clear.
        * Inside EVERY pause/pocket between lines: swells the real song up to `-2.8 dB` full-frequency so the
          clap/riff groove 'nods to the beat' without disrupting the song!
    - Act 2 (`drop_s .. total_dur_s`): Unleashes 100% un-ducked studio amplitude (`0 dB`) right on the drop transient!
    """
    from scipy.signal import butter, sosfiltfilt

    song = _slice_audio_segment(song_path, song_offset_s, total_dur_s, sr=sr)
    n = len(song)
    peak_s = float(np.max(np.abs(song))) + 1e-8
    song = song * (0.88 / peak_s)

    if len(dialogue_stereo) < n:
        vox = np.vstack([dialogue_stereo, np.zeros((n - len(dialogue_stereo), 2), dtype=np.float32)])
    else:
        vox = dialogue_stereo[:n].copy()

    act1_n = min(n, int(round(drop_s * sr)))
    if act1_n > int(0.15 * sr):
        # Normalize active speech regions cleanly
        vox_mono = np.mean(np.abs(vox[:act1_n]), axis=1)
        active = vox_mono[vox_mono > 0.012]
        if len(active) > 100:
            target_scale = 0.24 / (float(np.sqrt(np.mean(active ** 2))) + 1e-6)
            vox[:act1_n] = np.tanh(vox[:act1_n] * min(3.2, target_scale) * 1.12) * 0.88

        # Build smooth Premiere-style rubberband envelope (`45ms` attack, `150ms` release)
        win_rms = max(64, int(0.025 * sr))
        env_raw = np.sqrt(
            np.convolve(np.mean(vox[:act1_n] ** 2, axis=1), np.ones(win_rms) / win_rms, mode="same") + 1e-12
        )
        speech_gate = np.clip((env_raw - 0.018) / 0.055, 0.0, 1.0)
        # Smooth rubberband ramps (~110ms window) so volume glides diagonally like Premiere keyframes
        k_smooth = max(64, int(0.11 * sr))
        rubber = np.convolve(speech_gate, np.hanning(k_smooth) / np.sum(np.hanning(k_smooth)), mode="same")
        rubber = np.clip(rubber, 0.0, 1.0)[:, None]

        # Frequency-selective pocket carving on Act 1 song
        sos_mid = butter(3, [290.0 / (sr * 0.5), 5200.0 / (sr * 0.5)], btype="band", output="sos")
        song_act1 = song[:act1_n].astype(np.float64)
        mids = sosfiltfilt(sos_mid, song_act1, axis=0)
        groove = song_act1 - mids  # sub-bass + kick + crisp hi-hat/clap air

        # Speech active -> mids=0.20 (-14dB), groove=0.42 (-7.5dB)
        # Pocket / pause -> mids=0.72 (-2.8dB), groove=0.76 (-2.4dB) -> song breathes & nods in every gap!
        gain_mids = 0.72 * (1.0 - rubber) + 0.20 * rubber
        gain_groove = 0.76 * (1.0 - rubber) + 0.42 * rubber
        shaped_act1 = (mids * gain_mids + groove * gain_groove).astype(np.float32)

        # Smooth 120ms ramp into full 1.00 studio drop right at `drop_s`!
        ramp_n = min(act1_n, int(0.12 * sr))
        if ramp_n > 16:
            r_up = np.linspace(0.0, 1.0, ramp_n, dtype=np.float32)[:, None]
            shaped_act1[-ramp_n:] = shaped_act1[-ramp_n:] * (1.0 - r_up) + song[act1_n - ramp_n:act1_n] * r_up
        song[:act1_n] = shaped_act1

    # Gentle 0.12s fade-in at 0.0s & 0.65s fade-out at end
    fi_n = min(n, int(0.12 * sr))
    fo_n = min(n, int(0.65 * sr))
    if fi_n > 8:
        song[:fi_n] *= np.linspace(0.25, 1.0, fi_n, dtype=np.float32)[:, None]
    if fo_n > 8:
        song[-fo_n:] *= np.linspace(1.0, 0.0, fo_n, dtype=np.float32)[:, None]

    mix = vox + song
    pk = float(np.max(np.abs(mix))) + 1e-8
    if pk > 0.95:
        mix *= 0.95 / pk
    return mix.astype(np.float32)


def render_aura_edit(
    out_mp4: str | Path,
    *,
    sources: dict[str, str | Path],
    vocal_sources: dict[str, str | Path] | None = None,
    song_path: str | Path | None = None,
    song_offset_s: float = 0.0,
    scene_segments: list[dict[str, Any]],
    scene_captions: list[dict[str, Any]],
    montage_clips: list[dict[str, Any]],
    hero_drop_title: str = "GOSLING",
    bpm: float = 125.0,
    pre_drop_black_frames: int = 0,
) -> dict[str, Any]:
    """Render a full 2-Act `1080x1920` (`9:10` `1080x1200` center viewport) Scene -> Aura Montage edit."""
    ff = get_ffmpeg()
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    vocal_sources = vocal_sources or {}

    fps = 30
    canvas_w, canvas_h = 1080, 1920
    box_w, box_h = 1080, 1200
    y_off = (canvas_h - box_h) // 2  # 360px top & bottom pure black bars
    sr = 44100

    detect_fn, _ = _make_face_detector()
    segmenter = PersonSegmenter()

    with tempfile.TemporaryDirectory(prefix="aura_edit_") as td:
        tmp_dir = Path(td)
        raw_vid = tmp_dir / "video_raw.mp4"
        mix_wav = tmp_dir / "audio_mix.wav"

        # 1. Pre-build Act 1 (Scene) frames & clean dialogue track
        scene_boxes: list[np.ndarray] = []
        dialogue_chunks: list[np.ndarray] = []
        v_methods: list[str] = []
        for idx, seg in enumerate(scene_segments):
            sk = seg["src"]
            s0 = float(seg["start_s"])
            dur = float(seg["dur_s"])
            src_dur = float(seg.get("src_dur_s", dur))
            raw_frames = _slice_clip_frames_30fps(sources[sk], s0, src_dur, tmp_dir, f"sc_{idx}")
            target_f = max(1, int(round(dur * fps)))
            cropped = _crop_9x10_smart(
                raw_frames, box_w, box_h,
                zoom_start=float(seg.get("zoom_start", 1.0)),
                zoom_end=float(seg.get("zoom_end", 1.05)),
                detect_fn=detect_fn,
                cx_override=seg.get("cx_override"),
            )
            if abs(src_dur - dur) > 0.06 and len(cropped) >= 2:
                # Smooth optical-flow slow-mo for silent reaction/kiss payoff clips!
                cropped = _velocity_resample_optical(cropped, target_f)
            else:
                while len(cropped) < target_f and cropped:
                    cropped.append(cropped[-1].copy())
                cropped = cropped[:target_f]

            graded = [_apply_4k_cc_grade(f, warm_boost=1.05, sat_mult=1.08) for f in cropped]
            scene_boxes.extend(graded)

            seg_dur_actual = len(graded) / float(fps)
            target_n = int(round(seg_dur_actual * sr))
            if not seg.get("include_dialogue", True):
                # Silent visual reaction/makeout pocket — let the real song swell cleanly!
                dialogue_chunks.append(np.zeros((target_n, 2), dtype=np.float32))
                v_methods.append("music_pocket_swell")
            elif sk in vocal_sources:
                v_chunk = _slice_audio_segment(vocal_sources[sk], s0, seg_dur_actual, sr=sr)
                v_methods.append("provided_vocal")
                dialogue_chunks.append(v_chunk)
            else:
                vox_wav = tmp_dir / f"vox_{idx}.wav"
                m_used = isolate_clean_vocal_slice(str(sources[sk]), s0, s0 + seg_dur_actual, str(vox_wav), sr=sr)
                v_methods.append(m_used)
                v_chunk, _ = sf.read(str(vox_wav), dtype="float32", always_2d=True)
                if len(v_chunk) < target_n:
                    v_chunk = np.vstack([v_chunk, np.zeros((target_n - len(v_chunk), 2), dtype=np.float32)])
                else:
                    v_chunk = v_chunk[:target_n]
                dialogue_chunks.append(v_chunk)

        # Overlay @Proxeditz07 neon keyword captions onto Act 1 scene_boxes
        for fi in range(len(scene_boxes)):
            t_cur = fi / float(fps)
            for cap_item in scene_captions:
                c0, c1 = float(cap_item["t0"]), float(cap_item["t1"])
                if c0 <= t_cur <= c1:
                    scene_boxes[fi] = _draw_neon_keyword_caption(
                        scene_boxes[fi],
                        prefix_text=cap_item.get("prefix", ""),
                        highlight_text=cap_item.get("highlight", ""),
                        suffix_text=cap_item.get("suffix", ""),
                        accent_hex=cap_item.get("accent_hex", "#FF4818"),
                        pop_progress=max(0.0, t_cur - c0),
                    )
                    break

        # Add pre-drop blackout frames (`4 frames` = 0.133s total vacuum!)
        for _ in range(pre_drop_black_frames):
            scene_boxes.append(np.zeros((box_h, box_w, 3), dtype=np.uint8))
        if pre_drop_black_frames > 0:
            dialogue_chunks.append(np.zeros((int(round((pre_drop_black_frames / float(fps)) * sr)), 2), dtype=np.float32))

        drop_frame_idx = len(scene_boxes)
        drop_s = drop_frame_idx / float(fps)

        # 2. Build Act 2 (Cross-Movie Aura Velocity Montage)
        beat_s = 60.0 / bpm  # 0.48s
        montage_boxes: list[np.ndarray] = []
        for m_idx, mc in enumerate(montage_clips):
            sk = mc["src"]
            s0 = float(mc["start_s"])
            src_dur = float(mc.get("src_dur_s", 1.35))
            if "dur_s" in mc:
                out_frames_n = max(10, int(round(float(mc["dur_s"]) * fps)))
            else:
                beats = float(mc.get("beats", 2.0))
                out_frames_n = max(12, int(round(beats * beat_s * fps)))

            raw_m = _slice_clip_frames_30fps(sources[sk], s0, src_dur, tmp_dir, f"mc_{m_idx}")
            cropped_m = _crop_9x10_smart(
                raw_m, box_w, box_h,
                zoom_start=1.02, zoom_end=1.08,
                detect_fn=detect_fn,
                cx_override=mc.get("cx_override"),
            )
            # Farneback Optical-Flow Velocity Curve (2.7x fast whip -> 0.38x ultra-smooth slow-mo)
            vel_frames = _velocity_resample_optical(cropped_m, out_frames_n)
            graded_m = [_apply_4k_cc_grade(f, warm_boost=1.18, sat_mult=1.22) for f in vel_frames]

            # On Drop Clip #0, place giant 3D Hero Title BEHIND the AI-rotoscoped actor!
            if m_idx == 0 and hero_drop_title:
                graded_m = [_draw_roto_hero_text(f, hero_drop_title, segmenter) for f in graded_m]

            shaken_m = _apply_impact_shake_and_flash(
                graded_m,
                shake_px=float(mc.get("shake_px", 24.0 if m_idx == 0 else 18.0)),
                flash_peak=float(mc.get("flash_peak", 0.68 if m_idx == 0 else 0.44)),
                shockwave=bool(mc.get("shockwave", m_idx in (0, 4))),
            )
            montage_boxes.extend(shaken_m)

        # Smooth 10-frame fade-to-black at very end
        fade_f = min(10, len(montage_boxes))
        for k in range(fade_f):
            alpha_f = (fade_f - 1 - k) / float(max(1, fade_f))
            montage_boxes[-fade_f + k] = (montage_boxes[-fade_f + k].astype(np.float32) * alpha_f).astype(np.uint8)

        total_frames = len(scene_boxes) + len(montage_boxes)
        total_dur_s = total_frames / float(fps)

        # 3. Stream all 1080x1920 frames into libx264
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
        for box in scene_boxes + montage_boxes:
            canvas[y_off:y_off + box_h, 0:box_w] = box
            enc.stdin.write(canvas.tobytes())
        enc.stdin.close()
        enc.wait()

        # 4. Audio Engine: Prefer REAL Song Jigsaw Pocket & Amplitude Automation (`@thisiszohair` `7f2...` law!)
        dialogue_full = np.vstack(dialogue_chunks) if dialogue_chunks else np.zeros((0, 2), dtype=np.float32)
        if song_path is not None and Path(song_path).exists():
            master_mix = mix_real_song_jigsaw(
                song_path,
                song_offset_s=song_offset_s,
                total_dur_s=total_dur_s,
                drop_s=drop_s,
                dialogue_stereo=dialogue_full,
                sr=sr,
            )
            music_mode = f"real_song_jigsaw ({Path(song_path).name} @ {song_offset_s:.2f}s)"
        else:
            music = synthesize_phonk_aura_soundtrack(total_dur_s, drop_s, bpm=bpm, sr=sr)
            total_samples = len(music)
            if len(dialogue_full) < total_samples:
                dialogue_pad = np.vstack([dialogue_full, np.zeros((total_samples - len(dialogue_full), 2), dtype=np.float32)])
            else:
                dialogue_pad = dialogue_full[:total_samples]
            act1_n = min(total_samples, int(round(drop_s * sr)))
            if act1_n > 0:
                d_rms = float(np.sqrt(np.mean(dialogue_pad[:act1_n] ** 2))) + 1e-6
                dialogue_pad[:act1_n] = np.tanh((dialogue_pad[:act1_n] * (0.20 / d_rms)) * 1.15) * 0.86
            master_mix = dialogue_pad + music
            pk = float(np.max(np.abs(master_mix))) + 1e-8
            if pk > 0.94:
                master_mix *= 0.94 / pk
            music_mode = "synth_fallback"

        sf.write(str(mix_wav), master_mix, sr, subtype="PCM_16")

        # 5. Final mux + 2-stage EBUR128 / loudnorm (`-14.5 LUFS`, `level=false` true-peak limiter)
        subprocess.run(
            [
                ff, "-y",
                "-i", str(raw_vid), "-i", str(mix_wav),
                "-c:v", "copy",
                "-af", "loudnorm=I=-14.5:TP=-1.5:LRA=9,alimiter=limit=-1.5dB:level=false",
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
        "resolution": f"{canvas_w}x{canvas_h}",
        "active_viewport": f"{box_w}x{box_h} (9:10)",
        "drop_s": round(drop_s, 3),
        "duration_s": round(total_dur_s, 3),
        "scene_clips": len(scene_segments),
        "montage_clips": len(montage_clips),
        "vocal_isolation": sorted(set(v_methods)),
        "music_mode": music_mode,
        "size_mb": round(out_mp4.stat().st_size / (1024 * 1024), 2),
    }
