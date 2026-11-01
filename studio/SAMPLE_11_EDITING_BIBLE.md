# SAMPLE 11 — MASTER VIRAL EDITING BIBLE (`maker-studio`)

Complete frame-by-frame (`33 ms`), audio-sync, typography, and VFX reverse-engineering of all **11 reference & breakdown videos** from the `Sample` collection — documenting both **what each video communicates (`Story / Message`)** and **exact technical execution (`How It Is Edited & How Our Studio Reproduces It`)**.

---

## Summary Matrix of All 11 Videos

| # | File Prefix | Creator / Style | Specs | Core Category | Signature Mechanic |
|---|---|---|---|---|---|
| **S01** | `1a5bf441...mp4` | `@sumanth.mp4` (*Jujutsu Kaisen — Sukuna*) | `720x406` (`16:9`), `30fps`, `28.9s` | Anime/Live-Action Roto + Typography | Dual-font Red/White stacked slam (`PUPPET / FOOLISH`) + `-32°` Red B-Roll Ribbon sandwiched behind rotoscoped silhouette over B&W sky + `1-2f` katana luma-invert flash |
| **S02** | `65460EFC...mov` | `@thisiszohair` (*Spider-Man "Loser"* Sony-viral edit) | `1080x1920` (`9:16` w/ centered `16:9`), `30fps`, `32.3s`, **89 cuts** | Blockbuster Story Rhythm Edit | **"Jigsaw Musical Gap-Filling"** (dialogue slotted into song silence pockets) + `3f` (`0.10s`) snare-roll machine-gun cuts + tiny centered `18pt` serif subtitles |
| **S03** | `7841808f...mp4` | `@_.raajjjjjj_` (*Oppenheimer × Bhagavad Gita*) | `720x544` (`4:3`), `30fps`, `50.9s`, `Vessel - Red Sex` | Brutalist Dither / Risograph / CRT Essay | Indigo 2-tone posterized halftone + 1-bit Bayer dither silhouette (`VISHNU`) + Risograph scripture panels + curved CRT barrel distortion + giant crimson brutalist `DEATH / WORLDS` slam |
| **S04** | `7f2aba0c...mp4` | `@thisiszohair` (Premiere Pro Breakdown of **S02**) | `720x1280` (`9:16`), `29.98fps`, `81.8s`, **49 cuts** | Talking-Head + Timeline Tutorial | Split-screen live Premiere timeline + animated white pointer arrows + rule: *edit around the music, fill applause/instrumental gaps with story dialogue without fighting the beat* |
| **S05** | `7f73e363...mp4` | `@cashworthclipz` (*"The Edit Is Done"* -> Hawaii Surf) | `720x1280` (`9:16`), `30fps`, `41.4s` | Monitor Reveal -> Kinetic Lifestyle Edit | 3D Z-depth text behind roto subject (`HAWAII`) + `3x3` bento grid + mixed italic-serif vs giant video-textured impact text + `3` freeze-frame roto clones on `#000000` + planar wave-tracked text |
| **S06** | `8f7025e1...mp4` | `@marcelgrauu` (*7 Trending VFX Shaders*) | `720x1280` (`9:16`), `25.75fps`, `14.1s` | Experimental Shader / Texture Catalog | 1) `Datamosh`, 2) `Blob Tracking` (OpenCV boxes + web lines), 3) `Flash Light` luma glow, 4) `Receipt Ticket` thermal dither, 5) `CRT` cyan phosphor, 6) `1-Bit Dither`, 7) `Pink Phosphor` + spatial stacked CTA text |
| **S07** | `8fb5d1e4...mp4` | `@technocraftss` (*Iron Man — "Paper in My Pocket"*) | `720x406` (`16:9`), `26.02fps`, `20.37s` | Difference-Typography + Velocity Edit | Giant `#FFFFFF` bold sans in **`Blending Mode: DIFFERENCE` (`|255 - BaseRGB|`)** + `5f` `#000000` strobe cuts + 2-line left slam -> `0.45s` half-beat `3x -> 0.35x` optical-flow velocity montage |
| **S08** | `F0E2B6A9...mov` | `kevamarts` (*"God's Wisdom"* Hindu Artwork Edit) | `1080x1920` (`9:16` w/ centered `16:9`), `30fps`, `15.4s` | Still-Illustration Motion Edit | `1f` Red/Black -> Red/White polarity flip title + continuous `wiggle(6,18)` shake on a single drawing + radial light sweep + `125%` zoomed-invert glitch bars + center red-duotone box swap |
| **S09** | `a4b9dd5d...mp4` | `@willrvail` (*12 Music-Video VFX Breakdown*) | `720x1280` (`9:16`), `24.35fps`, `71.0s` | Live Reaction + Checklist Breakdown | Persistent 12-item HUD checklist + 1) Masking hook w/ red/white flashes, 2) Foreground frame-wipe, 3) Multi-layer + bass shockwave, 4) Roto clones, 5) **Double-exposure silhouette overlay**, 6) Breather slow-mo w/ flashes, 7) Negative invert |
| **S10** | `aa23f6bb...mp4` | `@astroospace` (*Blawan — Close the Cycle* Space Edit) | `720x406` (`16:9`), `30fps`, `26.57s`, **69 center cuts** | Hypnotic Center-Locked Match-Cut Strobe | Radial `(cx, cy)` geometric match-cuts (`2f` `0.067s` strobe bursts) + **B&W pre-beat tension -> full-color explosion on bass hit** + square macroblock datamosh glitches |
| **S11** | `d679b486...mp4` | `@ediday.5` (*Fight Club* Face-Locked Shake Tutorial) | `720x540` (`4:3`), `25.04fps`, `23.2s`, **24 cuts** | Split Brutalist Hook + Stabilized-Shake Tutorial | 2-panel top/bottom split w/ edge-framed Red/White condensed text (`FIGHT CLUB / SHAKE EFFECT`) + **Point-Track nose/eyes -> Match-Move (`BG Only`)** so face stays locked dead-center while background violently motion-blurs + heavy 35mm grain |

---

## Detailed Per-Video Breakdown (`Story` + `Exact Editing Mechanics`)

### S01 — `@sumanth.mp4` (*Sukuna "Malevolent Shrine" Dark Roto + Red-Ribbon Edit*)
- **What It Says:** Uses Ryomen Sukuna's menacing *Jujutsu Kaisen* lines (*"I'm gonna kill you for that... Don't forget your place, foolish puppet. Domain Expansion: Malevolent Shrine"*) to build dread from pitch darkness into an overwhelming supernatural slash climax.
- **Exact Editing Mechanics:**
  1. **Act 1 (`0–11.4s`):** Pitch-black `#000000` canvas where tall narrow crimson (`#CC0814`) condensed text emerges from darkness, then switches to **2-layer contrasting typography**: giant red background word (`PUPPET`, `SHRINE`) with smaller crisp white foreground word (`FOOLISH`, `MALEVOLENT`) slammed dead-center over it.
  2. **Bridge (`4 frames`):** Luma-inverted stencil cut.
  3. **Act 2 (`11.5–24.5s`):** **3-Layer Composite Sandwich:**
     - *Bottom Layer:* Desaturated B&W moody sky/rooftop.
     - *Middle Layer:* Diagonal (`-32°`) or horizontal razor-edged **Crimson-Tinted B-Roll Ribbon** playing rapid anime combat clips inside the red strip.
     - *Top Layer:* **Rotoscoped dark silhouette** of the character standing *in front* of the red ribbon!
  4. **Impact Accent (`22.1s`):** `1–2 frame` pure `#FFFFFF` white katana flash -> `8–12 frames` **full luma negative invert** (`255 - Y`), closing on concentric dark shrine portal rectangles.

### S02 + S04 — `@thisiszohair` (*Viral Sony Spider-Man "Loser" Edit* + *81.8s Premiere Pro Breakdown*)
- **What S02 Says:** Tells Peter Parker & MJ's tragic memory-wipe story (*"Hi, my name is Peter Parker" -> "I'm MJ" -> "I'm gonna come and find you" -> "We used to know each other"*) woven into high-adrenaline *Spider-Man* action over a fast upbeat clap-driven track.
- **What S04 Teaches (Creator's Exact Rules):**
  1. **Edit Around the Music ("Jigsaw Puzzle Rule"):** Fast song = quick dialogue. Never place dialogue *over* heavy vocals or drown out the groove; find **empty instrumental/applause gaps** in the track and drop short dialogue hooks (`"I'm gonna come and find you"`) precisely into those pockets so speech *nods* to the beat and builds a story hook.
  2. **Layout & Micro-Typography (`S02`):** `1080x1920` (`9:16`) black canvas with centered `16:9` strip (`y=656..1264`), tiny minimal `18pt` white serif subtitles dead-center of the frame (zero eye travel during fast cuts!), and subtle top-right countdown timer.
  3. **Pacing Contrast (`89 cuts in 27.5s`):** Alternates `1.2s` emotional dialogue holds with **`3-frame` (`0.10s` = 10 cuts/sec) machine-gun action match-cuts** (`9.90s–11.07s`) synced to drum/clap rolls, using motion-direction continuity (swing left-to-right -> flip left-to-right -> punch impact).
  4. **Breakdown Editing Style (`S04` itself):** Top/bottom split showing face-cam + live zoomed Premiere timeline, curved animated white pointer arrows (`draw-on` stroke), and clean serif word-by-word captions.

### S03 — `@_.raajjjjjj_` (*Oppenheimer × Bhagavad Gita Brutalist Dither/CRT Edit*)
- **What It Says:** J. Robert Oppenheimer's haunting Trinity nuclear test reflection (*"Few people laughed, few people cried, most people were silent. I remember the line from the Hindu scripture, the Bhagavad Gita... Now I am become Death, the destroyer of worlds"*) set to dark industrial ambient (`Vessel - Red Sex`).
- **Exact Editing Mechanics:**
  1. **Cold Minimalist Strobe (`0–11s`):** Deep `#000000` void with stark ultramarine-blue (`#1028FF`) condensed Impact phrases flashing briefly and disappearing back into multi-second silence/blackness (`969` black frames total = deliberate dread!).
  2. **2-Tone Risograph / Blueprint Posterization (`13–30s`):** Footage & classical Kurukshetra chariot illustrations quantized into **2–3 Indigo/Periwinkle tones (`#1A2168` + `#CED8F7`)** with fine horizontal scanline/paper grain and editorial crimson serif header/footer banners (`LINE, FROM THE` / `BHAGWAT GITA`).
  3. **1-Bit Ordered Bayer Dither (`21.2s`):** Hard monochrome pixel-matrix stipple silhouette of Lord Vishnu with contrasting gold (`#D9C53B`) text inside the dark chest void.
  4. **CRT Television Lens (`33.9s`):** Rounded vignette + barrel lens distortion (`cv2.remap` `r' = r * (1 + k*r^2)`) framing multi-armed Vishvarupa.
  5. **Brutalist Climax Typography (`38–43s`):** Massive full-width blood-red (`#C90A14`) condensed block type (`DEATH`, `WORLDS`) filling 80% of the screen height with micro-justified small caps (`NOW   I BECAME`, `THE   DESTROYER   OF`) stretched flush across the top edge.

### S05 — `@cashworthclipz` (*"The Edit Is Done" Monitor Reveal -> Hawaii Surf Lifestyle Edit*)
- **What It Says:** Opens with creator's genuine excitement (*"The edit is done, check this out!"*), pans to his PC monitor, and plays a euphoric summer philosophy edit (*"Life moves pretty fast. If you don't stop and look around once in a while, you could miss it — come on, wake up!"*).
- **Exact Editing Mechanics:**
  1. **Meta Framing Hook (`0–7.5s`):** Front-cam reaction -> whip-pan to NLE timeline -> animated rotating phone icon -> monitor playback (turns a `16:9` edit into an authentic `9:16` story!).
  2. **Z-Depth Roto Typography (`8.2–9.5s`, `15.7s`, `25.5s`):** `HAWAII` in giant sunset-gold Impact placed *behind* the rotoscoped silhouette; `AROUND` textured with red video fill behind friends; `THEY CAN SMELL THE LEGACY` 3D-skewed and planar-tracked onto the moving ocean wave behind the surfer's spray.
  3. **Dynamic Aspect-Ratio & Grid Shifts:** Full `16:9` -> **`3x3` 9-tile Bento Grid** popping in on beats (`11.99s`) -> **shrinking center `4:5` postcard frame** over black (`15.78s`, `19.57s`) -> full `16:9` wave drop.
  4. **Freeze-Frame Roto Clone Trail (`20.83s`):** 3 sequential rotoscoped cutouts of the surfer's mid-air flip isolated on pure `#000000` black popping left-to-right (`1-2-3`) on consecutive beats!

### S06 — `@marcelgrauu` (*7 Trending Experimental VFX Filters + Spatial Hook Typography*)
- **What It Says:** Rapidly showcases 7 high-demand modern visual effects (`Datamosh`, `Blob Tracking`, `Flash Light`, `Receipt Ticket`, `CRT`, `1-Bit Dither`, `Pink Phosphor`) with an engagement CTA (*"Comment your favorite one and I'll send them to you"*).
- **Exact Editing Mechanics (7 Buildable OpenCV/Shader Filters):**
  1. **Datamosh:** Motion-vector macroblock smear across cut boundary without refreshing keyframe texture.
  2. **Blob Tracking (`OpenCV`):** Threshold bright moving keypoints -> draw crisp `1px` white rectangles + tiny coordinate/ID labels + thin connecting web lines (`cv2.line`) between tracked nodes!
  3. **Flash Light Silhouette:** Luma-thresholded glowing white human cutout with soft bloom in darkness.
  4. **Receipt Ticket:** Desaturate + high-contrast Floyd-Steinberg/Atkinson dither + multiply onto crinkled white thermal receipt paper texture with monospace receipt header/price text!
  5. **CRT Cyan Phosphor:** Quantize + cyan tint (`#00E5FF`) + RGB aperture-grille scanlines + halation bloom.
  6. **1-Bit Dither:** Pure `#000000`/`#FFFFFF` Bayer `4x4`/`8x8` ordered dithering matrix on statues/portraits.
  7. **Pink Phosphor:** Hot-magenta (`#FF18C8`) night-vision halftone + horizontal sync glitch.
  8. **Floating Pop-In Collage & Spatial Text:** Example cards pop around the speaker with subtle drop-shadows while clean Helvetica words (`your / FAVOURITE / one`) stack asymmetrically above his cap.

### S07 — `@technocraftss` (*Iron Man "Paper in My Pocket" — Already Built in `om_hybrid/ironman_edit.py`!*)
- **What It Says:** Swagger-heavy Tony Stark / Iron Man suit-up edit (*"Paper, paper, paper in my pocket... I need that fuel inside my rocket... Jarvis, drop my needle"* -> heavy bass drop).
- **Exact Editing Mechanics:** Giant `#FFFFFF` `ArchivoBlack` lyrics in **`Blending Mode: DIFFERENCE` (`|255 - BaseRGB|`)** auto-inverting warm background to blue and blue arc-reactor to fiery orange + `5f` `#000000` black strobe cuts + 2-line left-aligned pre-drop slam + Act 2 `0.45s` half-beat `2.8x -> 0.38x` Farneback optical-flow velocity speed-ramp montage.

### S08 — `kevamarts` (*"God's Wisdom" Single-Illustration Motion Edit*)
- **What It Says:** Pure instrumental beat edit turning a **single static black-ink sketchbook drawing** of a multi-armed deity into a high-energy 15.4s edit titled *"GOD'S WISDOM"*.
- **Exact Editing Mechanics (Zero Video Footage Needed!):**
  1. **`1-Frame` Polarity-Swap Grunge Title (`0–3.8s`):** Dark vignette drawing + crimson `#E50914` `GOD'S / WISDOM` -> `1-frame` hard cut to solid `#E50914` red background + textured `#FFFFFF` grunge `WISDOM` with continuous handheld `wiggle(6, 18)`.
  2. **Bringing a Still Drawing to Life (`3.8–15.4s`):** Continuous camera shake + slow push-in + rotating radial white glow behind the crown + `125%`-zoomed horizontal inverted glitch slice bars (`4–6f`) + `1.0s` center box swap (center rectangle flips to Crimson+Black duotone while outer wings invert luma!).

### S09 — `@willrvail` (*12-Effect Music Video VFX Breakdown*)
- **What It Says:** Breaks down a nature/rap visual edit in real time, naming 12 pro transition & layering techniques so the viewer never gets bored.
- **Exact Editing Mechanics (12-Technique Vocabulary + Reaction Layout):**
  1. **Masking Hook + Red/White Flashes:** Rapid `1–2f` red (`#FF1010`) and white (`#FFFFFF`) strobe frames behind a rotoscoped subject in the first `2.5s`.
  2. **Foreground Wipe Transition:** Pass a dark foreground object/silhouette across `0% -> 100%` of the frame width (`alpha matte wipe`) to seamlessly reveal a wide-angle shot.
  3. **Depth Layering + Bass Shockwave:** Stack foreground roto + midground fog + background mountain, firing a radial displacement ripple (`shockwave`) on the 808 hit.
  4. **Beat-Pop Roto Clones:** Offset 2–3 rotoscoped copies of the subject left/right by `+-140px` popping in `1–2–3` on consecutive snare hits.
  5. **Double-Exposure Inverted Silhouette (`22–28s`):** High-contrast black subject silhouette against pure white sky where **fast-changing B-roll clips play ONLY inside the black silhouette matte** (`out = bg_white * (1 - mask) + broll * mask`)!
  6. **Pacing Breather Rule (`39–45s`):** After intense fast cuts, insert a `4s` optical-flow slow-mo shot to let the viewer breathe, punctuated by `1f` micro-flashes so retention stays locked.

### S10 — `@astroospace` (*Blawan "Close the Cycle" Hypnotic Cosmic Match-Cut Edit*)
- **What It Says:** Zero spoken words — tells the birth, collapse, and rebirth of the cosmos ("Close the Cycle") purely through **visual geometry + industrial techno percussion**.
- **Exact Editing Mechanics:**
  1. **Center-Point `(cx, cy)` Geometric Match-Cutting:** Every single shot's focal circle/core (planet, black hole ring, pulsar beam, nebula core) is registered to the exact center pixel `(w/2, h/2)`. Even at **15 cuts/sec (`2-frame` strobes)**, the viewer's eye stays effortlessly locked!
  2. **Desaturated Tension -> Color Drop (`B&W -> Full Saturation`):** Enters a new cosmic structure in stark monochrome B&W (`sat = 0`), builds tension for `0.8s`, and snaps instantly to **140% vibrant color + glow bloom** on the downbeat (`12.25s->13.06s`, `14.67s->15.47s`, `18.69s->19.50s`).
  3. **Macroblock Datamosh Ticks (`6.6s`, `8.2s`, `9.8s`):** Displaces `16x16` / `32x32` square patches & pixel-stretched rows/columns for `2–4 frames` on glitch percussion hits.

### S11 — `@ediday.5` (*Fight Club Face-Locked Camera Shake + Split Brutalist Hook*)
- **What It Says:** Teaches how to create the iconic *Fight Club* disorienting psychological camera-shake effect in 19 seconds.
- **Exact Editing Mechanics:**
  1. **2-Panel Brutalist Split Hook (`0–3s`):** Top half = B&W creator clip; Bottom half = warm gritty *Fight Club* film clip. Tall condensed `#FF0000` + `#FFFFFF` title words (`FIGHT`, `CLUB`, `SHAKE`, `EFFECT`) are pinned flush to the **far-left and far-right margins**, framing both faces cleanly in the center column!
  2. **Face-Locked Stabilized Shake ("Fight Club Shake"):**
     - Apply aggressive horizontal/rotational camera shake + directional motion blur (`dx = A * sin(...)`, `cv2.filter2D` motion kernel) OR film handheld shake, then **lock the subject's nose/eyes `(face_cx, face_cy)` rigidly to `(w/2, h/2)`** every single frame!
     - Because the face is pinned stationary (`0 px` drift) while perspective, lighting, and the entire room violently smear left-and-right around their head, it creates an uncanny, visceral cinema-thriller intensity — finished with heavy 35mm film grain & halation!

---

## How `maker-studio` Applies These 11 Blueprints Going Forward

1. **Movie / Character Hype Edits:** Combine **S07** (`Difference` typography + optical-flow velocity, already live in `om_hybrid/ironman_edit.py`), **S01** (`-32°` crimson B-roll ribbon behind rotoscoped silhouette + luma-invert flash), **S11** (MediaPipe face-locked *Fight Club* shake), and **S02/S04** (`9:16` centered `16:9` + musical-pocket dialogue weaving + `3f` drum-roll match-cut bursts + tiny `18pt` centered serif subs).
2. **Dark Philosophy / History / Science / Mystery Edits (Type 3 & Standalone):** Combine **S03** (2-tone Indigo Risograph posterization + 1-bit Bayer dither + CRT barrel lens + giant crimson brutalist type), **S06** (`Blob Tracking` OpenCV HUD web + `Receipt Ticket` + `CRT` / `Pink Phosphor` shaders), and **S10** (`(cx, cy)` geometric match-cuts + `B&W -> Color` beat drops).
3. **Creator / Breakdown / Lifestyle Edits:** Combine **S04 + S09** (split timeline/reaction HUD + live numbered checklist + animated pointer arrows) and **S05** (`Z-depth` text behind roto subject + `3x3` bento grid + `3` freeze-frame roto clones on black).
4. **Zero-Footage / Artwork / Manga / Comic Edits:** Use **S08** (`1f` polarity-swap grunge title + continuous `wiggle` + radial light sweep + `125%` zoomed-invert glitch bars + duotone center box swap).
