---
name: viral-edits
description: Apply 17 pro After-Effects / TouchDesigner / Premiere / Resolve viral editing techniques (AI human rotoscoping, Difference typography, optical-flow velocity ramps, Red B-roll ribbons, Blob Tracking, Fight Club face-locked shake, Risograph 2-tone print, 1-Bit Bayer dither, Thermal Receipt, CRT/Pink Phosphor, Optical Datamosh, Double-Exposure Silhouette, Roto Clones, Bass Shockwave, Still-Art motion, and Jigsaw Musical Gap dialogue weaving) to ANY video locally or on the 16 GB GitHub Cloud Farm.
---

# Viral Edits Skill (`maker-studio` — 17-Weapon Arsenal)

Use this skill whenever building or upgrading **any** video in `maker-studio` so edits feel like high-retention human After Effects / Premiere / TouchDesigner productions rather than plain footage + text.

---

## 1. Quick Routing Matrix — Which Cool Edit Fits Which Video?

*(Always preserve Type 1 / Type 2 / Type 3 structural separation in `START_HERE.md` — apply VFX selectively via `--windows-json` on hooks, transitions, and climax beats when dialogue clarity is primary!)*

| Video Type / Genre | Best Effects to Combine | Why It Works |
|---|---|---|
| **Type 1 — Continuous Movie Scene (`20–25s`)** | `fight_club_shake` (on `0.8s` intense line) + `bass_shockwave` (on Hook->Story seam) + `smart_camera` `zoom_through` | Keeps movie scene continuous & clean while making peak emotional moments hit viscerally |
| **Type 2 — Ranking / Fails / Reaction** | `blob_tracking` (on tech/stunt moment) + `roto_clone_pop` (on `#1` winner reveal) + `bass_shockwave` | Turns static clip reveals into modern high-energy creator edits |
| **Type 3 — Hindi Explainer / Mystery / History / Science** | `risograph_2tone` (historical scenes) + `dither_1bit` + `crt_phosphor` (`indigo_tv`) + `text_behind_subject` (topic hook) | Gives documentary/scripture/science visuals a signature `@_.raajjjjjj_` / `@marcelgrauu` editorial look (with **NO BGM** per Type 3 law!) |
| **Superhero / Anime / Villain Hype Edit** | `ironman_edit` (`Difference` text + velocity) OR `red_ribbon_roto` (`-32°` crimson B-roll behind roto silhouette + katana invert flash) | Authentic `@technocraftss` & `@sumanth.mp4` viral fan-edit mechanics |
| **Romantic / Emotional Movie Montage** | `plan_jigsaw_music_pockets` + `9:16_center_16:9` + `write_center_serif_ass` (`18pt`) + `3-frame` (`0.10s`) drum-roll match cuts | Exact `@thisiszohair` Sony-viral Spider-Man formula |
| **Music / Rap / Lifestyle / Travel Edit** | `text_behind_subject` (`HAWAII` style) + `silhouette_double_exp` + `roto_clone_pop` (`freeze_black` or `offset_live`) + `datamosh_optical` | Authentic `@cashworthclipz` & `@willrvail` multi-layer depth |
| **Tech / AI / Cyberpunk / Underground Edit** | `blob_tracking` + `receipt_ticket` + `crt_phosphor` (`cyan` or `pink`) + `center_match_strobe` | Instant `@marcelgrauu` & `@astroospace` TouchDesigner aesthetic |
| **Zero-Footage Poster / Manga / Sketch / Deity Art** | `still-art` (`render_still_art_edit`) | Turns **1 single static image** into a 15–20s beat-synced edit (`kevamarts` style) |

---

## 2. One-Line CLI Commands (`studio/om_hybrid/cli.py`)

List all 17 available effects at any time:
```bash
python3 /home/user/studio/om_hybrid/cli.py vfx-list
```

### A. AI Human Rotoscoping & Depth Layering (`selfie_segmenter.tflite` — 30+ FPS CPU)

1. **3D Z-Depth Text Behind Person (`S05` `HAWAII` / `AROUND`):**
   ```bash
   # Solid sunset-gold giant text behind the person:
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect text_behind_subject \
     --params-json '{"text":"LEGACY","color_hex":"#F4A236","font_px":220,"y_frac":0.42}' \
     --windows-json '[[0.0, 2.5]]' --out out.mp4

   # Video-textured text fill (pass broll_mp4 inside params):
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect text_behind_subject \
     --params-json '{"text":"STOP","broll_mp4":"fire_broll.mp4","font_px":260}' --out out.mp4
   ```

2. **Crimson B-Roll Ribbon Behind Roto Silhouette + Katana Invert Flash (`S01` `@sumanth.mp4`):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect red_ribbon_roto \
     --params-json '{"broll_mp4":"action_broll.mp4","angle_deg":-24,"band_frac":0.15,"katana_flash_times":[3.2, 6.4]}' \
     --out out.mp4
   ```

3. **Double-Exposure Inverted Silhouette (`S09` `@willrvail` — B-Roll Plays *Inside* Human Silhouette):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect silhouette_double_exp \
     --params-json '{"broll_mp4":"fast_cuts.mp4","bg_hex":"#F2F4F8"}' \
     --windows-json '[[2.0, 5.0]]' --out out.mp4
   ```

4. **Beat-Synced Roto Clones (`S09` Live Offset Clones OR `S05` 3 Freeze-Frames on `#000000`):**
   ```bash
   # Live left/right clones popping with 1-frame flash on snare hits:
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect roto_clone_pop \
     --params-json '{"clone_mode":"offset_live","offset_px":140,"beat_times":[0.8, 1.6, 2.4]}' \
     --windows-json '[[0.6, 2.8]]' --out out.mp4

   # 3 sequential freeze-frame cutouts popping 1->2->3 on pure black:
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect roto_clone_pop \
     --params-json '{"clone_mode":"freeze_black","beat_times":[0.2, 0.6, 1.0]}' --out out.mp4
   ```

5. **Flash-Light Glowing Silhouette (`S06` `@marcelgrauu`):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect flashlight_glow --out out.mp4
   ```

---

### B. TouchDesigner, Brutalist Print, CRT & Glitch Shaders (`S03`, `S06`, `S10`)

6. **TouchDesigner Blob Tracking (`S06` — Vendored `k1sh0r/blob-tracker` MIT):**
   *(White boxes locking onto bright/moving regions + connecting web lines + numeric coordinate chips + inverted windows)*
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect blob_tracking \
     --params-json '{"small":25,"medium":8,"large":3,"invert":0.25}' --out out.mp4
   ```

7. **2-Tone Indigo Risograph Print + Crimson Serif Bars (`S03` *Oppenheimer × Bhagavad Gita*):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect risograph_2tone \
     --params-json '{"dark_hex":"#1A2168","light_hex":"#CED8F7","top_caption":"LINE, FROM THE","bot_caption":"BHAGAVAD GITA"}' \
     --out out.mp4
   ```

8. **1-Bit Ordered Bayer Stipple Dither (`S03` Vishnu / `S06` Statue):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect dither_1bit \
     --params-json '{"contrast":1.4,"label":"VISHNU","label_hex":"#D9C53B"}' --out out.mp4
   ```

9. **Thermal Receipt Ticket Print (`S06` `@marcelgrauu`):**
   ```bash
   python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect receipt_ticket \
     --params-json '{"title":"MAKER ARCHIVE"}' --out out.mp4
   ```

10. **CRT Cyan Phosphor / Pink Phosphor / Curved Barrel-Lens TV (`S03` & `S06`):**
    ```bash
    # Cyan CRT | Pink Phosphor | Curved Indigo TV (`palette`: "cyan" | "pink" | "indigo_tv")
    python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect crt_phosphor \
      --params-json '{"palette":"indigo_tv","barrel_k":0.24}' --out out.mp4
    ```

11. **Optical-Flow P-Frame Datamosh + Square Block Glitch (`S06` & `S10`):**
    *(Melts pixels along optical-flow vectors without corrupting MP4 headers!)*
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect datamosh_optical \
      --params-json '{"mosh_times":[1.2, 3.8],"mosh_dur_s":1.1,"block_glitches":14}' --out out.mp4
    ```

---

### C. Camera Physics, Rhythm Pocketing & Zero-Footage Art (`S02/S04`, `S07`, `S08`, `S09`, `S10`, `S11`)

12. **Fight Club Face-Locked Camera Shake (`S11` `@ediday.5`):**
    *(Tracks nose/eyes and locks the face dead-still at center while violently shaking + motion-blurring the room + 35mm grain!)*
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect fight_club_shake \
      --params-json '{"shake_px":28,"rot_deg":2.0,"zoom":1.18}' \
      --windows-json '[[0.0, 2.2]]' --out out.mp4
    ```

13. **Bass Radial Shockwave (`S09` `@willrvail`):**
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect bass_shockwave \
      --params-json '{"beat_times":[0.5, 2.4, 4.8],"wave_dur_s":0.42,"strength_px":30}' --out out.mp4
    ```

14. **B&W Tension -> Full-Color Beat Explosion (`S10` `@astroospace`):**
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py vfx in.mp4 --effect center_match_strobe \
      --params-json '{"drop_s":1.8}' --out out.mp4
    ```

15. **Jigsaw Musical Pocket Finder + `18pt` Center Serif Subtitles (`S02 + S04` `@thisiszohair` Rule):**
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py music-pockets song.mp3 --min-gap 0.50
    ```
    *Golden Rule:* Never drop dialogue ON TOP of loud song hooks; place short character lines inside the returned `pockets` so speech nods to the beat, and pair with `om_hybrid.write_center_serif_ass(...)`.

16. **Zero-Footage Still Drawing / Poster Motion Edit (`S08` `kevamarts`):**
    ```bash
    python3 /home/user/studio/om_hybrid/cli.py still-art artwork.jpg \
      --title-top "GOD'S" --title-main "WISDOM" --dur 15.4 --layout 9:16_center_16:9 --out edit.mp4
    ```

17. **`@technocraftss` Difference-Typography + Optical-Flow Velocity Edit (`S07`):**
    - Python: `om_hybrid.render_ironman_style_edit(spec, out_mp4)` (supports `"layout": "9:16_center_16:9"`, `HDemucs` pure neural vocal isolation, and `125 BPM` clean Butterworth dark synthwave).
    - Cloud: `python3 /home/user/studio/gh_farm.py run --mode ironman_edit --job job.json --out-dir /tmp/out`

---

## 3. Running Chained Multi-Effect Edits on the 16 GB / 4 vCPU GitHub Cloud Farm (`--mode vfx_edit`)

When combining multiple heavy effects on 1080p footage, dispatch a `chain` job to the unlimited public `thecattrex/maker-studio` runner:

```json
{
  "out_name": "chained_viral_edit.mp4",
  "src_url": "https://.../clip.mp4",
  "broll_url": "https://.../broll.mp4",
  "chain": [
    {"effect": "text_behind_subject", "params": {"text": "WAKE UP", "color_hex": "#F4A236"}, "windows": [[0.0, 2.0]]},
    {"effect": "red_ribbon_roto", "params": {"katana_flash_times": [3.5]}, "windows": [[2.0, 5.5]]},
    {"effect": "fight_club_shake", "params": {"shake_px": 26}, "windows": [[5.5, 7.5]]},
    {"effect": "blob_tracking", "params": {"small": 22}}
  ]
}
```
```bash
python3 /home/user/studio/gh_farm.py run --mode vfx_edit --job job.json --out-dir /tmp/vfx_out
```

---

## 4. Core Editing Laws Distilled from All 11 Sample Videos

1. **Contrast Creates Impact:** Pair silence (`0.4s` blackout) right before a bass drop (`S07`), or `B&W` desaturation right before a color burst (`S10`), or `1.2s` emotional dialogue holds right before a `3-frame` (`0.10s`) machine-gun action burst (`S02`).
2. **Isolate Dialogue Cleanly (`HDemucs`):** Whenever pulling voice lines from movie trailers (`S01`, `S03`, `S07`), strip background trailer theme music via `ironman_edit.isolate_clean_vocal_slice` (`HDEMUCS_HIGH_MUSDB_PLUS`) so unrelated themes or end stings never bleed into your beat.
3. **Insert a Breather After Fast Cuts (`S09` Rule):** After `8–12s` of rapid cuts, give the viewer a `3–4s` optical-flow slow-mo breather shot punctuated by `1–2f` micro-flashes so their eyes rest without losing retention.
4. **Use Z-Depth (`PersonSegmenter`):** Putting text or a crimson B-roll ribbon *behind* the human subject (`S01`, `S05`) immediately makes a Python-rendered video look like a manual 3-hour After Effects rotoscope project.
