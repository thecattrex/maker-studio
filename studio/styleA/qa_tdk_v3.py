#!/usr/bin/env python3
"""QA for TDK Style A v3 — every number measured off the rendered file itself."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

FF = "/home/user/bin/ffmpeg"
CARD = "crop=1036:584:22:668"
PLAN = "/home/user/studio/styleA/plan_tdk_v3.json"


def dur_of(vid: str) -> float:
    out = subprocess.run([FF, "-i", vid], capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def main() -> int:
    vid = sys.argv[1]
    plan = json.loads(Path(PLAN).read_text())
    res = {"duration_s": round(dur_of(vid), 3)}

    # 1. cuts vs measured onsets of "Mountains"
    on = np.load("/var/tmp/tdk/mtn_onsets.npy")
    on = on - plan["song_offset_s"]
    on = on[(on >= -0.1) & (on <= 45)]
    cuts, t = [], 0.0
    for c in plan["visual_cuts"]:
        cuts.append(t)
        t += c["dur_s"]
    d = []
    for ct in cuts[1:]:
        d.append((ct - on[int(np.argmin(np.abs(on - ct)))]) * 1000)
    d = np.array(d)
    res["cut_vs_onset_ms"] = {"n": int(len(d)), "median": round(float(np.median(np.abs(d))), 1),
                              "max": round(float(np.max(np.abs(d))), 1),
                              "within_15ms": int((np.abs(d) <= 15).sum())}

    # 2. freeze scan inside the card
    w, h = 200, 113
    raw = subprocess.run([FF, "-v", "error", "-i", vid, "-vf", f"{CARD},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    g = np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)
    dif = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    per_cut, t0 = [], 0.0
    for c in plan["visual_cuts"]:
        f0 = int(round(t0 * 30))
        f1 = int(round((t0 + c["dur_s"]) * 30))
        seg = dif[max(0, f0):max(f0 + 1, f1 - 1)]
        per_cut.append({"cut": c["src"], "t": round(t0, 2), "min": round(float(seg.min()), 2)})
        t0 += c["dur_s"]
    res["freeze"] = {"frames": int(n), "median_frame_diff": round(float(np.median(dif)), 2),
                     "min_frame_diff": round(float(dif.min()), 3),
                     "still_runs_ge3f": [], "unique_hashes": len({hash(g[k, ::3, ::3].tobytes()) for k in range(n)})}
    thr = 0.30
    runs, i = [], 0
    fz = dif < thr
    while i < len(fz):
        if fz[i]:
            j = i
            while j < len(fz) and fz[j]:
                j += 1
            if j - i >= 2:
                runs.append([round((i + 1) / 30, 2), int(j - i + 1)])
            i = j
        else:
            i += 1
    res["freeze"]["still_runs_ge3f"] = runs
    res["per_cut"] = per_cut

    # 3. loudness
    e = subprocess.run([FF, "-hide_banner", "-nostats", "-i", vid, "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = e[e.rfind("Summary:"):]
    for line in tail.splitlines():
        s = line.strip()
        if s.startswith(("I:", "LRA:", "Peak:")):
            res.setdefault("loudness", {})[s.split(":")[0]] = s.split(":", 1)[1].strip()

    # 4. end-to-end voice sync against the plan
    SR = 44100
    mix = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", vid, "-ac", "1", "-ar", str(SR),
                                        "-f", "f32le", "-"], capture_output=True).stdout,
                        np.float32).astype(np.float64)
    sos = butter(2, [300 / (SR / 2), 3200 / (SR / 2)], btype="band", output="sos")
    syn = []
    for de in plan["dialogue_events"]:
        tag = de["src"].replace("vox_", "")
        v, _ = sf.read(f"/var/tmp/tdk/dlg3/{tag}.wav", dtype="float32")
        v = np.asarray(v)
        v = v.mean(axis=1) if v.ndim > 1 else v
        v = v.astype(np.float64)
        t0 = de["timeline_s"]
        w0 = max(0, int((t0 - 0.6) * SR))
        w1 = min(len(mix), int((t0 + 0.6 + len(v) / SR) * SR))
        a = sosfiltfilt(sos, mix[w0:w1])
        a /= np.linalg.norm(a) + 1e-9
        b = sosfiltfilt(sos, v)
        b /= np.linalg.norm(b) + 1e-9
        c = np.correlate(a, b, "valid")
        k = int(np.argmax(c))
        syn.append({"tag": tag, "plan": round(t0, 2), "measured": round(w0 / SR + k / SR, 3),
                    "offset_ms": round((w0 / SR + k / SR - (t0 + 0.12)) * 1000, 1),
                    "corr": round(float(c[k]), 3)})
    res["sync"] = syn

    # 5. music answer after each line (low-band lift)
    low = sosfiltfilt(butter(2, [40 / (SR / 2), 150 / (SR / 2)], btype="band", output="sos"), mix)
    ans = []
    for de in plan["dialogue_events"]:
        end = de["timeline_s"] + 0.12 + de["dur_s"] - 0.24
        a = low[int((end - 0.5) * SR):int(end * SR)]
        b = low[int(end * SR):int((end + 0.8) * SR)]
        ans.append({"tag": de["src"].replace("vox_", ""),
                    "low_after_db": round(float(20 * np.log10((np.sqrt(np.mean(b ** 2)) + 1e-9) /
                                                              (np.sqrt(np.mean(a ** 2)) + 1e-9))), 1)})
    res["music_answer"] = ans
    Path("/var/tmp/tdk/qa_v3.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "per_cut"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
