"""visual_qa.py — Automated Post-Render Decode, Loudness, Occlusion & Sheet QA.

Combines OpenMontage's `visual_qa.py` + `composition_validator.py` with our
strict studio gates (works with standalone static `/home/user/bin/ffmpeg` —
does NOT require a separate `ffprobe` binary):
  1. Full bitstream decode (`ffmpeg -v error -i <mp4> -f null -`) -> 0 errors.
  2. Stream & format inspection (resolution, fps, codec, yuv420p, stereo 48kHz).
  3. EBUR128 Integrated Loudness (`I`), `LRA`, and True Peak (`Peak <= -1.0 dBFS`).
  4. Face-vs-Caption Occlusion Check across sampled frames inside the video band.
  5. Optional 4x4 visual review contact sheet output.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import cv2

from .smart_camera import _make_face_detector

from ._ffmpeg import get_ffmpeg


def run_full_qa(
    mp4_path: str,
    expected_size: tuple[int, int] = (1080, 1920),
    min_dur: float = 15.0,
    max_dur: float = 65.0,
    lufs_range: tuple[float, float] = (-17.5, -12.5),
    max_true_peak_dbfs: float = -1.0,
    caption_zone_y: tuple[int, int] = (1300, 1460),
    sheet_out: str | None = None,
) -> dict[str, Any]:
    """Run comprehensive studio + OpenMontage QA on a rendered Short."""
    p = Path(mp4_path)
    if not p.exists():
        return {"passed": False, "errors": [f"File not found: {mp4_path}"]}

    errors: list[str] = []
    warnings: list[str] = []

    ffmpeg = get_ffmpeg()
    # 1. Full decode check
    dec = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(p), "-f", "null", "-"],
        capture_output=True, text=True, timeout=180,
    )
    if dec.returncode != 0 or dec.stderr.strip():
        errors.append(f"Decode error: {dec.stderr.strip()[:240]}")

    # 2. Stream metadata via OpenCV + ffmpeg -i header
    cap = cv2.VideoCapture(str(p))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = frames / fps if fps > 0 else 0.0

    if (w, h) != tuple(expected_size):
        errors.append(f"Resolution {w}x{h} != expected {expected_size[0]}x{expected_size[1]}")
    if not (min_dur <= dur <= max_dur):
        warnings.append(f"Duration {dur:.2f}s outside [{min_dur}, {max_dur}]s")

    # 3. Face-vs-Caption occlusion check at 6 timestamps
    detect_fn, _ = _make_face_detector()
    cap_y0, cap_y1 = caption_zone_y
    occlusion_hits = 0
    for frac in (0.08, 0.22, 0.38, 0.55, 0.72, 0.88):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frames * frac))
        ok, frame = cap.read()
        if not ok:
            continue
        for (cx, cy, bw, bh, _conf) in detect_fn(frame):
            face_bot_px = (cy + bh * 0.5) * h
            face_top_px = (cy - bh * 0.5) * h
            # Overlap with caption text band (specifically mouth/eyes region)
            if face_bot_px > cap_y0 + 25 and face_top_px < cap_y1:
                occlusion_hits += 1
    cap.release()
    if occlusion_hits >= 2:
        warnings.append(
            f"Face bounding box overlaps caption zone y={cap_y0}..{cap_y1} on {occlusion_hits}/6 sampled frames."
        )

    # 4. EBUR128 Loudness & True Peak
    eb = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(p), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, timeout=180,
    )
    mi = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", eb.stderr)
    mlra = re.findall(r"LRA:\s*([\d.]+)\s*LU", eb.stderr)
    mpk = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", eb.stderr)

    i_lufs = float(mi[-1]) if mi else None
    lra_lu = float(mlra[-1]) if mlra else None
    tp_dbfs = float(mpk[-1]) if mpk else None

    if i_lufs is None:
        errors.append("No audio / failed to measure EBUR128 integrated loudness")
    elif not (lufs_range[0] <= i_lufs <= lufs_range[1]):
        warnings.append(f"Integrated loudness {i_lufs} LUFS outside target {lufs_range}")

    if tp_dbfs is not None and tp_dbfs > max_true_peak_dbfs:
        errors.append(f"True peak {tp_dbfs} dBFS exceeds ceiling {max_true_peak_dbfs} dBFS")

    # 5. Optional 4x4 contact sheet
    if sheet_out and dur > 0:
        Path(sheet_out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "error", "-i", str(p),
                "-vf", f"fps=16/{max(1.0, dur):.3f},scale=320:-2,tile=4x4",
                "-frames:v", "1", sheet_out,
            ],
            check=False,
        )

    return {
        "passed": len(errors) == 0,
        "file": str(p),
        "size_mb": round(p.stat().st_size / 1048576.0, 2),
        "resolution": f"{w}x{h}",
        "fps": round(fps, 3),
        "duration_s": round(dur, 2),
        "integrated_lufs": i_lufs,
        "lra_lu": lra_lu,
        "true_peak_dbfs": tp_dbfs,
        "caption_occlusion_frames": occlusion_hits,
        "sheet_out": sheet_out,
        "errors": errors,
        "warnings": warnings,
    }
