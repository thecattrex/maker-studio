#!/usr/bin/env python3
"""Isolated GitHub Actions worker for Style 3 only.

No import from hq_worker, om_hybrid, Style A/B, or Type 1/2/3/4 is used.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from studio.style3.render_maverick import render_full, validate_plan  # noqa: E402


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def _download(url: str, dest: Path, expected_size: int) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size == expected_size:
        print(f"CACHE HIT {dest.name} {expected_size}", flush=True)
        return {"name": dest.name, "size": expected_size, "cache": "hit"}
    part = dest.with_suffix(dest.suffix + ".part")
    if part.exists():
        part.unlink()
    last_error = None
    for attempt in range(3):
        try:
            print(f"DOWNLOAD {url} attempt={attempt + 1}", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "maker-studio-style3/1.0"})
            with urllib.request.urlopen(req, timeout=180) as response, part.open("wb") as handle:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    handle.write(block)
            actual = part.stat().st_size
            if actual != expected_size:
                raise RuntimeError(f"Size mismatch for {dest.name}: {actual} != {expected_size}")
            part.replace(dest)
            return {"name": dest.name, "size": actual, "cache": "downloaded"}
        except Exception as exc:  # retry transient archive/network failures only
            last_error = exc
            print(f"download attempt failed: {exc}", flush=True)
            if part.exists():
                part.unlink()
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Unable to download {url}: {last_error}")


def _probe(path: Path) -> dict:
    proc = subprocess.run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def _loudness(path: Path) -> dict:
    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-",
    ], capture_output=True, text=True, check=True)
    j0, j1 = proc.stderr.rfind("{"), proc.stderr.rfind("}") + 1
    values = json.loads(proc.stderr[j0:j1])
    return {
        "integrated_lufs": float(values["input_i"]),
        "true_peak_dbtp": float(values["input_tp"]),
        "lra": float(values["input_lra"]),
        "threshold": float(values["input_thresh"]),
    }


def _frame_at(cap: cv2.VideoCapture, t: float) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000.0)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"QA frame decode failed at {t:.3f}s")
    return frame


def _visual_qa(path: Path, plan: dict, sheet_out: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frames / fps
    times = np.linspace(0.25, duration - 0.25, 24)
    tiles = []
    for t in times:
        frame = _frame_at(cap, float(t))
        thumb = cv2.resize(frame, (180, 320), interpolation=cv2.INTER_AREA)
        tile = np.zeros((344, 180, 3), dtype=np.uint8)
        tile[:320] = thumb
        cv2.putText(tile, f"{t:05.2f}s", (5, 336), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(tile)
    sheet = np.vstack([np.hstack(tiles[i : i + 6]) for i in range(0, 24, 6)])
    cv2.imwrite(str(sheet_out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])

    motion = []
    active_means = []
    for seg in plan["segments"]:
        start, end = float(seg["start"]), float(seg["end"])
        dur = end - start
        ta = start + min(0.18, dur * 0.25)
        tb = start + min(0.52, dur * 0.72)
        if tb <= ta:
            tb = start + dur * 0.8
        a = _frame_at(cap, ta)[744:1176, 24:1056]
        b = _frame_at(cap, tb)[744:1176, 24:1056]
        ag = cv2.cvtColor(cv2.resize(a, (270, 108), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        bg = cv2.cvtColor(cv2.resize(b, (270, 108), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        score = float(np.mean(cv2.absdiff(ag, bg)))
        motion.append({"id": seg["id"], "mean_abs_diff": round(score, 3)})
        mid = _frame_at(cap, (start + end) * 0.5)[744:1176, 24:1056]
        active_means.append({"id": seg["id"], "active_band_mean": round(float(mid.mean()), 2)})
    cap.release()
    min_motion = min(x["mean_abs_diff"] for x in motion)
    min_active = min(x["active_band_mean"] for x in active_means)
    return {
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frames": frames,
        "duration": round(duration, 3),
        "motion_by_segment": motion,
        "active_band_by_segment": active_means,
        "min_motion_score": round(min_motion, 3),
        "min_active_band_mean": round(min_active, 2),
        "motion_pass": min_motion >= 0.05,
        "active_picture_pass": min_active >= 4.0,
    }


def _asr(path: Path, model_name: str) -> dict:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
        segments, info = model.transcribe(
            str(path), language="en", beam_size=5, word_timestamps=True,
            condition_on_previous_text=False, vad_filter=False,
        )
        rows = []
        words = []
        for seg in segments:
            rows.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
            for word in seg.words or []:
                words.append({"start": round(word.start, 3), "end": round(word.end, 3), "word": word.word})
        text = " ".join(x["text"] for x in rows).strip()
        lowered = text.lower()
        return {
            "status": "ok",
            "model": model_name,
            "language": info.language,
            "text": text,
            "segments": rows,
            "words": words,
            "danger_zone_detected": "danger" in lowered and "zone" in lowered,
            "overdrive_detected": "overdrive" in lowered or "over drive" in lowered,
        }
    except Exception as exc:
        return {"status": "error", "model": model_name, "error": str(exc), "danger_zone_detected": False, "overdrive_detected": False}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-b64", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    job = json.loads(base64.b64decode(args.job_b64).decode("utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = ROOT / job.get("plan", "studio/style3/maverick_plan.json")
    plan = json.loads(plan_path.read_text())
    plan_validation = validate_plan(plan)
    cache = Path(os.environ.get("MAKER_STYLE3_CACHE", "/tmp/maker_style3_cache"))
    cache.mkdir(parents=True, exist_ok=True)

    source_paths = {}
    cache_report = []
    for key, spec in plan["sources"].items():
        dest = cache / spec["cache_name"]
        cache_report.append(_download(spec["url"], dest, int(spec["size"])))
        source_paths[key] = str(dest)
    music = plan["music"]
    song_path = cache / music["cache_name"]
    cache_report.append(_download(music["url"], song_path, int(music["size"])))

    out_name = job.get("out_name", plan["output"]["name"])
    master = out_dir / out_name
    work = Path("/tmp/style3_maverick_render")
    render_full(plan, source_paths, str(song_path), master, work)

    probe = _probe(master)
    streams = probe["streams"]
    video_streams = [s for s in streams if s["codec_type"] == "video"]
    audio_streams = [s for s in streams if s["codec_type"] == "audio"]
    visual = _visual_qa(master, plan, out_dir / "qa_sheet.jpg")
    loudness = _loudness(master)
    asr = _asr(master, job.get("asr_model", "small.en"))
    (out_dir / "asr_report.json").write_text(json.dumps(asr, indent=2))

    expected_duration = float(plan["output"]["duration"])
    technical_pass = (
        len(video_streams) == 1 and len(audio_streams) == 1
        and visual["width"] == 1080 and visual["height"] == 1920
        and abs(visual["fps"] - 30.0) < 0.01
        and abs(visual["duration"] - expected_duration) <= 0.12
        and visual["frames"] == int(round(expected_duration * 30))
        and video_streams[0]["codec_name"] == "h264"
        and audio_streams[0]["codec_name"] == "aac"
    )
    audio_pass = -16.5 <= loudness["integrated_lufs"] <= -11.5 and loudness["true_peak_dbtp"] <= -0.8
    sha256 = hashlib.sha256(master.read_bytes()).hexdigest()
    report = {
        "mode": "style3_maverick",
        "video_rendered": True,
        "style": "Style 3 — Cashworth only",
        "movie": plan["movie"],
        "master": {"name": out_name, "bytes": master.stat().st_size, "sha256": sha256},
        "plan": str(plan_path.relative_to(ROOT)),
        "plan_validation": plan_validation,
        "cache": cache_report,
        "probe": {
            "duration": probe["format"].get("duration"),
            "video": [{k: s.get(k) for k in ["codec_name", "width", "height", "r_frame_rate", "pix_fmt", "nb_frames"]} for s in video_streams],
            "audio": [{k: s.get(k) for k in ["codec_name", "sample_rate", "channels", "channel_layout"]} for s in audio_streams],
        },
        "technical_pass": technical_pass,
        "visual_qa": visual,
        "audio_loudness": loudness,
        "audio_loudness_pass": audio_pass,
        "audio_asr": asr,
        "audio_asr_pass": bool(asr.get("danger_zone_detected")),
        "isolation": {
            "worker": "studio/cloud/style3_worker.py",
            "renderer": "studio/style3/render_maverick.py",
            "legacy_hq_worker_imported": "studio.cloud.hq_worker" in sys.modules,
            "om_hybrid_imported": any(k == "om_hybrid" or k.startswith("om_hybrid.") for k in sys.modules),
            "creative_mix": False,
        },
        "render_qa_pass": bool(technical_pass and visual["motion_pass"] and visual["active_picture_pass"] and audio_pass),
        "note": "Automated report plus contact sheet; final visual review happens after artifact download.",
    }
    (out_dir / "cloud_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ["mode", "video_rendered", "technical_pass", "audio_loudness_pass", "audio_asr_pass", "render_qa_pass"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
