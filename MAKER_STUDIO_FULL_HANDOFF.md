# MAKER STUDIO — COMPLETE END-TO-END HANDOFF & OPERATING BIBLE (`OpenMontage` -> `Phase 11`)

**Repository:** `https://github.com/thecattrex/maker-studio` (**PUBLIC** — Unlimited 16 GB RAM / 4 vCPU GitHub Actions)  
**Purpose of this file:** Upload this `.md` file into **any new Arena / AI Agent chat** along with your GitHub Personal Access Token (`<USER_GITHUB_TOKEN>`). The new agent should read this file first, run the 60-second bootstrap below, and immediately gain **100% of our studio code, 16 GB Cloud Render Farm, 3-engine SFX stack, 11 Sample Video blueprints, and all 17 Viral Edit tools & skills**.

---

## 0. Instant 60-Second Setup in a New Chat (Using User's GitHub Token)

When the user provides this `.md` file + their GitHub token (`<USER_GITHUB_TOKEN>`), run this exact setup in `bash`:

```bash
set -e
# 1. Clone maker-studio into /home/user (or pull latest if already present)
if [ ! -d /home/user/studio ]; then
  git clone https://github.com/thecattrex/maker-studio.git /tmp/ms_clone
  cp -a /tmp/ms_clone/. /home/user/
  rm -rf /tmp/ms_clone
fi

# 2. Store GitHub token ONLY in /home/user/.git-credentials (excluded from snapshots & git!)
printf "https://thecattrex:%s@github.com\n" "<USER_GITHUB_TOKEN>" > /home/user/.git-credentials
chmod 600 /home/user/.git-credentials
git config --global credential.helper "store --file=/home/user/.git-credentials"
cd /home/user
git remote add origin https://github.com/thecattrex/maker-studio.git 2>/dev/null || \
  git remote set-url origin https://github.com/thecattrex/maker-studio.git
git pull --ff-only origin main || true

# 3. Bootstrap local FFmpeg 7.0.2 + ffprobe + MediaPipe SelfieSegmenter + audio/vision stack
bash /home/user/studio/bootstrap.sh

# 4. Verify 16 GB GitHub Cloud Render Farm connection + list all 17 Viral VFX tools
python3 /home/user/studio/gh_farm.py status
python3 /home/user/studio/om_hybrid/cli.py vfx-list
```

### Mandatory GitHub & Security Guardrails (NEVER VIOLATE)
1. **Keep `thecattrex/maker-studio` PUBLIC:** Public visibility unlocks `15.61 GB RAM / 4 vCPU` GitHub-hosted `ubuntu-latest` runners with **unlimited free GitHub Actions minutes**. Never switch it to private.
2. **Scope Strictly to `thecattrex/maker-studio`:** Never read, modify, or touch any other repository under `thecattrex`'s GitHub account.
3. **Zero Secrets or Private Links in Git:** Never commit personal access tokens, `.git-credentials`, or unlisted Google Drive file links into public commits.
4. **Turn-Pause Credential Note:** Arena snapshots intentionally exclude `.git/config` and `.git-credentials` across paused turns (such as `ask_user`). Before pushing or calling `gh_farm.py` after a paused turn, re-create `/home/user/.git-credentials` (`chmod 600`) and `git remote set-url origin https://github.com/thecattrex/maker-studio.git`.
5. **Keep `/home/user` Under `128 MB`:** Store large temporary source downloads and intermediate renders in `/tmp/...` and clean them up (`rm -rf /tmp/...`) once the final deliverable is saved.

---

## 1. User Standing Rules & Format Laws

1. **Language:** Always reply in **Roman Hinglish** (English alphabet Hinglish — e.g. `"bhai ye video ready hai"`, **NOT Devanagari Hindi script**!).
2. **Google Drive Rule:** Do **not** touch, inspect, upload, or modify Google Drive unless the user explicitly asks in that message. (Never inspect `ep1..ep4` episodes unless explicitly instructed.)
3. **Keep Video Formats Strictly Separated (`START_HERE.md` + `studio/SPEC.md`):**
   - **Type 1 (Continuous Movie Scene Short):** `20–25 seconds`, **English movie + English original audio** (overrides old generic Hindi-dub note), **Hook / Punchline ALWAYS placed FIRST at `0.00s`** followed by a velocity-matched `zoom_through` seam into the continuous scene, dynamic word-level safe-zone captions (`caption_occlusion_frames == 0`), smooth alternating camera motion, `.cube` cinema LUT, and voice-safe ducked SFX (`-14.8 LUFS`, `<= -1.5 dBTP`).
   - **Type 2 (Ranking / Fails Compilation):** Governed strictly by `studio/type2/TYPE2_SPEC.md` + frame-exact rank/transition SFX.
   - **Type 3 (Hindi Narration Explainer / Mystery / Science):** Clean Hindi narration, **strictly NO background music (`BGM`)** per `SPEC.md`, subtle non-musical UI/transition ticks only, paired with high-retention visual shaders (`risograph_2tone`, `dither_1bit`, `crt_phosphor`, `blob_tracking`, `text_behind_subject`).
   - **Standalone Viral Fan / Aesthetic Edits (`@technocraftss`, `@sumanth.mp4`, `@thisiszohair`, `kevamarts`, `@astroospace`):**
     - **0.0s Hook / Punchline / Naughtiness Rule:** ALWAYS open immediately at `0.00s` with a spicy, witty, cheeky, or punchline hook moment that grabs attention on the very first second — never open with slow exposition.
     - **Real Song + `7f2...` Jigsaw Amplitude Rule (NO Python-synthesized songs!):** Never generate synthetic music from scratch in Python. Always choose a **real song/track** (via `Archive.org`, `Openverse`, `Jamendo`, or user-supplied audio), profile its actual waveform amplitude valleys & transient peaks, weave `HDemucs`-isolated dialogue into the song's pockets with diagonal Premiere-style rubberband ducking (`mix_real_song_jigsaw` — ducking vocal-mids `-14 dB` during speech, swelling up `-2.8 dB` inside every micro-pause so the song nods to the beat!), and snap every Act-2 visual cut directly onto the real song's measured kick/clap transients!

---

## 2. Complete Chronological Upgrade Summary (`OpenMontage` -> `Phase 11`)

Everything built and integrated from the moment we started inspecting external repositories:

| Phase | Repo / Capability Integrated | Where It Lives in `maker-studio` | What It Unlocked |
|---|---|---|---|
| **Phase 1** | **`calesthio/OpenMontage`** (selective hybrid) | `studio/om_hybrid/{smart_camera,pacing_audio,clip_scout,visual_qa,cli}.py` | MediaPipe `BlazeFace` multi-face safe framing, sub-pixel `INTER_LANCZOS4` pan/zoom (zero 2px integer jitter), native FPS preservation, 4 seam transitions (`zoom_through`, `whip_pan`, `rack_focus`, `dip`), 5D hook-first scorer, 16 zero-key stock adapters + IGN 1080p MP4 extractor, automated EBUR128 + occlusion QA |
| **Phase 2** | **16 GB GitHub Actions Cloud Farm + `Remotion`** | `.github/workflows/cloud_render.yml`, `studio/cloud/hq_worker.py`, `studio/gh_farm.py`, `studio/remotion-composer/` | Offloads heavy 1080p renders, `faster-whisper medium.en` word ASR, and React/Remotion compositions (`CinematicRenderer`, `Explainer`, `TitledVideo`, `CollageBurst`, `LyricOverlay`) from 2 GB sandbox to Cloud |
| **Phase 3** | **`heygen-com/hyperframes`** (`0.8.224`) *(skipped `Agent-Reach`)* | `studio/hyperframes/`, `om_hybrid/cinema_looks.py`, `om_hybrid/sfx_sync.py` | HTML+CSS+GSAP headless Chrome deterministic motion-graphics engine (`448` installable registry blocks) + 6 offline `33^3` `.cube` 3D cinema LUTs (`teal-orange-blockbuster`, `crisp-editorial`, `warm-cinema`, `bleach-bypass`, `film-fade`, `scifi-cool`) |
| **Phase 4** | **Public Repo Flip (`16 GB / 4 vCPU`)** | `https://github.com/thecattrex/maker-studio` | Verified `15.61 GB RAM / 4 Xeon vCPUs` + unlimited free Actions minutes |
| **Phase 5** | **`Leonxlnx/earshot`** (`v0.4.0`, `MIT`) | `studio/earshot/` + Cloud `--mode earshot` | **252 zero-copyright procedural studio SFX** (`pro_whoosh_big`, `swish`, `cut_hit`, `pro_riser`, `pro_sub_drop`, `glitch`, `ui`, etc.) synced with `0 ms` peak-to-cut lag + Cloud PyTorch `CLAP + AST` neural AI Ears (`earshot_sheet.png` + `earshot_critique.json`) |
| **Phase 6** | **`WordPress/openverse`** + **`Clipwing/skills` (`real-sfx`)** | `om_hybrid/openverse_realsfx.py`, `studio/real_sfx/` (`78` CC0 `uisfx`) + Cloud `--mode real_sfx` | Keyless search across `5M+` CC audio & `800M+` images (`api.openverse.org` w/ Wikimedia+IA fallback) + frame-exact speech-ducking mixer (`--voice-safe --duck`, `<= 5 cues/10s`, AAC true-peak guard, isolated `*_sfx_track.wav` stem) |
| **Phase 7** | **Unified 6-Layer `master` Pipeline** | `om_hybrid/master_pipeline.py` (`cli.py master` + Cloud `--mode master`) | Chains Intelligence -> `.cube` 3D LUT -> Openverse + Earshot + Real-SFX -> Visual QA -> Cloud `CLAP/AST` AI Ears in 1 command for any video |
| **Phase 8** | **`Motion Director` + Multi-Repo Routing** | `om_hybrid/motion_director.py`, `studio/MOTION_AND_TOOL_ROUTING.md` | Alternating shot choreography (`hook_punch`, `push_in`, `pull_reveal`, `drift_push`, `climax_punch`), `libass` vector kinetic HUD (hook flash + bottom retention bar), and `composite_motion_overlay` (`screen`/`colorkey`/`alpha`) |
| **Phase 9** | **`@technocraftss` Iron Man Engine + `HDemucs`** | `om_hybrid/ironman_edit.py` + Cloud `--mode ironman_edit` | `9:16_center_16:9` & `16:9` layouts, 3x-supersampled **`Blending Mode: DIFFERENCE` (`|255 - BaseRGB|`)** giant typography, `5f` `#000000` strobes, Farneback optical-flow `2.8x -> 0.38x` velocity cuts, **Meta `HDEMUCS_HIGH_MUSDB_PLUS` Neural Vocal Stem Isolation** (strips 100% of trailer theme music/clanks!), and Butterworth `125 BPM` dark synthwave generator |
| **Phase 10** | **11 `Sample` Videos Master Breakdown** | `studio/SAMPLE_11_EDITING_BIBLE.md` | Frame-exact (`33 ms`) + Whisper ASR reverse-engineering of all 11 reference edits & pro creator breakdowns (`S01..S11`) |
| **Phase 11** | **17-Weapon Viral VFX Arsenal + AI Roto + Skills** | `om_hybrid/viral_vfx.py`, `om_hybrid/models/selfie_segmenter.tflite`, `studio/skills/blob-tracking/`, `studio/skills/viral-edits/SKILL.md`, Cloud `--mode vfx_edit` | 30+ FPS XNNPACK human rotoscoping (`selfie_segmenter.tflite`), TouchDesigner `blob-tracker` (`k1sh0r/blob-tracker` MIT), 17 CLI/Python/Cloud VFX tools, and step-by-step reusable `SKILL.md` guides |
| **Phase 12** | **2-Act `9:10` Scene -> Cross-Movie Actor Aura Drop Engine** | `om_hybrid/aura_edit.py` + Cloud `--mode aura_edit` | Exact `1080x1200` (`9:10` inside `1080x1920`) cinema box, 4K AE CC sharpen grade, `HDemucs` neural vocal isolation + `@Proxeditz07` glowing neon keyword captions in Act 1, and cross-movie Optical-Flow Velocity + `S_Shake` + `bass_shockwave` + AI-roto 3D hero title in Act 2 |

---

## 3. Repository File Map (`/home/user/`)

```text
/home/user/
├── README.md                              # Architecture overview & quick start
├── START_HERE.md                          # Core studio operating rules (Type 1 / Type 2 / Type 3 separation)
├── MAKER_STUDIO_FULL_HANDOFF.md           # THIS complete end-to-end handoff document
├── .github/workflows/cloud_render.yml     # 16 GB / 4 vCPU GitHub Actions workflow (9 modes)
├── assets/fonts/                          # 16 bundled fonts (ArchivoBlack, Anton, PlayfairDisplay, Inter, NotoSansDevanagari...)
└── studio/
    ├── bootstrap.sh                       # Self-healing installer: static ffmpeg/ffprobe 7.0.2 + mediapipe + yt-dlp + audio/CV
    ├── gh_farm.py                         # Local -> GitHub Cloud controller (`status`, `run --mode ... --job ... --out-dir ...`)
    ├── SPEC.md                            # Canonical Type 1 / Type 2 / Type 3 spec
    ├── MOTION_AND_TOOL_ROUTING.md         # Mandatory motion, LUT, HUD & SFX routing rules
    ├── SAMPLE_11_EDITING_BIBLE.md         # Complete reverse-engineering of all 11 Sample videos (S01..S11)
    ├── UPGRADE_HANDOFF_LOG.md             # Detailed Phase 1..11 engineering changelog
    ├── t1.py, render.py, textkit.py, templates.py, analyze.py, t3.py, type2/   # Core Type 1/2/3 engines
    ├── cloud/hq_worker.py                 # 16 GB Cloud worker executing all 9 render modes + QA
    ├── earshot/                           # Vendored MIT earshot v0.4.0 (252 procedural SFX + CLAP/AST AI Ears)
    ├── real_sfx/                          # Vendored MIT Clipwing real-sfx + 78 CC0 uisfx cues
    ├── hyperframes/                       # HeyGen HyperFrames HTML+CSS+GSAP compositions
    ├── remotion-composer/                 # React/Remotion compositions
    ├── skills/
    │   ├── viral-edits/SKILL.md           # MASTER SKILL: How & when to run all 17 S01..S11 viral edits on any video
    │   └── blob-tracking/                 # Vendored MIT k1sh0r/blob-tracker (SKILL.md + blobtrack.py + JetBrainsMono)
    └── om_hybrid/
        ├── cli.py                         # Unified CLI (`vfx-list`, `vfx`, `still-art`, `music-pockets`, `master`, `grade`, `overlay`...)
        ├── viral_vfx.py                   # 17-Weapon Viral Edit Engine (AI roto, shaders, Fight Club shake, Risograph, Datamosh...)
        ├── ironman_edit.py                # @technocraftss Difference-Typography + Optical-Flow Velocity + HDemucs Vocal Isolation
        ├── smart_camera.py                # BlazeFace safe-zone planner + sub-pixel Lanczos4 camera + 4 seam transitions
        ├── motion_director.py             # Alternating shot choreography + libass HUD + motion overlay compositor
        ├── cinema_looks.py                # 33^3 .cube 3D LUT generator & applicator
        ├── sfx_sync.py                    # 0ms apex-synced earshot wrapper
        ├── openverse_realsfx.py           # Openverse 5M+ CC search + Real-SFX auto sound-design wrapper
        ├── master_pipeline.py             # 6-layer end-to-end polish pipeline
        ├── pacing_audio.py                # Silences, energy curve, 5D hook-first candidate scorer
        ├── clip_scout.py                  # 16 public stock adapters + IGN 1080p MP4 extractor
        ├── visual_qa.py                   # Decode + resolution + face-caption collision + EBUR128 loudness + contact sheet QA
        └── models/
            ├── blaze_face_short_range.tflite   # MediaPipe BlazeFace detector
            └── selfie_segmenter.tflite         # MediaPipe XNNPACK AI Human Foreground Rotoscope model (244 KB)
```

---

## 4. All 17 Viral Edit Weapons (`S01..S11`) — Quick Command Reference

Full recipes live in **`/home/user/studio/skills/viral-edits/SKILL.md`**. Every effect in `cli.py vfx` accepts `--windows-json '[[t0, t1], ...]'` so you can fire effects selectively on hooks, beats, or climax moments without hurting dialogue clarity!

| # | Effect / Tool | Inspired By | One-Line Local CLI Command (`python3 studio/om_hybrid/cli.py ...`) |
|---|---|---|---|
| 1 | **`ironman_edit`** (`Difference` Text + Optical-Flow Velocity + `HDemucs` Vocals) | `S07` (`@technocraftss`) | `python3 studio/gh_farm.py run --mode ironman_edit --job job.json --out-dir /tmp/out` *(or `om_hybrid.render_ironman_style_edit`)* |
| 2 | **`red_ribbon_roto`** (B&W Sky + `-22°` Crimson B-Roll Strip Behind Roto Silhouette + Katana Invert Flash) | `S01` (`@sumanth.mp4`) | `vfx in.mp4 --effect red_ribbon_roto --params-json '{"broll_mp4":"act.mp4","angle_deg":-22,"katana_flash_times":[3.2]}' --out out.mp4` |
| 3 | **`text_behind_subject`** (3D Solid or Video-Textured Giant Text Behind Person) | `S05` (`@cashworthclipz` *HAWAII*) | `vfx in.mp4 --effect text_behind_subject --params-json '{"text":"LEGACY","color_hex":"#F4A236","font_px":220}' --windows-json '[[0,2.5]]' --out out.mp4` |
| 4 | **`silhouette_double_exp`** (Fast B-Roll Playing *Inside* Human Silhouette) | `S09` (`@willrvail` #7) | `vfx in.mp4 --effect silhouette_double_exp --params-json '{"broll_mp4":"broll.mp4","bg_hex":"#F2F4F8"}' --out out.mp4` |
| 5 | **`roto_clone_pop`** (Beat-Pop Left/Right Clones OR `1-2-3` Freeze Cutouts on `#000000`) | `S05` + `S09` | `vfx in.mp4 --effect roto_clone_pop --params-json '{"clone_mode":"offset_live","beat_times":[0.8,1.6]}' --out out.mp4` |
| 6 | **`flashlight_glow`** (Glowing White Phosphor Silhouette + Bloom in Darkness) | `S06` (`@marcelgrauu`) | `vfx in.mp4 --effect flashlight_glow --out out.mp4` |
| 7 | **`blob_tracking`** (TouchDesigner Boxes + Connecting Web Lines + Numeric Chips) | `S06` (`k1sh0r/blob-tracker`) | `vfx in.mp4 --effect blob_tracking --params-json '{"small":25,"medium":8,"large":3,"invert":0.25}' --out out.mp4` |
| 8 | **`fight_club_shake`** (Nose/Eye Locked Still at Center + Motion-Smeared Shaking Room + 35mm Grain) | `S11` (`@ediday.5`) | `vfx in.mp4 --effect fight_club_shake --params-json '{"shake_px":26,"zoom":1.18}' --windows-json '[[0,2.2]]' --out out.mp4` |
| 9 | **`risograph_2tone`** (Indigo/Periwinkle 2-Tone Print + Crimson Serif Bars) | `S03` (*Oppenheimer × Gita*) | `vfx in.mp4 --effect risograph_2tone --params-json '{"top_caption":"LINE, FROM THE","bot_caption":"BHAGAVAD GITA"}' --out out.mp4` |
| 10 | **`dither_1bit`** (`8x8` Ordered Bayer 1-Bit Stipple Dither + Gold Label) | `S03` + `S06` | `vfx in.mp4 --effect dither_1bit --params-json '{"contrast":1.4,"label":"VISHNU","label_hex":"#D9C53B"}' --out out.mp4` |
| 11 | **`receipt_ticket`** (Crinkled Thermal Receipt Paper + Dithered Video + Barcode) | `S06` (`@marcelgrauu`) | `vfx in.mp4 --effect receipt_ticket --params-json '{"title":"MAKER STUDIO"}' --out out.mp4` |
| 12 | **`crt_phosphor`** (`cyan` CRT, `pink` Night-Vision Phosphor, or `indigo_tv` Curved Barrel Lens) | `S03` + `S06` | `vfx in.mp4 --effect crt_phosphor --params-json '{"palette":"indigo_tv","barrel_k":0.24}' --out out.mp4` |
| 13 | **`datamosh_optical`** (Optical-Flow P-Frame Pixel Melt + `16x16` Block Glitches) | `S06` + `S10` | `vfx in.mp4 --effect datamosh_optical --params-json '{"mosh_times":[1.2],"mosh_dur_s":1.1,"block_glitches":14}' --out out.mp4` |
| 14 | **`bass_shockwave`** (Concentric Radial Refraction Ripple on 808 Beats) | `S09` (`@willrvail` #4) | `vfx in.mp4 --effect bass_shockwave --params-json '{"beat_times":[0.5,2.4],"strength_px":30}' --out out.mp4` |
| 15 | **`center_match_strobe`** (`B&W` Pre-Beat Desaturation -> `145%` Full-Color Explosion) | `S10` (`@astroospace`) | `vfx in.mp4 --effect center_match_strobe --params-json '{"drop_s":1.8}' --out out.mp4` |
| 16 | **`music-pockets` + `write_center_serif_ass`** (*Jigsaw Musical Gap* Dialogue Planner + `18pt` Center Serif Subs) | `S02 + S04` (`@thisiszohair`) | `music-pockets song.mp3 --min-gap 0.50` |
| 17 | **`still-art`** (Zero-Footage 1-Image Motion Edit: `1f` Polarity Flip + Wiggle + Radial Glow + Glitch Bars) | `S08` (`kevamarts`) | `still-art poster.jpg --title-top "GOD'S" --title-main "WISDOM" --layout 9:16_center_16:9 --out edit.mp4` |

---

## 5. All 9 GitHub Cloud Render Farm Modes (`studio/gh_farm.py`)

Run heavy HD renders on GitHub's `15.61 GB RAM / 4 vCPU` runner and auto-download the finished MP4 + `qa_sheet.jpg` + `cloud_report.json`:

```bash
python3 /home/user/studio/gh_farm.py run --mode <MODE> [--job /tmp/job.json] --out-dir /tmp/cloud_out
```

1. **`t1_hq`** — Full Type-1 Hook-First Movie Short (`faster-whisper medium.en` word karaoke + BlazeFace sub-pixel camera + `choreograph_shots_table` + `zoom_through` seam + `teal-orange-blockbuster` `.cube` LUT + `libass` retention HUD + voice-safe `Real-SFX` + 2-pass `-14.8 LUFS` mastering):
   ```json
   {
     "out_name": "movie_ep.mp4",
     "src_url": "https://assets.ign.com/videos/.../trailer_1080p.mp4",
     "story_start": 42.0,
     "story_dur": 21.5,
     "hook_start": 56.2,
     "hook_dur": 3.2,
     "seam_mode": "zoom_through",
     "look_id": "teal-orange-blockbuster"
   }
   ```
2. **`ironman_edit`** — 2-Act `@technocraftss` Difference-Typography + Optical-Flow Velocity + `HDemucs` Neural Vocal Stem Isolation (`layout: "9:16_center_16:9"` or `"16:9"`):
   - Downloads `sources` dict (`{"src1": "https://..."}`), isolates 100% clean character dialogue via `torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS` (stripping trailer theme songs!), renders 3x-supersampled `Difference` text + velocity cuts + clean `125 BPM` Butterworth dark synthwave beat.
3. **`vfx_edit`** — Chained Multi-Effect Viral VFX Pipeline (or `still_art_edit` via `image_url`):
   ```json
   {
     "out_name": "chained_vfx.mp4",
     "src_url": "https://.../clip.mp4",
     "broll_url": "https://.../broll.mp4",
     "chain": [
       {"effect": "text_behind_subject", "params": {"text": "RISE", "color_hex": "#F4A236"}, "windows": [[0.0, 2.0]]},
       {"effect": "red_ribbon_roto", "params": {"katana_flash_times": [3.4]}, "windows": [[2.0, 5.0]]},
       {"effect": "fight_club_shake", "params": {"shake_px": 24}, "windows": [[5.0, 7.0]]},
       {"effect": "blob_tracking", "params": {"small": 22}}
     ]
   }
   ```
4. **`master`** — End-to-end 6-Layer Master Pipeline (HyperFrames or `src_url` + `.cube` LUT + live `Openverse` API + `earshot` 252 + `Real-SFX` + `CLAP/AST` neural AI Ears spectrogram critique).
5. **`hyperframes`** — Node 22 + Headless Chrome GSAP motion-graphics composition (`comp_dir` or inline HTML).
6. **`remotion`** — Node 20 React/Remotion composition render.
7. **`real_sfx`** — Frame-exact Clipwing `Real-SFX` + live `Openverse` audio design.
8. **`earshot`** — Standalone procedural SFX + PyTorch `CLAP + AST` audio-visual sync evaluation.
9. **`smoke`** — Fast 45-second health check verifying runner RAM, CPUs, FFmpeg, LUTs, and QA.
10. **`aura_edit`** — 2-Act `9:10` (`1080x1200` inside `1080x1920`) Scene Setup -> Cross-Movie Actor Aura Velocity Drop (`om_hybrid/aura_edit.py` + `HDemucs` vocal stem isolation + glowing keyword subs + multi-movie optical-flow velocity montage).

---

## 6. Proven Footage Sources & Sandbox Technical Notes (Avoid Past Dead Ends!)

1. **Fetching Official 1080p Movie Trailers on Datacenter IPs:**
   - YouTube (`yt-dlp`) and IMDb video pages block cloud/datacenter IPs.
   - **Reliable Official 1080p Source:** Search `site:ign.com/videos "<Movie Name>" trailer` via `web_search`, then run:
     ```bash
     python3 /home/user/studio/om_hybrid/cli.py ign "https://www.ign.com/videos/..."
     ```
     which extracts direct `1920x1080` `https://assets.ign.com/videos/...mp4` CDN links downloadable via `curl` at full speed both locally and on GitHub Cloud!
   - For CC0/CC-BY B-roll, images, and real Foley audio: use `cli.py search "<query>"` (16 public stock adapters) and `cli.py openverse-audio "<query>"` / `cli.py openverse-images "<query>"`.
2. **Technical Gotchas Already Solved in Code:**
   - **2 GB Local Sandbox RAM Cap:** Never hold >1 decoded `1920x1080` clip in RAM locally; stream frame-by-frame into FFmpeg (`-preset fast -x264-params rc-lookahead=20`) or dispatch heavy multi-clip HD jobs to the `16 GB` GitHub Cloud Farm (`gh_farm.py`).
   - **`faster-whisper` + `PyAV` locally:** Decode `16 kHz` mono float32 WAV via FFmpeg + `soundfile.read(..., dtype="float32")` and pass the NumPy array directly to `WhisperModel.transcribe(audio_np)` to avoid `av.open(metadata_errors=...)` version mismatches.
   - **Static FFmpeg `7.0.2` Filters:** Has `libass` (`ass=`), `lut3d=`, `ebur128`, `loudnorm`, and `alimiter` (always pass `level=false` to `alimiter` so it doesn't undo `loudnorm`!); does not compile `drawtext` (use `libass` or PIL/OpenCV).
   - **Frame-Accurate H.264 Clip Slicing:** Always use 2-stage FFmpeg seeking (`-ss max(0, s0-2.5) -i video.mp4 -ss min(2.5, s0) -t dur`) so GOP keyframes never shift shot boundaries or introduce accidental mid-shot cuts.
   - **`detect_shots()` Return Schema:** Shot dicts use `f_start`, `f_end`, and `fps` (`start_s = sh["f_start"] / sh["fps"]`).
