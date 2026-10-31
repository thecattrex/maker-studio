# HyperFrames Cloud Engine & Registry Playbook (`studio/hyperframes/`)

## Why HyperFrames Runs on Our GitHub Cloud Farm (and What Runs Locally)
- **GitHub Cloud Farm (`--mode hyperframes`, Node 22 + 7.75 GB RAM):**
  - `@hyperframes/cli` (`>=0.8.x`) requires **`Node.js >= 22`** and headless Chrome `BeginFrame` capture (Arena sandbox runs `Node 20` with `1.94 GB RAM`).
  - Use `--mode hyperframes` for HTML + CSS + GSAP explainers, kinetic typography, data charts, and any of the **448 registry blocks & components**.
- **Local Arena + Cloud (`om_hybrid` Python):**
  - **Cinema 3D `.cube` LUT Color Grading** (`om_hybrid/cinema_looks.py` -> `teal-orange-blockbuster`, `bleach-bypass`, `film-fade`, `warm-cinema`, `crisp-editorial`, `scifi-cool`) runs **locally in <5ms** with zero RAM overhead via FFmpeg `lut3d`.
  - **Velocity-Matched Seam Cuts** (`om_hybrid/smart_camera.py` -> `seam_mode="dip" | "zoom_through" | "whip_pan" | "rack_focus"`) run **both locally and on GitHub Cloud**.

---

## Deterministic HTML + GSAP Contract
1. Root element: `<div id="root" data-composition-id="main" data-start="0" data-duration="<sec>" data-width="1080" data-height="1920">`.
2. Every timed element inside `#root` carries `class="clip" data-start="0" data-duration="<sec>" data-track-index="0"`.
3. Build ONE paused GSAP timeline and register it:
   ```js
   window.__timelines = window.__timelines || {};
   const tl = gsap.timeline({ paused: true });
   // tweens using transforms/opacity only (no Date.now(), no Math.random(), no timers)
   window.__timelines["main"] = tl;
   tl.seek(0);
   ```
4. Always paint `#root` with an explicit opaque background (`#root { background: var(--ground); }`) so seam transitions never flash white.

---

## High-Value Registry Components (`npx hyperframes add <slug>`)
- **Viral Captions:** `caption-pill-karaoke`, `caption-kinetic-slam`, `caption-editorial-emphasis`, `caption-highlight`, `caption-neon-accent`, `caption-gradient-fill`, `caption-weight-shift`, `caption-camera-follow`
- **Transitions & Camera:** `whip-pan-cut`, `before-after-wipe`, `chromatic-aberration-wipe`, `camera-dolly-zoom`, `camera-shake`, `beat-freeze-cut`
- **Explainer & Data Blocks:** `bar-chart-race`, `apple-money-count`, `ai-answer-rank`, `animated-bar-chart`, `chart-story`, `code-terminal-run`, `camcorder-hud`

---

## Creative Laws (Distilled from HyperFrames Skills)
1. **Rail-First, Embed-Scarce (`captions-overlay`):** Keep verbatim spoken words on a clean lower-third **Rail**; promote at most **1 peak word per beat** to a large **Embed** behind the subject.
2. **Cut-the-Curve (`cut-the-curve`):** Cut at peak velocity and match Z scale sign across the cut (`1.0 -> 1.18` exit paired with `0.85 -> 1.0` arrival — never flip push to pull).
3. **Numbers Over Adjectives (`spec.md`):** Hero fills >=40% of frame; one hero move per shot; readable text >=28px held `0.5s + 0.3s/word`; new visual beat every `2–4s`.

---

## Cloud Dispatch Usage
```bash
# Default portrait starter test:
python3 /home/user/studio/gh_farm.py run --mode hyperframes --out-dir /tmp/hf_out

# Custom HTML composition + registry components:
python3 /home/user/studio/gh_farm.py run --mode hyperframes --job my_hf_job.json --out-dir /tmp/hf_out
```
Where `my_hf_job.json` supports:
```json
{
  "out_name": "explainer_ep1.mp4",
  "resolution": "portrait",
  "quality": "delivery",
  "fps": 30,
  "registry_items": ["caption-pill-karaoke"],
  "project_dir": "studio/hyperframes/starter_short",
  "index_html": "optional inline HTML override..."
}
```
