# Maker Studio — Post-OpenMontage Upgrade & Handoff Log

> **Tracking Window:** Starting from the `calesthio/OpenMontage` repository inspection onwards (`2026-11-01`).
> **Purpose:** Complete, chronological record of all modules, configs, workflows, fixes, and rules added so any other Arena chat can apply the entire upgrade in **one shot** without re-explaining anything.
> **Security Rule:** Zero tokens or credentials are ever stored in this file or in Git.

---

## Phase 1 — `calesthio/OpenMontage` Inspection & Local Hybrid Studio (`studio/om_hybrid/`)

Inspected `https://github.com/calesthio/OpenMontage` (`AGPL-3.0`) and built a lightweight, zero-API-cost hybrid package inside `/home/user/studio/om_hybrid/` combining Maker Studio's Type 1 / Type 2 / Type 3 engines with OpenMontage's strongest free tools:

### Files Created / Modified in Phase 1
- `/home/user/studio/om_hybrid/__init__.py` — Public Python exports (`plan_smart_camera`, `render_subpixel_segments`, `detect_silences`, `measure_audio_energy`, `score_hook_candidates`, `master_loudness`, `search_free_broll`, `list_available_sources`, `run_full_qa`, `score_slideshow_risk`).
- `/home/user/studio/om_hybrid/_ffmpeg.py` — Self-healing FFmpeg/FFprobe binary resolver: checks `/tmp/vidtools/ffmpeg`, `PATH`, and automatically executes `/home/user/studio/bootstrap.sh` if a container snapshot resume resets `/tmp`.
- `/home/user/studio/om_hybrid/smart_camera.py` — Shot-boundary segmented (`cv2.calcHist` HSV cut detector) + face/two-shot aware sub-pixel camera planner & renderer (`cv2.warpAffine(..., flags=cv2.INTER_LANCZOS4)` at native source FPS, plus optional 4-frame cinema dip-to-black between cold-open hook and main body, plus caption-zone face-collision guard).
- `/home/user/studio/om_hybrid/models/` — Offline face-detection model bundle (`~2.0 MB` total) so detection works across Python/OpenCV/MediaPipe versions without runtime downloads:
  - `blaze_face_short_range.tflite` (`225 KB`, MediaPipe Tasks `FaceDetector` API — supports both `mediapipe.tasks.python.BaseOptions` and `mp.tasks.BaseOptions`).
  - `haarcascade_frontalface_default.xml` & `haarcascade_profileface.xml` (bundled fallback for local 2 GB box and OpenCV 5.0 wheels that omit `cv2/data/`).
- `/home/user/studio/om_hybrid/pacing_audio.py` — FFmpeg `silencedetect` analyzer, 100ms `ebur128` loudness timeline, cold-open `score_hook_candidates()` ranker, and `-14.8 LUFS` / `-1.5 dBFS` true-peak loudness mastering (`alimiter=limit=0.81:level=false:attack=5:release=50`).
- `/home/user/studio/om_hybrid/clip_scout.py` & `/home/user/studio/om_hybrid/stock_sources/` — 16 stock/public-domain video adapters ported from OpenMontage (`archive_org`, `wikimedia`, `nasa`, `noaa`, `esa`, `jaxa`, `loc`, `nara`, `dareful`, `coverr`, `mixkit`, `videvo`, `pond5_pd`, `pexels`, `pixabay_video`, `unsplash`).
- `/home/user/studio/om_hybrid/visual_qa.py` — Pre-delivery automated QA gate (resolution/codec/FPS/duration, black-frame ratio, `ebur128` LUFS + true-peak check, caption-band face-occlusion check, optional contact sheet).
- `/home/user/studio/om_hybrid/slideshow_risk.py` — 6-dimension slideshow-risk scorer (`0–5` scale) ported from OpenMontage.
- `/home/user/studio/om_hybrid/cli.py` — Unified CLI (`python3 -m om_hybrid.cli {sources|search|analyze|qa|risk}`).
- `/home/user/studio/om_hybrid/PLAYBOOK_RULES.md` — Universal short-form safe zones (`900x1400` inside `1080x1920`, bottom `300–320px` UI dead zone, 1–3s visual change cadence, `-14.8 LUFS` / `-1.5 dBFS`).
- `/home/user/studio/om_hybrid/NOTICE_OPENMONTAGE.md` — `AGPL-3.0` attribution notice for adapted OpenMontage components.

---

## Phase 2 — GitHub Cloud Render Farm Setup (`thecattrex/maker-studio`)

Connected dedicated **private** GitHub repository `https://github.com/thecattrex/maker-studio` (leaving all other user repositories completely untouched) to bypass Arena's `1.94 GB` sandbox RAM ceiling via GitHub Actions cloud runners (`7.75 GB RAM` on private repo / `16 GB RAM` on public runner).

### Files Created / Modified in Phase 2
- `/home/user/.gitignore` — Excludes `.git-credentials`, `.gitconfig`, `.netrc`, caches/runtimes, `bin/`, `studio/samples/*.mp4`, `studio/_scratch/`, and `studio/cloud_out/`.
- `/home/user/studio/remotion-composer/` — Sparse-checked out OpenMontage's React/Remotion project (`597 KB` source, no local `node_modules`) supporting `CinematicRenderer`, `Explainer`, `TitledVideo`, `TalkingHead`, `CollageBurst`, and `LyricOverlay`.
- `/home/user/studio/cloud/hq_worker.py` — Cloud execution worker supporting 3 modes:
  1. `smoke`: Verifies runner RAM/CPU, custom fonts + `libass`, `mediapipe` + BlazeFace/Haar detection, FFmpeg encode, and `om_hybrid` QA.
  2. `t1_hq`: Downloads source URL(s), runs `faster-whisper medium.en` word-level ASR, `mediapipe` BlazeFace smart camera + sub-pixel `INTER_LANCZOS4` crop, `libx264 -preset slow -crf 17`, and true 2-pass linear `loudnorm` (`-14.8 LUFS`, `-1.5 dBTP`).
  3. `remotion`: Renders any `studio/remotion-composer` React composition via headless Chromium on the cloud runner.
- `/home/user/.github/workflows/cloud_render.yml` — `workflow_dispatch` GitHub Actions workflow (`smoke` | `t1_hq` | `remotion`) with automatic artifact upload (`maker-render-<run_id>`).
- `/home/user/studio/gh_farm.py` — Zero-dependency Arena-side controller CLI (`status` and `run`) that dispatches cloud jobs, polls until completion, strips `Authorization` headers across GitHub->Azure 302 artifact redirects, and extracts rendered MP4 + `cloud_report.json` locally.
- `/home/user/studio/FORMAT_MEMORY.md` — Updated with persistent documentation for `studio/om_hybrid/` and `thecattrex/maker-studio`.
- **Live Verification:** GitHub Actions Run `#41242146935` completed with `conclusion: "success"` (`7.75 GB RAM`, `1080x1920`, `qa.passed: true`, artifact round-trip verified).

---

## Ongoing Changes Log (Phase 3+)

### Phase 3 — `heygen-com/hyperframes` Integration (Local + GitHub Cloud Farm — `2026-11-01`)
Inspected `https://github.com/heygen-com/hyperframes` (`Apache-2.0`, `v0.8.224+`, deterministic HTML + CSS + GSAP -> Chrome `BeginFrame` -> FFmpeg engine + 448 registry blocks/components) and integrated a split **Local + Cloud** pipeline:

1. **Runs Both Locally (2 GB Arena) & on Cloud (`studio/om_hybrid/`):**
   - `/home/user/studio/om_hybrid/cinema_looks.py` — Offline NumPy **3D `.cube` LUT generator** + FFmpeg `lut3d` color-grading applier (`teal-orange-blockbuster`, `bleach-bypass`, `film-fade`, `warm-cinema`, `crisp-editorial`, `scifi-cool`). Zero extra RAM overhead (`< 5 ms` `.cube` generation).
   - `/home/user/studio/om_hybrid/smart_camera.py` — Upgraded `render_subpixel_segments(..., seam_mode=...)` with HyperFrames `Cut-the-Curve` velocity-matched transitions between segments:
     - `"dip"` (classic dip-to-black)
     - `"zoom_through"` (matched positive Z push `1.0->1.18` exit + `0.85->1.0` arrival + peak Gaussian blur)
     - `"whip_pan"` (lateral speed-ramp whip + 1D horizontal streak blur)
     - `"rack_focus"` (DSLR Gaussian defocus-cut across boundary)
   - `/home/user/studio/om_hybrid/__init__.py` & `/home/user/studio/om_hybrid/cli.py` — Exported `list_cinema_looks`, `generate_cube_lut`, `lut3d_filter_str`, `apply_cinema_look`, and added CLI subcommands `looks` & `grade`.

2. **Runs on GitHub Cloud Farm (`thecattrex/maker-studio`, `--mode hyperframes`):**
   - Why on GitHub: `hyperframes` npm CLI requires **`Node.js >= 22`** and headless Chrome `BeginFrame` frame capture (Arena sandbox runs `Node 20` with `1.94 GB RAM`).
   - `/home/user/studio/hyperframes/NOTICE_HYPERFRAMES.md` — `Apache-2.0` attribution notice.
   - `/home/user/studio/hyperframes/REGISTRY_PLAYBOOK.md` — HTML + GSAP deterministic contract, creative laws (`Rail + Embed` captions, `Cut-the-Curve`, `Numbers Over Adjectives`), and curated index of the 448 installable registry blocks/components.
   - `/home/user/studio/hyperframes/starter_short/index.html` — Lint-clean `1080x1920 @ 30fps` vertical GSAP starter composition.
   - `/home/user/.github/workflows/cloud_render.yml`, `/home/user/studio/cloud/hq_worker.py`, & `/home/user/studio/gh_farm.py` — Added `--mode hyperframes` (`actions/setup-node@v4` with `node-version: "22"`, `npm install -g hyperframes`, `hyperframes browser ensure`, optional `hyperframes add <registry_item>`, `hyperframes lint`, `hyperframes render`, and `ffprobe`/contact-sheet QA), plus wired `look_id` and `seam_mode` into `--mode t1_hq`.
   - **Live Verification:** GitHub Actions Run `#41243548618` completed with `conclusion: "success"` (`1080x1920`, `30fps`, `lint_exit_code: 0`, `qa.passed: true`, rendered `258 KB` GSAP MP4 verified visually).

---
### Phase 4 — Public Repo Upgrade for Unlimited 16 GB / 4 vCPU Cloud Minutes (`2026-11-01`)
- Per user instruction (`"maker ko public rkhna taki ulimited use krpao"`), audited and sanitized Git history (zero tokens/secrets, unlisted Google Drive episode manifests git-ignored so Drive links stay local-only while `/home/user/` files remain 100% intact) and switched `https://github.com/thecattrex/maker-studio` to **`public` (`private: false`)**.
- Unlocks **unlimited free GitHub Actions minutes** AND upgrades standard `ubuntu-latest` cloud runners from `7.75 GB / 2 vCPU` to the full **`16 GB RAM / 4 vCPU`** tier (`workflow_dispatch` remains restricted exclusively to repository writers).

---
### Phase 5 — `Leonxlnx/earshot` Integration ("AI Ears" + 252 Procedural Studio SFX — `2026-11-01`)
Inspected `https://github.com/Leonxlnx/earshot` (`MIT` license, `v0.4.0`, procedural physical-synthesis SFX bank + CLAP/AST neural audio perception & audio-video sync critique) and integrated a **Local + 16 GB Cloud** pipeline:

1. **Runs 100% Locally in Arena (`<0.4s`, Zero Model Overhead) & on Cloud:**
   - `/home/user/studio/earshot/` (`3.6 MB`, `MIT` license; see `studio/earshot/LICENSE_EARSHOT_MIT.txt`) — Vendored core package containing **252 procedural studio sound effects** across 34+ motion-design categories (`cut_hit`, `pro_whoosh_big`, `whoosh`, `swish`, `swipe`, `pro_riser`, `riser`, `downlifter`, `pro_sub_drop`, `click`, `pop`, `drip`, `glitch`, `logo_sting`, `pluck`, `fit/*`).
   - `/home/user/studio/om_hybrid/sfx_sync.py` — Frame-exact SFX wrapper (`list_sfx_bank`, `render_synced_sfx`, `mix_sfx_cues`): renders 48 kHz WAVs via NumPy/SciPy and aligns each sound's measured acoustic peak (`meta["peak_s"]`) to the exact video cut timestamp (`insert_at_s = cut_time_s - peak_s`, `0 ms` lag) using FFmpeg `adelay` + unity `amix`.
   - `/home/user/studio/om_hybrid/__init__.py` & `/home/user/studio/om_hybrid/cli.py` — Added `sfx-list` and `sfx-render` CLI subcommands.

2. **Runs on Unlimited 16 GB / 4 vCPU GitHub Cloud Farm (`--mode earshot`):**
   - Installs CPU PyTorch + HuggingFace `transformers` (`CLAP` + `AST` audio models) + `librosa`/`pyloudnorm`/`matplotlib` when `mode == 'earshot'`.
   - Generates `earshot_sheet.png` (annotated video frames + spectrogram + loudness + beat/cut sync markers) and `earshot_critique.json` (`earshot critique --fast --json` or `earshot describe --json`) so the agent can visually and quantitatively "hear" any rendered video's mix & cut timing.
   - **Live Verification:** GitHub Actions Run `#41244579041` completed with `conclusion: "success"` (`earshot_sheet.png` + `earshot_critique.json` downloaded & verified).

---
### Phase 6 — `Openverse` + `Clipwing Real SFX` Integration (Complete 3-Tool Sound Design Stack — `2026-11-01`)
Discovered and integrated the remaining two tools of the 3-tool open motion sound-design workflow alongside `earshot`:
- **`Openverse`** (`https://api.openverse.org/v1/` / `WordPress/openverse`, `MIT` license): Keyless public search API across **5M+ openly-licensed real audio files** (Wikimedia Commons `3.88M+`, Jamendo `627K+`, Freesound `587K+`) and **800M+ CC/Public-Domain images**.
- **`Real SFX`** (`https://github.com/Clipwing/skills` -> `skills/real-sfx`, `MIT` scripts + **78 CC0 `uisfx` sounds**): Frame-exact video & HyperFrames sound-design mixer with speech-aware ducking, tonal key matching, mono-cancellation check, AAC true-peak overshoot guard, and separate stem export.

1. **Runs Locally in Arena & on Cloud (`studio/real_sfx/` + `studio/om_hybrid/openverse_realsfx.py`):**
   - `/home/user/studio/real_sfx/` (`1.2 MB`, `MIT`; see `studio/real_sfx/LICENSE_REAL_SFX_MIT.txt`) — Vendored Clipwing `real-sfx` engine (`find_moments.py`, `from_hyperframes.py`, `ui_events.py`, `suggest_cues.py`, `mix.py --voice-safe --duck`, `tonal.py`, `beats.py`, `texture.py`, `bed.py`, `critique.py`, plus `vendor/package.json` installing 78 CC0 `uisfx` cues).
   - `/home/user/studio/om_hybrid/openverse_realsfx.py`:
     - `search_openverse_audio` & `search_openverse_images`: Queries `https://api.openverse.org/v1/` directly on unfiltered cloud IPs (`4.5s` timeout), with automatic fallback to Openverse's upstream Wikimedia Commons + Internet Archive CC catalogs when datacenter IPs block Cloudflare.
     - `ensure_realsfx_ready`: Seeds a 22-sound multi-role `starter_lib/` (`8` distinct whoosh families, `4` hits, risers, drops, pops, clicks, chimes, glitches), indexes any downloaded `openverse_cc0/` recordings, and installs `uisfx` (`78` CC0 UI cues).
     - `auto_sound_design_video`: Runs `from_hyperframes.py` or `find_moments.py --fine` -> `suggest_cues.py` -> `mix.py --voice-safe --duck` -> `critique.py`, outputting both `*_sfx.mp4` and isolated `*_sfx_track.wav` stems.
   - `/home/user/studio/bootstrap.sh` & `/home/user/studio/om_hybrid/_ffmpeg.py`: Upgraded to self-heal **both `ffmpeg` and `ffprobe` (`7.0.2-static`)** in `/tmp/vidtools/`.
   - `/home/user/studio/om_hybrid/cli.py`: Added subcommands `openverse-audio`, `openverse-images`, `realsfx-setup`, and `realsfx-mix`.

2. **Runs on Unlimited 16 GB / 4 vCPU GitHub Cloud Farm (`--mode real_sfx`):**
   - Added `real_sfx` mode across `.github/workflows/cloud_render.yml`, `studio/cloud/hq_worker.py`, and `studio/gh_farm.py` — queries live `api.openverse.org` directly from GitHub's runner IP, renders HyperFrames (or custom `src_url`), mixes frame-exact voice-safe SFX, and runs full visual + loudness QA.
   - **Live Verification:** GitHub Actions Run `#41246041068` completed with `conclusion: "success"` (`15.61 GB RAM / 4 vCPU`, `1080x1920 @ 30fps`, `-14.5 LUFS`, `-1.7 dBTP`, `qa.passed: true`, `0` errors/warnings).

---
### Phase 7 — Unified 6-Layer `master` Pipeline (Connecting All Tools for Any Video — `2026-11-01`)
Audited cross-tool integration so engines do not sit as isolated modes, and connected all 6 layers into a single unified pipeline for **any** video type (`movie`, `cinema`, `motion`, `reaction`, `scifi`):
- `/home/user/studio/om_hybrid/master_pipeline.py` (`master_polish_video` + `cli.py master`): Chains `OpenMontage` intelligence (`detect_silences`, `analyze_energy`, `plan_smart_camera`) -> `HyperFrames` `.cube` 3D LUT color grade (`apply_cinema_look`) -> `Openverse` CC audio + `earshot` 252 bank + `Clipwing Real-SFX` voice-safe ducked sound design (`auto_sound_design_video`) -> `visual_qa` (`run_full_qa`) -> `earshot` Neural AI Ears (`CLAP + AST` sheet & critique when `torch` is installed).
- Upgraded `studio/cloud/hq_worker.py` (`run_t1_hq` and `run_hyperframes`) so both automatically run `Real-SFX` (`sound_design: true` by default, voice-safe ducked on `t1_hq`), and added **`--mode master`** across `.github/workflows/cloud_render.yml`, `hq_worker.py`, and `gh_farm.py` to execute all 6 layers (Node 22 HyperFrames + Openverse + Earshot + Real-SFX + PyTorch CLAP/AST AI Ears + Visual QA) in one Cloud run.
- Added root `/home/user/README.md` documenting the 6-layer stack and 1-command clone/bootstrap workflow.
- **Live Verification:** Tested locally on `ep1` (`23.94s`, `teal-orange-blockbuster`, `13 cues / 10 distinct files`, `-15.5 LUFS`, `-1.6 dBTP`, `0` warnings) AND on GitHub Actions Run `#41246749221` (`--mode master`, `conclusion: "success"`, `15.61 GB RAM / 4 vCPU`, `openverse_api` `200 OK` + `crisp-editorial` LUT + `Real-SFX` + `CLAP/AST` `earshot_sheet.png` + `qa.passed: true`).

---
### Phase 8 — `Motion Director` + Automatic Multi-Repo Motion Routing (`2026-11-01`)
Added automatic motion choreography, vector kinetic HUDs, live-action motion-graphic compositing, and explicit routing rules so every integrated repo's motion & audio features are actively used in real videos:
- `/home/user/studio/om_hybrid/motion_director.py`:
  - `choreograph_shots_table`: Replaces uniform zoom curves with alternating cinematic shot choreography (`hook_punch`, `push_in`, `pull_reveal`, `drift_push`, `climax_punch`).
  - `add_kinetic_motion_hud`: Zero-RAM `libass` vector motion accents (Frame-0 optical hook flash, Hook->Story seam flash, and smooth bottom-edge retention progress bar).
  - `composite_motion_overlay` (`cli.py overlay`): Composites `HyperFrames` (448 GSAP blocks) or `Remotion` motion graphics directly onto live-action video via `screen` luma blend, `colorkey`, or `alpha`.
- Upgraded `studio/cloud/hq_worker.py` (`run_t1_hq`) to enable `choreograph_shots_table`, `add_kinetic_motion_hud`, `seam_mode="zoom_through"`, `look_id="teal-orange-blockbuster"`, and `sound_design=True` by default.
- Added `/home/user/studio/MOTION_AND_TOOL_ROUTING.md` and linked it in `/home/user/START_HERE.md` so any future session automatically applies the full motion + LUT + SFX stack per video type.

---
### Phase 9 — `@technocraftss` Iron Man-Style Difference-Typography + Optical-Flow Velocity Engine (`2026-11-01`)
Reverse-engineered the exact After Effects / Alight Motion mechanics behind the viral `@technocraftss` Iron Man edit format (`33 ms` frame-by-frame RGB math + optical-flow inspection) and built a reusable production engine locally & on the 16 GB Cloud Farm:
- `/home/user/studio/om_hybrid/ironman_edit.py` (`render_ironman_style_edit`):
  - **Layouts (`9:16_center_16:9` & `16:9`):** Supports both Reels/Shorts `1080x1920` (`9:16`) portrait canvas with a dead-centered `1080x608` (`16:9`, `y=656..1264`) cinema strip over pure `#000000` bars and full-bleed `1920x1080` (`16:9`).
  - **Act 1 (`0..drop_s`):** 3x supersampled `ArchivoBlack` `#FFFFFF` typography with `1.12 -> 1.00` ease-out scale slam composited via true **`Blending Mode = Difference` (`|255 - BaseRGB|`)** (warm flames/flares auto-invert to cobalt/cyan, cyan/blue lightning auto-inverts to copper/orange, dark armor/silhouettes auto-turn `#FFFFFF`), `5–8f` `#000000` hard strobe cuts, left-aligned 2-line pre-drop stacked slam, and silent pre-drop blackout tension gap.
  - **Act 2 (`drop_s..end`):** Frame-accurate 2-stage FFmpeg clip decoding + half-beat (`0.48s` / `125 BPM`) velocity speed-ramp (`2.8x` entry snap -> `0.38x` silky slow-mo settle) with bidirectional **Farneback optical-flow frame interpolation (`optical_flow_interp`)**, controlled micro-impulse zoom-shake, dark moody cinema color grade, and clean `0.38s` end fade-to-black.
  - **Neural Vocal Isolation + Clean Dark Synthwave Audio (`isolate_clean_vocal_slice` + `synthesize_clean_dark_edit_music`):** Uses `torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS` neural source separation + soft RMS noise gating to strip 100% of trailer theme music/SFX from character dialogue, paired with a Butterworth-filtered `125 BPM` dark analog synthwave beat (`Dm -> Bb -> Gm -> A` sidechained Reese bass + filtered lead + tight electronic kick/snare + `1.15s` cosine fade-out; `loudnorm` `-14.4 LUFS`, `-1.6 dBTP`).
- Wired **`--mode ironman_edit`** across `.github/workflows/cloud_render.yml` (with `torch` + `torchaudio` for HDemucs), `studio/cloud/hq_worker.py`, `studio/gh_farm.py`, `studio/om_hybrid/__init__.py`, and `studio/MOTION_AND_TOOL_ROUTING.md`.
- **Live Production Verification:** Rendered ***Avengers: Doomsday* (2026) — Robert Downey Jr. (Doctor Doom) Clean `9:16` Edit** (`avengers_doomsday_ironman_edit.mp4`, `1080x1920 @ 30fps`, centered `1080x608` `16:9` strip, `20.64s`, `7.19 MB`) on GitHub Actions Run `#41250549670` (`15.61 GB RAM / 4 vCPU`, `vocal_isolation: ["hdemucs_neural"]`, `-14.4 LUFS`, `-1.6 dBTP`, `qa.passed: true`, `0` errors/warnings).

---
### Phase 10 — Deep Reverse-Engineering of All 11 `Sample` Videos (`SAMPLE_11_EDITING_BIBLE.md` — `2026-11-01`)
Performed full frame-by-frame (`33 ms`), word-level Whisper ASR, cut-cadence, color/shader, and audio-pocket analysis across all **11 reference & creator-breakdown videos** (`S01..S11`) in the user's `Sample` collection, and codified every story pattern + editing blueprint into `/home/user/studio/SAMPLE_11_EDITING_BIBLE.md` (linked in `START_HERE.md`):
- **S01 (`@sumanth.mp4`):** Dual-font Red/White stacked typography + `-32°` Crimson B-Roll Ribbon sandwiched behind rotoscoped silhouette over B&W sky + `1-2f` katana luma-invert flash.
- **S02 + S04 (`@thisiszohair` Sony-viral Spider-Man edit + 81.8s Premiere timeline breakdown):** *"Jigsaw Musical Gap-Filling"* (weaving character dialogue into song applause/instrumental pockets without fighting the groove) + `9:16` centered `16:9` + tiny `18pt` center serif subs + `3f` (`0.10s`, 10 cuts/sec) drum-roll match-cut bursts (`89 cuts` in `27.5s`).
- **S03 (`@_.raajjjjjj_` *Oppenheimer × Bhagavad Gita*):** Cold blue strobe in `#000000` silence + 2-tone Indigo Risograph posterization + 1-bit Bayer dither silhouette (`VISHNU`) + curved CRT barrel lens + monumental full-screen crimson brutalist `DEATH / WORLDS` slam.
- **S05 (`@cashworthclipz` Hawaii Surf):** Meta monitor reveal + Z-depth `HAWAII` behind roto silhouette + `3x3` bento grid + `3` freeze-frame roto clones on `#000000` + 3D planar wave-tracked text (`THEY CAN SMELL THE LEGACY`).
- **S06 (`@marcelgrauu`):** 7 trending shader/OpenCV effects (`Datamosh`, `Blob Tracking` bounding-box web, `Flash Light` luma glow, `Receipt Ticket` thermal dither, `CRT` cyan phosphor, `1-Bit Dither`, `Pink Phosphor`) + asymmetric stacked CTA typography.
- **S07 (`@technocraftss` Iron Man):** Giant `#FFFFFF` `Blending Mode: DIFFERENCE` typography + `5f` `#000000` strobe cuts + `0.45s` half-beat optical-flow velocity montage (implemented in `om_hybrid/ironman_edit.py`).
- **S08 (`kevamarts` *"God's Wisdom"*):** Zero-footage still-drawing edit via `1f` Red/White polarity swap + continuous `wiggle(6,18)` + radial crown glow + `125%` zoomed-invert glitch bars + duotone box swap.
- **S09 (`@willrvail`):** 12-effect music-video checklist (foreground frame wipe, bass shockwave ripple, beat-pop roto clones, **double-exposure inverted silhouette B-roll matte**, slow-mo breather w/ micro-flashes).
- **S10 (`@astroospace`):** Center-locked `(cx, cy)` geometric match-cuts (`69 cuts` in `22s`, `2f` `15 cuts/s` bursts) + `B&W -> Full-Color` beat explosion + square macroblock datamosh ticks.
- **S11 (`@ediday.5` *Fight Club* Shake):** 2-panel top/bottom split w/ edge-pinned Red/White condensed title + nose/eye **Match-Move Face-Locked Shake** (face stationary at center while background smears violently) + 35mm grain.

---
*(Subsequent changes in Phase 11+ will be appended directly below.)*
