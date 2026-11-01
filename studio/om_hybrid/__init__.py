"""om_hybrid — Studio x OpenMontage Hybrid Engine.

Combines our lightweight, sub-pixel Lanczos4 + libass + FFmpeg studio engine
with OpenMontage's best local intelligence modules:
  - smart_camera: Shot-aware multi-face / two-shot tracking + caption-collision
                  guard + sub-pixel Lanczos4 camera motion renderer.
  - pacing_audio: Silence/dead-air detector, 100ms ebur128 momentary energy
                  profiler, Clip-Factory 5D hook/punchline scorer, and
                  6D anti-slideshow scorer.
  - clip_scout:   16 free/public stock footage adapters (Archive.org, Wikimedia,
                  NASA, NOAA, ESA, JAXA, LOC, NARA, Dareful, Coverr, Mixkit,
                  Videvo, Pond5-PD, Pexels, Pixabay, Unsplash) + IGN 1080p
                  official movie clip resolver.
  - visual_qa:    Automated decode check, EBUR128 LUFS & True Peak check,
                  face-vs-caption occlusion detector, and contact-sheet builder.
"""
from .slideshow_risk import score_slideshow_risk
from .smart_camera import detect_shots, plan_smart_camera, render_subpixel_segments
from .pacing_audio import detect_silences, analyze_energy, score_hook_candidates
from .clip_scout import list_sources, search_stock_clips, extract_ign_1080p_mp4
from .visual_qa import run_full_qa
from .cinema_looks import list_cinema_looks, generate_cube_lut, lut3d_filter_str, apply_cinema_look
from .sfx_sync import list_sfx_bank, render_synced_sfx, mix_sfx_cues
from .openverse_realsfx import (
    search_openverse_audio,
    search_openverse_images,
    ensure_realsfx_ready,
    auto_sound_design_video,
)
from .master_pipeline import master_polish_video, has_neural_ears
from .motion_director import (
    choreograph_shots_table,
    add_kinetic_motion_hud,
    composite_motion_overlay,
)
from .ironman_edit import render_ironman_style_edit
from .viral_vfx import (
    PersonSegmenter,
    apply_vfx_pipeline,
    list_viral_vfx,
    plan_jigsaw_music_pockets,
    render_still_art_edit,
    run_blob_tracking,
    segment_person_mask,
    write_center_serif_ass,
)

__all__ = [
    "score_slideshow_risk",
    "detect_shots",
    "plan_smart_camera",
    "render_subpixel_segments",
    "detect_silences",
    "analyze_energy",
    "score_hook_candidates",
    "list_sources",
    "search_stock_clips",
    "extract_ign_1080p_mp4",
    "run_full_qa",
    "list_cinema_looks",
    "generate_cube_lut",
    "lut3d_filter_str",
    "apply_cinema_look",
    "list_sfx_bank",
    "render_synced_sfx",
    "mix_sfx_cues",
    "search_openverse_audio",
    "search_openverse_images",
    "ensure_realsfx_ready",
    "auto_sound_design_video",
    "master_polish_video",
    "has_neural_ears",
    "choreograph_shots_table",
    "add_kinetic_motion_hud",
    "composite_motion_overlay",
    "render_ironman_style_edit",
    "PersonSegmenter",
    "segment_person_mask",
    "run_blob_tracking",
    "apply_vfx_pipeline",
    "plan_jigsaw_music_pockets",
    "write_center_serif_ass",
    "render_still_art_edit",
    "list_viral_vfx",
]
