"""pacing_audio.py — Silence Detection, Momentary Energy Curve & Hook Scoring.

Ports and streamlines OpenMontage's:
  - `silence_cutter.py` (dead-air detection & speech segment extraction)
  - `audio_energy.py` (100ms ebur128 momentary loudness profiling + peak window finder)
  - `clip-factory/script-director` 5-dimension hook/punchline candidate scorer
"""
from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from ._ffmpeg import get_ffmpeg

_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):([\d.]+)")
_SIL_START_RE = re.compile(r"silence_start:\s*([\d.]+)")
_SIL_END_RE = re.compile(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)")
_EBUR_M_RE = re.compile(r"t:\s*([\d.]+)\s+.*?M:\s*(-?[\d.]+)")


def probe_media_duration(path: str) -> float:
    """Get media duration in seconds using standalone `ffmpeg -i` (no ffprobe needed)."""
    r = subprocess.run([get_ffmpeg(), "-hide_banner", "-i", path], capture_output=True, text=True)
    m = _DUR_RE.search(r.stderr)
    if not m:
        return 0.0
    hh, mm, ss = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return hh * 3600.0 + mm * 60.0 + ss


def detect_silences(
    input_path: str,
    threshold_db: float = -35.0,
    min_duration: float = 0.45,
    padding_s: float = 0.08,
) -> dict[str, Any]:
    """Detect dead-air silences and inverse speech segments."""
    total_dur = probe_media_duration(input_path)
    cmd = [
        get_ffmpeg(), "-hide_banner", "-nostats", "-i", input_path,
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    silences: list[dict[str, float]] = []
    cur_start: float | None = None
    for line in r.stderr.splitlines():
        ms = _SIL_START_RE.search(line)
        if ms:
            cur_start = float(ms.group(1))
            continue
        me = _SIL_END_RE.search(line)
        if me and cur_start is not None:
            end_t = float(me.group(1))
            dur_t = float(me.group(2))
            silences.append({
                "start": round(cur_start, 3),
                "end": round(end_t, 3),
                "duration": round(dur_t, 3),
            })
            cur_start = None

    # Inverse speech segments with word-safe padding
    speech: list[dict[str, float]] = []
    cursor = 0.0
    for s in silences:
        sp_end = min(total_dur, s["start"] + padding_s)
        if sp_end - cursor > 0.12:
            speech.append({"start": round(cursor, 3), "end": round(sp_end, 3)})
        cursor = max(cursor, s["end"] - padding_s)
    if total_dur - cursor > 0.12:
        speech.append({"start": round(cursor, 3), "end": round(total_dur, 3)})

    sil_sum = sum(s["duration"] for s in silences)
    return {
        "total_duration": round(total_dur, 3),
        "silence_count": len(silences),
        "silence_seconds": round(sil_sum, 3),
        "dead_air_ratio": round(sil_sum / max(0.001, total_dur), 3),
        "silences": silences,
        "speech_segments": speech,
    }


def analyze_energy(
    input_path: str,
    window_s: float = 24.0,
    active_threshold_lufs: float = -38.0,
) -> dict[str, Any]:
    """Profile 1-second loudness curve + peak hook second + highest-energy window."""
    cmd = [get_ffmpeg(), "-hide_banner", "-nostats", "-i", input_path, "-af", "ebur128", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    pts: list[tuple[float, float]] = []
    for line in r.stderr.splitlines():
        m = _EBUR_M_RE.search(line)
        if m:
            pts.append((float(m.group(1)), float(m.group(2))))

    if not pts:
        return {"error": "No ebur128 momentary points parsed"}

    max_sec = int(pts[-1][0]) + 1
    profile = []
    for sec in range(max_sec):
        vals = [v for t, v in pts if sec <= t < sec + 1 and v > -115.0]
        avg_v = sum(vals) / len(vals) if vals else -120.0
        profile.append({
            "sec": sec,
            "lufs": round(avg_v, 1),
            "active": avg_v > active_threshold_lufs,
        })

    active_Only = [p for p in profile if p["lufs"] > -115.0]
    peak = max(active_Only, key=lambda p: p["lufs"]) if active_Only else {"sec": 0, "lufs": -120.0}
    first_active = next((p["sec"] for p in profile if p["active"]), 0)

    win = max(1, min(int(round(window_s)), max_sec))
    vals_clamped = [p["lufs"] if p["lufs"] > -115.0 else -60.0 for p in profile]
    best_s, best_avg = 0, -999.0
    for i in range(0, max(1, len(vals_clamped) - win + 1)):
        a = sum(vals_clamped[i : i + win]) / win
        if a > best_avg:
            best_avg, best_s = a, i

    return {
        "duration_s": max_sec,
        "first_active_s": first_active,
        "peak_sec": peak["sec"],
        "peak_lufs": peak["lufs"],
        "best_window_start_s": best_s,
        "best_window_end_s": best_s + win,
        "best_window_avg_lufs": round(best_avg, 1),
        "profile": profile,
    }


_PUNCH_TOKENS = {
    "never", "ever", "fired", "ugly", "insane", "deserve", "die", "died",
    "kill", "right", "here", "stop", "shut", "hell", "god", "what", "no",
    "wait", "secret", "lie", "truth", "money", "million", "billion", "hate",
    "love", "better", "worst", "crazy", "touch", "run",
}


def score_hook_candidates(
    segments: list[dict[str, Any]],
    min_dur: float = 2.2,
    max_dur: float = 4.6,
) -> list[dict[str, Any]]:
    """Rank 1-2 segment cold-open hook/punchline candidates using Clip-Factory heuristics.

    Each input item in `segments`: `{"start": float, "end": float, "text": str}`.
    Returns top candidates sorted descending by `total_score`.
    """
    candidates: list[dict[str, Any]] = []
    n = len(segments)
    for i in range(n):
        for span in (1, 2, 3):
            if i + span > n:
                continue
            chunk = segments[i : i + span]
            t0, t1 = float(chunk[0]["start"]), float(chunk[-1]["end"])
            dur = t1 - t0
            if dur < min_dur or dur > max_dur:
                continue
            txt = " ".join(c["text"].strip() for c in chunk).strip()
            words = re.findall(r"[A-Za-z']+", txt.lower())
            if len(words) < 3:
                continue

            # 1. Punch/Emotion lexical trigger (0..5)
            hits = sum(1 for w in words if w in _PUNCH_TOKENS)
            hook_score = min(5.0, 1.5 + hits * 1.2 + (1.0 if ("?" in txt or "!" in txt) else 0.0))

            # 2. Standalone clarity: penalize dangling openings ("and", "but", "because", "so")
            dangling = words[0] in {"and", "or", "because", "which", "than"}
            coherence = 2.2 if dangling else 4.5

            # 3. Pace / Word density (ideal ~2.2 - 3.8 words/sec)
            wps = len(words) / max(0.1, dur)
            energy = 4.6 if 1.8 <= wps <= 4.2 else 2.8

            # 4. Position bonus: climax/payoff lines in the final 40% of a scene make killer cold-opens!
            rel_pos = (i + span) / max(1, n)
            payoff_bonus = 4.8 if rel_pos >= 0.60 else 3.2

            total = round((hook_score * 0.35 + coherence * 0.25 + energy * 0.20 + payoff_bonus * 0.20), 2)
            candidates.append({
                "start": round(t0, 3),
                "end": round(t1, 3),
                "duration": round(dur, 3),
                "text": txt,
                "score": total,
                "breakdown": {
                    "hook": round(hook_score, 2),
                    "coherence": round(coherence, 2),
                    "energy": round(energy, 2),
                    "payoff_position": round(payoff_bonus, 2),
                },
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:8]
