# type2 — ek command wala reel builder

```
python3 build.py --ep 1        # -> ~/dl/type2_ep1.mp4
```

Pipeline: **render base → timing detect (video se) → chicken insert → mix → mux → QA sheet**

| file | kya |
|---|---|
| `config.json` | saare numbers: frame, gap, ladder, clips (ss/dur/label/color/sfx), music, voice, chicken, levels |
| `build.py` | poora pipeline + timing auto-detect + QA (sheet, LUFS, transitions) |
| `mix.py` | audio: clip bed → music 17% → SFX → chicken scream → duck → voice 4× → master |
| `scan.py` | source scan: 1 s thumbnail sheet |
| `plan.json` | renderer plan (items appearance order me) |
| `assets/` | 5 clips (+ `_fill`/`_clean` versions), `rc5_src.mp4`, music `c2_48.wav`, scream |
| `TYPE2_SPEC.md` | locked spec (visual, audio, maths, selection) |
| `LEARNINGS.md` | selection skill — **portable, type 3 pe bhi lagegi** |

## Naya episode
1. Clips chuno (`scan.py` se source dekho), `assets/` me daalo, `rc5_src.mp4` concat karo.
2. `config.json` me clips/labels/ss update karo, `plan.json` regenerate.
3. `python3 build.py --ep <n>`
4. Drive: upload → `make_public` (reader, discovery off) → curl se size+md5 verify → user ko link.

## Naming
`type2_ep1.mp4`, `type2_ep2.mp4`, ... (series: type2 epi 1,2,3…)
