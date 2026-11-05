#!/usr/bin/env python3
"""Interstellar Style A — slices + plan (film-time-exact dialogue, no freeze)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

FF = "/home/user/bin/ffmpeg"
SRC = "/var/tmp/int/int1080.mkv"
SL = Path("/var/tmp/int/sl")
OUT = Path("/home/user/studio/styleA/plan_interstellar.json")

BEAT = 0.627            # 95.7 BPM, measured from Cornfield Chase
BEATS_TOTAL = 69
DROP_BEATS = 56
SONG_DROP = 41.773      # measured energy hit in the track
SONG = "/var/tmp/int/cornfield.flac"

DLG_LEAD = 0.60         # how long the face is on screen before the first word
DLG_PAD = 0.10          # clips carry 100 ms pad before the line

# (slice, film in-point, beats, is_dialogue, dialogue line)
SEGMENTS = [
    ("a01_cockpit", 103.0, 4, False),
    ("a02_truck", 470.0, 4, False),
    ("d1_dirt", None, 10, True),          # dialogue slice, in-point computed below
    ("a03_farm", 500.0, 3, False),
    ("a04_dust", 530.0, 3, False),
    ("d2_murph", None, 6, True),
    ("a05_launch", 2905.0, 4, False),
    ("a06_rocket", 2911.5, 3, False),
    ("a07_saturn", 3300.0, 4, False),
    ("a08_endo", 3350.0, 2, False),
    ("a09_school", 700.0, 3, False),
    ("a10_blackhole", 7705.0, 2, False),
    ("d3_dock", None, 6, True),
    ("a11_glass", 7751.0, 2, False),
    # ---- drop ----
    ("a12_dock1", 7758.75, 1, False),
    ("a13_dock2", 7791.75, 1, False),
    ("a14_tess", 8600.5, 1, False),
    ("a15_tess2", 8662.5, 1, False),
    ("a16_launch2", 2910.0, 2, False),
    ("a17_saturn2", 3302.0, 1, False),
    ("a18_bh2", 7721.25, 1, False),
    ("a19_dock3", 7643.0, 1, False),
    ("a20_tess3", 8123.25, 1, False),
    ("a21_endo2", 3352.0, 1, False),
    ("a22_corn", 472.0, 1, False),
    ("a23_tess4", 8177.75, 1, False),
]

# dialogue: (line start, line end, subtitle)
LINES = {
    "d1_dirt": (1010.09, 1014.47, "Now we just look down and worry about our place in the dirt."),
    "d2_murph": (2419.71, 2422.05, "Don't make me leave like this, Murph!"),
    # CASE says "It's not possible" off-mouth -> dropped; Cooper's "No... it's necessary" is front-on face
    "d3_dock": (7701.25, 7703.35, "No... it's necessary."),
}
SLICE_S = 8.0


def extract(name: str, t_in: float) -> float:
    out = SL / f"{name}.mp4"
    subprocess.run(
        [FF, "-y", "-v", "error", "-ss", f"{t_in:.3f}", "-t", f"{SLICE_S:.2f}", "-i", SRC,
         "-an", "-vf", "crop=1920:816:0:132,scale=1280:544",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        check=True)
    return SLICE_S


W_M, H_M = 96, 41


def motion_of(path: str, t0: float, dur: float) -> float:
    """Mean abs frame diff over the cut window, 96x41 gray."""
    raw = subprocess.run(
        [FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", path,
         "-vf", f"scale={W_M}:{H_M},format=gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (W_M * H_M)
    if n < 2:
        return 99.0
    import numpy as np
    f = np.frombuffer(raw[:n * W_M * H_M], np.uint8).reshape(n, H_M, W_M).astype(np.float32)
    return float(np.abs(np.diff(f, axis=0)).mean())


def zoom_for(m: float) -> tuple[float, float]:
    """Static shot -> strong push so no cut ever looks frozen."""
    if m < 0.5:
        return 1.06, 1.17
    if m < 2.0:
        return 1.02, 1.11
    return 1.01, 1.06


def main() -> int:
    SL.mkdir(parents=True, exist_ok=True)
    # in-points
    in_pt, dlg_meta = {}, {}
    for name, t_in, beats, is_d in SEGMENTS:
        if is_d:
            s0, s1, sub = LINES[name]
            start = round(s0 - 1.20, 3)          # 1.2 s of pre-roll inside the slice
            in_pt[name] = start
            dlg_meta[name] = (s0, s1, sub, start)
        else:
            in_pt[name] = t_in

    for name in in_pt:
        extract(name, in_pt[name])

    cuts, timeline, problems = [], 0.0, []
    for name, t_in, beats, is_d in SEGMENTS:
        dur = round(beats * BEAT, 3)
        if is_d:
            s0, s1, sub, start = dlg_meta[name]
            cut_start = round(DLG_LEAD - (s0 - start) + (s0 - start) * 0 + 1.20 - DLG_LEAD, 3)  # = 0.30
            cut_start = round(1.20 - DLG_LEAD, 3)
            lead_in_cut = DLG_LEAD
        else:
            cut_start = 0.45
            lead_in_cut = None
        src_dur = round(cut_start + dur + 0.35, 3)
        if src_dur > SLICE_S:
            problems.append(f"{name}: needs {src_dur}s of slice, has {SLICE_S}")
        mom = motion_of(f"{SL}/{name}.mp4", cut_start, dur)
        z0, z1 = zoom_for(mom)
        if is_d:                       # dialogue must never sit on a static frame
            z0, z1 = (1.05, 1.16) if mom < 1.2 else (1.02, 1.12)
        cuts.append({
            "src": name, "start_s": cut_start, "dur_s": dur, "src_dur_s": src_dur,
            "zoom_start": z0, "zoom_end": z1, "src_motion": round(mom, 3),
            "transition_in": "flash_white" if name in ("a12_dock1", "a14_tess") else "none",
            "is_dialogue": is_d,
        })
        if is_d:
            dlg_meta[name] = (s0, s1, sub, cut_start, timeline, dur)
        timeline += dur

    dlg, sources = [], {c["src"]: f"{SL}/{c['src']}.mp4" for c in cuts}
    for name, meta in dlg_meta.items():
        s0, s1, sub, cut_start, cut_timeline, cut_dur = meta
        clip_start_film = s0 - DLG_PAD
        timeline_s = round(cut_timeline + DLG_LEAD - DLG_PAD, 3)
        clip_dur = round((s1 + DLG_PAD) - clip_start_film, 3)
        if timeline_s + clip_dur > cut_timeline + cut_dur - 0.05:
            problems.append(f"{name}: clip ends {timeline_s + clip_dur:.2f} past cut end {cut_timeline + cut_dur:.2f}")
        wav = f"/var/tmp/int/dlg/{name}.wav"
        subprocess.run(
            [FF, "-y", "-v", "error", "-ss", f"{clip_start_film:.3f}", "-t", f"{clip_dur:.3f}",
             "-i", SRC, "-af",
             "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=58:width_type=q:w=0.7,lowpass=f=15000,"
             "equalizer=f=2500:width_type=o:w=1.2:g=3,"
             "acompressor=threshold=-20dB:ratio=3:attack=5:release=140:makeup=6dB",
             "-ar", "48000", "-ac", "1", wav], check=True)
        # normalise + soft limit
        import numpy as np
        import soundfile as sf
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
        sources["vox_" + name] = wav
        dlg.append({
            "src": "vox_" + name, "start_s": 0.0, "dur_s": clip_dur,
            "timeline_s": timeline_s, "subtitle": sub,
            "sub_t0": round(timeline_s + DLG_PAD - 0.03, 2),
            "sub_t1": round(min(cut_timeline + cut_dur - 0.05, timeline_s + clip_dur + 0.20), 2),
        })
        print(f"  {name}: film {clip_start_film:.2f}-{s1 + DLG_PAD:.2f} ({clip_dur:.2f}s) -> timeline {timeline_s:.3f}  cut {cut_timeline:.2f}-{cut_timeline+cut_dur:.2f}")

    plan = {
        "name": "styleA_interstellar_v1",
        "engine": "zohair_jigsaw",
        "song_path": SONG,
        "song_offset_s": round(SONG_DROP - DROP_BEATS * BEAT, 3),
        "total_s": round(timeline, 2),
        "drop_s": round(DROP_BEATS * BEAT, 3),
        "beat_s": BEAT,
        "sources": sources,
        "visual_cuts": cuts,
        "dialogue_events": dlg,
        "sfx_events": [],
        "outro_black_s": 0.0,
    }
    OUT.write_text(json.dumps(plan, indent=1))
    print(f"beats {BEATS_TOTAL} = {timeline:.3f}s | drop @{plan['drop_s']} | song offset {plan['song_offset_s']}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  ", p)
    else:
        print("all cuts have >=0.35s slice headroom -> no freeze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
