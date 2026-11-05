#!/usr/bin/env python3
"""QA for TDK Style A v2 — every number measured off the rendered file itself."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

FF = "/home/user/bin/ffmpeg"
FFP = "/home/user/bin/ffprobe"
CARD = "crop=1036:584:22:668"


def main():
    vid = sys.argv[1]
    plan = json.loads(Path("/home/user/studio/styleA/plan_tdk_v2.json").read_text())
    out = {}
    out["duration_s"] = round(float(subprocess.run(
        [FFP, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", vid],
        capture_output=True, text=True).stdout.strip()), 3)

    # ---------- 1. every cut vs the measured onset grid ----------
    ev = json.loads(Path("/var/tmp/tdk/song_events.json").read_text())
    majors = np.array([m[0] for m in ev["majors"]])
    onsets = np.array(sorted([m[0] for m in ev["majors"]] + ev["minors"]))
    cuts, t, rows = [], 0.0, []
    for c in plan["visual_cuts"]:
        cuts.append(t)
        t += c["dur_s"]
    for ct in cuts:
        s = plan["song_offset_s"] + ct
        k = int(np.argmin(np.abs(onsets - s)))
        km = int(np.argmin(np.abs(majors - s)))
        rows.append([round(ct, 2), round(s - 866.0, 2), round((s - onsets[k]) * 1000),
                     round((s - majors[km]) * 1000)])
    d = np.array([abs(r[2]) for r in rows[1:]])
    out["cut_vs_onset"] = {"n": int(len(d)), "median_ms": int(np.median(d)),
                           "mean_ms": int(round(d.mean())), "max_ms": int(d.max()),
                           "within_50ms": int((d <= 50).sum())}
    out["cut_table_t_song_delta_nearest_major"] = rows

    # ---------- 2. freeze scan inside the 16:9 card only ----------
    w, h = 200, 113
    raw = subprocess.run([FF, "-v", "error", "-i", vid, "-vf", f"{CARD},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    g = np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)
    dif = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    thr = 0.35
    runs, i = [], 0
    frz = dif < thr
    while i < len(frz):
        if frz[i]:
            j = i
            while j < len(frz) and frz[j]:
                j += 1
            if j - i >= 2:
                runs.append([round((i + 1) / 30, 2), int(j - i + 1)])
            i = j
        else:
            i += 1
    hashes = {hash(g[k, ::3, ::3].tobytes()) for k in range(n)}
    out["freeze"] = {"frames": int(n), "median_frame_diff": round(float(np.median(dif)), 2),
                     "min_frame_diff": round(float(dif.min()), 3),
                     "still_runs_ge3f": runs, "unique_frame_hashes": len(hashes)}

    # ---------- 3. loudness ----------
    e = subprocess.run([FF, "-hide_banner", "-nostats", "-i", vid, "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = e[e.rfind("Summary:"):]
    for line in tail.splitlines():
        s = line.strip()
        if s.startswith(("I:", "LRA:", "Peak:")):
            out.setdefault("loudness", {})[s.split(":")[0]] = s.split(":", 1)[1].strip()

    # ---------- 4/5/6 audio ----------
    subprocess.run([FF, "-y", "-v", "error", "-i", vid, "-ac", "1", "-ar", "48000",
                    "/var/tmp/tdk/qa_audio.wav"], check=True)
    a, sr = sf.read("/var/tmp/tdk/qa_audio.wav", dtype="float32")
    a = a.astype(np.float64)
    hop = int(0.01 * sr)

    sos_v = butter(3, [700 / (sr / 2), 3600 / (sr / 2)], btype="band", output="sos")
    sos_l = butter(3, [40 / (sr / 2), 160 / (sr / 2)], btype="band", output="sos")
    vb = sosfiltfilt(sos_v, a)
    lb = sosfiltfilt(sos_l, a)

    def env(x):
        return np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]

    sync, ans = [], []
    for d_ in plan["dialogue_events"]:
        if "cap" in d_["src"]:
            continue
        v, _ = sf.read(plan["sources"][d_["src"]], dtype="float32")
        v = np.mean(v, axis=1).astype(np.float64)
        t0 = d_["timeline_s"]
        # lag: search +-400 ms, envelope correlation in the speech band
        eo = env(vb[int(t0 * sr): int((t0 + d_["dur_s"]) * sr)])
        ee = env(sosfiltfilt(sos_v, v))
        eo = (eo - eo.mean()) / (eo.std() + 1e-9)
        ee = (ee - ee.mean()) / (ee.std() + 1e-9)
        m = min(len(eo), len(ee))
        best = None
        for lag in range(-40, 41):
            if lag >= 0:
                x = eo[lag:m]
                y = ee[: m - lag]
            else:
                x = eo[: m + lag]
                y = ee[-lag:m]
            c = float(np.mean(x * y))
            if best is None or c > best[0]:
                best = (c, lag)
        sync.append({"sub": d_["subtitle"], "lag_ms": best[1] * 10,
                     "env_corr": round(best[0], 3)})
        # music answer: onset strength on the mix, pocket floor vs first hit after the last word
        t_se = t0 + d_["dur_s"] - 0.24
        seg_d = lb[int((t_se - 0.5) * sr): int(t_se * sr)]
        seg_a = lb[int(t_se * sr): int((t_se + 1.0) * sr)]
        floor = np.sqrt(np.mean(seg_d ** 2))
        win = max(2, int(0.03 * sr))
        rms_a = np.sqrt(np.convolve(seg_a ** 2, np.ones(win) / win, "same"))
        pk = float(np.max(rms_a))
        ans.append({"sub": d_["subtitle"], "low_band_answer_db": round(
            20 * np.log10((pk + 1e-9) / (floor + 1e-9)), 1)})
    out["sync"] = sync
    out["music_answer"] = ans

    print(json.dumps(out, indent=1))
    Path("/var/tmp/tdk/qa_v2.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
