# VIDEO STUDIO — MASTER SPEC
_Ye file authoritative hai. Kuch bhi change karne se pehle isse padho._
_Last updated: 2026-10-23_

---

## ⚠️ KAUN SA TYPE, KAUN SA ENGINE (ye galti mat karo)

| Type | Engine | Kabhi mat karo |
|---|---|---|
| **Type 1** | `run.py peak` / `run.py scene` | — |
| **Type 2** | Reusable maker: `studio/type2/build.py` + `mix.py` + `config.json`; newer EP29-style frame uses `build_ranking` | Current selected BGM: C2 (`c2_48.wav`) at ~17%; keep the phrase + chicken interstitial |
| **Type 3** | **`t3.py` ONLY** (`projects/<name>/`) | `run.py plan` se Type 3 mat banao (guard laga hai, error dega) |

**Rule:** jis type pe kaam ho raha hai, sirf usi ka code aur usi ki settings.
Ek type ki setting doosre me le jana = reject. Audio ke numbers jaan-boojh kar
alag hain — neeche "AUDIO — Type 2 vs Type 3" table dekho.

---

## 0. User rules (permanent, never drop)

- **Hinglish me reply.**
- **Jis type pe kaam ho raha hai, sirf usi ko chhedo.** Type 2 bola -> Type 2 ka code/settings.
  Type 3 bola -> Type 3. Ek type ka setting doosre me mix karna = reject (2026-10-23 user rule).
- **No UI.** Sirf CLI/automation. Content main khud internet se laata hoon.
- **Topic khud pick karna hai** — web se views/trend dekh ke. User har baar topic nahi dega.
- **Editing hi deliverable hai.** Raw clip + overlay = failure. Text layers, action captions,
  impact words, hook, pacing, frame treatment = asli kaam.
- **Storage discipline:** junk mp4 delete karo, workspace chhota rakho, sirf latest output rakho.
- **Progress dikhao, bade render se pehle bolo.** Long silent runs mat karo.

---

## 1. Teen formats

### TYPE 1 — Continuous movie scene (Kingsman style)
- **Ek hi scene, uncut, no narration, no montage.** Internal shot changes film ki apni cutting hain.
- **Hook:** pehle 4–5 s me scene ka peak/punchline, phir scene apne start se.
- **Language:** movie ka **existing Hindi dub** (Hindi version ke liye). Khud dub/voice-clone nahi.
- **Text:** header (2 lines, line-2 accent), action captions `(LIKE THIS)`, impact words.
- **Reference:** `_6HF-smeZvc` (43.4s, GoT), `zzY9iXVh5IA` (55.2s, Kingsman).
- **Status:** built (`build_scene_edit`). User ka Type-1 feedback pending hai.

### TYPE 2 — Top-5 countdown (fails / parkour / funny)
**Reference: `Q1c7K8PrsC4` — "Ranking Insane Parkour Fails" (25.1s, 608×1080)**

| Element | Spec |
|---|---|
| Canvas | 1080×1920 (9:16) |
| Top band | **black, ~19% height** (≈360px) — yahan title rehta hai, poore video me |
| Bottom band | black, ~7% height (≈135px) |
| Video area | full-width strip band ke neeche, **koi rounded card / square / blur backdrop nahi** |
| Title | 2 lines, har word ka apna colour — white / yellow / red. Bold sans (Poppins ExtraBold). Poore video me continuously. |
| Side list | left edge pe `1. 2. 3. 4. 5.` + chhota label. Jo chal raha hai wo bright, baaki dim. |
| Order | **shuffled** (2nd, 5th, 4th, 3rd…) par **#1 sabse last**. |
| Clip end | clips ke beech **black gap (~0.2s)** taaki pata chale clip khatam hui. |

**Editing do tarah se ho sakti hai — source dekh ke decide karo:**
1. **Ranking style** (jaisa `Q1c7K8PrsC4`) — jab clips action/parkour/skill ho.
2. **Funny style** (jaisa `1hnS01vks6A` — Parkour Fails) — jab clips genuinely funny/fail ho:
   **black & white**, skull emoji, `DISASTER` stamp, sound effect. Funny content ko waise hi rehne do.

⚠️ **Content rule:** clip ke andar wo actual moment hona chahiye jo label bolta hai.
Har timestamp contact-sheet se verify karo — title/thumbnail dekh ke guess nahi.

**Status:** ✅ BUILT + RENDERED. `samples/type2_ranking_fails.mp4` (24.0s).
`build_ranking` + `Timeline.frame` (video ko band area me confine karta hai).

### TYPE 3 — Narration explainer
**Reference: `v3wYzQ0fU6o` — layout/caption reference (720×800, 9:10)**
**Accepted output:** `samples/type3_FINAL.mp4` · `type3_trial3.mp4` (58.82 s) — Trial 3 user ne accept kiya.

> **Purana spec (4:5 portrait 864x1080, "small caps") GALAT tha - delete kar diya.**
> Asli ratio Trial 3 me user ne fix kiya: **1080x1920, 9:10 content band**. Wahi locked hai.

| Element | Value (LOCKED) |
|---|---|
| Canvas | **1080x1920** |
| Content band | **1080x1200 @ y = 360..1560** (9:10) - upar-neeche **360 px black** |
| Header line 1 | Anton, **`\fs148` = 77 px cap-height**, `y=112` - pehla word **RED**, baaki WHITE |
| Header line 2 | Anton, **`\fs113` = 59 px cap-height**, `y=202` - pehla word **YELLOW**, baaki WHITE |
| Caption font | **Poppins ExtraBold `\fs58`**, centre `x=540`, **`y=1260`**, border 10 black, shadow 4 |
| Caption behaviour | **purani line WHITE + nayi line YELLOW**, word-by-word build (reference `v3wYzQ0fU6o`) |
| Caption animation | **KOI scale-pop nahi** - user ne reject kiya ("disturbing"). Sirf colour build. |
| Caption script | **Hinglish (Roman)** - Devanagari screen pe KABHI nahi |
| Narration | **Hindi (Devanagari script to TTS)**, voice **`voice-02`** (Arena), feelings/emotion chahiye - flat delivery reject |
| Source audio | movie ka original **0.50x** (`duck: 0.50`) pe - narration ke neeche |
| Background music | **KOI NAHI.** Type 2 ka selected C2 bed yahan mix nahi hota - ye permanent rule hai. |
| Master gain | **+2.5 dB** (safe; +3.5 clip karta hai) |
| End card | `THE END` `\fs136` `y=1260` |

**libass scale rule (verified, dobara guess mat karo):**
```
Anton cap-height = fs x 0.52      (fs 46=24, 88=46, 148=77, 200=103 px)
target px chahiye  ->  fs = target / 0.52
```

**Pipeline:** `t3.py` - **Type 3 ka ekmatra engine.** `run.py plan` Type 3 nahi banata.
```
python3 t3.py new    projects/<name>   # scaffold
python3 t3.py fetch  projects/<name>   # source download
python3 t3.py narr   projects/<name>   # whisper word-timing
python3 t3.py build  projects/<name>   # render
python3 t3.py check  projects/<name>   # audio + caption QC
python3 t3.py verify projects/<name>   # SPEC vs project.json + contamination scan
```

**Status:** BUILT + ACCEPTED. `projects/inception/` = reference project (Inception ending, 58.82 s).

## 2. Reference measurements (ffmpeg scene detect)

| Ref | Dur | Cuts | Median shot |
|---|---|---|---|
| `_6HF-smeZvc` GoT edit | 43.4s | 29 (0.67/s) | **1.03s** |
| `zzY9iXVh5IA` Kingsman | 55.2s | 50 (0.91/s) | **1.12s** |
| `Q1c7K8PrsC4` Ranking fails | 25.1s | ~5 items | ~5s/item, 0.2s black between |
| `IOlPh-GFKI8` SPR explain | 34.8s | continuous scene | captions each line |

**Measured bars:** `Q1c7K8PrsC4` → top **18.8%**, bottom **6.9%**. `IOlPh-GFKI8` → 0/0 (full-bleed 4:5).

---

## 3. Text system (textkit.py)

18 ASS styles, sab defined: `Title, TitleHi, Sub, Cap, CapHi, Rank, RankDim, Small, Chip,
Watermark, Header, HeaderHi, ActionCap, Impact, RankNum, RankLbl, Dialogue, DialogueHi`

| Method | Kaam |
|---|---|
| `header(t0,t1,top,bottom)` | 2-line header, line-2 accent colour, dark halo (bright frames pe legible) |
| `action_caption(t0,t1,txt)` | `(GREY-WHITE, LETTER-SPACED)` with outline |
| `impact(t,dur,txt)` | bada punch word — white fill + coloured glow + pop-scale |
| `dialogue_caps(words, to_global)` | **word-level dialogue captions**, 2–3 words/card, bola ja raha word red |
| `rank_side_list(…)` | left column 1..5, bright/dim/done + `labels_on` (progressive reveal) |
| `watermark` | bottom-right, halka |

**Rules jo user ne diye:**
- Captions **clean font** (Poppins ExtraBold), **koi AI bubble / box / emoji spam nahi**.
- Text **confusion-free** — saaf padhne layak, upar ki black jagah me continuously.
- Ek saath **stacked text nahi** ("bht ajjeb" lagta hai).

---

## 4. Colour / frame treatment

- **Type 1:** rounded card (1010×860 at y=300) + **blurred same-frame backdrop** (brightness −0.16, sat 0.95). Full-bleed nahi.
- **Type 2:** full-width strip, **no card**, black bands top/bottom.
- **Type 3:** 4:5 full-bleed + **`film` grade** (measured against Kingsman `4rlFBAAYEZE`:
  contrast 1.24, sat 1.16, teal shadows / warm highlights, vignette, grain). Optionally `teal`.
- Common grade: `contrast 1.07, saturation 1.16` + `unsharp 5:5:0.55`.
- Slow push-in: `zoom_to` 1.03–1.07 per clip.

---

## 5. Rejections (kabhi dobara mat karna)

| Rejected | Kyun |
|---|---|
| Raw compile + text overlay | "clip hi de diya, editing kahan hai" |
| Invented SFX (BOOM/whoosh) | source me nahi hai |
| Stacked / layered text | "bht ajjeb" |
| Rapid montage + black bars | movie edit me pacing tod deta hai |
| Clip bina text editing | editing = deliverable |
| **Type 2 me rounded square card + blur bg** | "proper square me mat rakho" |
| Type 2 me galat moment (label vs clip mismatch) | confusion |
| Text dim / unreadable | "text achha rehna chahiye, confusion nahi" |

### LOCKED: Type 2 final look (2026-10-22, user ne approve kiya)
- **Title:** Anton, `title_size=116`, 2 lines, per-word colour, band 360 ke andar continuous.
- **Side list numbers:** `Archivo Black`, fs **101** (`\fnArchivo Black\fsp0`), no trailing dot.
- **Side list labels:** `Anton`, fs **70**, **ALL-CAPS**, sirf tab dikhta hai jab wo rank aa chuka ho
  (`labels_on = set(before) | {n-1}`) — baaki ranks pe sirf number.
- Spacing: `x=86, y0=band+168, gap=232, num_w=96`. Outline solid (`\3a&H00&`).
- **Font gotcha:** "Poppins ExtraBold" libass me resolve nahi hota → Arial pe fallback. Har overlay
  me explicit `\fn<family>` do. Families jo pakka chalti hain: Anton, Archivo Black, Bebas Neue,
  Barlow Condensed.


---

## 6. Technical gotchas (code-level)

- **RAM 2 GB.** Giant `filter_complex` OOM → per-segment render + concat. Kabhi `faster-whisper`
  aur `cv2` saath mat chalao.
- **Render "atak" ka asli reason:** ek se zyada render process ek saath chalna + `loudnorm` +
  `+faststart` ka memory. **Fix: `NORM=0`** → 25s ka short 15 min se **30 s** me ban jaata hai.
  Render se pehle `pkill -9 ffmpeg` karke check karo ki koi purana process zinda na ho.
- `mask.png` full canvas ka hota hai → `crop` karke box size me laana padta hai (warna
  "Input frame sizes do not match").
- Mask input ko **last** me add karo, warna video/audio input index shift ho jaate hain.
- Cache `work/segs/` code change chhupata hai → `rm -rf work/segs` ya `CODE_V` bump.
- yt-dlp kabhi **video-only** fragment deta hai → `probe()["has_audio"]` check karo.
- **"Hindi" title ka matlab Hindi audio nahi** — `detect_language()` pehle chalao.
- Snapshots **bade source mp4 wipe kar dete hain** (>~250 MB) → source `/tmp` me rakho,
  deliverables `samples/` me.
- `crop` me timeline `t` nahi hota; out-of-range seek → black frame → `_is_black()` retry.

---

## 7. File map (yahan kya hai)

```
studio/
  SPEC.md              ← YE FILE (master spec)
  SHORTS_EDITING_PLAYBOOK.md  ← tutorials se seekhi techniques
  render.py            ← Timeline (canvas size, rounded_frame, add_gap, bright, NORM)
  textkit.py           ← Overlay + 18 styles + saare text methods
  templates.py         ← build_scene_edit (T1), build_ranking (T2), build_plan_edit (T3/plan)
  run.py               ← CLI: search|rank|cine|peak|scene|ranking|plan|auto
  analyze.py           ← video_timeline, shots, moments, detect_bars, rounded_mask
  discover.py          ← search + download (best quality, id parsing fixed)
  util.py / music.py / sfx.py
  clips/               ← plans (JSON) + narration wav
  samples/             ← deliverables (sirf jo user ko dikhane hain)
  work/ cache/         ← regenerable; delete safe
assets/fonts/          ← Poppins ExtraBold/Bold/Italic, BarlowCondensed, Montserrat
notes/                 ← tutorials extract, key learnings
tools/watch.py         ← kisi bhi link ko frames+audio me tod ke dekhne ka tool
```

---

## 8. Deliverable checklist (har video se pehle)

- [ ] Source **highest quality** (1080p), audio stream verified
- [ ] Har clip ka timestamp **contact sheet se verify** — moment sahi hai?
- [ ] Hook pehle 3–4 s
- [ ] Text readable, overlap nahi, confusion nahi
- [ ] Render `NORM=0`, single process
- [ ] QC contact sheet dekho
- [ ] `samples/` me copy + `present_file` **usi turn me**

---

## 9. Reference links (user ne diye — dobara mat maango)

| Link | Kya | Kis kaam |
|---|---|---|
| `4rlFBAAYEZE` (Kingsman) | colour grade ONLY | Type 3 filter |
| `IOlPh-GFKI8` (SPR explain) | ratio + captions | Type 3 layout |
| `Q1c7K8PrsC4` (Ranking Parkour Fails) | default/ranking style | Type 2 main |
| `1hnS01vks6A` (Parkour Fails B&W) | funny/skull option | Type 2 alternative |
| `_6HF-smeZvc` (GoT) | header + rounded card | Type 1 |
| `zzY9iXVh5IA` (Kingsman) | action caps + impact | Type 1 |

## AUDIO — Type 2 vs Type 3 (latest user-confirmed recipe)

> Type 2 = countdown; clips/SFX remain clear, with the series-selected bed and interstitials.
> Type 3 = narration explainer; no background music. Do not carry one type's mix into another.

| Layer | Type 2 | Type 3 |
|---|---|---|
| Clip audio | Keep suitable source/natural audio audible; remove/reject source songs if not cleanly separable | Original scene audio under narration at 0.50/duck 0.50 |
| Background music | **C2_ComedyToyBand / `studio/type2/assets/c2_48.wav` only; ~17% / −27.4 dB RMS, 0.5 s fade** | **NONE** |
| Voice / interstitial | “I got this” at clip transitions; chicken+scream immediately before #1. Match phrase count to the active clip layout. | Hindi narration; Roman Hinglish captions |
| SFX | Funny impact SFX aligned to the actual impact; use the selected Type-2 SFX library | None unless specifically requested |
| Type-2 audio controls | Use `type2/config.json` + `type2/mix.py`; don't reuse obsolete QKThr/67% prototype values | Duck/mix as configured in `project.json`; master gain +2.5 dB |

**Music asset verification:** current EP30–EP34 manifests reference `c2_48.wav`; its decoded audio exactly matches `MUSIC_FINAL/C2_ComedyToyBand.mp3`. This is the reusable selected track. Earlier QKThr/67% references in this spec were stale prototype settings and are superseded by the Type-2 locked spec.


### SFX rule
- **Ek clip pe max 1 SFX.** 2+ = congested.
- SFX ke beech minimum **3 s** gap.
- Placement scene dekh ke — plan: `clips/rank_dashcam.json` → `items[].sfx = [{"at": <clip ke andar seconds>, "key": "<naam>"}]`.

| clip | SFX | scene |
|---|---|---|
| #3 blind junction | `suspense` | car aane wali hai |
| #5 white knuckle | `faah` | white car saamne |
| #2 red light runner | `dun_dun_dun` | red car frame bhar deta hai |
| #4 inches away | `yeet` | gaadi camera ke saamne se |
| #1 the squeeze | `slap` | tight squeeze |

### Code changes (Type 2 only — Type 1/3 untouched)
- `templates.py::build_ranking` — naye kwargs `music, music_vol, music_ss, clip_vol, sfx_dir, sfx_peak_db`; per-item `sfx` list; `_peak_db()` helper.
- `render.py` — `Timeline.music_ss` (music input pe `-ss`), `Timeline.master_gain_db`.
- `run.py::cmd_ranking` — sab pass karta hai.

**SFX hataana:** `rm trial/sfx/<naam>.mp3` — build gracefully skip karta hai (log: "sfx missing, skipping"). Code chhune ki zarurat nahi.
