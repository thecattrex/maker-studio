# TYPE 2 — LOCKED SPEC (updated 26 Oct 2026)

Ye file type-2 reel ka final, locked template hai. Har naye type-2 build me yahi rules lagenge.

---

## 1. Series — jo ban chuka (Drive pe final)

| ep | content | local size | duration | avg/clip | Drive file id |
|---|---|---|---|---|---|
| ep1 | surf / skates / golf / tube / tramp | 9,849,005 B | 12.100 s | — | `1emnoNDP8MxWBPWreUI7JpSEi3c-1xhth` |
| ep2 | (C_h4U9klE-Mb8 source) | 12,696,893 B | 17.633 s | — | `1Vo2j1fsN3o8lK8OVG8fBKiJfSqRl4cOg` |
| ep3 | parkour fails (Z1kMl6ptui8) | 12,431,375 B | 16.767 s | 2.967 s | `12RlifZMQC8d1ZBmUGZBSwplquHZB_NI6` |
| ep4 | BMX fails (jH39BOWwfvE) | 17,189,037 B | 17.000 s | 3.01 s | `1TAZ5Na0PfBtcLycybk1BFMcrkTfxu10A` |
| ep5 | enduro fails (lpQSkp4HGb8) | 23,774,290 B | 17.167 s | 3.05 s | `1FO33zwqTuV2w7eNWcZQjEOErFTscfDRK` |
| ep6 | funny fails mix (FFi-AU09ZUY) | 11,332,967 B | 16.967 s | 3.01 s | `1VamtpTSGmcZWvk2fxHE4M09yVnHHd3fF` |

Sab **anyone-with-link · viewer · discovery OFF**.

**Common final spec:** 1080×1920 · 30 fps · H.264 yuv420p · AAC 192 kbps 48 kHz · **−14.2/−14.4 LUFS** · true peak < −4 dB.

---

## 1b. ep4 — last build ka poora data (reference episode)

**Source:** YouTube `jH39BOWwfvE` — freedombmx "BMX FAILS 2023", 289.1 s, 2560×1440@60. Vertical crop `crop=1089:1440:735:0` → `scale=1080:1428`.

| # | clip | src ss | cfg dur | asset dur | SFX (rel) |
|---|---|---|---|---|---|
| 3 | the ramp drop | 142.00 | 2.95 | 3.00 | slap @0.60 |
| 5 | the bowl crash | 221.60 | 2.95 | 3.00 | yeet @2.60 |
| 2 | the ledge jump | 150.40 | 3.25 | 3.30 | oof @2.30 |
| 4 | the rail bail | 157.35 | 2.75 | 2.80 | ba_drum_tss @1.25 |
| 1 | the dirt faceplant | 70.80 | 3.20 | 3.20 | fail @2.10 |

cfg sum **15.10 / 5 = 3.02** (asset avg 3.064). Final **17.000 s** = 15.10 clip + 4×0.267 gap + chicken 0.567 + gap (measured frames).
Measured: starts `0 · 3.2667 · 6.5 · 10.0333 · 13.9667` · ends `3.0 · 6.2333 · 9.7667 · 12.8 · 17.0` · chicken **13.0667–13.7** · rank-1 @13.967.

**Voice (measured NCC):** 0.996 @0.000 · 0.993 @2.650 · 0.962 @5.8833 · 0.964 @9.4167 · scream 0.818 @13.067 · gap me voice 0.059 (nahi).
**SFX abs:** slap 0.600 · yeet 5.870 · oof 8.800 · ba_drum_tss 11.280 · fail 16.067 — sab 0–3 ms pe.
**Loudness:** −15.1 → −14.2 LUFS (+0.90 dB).

**ep4 sourcing data (yahi se agla BMX-style ep banega):** usable windows 141.46–145.60 (ramp) · 221.08–225.22 (bowl) · 149.58–153.76 (ledge) · 157.04–160.32 (rail) · 69.66–74.28 (dirt). Unused: 34.70–37.74, 37.74–41.90, 62.52–66.90, 81.24–84.78, 84.78–88.66, 128.30–131.52, 178.70–182.22, 225.22–229.20. Reject: 101.62–105.00 (static indoor), 116.32–120.78 (balcony far).

---

## 1c. ep5 — enduro build (reference)

**Source:** YouTube `lpQSkp4HGb8` — Enduro DKA "Dirt Bike Fails 2024", 653.6 s, 2560×1440@60 (AV1/opus). Crop `crop=1089:1440:735:0` → `scale=1080:1428` (source frame me content left me hai, x0=735).
Source me corner pe chhota hexagon logo hai — 1080 width pe invisible, crop ke andar.

| # | clip | src ss | cfg dur | SFX (rel / abs) |
|---|---|---|---|---|
| 3 | the tire pit | 167.90 | 2.95 | ba_drum_tss @1.35 (1.350) |
| 5 | the root climb | 57.30 | 2.95 | yeet @1.75 (5.017) |
| 2 | the log slide | 323.20 | 3.05 | slap @2.00 (8.500) |
| 4 | the slope flip | 582.40 | 2.85 | oof @1.95 (11.783) |
| 1 | the flying bike | 245.00 | 3.45 | fail @2.90 (16.767) |

**cfg avg 3.05** (sum 15.25) · final **17.167 s** · −14.3 LUFS · peak −3.8 dBFS.
Starts `0 · 3.267 · 6.5 · 9.833 · 13.867` · chicken **12.967–13.6** · rank-1 @13.867.

**Voice:** 0.995 / 0.996 / 0.989 / 0.989 @ 0.000 / 2.650 / 5.883 / 9.217 · chicken zone max corr 0.037 · scream 0.847 @12.967.
**SFX:** sab **0 ms** off (1.350 / 5.017 / 8.500 / 11.783 / 16.767).

**CRITICAL FIX (build.py):** gap detector pehle `a < 35` mean-luma use karta tha. Night/forest clip (mean ~34) ko gap samajh liya → chicken 9.85 pe chala gaya, saara audio shift. Ab threshold **`gap_luma` (config, default 15)** — pure black hi gap. Purane ep (bright) pe farak nahi.

**Rejected sources (dobara mat scan karo):** `CqaoMPxYQ_w` Pinkbike (POV), `Ta9a3hUXgls` scooter (snapchat/portrait mix + text), `9jvSat6t73g` FIS (too far, rank-cards), `6pJus2X3_SY` trampoline FailArmy (watermark), `88VRXgheKcA` snowboard (FunnyVines watermark box), `GLUG1czDi1M` skate (TrickTown watermark), `1EnQKVbRUrA` karting (POV), `WbkTtTomZD4` cliff jump (GoPro POV + long shots), `ghIDEMV3rZg` snowboard (GoPro POV).

---

## 2. Structure (fixed)

**Title band (top 360 px):** `RANKING BEST FAIL MOMENTS` — "FAIL" red, "MOMENTS" yellow, Archivo Black + Anton, black band.

**Left ladder:** rows **1 upar → 5 neeche**, FIXED position. Numbers 1..5 hamesha dikhte hain (dim). Label (`THE SURFBOARD` etc.) apni row pe **tab likha jata hai jab wo clip play hoti hai** — play order se rows nahi badalti.
Current clip ki row bright, played rows dim, aane wali rows darker dim.

**Clip order (play):** 3 → 5 → 2 → 4 → **🐔 chicken** → 1

| # | t (s) | Clip | Row | SFX |
|---|---|---|---|---|
| 1 | 0.000–3.000 | surfboard pool slip | 3 | yeet @1.55 |
| 2 | 3.250–5.283 | gym skates fall | 5 | oof @4.07 |
| 3 | 5.533–7.599 | golf cart tip-over | 2 | ba_dum_tss @7.08 |
| 4 | 7.816–9.882 | pool tube flip | 4 | slap @8.52 |
| — | 10.132–10.699 | **chicken face + scream** | — | scream @10.13 |
| 5 | 10.699–12.299 | trampoline miss | 1 | fail @11.25 |

Gaps 0.25 s (black beat). Chicken gap = 0.25 + 0.5667 + 0.25.

---

## 3. Audio

**Music:** C2 bed, **17%** → RMS **−27.4 dB**, last 0.5 s fade-out. (25% se ghata kar 17%.)

**Voice "I got this" — 4 baar, gap me:**
| # | Kahan | placed | sunai |
|---|---|---|---|
| 1 | sabse pehle | 0.00 | 0.20 |
| 2 | 3rd ⇄ 5th | 2.65 | 2.84–3.43 (cut 3.00) |
| 3 | 5th ⇄ 2nd | 4.93 | 5.12–5.71 (cut 5.28) |
| 4 | 2nd ⇄ 4th | 7.25 | 7.44–8.03 (cut 7.60) |

→ voice file 0.35 s pehle cut se shuru hoti hai, speech cut ke aar-paar baithti hai = "dono clips ke bich".
**4th–1st ke bich koi voice nahi** — na pehle, na baad. Wahan sirf chicken.

**Levels:** clip bed +2 dB → tanh 1.2 → **−20 dB RMS** · voice **−13 dB RMS** · duck **0.15** (voice) / **0.45** (chicken) · tanh 1.1 · peak cap **−4.8** · master tanh + cap.

---

## 4. Banned (hamesha)

- Zoom / punch-in (`zoom_to = 1.0`), action poora frame me.
- Black bars, blur-bg card, watermark, mirror/pitch tricks.
- Clip ke andar text — source ka burned-in text **delogo se hataya** jata hai (delogo source coords pe pehle, phir crop).
- Invented SFX (jo clip me sunai na de), stacked/glowing/pop text, basic font, label mismatch.
- Copyright lecture, pirated sites, VPN.
- 4-clip shortcut (5 hi, jab tak sach me 5 achhe clips na milen).
- Chicken ko last me rakhna.

---

## 5. QA gates (har build pe)

1. **Ladder check** — rows 1..5 fixed, label sirf played rows pe (sheet se verify).
2. **Voice correlation** — 4 hits pe corr > 0.95; 9.9 s ke baad max corr < 0.10 (no voice at tube/chicken/tramp).
3. **SFX peaks** — sab −4.8..−7.5 dB range me.
4. **Loudness** — −14 ± 1 LUFS, peak < −4 dB.
5. **Visual sheet** — order 3→5→2→4→🐔→1, koi black-flash nahi, koi residual source text nahi.
6. Upload → `make_public` reader + discovery OFF → curl download → **size + md5 match**.

---

## 6. Reproduce

```bash
# 1) silent base (plan me items appearance order me; "ladder":"asc" = 1 upar)
NORM=0 python3 run.py ranking --source /tmp/rc5_src.mp4 \
        --plan clips/rank_new5b.json --name type2new5c --watermark ""

# 2) chicken insert (10.132 pe trim + chicken_face + baaki)
#    -> /tmp/vid5c.mp4  (12.3333 s)

# 3) mix (music 17%, voice 4x, sfx 5+1)
python3 ~/studio/mix_new5b.py          # -> /tmp/mix5c.wav (12.300 s)

# 4) mux
ffmpeg -i /tmp/vid5c.mp4 -i /tmp/mix5c.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest out.mp4
```

**Assets (workspace me copy, /tmp bharosemand nahi):**
`~/studio/type2/assets/` → `2_surf.mp4` `5_gym.mp4` `1_golf.mp4` `3_tube.mp4` `4_tramp.mp4`
`c2_48.wav` (music) · `scream48.wav` (chicken) · `rc5_src.mp4` (11.73 s silent sequence source)
Plan: `~/studio/type2/plan_type2.json` · Mixer: `~/studio/type2/mix_type2.py`

**Source:** YouTube short `HG3gevu51Rc` (720×1280 → 1080 upscale, thodi softness accept).

**Clip cut coords** (delogo pehle, phir crop, `scale=1080:1428,fps=30,setsar=1`):
surf `ss 8.60` d3.0 `crop=634:839:43:232` ·
skates `ss 38.85` d2.0 `delogo=x=200:y=1155:w=430:h=60,crop=680:830:20:310` ·
golf `ss 25.88` d2.02 `delogo=x=190:y=1132:w=440:h=48,crop=720:952:0:240` ·
tube `ss 33.95` d2.0 `delogo=x=190:y=1132:w=440:h=48,delogo=x=468:y=182:w=145:h=64,crop=720:952:0:250` ·
tramp `ss 1.80` d1.6 `crop=720:952:0:265`

---

# 7. CLIP SELECTION — soch (locked)

## 7.1 Pehle source, phir moment
1. **Source chuno:** compilation ho to bhi 720×1280 vertical, watermark/text kam. Tier: Pexels/Mixkit/Coverr → license-checked archive → chhota creator. ESPN / FailArmy / House of Highlights **nahi**.
2. **Source-ID history check:** `/home/user/studio/type2/SOURCE_ID_HISTORY.json` aur locally available episode manifests check karo; final ke selected aur replaced/suspect IDs central history me add karo. History incomplete ho to clearly note karo.
3. **Poora source ek baar scan karo** — har 1 s pe thumbnail sheet. Jo range chicken/animal ya talking-head ho, pehle hi **blacklist** (is build me 12–25 s chicken tha).
4. **Authenticity / AI-screen (mandatory):** action window ko frame-by-frame, temporal sequence me dekho—not just a still. Face/body/prop geometry, background details, water/splash physics aur continuity me morphing ya impossible changes dikhen to candidate ko reject/hold karo. Suspicion ko suspicion hi bolo; frame review se AI provenance prove nahi hoti. Questionable source ko final render me mat le jao.
5. **Har candidate pe 3 sawaal:**
   - **Setup dikhta hai?** — galti hone se **0.3–0.5 s pehle** shot shuru hona chahiye. Seedha impact se shuru = audience ko samajh nahi aata.
   - **Payoff dikhta hai?** — splash / landing / face. Impact ke baad clip **turant** khatam.
   - **Frame me rehta hai?** — 0.756 aspect crop ke andar action poora. Subject crop se bahar gaya = reject.
6. **Text/logo:** clip me burned-in text ho to (a) delogo se hatao, ya (b) reject. Delogo **source coords pe pehle, phir crop** (warna "outside of frame" error).
7. **Black frames:** source ke shuru/aant me black flash — 1 s sheet dekh ke start point aage badhao (is build me 0.0 s black tha → 1.80 s se).
8. **Variety:** 5 clips me 5 alag failure type — paani/slip, skates, cart, float, trampoline. Ek jaisa repeat nahi.

## 7.2 Rank kaise tay hota hai
- **5** = sabse halka laugh (skates — bas slip), **1** = sabse bada payoff (trampoline — chhat se chhalang, hoop ke andar).
- Rank **content** decide karta hai, clip ki position nahi. Position rule alag hai (7.3).

## 7.3 Play order ka logic
`3 → 5 → 2 → 4 → 1`
- 1 **last** — climax sabse aakhir me (payoff).
- 2 second-last **nahi** — warna climax telegraph ho jata.
- Beech me 3/5/4 shuffle — ladder upar-neeche hoti rehti hai, monotonous nahi lagta.

## 7.4 Chicken
- Chicken **4th aur 1st ke bich** — 4th ke payoff ke baad comic beat, 1st ke climax se pehle.
- Wahan **koi voice nahi** (na pehle, na baad) — sirf face + scream.

---

# 8. MATHS (locked)

**Frame:** 1920 = 360 (title band) + **1428** (clip) + 132 (bottom). Clip canvas 1080×1428 = **aspect 0.7563**.
Har cut isi aspect pe normalize hota hai (`crop` → `scale=1080:1428`) — 720/952, 634/839 = 0.756 ✓.

**Timeline:**
```
clip durations : 3.000 + 2.033 + 2.033 + 2.033 + 1.600 = 10.733 s
gaps (4 × 0.25) :                                1.000 s
chicken insert  :                                0.567 s
----------------------------------------------------------
total           :                               12.300 s
```
**Starts (measured, frame quantisation ±0.03 s):**
S = `0.000 · 3.250 · 5.5333 · 7.8166 · 10.699` (chicken = `10.132`)
Har start = pichli clip ka end + 0.25. Chicken = tube end (9.882) + 0.25.

**Voice placement:** cut se **−0.35 s**.
Voice file 0.780 s, usme ~0.19 s lead silence → speech ~0.59 s, jo cut ke aar-paar baithti hai (0.295 s pehle + 0.295 s baad).
→ `0.000 · 2.650 · 4.933 · 7.250`

**Music % → dB:** 25% = −24.0 dB RMS. `17% → −24 + 20·log10(17/25) = −24 − 3.36 = **−27.4 dB**`.

**Duck:** 0.15 amplitude = **−16.5 dB** dip (voice), 0.45 = −6.9 dB (chicken). Fade 80 ms in/out + 30 ms hanning smooth.

**Voice level:** −13 dB RMS vs bed −20 dB RMS = +7 dB nominal; measured window diff **12–22 dB** (clip ke loud hisson me zyada).

**Peak cap:** tanh(1.1) → phir −4.8 dBFS hard cap → measured peak −4.63 dB, rms −18.14, **−14.3 LUFS**.

**SFX timing (event pe, clip start se):** yeet +1.55 · oof +0.82 · ba_dum_tss +1.55 · slap +0.70 · fail +0.55 (chicken scream absolute 10.132).
Rule: SFX impact frame se **0–0.1 s** pehle/baad — visible action ke saath sync, warna "invented SFX" lagta hai.

---

# 9. SERIES / NAMING / DELIVERY (locked 24 Oct)

- **Series:** type 2 **epi 1, 2, 3…** → file `type2_ep1.mp4`, `type2_ep2.mp4` …
- **Sourcing order:** **YouTube → TikTok → Pexels → jahan best mile**.
- **Length (LOCKED ep3 ke baad):** total **15–20 s**, per clip **~2.8–3.4 s** (source window **≥3.6 s** taaki trim me kuch na kate), average **~3.0 s** target. Approach + action + payoff teeno dikhne chahiye.
- **5 clips max**, kam nahi (5 hi, jab tak sach me 5 achhe na milen).
- **Speed change nahi** — sirf trim, `speed 1.0` (bina puche setpts/speed nahi).
- **Voice hits = clips − 1** (5 clips → 4 hits; 4 clips → 3).
- **Chicken compulsory** har type-2 reel me, hamesha rank-1 clip se **turant pehle**.
- **Music:** C2 + 17% / −27.4 dB RMS **fixed** — naya track nahi.
- **Header:** reference reels se derive hua, fixed.
- **Upload:** anyone-with-link, viewer, discovery OFF; curl se size+md5 verify.

# 10. BUILD

```bash
cd ~/studio/type2
python3 build.py --ep 4 --source /abs/path/rc5_src.mp4 --out ~/dl/type2_ep4.mp4
```
Timing **plan ke numbers se nahi, video se** measure hoti hai (transition detect) —
isliye SFX/voice kabhi shift nahi hota.

# 11. Naya episode (checklist)

1. `python3 select.py <source>` → 1 s sheet, poora source dekho.
2. Clips cut karo: `crop` **content pe** (bars hatane ke liye), phir `scale=1080:1428`, `fps=30`, `setsar=1`.
3. `assets/` me daalo → `rc5_src.mp4` concat (`-f concat -c copy`, order = play order).
4. `config.json` ke `clips` (n, ss, dur, label, color, sfx) + `plan.json` update karo.
5. `python3 build.py --ep <n>` → sheet check → Drive upload → make_public → md5 verify.

# 12. Render ke fixed bugs (24 Oct, ep1)

- Clip **content-pe crop** hoke aata hai (`_fill`/`_clean` assets) — koi black side bar nahi.
- Ladder label ka **black outline** ab kaam karta hai (`\bordcolor` tag libass me border white kar deta tha → hataya).
- Trampoline clip fade-in ke baad se (ss 9.45) — dark frames nahi.
- Timing video se: gap detect + final cut detect; audio clip bed bhi `ss` se slice hota hai (lip/ambience sync).
