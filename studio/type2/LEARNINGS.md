# LEARNINGS — clip selection skill (PORTABLE, har type pe)

> Ye **soch** hai, formula nahi. Type-2 ke numbers (5 clips, 15–20 s, 0.756 aspect, 3-5-2-4-1)
> sirf type-2 ke liye hain. Type 3 aayega to numbers naye honge — ye soch wahi rahegi.

## Kaam karta hai
1. **Poora source pehle dekho** (1 s sheet), phir clip chuno. Aadha dekh ke cut karna = galat clip.
2. **Setup → impact → payoff** ka teen-second rule: galti se **0.3–0.5 s pehle** shot shuru, impact ke baad turant cut.
3. **Frame test:** action crop ke andar rehna chahiye, poora. Subject bahar gaya = reject.
4. **Text/logo test:** hata sakte ho (delogo/crop) to rakho, warna reject. Delogo **source coords pe pehle**, phir crop — warna "outside of frame".
5. **Black frame test:** source ke shuru me black flash ho to start aage badhao.
6. **Variety:** ek reel me ek jaisa fail repeat na ho; har clip ka apna maza.
7. **Rank content se** (kitna bada laugh), **position rule se** (kab dikhana hai).
8. **SFX clip dekh ke** — jo event dikh raha hai uska hi sound, impact se 0–0.1 s ke andar.
9. **Ek clip pe atko mat** — 4 try ke baad bhi na mile to agla moment dekho. (5th clip pe 4 try lage the.)

## Galtiyan jo ho chuki hain (dobara nahi)
- 4-clip shortcut jab 5 achhe clip mil sakte hain. — **5 hi, jab tak sach me na milen.**
- Chicken wale range (12–25 s) me golf/tube dhundhna — pehle range blacklist karo.
- Plan ke `items` me labels play-order se bhar dena (rank vs appearance confuse).
- Audio timing plan ke numbers se lena — **video se measure karo** (black gap detect). Warna SFX 0.2 s shift.
- Delogo box galat jagah (AFV logo x≈765–945, y≈0–80) — har baar frame nikaal ke box confirm karo.
- Pillarboxed source clip (golf 142–939, tube 79–1003, tramp 70–983) — final me bars dikhte hain.
  **Naya clip cut karte waqt `crop` content pe hi lagao, phir `scale`.**

## Tool
- `python3 select.py <source>` — 1 s sheet, poora source ek nazar me.

## 24 Oct — render ke do jaal (dono pakde gaye)
1. **Black side bars:** source clip pillarboxed ho (golf 142–939, tube 79–1003, tramp 70–983) to
   `fit=crop` kuch nahi karta — bars output me aa hi jate hain. Fix: asset banate waqt hi
   `crop=<w>:<h>:x:y` content pe lagao (h = w/0.7563, warna stretch), phir `scale=1080:1428`.
   Tube me AFV logo top par tha → crop ke top 103 px se apne aap nikal gaya (delogo se ghost bachta hai).
2. **White label white sky par gayab:** libass me `\bordcolor&H000000&` tag border ko override kar deta hai
   (border white ho jata hai). Fix: `\bordcolor` **hata do**, sirf `\3c&H000000&\3a&H00&` rakho.
   Style line me OutlineColour bhi valid colour hona chahiye (`&H00000000`), `9`/`8` jaisa number nahi.
3. **Fade-in wala clip** (tramp ka pehla 0.3 s dark) — ss 0.25–0.3 s aage badhao, warna rank-1 payoff
   andhera dikhta hai.

## 26 Oct — ep6 me pakde gaye do bade jaal (dono ne build galat kiya)

1. **`run.py` ko plan ka `order` field chahiye.** `plan.json` ke `items` **rank order me** (n=1..5,
   index 0..4) hone chahiye, aur play sequence `"order": [...]` se di jati hai — index ki list.
   ep6 me `order = [2,4,1,3,0]` → play 3→5→2→4→1. Items ko play order me rakh dene se list ulti
   ho jati hai (chart me "3,5,2,4,1" dikhta hai par screen pe galat clip aata hai) **aur** `ss`
   bhi galat clip pe lag jata hai — dono mil ke "clip/label mismatch" jaisa dikhta hai.
2. **Segment cache kaamback — `s.src` full path signature me hai, lekin har episode ka concat
   `.../epN/rc5_src.mp4` hota hai, isliye basename-level path same nahi par agar kisi bhi wajah se
   same path + same (ss,dur) ho to purana segment utha liya jata hai.** ep5 ke segments ep6 me
   ghus gaye the (clips ke numbers bhi ep5 ke). Fix: build se pehle
   `rm -rf ~/studio/work/segs/*` — regenerable hai (analysis json cache alag rehta hai, wo delete na karo).
   **Lakshan:** sheet me clips badalte nahi, aur sheet ka size har build me same rehta hai.

3. QA shortcut jo har build ke baad chalana hai (ek hi pass me sab):
   voice 4 hits NCC > 0.95, chicken zone me voice NCC < 0.3, scream @ chicken > 0.8,
   5 SFX offset ±0 ms, LUFS −14.2..−14.4, peak < −4.5 dBFS.

## 27 Oct — EP7 taste/profile corrections (standing)
- Bike footage means **road-circuit sportbike/MotoGP racing only**; reject motocross, dirt, enduro, trail, mud riding, and paddock/garage tip-overs when the brief is on-track falls.
- For source audio, background music must be **only the series-selected/generated Type-2 track**. Remove source songs; if vocals/lyrics remain or separation is not clean, mute the entire source audio or reject/replace that clip. Keep natural speech/laughter only when it is clearly separated from the song. Do not claim a listening check unless one actually happened.
- Screen the actual cut windows after crop, not just the full source. In particular, start before the impact and ensure the crash/fall itself is visible; an aftermath-only shot is a weaker pick.
- Avoid severe injury/gore. Use only clips whose visible fall is not medically graphic.
- Standalone and non-bike fail moments should feel distinct in *action/setting*; avoid two near-identical gym clips if a varied clean candidate is available.
