# Video-format memory (compact, reusable rules only)

This file preserves reusable production decisions and corrections, not episode-specific media. Read before any Type 1/2/3 build. Keep source manifests as small provenance/dedup records; do not keep source clips, candidate sheets, or per-episode scratch solely as memory after a final is accepted/deleted.

## Authority and code map
- Cross-format master rules: `studio/SPEC.md`.
- Type 1 engine: `studio/t1.py`; shared timeline/render/text: `studio/render.py`, `studio/textkit.py`, `studio/templates.py`.
- Type 2 reusable maker: `studio/type2/build.py` (render → timing-detected chicken interstitial → mix → mux/QA) + `studio/type2/mix.py` + reusable base `studio/type2/config.json`; detailed recipe/sourcing/QA: `studio/type2/TYPE2_SPEC.md`, with selection/audio learnings in `studio/type2/LEARNINGS.md`.
- Type 3 engine only: `studio/t3.py`; project data in `studio/projects/<name>/project.json` plus narration/wordtimes.
- Source discovery/download helpers: `studio/discover.py` (YouTube search/download); Type 3 URL fetch is in `t3.py`.

## Type 1 — continuous movie-scene edit
- One continuous scene; no montage and no added narration. **Hook/punchline-first rule (reaffirmed by user):** always open at `0.0s` with the 2.5–3.8s peak hook/punchline (fully captioned), dip cleanly (4-frame dip-to-black + click-free audio fade) into the continuous uncut scene from its start through payoff.
- Language follows request: Hindi dub by default, or original English movie + English audio when requested (e.g., 2026 English movie series uploaded to Google Drive folder `movies` `1vehwtuYIsqcrbzM9eQfZDFGanW67XmyB` as `ep1 - <Movie>.mp4`, `ep2 - ...`; provenance in `studio/projects/t1_english_demos_manifest.json`).
- Header, action captions, word-synced `Archivo Black` karaoke (`y=1405`), and `Anton` impact words; no background music (`t1.py`). Render motion via native-FPS sub-pixel `cv2.warpAffine(..., INTER_LANCZOS4)` (`om_hybrid/smart_camera.py`) and master audio with `alimiter=limit=0.81:level=false` (`~-15 LUFS`, `<= -1.5 dBFS` TP).
- **Layout note:** Visual inspection of references `_6HF-smeZvc` (rounded card on solid black) and `zzY9iXVh5IA` (`9:10` full-width band on solid black) confirmed neither uses a blurred backdrop; `1080x1200` (`y=360..1560`) between `360px` solid black bands is active default.

## Studio x OpenMontage Hybrid (`studio/om_hybrid/`)
- Lightweight (~230 KB, zero-GPU, 2 GB RAM safe) integration of OpenMontage's best local modules with our fast `cv2` + `libass` + `ffmpeg` engine (skipping heavy Remotion/Blender/paid-API bloat):
  - `om_hybrid/smart_camera.py`: Shot-segmented multi-face / two-shot active-speaker reframing + caption-collision guard + sub-pixel `Lanczos4` segment renderer.
  - `om_hybrid/pacing_audio.py`: Dead-air `silencedetect`, 100ms `ebur128` momentary energy profiler, and Clip-Factory 5D hook/punchline candidate scorer.
  - `om_hybrid/clip_scout.py` + `stock_sources/`: 16 unified stock/public-archive video adapters (`archive_org`, `wikimedia`, `nasa`, `noaa`, `esa`, `jaxa`, `loc`, `nara`, `dareful`, `coverr`, `mixkit`, `videvo`, `pond5_pd`, `pexels`, `pixabay_video`, `unsplash`) + IGN `1080p` (`zencoder`/`mediaconvert`) movie-clip extractor.
  - `om_hybrid/visual_qa.py` & `slideshow_risk.py`: Full bitstream decode, `ebur128` LUFS/TP gate, face-vs-caption occlusion check, contact-sheet generator, and 6D anti-slideshow scorer.
  - Unified CLI: `python3 /home/user/studio/om_hybrid/cli.py {sources|search|ign|analyze|qa}`.

## Type 2 — ranking/countdown (latest user-confirmed ingredients)
- Current EP29-style frame: vertical 1080x1920; 360px black title band, 1080x1428 central video, 132px footer; persistent title; left rank ladder; title 116, numbers 101, labels 70, `@studio`; no extra pills, unnecessary zoom, or speed changes.
- Main fail clips must show setup through the actual fall/landing/splash. Verify selected timestamps after crop; avoid severe injury/gore. Prefer distinct source moments. Rank from lighter to strongest payoff, with #1 last.
- **Audio recipe user specifically reaffirmed:** series BGM around 17%; retain suitable source/natural audio; add funny impact SFX on impact; use the recurring “I got this” phrase at transitions; insert the chicken/scream immediately before #1. Treat the chicken as a recurring interstitial, not one of the fail-source clips. Phrase count follows the active clip structure (legacy five-ranked build used 4 hits; a four-clip layout needs its corresponding transition count). `TYPE2_SPEC.md` contains the detailed historical timing/mix/QA recipe.
- Source screening: use YouTube/TikTok/Pexels/other suitable sources; record platform + direct URL + source ID/time; scan full source and inspect candidate cut windows/contact sheets; remove/reject baked-in logos/text when they cannot be cleanly handled. Keep a compact source-ID ledger for deduplication after deleting source files.
- Audio caveat: do not claim subjective audition, song-free audio, or rights clearance unless actually checked.
- **Code check:** `studio/type2/build.py` + `mix.py` + `config.json` implement the recurring phrase, chicken/scream, selected music, SFX, ducking, and measured-gap timing (the generic config is built around five ranked clips plus the interstitial). The EP33/34 one-off builder uses the newer four-clip frame but omits the phrase and chicken. Do not reuse that one-off as the canonical future Type 2 maker; combine the accepted newer frame with the reusable audio/interstitial recipe before a future build.
- **Only current selected Type-2 BGM:** C2, stored as `/home/user/MUSIC_FINAL/C2_ComedyToyBand.mp3` (master) and `/home/user/studio/type2/assets/c2_48.wav` (engine-ready). EP30–EP34 manifests point to the WAV; decoded C2 MP3/WAV audio matched exactly. Prior QKThr/67% settings and the other audition tracks are obsolete/unselected. Preserve narration MP3s, SFX, `got_this` voice, and chicken/scream assets. Old prototype configs under `studio/clips/` and `studio/trial/sfx_map.json` still reference removed tracks; don't run them unchanged—use the canonical `studio/type2/build.py` + `mix.py` + `config.json` path.

## Type 3 — narrated explainer
- `t3.py` only. 1080x1920 canvas; locked 9:10 content band y=360..1560, 360px black above/below.
- Hindi narration (Devanagari TTS); on-screen captions in Roman Hinglish. Current word yellow, previous line/words white; no scale-pop. Header per `SPEC.md` (Anton, two lines); end card `THE END`.
- Original scene audio under narration at 0.50/duck 0.50; no background music. Master gain +2.5 dB; verify clipping. Keep narration timings/project JSON, not source b-roll after final acceptance unless needed for an active project.

## Reusable priorities and failure-prevention
1. User feedback that changes the format becomes a reusable rule here / in the relevant type spec, not a reason to retain the whole episode's source footage or screenshots.
2. Verify the true action, crop, timing, source audio, caption readability, and full decode before delivery. Do not claim checks that were not performed.
3. Keep episode-specific source IDs/URLs/timestamps/manifests to avoid accidental reuse; delete bulky source clips and review sheets once the final is accepted and source history is recorded.
4. Preserve maker code, canonical specs, fonts, required BGM/SFX/voice/chicken assets, and active Type 3 project data. Never delete user uploads or Drive finals during workspace cleanup unless explicitly asked.
5. After the user asks to remove an episode/final, also remove its local source downloads, intermediate renders, and episode-specific review images; retain only the compact reusable lesson and source-ID record.
6. Drive upload rule: only when upload is explicitly requested, set anyone-with-link viewer, keep discovery off, and verify the permission. Do not alter existing Drive finals or permissions without explicit instruction.

## Storage audit and cleanup (2026-10-31)
- Before cleanup: workspace ~506 MB; `/home/user/studio` ~208 MB (`type2` ~157 MB, mostly review images), `/home/user/dl` ~93 MB, `/home/user/studio/work` ~44 MB. `.cache` (~29 MB) and `.deno` (~92 MB) are environment caches/tooling, not episode media; left untouched.
- User approved full local episode-media cleanup. Removed 3,896 generated/redundant files (about 343.2 MiB): contact sheets/frame-review JPG/PNG/GIFs, temporary `.ass` overlays, Python `.pyc`, local `dl` episode/source/test MP4s, and the one-off Type-2 crop test. `/home/user/uploads`, Drive files, common fonts/BGM/SFX/voice/chicken assets, manifests/configs/specs, and maker code were preserved.
- After cleanup: `/home/user` workspace ~155 MB; `/home/user/studio` ~13 MB; only reusable local MP4s are the chicken insert and black-frame helper.
- EP33/34 manifests and builder remain, but their local source directory `/home/user/dl/src/ep33_34_candidates` and render directory `/home/user/studio/out` were absent before cleanup. Final EP33/34 MP4s are in Drive; manifests retain YouTube URLs and cut times, so sources must be fetched again to re-render.
- Detailed cleanup record: `studio/CLEANUP_LOG_2026-10-31.md`.

## Full A–Z workspace pass (2026-10-31)
- Removed 83 verified cache/review/search/metadata/log files totaling 31,469,949 bytes (~30.01 MiB), plus a corrupt 9-byte `Not Found` archive. Cleared the regenerable pip download cache; kept `.deno` because it is the active runtime.
- Removed only unused saved HTML/search results, review sheets, an unreferenced black-frame cache, old candidate metadata/logs, and the superseded 24 Oct Type 2 spec copy. The current `studio/type2/TYPE2_SPEC.md` already contains the reusable selection, audio, QA, and source guidance.
- Preserved all 19 EP15–EP34 source manifests (74 selected clip IDs), earlier episode progress/config/plan records, all maker scripts/settings, user uploads, Drive finals, fonts, narration, SFX, “I got this,” chicken/scream, reference audio, current C2, and active project data. No music or recurring audio was deleted in this pass.
- Syntax-parsed all 127 Python files in `studio`, `tools`, and root with zero errors; `tools/watch.py --help` passed. This does not claim semantic/runtime validation of every legacy one-off script.
- Kept old candidate-generation scripts and episode configs where they may still contain source IDs or useful logic; not proven redundant, and too small to justify risky deletion. Root `WORKSPACE.md`/`TODO.md` are marked archival; current rules live in this file and the current specs.
- Current workspace is ~117 MiB; `.deno` (~92 MiB) is the main remaining runtime footprint. Full audit: `studio/A_Z_CLEANUP_AUDIT.md`; exact removal list: `studio/A_Z_CLEANUP_REMOVED_2026-10-31.tsv`.

## OpenMontage Hybrid Studio (`studio/om_hybrid/` — 2026-11-01)
- Lightweight local + cloud hybrid package combining Maker Studio's Type 1/2/3 engines with best zero-cost modules from `calesthio/OpenMontage` (`AGPL-3.0`; see `studio/om_hybrid/NOTICE_OPENMONTAGE.md` and `studio/om_hybrid/PLAYBOOK_RULES.md`):
  - `smart_camera.py`: Shot-boundary + face-tracked sub-pixel `cv2.warpAffine(..., INTER_LANCZOS4)` camera planner & renderer with bundled `models/blaze_face_short_range.tflite` (`mediapipe_blazeface` Tasks API) + bundled Haar cascades (`opencv_haar` fallback).
  - `pacing_audio.py`: FFmpeg `silencedetect`, 100ms `ebur128` energy timeline, and `-14.8 LUFS` / `-1.5 dBFS` loudness mastering (`alimiter=limit=0.81:level=false`).
  - `clip_scout.py` + `stock_sources/`: 16 free/public-domain stock video adapters (`nasa`, `wikimedia`, `archive_org`, `noaa`, `esa`, `jaxa`, `loc`, `nara`, `dareful`, `coverr`, `mixkit`, `videvo`, `pond5_pd`, `pexels`, `pixabay_video`, `unsplash`) + hook-first candidate ranker (`score_hook_candidates`).
  - `visual_qa.py` & `slideshow_risk.py`: Pre-delivery codec/black-frame/loudness/safe-zone QA gate and 6-dimension slideshow-risk scorer.
  - `cinema_looks.py` & `smart_camera.py` (adapted from `heygen-com/hyperframes`, `Apache-2.0`; see `studio/hyperframes/NOTICE_HYPERFRAMES.md`): Offline NumPy 3D `.cube` LUT generator (`teal-orange-blockbuster`, `bleach-bypass`, `film-fade`, `warm-cinema`, `crisp-editorial`, `scifi-cool`) + velocity-matched seam modes (`seam_mode="dip"|"zoom_through"|"whip_pan"|"rack_focus"`) — both run locally in Arena (`<5ms` LUT build) and on Cloud.
  - `sfx_sync.py` & `studio/earshot/` (adapted/vendored from `Leonxlnx/earshot`, `MIT` license): 252 zero-copyright procedural studio SFX (`cut_hit`, `pro_whoosh_big`, `riser`, `sub_drop`, `click`, `pop`, `glitch`, `logo_sting`) rendered offline in `<0.4s` via NumPy/SciPy with sub-millisecond peak-to-cut alignment (`insert_at_s = cut_time_s - peak_s`).
  - `openverse_realsfx.py` & `studio/real_sfx/` (`Openverse` `MIT` + `Clipwing/skills` `real-sfx` `MIT` + 78 CC0 `uisfx` cues): Searches & downloads CC0/CC real recordings via `api.openverse.org/v1/` (with automatic Wikimedia Commons + Archive.org CC fallback on datacenter IPs) and auto-mixes frame-accurate, voice-ducked SFX (`from_hyperframes.py` / `find_moments.py` -> `suggest_cues.py` -> `mix.py --voice-safe --duck` -> `critique.py`).
  - `_ffmpeg.py`: Self-healing `ffmpeg` + `ffprobe` (`7.0.2-static`) resolver that automatically runs `studio/bootstrap.sh` if container snapshot resume resets `/tmp/vidtools/`.
  - CLI: `python3 -m om_hybrid.cli {sources|search|ign|analyze|qa|looks|grade|sfx-list|sfx-render|openverse-audio|openverse-images|realsfx-setup|realsfx-mix}` (run from `/home/user/studio`).

## GitHub Cloud Render Farm (`thecattrex/maker-studio` — 2026-11-01)
- Dedicated **public** GitHub repository: `https://github.com/thecattrex/maker-studio` (unlimited Actions minutes + `16 GB RAM / 4 vCPU` runners; strictly isolated — never touch user's other GitHub repos; never commit tokens/credentials or unlisted Google Drive URLs). Full chronological upgrade record: `studio/UPGRADE_HANDOFF_LOG.md`.
- Unlocks heavy skills blocked by Arena's 2 GB sandbox RAM / Node 20 cap by dispatching onto GitHub Actions (`16 GB RAM / 4 vCPU`):
  1. **`t1_hq`**: `faster-whisper medium.en` word-level ASR + `mediapipe` BlazeFace tracking + sub-pixel `INTER_LANCZOS4` + optional `.cube` `look_id` & velocity `seam_mode` + `libx264 -preset slow -crf 17` + true 2-pass linear `loudnorm` (`-14.8 LUFS`, `-1.5 dBTP`).
  2. **`hyperframes`**: Node 22 + HeyGen `hyperframes` CLI (`studio/hyperframes/`) — deterministic HTML + CSS + GSAP -> Chrome `BeginFrame` -> FFmpeg rendering + on-demand installation from 448 registry blocks/components.
  3. **`earshot`**: PyTorch CPU + `CLAP` + `AST` neural audio perception ("AI Ears") — generates `earshot_sheet.png` (annotated frames + spectrogram + loudness + beat/cut sync map) and `earshot_critique.json`.
  4. **`real_sfx`**: Live `api.openverse.org/v1/` CC0/CC audio & image scout + Clipwing `real-sfx` frame-exact sound design (`*_sfx.mp4` + `*_sfx_track.wav` stem + QA).
  5. **`remotion`**: Full React/Remotion rendering via `studio/remotion-composer/` (`CinematicRenderer`, `Explainer`, `TitledVideo`, `TalkingHead`, `CollageBurst`, `LyricOverlay`) on headless Chromium.
  6. **`smoke`**: Fast health/QA verification of the cloud runner + artifact round-trip.
- Controller CLI:
  - Status: `python3 /home/user/studio/gh_farm.py status`
  - Run job & pull MP4/QA back into workspace: `python3 /home/user/studio/gh_farm.py run --mode {smoke|t1_hq|hyperframes|earshot|real_sfx|remotion} [--job path/to/job.json] --out-dir /tmp/cloud_out`

