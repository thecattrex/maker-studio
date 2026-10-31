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

---
*(Subsequent changes in Phase 6+ will be appended directly below.)*
