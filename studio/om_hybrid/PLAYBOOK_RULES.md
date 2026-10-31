# Hybrid Short-Form & Clip-Factory Rules (`studio` + `OpenMontage`)

Distilled from OpenMontage (`skills/creative/short-form.md`, `skills/pipelines/clip-factory/*`, `lib/slideshow_risk.py`) and aligned with `studio/SPEC.md` + `studio/FORMAT_MEMORY.md`.

## 1. Universal Safe Zones (`1080x1920`)
- Universal cross-platform safe zone (Shorts + Reels + TikTok): **`900x1400` centered** (avoid bottom `300-320px` and right `96-120px` for critical text).
- Type-1 canonical frame: **`1080x1200` (9:10) central video band (`y=360..1560`)** between `360px` solid black bands.
- Dialogue captions sit at **`y=1405` (`\an2`)** inside the lower video band — comfortably above the `y=1560` border and well above platform bottom UI dead zones (`y > 1600`), while staying below speaker faces (`y_face_bottom <= 0.74`).

## 2. The 0.0–3.0s Hook / Punchline-First Rule (Type 1)
- **70%+ of viewers decide to scroll or stay within 1.7–3.0 seconds.**
- Always open Type-1 movie Shorts at **`0.0s`** with a **2.5–3.8s Cold-Open Peak / Punchline** from the climax of the scene (fully word-captioned + impact pop), followed by a crisp **4-frame cinema dip-to-black** and click-free audio fade into the **full continuous uncut scene**.
- **Standalone Clarity Check (`clip-factory`):** Reject hooks/clips that begin with dangling connectors (*"and"*, *"because"*, *"which"*) or end before the reaction/payoff lands.

## 3. Camera Motion & Active-Speaker Framing (`om_hybrid.smart_camera`)
- Never smooth `focus_x` across a hard camera cut — segment shots first (`detect_shots`), then apply smooth sub-pixel `cv2.warpAffine(..., INTER_LANCZOS4)` push-in (`1.00 -> 1.06x`) and damped tracking within each shot at native source FPS (`23.976` / `24` / `30`).
- **Two-Shot Rule:** When two faces fit within 88% of `crop_w`, center their group midpoint so neither speaker is clipped at the frame edge.
- **Caption Collision Guard:** Verify via `visual_qa.run_full_qa` that face bounding boxes do not collide with the caption band (`y=1300..1460`).

## 4. Audio & Loudness Spec (`om_hybrid.pacing_audio` + `visual_qa`)
- **Type 1:** Pure original movie dialogue only (`BGM = None`, zero synthetic boom/whoosh SFX).
- **Type 2:** Selected C2 track (`c2_48.wav`) @ ~17%, natural fail audio, impact SFX, recurring `"I got this"` transitions, chicken interstitial before `#1`.
- **Type 3:** Hindi TTS narration + ducked scene audio (`0.50`), Roman Hinglish active-word yellow captions, no scale-pop, no BGM.
- **Mastering Target:** **`-16 to -14 LUFS`** integrated, **`<= -1.5 dBFS` True Peak** (`alimiter=limit=0.81:level=false` — always set `level=false` so FFmpeg does not re-boost peaks to `0 dBFS`!).

## 5. Anti-Slideshow Check for Type-3 Explainers (`om_hybrid.score_slideshow_risk`)
- Run `score_slideshow_risk(scenes)` on multi-scene plans; keep average `< 2.5` (`strong` / `acceptable`) by varying shot scale, giving every shot explicit narrative intent, and sourcing real motion clips via `om_hybrid.clip_scout` (`archive_org`, `wikimedia`, `nasa`, `dareful`, `coverr`, `mixkit`, etc.) instead of static text slides.
