"""cinema_looks.py — Deterministic 3D .cube LUT Color Grading Engine.

Adapted from `heygen-com/hyperframes` (`skills/media-use/luts`, Apache-2.0).
Generates standard Adobe/Resolve `.cube` 3D LUT files purely offline with NumPy
in <5ms (~0 MB extra RAM) and applies them via FFmpeg `lut3d` filter — works
both locally inside the 2 GB Arena sandbox and on the GitHub Cloud Render Farm.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from ._ffmpeg import get_ffmpeg

LOOKS_CATALOG: dict[str, dict[str, Any]] = {
    "teal-orange-blockbuster": {
        "description": "Teal shadows and warm orange highlights for blockbuster movie clips.",
        "intensity": 0.85,
        "contrast": 0.18,
        "saturation": 0.08,
        "vibrance": 0.12,
        "temperature": 0.0,
        "blacks": 0.0,
        "shadows_lift": 0.0,
        "highlights_gain": 0.0,
        "split_shadows": (-0.04, 0.05, 0.09),
        "split_highlights": (0.10, 0.04, -0.03),
        "split_intensity": 0.62,
        "split_balance": 0.52,
    },
    "bleach-bypass": {
        "description": "High-contrast desaturated gritty thriller/action cinema look.",
        "intensity": 0.80,
        "contrast": 0.45,
        "saturation": -0.58,
        "vibrance": -0.20,
        "temperature": -0.02,
        "blacks": -0.03,
        "shadows_lift": -0.06,
        "highlights_gain": 0.08,
        "split_shadows": (-0.01, 0.0, 0.02),
        "split_highlights": (0.02, 0.02, 0.0),
        "split_intensity": 0.25,
        "split_balance": 0.50,
    },
    "film-fade": {
        "description": "Soft faded vintage 35mm film wash with lifted blacks and warm highlights.",
        "intensity": 0.75,
        "contrast": -0.18,
        "saturation": -0.10,
        "vibrance": -0.06,
        "temperature": 0.14,
        "blacks": 0.06,
        "shadows_lift": 0.05,
        "highlights_gain": -0.02,
        "split_shadows": (0.02, 0.01, -0.01),
        "split_highlights": (0.06, 0.03, -0.03),
        "split_intensity": 0.35,
        "split_balance": 0.50,
    },
    "warm-cinema": {
        "description": "Golden warm skin tones with rich contrast for comedy/drama dialogue.",
        "intensity": 0.80,
        "contrast": 0.14,
        "saturation": 0.10,
        "vibrance": 0.14,
        "temperature": 0.10,
        "blacks": -0.01,
        "shadows_lift": 0.0,
        "highlights_gain": 0.03,
        "split_shadows": (0.01, 0.0, -0.01),
        "split_highlights": (0.07, 0.03, -0.03),
        "split_intensity": 0.40,
        "split_balance": 0.55,
    },
    "crisp-editorial": {
        "description": "Clean punchy micro-contrast and vibrant color for explainers & rankings.",
        "intensity": 0.85,
        "contrast": 0.20,
        "saturation": 0.12,
        "vibrance": 0.18,
        "temperature": 0.01,
        "blacks": -0.02,
        "shadows_lift": -0.02,
        "highlights_gain": 0.04,
        "split_shadows": (-0.01, 0.01, 0.03),
        "split_highlights": (0.03, 0.02, 0.0),
        "split_intensity": 0.25,
        "split_balance": 0.50,
    },
    "scifi-cool": {
        "description": "Crisp cyan-steel space & sci-fi palette with deep blacks.",
        "intensity": 0.82,
        "contrast": 0.22,
        "saturation": -0.05,
        "vibrance": 0.10,
        "temperature": -0.10,
        "blacks": -0.02,
        "shadows_lift": -0.02,
        "highlights_gain": 0.04,
        "split_shadows": (-0.05, 0.03, 0.08),
        "split_highlights": (-0.01, 0.04, 0.06),
        "split_intensity": 0.50,
        "split_balance": 0.48,
    },
}


def list_cinema_looks() -> list[dict[str, Any]]:
    return [
        {"id": k, "description": v["description"], "default_intensity": v["intensity"]}
        for k, v in LOOKS_CATALOG.items()
    ]


def generate_cube_lut(
    look_id: str,
    out_cube_path: str | None = None,
    size: int = 17,
    intensity: float | None = None,
) -> str:
    """Generate a deterministic 3D `.cube` LUT file and return its path."""
    if look_id not in LOOKS_CATALOG:
        raise ValueError(f"Unknown look '{look_id}'. Available: {sorted(LOOKS_CATALOG)}")
    p = LOOKS_CATALOG[look_id]
    mix = float(p["intensity"] if intensity is None else intensity)
    mix = max(0.0, min(1.0, mix))

    if out_cube_path is None:
        lut_dir = Path("/tmp/om_hybrid_luts")
        lut_dir.mkdir(parents=True, exist_ok=True)
        out_cube_path = str(lut_dir / f"{look_id}_{int(round(mix * 100))}.cube")

    grid = np.linspace(0.0, 1.0, size, dtype=np.float32)
    # .cube order: R fastest, then G, then B slowest
    bb, gg, rr = np.meshgrid(grid, grid, grid, indexing="ij")
    rgb0 = np.stack([rr.ravel(), gg.ravel(), bb.ravel()], axis=-1)
    rgb = rgb0.copy()

    # 1) Black point & shadow/highlight lift
    luma = 0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2]
    sh_mask = (1.0 - luma) ** 2
    hi_mask = luma ** 2
    rgb += p["blacks"] * ((1.0 - luma) ** 3)[:, None]
    rgb += p["shadows_lift"] * sh_mask[:, None]
    rgb += p["highlights_gain"] * hi_mask[:, None]

    # 2) S-curve contrast around midpoint 0.5
    c = float(p["contrast"])
    if abs(c) > 1e-4:
        rgb = np.clip(rgb, 0.0, 1.0)
        factor = 1.0 + c
        rgb = 0.5 + (rgb - 0.5) * factor

    # 3) Color temperature shift (warm = +R/-B, cool = -R/+B)
    temp = float(p["temperature"])
    if abs(temp) > 1e-4:
        rgb[:, 0] += temp * 0.08
        rgb[:, 2] -= temp * 0.08

    # 4) Split toning (shadows vs highlights)
    si = float(p["split_intensity"])
    if si > 1e-4:
        bal = float(p["split_balance"])
        luma = np.clip(0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2], 0.0, 1.0)
        w_sh = np.clip((bal - luma) / max(0.05, bal), 0.0, 1.0) * si
        w_hi = np.clip((luma - bal) / max(0.05, 1.0 - bal), 0.0, 1.0) * si
        rgb += w_sh[:, None] * np.array(p["split_shadows"], dtype=np.float32)
        rgb += w_hi[:, None] * np.array(p["split_highlights"], dtype=np.float32)

    # 5) Saturation + Vibrance (vibrance boosts muted colors more than already-saturated skin)
    luma = (0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2])[:, None]
    max_c = np.max(rgb, axis=1, keepdims=True)
    min_c = np.min(rgb, axis=1, keepdims=True)
    cur_sat = np.clip(max_c - min_c, 0.0, 1.0)
    sat_mult = (1.0 + float(p["saturation"])) * (1.0 + float(p["vibrance"]) * (1.0 - cur_sat))
    rgb = luma + (rgb - luma) * sat_mult

    # Blend with identity by `mix` and clamp
    final_rgb = np.clip(rgb0 * (1.0 - mix) + np.clip(rgb, 0.0, 1.0) * mix, 0.0, 1.0)

    lines = [
        f'TITLE "{look_id}"',
        f"LUT_3D_SIZE {size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    lines.extend(f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in final_rgb)
    Path(out_cube_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_cube_path).write_text("\n".join(lines) + "\n")
    return out_cube_path


def lut3d_filter_str(look_id: str, intensity: float | None = None) -> str:
    """Return an FFmpeg `-vf` snippet (`lut3d=file='...':interp=tetrahedral`)."""
    cube = generate_cube_lut(look_id, intensity=intensity)
    return f"lut3d=file='{cube}':interp=tetrahedral"


def apply_cinema_look(
    in_video: str,
    out_video: str,
    look_id: str = "teal-orange-blockbuster",
    intensity: float | None = None,
    crf: int = 18,
    preset: str = "medium",
) -> dict[str, Any]:
    """Apply a HyperFrames-style 3D `.cube` cinema look to a video via FFmpeg."""
    vf = lut3d_filter_str(look_id, intensity=intensity)
    cmd = [
        get_ffmpeg(), "-y", "-v", "warning",
        "-i", in_video,
        "-vf", vf,
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart",
        out_video,
    ]
    subprocess.run(cmd, check=True)
    return {"out_video": out_video, "look_id": look_id, "vf": vf}
