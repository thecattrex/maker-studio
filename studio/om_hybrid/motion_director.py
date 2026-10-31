"""motion_director.py — Automatic Camera Choreography, Kinetic HUD & Motion Overlay Bridge.

Ensures every video rendered in Maker Studio actively uses the motion capabilities
of our integrated engines (`OpenMontage`, `HyperFrames`, `Remotion`) instead of static
or monotonous framing:

  1. `choreograph_shots_table`: Upgrades uniform zoom tables into alternating cinematic
     shot motions (`hook_punch`, `push_in`, `pull_reveal`, `drift_push`, `climax_punch`)
     so consecutive cuts always contrast in motion direction/energy.
  2. `add_kinetic_motion_hud`: Injects zero-RAM vector ASS (`\\p1`) motion accents:
     - Frame-0 optical hook flash (`0..180 ms`)
     - Velocity-seam optical flash at the Hook -> Story cut (`zoom_through` / `whip_pan`)
     - Smooth retention progress bar along the bottom edge of the video band.
  3. `composite_motion_overlay`: Composites a `HyperFrames` (HTML+GSAP) or `Remotion`
     motion-graphic overlay clip onto live-action footage via `screen` luma blend,
     `colorkey`, or straight `alpha`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ._ffmpeg import get_ffmpeg


def choreograph_shots_table(
    shots_table: list[list[float]],
    hook_frame_range: tuple[int, int] | None = None,
    climax_frame: int | None = None,
) -> list[list[float]]:
    """Assign varied, cinematic zoom & micro-drift curves across shots.

    Input/Output row format:
      `[f_start, f_end, fx0, fx1, fy0, fy1, z0, z1]`
    """
    out: list[list[float]] = []
    for idx, row in enumerate(shots_table):
        a, b, fx0, fx1, fy0, fy1, _z0, _z1 = row
        a_i, b_i = int(a), int(b)

        is_hook = bool(
            hook_frame_range
            and a_i <= hook_frame_range[1]
            and b_i >= hook_frame_range[0]
        )
        is_climax = bool(climax_frame is not None and a_i <= climax_frame <= b_i)

        if is_hook:
            # Immediate high-engagement push for the opening hook
            z0, z1 = 1.030, 1.095
        elif is_climax:
            # Peak emotional/action punch-in
            z0, z1 = 1.015, 1.092
        else:
            mode = idx % 3
            if mode == 0:
                # Classic cinema push-in
                z0, z1 = 1.000, 1.060
            elif mode == 1:
                # Breath pull-back / spatial reveal
                z0, z1 = 1.062, 1.005
            else:
                # Gentle lateral micro-drift + subtle push
                drift = 0.035 if (idx % 2 == 0) else -0.035
                fx0 = max(0.0, min(1.0, fx0 - drift * 0.5))
                fx1 = max(0.0, min(1.0, fx1 + drift * 0.5))
                z0, z1 = 1.010, 1.055

        out.append([a_i, b_i, round(fx0, 4), round(fx1, 4), round(fy0, 4), round(fy1, 4), round(z0, 4), round(z1, 4)])
    return out


def add_kinetic_motion_hud(
    overlay: Any,
    total_dur: float,
    hook_end_s: float | None = None,
    band_top_y: int = 360,
    band_bottom_y: int = 1560,
    accent_bgr: str = "&H002E2EF7&",
    enable_progress_bar: bool = True,
    enable_flashes: bool = True,
) -> None:
    """Add lightweight ASS vector motion graphics (flashes + live progress bar) to `textkit.Overlay`."""
    band_h = max(100, band_bottom_y - band_top_y)

    # 1. Opening Hook Optical Flash (0.00s -> 0.18s, soft additive-feel white veil)
    if enable_flashes and total_dur > 1.0:
        overlay.add(
            0.0,
            0.18,
            "Flash",
            r"{\an7\pos(0," + str(band_top_y) + r")\bord0\shad0\c&H00FFFFFF&"
            r"\alpha&HB8&\t(0,180,\alpha&HFF&)\p1}"
            f"m 0 0 l 1080 0 1080 {band_h} 0 {band_h}" + r"{\p0}",
            layer=8,
        )

    # 2. Velocity Seam Optical Flash right on Hook -> Story transition
    if enable_flashes and hook_end_s and 0.4 < hook_end_s < (total_dur - 0.5):
        t0 = max(0.0, hook_end_s - 0.06)
        t1 = min(total_dur, hook_end_s + 0.12)
        dur_ms = max(60, int(round((t1 - t0) * 1000)))
        overlay.add(
            round(t0, 3),
            round(t1, 3),
            "Flash",
            r"{\an7\pos(0," + str(band_top_y) + r")\bord0\shad0\c&H00FFFFFF&"
            r"\alpha&HC0&\t(0," + str(dur_ms) + r",\alpha&HFF&)\p1}"
            f"m 0 0 l 1080 0 1080 {band_h} 0 {band_h}" + r"{\p0}",
            layer=8,
        )

    # 3. Live Retention Progress Bar along bottom of video band (`0 -> 1080px`)
    if enable_progress_bar and total_dur > 1.0:
        bar_y = band_bottom_y - 6
        total_ms = int(round(total_dur * 1000))
        # Subtle dark track
        overlay.add(
            0.0,
            total_dur,
            "HUD",
            r"{\an7\pos(0," + str(bar_y) + r")\bord0\shad0\c&H00181818&\alpha&H70&\p1}"
            "m 0 0 l 1080 0 1080 6 0 6{\\p0}",
            layer=6,
        )
        # Animated accent bar sliding from x=-1080 -> x=0 across total_dur
        overlay.add(
            0.0,
            total_dur,
            "HUD",
            r"{\an7\move(-1080," + str(bar_y) + f",0,{bar_y},0,{total_ms})"
            + r"\clip(0," + str(bar_y) + f",1080,{bar_y + 6})"
            + r"\bord0\shad0\c" + accent_bgr + r"\alpha&H18&\p1}"
            "m 0 0 l 1080 0 1080 6 0 6{\\p0}",
            layer=7,
        )


def composite_motion_overlay(
    base_mp4: str,
    overlay_mp4: str,
    out_mp4: str,
    at_s: float = 0.0,
    mode: str = "screen",
    colorkey_hex: str = "0x00FF00",
    opacity: float = 0.95,
) -> dict[str, Any]:
    """Composite a HyperFrames / Remotion motion-graphic clip on top of live-action video.

    Modes:
      - `screen`:   Render HyperFrames/Remotion on pure `#000000` black; bright kinetic
                    typography, HUDs, glows, and lower-thirds blend cleanly with zero matte halo.
      - `colorkey`: Chroma-key out `colorkey_hex` background.
      - `alpha`:    Straight alpha overlay (WebM VP9 / ProRes 4444 / PNG sequence).
    """
    ffmpeg = get_ffmpeg()
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)

    if mode == "screen":
        vf = (
            f"[1:v]setpts=PTS+{at_s:.3f}/TB,format=rgba,"
            f"colorchannelmixer=rr={opacity:.3f}:gg={opacity:.3f}:bb={opacity:.3f}[ov];"
            f"[0:v][ov]blend=all_mode=screen:shortest=0[vout]"
        )
    elif mode == "colorkey":
        vf = (
            f"[1:v]setpts=PTS+{at_s:.3f}/TB,colorkey={colorkey_hex}:0.18:0.08,"
            f"format=rgba,colorchannelmixer=aa={opacity:.3f}[ov];"
            f"[0:v][ov]overlay=0:0:eof_action=pass[vout]"
        )
    else:
        vf = (
            f"[1:v]setpts=PTS+{at_s:.3f}/TB,format=rgba,"
            f"colorchannelmixer=aa={opacity:.3f}[ov];"
            f"[0:v][ov]overlay=0:0:eof_action=pass[vout]"
        )

    subprocess.run(
        [
            ffmpeg, "-y", "-v", "warning",
            "-i", str(base_mp4),
            "-i", str(overlay_mp4),
            "-filter_complex", vf,
            "-map", "[vout]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart",
            str(out_mp4),
        ],
        check=True,
    )
    return {"out_mp4": str(out_mp4), "mode": mode, "at_s": at_s}
