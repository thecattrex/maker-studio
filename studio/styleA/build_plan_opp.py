#!/usr/bin/env python3
"""Build the Style A (zohair jigsaw) plan for Oppenheimer x Can You Hear The Music.

Structure
  0.00 – 33.85  build (ticking keyboard + soft strings), slow cuts, 4 jigsaw lines
  33.85 – 40.53 drop: 0.75s machine-gun bursts through the Trinity fireball
Music window: song 59.0s -> 99.5s (the melody section before the 100s tail).
"""
from __future__ import annotations

import json
from pathlib import Path

SL = "/var/tmp/opp/sl"
OUT = Path("/home/user/studio/styleA/plan_oppenheimer.json")
FPS = 30

# (src, src_start, source-duration, note)
CUTS_LIST = [
    ("s04_tower",  0.30, 2.6, "tower against sky"),
    ("s01_desert", 0.30, 2.6, "men at table / desert"),
    ("s06_equip",  0.30, 2.6, "getting equipment ready"),
    ("s08_climb",  0.10, 2.2, "climbing the tower"),
    ("s03_tent",   0.30, 2.2, "tent, Oppenheimer sitting"),
    ("s10_places", 0.30, 2.2, "everybody take your places"),
    ("s05_kitty",  0.30, 2.2, "Kitty watching"),
    ("s02_opp",    0.30, 2.2, "Oppenheimer close-up"),
    ("s07_oppeq",  0.30, 2.4, "Oppenheimer with equipment"),
    ("s19_cheer",  0.30, 2.4, "crowd cheering"),
    ("s20_wide",   0.30, 2.4, "wide camp"),
    ("s18_crowd",  0.30, 2.4, "crowd behind glass"),
    ("s19_cheer",  1.30, 2.0, "crowd cheering (bright beat)"),
    ("s03_tent",   0.90, 2.0, "tent again (new frame)"),
    ("s07_oppeq",  1.20, 2.0, "equipment b-roll"),
    ("s02_opp",    1.10, 2.0, "close-up hold"),
    ("s12_flash",  0.00, 0.75, "first flash"),
    ("s21_ball",   0.10, 0.75, "fireball"),
    ("s15_face",   0.10, 0.75, "face lit orange"),
    ("s22_rise",   0.10, 1.50, "cloud rising"),
    ("s14_col",    0.60, 0.75, "fire column (bright)"),
    ("s14_col",    0.10, 0.75, "fire column"),
    ("s16_eyes",   0.10, 0.75, "eyes behind glass"),
    ("s19_cheer",  0.60, 1.50, "cheering"),
    ("s23_ball2",  0.10, 1.50, "fireball two"),
    ("s22_rise",   1.60, 0.75, "cloud rising (end hold)"),
]

# jigsaw dialogue: (timeline_s, dlg key, subtitle, sub_start_extra)
DIALOGUE = [
    (4.85,  "d1", "Theory will get you only so far.", 0.0),
    (8.95,  "d2", "Setting fire to the atmosphere.", 0.0),
    (14.45, "d3", "And we destroy the world?", 0.0),
    (32.20, "d4", "And we have won.", 0.0),
]

DROP_SONG_T = 82.90        # measured +4 dB jump here (song drop)
SONG_OFFSET = 0.0          # computed below: drop_song_t - DROP_AT
BEAT = 0.604             # measured 99.4 BPM
BUILD_BEATS = [4, 4, 3, 3, 4, 3, 4, 3, 4, 4, 3, 4, 4, 3, 4, 4]   # 56 beats
BURST_BEATS = [1, 1, 1, 1, 1, 2, 1, 1, 1, 1]                     # 11 beats
DROP_AT = round(sum(BUILD_BEATS) * BEAT, 3)
TOTAL_TARGET = round((sum(BUILD_BEATS) + sum(BURST_BEATS)) * BEAT, 3)


# curated build order (src, src_start) — hook first, no two similar shots adjacent
BUILD_ORDER = [
    ("s02_opp", 0.30), ("s10_places", 0.30), ("s19_cheer", 0.30), ("s01_desert", 0.30),
    ("s03_tent", 0.30), ("s05_kitty", 0.30), ("s08_climb", 0.10), ("s20_wide", 0.30),
    ("s18_crowd", 0.30), ("s04_tower", 0.30), ("s07_oppeq", 0.30), ("s19_cheer", 1.30),
    ("s06_equip", 0.60), ("s04_tower", 1.20), ("s09_wind", 0.20), ("s08_climb", 1.10),
]
BUILD = [(src, st, 2.0, "") for src, st in BUILD_ORDER]
BURST = [c for c in CUTS_LIST if c[2] <= 1.5][:len(BURST_BEATS)]


def main() -> int:
    total_beats = sum(BUILD_BEATS) + sum(BURST_BEATS)
    visual = []
    for i, (src, s0, _dur, note) in enumerate(BUILD):
        visual.append({
            "src": src, "start_s": s0, "dur_s": round(BUILD_BEATS[i] * BEAT, 3),
            "zoom_start": 1.01, "zoom_end": 1.06,
            "transition_in": "none", "note": note,
        })
    for i, (src, s0, _dur, note) in enumerate(BURST):
        d = round(BURST_BEATS[i] * BEAT, 3)
        visual.append({
            "src": src, "start_s": s0, "dur_s": d, "src_dur_s": round(s0 + d + 0.10, 3),
            "zoom_start": 1.02, "zoom_end": 1.09,
            "transition_in": "flash_white" if i in (0, 3, 6, 9) else "none",
            "note": note,
        })

    total = round(sum(v["dur_s"] for v in visual), 2)
    assert all(v["dur_s"] > 0.2 for v in visual), "negative/too-short cut"

    dlg = []
    for tl, key, sub, _x in DIALOGUE:
        dlg.append({
            "src": "dlg_" + key, "start_s": 0.0, "dur_s": 4.0,
            "timeline_s": tl, "subtitle": sub,
            "sub_t0": round(tl - 0.05, 2), "sub_t1": round(tl + 2.55, 2),
        })

    sources = {f"dlg_{k}": f"/var/tmp/opp/dlgf/{k}.wav" for k in ("d1", "d2", "d3", "d4")}
    for name in {c[0] for c in CUTS_LIST} | {c[0] for c in BUILD} | {c[0] for c in BURST}:
        sources[name] = f"{SL}/{name}.mp4"

    song_offset = round(DROP_SONG_T - DROP_AT, 3)
    plan = {
        "name": "styleA_oppenheimer_canyouhear",
        "engine": "zohair_jigsaw",
        "song_path": "/var/tmp/opp/song.flac",
        "song_offset_s": song_offset, "drop_song_t": DROP_SONG_T,
        "total_s": total, "drop_s": DROP_AT, "beat_s": BEAT,
        "sources": sources, "visual_cuts": visual, "dialogue_events": dlg,
        "sfx_events": [], "outro_black_s": 0.0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, indent=1))
    print(f"plan -> {OUT}\n total={total}s ({total_beats} beats) drop={DROP_AT}s song_offset={song_offset}s")
    print(f" cuts build={len(BUILD)} burst={len(BURST)}")
    for d in dlg:
        print(f"  dlg {d['src']:8s} @{d['timeline_s']:6.2f}s  \"{d['subtitle']}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
