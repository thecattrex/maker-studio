# Skill Plan — Krishna Updesh — Print Reveal (dialogue-led)

**Brief:** Sample F0E2B6A9 jaisa print/sketchbook reveal format, Krishna Bhagwan par, Hindi me. Audio me pehle alag intro BGM, phir Krishna ka dialogue jo samjhate hue bol rahe hain — goosebumps vibe. Bhajan nahi.

**Must have:** separate intro BGM (first 2-3s), Krishna Hindi dialogue as hero, music ducked -16 to -20 dB under dialogue, goosebump swell + flash on key line, Devanagari print typography, 1080x1920 15-20s

**Type:** `deity_no_footage, dialogue_led`  
**Flags:** `dialogue`, `song_only`, `zero_footage`, `hindi`, `reference_sample`, `short`

**Registry:** 49 skills curated (49 verified) out of 289 python modules scanned


## Stages (in order)


### `source`
available (pick by need):
- `clipsel.scan` [ok] — Candidate clips ko score karke fail/weak wale hataata hai
- `om_hybrid.clip_scout` [ok] — Trailer/1080p source fetch
- `srcget` [ok] — Multi-source stock/archive fetch
- `stock_sources` [ok] — 24 stock/archive adapters (pexels, archive.org, nasa, loc...)

### `listen`
**MUST USE**
- `asr.listen` [OK] — Dialogue ko TEXT me sunna (Groq whisper-large-v3, word timings)
- `real_sfx.masking` [OK] — Kya dialogue music ke neeche dab raha hai (masked cues)
- `earshot.critique` [OK] — Mix ko grade karta hai + actionable fixes deta hai
available (pick by need):
- `earshot.measure` [ok] — LUFS/TP/bands/onsets/tonal — audio ka objective naksha
- `earshot.describe` [ok] — Audio me kya hai (speech/music/hits) — bina sunne maan lene se bachao
- `earshot.realness` [ok] — Kya ye 'real produced music' lagta hai ya synth/canned
- `earshot.timeline` [ok] — Audio events vs video cuts ka sync map (cut_sync gate)
- `earshot.compare` [ok] — Reference sample vs apna mix — A/B distance
- `asr.faster_whisper` [ok] — Offline ASR (faster-whisper) — intelligibility + gibberish detect
- `real_sfx.listen_yamnet` [ok] — YAMNet se sound tags + voice command detection
- `real_sfx.refstyle` [ok] — Reference edit ka audio style napna
- `real_sfx.unbake` [ok] — Reference ke layers (voice/bed/sfx) alag karke levels nikalna

### `structure`
available (pick by need):
- `analyze.video_timeline` [ok] — Source ka scene/shots/audio-energy/speech timeline nikalta hai
- `pacing_audio.hook_candidates` [ok] — Kaunsa moment hook ban sakta hai, energy+silenсes se rank
- `templates.beat_grid` [ok] — Beat grid + snap to frames
- `templates.find_peak_scene` [ok] — Peak/climax scene dhoondhta hai

### `visuals`
**MUST USE**
- `viral_vfx.still_art` [OK] — 1 static art -> 15-20s beat-synced edit (kevamarts style)
- `printrev.page_system` [OK] — Sketchbook page / card reveal format (F0E2B6A9 sample)
available (pick by need):
- `cashworth.9piece` [ok] — @cashworthclipz 9-piece aesthetic engine
- `zohair.jigsaw` [ok] — @thisiszohair vocal-pocket rhythm edit
- `aura.viral` [ok] — Scene->drop Style 2 engine + 4K CC look
- `ironman.difference` [ok] — Difference-typography hype edit
- `viral_vfx.pipeline` [ok] — 17-effect VFX arsenal (riso/dither/crt/shockwave/roto)
- `skills.blob_tracking` [ok] — Object/blob track -> HUD labels

### `type`
available (pick by need):
- `textkit.ass` [ok] — Styled ASS subtitles burn-in
- `viral_vfx.center_serif` [ok] — Center serif subs (Style 1 look)
- `printrev.rough_type` [ok] — Rubber-stamp ink text (Devanagari-safe, chipped edges)

### `motion`
available (pick by need):
- `smart_camera` [ok] — Shot-wise subpixel camera moves / reframe
- `motion_director` [ok] — Shot table ke hisaab se motion plan
- `ironman.optical_flow` [ok] — Optical-flow frame interpolation

### `grade`
available (pick by need):
- `cinema_looks` [ok] — Cube LUT based cinema looks
- `aura.4k_cc` [ok] — 5-layer 4K Quality CC (denoise->CLAHE->unsharp->blacks->vibrance)
- `cashworth.dream_grade` [ok] — Dreamy aesthetic grade

### `sfx`
available (pick by need):
- `sfx_sync` [ok] — Beat-synced SFX cues
- `sfx.build` [ok] — Whoosh/impact/riser/pop generation
- `real_sfx.mix` [ok] — SFX busses + masking-aware mix
- `openverse_realsfx` [ok] — Auto sound design (licensed assets)

### `audio_mix`
available (pick by need):
- `zohair.multitrack` [ok] — Dialogue pockets me song ko chhota karke weave karna
- `aura.muffle_under_scene` [ok] — Scene ke neeche -18.5dB LPF song, phir drop pe 0dB sweep
- `printrev.loudnorm` [ok] — 2-pass loudnorm + true-peak safe mux

### `qa`
available (pick by need):
- `visual_qa` [ok] — Frame-level visual QA
- `slideshow_risk` [ok] — Slideshow/dead-motion risk score
- `master_pipeline` [ok] — Neural-ears master polish pass
- `earshot.scorecard` [ok] — Audio scorecard (dialogue clarity, bed balance, sync)
- `real_sfx.levels` [ok] — Levels/group balance report

## GATES (pass hona zaroori)

- **G1_speech_understanding** — source audio ko ASR + earshot.describe se SUNO, graph se guess mat karo  
  tools: `asr.listen`, `earshot.describe`, `earshot.measure`
- **G2_dialogue_intelligible** — final mix pe ASR re-run: har line 90%+ words match honi chahiye  
  tools: `asr.listen`, `real_sfx.masking`
- **G3_bed_ducking** — dialogue ke neeche bed -14 se -20 dB; masking report clean  
  tools: `real_sfx.masking`, `earshot.critique`
- **G4_cut_sync** — cuts dialogue ke phrase pe, beat pe nahi  
  tools: `earshot.timeline`
- **G1_speech_understanding** — source audio ASR = speech hai ya music? (guess nahi, sun ke)  
  tools: `asr.listen`, `earshot.describe`
- **G5_real_music** — song real produced ho (realness), synth nahi  
  tools: `earshot.realness`
- **G4_cut_sync** — cuts beat grid pe, offset <= 1 frame  
  tools: `earshot.timeline`, `templates.beat_grid`
- **G6_reference_match** — reference sample se A/B compare + style match report  
  tools: `earshot.compare`, `real_sfx.refstyle`
- **G7_loudness** — I -14 LUFS, TP <= -1.5 dBTP  
  tools: `earshot.measure`, `printrev.loudnorm`
- **G8_visual_qa** — frame QA + slideshow risk  
  tools: `visual_qa`, `slideshow_risk`

## Anti-patterns (jo nahi karna)

- Audio ko sirf RMS/spectrum se 'samajh' lena — ASR/describe/critique se sunna zaroori.
- Reference sample ka audio transcribe kiye bina usko 'music-only' maan lena.
- Song ko dialogue wale video me full-volume chalana (dialogue dab jaata hai).
- Music Python se synthesize karna (real produced song hona chahiye).
- Beat grid ko audio ka 'content' samajh lena — wahi sirf tempo hai.
- Ek hi engine (jaise printrev) se sab kuch karna jab 40+ skills available hain.