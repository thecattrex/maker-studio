#!/usr/bin/env python3
"""The Dark Knight — Style A (Joker) v1. Beat-locked, no-freeze, film-time dialogue."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/tdk/tdk1080.mp4"
SONG = "/var/tmp/tdk/song.wav"
SL = Path("/var/tmp/tdk/sl")
DL = Path("/var/tmp/tdk/dlg")
OUT = Path("/home/user/studio/styleA/plan_tdk.json")

SONG_DROP = 678.42      # measured energy impact in "A Dark Knight"
DROP_BEATS = 56
BEATS_TOTAL = 69
DLG_LEAD = 0.60
DLG_PAD = 0.20
SLICE_S = 8.0

# ---- pre-drop (56 beats): 5 hook shots, 3 dialogue pockets, 10 build shots ----
PRE = [
    ("a01_bus", 92.75, 3),
    ("a02_cont", 96.25, 2),
    ("a03_jstreet", 214.00, 2),
    ("a04_mob", 273.50, 2),
    ("a05_heist", 298.50, 2),
    ("d1_dawn", None, 7),
    ("a06_podium", 4312.25, 2),
    ("a07_crowd", 4329.25, 2),
    ("d2_tvwarn", None, 9),
    ("a08_gala", 3522.50, 2),
    ("a09_gala2", 3606.50, 2),
    ("d3_idont", None, 6),
    ("a10_fight1", 8031.00, 2),
    ("a11_fight2", 3743.75, 3),
    ("a12_fight3", 3726.75, 2),
    ("a13_chase", 7269.25, 3),
    ("a14_ambush", 4315.25, 3),
    ("a15_mob2", 4596.00, 2),
]

# ---- post-drop (13 beats): one cut per beat ----
POST = [
    ("b01_blast", 4678.25, 1),
    ("b02_flip", 7521.25, 1),
    ("b03_blast2", 4595.50, 1),
    ("b04_crash", 7620.75, 1),
    ("b05_crane", 7297.50, 1),
    ("b06_truck", 7687.25, 1),
    ("b07_boom", 4670.25, 1),
    ("b08_slam", 7637.00, 1),
    ("b09_ram", 7517.25, 1),
    ("b10_hit", 7515.25, 1),
    ("b11_tumble", 7686.25, 1),
    ("b12_dust", 7859.00, 1),
    ("b13_end", 8940.50, 2),
]

# (film in, film out, subtitle)
LINES = {
    "d1_dawn": (4293.90, 4297.35, "The night is darkest just before the dawn."),
    "d2_tvwarn": (2602.40, 2606.70, "People will die. Starting tonight."),
    "d3_idont": (5280.50, 5282.80, "I don't want to kill you."),
}

W_M, H_M = 96, 40


def motion_of(path: str, t0: float, dur: float) -> float:
    raw = subprocess.run(
        [FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", path,
         "-vf", f"scale={W_M}:{H_M},format=gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (W_M * H_M)
    if n < 2:
        return 99.0
    f = np.frombuffer(raw[:n * W_M * H_M], np.uint8).reshape(n, H_M, W_M).astype(np.float32)
    return float(np.abs(np.diff(f, axis=0)).mean())


def zoom_for(m: float) -> tuple[float, float]:
    if m < 0.5:
        return 1.06, 1.17
    if m < 2.0:
        return 1.02, 1.11
    return 1.01, 1.06


def beat_length() -> float:
    import librosa
    y, sr = librosa.load(SONG, sr=22050, mono=True, offset=600, duration=340)
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512, units="time")
    b = np.array(beats) + 600
    b = b[(b > 610) & (b < 935)]
    return float(np.median(np.diff(b)))


def extract(name: str, t_in: float) -> None:
    subprocess.run(
        [FF, "-y", "-v", "error", "-ss", f"{t_in:.3f}", "-t", f"{SLICE_S:.2f}", "-i", SRC,
         "-an", "-vf", "crop=1920:800:0:0,scale=1280:-2",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
         str(SL / f"{name}.mp4")], check=True)


def main() -> int:
    SL.mkdir(parents=True, exist_ok=True)
    DL.mkdir(parents=True, exist_ok=True)
    BEAT = beat_length()
    print(f"BEAT {BEAT:.5f}s  ({60/BEAT:.2f} BPM)")
    song_offset = round(SONG_DROP - DROP_BEATS * BEAT, 3)

    segs = PRE + POST
    in_pt, dlg_meta = {}, {}
    for name, t_in, beats in segs:
        if name in LINES:
            s0, s1, sub = LINES[name]
            start = round(s0 - 1.50, 3)          # 1.5 s pre-roll inside the slice
            in_pt[name] = start
            dlg_meta[name] = {"s0": s0, "s1": s1, "sub": sub, "slice_in": start}
        else:
            in_pt[name] = t_in
    for name, t_in in in_pt.items():
        extract(name, t_in)

    cuts, sources, problems, tl = [], {}, [], 0.0
    for name, _t, beats in segs:
        dur = round(beats * BEAT, 3)
        if name in LINES:
            cut_start = round(1.50 - DLG_LEAD, 3)
        else:
            cut_start = 0.40
        head = 0.35 if beats > 1 else 0.12
        src_dur = round(cut_start + dur + head, 3)
        if src_dur > SLICE_S:
            problems.append(f"{name}: needs {src_dur}s, slice {SLICE_S}")
        mom = motion_of(str(SL / f"{name}.mp4"), cut_start, dur)
        z0, z1 = zoom_for(mom)
        if name in LINES:
            z0, z1 = (1.05, 1.16) if mom < 1.2 else (1.02, 1.12)
        cuts.append({
            "src": name, "start_s": cut_start, "dur_s": dur, "src_dur_s": src_dur,
            "zoom_start": z0, "zoom_end": z1, "src_motion": round(mom, 3),
            "transition_in": "flash_white" if name in ("b01_blast", "b02_flip") else "none",
        })
        sources[name] = str(SL / f"{name}.mp4")
        if name in LINES:
            dlg_meta[name]["cut_tl"] = tl
            dlg_meta[name]["cut_dur"] = dur
        tl += dur

    dlg = []
    for name, m in dlg_meta.items():
        s0, s1 = m["s0"], m["s1"]
        clip_in = round(s0 - 0.10, 3)
        clip_dur = round((s1 + 0.10) - clip_in, 3)
        timeline_s = round(m["cut_tl"] + DLG_LEAD - 0.10, 3)
        wav = DL / f"{name}.wav"
        subprocess.run(
            [FF, "-y", "-v", "error", "-ss", f"{clip_in:.3f}", "-t", f"{clip_dur:.3f}", "-i", SRC,
             "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=58:width_type=q:w=0.7,lowpass=f=15000,"
                    "equalizer=f=2500:width_type=o:w=1.2:g=3,"
                    "acompressor=threshold=-20dB:ratio=3:attack=5:release=140:makeup=6dB",
             "-ar", "48000", "-ac", "1", str(wav)], check=True)
        a, sr = sf.read(wav, dtype="float32")
        a = a.astype("float64")
        a *= 0.80 / (float(np.max(np.abs(a))) + 1e-9)
        knee, head = 0.66, 0.92
        over = np.abs(a) > knee
        a[over] = np.sign(a[over]) * (knee + (head - knee) * np.tanh((np.abs(a[over]) - knee) / (head - knee)))
        fn = int(0.025 * sr)
        r = np.linspace(0, 1, fn)
        a[:fn] *= r
        a[-fn:] *= r[::-1]
        sf.write(wav, np.stack([a, a], 1).astype("float32"), sr, subtype="PCM_16")
        sources["vox_" + name] = str(wav)
        cut_end = m["cut_tl"] + m["cut_dur"]
        if timeline_s + clip_dur > cut_end + 0.02:
            problems.append(f"{name}: audio ends {timeline_s+clip_dur:.2f} past cut end {cut_end:.2f}")
        dlg.append({
            "src": "vox_" + name, "start_s": 0.0, "dur_s": clip_dur, "timeline_s": timeline_s,
            "subtitle": m["sub"],
            "sub_t0": round(timeline_s + 0.07, 2),
            "sub_t1": round(min(cut_end - 0.05, timeline_s + clip_dur + 0.15), 2),
        })
        print(f"  {name}: film {clip_in:.2f}-{s1+0.10:.2f} ({clip_dur:.2f}s) -> tl {timeline_s:.2f} "
              f"| cut {m['cut_tl']:.2f}-{cut_end:.2f} | '{m['sub']}'")

    plan = {
        "name": "styleA_tdk_joker_v1",
        "engine": "zohair_jigsaw",
        "song_path": SONG,
        "song_offset_s": song_offset,
        "total_s": round(tl, 2),
        "drop_s": round(DROP_BEATS * BEAT, 3),
        "beat_s": round(BEAT, 5),
        "sources": sources,
        "visual_cuts": cuts,
        "dialogue_events": dlg,
        "sfx_events": [],
        "outro_black_s": 0.0,
    }
    OUT.write_text(json.dumps(plan, indent=1))
    print(f"beats {BEATS_TOTAL} = {tl:.3f}s | drop @{plan['drop_s']} | song_offset {song_offset}")
    print("PROBLEMS:" if problems else "all cuts have headroom -> no freeze")
    for p in problems:
        print("  ", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
