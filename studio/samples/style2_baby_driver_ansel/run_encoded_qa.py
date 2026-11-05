#!/usr/bin/env python3
"""Encoded-master QA for the isolated Baby Driver Style 2 plan.

Usage: python3 run_encoded_qa.py MASTER [PLAN] [OUT_DIR]
No prompt-assisted ASR is done here; run_encoded_asr.py handles that separately.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
W, H = 1080, 1920
BOX_Y, BOX_H = 360, 1200


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def timeline(plan: dict) -> tuple[list[dict], int]:
    rows = [{
        "kind": "act1", "label": "ACT 1 — continuous diner scene",
        "frames": int(round(float(plan["scene_segments"][0]["dur_s"]) * FPS)),
    }]
    black = int(plan.get("pre_drop_black_frames", 0))
    rows.append({"kind": "black", "label": "intended pre-drop black", "frames": black})
    bpm = float(plan["bpm"])
    for i, clip in enumerate(plan["montage_clips"], 1):
        if "dur_s" in clip:
            nf = max(10, int(round(float(clip["dur_s"]) * FPS)))
        else:
            nf = max(12, int(round(float(clip.get("beats", 2.0)) * (60.0 / bpm) * FPS)))
        rows.append({"kind": "montage", "label": f"DROP {i:02d} — {clip['src']}", "frames": nf})
    start = 0
    for row in rows:
        row["start_frame"] = start
        row["end_frame"] = start + row["frames"]
        start = row["end_frame"]
    return rows, start


def parse_loudness(text: str) -> dict:
    def last(pattern: str, default=None):
        vals = re.findall(pattern, text, flags=re.I | re.M)
        return float(vals[-1]) if vals else default
    return {
        "integrated_lufs": last(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS"),
        "lra_lu": last(r"LRA:\s*(-?\d+(?:\.\d+)?)\s*LU"),
        "true_peak_dbfs": last(r"Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS"),
    }


def main() -> None:
    master = Path(sys.argv[1]).resolve()
    plan_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).parents[2] / "styleB/plan_baby_driver_ansel_style2.json"
    out_dir = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else master.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = json.loads(plan_path.read_text())
    rows, expected_frames = timeline(plan)
    drop_frame = rows[1]["end_frame"]
    allowed_black = set(range(rows[1]["start_frame"], rows[1]["end_frame"]))
    allowed_black.add(expected_frames - 1)  # engine's designed final fade

    wanted: dict[int, tuple[str, str]] = {}
    for sec, label in [(0.8, "THEY CALL; I GO."), (5.3, "SO WHAT IS IT YOU DO?"), (7.7, "I'M A DRIVER.")]:
        wanted[min(rows[0]["frames"] - 1, int(round(sec * FPS)))] = ("ACT 1", label)
    for row in rows[2:]:
        wanted[(row["start_frame"] + row["end_frame"] - 1) // 2] = ("ACT 2", row["label"])

    cap = cv2.VideoCapture(str(master))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {master}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    declared = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stats = [{"frames": 0, "motion": [], "brightness": [], "hashes": [], "max_dup": 0} for _ in rows]
    unexpected_black: list[int] = []
    bar_failures: list[int] = []
    thumbs: list[tuple[str, str, Image.Image]] = []
    prev_small: np.ndarray | None = None
    prev_hash: str | None = None
    prev_row_idx: int | None = None
    frame_idx = 0
    row_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        while row_idx < len(rows) - 1 and frame_idx >= rows[row_idx]["end_frame"]:
            row_idx += 1
            prev_small = None
            prev_hash = None
        if frame_idx >= expected_frames:
            raise SystemExit(f"Extra decoded frame {frame_idx}; expected {expected_frames}")
        if frame.shape[:2] != (H, W):
            raise SystemExit(f"Bad frame shape at {frame_idx}: {frame.shape}")
        active = frame[BOX_Y:BOX_Y + BOX_H]
        small = cv2.resize(cv2.cvtColor(active, cv2.COLOR_BGR2GRAY), (135, 150), interpolation=cv2.INTER_AREA)
        brightness = float(np.mean(small))
        hsh = hashlib.sha1(small.tobytes()).hexdigest()
        st = stats[row_idx]
        st["frames"] += 1
        st["brightness"].append(brightness)
        st["hashes"].append(hsh)
        if prev_small is not None and prev_row_idx == row_idx:
            st["motion"].append(float(np.mean(cv2.absdiff(small, prev_small))))
        if prev_hash == hsh and prev_row_idx == row_idx:
            st["max_dup"] += 1
        prev_small, prev_hash, prev_row_idx = small, hsh, row_idx
        if brightness < 2.0 and frame_idx not in allowed_black:
            unexpected_black.append(frame_idx)
        # The canvas outside the centered 1080x1200 active box must remain black.
        top_mean = float(np.mean(frame[:BOX_Y]))
        bot_mean = float(np.mean(frame[BOX_Y + BOX_H:]))
        if top_mean > 1.0 or bot_mean > 1.0:
            bar_failures.append(frame_idx)
        if frame_idx in wanted:
            kind, label = wanted[frame_idx]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            thumbs.append((f"{kind}  f{frame_idx}", label, Image.fromarray(rgb)))
        frame_idx += 1
    cap.release()

    cut_rows = []
    motion_failures = []
    for row, st in zip(rows, stats):
        if row["kind"] == "black":
            continue
        uniq = len(set(st["hashes"])) / max(1, len(st["hashes"]))
        item = {
            **{k: row[k] for k in ("kind", "label", "start_frame", "end_frame")},
            "frames": st["frames"],
            "mean_motion": round(float(np.mean(st["motion"])) if st["motion"] else 0.0, 4),
            "min_motion": round(float(np.min(st["motion"])) if st["motion"] else 0.0, 4),
            "mean_brightness": round(float(np.mean(st["brightness"])), 3),
            "unique_frame_ratio": round(uniq, 4),
            "max_exact_duplicate_run": st["max_dup"],
        }
        cut_rows.append(item)
        if row["kind"] == "montage" and (uniq < 0.80 or item["mean_motion"] < 0.02):
            motion_failures.append(row["label"])

    ff = ffmpeg_exe()
    decode = subprocess.run([ff, "-v", "error", "-i", str(master), "-f", "null", "-"], capture_output=True, text=True)
    loud = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(master), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    loudness = parse_loudness(loud.stderr)
    audio_wav = Path("/var/tmp/style2_baby_driver/qa/encoded_full.wav")
    audio_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ff, "-y", "-v", "error", "-i", str(master), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio_wav)], check=True)

    # Contact sheet: three Act 1 dialogue frames + every montage clip midpoint.
    tw, th, lh, cols = 216, 384, 42, 5
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 14)
    except Exception:
        font = ImageFont.load_default()
    sheet = Image.new("RGB", (cols * tw, math.ceil(len(thumbs) / cols) * (th + lh)), (8, 8, 10))
    draw = ImageDraw.Draw(sheet)
    for i, (kind, label, im) in enumerate(thumbs):
        x, y = (i % cols) * tw, (i // cols) * (th + lh)
        sheet.paste(im.resize((tw, th), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 4, y + th + 2), kind, font=font, fill=(255, 46, 99))
        draw.text((x + 4, y + th + 19), label[:31], font=font, fill=(245, 245, 245))
    sheet_path = out_dir / "encoded_storyboard.jpg"
    sheet.save(sheet_path, quality=93)

    duration = frame_idx / FPS
    errors = []
    if (width, height) != (W, H): errors.append(f"resolution {width}x{height}")
    if abs(fps - FPS) > 0.01: errors.append(f"fps {fps}")
    if frame_idx != expected_frames: errors.append(f"decoded frames {frame_idx} != expected {expected_frames}")
    if decode.returncode != 0 or decode.stderr.strip(): errors.append(f"ffmpeg full decode: {decode.stderr.strip()[:300]}")
    if unexpected_black: errors.append(f"unexpected black frames: {unexpected_black[:20]}")
    if bar_failures: errors.append(f"nonblack canvas bars: {bar_failures[:20]}")
    if motion_failures: errors.append(f"static/slideshow montage cuts: {motion_failures}")
    if loudness["integrated_lufs"] is None or abs(loudness["integrated_lufs"] + 14.0) > 1.0:
        errors.append(f"integrated loudness {loudness['integrated_lufs']}")
    if loudness["true_peak_dbfs"] is None or loudness["true_peak_dbfs"] > -1.3:
        errors.append(f"true peak {loudness['true_peak_dbfs']} exceeds -1.3 dBFS")

    report = {
        "passed": not errors,
        "master": str(master),
        "plan": str(plan_path),
        "resolution": f"{width}x{height}",
        "fps": fps,
        "declared_frames": declared,
        "decoded_frames": frame_idx,
        "expected_frames": expected_frames,
        "duration_s": round(duration, 6),
        "drop_s": round(drop_frame / FPS, 6),
        "full_decode_passed": decode.returncode == 0 and not decode.stderr.strip(),
        "active_box": "1080x1200 centered at y=360; outer bars black",
        "unexpected_black_frames": unexpected_black,
        "canvas_bar_failures": bar_failures,
        "motion_failures": motion_failures,
        **loudness,
        "cuts": cut_rows,
        "storyboard": str(sheet_path),
        "encoded_audio_for_asr": str(audio_wav),
        "errors": errors,
    }
    (out_dir / "encoded_qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cuts"}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
