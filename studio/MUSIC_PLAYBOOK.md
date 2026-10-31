# MUSIC PLAYBOOK — do approaches + article rules

_User ka permanent rule (2026-10-24): "jab bhi music banane bolu, ye dono approach lagao."_

**Current production selection (verified 2026-10-31):** Type 2 uses C2 (`MUSIC_FINAL/C2_ComedyToyBand.mp3`, converted to the engine-ready `studio/type2/assets/c2_48.wav`) at about 17%. The QKThr section below is historical arrangement/reference research, not the current Type-2 music asset. Type 1 and Type 3 use no BGM.

---

## STEP 0 — pehle reference ka INSTRUMENT pata karo (guess nahi)

| Track | Asli instruments | Key facts | Source |
|---|---|---|---|
| **Monkeys Spinning Monkeys** | **Flute** (lead) + **Violin, Viola, Cello** (pizzicato staccato) | 142 BPM, mid-heavy 808 Hz, no vocals, CC BY 4.0 | Wikimedia file page: "Instruments: Flutes, Violin, Viola, Cello" |
| **QKThr (Aphex Twin)** | **Harmonium** (reed organ, "Penty Harmonium") + brushed acoustic kit + upright/double bass + slightly out-of-tune echoing piano | 61-79 BPM, **Db major**, chords **Dbmaj7 – Ab7 – Db – Gb**, moody/serene | last.fm wiki, brettworks, Chordify, Shazam |

**Lesson:** pehli baar marimba use kiya tha Monkeys ke liye — **galat**. Real palette flute + pizz strings hai.

---

## APPROACH 1 — same instruments, article ke rules se arrange karo

Reference ke asli instruments lo, aur unhe niche wale arrangement rules se set karo.

## APPROACH 2 — same notes/chords, alag (better) instrument combination

Melody/chords same rakho, sirf instrument combo badlo. Article ke "blend" rules se naya combo chuno
(jaise strings family = zyada blend; trumpet+clarinet+viola+bassoon = kam blend, zyada character).

---

## ARTICLE RULES (jo yaad rakhne hain)

**Brinkman, "How to Orchestrate and Arrange Music"**
- **Masking se bacho:** melody top pe ho, ya uski tone quality alag ho. Same register me do parts = mud.
- **Blend:** same family = zyada blend (strings); mixed families = kam blend, zyada colour.
- Melody ko space do — voicing spread karo, warna melody dab jaati hai.
- Percussion ka kaam: **drive, accents, effects.**

**Sound on Sound, "Arranging Pop"**
- **Less is more** — 5 parts ka matlab 5 instruments nahi; doubling se texture banao.
- Doubling ka classic: **flute + oboe** jaise do timbres milao → ek ko delicacy, ek ko warmth.
- **Hook ko do jagah use karo:** vocal melody ko instrument pe bhi bajaao.
- Lead ke same register me backing parts mat rakho — fight karte hain.
- Ek **single high sustained string note** chorus/transition pe = instant impact.

**The Instrumentalist, "Arranging for Jazz Combo"**
- **Anticipation:** melody ke downbeat notes ko aadha beat pehle khiska do → swing feel.
- **Syncopation:** downbeats ko upbeats pe shift karo.
- **Build: low → high, few → many.** Combinations 8-16 bar se zyada tezi se mat badlo.
- Pedal point bass + ostinato = intro ka best tareeka.

**jimrepa, "Arranging in a Nutshell"**
- Simple arrangement = unison/octave, sirf chuni hui jagah harmony.
- Form: intro → head → interlude → variation.

**Friedemann Findeisen — "The Addiction Formula"** (book)
- Arrangement = build/drop ka khel; section-wise energy curve. Har section me kuch add ya remove hota rahe.

---

## MERA WORKING CHECKLIST (har track pe)

1. Instrument palette fix (Approach 1) **ya** same notes + naya combo (Approach 2)
2. Melody alag register me, alag timbre me — masking zero
3. Hook ko 2 instruments pe double karo (octave ya third)
4. Swing/humanize: 16th pe 6-10% swing, velocity ±8%, timing ±8 ms
5. Build: 2 bar sparse → 4 bar full → 2 bar variation + fill
6. Ek high sustained note transition pe
7. Mix: bus-wise EQ + gentle compression + plate/ping-pong reverb
8. **Loudness: -14 LUFS, peak -1 dB** (ffmpeg loudnorm)

---

# COMEDY / FUNNY MUSIC — research (2026-10-24)

Sources: northernfilmorchestra.com "How to Write Music for Comedy" · professionalcomposers.com
"How to make Funny Music" · sonilo.com "Funny Background Music" · melodigging.com "Cartoon" ·
Wikipedia "Comedy music" · Sound on Sound "Cartoon Composing" · r/musictheory threads

## Instruments jo khud me funny hain (ranking)
1. **Bassoon** — "clown of the orchestra". Staccato = instant comedy.
2. **Tuba** — staccato oom-pah bass. "Tuba is never not funny."
3. **Pizzicato strings** — snappy, cheeky, tiptoe feel.
4. **Glockenspiel / xylophone** — cartoon eye-blinks, spins, falls.
5. **Clarinet** — staccato, mischievous; long gliss possible.
6. **Slide whistle** — vertical movement / falls.
7. **Kazoo, accordion, banjo, ocarina, ratchet, woodblock, temple blocks** — toy-band colour.
8. **Muted trumpet "wah-wah"** — confusion / disappointment ("sad trombone").

## Techniques
- **Alternating root/fifth staccato bass (oom-pah)** — #1 funny recipe.
- **Staccato everywhere** — short notes = bounce.
- **Dotted rhythm** — lopsided / "drunk" walk.
- **Glissando** — instant gag (trombone/slide whistle/clarinet).
- **Stop-time + silence** — joke ko jagah do; punchline se pehle music kaat do.
- **Melody ko mallets pe double karo** (pizz + glock octave apart).
- **Melody instrument-to-instrument bounce** kare mid-phrase.
- **Major key**, mode mixture, tritone jab, chromatic runs.
- **Drum fill "ba-da-ba-tsss"** punchline pe + ratchet/timpani hit.
- **Lots of SPACE** — non-stop music me joke land nahi karta.

## C1 vs C2 (mere builds)
- **C1 (Approach 1)** = research ka asli palette: pizz strings lead + glock double + bassoon counter + tuba oom-pah + clarinet octave + woodblock + slide whistle + ba-da-ba-tsss.
- **C2 (Approach 2)** = same tune/chords, naya combo: kazoo lead + banjo double + accordion pump + whistle + ratchet.
