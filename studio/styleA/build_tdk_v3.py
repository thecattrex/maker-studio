#!/usr/bin/env python3
"""The Dark Knight — Style A v3.

Changes vs v2, all measured
--------------------------
* SONG: Interstellar — "Mountains" (Hans Zimmer), 84.00 -> 128.00 s, ONE continuous
  piece. Why: "A Dark Knight" 866-910 had 5.2 dB low-end dynamics / +0.9 dB build
  (flat). Mountains 84-128 = quiet ticking build (tick density 5 -> 10/s, hi-band
  -50 -> -37 dB) into the big drop at 122.0 s (= 38.0 s in our timeline).
* SHOTS: Joker-centred. Every shot is either the Joker himself or a silent
  action/reverse shot. NO muted talking faces (v2 had 6 of them: 7.63 / 10.13 /
  13.90 / 20.93 / 23.73-27.67 s and a non-speaking Gordon CU).
* DIALOGUE: only Joker lines that are spoken ON CAMERA (mouth motion measured
  frame-by-frame: party shot mouth-diff med 17.9, interrogation 8.9-18.5,
  "not a monster" 10.0). Gordon's VO line is gone.
* ENDING: built from his own lines - "You complete me." (interrogation) and
  "I'm not a monster." (just before Batman slams him), then the fight cut to the
  big drop + his laughing face on the last hit.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/tdk/orig.mp4"
SONG = "/var/tmp/tdk/mountains.wav"
SL = Path("/var/tmp/tdk/sl3")
DL = Path("/var/tmp/tdk/dlg3")
OUT = Path("/home/user/studio/styleA/plan_tdk_v3.json")
SONG_OFFSET = 84.0
FPS = 30
W_M, H_M = 96, 40

# slice start (film seconds) for every clip used below
SLICE_IN = {"party_wide": 3043.0, "party_scars": 3046.5, "party_arrive": 3009.0,
            "walk": 1567.0, "host": 8050.0, "host_bat": 8055.0, "street": 6376.0,
            "mcu_joker": 5274.0, "mcu_d": 5337.0, "mcu_fight": 5343.5}

# dialogue lines: tag, film start/end of the spoken words, gain, caption
LINES = [
    ("v1", 3047.30, 3048.08, 1.15, "Is it the scars?"),
    ("v2", 3050.32, 3051.46, 1.15, "You want to know how I got them?"),
    ("v3", 5274.36, 5276.90, 1.15, "You've changed things. Forever."),
    ("v4", 5280.60, 5282.60, 1.15, "I don't want to kill you."),
    ("v5", 5283.40, 5285.00, 1.15, "What would I do without you?"),
    ("v6", 5337.80, 5339.20, 1.20, "I'm not a monster."),
]

# cut table: cut time is snapped to the nearest measured onset afterwards.
# (target_t, slice, in-point inside the slice)
CUTS = [
    (0.00,  "walk",         0.30),
    (0.83,  "party_arrive", 0.30),
    (1.46,  "party_wide",   0.30),
    (2.09,  "host",         0.30),
    (2.72,  "party_scars",  0.30),   # LINE 1 lip-sync shot
    (4.44,  "party_scars",  2.90),   # LINE 2 punch-in, same take
    (6.06,  "host",         2.40),
    (7.10,  "street",       0.30),
    (7.72,  "host_bat",     0.30),
    (8.35,  "walk",         1.80),
    (8.97,  "host",         4.60),
    (9.61,  "street",       2.00),
    (10.13, "party_wide",   1.60),
    (10.78, "host_bat",     2.20),
    (11.31, "walk",         3.60),
    (11.89, "host",         6.20),
    (12.62, "street",       4.20),
    (13.22, "party_arrive", 1.10),
    (13.97, "host_bat",     4.00),
    (14.84, "host",         8.00),
    (15.69, "walk",         4.60),
    (16.44, "street",       6.00),
    (17.19, "host_bat",     6.20),
    (17.94, "party_wide",   1.60),
    (18.62, "mcu_fight",    0.30),
    (19.29, "mcu_joker",    0.30),   # LINE 3 shot
    (21.27, "host_bat",     0.30),
    (22.03, "street",       7.00),
    (23.04, "host",         4.60),
    (23.90, "mcu_joker",    6.10),   # LINE 4 shot
    (26.66, "host_bat",     2.20),
    (28.20, "mcu_joker",    9.25),   # LINE 5 shot
    (29.87, "host_bat",     2.20),
    (31.74, "walk",         3.60),
    (32.43, "street",       2.00),
    (33.74, "mcu_fight",    0.30),
    (34.62, "host_bat",     4.00),
    (35.44, "host",         8.00),
    (36.66, "mcu_d",        0.30),   # LINE 6 shot
    (38.97, "mcu_fight",    2.20),
    (39.44, "mcu_fight",    3.40),
    (40.86, "host",         8.60),
    (41.93, "mcu_d",        6.40),
    (42.90, "host",         9.60),   # final image: his laughing face
]
# where each line's speaking shot sits in CUTS (index) -> used to compute sync
LINE_SHOT = {"v1": ("party_scars", 0.30), "v2": ("party_scars", 2.90),
             "v3": ("mcu_joker", 0.30), "v4": ("mcu_joker", 6.10),
             "v5": ("mcu_joker", 9.25), "v6": ("mcu_d", 0.30)}


def shot_index(tag: str) -> int:
    name, s_in = LINE_SHOT[tag]
    for i, (_, n, si) in enumerate(CUTS):
        if n == name and abs(si - s_in) < 1e-6:
            return i
    raise KeyError(f"no shot for {tag}")

ZOOM = {"line": (1.10, 1.02), "line2": (1.02, 1.12), "hold": (1.06, 1.01),
        "hold2": (1.01, 1.08), "roll": (1.00, 1.04), "final": (1.03, 1.12)}
ROLE = {i: "line" for i in (shot_index(t) for t in LINE_SHOT)}
ROLE[shot_index("v2")] = "line2"
ROLE[len(CUTS) - 1] = "final"
_ix = [i for i, (t, n, si) in enumerate(CUTS)]
FLASH = {i for i in (shot_index("v6") + 1, len(CUTS) - 3, len(CUTS) - 2)
         if 0 <= i < len(CUTS)}


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


def snap(targets: list[float]) -> list[float]:
    """Snap every cut time to the nearest measured onset of the song window."""
    ts = np.load("/var/tmp/tdk/mtn_onsets.npy") - SONG_OFFSET
    ts = ts[(ts >= -0.1) & (ts <= 44.5)]
    out = [0.0]
    for t in targets[1:]:
        d = np.abs(ts - t)
        k = int(np.argmin(d))
        out.append(round(float(ts[k]), 3) if d[k] <= 0.26 else round(t, 3))
    return out


def main() -> int:
    DL.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    # ---- cut times (snapped to the music) and per-cut frames
    targets = [c[0] for c in CUTS]
    times = snap(targets)
    for i, (t0, tn) in enumerate(zip(targets, times)):
        if abs(t0 - tn) > 0.001:
            print(f"  cut {i:02d}: {t0:5.2f} -> {tn:5.2f} (onset snap {1000*(tn-t0):+.0f} ms)")
    # frame-align every cut so the timeline never drifts off the measured onsets
    total_frames = int(round(44.0 * FPS))
    f_idx = [0]
    for t in times[1:]:
        k = int(round(t * FPS))
        if k <= f_idx[-1]:
            k = f_idx[-1] + 2
        f_idx.append(k)
    times = [k / FPS for k in f_idx]
    frames = [f_idx[i + 1] - f_idx[i] for i in range(len(f_idx) - 1)]
    frames.append(total_frames - f_idx[-1])
    total_s = sum(frames) / FPS
    print(f"cuts={len(CUTS)} total={total_s:.3f}s  song {SONG_OFFSET:.2f}-{SONG_OFFSET+total_s:.2f}")

    # ---- dialogue clips (film audio, 44.1 kHz, same knee/limit as v2)
    dlg = []
    for tag, s0, s1, gain, sub in LINES:
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
        # voice onset = film time of the first word; shot film time = SLICE_IN + in-point
        idx = shot_index(tag)
        shot_film = SLICE_IN[CUTS[idx][1]] + CUTS[idx][2]
        voice_tl = round(times[idx] + (s0 - shot_film), 3)
        dlg.append({"tag": tag, "wav": str(wav), "dur": clip_dur, "voice": voice_tl,
                    "tl": round(voice_tl - 0.12, 3), "sub": sub, "gain": gain,
                    "film": (s0, s1)})
        print(f"  {tag}: film {s0:.2f}-{s1:.2f} -> voice {voice_tl:.2f}s "
              f"(shot {CUTS[idx][1]} in {CUTS[idx][2]:.2f} @ {times[idx]:.2f})")

    # ---- visual cuts
    cuts, sources = [], {}
    for i, (_, name, s_in) in enumerate(CUTS):
        dur = frames[i] / FPS
        role = ROLE.get(i, "hold" if i % 2 == 0 else "hold2")
        z0, z1 = ZOOM[role]
        p = str(SL / f"{name}.mp4")
        if not Path(p).exists():
            problems.append(f"missing slice {p}")
            continue
        mom = motion_of(p, s_in, dur)
        if mom < 0.30 and dur > 0.2:
            problems.append(f"low motion {name}@{i}: {mom:.2f}")
        cuts.append({"src": name, "start_s": round(s_in, 3), "dur_s": round(dur, 4),
                     "src_dur_s": round(dur + 0.20, 3), "zoom_start": z0, "zoom_end": z1,
                     "src_motion": round(mom, 3),
                     "transition_in": "flash_white" if i in FLASH else "none"})
        sources[name] = p

    # ---- dialogue events
    ev = []
    for d in dlg:
        sources["vox_" + d["tag"]] = d["wav"]
        ev.append({"src": "vox_" + d["tag"], "start_s": 0.0, "dur_s": d["dur"],
                   "timeline_s": d["tl"], "subtitle": d["sub"],
                   "sub_t0": round(d["voice"] + 0.08, 2),
                   "sub_t1": round(d["voice"] + d["dur"] - 0.16, 2), "gain": d["gain"]})

    plan = {"name": "styleA_tdk_joker_v3", "engine": "zohair_jigsaw", "song_path": SONG,
            "song_offset_s": SONG_OFFSET, "total_s": round(total_s, 3), "drop_s": 38.0,
            "beat_s": 0.3125, "sources": sources, "visual_cuts": cuts,
            "dialogue_events": ev, "sfx_events": [], "outro_black_s": 0.0}
    OUT.write_text(json.dumps(plan, indent=1))
    print("PROBLEMS:" if problems else "no problems")
    for p in problems:
        print("  ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
