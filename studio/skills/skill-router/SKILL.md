---
name: skill-router
description: Decide which of maker-studio's 49 curated skills (out of 289 python modules) must be used for a given video brief, in which stage, with hard verification GATES — then audit a finished file to prove which skills actually fired and which were skipped.
---

# Skill Router (`studio/skill_router.py`)

Maker-studio me 289 python modules, 58 engine files, `earshot` (audio ears),
`real_sfx` (sound design), `skills/viral-edits` (routing matrix) installed hain.
Bina router ke build karte waqt sirf 2-3 skills use hote hain aur baaki pada
reh jaata hai — usi se "style match, feel mismatch" wali galtiyan hoti hain.

Ye skill **kaunsi skill kab lagegi** decide karta hai, aur **ban chuki file pe
proof** deta hai.

## Commands

```bash
# 1) registry banao (filesystem ke against har skill verify hoti hai)
python3 studio/skill_router.py discover
#    -> studio/skills_registry.json   (49 skills, verified flags)

# 2) brief se plan nikalo
python3 studio/skill_router.py plan --brief studio/briefs/krishna_dialogue.json
#    -> studio/plans/<title>_plan.md  (stages + MUST USE + GATES + anti-patterns)

# 3) reference sample ka audio fingerprint (style target)
python3 studio/skill_router.py refprofile --video sample.mov --name f0e2b6a9_gods_wisdom

# 4) ban chuki file audit karo (ASR + earshot + motion + reference match)
python3 studio/skill_router.py audit --video out.mp4 \
        --brief studio/briefs/krishna_dialogue.json --ref f0e2b6a9_gods_wisdom
#    -> studio/plans/<file>_audit.md   (PASS / WARN / FAIL per gate)

# 5) tag/stage se skill dhoondo
python3 studio/skill_router.py skills --tag audio
python3 studio/skill_router.py skills --stage listen
```

## Stages (fixed order)

`source → listen → structure → visuals → type → motion → grade → sfx → audio_mix → qa`

`listen` stage hi wo tha jo pehle missing tha: audio ko **sirf naapna nahi,
sunna** — `asr.listen`, `earshot.describe/critique/realness/timeline`,
`real_sfx.masking`, `real_sfx.unbake`, `real_sfx.refstyle`.

## Gates (hard checks)

| Gate | Kya check karta hai | Tools |
|---|---|---|
| G1_speech_present | mix speech-led hai ya song-led (`harmonic_ratio` + `LRA`) | earshot.measure |
| G2_dialogue_decodable | ASR se dialogue actually samajh aata hai | asr.faster_whisper |
| G3_bed_ducking | dialogue ke neeche bed -14…-20 dB, masking report clean | real_sfx.masking |
| G4_cut_sync | cuts phrase pe hain, offset ≤ 1 frame | earshot.timeline |
| G5_real_music | music real produced hai, synth nahi | earshot.realness |
| G6_reference_match | reference sample ka audio fingerprint se distance | refprofile + compare |
| G7_loudness | I ≈ -14 LUFS, TP ≤ -1.5 dBTP | printrev.loudnorm |
| G8_visual_qa | static/black frame ratio, slideshow risk | visual_qa, slideshow_risk |
| G9_spec | 1080x1920@30, codecs, duration | ffprobe |

Verdict: **PASS** (sab pass) / **PARTIAL** (koi WARN) / **FAIL** (koi FAIL).

## Lesson jo ise banane ki wajah bani

Sample (`F0E2B6A9`) ko maine pehle energy-graph se "music-only" maan liya tha —
galat. Router/ASR se sunne pe nikla:

- `0 – 2.9s` → alag intro BGM (energy ~7x kam)
- `2.93 – 5.59s` → "ये … तुम्हें शोभा नहीं देगी"
- `5.59 – 8.31s` → "युद्ध करना तुम्हारा कर्तव्य है"
- `9.27 – 10.47s` → "शस्त्र उठाओ"
- audio fingerprint: `harmonic_ratio 0.22`, `LRA 5.2`, `TP -0.9` → **speech-led**

Yani format ka asli audio architecture: **intro BGM → Krishna ka Geeta updesh →
swell**. Isi gate ne bhajan wali galti pakdi (jab `harmonic_ratio 0.82`,
`LRA 0.8` aaya).

## Rules

- Brief me `dialogue` ho to `listen` stage aur G1–G4 **skip nahi** hote.
- Har naye build se pehle `refprofile` + `plan`; build ke baad `audit` — audit
  FAIL ho to deliver nahi karna.
- Registry me naya engine add karne pe `SKILLS` list me entry + `discover` re-run.
