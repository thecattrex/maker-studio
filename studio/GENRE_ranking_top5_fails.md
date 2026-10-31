# GENRE SPEC — "Ranking Top 5 ___ Moments" shorts
Source: 6 reference shorts decoded (1080×1920, 2026-10-24)

## What it is
A **ranked fail compilation**. Not a story, not a tutorial. 5 unrelated viral
clips of the same *type* of accident, ranked by how funny they are, countdown
**5 → 1**, and the funniest one is saved for last.

## Measured references
| id | views | dur | clips | title line 1 | title line 2 |
|---|---|---|---|---|---|
| XulN4FZCqJ4 | 15.8M | 30.7s | 5 | RAKING **BEST** FALLING MOMENTS (white/green) | — |
| _exNdBh9DxA | 12.7M | 28.1s | 5 + 5 flash cards | Ranking **TOP 5** (TOP 5 red) | **Waterslide** Moments (yellow) |
| pfJzZqdF6CI | 288K | 37.3s | 5 | RANKING **FUNNIEST** (red) | **FAIL** MOMENTS (yellow) |
| -iCZA86PYC0 | 72K | 21.1s | 5 | Ranking Top 5 (purple) | Funniest Fails (purple) |
| aconqF1_wIY | 9.3K | 48.3s | 5 | Ranking Top 5 **Fails** (red) | **Moments** (yellow) |
| uj4GXHn6Jw4 | 3.4K | 24.8s | 5 | Ranking top 5 funniest tatoo fails | — |

Winners are **21–31 s**, losers are **37–48 s**. Length is the single clearest
difference between 15M and 3K views.

## Beat sheet (what actually happens)
1. **0.0 s — title card + clip already playing.** No intro, no logo, no "hello".
2. **Number stack is already on screen**: `1. 2. 3. 4. 5.` down the LEFT edge,
   top to bottom. Each number a different colour (yellow / white / orange / red / purple).
3. **Countdown 5 → 4 → 3 → 2 → 1** (bottom-up reveal). Each clip = one fail.
4. As each clip plays, its rank number gets its **punchline word + emoji** next to it
   (`3.Bouncy 😂`, `4.Too fast 🥀`, `5.Incoming 🎆`, `5.Toilet Spy 😳`, `5.Woo😂`, `3.WEE`).
   Labels accumulate — by the end all 5 are filled.
5. **Flash cards between clips** (in the 12.7M one): full-frame white or black with one
   word — `FAST`, `WOW`, `WHOA`, `DUDE`, `TOTALLY`, `1 DAY`. 0.8–1.5 s each. Pure rhythm.
6. **#1 last, longest, biggest payoff.** Then it just ends. No outro, no subscribe screen.

## Clip rules (this is the whole game)
- One clip = **one event**. Event must **complete on screen** — the fall has to land.
- Start **1–2 s before** the setup. End **0.5–1 s after** impact (reaction is the laugh).
- 4–7 s each. #1 is often 6–9 s.
- Subject must fill the frame — a 3-pixel cyclist on a dashcam is not a clip.
- Source captions/watermarks from TikTok/IG are left in (they don't bother cleaning).

## Audio
- **Continuous music bed** — measured 0% silence in 5 of 6 refs (min level −30 to −33 dB).
  Comedic/playful bed, low-mid level. (Same family as "Monkeys Spinning Monkeys".)
- **Original clip audio kept loud on top** — the "woo", the thud, the crowd. That IS the joke.
- No voiceover, no narration, no AI voice.
- Transition hit/whoosh at each cut.

## Layout
- 1080×1920, title in the top **~300 px** on pure black.
- Clip fills full width, no letterbox (the 288K one letterboxes and looks worse).
- Number stack overlaps the left ~15% of the frame.
- Text: heavy rounded sans, white with hard black outline, 2-line title with
  colour accents (`Fails` red, `Moments` yellow etc).

## What our previous build got wrong
| ref does | we did | fix |
|---|---|---|
| 21–31 s | 33 s then 25.7 s | keep 25–30 s |
| 5 clips, all with a completed event | 2 real + 2 filler (empty road / static car) | reject clips without a visible result |
| numbers 1→5 top-down, words appear as it plays | static 5→1 list with fixed labels | accumulate words per clip |
| flash-card transitions | gap only | add 0.8–1.2 s word cards |
| clip audio loud, kept | 55% (ducked) | raise to ~85% |
| music bed continuous | yes (65%) | keep ~55–65% under louder SFX |

## Monetization note (one line, factual)
This genre runs on **reposted UGC** (TikTok/IG clips). YouTube's reused-content
policy is what decides whether a channel like this can monetize — it's not a music
licensing issue.

---

# SELECTION MATHS (measured, 2026-10-24)

Motion maths does **not** separate good from bad clips. Measured on 17 reference
segments vs our own delivered clips: peak motion area, salience (peak/median) and
subject-blob size all came out **the same or better for our bad clips**. Camera
shake poisons every pixel-motion metric. Numbers proved useless as a filter.

The one metric that *does* separate: **is a human in frame, and how big.**

| | person found in | best person height | verdict |
|---|---|---|---|
| ref XulN4FZCqJ4 (15.8M) | 7/8 frames | 0.67 | big, clear subject |
| ref _exNdBh9DxA (12.7M) | 6/8 frames | 0.47 | clear subject |
| ref aconqF1_wIY | 7/8 frames | 0.17 | weakest of the refs — 9.3K views |
| **ours (delivered)** | **3/8 frames** | **0.26** | subject missing from half the frames |

Per-segment scan (`studio/pick.py`):

| source | result |
|---|---|
| ref XulN4FZCqJ4 — all 5 clips | **PASS 5/5**, person_h 0.32–0.68, cover 0.89–1.00 |
| ours — clip 1 (cyclist dashcam) | PASS but cover 1.00 / h 0.36 **only because of the 4× zoom** |
| ours — clip 2 (parker) | **REJECT** — person in 50% of frames, no event |
| ours — clip 3 (red light, dropped) | **WEAK** — person in 22% of frames |
| ours — clip 4 (roof) | **WEAK** — no event inside the clip |

## The rule (now code, `pick.py`)
```
PASS  : person_cover >= 0.60   (human visible in 60%+ of sampled frames)
        person_h     >= 0.22   (tallest human >= 22% of frame height)
        0.15 <= impact_pos <= 0.92
        2.5s <= dur <= 9s
score : person_h*3 + cover*2 + min(salience,4)*0.4 + (3..7s ? 1 : 0)
```

Practical reading: **the person has to be big and stay in the frame.**
Dashcam / CCTV wide shots are auto-rejected no matter how dramatic the event —
the viewer cannot see a human, so there is nothing to laugh at.

---

# TITLES — measured formula

On-screen title is **two lines, 4–5 words total**, `Ranking` + a superlative + the topic:

| views | line 1 | line 2 | pattern |
|---|---|---|---|
| 15.8M | RAKING BEST | **FALLING** MOMENTS | superlative + topic |
| 12.7M | Ranking TOP 5 | **Waterslide** Moments | number + topic |
| 288K | RANKING FUNNIEST | **FAIL** MOMENTS | superlative + topic |
| 72K | Ranking Top 5 | Funniest Fails | number + generic |
| 9.3K | Ranking Top 5 Fails | Moments | generic, no topic |
| 3.4K | Ranking top 5 funniest | tatoo fails moments | topic at the end |

Rules pulled from the data:
1. **Always start with `Ranking`** (one 15.8M video even spells it "RAKING" — nobody cares).
2. Word 2 is a **superlative**: `Top 5` / `Best` / `Funniest`.
3. Then the **topic noun**: `Falling` / `Waterslide` / `Fail` / `Tattoo`.
4. End with **`Moments`** (most common) or `Fails`.
5. **Two lines, ≤ 5 words.** The 3.4K video is the longest title (7 words) → weakest.
6. Line 2 is the topic; colour that word (yellow/green), keep the rest white.
7. Topic word must match the clips. Mixed subject matter → use the generic
   **`Funniest Fail Moments`** / **`Best Falling Moments`**, never an invented
   category word.

**Do NOT invent words like "DUMB".** The references never do. Our previous title
`TOP 4 DUMB MOMENTS` broke rule 2 (no superlative) and rule 7 (invented word).

Ready-to-use titles for mixed clips:
```
Ranking Top 5  |  Funniest Fails
Ranking Top 5  |  Best Fails
Ranking Top 5  |  Fail Moments
Ranking Funniest  |  Fail Moments
```

# SELECTION v2 — fall detection (`studio/clipsel.py`)

v1 asked only "is a human big in frame". Problem: that passes a clip where the
person just *stands* there, and on dashcam footage HOG happily labels a road
marking as a person.

v2 measures the thing the genre is actually about — **a fall**:

```
person   : HOG boxes TRACKED frame to frame (IoU > 0.15 with previous box).
           A one-frame false positive cannot count.
           cover = fraction of frames the same subject is tracked in.
           height = median of the 3 tallest tracked boxes (not one lucky frame).
motion   : biggest blob after removing global camera motion (phase correlation).
fall     : downward speed of that blob's centroid, in frame-heights/second.
trim     : output clip is cut so the impact lands at 78% of the clip.
```

Verdict thresholds (calibrated on the 6 reference shorts + our own failed build):

| check | pass |
|---|---|
| person tracked | ≥ 45% of frames |
| subject height | ≥ 0.22 of frame |
| fall speed | ≥ 0.55 frame-heights/sec |
| impact position | 0.35 – 0.95 |
| duration | 2.8 – 8 s |

Blind test, run on the reference shorts (which are all known-good) and on our
old delivered video (which is known-bad):

| video | PASS hits | REJECT/WEAK |
|---|---|---|
| XulN4FZCqJ4 (15.8M, all good) | 3/5 | 2 |
| aconqF1_wIY (9.3K) | 3/4 | 1 |
| pfJzZqdF6CI (288K) | 1/4 | 3 |
| _exNdBh9DxA (12.7M waterslide) | 1/4 | 3 |
| **ours (bad build)** | **1/5** | **4** |

The tool is not perfect — it is a **filter, not a judge**. Correct workflow:
`clipsel.py` narrows 40 candidates down to ~8, then a visual sheet is rendered
showing the exact impact frame of each, and a human (or a vision pass) picks the
final 5.
