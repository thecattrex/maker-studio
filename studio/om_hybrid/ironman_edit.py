"""ironman_edit.py — `@technocraftss` Iron Man-Style Difference-Typography + Optical-Flow Velocity Engine.

Implements the exact two-act After Effects / Alight Motion edit architecture
reverse-engineered from reference video #2 (`@technocraftss`), supporting both
native `16:9` (`1920x1080`) and Reels/Shorts `9:16` portrait (`1080x1920`) with a
dead-centered `16:9` (`1080x608`) cinema strip (`layout="9:16_center_16:9"`):

  Act 1 — Giant `DIFFERENCE`-Blend Typography (`|255 - BaseRGB|` at 3x supersampled
          glyph alpha) + scale-slam (`1.12 -> 1.00` easeOutExpo) + `5-frame` (`#000000`)
          hard black strobe cuts + 2-line pre-drop stacked slam + silent blackout tension gap.
  Act 2 — Beat-locked (`BPM` half-beat grid) Velocity Speed-Ramp Montage:
          Every cut hits a fast entry burst (`0..3 frames`) with smooth zoom-punch (`1.09 -> 1.02`)
          and subtle decaying camera impulse, settling into a `0.38x` silky slow-motion curve
          interpolated via bidirectional Farneback Optical Flow (`cv2.calcOpticalFlowFarneback`).
  Audio — Neural vocal isolation via `torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS` (strips 100%
          of trailer theme songs / background explosions / clanks so ONLY pure clean spoken voice
          remains) + clean Butterworth-filtered dark synthwave / edit beat (`125 BPM`) + subtle
          clean air transitions + 2-pass linear `loudnorm` (`-14.5 LUFS`, `-1.5 dBTP`).
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt

from ._ffmpeg import get_ffmpeg, get_ffprobe
from .sfx_sync import render_synced_sfx

ROOT_DIR = Path(__file__).resolve().parents[2]
FONTS_DIR = ROOT_DIR / "assets" / "fonts"


def _load_font(size_px: int, font_name: str = "ArchivoBlack-Regular.ttf") -> ImageFont.FreeTypeFont:
    cand = FONTS_DIR / font_name
    if not cand.exists():
        cand = FONTS_DIR / "Anton-Regular.ttf"
    return ImageFont.truetype(str(cand), size_px)


def render_supersampled_text_alpha(
    lines: list[str],
    w: int,
    h: int,
    font_px: int = 250,
    align: str = "center",
    scale: float = 1.0,
    letter_spacing: int = -5,
) -> np.ndarray:
    """Render razor-sharp supersampled glyph coverage mask in `[0..255]` (`H x W x 1` uint8)."""
    ss = 3 if w <= 1280 else 2
    sw, sh = w * ss, h * ss
    # Scale `font_px` & `letter_spacing` relative to 1920-wide reference viewport
    rel = w / 1920.0
    fpx = max(20, int(round(font_px * rel * ss * scale)))
    lspace = int(round(letter_spacing * rel * ss))
    font = _load_font(fpx)
    canvas = Image.new("L", (sw, sh), 0)
    draw = ImageDraw.Draw(canvas)

    line_metrics: list[tuple[str, int, int]] = []
    for ln in lines:
        adv_total = 0
        max_h = 0
        for idx, ch in enumerate(ln):
            bb = font.getbbox(ch)
            ch_h = bb[3] - bb[1]
            adv = int(round(font.getlength(ch)))
            adv_total += adv + (lspace if idx < len(ln) - 1 else 0)
            max_h = max(max_h, ch_h)
        line_metrics.append((ln, adv_total, max_h))

    line_gap = int(round(fpx * 0.08))
    total_h = sum(m[2] for m in line_metrics) + line_gap * max(0, len(line_metrics) - 1)
    cur_y = (sh - total_h) // 2 - int(round(fpx * 0.12))

    for ln, lw, lh in line_metrics:
        if align == "left":
            cur_x = int(round(sw * 0.085))
        else:
            cur_x = (sw - lw) // 2
        for ch in ln:
            draw.text((cur_x, cur_y), ch, fill=255, font=font)
            cur_x += int(round(font.getlength(ch))) + lspace
        cur_y += lh + line_gap

    arr = np.asarray(canvas, dtype=np.uint8)
    return cv2.resize(arr, (w, h), interpolation=cv2.INTER_AREA)[..., None]


def apply_difference_text(
    frame_bgr: np.ndarray,
    alpha_u8: np.ndarray,
    mode: str = "difference",
) -> np.ndarray:
    """Apply true After Effects `Blending Mode = Difference` (`|255 - Base|`) or solid white."""
    f = frame_bgr.astype(np.float32)
    alpha_mask = alpha_u8.astype(np.float32) * (1.0 / 255.0)
    if mode == "difference":
        inv = 255.0 - f
        inv = np.clip((inv - 128.0) * 1.16 + 132.0, 0.0, 255.0)
        out = f * (1.0 - alpha_mask) + inv * alpha_mask
    else:
        out = f * (1.0 - alpha_mask) + 255.0 * alpha_mask
    return np.clip(out, 0.0, 255.0).astype(np.uint8)


def optical_flow_interp(f0: np.ndarray, f1: np.ndarray, frac: float) -> np.ndarray:
    """Bidirectional Farneback optical-flow frame morphing for silky 0.38x velocity slow-mo."""
    if frac <= 0.02:
        return f0
    if frac >= 0.98:
        return f1
    h, w = f0.shape[:2]
    hw, hh = max(64, w // 2), max(64, h // 2)
    g0 = cv2.resize(cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY), (hw, hh))
    g1 = cv2.resize(cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY), (hw, hh))
    flow01 = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    flow01 = cv2.resize(flow01, (w, h), interpolation=cv2.INTER_LINEAR) * 2.0

    grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    map0_x = grid_x - flow01[..., 0] * frac
    map0_y = grid_y - flow01[..., 1] * frac
    map1_x = grid_x + flow01[..., 0] * (1.0 - frac)
    map1_y = grid_y + flow01[..., 1] * (1.0 - frac)

    w0 = cv2.remap(f0, map0_x, map0_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
    w1 = cv2.remap(f1, map1_x, map1_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
    return cv2.addWeighted(w0, 1.0 - frac, w1, frac, 0.0)


def extract_source_frames(video_path: str, start_s: float, end_s: float, w: int, h: int) -> tuple[list[np.ndarray], float]:
    """Decode exact frame-accurate slice `[start_s .. end_s]` resized to `(w, h)` (zero GOP drift)."""
    ffmpeg = get_ffmpeg()
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 23.976
    cap.release()

    pre_seek = max(0.0, start_s - 2.5)
    fine_seek = max(0.0, start_s - pre_seek)
    dur = max(0.15, end_s - start_s + 0.08)
    raw = subprocess.run(
        [
            ffmpeg, "-v", "error",
            "-ss", f"{pre_seek:.3f}",
            "-i", video_path,
            "-ss", f"{fine_seek:.3f}",
            "-t", f"{dur:.3f}",
            "-vf", f"scale={w}:{h}:flags=lanczos",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
        ],
        capture_output=True,
        check=True,
    ).stdout
    frame_bytes = w * h * 3
    n_f = len(raw) // frame_bytes
    arr = np.frombuffer(raw[: n_f * frame_bytes], dtype=np.uint8).reshape((n_f, h, w, 3))
    return [arr[i] for i in range(n_f)], fps


_VIG_CACHE: dict[tuple[int, int], np.ndarray] = {}


def cinema_moody_grade(frame_bgr: np.ndarray, boost_glow: float = 1.0) -> np.ndarray:
    """Dark moody armor contrast grade: deep shadows + vivid highlights/glows (`@technocraftss` look)."""
    h, w = frame_bgr.shape[:2]
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.ogrid[:h, :w]
        yn = (yy - h * 0.5) / (h * 0.5)
        xn = (xx - w * 0.5) / (w * 0.5)
        _VIG_CACHE[(h, w)] = np.clip(1.0 - 0.20 * (xn * xn + yn * yn), 0.75, 1.0).astype(np.float32)[..., None]
    vig = _VIG_CACHE[(h, w)]

    f = frame_bgr.astype(np.float32) * (1.0 / 255.0)
    luma = 0.114 * f[..., 0] + 0.587 * f[..., 1] + 0.299 * f[..., 2]
    curved = np.clip(0.5 + (f - 0.48) * 1.20, 0.0, 1.0)
    mean_c = np.mean(curved, axis=-1, keepdims=True)
    sat = 1.16 + 0.20 * (luma[..., None] ** 1.5) * boost_glow
    graded = np.clip(mean_c + (curved - mean_c) * sat, 0.0, 1.0)
    return np.clip(graded * vig * 255.0, 0.0, 255.0).astype(np.uint8)


def transform_zoom_shake(
    frame_bgr: np.ndarray,
    zoom: float,
    dx_px: float = 0.0,
    dy_px: float = 0.0,
    rot_deg: float = 0.0,
) -> np.ndarray:
    """Sub-pixel `INTER_LANCZOS4` affine zoom + clean subtle camera motion."""
    h, w = frame_bgr.shape[:2]
    mat = cv2.getRotationMatrix2D((w * 0.5, h * 0.5), rot_deg, zoom)
    mat[0, 2] += dx_px
    mat[1, 2] += dy_px
    return cv2.warpAffine(frame_bgr, mat, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT101)


def _lp_filter(sig: np.ndarray, cutoff_hz: float, sr: int, order: int = 4) -> np.ndarray:
    sos = butter(order, cutoff_hz / (0.5 * sr), btype="low", output="sos")
    return sosfilt(sos, sig)


def _hp_filter(sig: np.ndarray, cutoff_hz: float, sr: int, order: int = 2) -> np.ndarray:
    sos = butter(order, cutoff_hz / (0.5 * sr), btype="high", output="sos")
    return sosfilt(sos, sig)


def synthesize_clean_dark_edit_music(
    total_dur_s: float,
    drop_s: float,
    beat_s: float = 0.48,
    blackout_window: tuple[float, float] = (10.62, 11.04),
    phrase_hits: list[float] | None = None,
    sr: int = 48000,
) -> np.ndarray:
    """Synthesize an ultra-clean 48 kHz Dark Synthwave / Edit soundtrack (ZERO harsh metallic noise).

    - Act 1 (`0 .. blackout_window[0]`): Warm Butterworth-filtered dark analog D-minor pad
      (`D2 + A2 + D3 + F3`) + soft clean sub-pulse on phrase entries so isolated vocals sit crystal clear.
    - Blackout (`blackout_window[0] .. drop_s`): Pure digital silence under the isolated whisper!
    - Act 2 (`drop_s .. end`): Tight punchy electronic kick + crisp snare + sidechained warm dark
      analog bassline (`D -> Bb -> G -> A`) + smooth filtered dark synth lead, fading cleanly to 0 at end.
    """
    n = int(round(total_dur_s * sr))
    t = np.arange(n, dtype=np.float64) / sr
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    # 1. Act 1 Warm Filtered Dark Analog Pad (`0 .. blackout_window[0]`)
    act1_end = min(n, int(round(blackout_window[0] * sr)))
    if act1_end > 100:
        tt = t[:act1_end]
        # Detuned warm analog saws on D-minor chord (D2=73.42, A2=110.0, D3=146.83, F3=174.61)
        def _saw(freq: float, ph_off: float = 0.0) -> np.ndarray:
            p = (tt * freq + ph_off) % 1.0
            return 2.0 * p - 1.0

        pad_l = 0.35 * _saw(73.42, 0.0) + 0.25 * _saw(110.00, 0.13) + 0.22 * _saw(146.83, 0.37) + 0.18 * _saw(174.61, 0.61)
        pad_r = 0.35 * _saw(73.55, 0.5) + 0.25 * _saw(110.18, 0.71) + 0.22 * _saw(147.05, 0.19) + 0.18 * _saw(174.88, 0.83)
        pad_l = _lp_filter(pad_l, 420.0, sr, order=4) * 0.16
        pad_r = _lp_filter(pad_r, 420.0, sr, order=4) * 0.16

        fade = np.minimum(1.0, tt / 0.45) * np.minimum(1.0, np.maximum(0.0, (blackout_window[0] - tt) / 0.14))
        left[:act1_end] += pad_l * fade
        right[:act1_end] += pad_r * fade

        # Soft clean cinema sub-heartbeat on Act 1 phrase openings (pure smooth sine, zero click/clank)
        for pt in (phrase_hits or [0.04, 1.90, 3.60, 6.52, 9.68]):
            if pt >= blackout_window[0] - 0.15:
                continue
            i0 = int(round(pt * sr))
            ln = min(int(0.42 * sr), act1_end - i0)
            if ln > 32:
                ht = np.arange(ln, dtype=np.float64) / sr
                f_env = 46.0 + 48.0 * np.exp(-ht * 24.0)
                ph = 2 * np.pi * np.cumsum(f_env) / sr
                env = np.exp(-ht * 6.5) * np.sin(np.minimum(1.0, ht / 0.008) * (np.pi * 0.5))
                sub = 0.24 * np.sin(ph) * env
                left[i0:i0 + ln] += sub
                right[i0:i0 + ln] += sub

        # Smooth filtered air riser into blackout (`blackout_window[0] - 1.6s .. blackout_window[0]`)
        r_s0 = max(0.0, blackout_window[0] - 1.6)
        ri0, ri1 = int(round(r_s0 * sr)), act1_end
        if ri1 > ri0 + 100:
            rt = np.linspace(0.0, 1.0, ri1 - ri0)
            rng_r = np.random.default_rng(19)
            air = _lp_filter(_hp_filter(rng_r.standard_normal(ri1 - ri0), 300.0, sr), 2200.0, sr)
            riser_env = (rt ** 2.4) * np.minimum(1.0, np.maximum(0.0, (1.0 - rt) / 0.06))
            left[ri0:ri1] += air * riser_env * 0.09
            right[ri0:ri1] += air * riser_env * 0.09

    # 2. Act 2 Clean Dark Synthwave / Edit Drop (`drop_s .. total_dur_s`)
    i_drop = int(round(drop_s * sr))
    act2_len = n - i_drop
    if act2_len > 100:
        at = np.arange(act2_len, dtype=np.float64) / sr
        # Chord progression every 4 half-beats (1.92s per bar): Dm -> Bb -> Gm -> A
        bass_roots = [36.71, 29.14, 24.50, 27.50]      # D1, Bb0, G0, A0 (warm sub + octave)
        lead_notes = [293.66, 349.23, 261.63, 220.00,  # D4, F4, C4, A3
                      233.08, 293.66, 261.63, 220.00,  # Bb3, D4, C4, A3
                      196.00, 233.08, 293.66, 261.63,  # G3, Bb3, D4, C4
                      220.00, 277.18, 329.63, 277.18]  # A3, C#4, E4, C#4 (harmonic minor!)

        bar_idx = np.floor(at / (beat_s * 4.0)).astype(int) % len(bass_roots)
        step_idx = np.floor(at / beat_s).astype(int) % len(lead_notes)
        f_bass = np.array([bass_roots[b] for b in bar_idx], dtype=np.float64)
        f_lead = np.array([lead_notes[s] for s in step_idx], dtype=np.float64)

        # Sidechain pump envelope locked to every `beat_s` (`0.48s`) cut!
        beat_phase = (at % beat_s) / beat_s
        sidechain = 0.25 + 0.75 * (1.0 - np.exp(-beat_phase * 5.5))

        # Warm analog Reese bass (fundamental sine + filtered saw octave)
        ph_b1 = 2 * np.pi * np.cumsum(f_bass) / sr
        ph_b2_l = (np.cumsum(f_bass * 2.002) / sr) % 1.0
        ph_b2_r = (np.cumsum(f_bass * 1.998) / sr + 0.35) % 1.0
        saw_b_l = _lp_filter(2.0 * ph_b2_l - 1.0, 280.0, sr, order=4)
        saw_b_r = _lp_filter(2.0 * ph_b2_r - 1.0, 280.0, sr, order=4)
        bass_l = (0.30 * np.sin(ph_b1) + 0.16 * saw_b_l) * sidechain
        bass_r = (0.30 * np.sin(ph_b1) + 0.16 * saw_b_r) * sidechain

        # Smooth dark synthwave lead (detuned stereo saws low-passed at 1550 Hz — lush, zero metallic harshness!)
        ph_l_l = (np.cumsum(f_lead * 1.003) / sr) % 1.0
        ph_l_r = (np.cumsum(f_lead * 0.997) / sr + 0.25) % 1.0
        note_env = np.exp(-beat_phase * 2.2) * np.minimum(1.0, beat_phase / 0.04)
        lead_l = _lp_filter((2.0 * ph_l_l - 1.0) * note_env, 1550.0, sr, order=4) * 0.11 * sidechain
        lead_r = _lp_filter((2.0 * ph_l_r - 1.0) * note_env, 1550.0, sr, order=4) * 0.11 * sidechain

        left[i_drop:] += bass_l + lead_l
        right[i_drop:] += bass_r + lead_r

        # Clean punchy electronic kick on every half-beat (`0.48s`) + crisp snare on odd beats + silky 16th hats
        rng_d = np.random.default_rng(11)
        k = 0
        while True:
            bt = drop_s + k * beat_s
            # Stop drums 0.85s before the end so the final hero shot resolves smoothly on the synth chord!
            if bt >= total_dur_s - 0.85:
                break
            i0 = int(round(bt * sr))
            ln = min(int(0.28 * sr), n - i0)
            ht = np.arange(ln, dtype=np.float64) / sr

            # Tight studio punch kick (150 Hz -> 48 Hz fast pitch sweep, clean warm body)
            fk = 48.0 + 112.0 * np.exp(-ht * 46.0)
            pk = 2 * np.pi * np.cumsum(fk) / sr
            ek = np.exp(-ht * 11.5) * np.minimum(1.0, ht / 0.0025)
            kick = 0.42 * np.tanh(1.35 * np.sin(pk)) * ek
            left[i0:i0 + ln] += kick
            right[i0:i0 + ln] += kick

            # Clean crisp snare on odd half-beats (`k % 2 == 1`)
            if k % 2 == 1:
                sln = min(int(0.15 * sr), n - i0)
                st = np.arange(sln, dtype=np.float64) / sr
                sn_air = _lp_filter(_hp_filter(rng_d.standard_normal(sln), 900.0, sr), 6800.0, sr) * np.exp(-st * 24.0)
                sn_body = np.sin(2 * np.pi * 188.0 * st) * np.exp(-st * 30.0)
                sn = 0.20 * (0.68 * sn_air + 0.32 * sn_body)
                left[i0:i0 + sln] += sn
                right[i0:i0 + sln] += sn * 0.96

            # Soft clean hi-hat on the off-beat (`bt + 0.5 * beat_s`)
            h_t = bt + 0.5 * beat_s
            if h_t < total_dur_s - 0.90:
                hi0 = int(round(h_t * sr))
                hln = min(int(0.045 * sr), n - hi0)
                if hln > 16:
                    htt = np.arange(hln, dtype=np.float64) / sr
                    hh = _hp_filter(rng_d.standard_normal(hln), 5500.0, sr) * np.exp(-htt * 65.0) * 0.055
                    left[hi0:hi0 + hln] += hh
                    right[hi0:hi0 + hln] += hh * 0.9

            k += 1

    # Smooth 1.15s cosine fade-out at the end so the ending is 100% clean with zero abrupt tail!
    tail_n = min(n, int(1.15 * sr))
    cos_fade = 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, tail_n)))
    left[-tail_n:] *= cos_fade
    right[-tail_n:] *= cos_fade
    return np.stack([left, right], axis=1)


_HDEMUCS_BUNDLE: Any = None
_HDEMUCS_MODEL: Any = None


def isolate_clean_vocal_slice(
    src_video: str,
    src_s: float,
    src_e: float,
    out_wav: str,
    sr: int = 48000,
) -> str:
    """Extract `[src_s .. src_e]` and strip 100% of background music/theme/SFX via Neural HDemucs."""
    global _HDEMUCS_BUNDLE, _HDEMUCS_MODEL
    ffmpeg = get_ffmpeg()
    dur_v = max(0.12, src_e - src_s)
    pad_pre = min(0.45, src_s)
    pad_post = 0.45
    padded_wav = out_wav + ".pad.wav"

    # Extract padded slice at 44100 Hz stereo (HDemucs native sample rate)
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "error",
            "-ss", f"{src_s - pad_pre:.3f}",
            "-t", f"{dur_v + pad_pre + pad_post:.3f}",
            "-i", src_video,
            "-ar", "44100", "-ac", "2",
            padded_wav,
        ],
        check=True,
    )

    method = "center_eq_fallback"
    try:
        import torch
        import torchaudio

        if _HDEMUCS_MODEL is None:
            _HDEMUCS_BUNDLE = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
            _HDEMUCS_MODEL = _HDEMUCS_BUNDLE.get_model()
            _HDEMUCS_MODEL.eval()

        audio_44k, sr_in = sf.read(padded_wav, dtype="float32", always_2d=True)
        wav_t = torch.from_numpy(audio_44k.T).unsqueeze(0)  # (1, 2, T)
        ref_std = wav_t.std() + 1e-6
        with torch.no_grad():
            sources = _HDEMUCS_MODEL((wav_t / ref_std)) * ref_std
        # sources order in HDEMUCS_HIGH_MUSDB_PLUS: ['drums', 'bass', 'other', 'vocals']
        vox_44k = sources[0, 3].cpu().numpy().T  # (T, 2)
        i_trim0 = int(round(pad_pre * sr_in))
        i_trim1 = min(len(vox_44k), i_trim0 + int(round(dur_v * sr_in)))
        vox_slice = vox_44k[i_trim0:i_trim1]

        # Soft RMS noise gate so silence between words has zero residual breath/music bleed
        mono_env = np.sqrt(np.convolve(np.mean(vox_slice ** 2, axis=1), np.ones(882) / 882.0, mode="same") + 1e-12)
        peak_env = max(1e-4, float(np.max(mono_env)))
        gate = np.clip((mono_env / peak_env - 0.035) / 0.085, 0.0, 1.0)[:, None]
        vox_slice = vox_slice * gate

        raw_vox_44k = out_wav + ".vox44.wav"
        sf.write(raw_vox_44k, vox_slice, sr_in, subtype="PCM_24")
        fade_out_st = max(0.02, dur_v - 0.07)
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "error",
                "-i", raw_vox_44k,
                "-af", (
                    f"highpass=f=115,lowpass=f=8800,"
                    f"acompressor=threshold=-20dB:ratio=2.8:makeup=3.5dB,"
                    f"afade=t=in:st=0:d=0.04,afade=t=out:st={fade_out_st:.3f}:d=0.07"
                ),
                "-ar", str(sr), "-ac", "2",
                out_wav,
            ],
            check=True,
        )
        os.remove(raw_vox_44k)
        method = "hdemucs_neural"
    except Exception:
        # Fallback if torch/torchaudio unavailable locally: extract mid-channel speech band
        fade_out_st = max(0.02, dur_v - 0.07)
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "error",
                "-ss", f"{src_s:.3f}", "-t", f"{dur_v:.3f}",
                "-i", src_video,
                "-af", (
                    f"pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,"
                    f"highpass=f=130,lowpass=f=7500,"
                    f"afade=t=in:st=0:d=0.04,afade=t=out:st={fade_out_st:.3f}:d=0.07"
                ),
                "-ar", str(sr), "-ac", "2",
                out_wav,
            ],
            check=True,
        )
    finally:
        if os.path.exists(padded_wav):
            os.remove(padded_wav)
    return method


def render_ironman_style_edit(spec: dict[str, Any], out_mp4: str) -> dict[str, Any]:
    """Render a complete 2-act `@technocraftss` Iron Man-style edit from `spec`.

    Supports:
      - `layout = "9:16_center_16:9"`: Outer `1080x1920` (`9:16`) portrait canvas with a centered
        `1080x608` (`16:9`) cinema viewport (`y = 656..1264`) and pure `#000000` top/bottom bars.
      - `layout = "16:9"` (default): Full-bleed `width x height` (`1920x1080`).
    """
    ffmpeg = get_ffmpeg()
    get_ffprobe()
    layout = spec.get("layout", "16:9")
    if layout == "9:16_center_16:9":
        out_w = int(spec.get("width", 1080))
        out_h = int(spec.get("height", 1920))
        vw = out_w
        vh = (int(round(vw * 9.0 / 16.0)) // 2) * 2  # 608 px for 1080 width
        vy0 = (out_h - vh) // 2
    else:
        out_w = int(spec.get("width", 1920))
        out_h = int(spec.get("height", 1080))
        vw, vh, vy0 = out_w, out_h, 0

    out_fps = int(spec.get("fps", 30))
    drop_s = float(spec["drop_s"])
    beat_s = float(spec.get("beat_s", 0.48))
    total_dur_s = float(spec["total_dur_s"])
    total_frames = int(round(total_dur_s * out_fps))
    shake_scale = vw / 1920.0

    work = Path(tempfile.mkdtemp(prefix="ironman_edit_"))
    raw_vid = work / "video_only.mp4"

    clip_cache: dict[tuple[str, float, float], tuple[list[np.ndarray], float]] = {}

    def _get_clip(src_p: str, s0: float, s1: float) -> tuple[list[np.ndarray], float]:
        key = (src_p, round(s0, 3), round(s1, 3))
        if key not in clip_cache:
            clip_cache.clear()
            clip_cache[key] = extract_source_frames(src_p, s0, s1, vw, vh)
        return clip_cache[key]

    enc = subprocess.Popen(
        [
            ffmpeg, "-y", "-v", "warning",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{out_w}x{out_h}", "-r", str(out_fps),
            "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-x264-params", "rc-lookahead=20",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            str(raw_vid),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None

    act1_events = spec["act1_segments"]
    act2_cuts = spec["act2_velocity_cuts"]

    mask_cache: dict[tuple[Any, ...], np.ndarray] = {}

    def _text_mask(lines: list[str], font_px: int, align: str, scale: float) -> np.ndarray:
        k = (tuple(lines), font_px, align, round(scale, 2))
        if k not in mask_cache:
            if len(mask_cache) >= 8:
                mask_cache.clear()
            mask_cache[k] = render_supersampled_text_alpha(lines, vw, vh, font_px=font_px, align=align, scale=scale)
        return mask_cache[k]

    prev_act2_inner: np.ndarray | None = None
    outer_canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    for fi in range(total_frames):
        t_s = fi / out_fps

        if t_s < drop_s:
            seg = next((s for s in act1_events if s["t0"] <= t_s < s["t1"]), None)
            if seg is None or seg.get("blackout"):
                inner = np.zeros((vh, vw, 3), dtype=np.uint8)
            else:
                frames_src, src_fps = _get_clip(seg["src"], seg["src_s0"], seg["src_s1"])
                local_t = t_s - seg["t0"]
                src_pos = min(len(frames_src) - 1.001, max(0.0, local_t * seg.get("speed", 0.85) * src_fps))
                idx0 = int(math.floor(src_pos))
                frac = src_pos - idx0
                idx1 = min(len(frames_src) - 1, idx0 + 1)
                base = cv2.addWeighted(frames_src[idx0], 1.0 - frac, frames_src[idx1], frac, 0.0)
                base = cinema_moody_grade(base, boost_glow=1.22)

                prog = local_t / max(0.05, seg["t1"] - seg["t0"])
                zoom = seg.get("z0", 1.02) + (seg.get("z1", 1.08) - seg.get("z0", 1.02)) * prog
                dx = 3.0 * shake_scale * math.sin(t_s * 4.6)
                dy = 2.2 * shake_scale * math.cos(t_s * 3.9)
                inner = transform_zoom_shake(base, zoom=zoom, dx_px=dx, dy_px=dy)

                for wcard in seg.get("words", []):
                    if wcard["w0"] <= t_s < wcard["w1"]:
                        wt = t_s - wcard["w0"]
                        slam = 1.0 + 0.12 * math.exp(-wt * 26.0)
                        mask = _text_mask(
                            wcard["lines"],
                            font_px=int(wcard.get("font_px", 245)),
                            align=wcard.get("align", "center"),
                            scale=slam,
                        )
                        inner = apply_difference_text(inner, mask, mode=wcard.get("blend", "difference"))
                        break
        else:
            vseg = next((c for c in act2_cuts if c["t0"] <= t_s < c["t1"]), act2_cuts[-1])
            frames_src, src_fps = _get_clip(vseg["src"], vseg["src_s0"], vseg["src_s1"])
            seg_dur = max(0.08, vseg["t1"] - vseg["t0"])
            u = min(1.0, max(0.0, (t_s - vseg["t0"]) / seg_dur))

            mapped_u = u ** 0.44
            max_span = min(len(frames_src) - 1.001, seg_dur * 0.92 * src_fps)
            src_pos = min(len(frames_src) - 1.001, max(0.0, mapped_u * max_span))
            idx0 = int(math.floor(src_pos))
            frac = src_pos - idx0
            idx1 = min(len(frames_src) - 1, idx0 + 1)

            local_f = int(round((t_s - vseg["t0"]) * out_fps))
            if local_f <= 2:
                interp = cv2.addWeighted(frames_src[idx0], 1.0 - frac, frames_src[idx1], frac, 0.0)
            else:
                interp = optical_flow_interp(frames_src[idx0], frames_src[idx1], frac)

            graded = cinema_moody_grade(interp, boost_glow=1.30)

            # Clean controlled zoom-punch (`1.09 -> 1.02`) + smooth micro-impulse
            decay = math.exp(-u * 9.0)
            zoom = 1.02 + 0.07 * decay + 0.018 * u
            twitch_y = 8.0 * shake_scale * decay * math.cos(local_f * 2.2)
            twitch_x = 4.5 * shake_scale * decay * math.sin(local_f * 1.8)
            rot = 0.55 * decay * (1 if (act2_cuts.index(vseg) % 2 == 0) else -1)
            inner = transform_zoom_shake(graded, zoom=zoom, dx_px=twitch_x, dy_px=twitch_y, rot_deg=rot)

            if local_f == 0:
                inner = np.clip(inner.astype(np.float32) * 1.18 + 12.0, 0, 255).astype(np.uint8)
                if prev_act2_inner is not None:
                    inner = cv2.addWeighted(inner, 0.82, prev_act2_inner, 0.18, 0.0)
            elif local_f == 1 and prev_act2_inner is not None:
                inner = cv2.addWeighted(inner, 0.86, prev_act2_inner, 0.14, 0.0)

            prev_act2_inner = inner

        # Clean smooth fade-to-black over final 0.38s
        rem_s = total_dur_s - t_s
        if rem_s < 0.38:
            vf = max(0.0, rem_s / 0.38)
            inner = np.clip(inner.astype(np.float32) * vf, 0.0, 255.0).astype(np.uint8)

        if layout == "9:16_center_16:9":
            outer_canvas.fill(0)
            outer_canvas[vy0:vy0 + vh, 0:vw] = inner
            enc.stdin.write(outer_canvas.tobytes())
        else:
            enc.stdin.write(inner.tobytes())

    enc.stdin.close()
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg rawvideo encode failed with exit code {rc}")

    # ---------------- CLEAN AUDIO MASTERING (Neural Isolated Vocals + Clean Dark Synthwave) ----------------
    sr = 48000
    n_samples = int(round(total_dur_s * sr))
    phrase_hits = [float(s["t0"]) for s in act1_events]
    mix = synthesize_clean_dark_edit_music(
        total_dur_s=total_dur_s,
        drop_s=drop_s,
        beat_s=beat_s,
        blackout_window=tuple(spec.get("blackout_window", (drop_s - 0.42, drop_s))),
        phrase_hits=phrase_hits,
        sr=sr,
    )

    def _overlay_wav(wav_path: str, dst_t: float, gain_db: float = 0.0) -> None:
        a, file_sr = sf.read(wav_path, dtype="float64", always_2d=True)
        if file_sr != sr:
            tmp_r = work / f"rs_{os.path.basename(wav_path)}"
            subprocess.run([ffmpeg, "-y", "-v", "error", "-i", wav_path, "-ar", str(sr), "-ac", "2", str(tmp_r)], check=True)
            a, _ = sf.read(str(tmp_r), dtype="float64", always_2d=True)
        if a.shape[1] == 1:
            a = np.repeat(a, 2, axis=1)
        g = 10.0 ** (gain_db / 20.0)
        i0 = max(0, int(round(dst_t * sr)))
        ln = min(len(a), n_samples - i0)
        if ln > 0:
            mix[i0:i0 + ln] += a[:ln, :2] * g

    # 1. Isolate clean RDJ / character vocals via Neural HDemucs (ZERO Avengers theme / trailer SFX!)
    vocal_methods: list[str] = []
    for idx, vox in enumerate(spec.get("vocal_clips", [])):
        vox_wav = work / f"vox_iso_{idx:02d}.wav"
        m = isolate_clean_vocal_slice(
            vox["src"],
            float(vox["src_s"]),
            float(vox["src_e"]),
            str(vox_wav),
            sr=sr,
        )
        vocal_methods.append(m)
        _overlay_wav(str(vox_wav), float(vox["dst_t"]), gain_db=float(vox.get("gain_db", 4.5)))

    # 2. Place ONLY subtle, clean, non-metallic air/sub cues explicitly requested in `sfx_cues`
    for idx, cue in enumerate(spec.get("sfx_cues", [])):
        sfx_wav = work / f"sfx_{idx:02d}.wav"
        meta = render_synced_sfx(cue["sfx_id"], str(sfx_wav), cut_time_s=float(cue["at_s"]))
        _overlay_wav(str(sfx_wav), float(meta["insert_at_s"]), gain_db=float(cue.get("gain_db", -4.5)))

    raw_mix_wav = work / "raw_mix.wav"
    peak = float(np.max(np.abs(mix))) if len(mix) else 1.0
    if peak > 0.95:
        mix = mix * (0.92 / peak)
    sf.write(str(raw_mix_wav), mix, sr, subtype="PCM_24")

    # 3. True Two-Pass Linear EBU R128 Mastering (`-14.5 LUFS`, `-1.5 dBTP`)
    p1 = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-nostats", "-i", str(raw_mix_wav),
            "-af", "loudnorm=I=-14.5:TP=-1.5:LRA=9:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    )
    j0 = p1.stderr.rfind("{")
    j1 = p1.stderr.rfind("}") + 1
    ln = json.loads(p1.stderr[j0:j1])
    ln_af = (
        f"loudnorm=I=-14.5:TP=-1.5:LRA=9:"
        f"measured_I={ln['input_i']}:measured_TP={ln['input_tp']}:"
        f"measured_LRA={ln['input_lra']}:measured_thresh={ln['input_thresh']}:"
        f"offset={ln['target_offset']}:linear=true,"
        f"alimiter=limit=0.83:level=false:attack=5:release=50"
    )

    out_p = Path(out_mp4).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "warning",
            "-i", str(raw_vid), "-i", str(raw_mix_wav),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-af", ln_af,
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-shortest",
            str(out_p),
        ],
        check=True,
    )
    shutil.rmtree(work, ignore_errors=True)
    return {
        "out_mp4": str(out_p),
        "size_mb": round(out_p.stat().st_size / 1048576.0, 2),
        "duration_s": total_dur_s,
        "layout": layout,
        "width": out_w,
        "height": out_h,
        "viewport_16x9": f"{vw}x{vh}@y={vy0}",
        "resolution": f"{out_w}x{out_h}",
        "fps": out_fps,
        "vocal_isolation": sorted(set(vocal_methods)),
    }
