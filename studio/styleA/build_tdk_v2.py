#!/usr/bin/env python3
"""The Dark Knight — Style A v2 (beat-locked, no-freeze, no credits, monologue ending).

Measured basis
--------------
* ONE song, ONE continuous piece: "A Dark Knight" 866.00 -> 910.00 s (total 44.0 s).
  42 major + 52 minor onsets detected in that window; longest major-ononset gap
  inside the cut region is 5.0 s (25.16 -> 30.15) and it sits under a dialogue
  pocket, so no 8.8 s stretch ever plays without percussion.
* zohair grammar: ~1.2 s holds + 3-frame (0.10 s) rolls; every cut lands on a
  measured onset (or inside a deliberate 3-frame roll run-up).
* every intense line: pull-back before -> thin on the line -> music ANSWERS on
  the first real onset after the last word (hit + cut + flash).
* dialogue only on on-camera speaking shots; visual film-time is pinned to the
  voice film-time at every cut (no drift), voice + caption same time.
* "a dark knight" is VO over a non-speaking tunnel shot in the film -> delivered
  as the closing title slam on the final music hit (42.65 s).
* zero credit frames: last film image = 8665.3 s; credits roll starts ~8687 s.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/tdk/orig.mp4"
SONG = "/var/tmp/tdk/song.wav"
SL = Path("/var/tmp/tdk/sl2")
DL = Path("/var/tmp/tdk/dlg2")
OUT = Path("/home/user/studio/styleA/plan_tdk_v2.json")
SONG_OFFSET = 866.0
FPS = 30
W_M, H_M = 96, 40

# film in / timeline in / subtitle / per-line trim
LINES = [
    ("d1", 4293.80, 4297.45, 2.85, "The night is darkest just before the dawn.", 1.12),
    ("d2", 2602.30, 2606.80, 27.75, "People will die. Starting tonight.", 1.34),
    ("d3", 5280.50, 5282.80, 32.75, "I don't want to kill you.", 1.06),
    ("g2", 8659.48, 8661.55, 39.38, "A watchful protector.", 1.52),
]
# slice start (film s) of the clip each line's visual is cut from
SLICE_IN = {"d1": 4290.00, "d2": 2599.30, "d3": 5278.60, "g2": 8659.00}

# cut table: start frame, source, in-point inside that source slice, role
# (role: line | line2 | hold | roll | final)
CUTS = [
    # A. cold open — onsets 0.13 / 1.41 / 2.03 / 2.34 / 2.64
    (0,    "a02_cont",      0.30, "hold",  "Batman on the ledge (open)"),
    (42,   "a03_jstreet",   0.30, "hold",  "Dent podium, daylight"),
    (61,   "e01_joker_int", 0.30, "hold",  "Joker interrogation close"),
    (70,   "a15_ambush",    0.30, "roll",  "press scrum"),
    (73,   "b07_boom",      0.30, "roll",  "truck flip fire"),
    (76,   "g2_tunnel",     0.30, "roll",  "Batpod, lit tunnel"),
    # B. DENT LINE — voice 2.85-6.50
    (79,   "d1_vis_a",      0.00, "line",  "LINE 1 wide, pull-back"),
    (147,  "d1_vis_b",      0.00, "line2", "LINE 1 punch-in"),
    # C. montage — onsets 7.63 / 8.91 / 10.14 / 11.41 / 12.65
    (229,  "a08_crowd",     0.30, "hold",  "Dent, office window"),
    (267,  "a10_parade",    0.30, "hold",  "veterans parade"),
    (304,  "a13_fight3",    0.30, "hold",  "Batman on the fire escape (real motion)"),
    (342,  "a12_swat",      0.30, "hold",  "SWAT street"),
    (380,  "a14_monitors",  0.30, "hold",  "surveillance wall"),
    (417,  "a05_heist",     0.30, "hold",  "bank interior"),
    (455,  "a07_press",     0.30, "roll",  "press pack"),
    (473,  "e02_batman",    0.30, "roll",  "Batman rising"),
    (492,  "b01_blast",     0.30, "hold",  "fire"),
    # D. burst roll — onsets 17.64 / 18.26 / 18.91 / 19.52 / 20.15 / 20.93
    (529,  "b02_flip",      0.30, "roll",  "tunnel structure"),
    (548,  "b06_truck",     0.30, "roll",  "truck"),
    (567,  "b08_slam",      0.30, "roll",  "slam"),
    (586,  "b09_ram",       0.30, "roll",  "ram"),
    (605,  "b10_hit",       0.30, "roll",  "hit"),
    (618,  "b11_tumble",    0.30, "roll",  "3f"),
    (621,  "b12_dust",      0.30, "roll",  "3f"),
    (624,  "a04_mob",       0.30, "roll",  "4f into the hit"),
    (628,  "c07_daylight",  0.30, "hold",  "ANSWER: street crowd"),
    # E. montage on the 22.63-27.67 onsets (22.63 / 23.73 / 25.17)
    (679,  "a09_gala",      0.30, "hold",  "Lucius at the desk"),
    (712,  "c01_crowd",     0.30, "hold",  "shouting crowd"),
    (755,  "e04_crowd",     0.30, "hold",  "evacuation hall"),
    # F. JOKER TV LINE on the empty 27.65-32.64 stretch — voice 27.75-32.37
    (830,  "d2_vis_a",      0.00, "line",  "LINE 2 GCN broadcast"),
    (905,  "d2_vis_b",      0.00, "line2", "LINE 2 punch-in"),
    # G. JOKER LINE 3 — voice 32.75-35.05
    (979,  "d3_vis",        0.00, "line",  "LINE 3 I don't want to kill you"),
    # H. ANSWER roll on the 901-908 cluster (35.15 / 36.40 / 36.73 / 37.03 / 37.35 / 37.63)
    (1055, "b03_blast2",    0.30, "roll",  "answer slam"),
    (1092, "b05_crane",     0.30, "roll",  "answer"),
    (1102, "c02_man",       0.30, "roll",  "answer"),
    (1111, "b04_crash",     0.05, "roll",  "answer flash"),
    (1121, "c06_fall",      0.30, "roll",  "answer"),
    (1129, "b07_boom",      1.20, "roll",  "answer"),
    (1148, "b11_tumble",    1.50, "roll",  "answer"),
    # I. GORDON ON CAMERA — film 8659.00-8661.50, voice "A watchful protector" 8659.56
    (1167, "g1_face",       0.00, "line",  "Gordon close (LINE 4, part 1)"),
    (1204, "g1_face_b",     0.00, "line2", "Gordon close, punch-in on the 40.14 hit"),
    (1242, "b08_slam",      1.50, "roll",  "answer after the line"),
    (1261, "g2b_ram",       0.30, "roll",  "answer"),
    (1280, "g2_tunnel",     0.20, "final", "Batpod in the tunnel + 'A dark knight.'"),
]

# visual name -> actual slice file on disk
FILE = {"d1_vis_a": "d1_dent", "d1_vis_b": "d1_dent", "d2_vis_a": "d2_tv", "d2_vis_b": "d2_tv",
        "d3_vis": "d3_jok", "g2b_ram": "b09_ram", "g1_face_b": "g1_face"}

ZOOM = {
    "line":  (1.11, 1.03),   # pull-back before the line
    "line2": (1.02, 1.10),   # thin push on / after the line
    "hold":  (1.08, 1.02),
    "hold2": (1.02, 1.08),
    "roll":  (1.00, 1.03),
    "final": (1.04, 1.12),
}


def motion_of(path: str, t0: float, dur: float) -> float:
    raw = subprocess.run(
        [FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{max(0.12, dur):.3f}", "-i", path,
         "-vf", f"scale={W_M}:{H_M},format=gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (W_M * H_M)
    if n < 2:
        return 99.0
    f = np.frombuffer(raw[: n * W_M * H_M], np.uint8).reshape(n, H_M, W_M).astype(np.float32)
    return float(np.abs(np.diff(f, axis=0)).mean())


def main() -> int:
    DL.mkdir(parents=True, exist_ok=True)
    # --- voice over the film's own audio, then pre-baked once per line
    dlg, problems = [], []
    for tag, s0, s1, tl, sub, gain in LINES:
        clip_in = round(s0 - 0.12, 3)
        clip_dur = round((s1 + 0.12) - clip_in, 3)
        wav = DL / f"{tag}.wav"
        subprocess.run(
            [FF, "-y", "-v", "error", "-ss", f"{clip_in:.3f}", "-t", f"{clip_dur:.3f}", "-i", SRC,
             "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=58:width_type=q:w=0.7,lowpass=f=15000,"
                    "equalizer=f=2500:width_type=o:w=1.2:g=3,"
                    "acompressor=threshold=-20dB:ratio=3:attack=5:release=140:makeup=6dB",
             "-ar", "44100", "-ac", "1", str(wav)], check=True)
        a, sr = sf.read(wav, dtype="float32")
        a = a.astype("float64")
        a *= 0.80 / (float(np.max(np.abs(a))) + 1e-9)
        knee, head = 0.66, 0.92
        ov = np.abs(a) > knee
        a[ov] = np.sign(a[ov]) * (knee + (head - knee) * np.tanh((np.abs(a[ov]) - knee) / (head - knee)))
        fn = int(0.02 * sr)
        r = np.linspace(0, 1, fn)
        a[:fn] *= r
        a[-fn:] *= r[::-1]
        sf.write(wav, np.stack([a, a], 1).astype("float32"), sr, subtype="PCM_16")
        dlg.append({"tag": tag, "wav": str(wav), "dur": clip_dur,
                    "tl": round(tl - 0.12, 3), "sub": sub, "gain": gain})
        print(f"  {tag}: film {clip_in:.2f}-{s1+0.12:.2f} ({clip_dur:.2f}s) -> voice@{tl:.2f}")

    # --- per-line visual slices (film time pinned to the voice at every cut)
    dmap = {d["tag"]: d for d in dlg}
    line_vis = {"d1_vis_a": ("d1", 79), "d1_vis_b": ("d1", 147),
                "d2_vis_a": ("d2", 830), "d2_vis_b": ("d2", 905),
                "d3_vis": ("d3", 979), "g1_face": ("g2", 1167), "g1_face_b": ("g2", 1204)}
    vis_in: dict[str, float] = {}
    for name, (tag, f0) in line_vis.items():
        T_c = f0 / FPS
        T_l = dmap[tag]["tl"] + 0.12          # film time of s0 == timeline of s0
        F_l = [L for L in LINES if L[0] == tag][0][1]
        vis_in[name] = round((F_l - SLICE_IN[tag]) - (T_l - T_c), 4)
        print(f"  {name}: film@cut {SLICE_IN[tag]+vis_in[name]:.3f}s  in-slice {vis_in[name]:.3f}")

    cuts, sources = [], {}
    n = len(CUTS)
    hold_flip = 0
    for i, (f0, name, s_in, role, note) in enumerate(CUTS):
        f1 = CUTS[i + 1][0] if i + 1 < n else 1320
        dur = (f1 - f0) / FPS
        if name in vis_in:
            s_in = max(0.0, vis_in[name])
        z0, z1 = ZOOM[role if role != "hold" else ("hold" if hold_flip % 2 == 0 else "hold2")]
        # dialogue shots: pull-back into the line -> clear punch-in on the beat
        if name == "d1_vis_a":
            z0, z1 = (1.22, 1.06)
        if name == "d1_vis_b":
            z0, z1 = (1.30, 1.42)
        if name == "d2_vis_a":
            z0, z1 = (1.16, 1.04)
        if name == "d2_vis_b":
            z0, z1 = (1.26, 1.36)
        if name == "d3_vis":
            z0, z1 = (1.14, 1.02)
        if name == "g1_face":           # small pull/push; a real push is baked in
            z0, z1 = (1.00, 1.03)
        if name == "g1_face_b":         # punch-in must read as a new angle
            z0, z1 = (1.22, 1.34)
        if role == "hold":
            hold_flip += 1
        head = 0.20 if dur > 0.14 else 0.12
        src_dur = round(dur + head, 3)   # engine reads from start_s for src_dur s
        p = str(SL / f"{FILE.get(name, name)}.mp4")
        if not Path(p).exists():
            problems.append(f"missing slice {p}")
            continue
        mom = motion_of(p, s_in, dur)
        cuts.append({"src": name, "start_s": round(s_in, 3), "dur_s": round(dur, 4),
                     "src_dur_s": src_dur, "zoom_start": z0, "zoom_end": z1,
                     "src_motion": round(mom, 3), "transition_in": "none"})
        sources[name] = p
        if mom < 0.30 and dur > 0.2:
            problems.append(f"low motion {name}: {mom:.2f}")
        if src_dur > 6.4:
            problems.append(f"{name}: src_dur {src_dur} may exceed slice")
    for f0, name in ((529, "b02_flip"), (1055, "b03_blast2"), (1280, "g2_tunnel")):
        for i, (cf, cname, *_r) in enumerate(CUTS):
            if cf == f0:
                cuts[i]["transition_in"] = "flash_white"

    for d in dlg:
        sources["vox_" + d["tag"]] = d["wav"]
    ev = [{"src": "vox_" + d["tag"], "start_s": 0.0, "dur_s": d["dur"], "timeline_s": d["tl"],
           "subtitle": d["sub"], "sub_t0": round(d["tl"] + 0.22, 2),
           "sub_t1": round(d["tl"] + d["dur"] - 0.06, 2), "gain": d["gain"]} for d in dlg]
    cap = DL / "cap.wav"
    sf.write(cap, np.zeros((int(1.9 * 44100), 2), dtype="float32"), 44100, subtype="PCM_16")
    sources["vox_cap"] = str(cap)
    ev.append({"src": "vox_cap", "start_s": 0.0, "dur_s": 1.9, "timeline_s": 42.55,
               "subtitle": "A dark knight.", "sub_t0": 42.72, "sub_t1": 43.96, "gain": 1.0})

    total_s = sum(c["dur_s"] for c in cuts)
    plan = {"name": "styleA_tdk_joker_v2", "engine": "zohair_jigsaw", "song_path": SONG,
            "song_offset_s": SONG_OFFSET, "total_s": round(total_s, 3), "drop_s": 35.15,
            "beat_s": 0.3125, "sources": sources, "visual_cuts": cuts,
            "dialogue_events": ev, "sfx_events": [], "outro_black_s": 0.0}
    OUT.write_text(json.dumps(plan, indent=1))
    b = [c["dur_s"] for c in cuts]
    print(f"cuts={len(cuts)} total={total_s:.3f}s  song {SONG_OFFSET:.2f}-{SONG_OFFSET+total_s:.2f}")
    print("dur hist: 3f=%d  <0.25s=%d  0.25-1.0=%d  1.0-1.5=%d  >1.5=%d" % (
        sum(1 for x in b if abs(x - 0.1) < 1e-6), sum(1 for x in b if 0.12 < x < 0.25),
        sum(1 for x in b if 0.25 <= x < 1.0), sum(1 for x in b if 1.0 <= x <= 1.5),
        sum(1 for x in b if x > 1.5)))
    print("PROBLEMS:" if problems else "no problems")
    for p in problems:
        print("  ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
