# MOTION & MULTI-REPO ROUTING PLAYBOOK (`maker-studio`)

This playbook defines **how the agent must actively combine every integrated repository** (`OpenMontage`, `HyperFrames`, `Remotion`, `earshot`, `Openverse`, `Clipwing Real-SFX`) inside real videos — while strictly preserving the separation of Type 1, Type 2, and Type 3 format rules in `START_HERE.md` and `studio/SPEC.md`.

---

## 1. Camera & Cut Motion Stack (Mandatory on All Live-Action Clips)

1. **Sub-Pixel Face-Tracked Framing (`om_hybrid.smart_camera`):**
   - Never use integer FFmpeg `scale=eval=frame` zoom (causes 2px shimmer) or `fps=30` on `23.976` film (causes 3:2 pulldown judder).
   - Always run `plan_smart_camera(...)` (MediaPipe BlazeFace + two-shot framing + caption collision check) followed by `render_subpixel_segments(..., INTER_LANCZOS4)` at native source FPS.
2. **Alternating Shot Choreography (`om_hybrid.motion_director.choreograph_shots_table`):**
   - Never apply identical `1.00 -> 1.05` zoom to every shot.
   - Automatically alternate across cuts:
     - **Opening Hook (`0..3.5s`):** Fast-engage punch-push (`1.030 -> 1.095`) + Frame-0 optical flash (`0..180 ms`).
     - **Even Story Shots:** Classic cinema push-in (`1.000 -> 1.060`).
     - **Odd Story Shots:** Breath pull-back / spatial reveal (`1.062 -> 1.005`) or gentle micro-drift + push (`fx` drift `+-3.5%`, `1.010 -> 1.055`).
     - **Climax / Peak-Energy Shot (`analyze_energy`):** High-energy punch-in (`1.015 -> 1.092`).
3. **Velocity-Matched Seam Transitions (`seam_mode` in `render_subpixel_segments`):**
   - `zoom_through`: Default for Hook -> Story replay cut (`1.0->1.18` Z-push exit + `0.85->1.0` arrival + peak Gaussian blur + `140 ms` optical flash).
   - `whip_pan`: Best for energetic comedy / action / Type 2 clip-to-clip cuts (fast lateral speed-ramp + 1D horizontal motion streak).
   - `rack_focus`: Best for dramatic / mystery / Type 3 scene changes (DSLR defocus cut).
   - `dip`: Classic cinema dip-to-black when quiet emotional separation is needed.

---

## 2. Kinetic Typography, HUD & Motion Graphics Stack

1. **Vector Kinetic HUD (`om_hybrid.motion_director.add_kinetic_motion_hud`):**
   - Frame-0 subtle optical flash (`0..180 ms`), Hook->Story seam flash, and sleek `6px` bottom-edge live retention progress bar (`x=-1080 -> 0` over total duration).
2. **Word-Level Karaoke & Safe-Zone Captions (`textkit.word_caps_kara`):**
   - Driven by `faster-whisper medium.en` (`t1_hq` Cloud) or local ASR, placed at `cam["recommended_caption_y"]` so captions never occlude faces (`caption_occlusion_frames == 0`).
3. **HyperFrames (`studio/hyperframes/`) & Remotion (`studio/remotion-composer/`) Motion Graphics:**
   - **Standalone Motion Scenes / Explainers / Intro Cards:** Render via Cloud `--mode hyperframes` (Node 22 HTML+CSS+GSAP, `448` installable blocks via `hyperframes add <block>`) or `--mode remotion` (`CinematicRenderer`, `Explainer`, `TitledVideo`, `CollageBurst`, `LyricOverlay`).
   - **Overlaying Motion Graphics ON TOP OF Live Video (`om_hybrid.motion_director.composite_motion_overlay`):**
     Render the HyperFrames/Remotion badge, kinetic lower-third, stat counter, or title burst on pure `#000000` black and composite onto the live-action video with `cli.py overlay base.mp4 overlay.mp4 --out final.mp4 --mode screen` (zero alpha-fringe halo).

---

## 3. Cinema Color Grading Stack (`om_hybrid.cinema_looks`)

Apply offline `33^3` `.cube` 3D LUTs (`lut3d=...:interp=tetrahedral`) matched to genre:
- **Action / Thriller / Blockbuster (`Type 1`):** `teal-orange-blockbuster` (`intensity=0.60`)
- **Drama / Prestige Film (`Type 1`):** `warm-cinema` (`0.65`) or `film-fade` (`0.55`)
- **Sci-Fi / Tech (`Type 1` / `Type 3`):** `scifi-cool` (`0.65`)
- **Reaction / Ranking / Crisp Motion (`Type 2` / `HyperFrames`):** `crisp-editorial` (`0.45–0.65`)

---

## 4. 3-Engine Sound Design Stack (`Openverse` + `earshot` + `Real SFX`)

Respect each format's audio laws from `START_HERE.md` / `SPEC.md`:
- **Type 1 (Continuous Movie Scene):** Keep original movie dialogue clean and primary; use `Real SFX` in `--voice-safe --duck` mode so subtle hook/seam whoosh+impact cues (`earshot` 252 studio bank + `Openverse` CC recordings) land on `0 ms` frame cuts while ducking automatically under dialogue (`-14.8 LUFS`, `<= -1.5 dBTP`).
- **Type 2 (Ranking / Fails):** Follow `studio/type2/TYPE2_SPEC.md` (locked BGM/phrase/chicken rules) + frame-exact rank-card / transition hits from `earshot` / `Real SFX`.
- **Type 3 (Narration Explainer):** Strictly **NO background music** per `SPEC.md`; clean Hindi narration + subtle non-musical UI/transition ticks (`uisfx` / `earshot` `fit/click`, `swish/soft`) ducked under narration if motion cards transition.
- **Post-Mix QA:** Always pass `visual_qa.run_full_qa` locally, and run Cloud `earshot` (`CLAP + AST` spectrogram + sync critique) on flagship/master renders.
