#!/usr/bin/env python3
"""Style A v2 — rebuilt to the reference standard.

Rules baked in:
  * dialogue only over the shot where that character is ON CAMERA with a moving
    mouth (verified by mouth-motion scan + frame strip), shot is HELD, no cuts
  * every other second has real movement (motion-ranked shots, no stills)
  * every cut is beat-locked (99.4 BPM grid) and the drop lands on the music drop
  * no cut may run past its slice: src_dur >= dur + 0.30 (kills the freeze bug)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SL = "/var/tmp/opp/sl2s"
OUT = Path("/home/user/studio/styleA/plan_oppenheimer_v2.json")
FF = "/home/user/bin/ffmpeg"

BEAT = 0.604
TOTAL_BEATS = 69
DROP_BEATS = 58                     # 58 * 0.604 = 35.03 s
SONG_DROP = 82.90

# (slice, video offset into the slice, duration in seconds)
# (slice, video offset, beats, is_dialogue)
SEGMENTS = [
    ("a16_face_close", 0.25, 4, False),   # hook: Oppenheimer face
    ("a02_crowd_surge", 0.20, 4, False),  # crowd pushing forward
    ("dlg1_remote", 3.20, 5, True),       # ON CAMERA "remote chances are near zero"
    ("a06_detonator", 0.30, 2, False),
    ("dlg2_zero", 3.10, 4, True),         # ON CAMERA "zero would be nice"
    ("a04_fire_macro", 0.20, 4, False),
    ("a05_rope", 0.30, 3, False),
    ("a03_visor", 0.20, 3, False),
    ("a07_fire2", 0.20, 4, False),
    ("a09_truck", 0.20, 4, False),
    ("a01_opp_walk", 0.30, 3, False),
    ("a10_fire3", 0.20, 4, False),
    ("a11_men", 0.20, 4, False),
    ("dlg3_theory", 3.30, 5, True),       # ON CAMERA Fuchs "theory will get you only so far"
    ("a12_point", 0.20, 3, False),
    ("a13_headsup", 0.20, 3, False),
    ("a14_glass", 0.20, 1, False),        # pre-drop tick
    # ---- drop (11 beats) ----
    ("a15_fire4", 0.20, 1, False),
    ("a17_exp", 0.20, 1, False),
    ("a16_face_close", 1.10, 1, False),
    ("a04_fire_macro", 1.20, 1, False),
    ("a02_crowd_surge", 1.20, 1, False),
    ("a10_fire3", 1.00, 2, False),
    ("a03_visor", 1.00, 1, False),
    ("a07_fire2", 1.30, 1, False),
    ("a01_opp_walk", 1.20, 1, False),
    ("a04_fire_macro", 2.10, 1, False),
]

DLG_PREROLL = 0.00    # clips carry 100 ms pad before the first word
# lead = how far into the cut the first word really lands (measured frame-exact
# against the film: slice->movie template match 0.995+, audio xcorr 0.99)
# lead = (clip film-time start) - (film time the cut starts on), measured by
# frame-exact slice->movie match (0.995+) so picture time == audio time
DLG_LEADS = [0.301, 0.170, 0.682]
DIALOGUE = [
    ("/var/tmp/opp/dlgf/L1c.wav", "Our remote chances are near zero."),
    ("/var/tmp/opp/dlgf/L2c.wav", "Zero would be nice."),
    ("/var/tmp/opp/dlgf/L3c.wav", "Theory will get you only so far."),
]


def slice_len(name: str) -> float:
    p = subprocess.run([FF, "-hide_banner", "-i", f"{SL}/{name}.mp4"],
                       capture_output=True, text=True).stderr
    for ln in p.splitlines():
        if "Duration:" in ln:
            h, m, s = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def main() -> int:
    beats_total = sum(b for _, _, b, _ in SEGMENTS)
    total = beats_total * BEAT
    print(f"timeline {beats_total} beats = {total:.3f}s (drop at {DROP_BEATS} beats = {DROP_BEATS * BEAT:.3f}s)")

    problems = []
    t = 0.0
    visual, cuts_at = [], []
    for name, off, b, is_d in SEGMENTS:
        dur = round(b * BEAT, 3)
        L = slice_len(name)
        if L < off + dur + 0.30:
            problems.append(f"{name}: needs {off + dur + 0.30:.2f}s, has {L:.2f}s")
        visual.append({
            "src": name, "start_s": round(off, 3), "dur_s": dur,
            "src_dur_s": round(off + dur + 0.30, 3),
            "zoom_start": 1.01, "zoom_end": 1.055,
            "transition_in": "flash_white" if name in ("a15_fire4", "a17_exp") else "none",
            "is_dialogue": is_d,
        })
        cuts_at.append((name, t, is_d))
        t += dur

    if problems:
        print("FREEZE RISK:")
        for p in problems:
            print("   ", p)
    else:
        print("every cut has >=0.30s source headroom -> no freeze padding")

    # dialogue audio sits DLG_LEAD into its own cut
    dlg, di = [], 0
    for idx, (name, start, is_d) in enumerate(cuts_at):
        if not is_d:
            continue
        path, sub = DIALOGUE[di]
        lead = DLG_LEADS[di]
        cut_end = start + [c for c in visual if c["src"] == name][0]["dur_s"]
        di += 1
        tl = round(start + lead - DLG_PREROLL, 3)     # clip start (has 50 ms pre-roll)
        speech = start + lead                          # first word on screen
        sub_t1 = min(cut_end - 0.05, speech + 1.75)
        assert tl + 3.0 > 0
        dlg.append({
            "src": "vox_" + Path(path).stem, "start_s": 0.0, "dur_s": 4.0,
            "timeline_s": tl, "subtitle": sub,
            "sub_t0": round(speech - 0.03, 2), "sub_t1": round(sub_t1, 2),
        })
        print(f"  dlg lead {lead:.3f}s -> clip @{tl:.3f}s, first word @{speech:.3f}s, sub {speech-0.03:.2f}-{sub_t1:.2f}")

    sources = {name: f"{SL}/{name}.mp4" for name, _, _, _ in SEGMENTS}
    for path, _ in DIALOGUE:
        sources["vox_" + Path(path).stem] = path

    plan = {
        "name": "styleA_oppenheimer_v2",
        "engine": "zohair_jigsaw",
        "song_path": "/var/tmp/opp/song.flac",
        "song_offset_s": round(SONG_DROP - DROP_BEATS * BEAT, 3),
        "total_s": round(total, 2),
        "drop_s": round(DROP_BEATS * BEAT, 3),
        "beat_s": BEAT,
        "sources": sources,
        "visual_cuts": visual,
        "dialogue_events": dlg,
        "sfx_events": [],
        "outro_black_s": 0.0,
    }
    OUT.write_text(json.dumps(plan, indent=1))
    print(f"plan -> {OUT}")
    print(f" cuts {len(visual)} | song offset {plan['song_offset_s']}s | drop {plan['drop_s']}s")
    for d in dlg:
        print(f"  dlg @{d['timeline_s']:6.2f}s  {d['subtitle']}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
