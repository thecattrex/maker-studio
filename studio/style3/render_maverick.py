#!/usr/bin/env python3
"""Isolated Style 3 / Cashworth renderer for the Maverick fan edit.

Creative code in this module is deliberately independent of Style A/B and
Type 1/2/3/4.  It uses real decoded movie frames, a real produced song, and
only the layouts/typography declared in maverick_plan.json.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts"
CACHE_W, CACHE_H = 1200, 500
ALLOWED_LAYOUTS = {"strip", "banner", "square", "triptych", "split", "bento", "bento2", "video_text"}
FORBIDDEN_OVERLAYS = {"TOP GUN", "MAVERICK", "TOM CRUISE", "PARAMOUNT", "COPYRIGHT"}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    files = {
        "bold": "Poppins-ExtraBoldItalic.ttf",
        "serif": "PlayfairDisplay-Italic.ttf",
        "video": "ArchivoBlack-Regular.ttf",
    }
    path = FONT_DIR / files[name]
    if not path.exists():
        raise FileNotFoundError(f"Required Style 3 font missing: {path}")
    return ImageFont.truetype(str(path), size=size)


def validate_plan(plan: dict) -> dict:
    out = plan["output"]
    assert (out["width"], out["height"], out["fps"]) == (1080, 1920, 30)
    duration = float(out["duration"])
    segments = plan["segments"]
    assert segments and abs(float(segments[0]["start"])) < 1e-6
    assert abs(float(segments[-1]["end"]) - duration) < 1e-6
    assert abs(float(plan["music"]["duration"]) - duration) < 1e-6
    cuts = [float(s["start"]) for s in segments] + [duration]
    beats = [float(x) for x in plan["music"]["beats"]]
    beat_errors = []
    for a, b in zip(segments, segments[1:]):
        assert abs(float(a["end"]) - float(b["start"])) < 1e-6
    for seg in segments:
        assert seg["layout"] in ALLOWED_LAYOUTS, seg["layout"]
        assert float(seg["end"]) > float(seg["start"])
        expected = {"strip": 1, "banner": 1, "square": 1, "video_text": 1, "triptych": 3, "split": 2, "bento": 9, "bento2": 6}[seg["layout"]]
        assert len(seg["shots"]) == expected, (seg["id"], len(seg["shots"]), expected)
        if seg.get("text"):
            value = seg["text"]["value"].upper().strip()
            assert value and value not in FORBIDDEN_OVERLAYS, value
        for shot in seg["shots"]:
            assert shot["source"] in plan["sources"]
            assert float(shot["start"]) >= 0
            assert float(shot["source_end"]) > float(shot["start"])
            assert float(shot["start"]) + float(seg["end"]) - float(seg["start"]) <= float(shot["source_end"]) + 0.075, (seg["id"], shot)
    for cut in cuts:
        beat_errors.append(min(abs(cut - b) for b in beats))
    assert max(beat_errors) <= 0.031, beat_errors
    return {
        "segments": len(segments),
        "duration": duration,
        "fps": out["fps"],
        "resolution": [out["width"], out["height"]],
        "max_cut_to_beat_error_s": round(max(beat_errors), 4),
        "credit_or_title_overlays": 0,
        "isolated_layouts": sorted({s["layout"] for s in segments}),
    }


def _source_crop(frame: np.ndarray, crop: list[int]) -> np.ndarray:
    x, y, w, h = crop
    return frame[y : y + h, x : x + w]


def decode_shot(source_path: str, source_spec: dict, shot: dict, start: float, duration: float, fps_out: int, count: int) -> list[np.ndarray]:
    """Seek once, then decode sequentially; no per-output-frame random seeks."""
    cap = cv2.VideoCapture(source_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: {source_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 23.976)
    start_frame = max(0, int(round(start * fps)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current = start_frame
    frames: list[np.ndarray] = []
    last = None
    for n in range(count):
        target = int(round((start + n / fps_out) * fps))
        while current <= target:
            ok, frame = cap.read()
            current += 1
            if not ok:
                break
            frame = _source_crop(frame, source_spec["crop"])
            last = cv2.resize(frame, (CACHE_W, CACHE_H), interpolation=cv2.INTER_AREA)
        if last is None:
            cap.release()
            raise RuntimeError(f"Decode failed at {start:.3f}s in {source_path}")
        frames.append(last.copy())
    cap.release()
    if len(frames) != count:
        raise RuntimeError("Internal decode count mismatch")
    return frames


def _fit_crop(frame: np.ndarray, tw: int, th: int, focus: float, zoom: float) -> np.ndarray:
    h, w = frame.shape[:2]
    target_aspect = tw / th
    crop_h = h / zoom
    crop_w = crop_h * target_aspect
    if crop_w > w / zoom:
        crop_w = w / zoom
        crop_h = crop_w / target_aspect
    cx = float(np.clip(focus, 0.0, 1.0)) * w
    cy = h * 0.5
    x0 = float(np.clip(cx - crop_w / 2, 0, w - crop_w))
    y0 = float(np.clip(cy - crop_h / 2, 0, h - crop_h))
    patch = cv2.getRectSubPix(frame, (max(2, int(crop_w)), max(2, int(crop_h))), (x0 + crop_w / 2, y0 + crop_h / 2))
    return cv2.resize(patch, (tw, th), interpolation=cv2.INTER_CUBIC)


def _warm_halation(frame: np.ndarray) -> np.ndarray:
    """Style 3 warm coral/gold highlights; no Style A/B LUT or filter."""
    f = frame.astype(np.float32) / 255.0
    f[..., 2] *= 1.035
    f[..., 1] *= 1.008
    f[..., 0] *= 0.972
    f = (f - 0.5) * 1.035 + 0.5
    gray = cv2.cvtColor(np.clip(f, 0, 1), cv2.COLOR_BGR2GRAY)
    f = gray[..., None] * 0.16 + f * 0.84
    lum = cv2.cvtColor(np.clip(f, 0, 1), cv2.COLOR_BGR2GRAY)
    highlights = np.clip((lum - 0.64) / 0.36, 0, 1)[..., None]
    bloom = cv2.GaussianBlur(f * highlights, (0, 0), 7.0)
    f = 1.0 - (1.0 - np.clip(f, 0, 1)) * (1.0 - 0.13 * bloom)
    return (np.clip(f, 0, 1) * 255.0).astype(np.uint8)


def _rects(layout: str) -> list[tuple[int, int, int, int]]:
    x, y, w, h = 24, 744, 1032, 432
    if layout in {"strip", "video_text"}:
        return [(x, y, w, h)]
    if layout == "banner":
        return [(24, 800, 1032, 320)]
    if layout == "square":
        return [(324, 744, 432, 432)]
    if layout == "triptych":
        return [(108 + i * 292, y, 280, h) for i in range(3)]
    if layout == "split":
        return [(234, y, 300, h), (546, y, 300, h)]
    rows, cols, gap = (3, 3, 10) if layout == "bento" else (2, 3, 10)
    rects = []
    for r in range(rows):
        y0 = y + round(r * (h - gap * (rows - 1)) / rows) + r * gap
        y1 = y + round((r + 1) * (h - gap * (rows - 1)) / rows) + r * gap
        for c in range(cols):
            x0 = x + round(c * (w - gap * (cols - 1)) / cols) + c * gap
            x1 = x + round((c + 1) * (w - gap * (cols - 1)) / cols) + c * gap
            rects.append((x0, y0, x1 - x0, y1 - y0))
    return rects


def _union(rects: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return x0, y0, x1 - x0, y1 - y0


def _text_mask(value: str, kind: str, max_w: int, max_h: int) -> Image.Image:
    size = max(24, max_h)
    while size > 20:
        font = _font(kind, size)
        probe = Image.new("L", (8, 8))
        draw = ImageDraw.Draw(probe)
        box = draw.textbbox((0, 0), value, font=font, stroke_width=0)
        tw, th = box[2] - box[0], box[3] - box[1]
        if tw <= max_w and th <= max_h:
            mask = Image.new("L", (tw + 24, th + 24), 0)
            d = ImageDraw.Draw(mask)
            d.text((12 - box[0], 12 - box[1]), value, font=font, fill=255)
            return mask
        size -= 2
    raise RuntimeError(f"Cannot fit text: {value}")


def _apply_text(canvas: np.ndarray, rect: tuple[int, int, int, int], spec: dict, local_t: float, segment_dur: float) -> None:
    x, y, w, h = rect
    value = spec["value"].upper()
    kind = spec["kind"]
    position = spec.get("position", "top_left")
    max_h = 150 if kind == "serif" else (112 if position == "top_left" else 124)
    if w < 700:
        max_h = 82
    mask = _text_mask(value, kind, int(w * 0.91), max_h)
    entry = 0.18
    p = float(np.clip(local_t / entry, 0, 1))
    ease = 1 - (1 - p) ** 3
    alpha = ease
    y_shift = int(round((1 - ease) * 24))
    if position == "center":
        tx = x + (w - mask.width) // 2
        ty = y + (h - mask.height) // 2 + y_shift
    else:
        tx = x + int(w * 0.045)
        ty = y + int(h * 0.075) + y_shift
    overlay = Image.new("RGBA", (canvas.shape[1], canvas.shape[0]), (0, 0, 0, 0))
    shadow = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    shadow_patch = Image.new("RGBA", mask.size, (0, 0, 0, int(150 * alpha)))
    shadow_patch.putalpha(mask.point(lambda v: int(v * 0.60 * alpha)))
    shadow.paste(shadow_patch, (tx + 4, ty + 6), shadow_patch)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    overlay = Image.alpha_composite(overlay, shadow)
    ink = Image.new("RGBA", mask.size, (247, 241, 229, int(255 * alpha)))
    ink.putalpha(mask.point(lambda v: int(v * alpha)))
    overlay.paste(ink, (tx, ty), ink)
    base = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    canvas[:] = cv2.cvtColor(np.asarray(base.convert("RGB")), cv2.COLOR_RGB2BGR)


def _video_type(panel: np.ndarray, value: str, local_t: float) -> np.ndarray:
    h, w = panel.shape[:2]
    mask = _text_mask(value, "video", int(w * 0.92), int(h * 0.48))
    p = float(np.clip(local_t / 0.24, 0, 1))
    ease = 1 - (1 - p) ** 3
    bg = cv2.GaussianBlur(panel, (0, 0), 5.0)
    bg = (bg.astype(np.float32) * 0.30).astype(np.uint8)
    bright = np.clip(panel.astype(np.float32) * 1.16 + 5, 0, 255).astype(np.uint8)
    m = Image.new("L", (w, h), 0)
    m.paste(mask, ((w - mask.width) // 2, (h - mask.height) // 2))
    mask_np = (np.asarray(m).astype(np.float32) / 255.0 * ease)[..., None]
    out = bg.astype(np.float32) * (1 - mask_np) + bright.astype(np.float32) * mask_np
    # Warm glow hugs the live-video letters, never a parametric logo.
    glow = np.asarray(m.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255.0
    out[..., 2] += glow * 24 * ease
    out[..., 1] += glow * 7 * ease
    return np.clip(out, 0, 255).astype(np.uint8)


def render_frame(segment: dict, decoded: list[list[np.ndarray]], n: int, count: int) -> np.ndarray:
    canvas = np.zeros((1920, 1080, 3), dtype=np.uint8)
    rects = _rects(segment["layout"])
    progress = n / max(1, count - 1)
    local_t = n / 30.0
    panel_images = []
    for i, rect in enumerate(rects):
        x, y, w, h = rect
        focus = float(segment["shots"][i].get("focus", 0.5))
        zoom = 1.0 + 0.032 * progress + 0.004 * (i % 3)
        panel = _fit_crop(decoded[i][n], w, h, focus, zoom)
        panel = _warm_halation(panel)
        if segment["layout"] in {"bento", "bento2"}:
            delay = i * 0.055
            a = float(np.clip((local_t - delay) / 0.13, 0, 1))
            if a <= 0:
                continue
            if a < 1:
                panel = (panel.astype(np.float32) * a).astype(np.uint8)
        panel_images.append((rect, panel))
        canvas[y : y + h, x : x + w] = panel
    if segment["layout"] == "video_text":
        x, y, w, h = rects[0]
        canvas[y : y + h, x : x + w] = _video_type(panel_images[0][1], segment["text"]["value"].upper(), local_t)
    elif segment.get("text"):
        _apply_text(canvas, _union(rects), segment["text"], local_t, float(segment["end"]) - float(segment["start"]))
    return canvas


def _decode_segment(plan: dict, source_paths: dict[str, str], segment: dict, preview_only: bool) -> tuple[list[list[np.ndarray]], int]:
    fps = int(plan["output"]["fps"])
    # Allocate by cumulative timeline boundaries so rounded segment counts
    # always sum to exactly round(total_duration * fps).
    count = max(1, int(round(float(segment["end"]) * fps)) - int(round(float(segment["start"]) * fps)))
    duration = count / fps
    def one(shot):
        return decode_shot(source_paths[shot["source"]], plan["sources"][shot["source"]], shot, float(shot["start"]), duration, fps, count)
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(segment["shots"]))) as pool:
        decoded = list(pool.map(one, segment["shots"]))
    return decoded, count


def render_preview(plan: dict, source_paths: dict[str, str], out_jpg: Path) -> None:
    tiles = []
    full_dir = out_jpg.parent / "maverick_style3_frames"
    full_dir.mkdir(parents=True, exist_ok=True)
    for seg in plan["segments"]:
        decoded, count = _decode_segment(plan, source_paths, seg, True)
        n = max(0, int(count * 0.56))
        frame = render_frame(seg, decoded, n, count)
        cv2.imwrite(str(full_dir / f"{seg['id']}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 93])
        thumb = cv2.resize(frame, (180, 320), interpolation=cv2.INTER_AREA)
        tile = np.zeros((346, 180, 3), dtype=np.uint8)
        tile[:320] = thumb
        cv2.putText(tile, f"{seg['start']:05.2f} {seg['id'][:18]}", (4, 337), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(tile)
        print(f"preview {seg['id']}", flush=True)
    while len(tiles) < 15:
        tiles.append(np.zeros((346, 180, 3), dtype=np.uint8))
    sheet = np.vstack([np.hstack(tiles[i : i + 5]) for i in range(0, 15, 5)])
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_jpg), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def render_full(plan: dict, source_paths: dict[str, str], song_path: str, out_mp4: Path, work_dir: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for full render")
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    video_only = work_dir / "style3_video_only.mp4"
    audio_wav = work_dir / "style3_song_section.wav"
    fps = int(plan["output"]["fps"])
    duration = float(plan["output"]["duration"])
    cmd = [
        ffmpeg, "-y", "-v", "warning", "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", "1080x1920", "-r", str(fps), "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_only),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    written = 0
    try:
        for seg in plan["segments"]:
            decoded, count = _decode_segment(plan, source_paths, seg, False)
            for n in range(count):
                frame = render_frame(seg, decoded, n, count)
                proc.stdin.write(frame.tobytes())
                written += 1
                if written % 60 == 0:
                    print(f"rendered {written} frames", flush=True)
            del decoded
    finally:
        if proc.stdin:
            proc.stdin.close()
    rc = proc.wait()
    if rc:
        raise RuntimeError(f"ffmpeg video encoder exited {rc}")
    expected = int(round(duration * fps))
    if written != expected:
        raise RuntimeError(f"Frame count mismatch: wrote {written}, expected {expected}")

    start = float(plan["music"]["start"])
    fade_out = max(0.0, duration - 0.18)
    _run([
        ffmpeg, "-y", "-v", "warning", "-ss", f"{start:.6f}", "-t", f"{duration:.3f}",
        "-i", song_path, "-af", f"aresample=48000,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.04,afade=t=out:st={fade_out:.3f}:d=0.18",
        "-c:a", "pcm_s24le", str(audio_wav),
    ])
    p1 = subprocess.run([
        ffmpeg, "-hide_banner", "-nostats", "-i", str(audio_wav),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-",
    ], capture_output=True, text=True, check=True)
    j0, j1 = p1.stderr.rfind("{"), p1.stderr.rfind("}") + 1
    measured = json.loads(p1.stderr[j0:j1])
    loud = (
        f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={measured['input_i']}:"
        f"measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}:"
        f"measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}:linear=true,"
        "alimiter=limit=0.84:level=false:attack=5:release=50"
    )
    _run([
        ffmpeg, "-y", "-v", "warning", "-i", str(video_only), "-i", str(audio_wav),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", loud,
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-t", f"{duration:.3f}", "-movflags", "+faststart", str(out_mp4),
    ])
    (work_dir / "loudnorm_first_pass.json").write_text(json.dumps(measured, indent=2))
    print(f"MASTER {out_mp4} frames={written}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--source", action="append", default=[], help="key=/path/to/source.mp4")
    ap.add_argument("--song", default=None)
    ap.add_argument("--mode", choices=["validate", "preview", "render"], default="validate")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default="/tmp/style3_maverick_work")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    report = validate_plan(plan)
    print(json.dumps({"plan_validation": report}, indent=2), flush=True)
    if args.mode == "validate":
        Path(args.out).write_text(json.dumps(report, indent=2))
        return
    source_paths = {}
    for item in args.source:
        key, value = item.split("=", 1)
        source_paths[key] = value
    assert set(source_paths) == set(plan["sources"]), (source_paths.keys(), plan["sources"].keys())
    if args.mode == "preview":
        render_preview(plan, source_paths, Path(args.out))
    else:
        assert args.song, "--song is required for render"
        render_full(plan, source_paths, args.song, Path(args.out), Path(args.work))


if __name__ == "__main__":
    main()
