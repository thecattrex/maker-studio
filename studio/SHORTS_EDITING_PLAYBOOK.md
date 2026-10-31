# Shorts Editing Playbook (jo maine tutorials + tumhare references se seekha)

## 1. Diagnosis: mera pehla output kyun bekar tha

Maine tumhare 4 reference videos ko scene-detect karke naapa:

| Reference | Dur | Cuts | Cuts/sec | Median shot |
|---|---|---|---|---|
| Kingsman edit (`4rlFBAAYEZE`) | 54.8s | 228 | **4.16** | **0.17s** |
| GoT edit (`GNurTlWX0r4`) | 35.7s | 27 | 0.76 | 1.13s |
| RankCola (`7MNYboBFHBM`) | 29.9s | 14 | 0.47 | **5.9s per item** |
| DiaryRanks (`FFL6j7QMghs`) | 45.5s | 10 | 0.22 | **~8s per item** |

Mera output: har shot **1.2–2.4s**, uniform, aur rank items **2.5s**.

- Cine edit me mujhe **0.2–0.8s** ke cuts chahiye thay → 4-8x slow tha.
- Rank me mujhe **6–8s per item** chahiye thay → 3x fast tha, isliye "slideshow" lag raha tha.

Baaki galtiyan: gray panel content ke upar, same clip repeat, koi hook nahi, text chhota,
transition nahi, sound design boundary pe nahi, framing center nahi.

## 2. Techniques (CapCut tutorials se — FDOi29blAFI, LdTocMoppA)

1. **Hook 0–1.5s** — pehla frame hi sabse interesting ho. "Hey guys" nahi. Mid-action start.
2. **Ripple edit** — har pause/millisecond dead air hatao. Sunne me "punchy" yahi se aata hai.
3. **Punch in / punch out** — alternate cuts pe scale badhao (100% → 115%) — video dynamic lagta hai.
4. **Eye-line match** — punch in karte waqt subject ki aankhein same position pe rakho, warna jump dikhta hai.
5. **Clean cuts > fancy transitions** — capcut ke transitions gimmicky lagte hain; simple cut better.
6. **Captions** — 1–4 words per group, word-by-word, heavy font, center ke paas (aankh ko kam ghoomna pade), safe zone (bottom 15% chhodo).
7. **Color grade** — saturation up, contrast down, slight warm.
8. **Sound design** — whoosh on transition, riser before reveal, bass hit on payoff; music voice ke neeche -8 to -12 dB.
9. **Loop close** — last frame first frame se milta ho to replay milta hai.
10. **Word-by-word text animation** — 8 frame ke andar slide up + cubic ease.

## 3. Rules jo maine apne renderer me daale

### Rank / Top-5 style (tumhare neeche wale 2 examples)
- Item duration **6–8s**, har item alag source se (variety).
- **Scoreboard**: 1..N numbers permanently left me, current = red + bada, past = white, future = dim gray.
- **Hook**: sabse best item ka 1.2s teaser sabse pehle ("wait for #1" feel).
- Boundary pe **white flash (2 frame) + whoosh + tick**.
- Payoff pe **zoom punch + impact + text pop** ("BOOM!", "NO WAY").
- Title top pe 2 lines (white + accent red), tagline chhota.
- End card: freeze + "FOLLOW FOR MORE".

### Cine / music-edit style (tumhare upar wale 2 examples)
- Cut pattern beats pe: `0.35, 0.5, 0.35, 0.8, 0.35, 0.5, 1.2, 2.0` — uniform nahi.
- Alternate cuts pe punch-in (1.0 → 1.12), climax pe **slow-mo 0.55x + impact + flash**.
- Text 2–5 words, beat pe pop, center.
- Closing shot 1.5–2s hold (breathing room) + loop.

## 4. Abhi bhi missing (tumhare links se seekhna hai)
- Beat-exact music sync (mere paas royalty-free generated beat hai, real trending track nahi).
- Meme/emoji stickers, zoom-blur transitions, shake effects.
- Real "viral" hook copywriting per topic.

---

# 5. Correction #2 — "faltu sound" ka issue (tumne pakda)

## Galti kya thi
Tumhare 4 references me audio **ek hi cheez** hai: source ka real audio (movie dialogue / ball bounce / crowd).
Music sirf background layer hai. Maine `BOOM!`, whoosh, tick, impact **invent** kar diye — usme koi "BOOM" nahi bola
ja raha tha, koi transition sound source me nahi tha. Result: random awaazein = cheap.

## Tutorial se jo mila (0_JsY0H6hSo, timestamp 03:24)
> "Animate and edit with the sound first. Here's what most editors do incorrectly: they do the video,
> edit everything, and then put music underneath. Stop doing that."

Matlab: **audio timeline pehle banao, video uske upar**. Music baad me "chipkayi" cheez nahi hai.

## Ab code me kya badla
- Default `--music` = **None** → sirf source ka real audio
- `add_sfx(...)` / `boom_word(...)` calls **hata diye** (rank + cine dono se)
- Cine template ab **source ke apne audio onsets** pe cut karta hai (energy curve se), na ki fake beat pe
- Music aaye to bhi **-10 to -14 dB** neeche, sirf bed ki tarah (0.22 gain)
- Agar future me SFX chahiye, tab bhi **sirf 3 jagah**: item cut-in, payoff, end card — aur volume **-18 dB** se upar nahi

## Verification
`grep add_sfx templates.py` → sirf function definition bacha, koi call nahi.
