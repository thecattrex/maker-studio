# Maker Studio — Unified 6-Layer Video & Sound Production Engine

Public, self-contained production repository (`https://github.com/thecattrex/maker-studio`) combining **local 2 GB sandbox execution** with an **unlimited 16 GB RAM / 4 vCPU GitHub Actions Cloud Render Farm**.

Every video format (**Type 1** movie/podcast clips, **Type 2** compilations/reactions, **Type 3** motion graphics/explainers, **HyperFrames**, and **Remotion**) runs through one unified stack:

| Layer | Engine | What It Delivers |
|---|---|---|
| **1. Intelligence & Camera** | `studio/om_hybrid/` (`OpenMontage` hybrid) | MediaPipe BlazeFace multi-face safe zones, sub-pixel `INTER_LANCZOS4` motion, velocity seams (`dip`, `zoom_through`, `whip_pan`, `rack_focus`), 5D hook-first scorer, 16 public stock adapters + IGN 1080p resolver |
| **2. Cinema Color & Motion Graphics** | `studio/hyperframes/` + `studio/remotion-composer/` | Offline NumPy `33^3` `.cube` 3D LUTs (`teal-orange-blockbuster`, `crisp-editorial`, `warm-cinema`, `bleach-bypass`, `film-fade`, `scifi-cool`) + Node 22 HyperFrames (HTML+GSAP, 448 registry blocks) + React/Remotion |
| **3. Procedural Studio SFX (252)** | `studio/earshot/` (`MIT`) | 252 zero-copyright physical-synthesis SFX (`whoosh`, `swish`, `cut_hit`, `riser`, `sub_drop`, `pop`, `click`, `glitch`, `logo_sting`) with `0 ms` peak-to-cut sync |
| **4. Real Open-License Media (5M+)** | `studio/om_hybrid/openverse_realsfx.py` (`Openverse`) | Searches & downloads CC0 / CC-BY real recorded audio (`5M+` tracks) and images (`800M+`) via `api.openverse.org/v1/` with automatic Wikimedia + Internet Archive CC fallback |
| **5. Frame-Exact Sound Design** | `studio/real_sfx/` (`Clipwing Real-SFX` + `78` CC0 `uisfx`) | Auto-detects cuts/motion (`find_moments.py`) or HyperFrames elements (`from_hyperframes.py`), places cues (`<= 5 / 10s`), ducks under speech (`--voice-safe --duck`), guards mono phase & AAC true-peak (`-14.8 LUFS`, `<= -1.5 dBTP`), exports `*_sfx_track.wav` stem |
| **6. Visual QA + Neural AI Ears** | `visual_qa.py` + `earshot` (`CLAP + AST`) | Bitstream decode check, face-vs-caption collision check, EBUR128 loudness gate, 4x4 visual contact sheet, plus Cloud `CLAP + AST` spectrogram/sync critique (`earshot_sheet.png` + `earshot_critique.json`) |
| **7. 17-Weapon Viral Edit Arsenal & Skills** | `studio/om_hybrid/viral_vfx.py` + `ironman_edit.py` + `studio/skills/` | MediaPipe XNNPACK AI Human Rotoscoping (`selfie_segmenter.tflite`), TouchDesigner `blob-tracking` (`k1sh0r/blob-tracker` MIT), Difference Typography + Optical-Flow Velocity, Red B-Roll Ribbon behind Roto, 3D Text-Behind-Person, Double-Exposure Silhouette, Roto Clones, Fight Club Face-Locked Shake, Risograph 2-Tone, 1-Bit Bayer Dither, Thermal Receipt, CRT/Pink Phosphor, Optical Datamosh, Still-Art Motion, HDemucs Vocal Isolation, and Jigsaw Music-Pocket Planner (`studio/skills/viral-edits/SKILL.md`) |

---

## Quick Start (Any Fresh Chat or Machine)

```bash
git clone https://github.com/thecattrex/maker-studio.git
cd maker-studio
bash studio/bootstrap.sh
```

### Local Unified Master Pipeline (2 GB RAM Safe)
Polishes **any** video end-to-end (Intelligence -> `.cube` Cinema LUT -> Voice-Safe Real-SFX + Earshot 252 Bank -> Broadcast QA):
```bash
python3 studio/om_hybrid/cli.py master input.mp4 --out final_master.mp4 --preset movie
```

### 16 GB / 4 vCPU GitHub Cloud Render Farm (Unlimited Public Actions)
```bash
# Full 6-Layer Master Pipeline (HyperFrames/Source + LUT + Openverse + Real-SFX + Visual QA + CLAP/AST AI Ears)
python3 studio/gh_farm.py run --mode master --out-dir /tmp/cloud_out

# HQ Movie/Clip Short (faster-whisper medium.en + BlazeFace + 2-pass loudnorm + Voice-Safe Real-SFX)
python3 studio/gh_farm.py run --mode t1_hq --job job.json --out-dir /tmp/cloud_out

# Dedicated modes also available: smoke | hyperframes | earshot | real_sfx | remotion | ironman_edit | vfx_edit
```

### Reusable Agent Skills (`studio/skills/`)
- **`studio/skills/viral-edits/SKILL.md`** — Master guide & CLI/Cloud recipes for applying all 17 viral edit effects (`vfx-list`, `vfx`, `still-art`, `music-pockets`, `ironman_edit`, `vfx_edit`) across Type 1, Type 2, Type 3, and standalone edits.
- **`studio/skills/blob-tracking/SKILL.md`** — TouchDesigner-style OpenCV blob-tracking skill (`k1sh0r/blob-tracker`, `MIT`).
- **`studio/real_sfx/SKILL.md`** — Frame-exact voice-safe sound design skill (`Clipwing/skills`, `MIT`).

See **`START_HERE.md`** for studio rules, **`studio/SAMPLE_11_EDITING_BIBLE.md`** for all 11 reverse-engineered reference styles, and **`studio/UPGRADE_HANDOFF_LOG.md`** for the complete chronological changelog (Phases 1–11).
