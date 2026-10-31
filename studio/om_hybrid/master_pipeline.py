"""master_pipeline.py — Unified 'Best-Outcome' Master Pipeline for ANY Video.

Connects all 6 integrated studio layers into ONE cohesive pipeline instead of
separate islands, working both locally (2 GB Arena) and on the 16 GB Cloud Farm:

  Layer 1 — `OpenMontage` Intelligence (`smart_camera`, `pacing_audio`, `slideshow_risk`):
            Detects shots, MediaPipe BlazeFace safe zones, dead-air ratio, and hook window.
  Layer 2 — `HyperFrames` Cinema Grade (`cinema_looks`):
            Applies 33^3 `.cube` 3D LUT color grading (`teal-orange-blockbuster`,
            `crisp-editorial`, `warm-cinema`, `bleach-bypass`, `film-fade`, `scifi-cool`).
  Layer 3 — `earshot` Procedural Bank (252 studio sounds) + `Openverse` (5M+ CC audio)
            + `uisfx` (78 CC0 UI sounds):
            Unified multi-role sound library (`whoosh`, `hit`, `riser`, `drop`, `pop`, `click`, `chime`).
  Layer 4 — `Clipwing Real-SFX` Frame-Exact Mixer (`auto_sound_design_video`):
            Detects cuts/motion bursts (or reads HyperFrames HTML timeline), places frame-accurate
            cues (`0 ms` peak lag), ducks under dialogue (`--voice-safe --duck`), checks mono
            compatibility, and masters loudness (`~ -14.8 LUFS`, `<= -1.5 dBTP`).
  Layer 5 — `OpenMontage` Visual & Broadcast QA (`run_full_qa`):
            Bit-accurate decode check, resolution/fps check, EBUR128 LUFS/True-Peak gate,
            face-vs-caption collision check, and 4x4 visual contact sheet.
  Layer 6 — `earshot` Neural AI Ears (`CLAP + AST`, auto-enabled when `torch` is installed
            on the 16 GB Cloud Farm):
            Generates `earshot_sheet.png` + `earshot_critique.json` perceptual sync audit.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .cinema_looks import apply_cinema_look
from .openverse_realsfx import auto_sound_design_video, search_openverse_audio
from .pacing_audio import analyze_energy, detect_silences
from .smart_camera import plan_smart_camera
from .visual_qa import run_full_qa

STUDIO_DIR = Path(__file__).resolve().parents[1]

PRESET_TO_LOOK: dict[str, tuple[str | None, float]] = {
    "movie": ("teal-orange-blockbuster", 0.65),
    "cinema": ("warm-cinema", 0.70),
    "motion": ("crisp-editorial", 0.65),
    "reaction": ("crisp-editorial", 0.45),
    "scifi": ("scifi-cool", 0.70),
    "none": (None, 0.0),
}


def has_neural_ears() -> bool:
    """True when PyTorch + HuggingFace `transformers` are installed (16 GB Cloud Farm)."""
    return bool(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers"))


def master_polish_video(
    video_path: str,
    out_mp4: str,
    preset: str = "movie",
    look_id: str | None = None,
    look_intensity: float | None = None,
    enable_sfx: bool = True,
    voice_safe: bool = True,
    duck: bool = True,
    openverse_seed_query: str | None = None,
    hyperframes_dir: str | None = None,
    run_ai_ears: str = "auto",
    artifacts_dir: str | None = None,
) -> dict[str, Any]:
    """Run the unified end-to-end Master Finishing Pipeline on any input video."""
    src = Path(video_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input video not found: {src}")

    dst = Path(out_mp4).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    art_dir = Path(artifacts_dir).resolve() if artifacts_dir else dst.parent
    art_dir.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="maker_master_"))
    try:
        # Step 1: Intelligence pass (camera safe-zones + dead-air + energy profile)
        sil = detect_silences(str(src))
        eng = analyze_energy(str(src))
        dur = float(sil.get("total_duration") or 0.0)
        cam = plan_smart_camera(str(src), start_s=0.0, end_s=min(dur, 30.0) if dur > 0 else 10.0)

        # Resolve look preset
        default_look, default_int = PRESET_TO_LOOK.get(preset, (None, 0.0))
        chosen_look = look_id if look_id is not None else default_look
        chosen_int = look_intensity if look_intensity is not None else default_int

        current_video = str(src)

        # Step 2: Optional 3D `.cube` Cinema Color Grade (`HyperFrames` LUT engine)
        grade_info: dict[str, Any] = {"applied": False}
        if chosen_look and chosen_look != "none" and chosen_int > 0:
            graded_mp4 = work / "graded.mp4"
            grade_info = apply_cinema_look(current_video, str(graded_mp4), look_id=chosen_look, intensity=chosen_int)
            grade_info["applied"] = True
            current_video = str(graded_mp4)

        # Step 3: Optional Openverse CC Audio Enrichment + Clipwing Real-SFX + Earshot 252 Bank
        openverse_info: dict[str, Any] = {"queried": False}
        if openverse_seed_query:
            ov_dir = STUDIO_DIR / "real_sfx" / "openverse_cc0"
            ov_res = search_openverse_audio(openverse_seed_query, limit=2, download_dir=str(ov_dir))
            openverse_info = {
                "queried": True,
                "backend": ov_res.get("backend"),
                "hits": ov_res.get("count", 0),
            }

        sfx_info: dict[str, Any] = {"applied": False}
        if enable_sfx:
            sfx_res = auto_sound_design_video(
                current_video,
                str(dst),
                voice_safe=voice_safe,
                duck=duck,
                hyperframes_dir=hyperframes_dir,
            )
            sfx_info = {"applied": True, **sfx_res}
        else:
            shutil.copy2(current_video, dst)

        # Step 4: Visual + Loudness + Safe-Zone QA Gate
        sheet_jpg = str(art_dir / f"{dst.stem}_qa_sheet.jpg")
        qa = run_full_qa(
            str(dst),
            min_dur=max(1.5, min(15.0, dur * 0.8)) if dur > 0 else 2.0,
            max_dur=max(65.0, dur + 5.0),
            sheet_out=sheet_jpg,
        )

        # Step 5: Neural AI Ears (`earshot` CLAP + AST) when available or requested
        ears_info: dict[str, Any] = {"ran": False}
        want_ears = (run_ai_ears == "always") or (run_ai_ears == "auto" and has_neural_ears())
        if want_ears:
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{STUDIO_DIR}:{env.get('PYTHONPATH', '')}"
            ears_png = art_dir / f"{dst.stem}_earshot_sheet.png"
            ears_json = art_dir / f"{dst.stem}_earshot_critique.json"
            subprocess.run(
                [sys.executable, "-m", "earshot", "sheet", str(dst), "-o", str(ears_png), "--detail", "low"],
                env=env, check=True,
            )
            p_crit = subprocess.run(
                [sys.executable, "-m", "earshot", "critique", str(dst), "--fast", "--json"],
                env=env, capture_output=True, text=True, check=True,
            )
            ears_json.write_text(p_crit.stdout)
            ears_info = {
                "ran": True,
                "sheet_png": str(ears_png),
                "critique_json": str(ears_json),
            }

        report = {
            "out_mp4": str(dst),
            "preset": preset,
            "intelligence": {
                "duration_s": sil.get("total_duration"),
                "dead_air_ratio": sil.get("dead_air_ratio"),
                "peak_energy_sec": eng.get("peak_sec"),
                "recommended_caption_y": cam.get("recommended_caption_y"),
                "face_detector": cam.get("detector_backend"),
            },
            "cinema_grade": grade_info,
            "openverse": openverse_info,
            "sound_design": {
                "applied": sfx_info.get("applied", False),
                "indexed_sounds": sfx_info.get("indexed_sounds"),
                "sfx_stem_wav": sfx_info.get("sfx_stem_wav"),
            },
            "ai_ears": ears_info,
            "qa": qa,
        }
        (art_dir / f"{dst.stem}_master_report.json").write_text(json.dumps(report, indent=2))
        return report
    finally:
        shutil.rmtree(work, ignore_errors=True)
