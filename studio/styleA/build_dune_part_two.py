#!/usr/bin/env python3
"""Build the shot-first Style 1 plan for Dune: Part Two.

Media stays outside Git. Every visual alias is a distinct shot, while aliases
that point to the same URL share the worker's content-addressed download cache.
"""
from __future__ import annotations

import json
from pathlib import Path

FPS = 30
ROOT = Path(__file__).resolve().parent
TRAILER = (
    "https://archive.org/download/dune-part-two-4k-trailer3-imax-x265/"
    "Dune%20Part%20Two%20%282024%29%204K%20Trailer%203%20IMAX%20-%20x265.mkv"
)
MOVIE = (
    "https://www.myndir.sv1.is/dune2/"
    "Dune.Part.Two.2024.720p.WEBRip.x264.AAC-LAMA.mp4"
)
SONG = (
    "https://archive.org/download/dune-part-two/2024.%20Dune%20Part%20Two/"
    "18.%20Southern%20Messiah.mp3"
)

# Verified source-shot boundaries in the official 4K trailer. The local proxy
# has identical timing. No title, logo, green-rating or credit-card segments
# are included below.
T3 = {
    2: (6.000, 8.750), 20: (27.833, 28.583), 21: (28.583, 29.208),
    24: (30.292, 30.875), 31: (39.042, 42.167), 40: (52.792, 56.458),
    49: (69.750, 70.292), 50: (70.292, 71.000), 51: (71.000, 72.458),
    52: (72.458, 74.542), 53: (74.542, 76.292), 56: (78.667, 80.208),
    57: (80.208, 81.750), 59: (83.042, 86.208), 60: (86.208, 87.208),
    61: (87.208, 88.250), 62: (88.250, 89.250), 63: (89.250, 91.667),
    65: (94.125, 95.542), 70: (102.583, 104.167), 74: (107.958, 109.708),
    75: (109.708, 110.458), 76: (110.458, 112.000), 79: (115.333, 116.083),
    80: (116.083, 116.750), 81: (116.750, 117.750), 85: (120.458, 121.792),
    100: (131.000, 132.625), 104: (134.542, 135.917),
    107: (137.125, 138.208), 108: (138.208, 139.208),
    109: (139.208, 140.583), 110: (140.583, 143.792),
}

# (alias, trailer segment, source start, exact output frames)
ACTION = [
    ("t3_02", 2, 6.15, 45),
    ("t3_31", 31, 39.20, 45),
    ("t3_40", 40, 53.00, 45),
    ("t3_59", 59, 83.20, 45),
    ("PEOPLE", None, 7693.50, 75),
    ("t3_52", 52, 72.60, 45),
    ("t3_53", 53, 74.65, 45),
    ("t3_57", 57, 80.22, 45),
    ("t3_56", 56, 78.68, 45),
    ("t3_76", 76, 110.47, 45),
    ("KNIFE", None, 8973.35, 105),
    ("t3_51", 51, 71.04, 42),
    ("t3_65", 65, 94.13, 42),
    ("t3_63", 63, 89.30, 48),
    ("t3_70", 70, 102.60, 45),
    ("t3_74", 74, 108.00, 45),
    ("t3_100", 100, 131.00, 48),
    ("PARADISE", None, 9359.75, 75),
    ("t3_104", 104, 134.60, 34),
    ("t3_109", 109, 139.25, 36),
    # Drop: frame 1000 / 33.333 s. Cut boundaries follow the measured beat grid.
    ("t3_20", 20, 27.85, 19),
    ("t3_21", 21, 28.60, 13),
    ("t3_24", 24, 30.32, 14),
    ("t3_50", 50, 70.32, 18),
    ("t3_49", 49, 69.77, 14),
    ("t3_60", 60, 86.25, 15),
    ("t3_61", 61, 87.25, 15),
    ("t3_62", 62, 88.30, 16),
    ("t3_75", 75, 109.72, 14),
    ("t3_79", 79, 115.35, 15),
    ("t3_80", 80, 116.10, 15),
    ("t3_81", 81, 116.78, 14),
    ("t3_85", 85, 120.50, 29),
    ("t3_107", 107, 137.15, 16),
    ("t3_108", 108, 138.25, 17),
    ("t3_110", 110, 140.65, 76),
]

DIALOGUE = {
    "PEOPLE": {
        "start_s": 7694.094,
        "dur_s": 1.55,
        "subtitle": "I'm fighting for my people.",
        "gain": 1.20,
    },
    "KNIFE": {
        "start_s": 8973.775,
        "dur_s": 3.05,
        "subtitle": "May thy knife chip and shatter.",
        "gain": 1.10,
    },
    "PARADISE": {
        "start_s": 9360.161,
        "dur_s": 2.05,
        "subtitle": "Lead them to Paradise.",
        "gain": 1.20,
    },
}


def build() -> dict:
    sources: dict[str, str] = {}
    cuts: list[dict] = []
    dialogue_events: list[dict] = []
    timeline_f = 0
    drop_f = None

    for index, (alias, segment, source_start, frames) in enumerate(ACTION):
        is_dialogue = alias in DIALOGUE
        locator = MOVIE if is_dialogue else TRAILER
        source_alias = f"movie_{alias.lower()}" if is_dialogue else alias
        sources[source_alias] = locator
        dur = frames / FPS
        if segment is not None:
            lo, hi = T3[segment]
            assert lo - 0.002 <= source_start < hi, (alias, source_start, lo, hi)
            assert source_start + dur <= hi + 0.002, (alias, source_start + dur, hi)
        cut = {
            "src": source_alias,
            "start_s": round(source_start, 6),
            "dur_s": round(dur, 6),
            "src_dur_s": round(dur, 6),
            "zoom_start": 1.02 if is_dialogue else 1.01,
            "zoom_end": 1.12 if is_dialogue else (1.08 if alias == "t3_110" else 1.06),
            "transition_in": "none",
            "shot_id": f"{index + 1:02d}_{source_alias}",
            "timeline_s": round(timeline_f / FPS, 6),
        }
        if timeline_f == 1000:
            drop_f = timeline_f
            cut["transition_in"] = "flash_white"
        elif timeline_f == 1019:
            cut["transition_in"] = "flash_white"
        cuts.append(cut)

        if is_dialogue:
            event = DIALOGUE[alias]
            offset = event["start_s"] - source_start
            assert 0 <= offset <= dur
            timeline = timeline_f / FPS + offset
            dialogue_events.append({
                "src": source_alias,
                "start_s": event["start_s"],
                "dur_s": event["dur_s"],
                "timeline_s": round(timeline, 6),
                "subtitle": event["subtitle"],
                "sub_t0": round(timeline + 0.04, 6),
                "sub_t1": round(timeline + event["dur_s"] - 0.04, 6),
                "gain": event["gain"],
            })
        timeline_f += frames

    assert drop_f == 1000
    assert timeline_f == 1320, timeline_f
    assert len(cuts) == 36
    assert len({cut["src"] for cut in cuts}) == 36
    return {
        "name": "styleA_dune_part_two_v1",
        "engine": "zohair_jigsaw",
        "song_path": SONG,
        "song_offset_s": 181.000,
        "total_s": 44.000,
        "drop_s": 33.333333,
        "beat_s": 0.511,
        "sources": sources,
        "visual_cuts": cuts,
        "dialogue_events": dialogue_events,
        "sfx_events": [],
        "outro_black_s": 0.0,
    }


def main() -> None:
    plan = build()
    out = ROOT / "plan_dune_part_two.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    job = {
        "plan_path": "studio/styleA/plan_dune_part_two.json",
        "out_name": "Dune_Part_Two_Style1_SouthernMessiah_9x16.mp4",
        "prebaked_dialogue": False,
    }
    (ROOT / "job_dune_part_two.json").write_text(
        json.dumps(job, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {out}: {len(plan['visual_cuts'])} cuts, {plan['total_s']:.3f}s")


if __name__ == "__main__":
    main()
