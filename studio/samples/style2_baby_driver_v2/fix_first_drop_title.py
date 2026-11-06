#!/usr/bin/env python3
"""Rebuild only montage clip 1 with the same engine pipeline, then place its title after shake.

The cloud render applied z_depth_text before impact shake, which pushed BABY DRIVER offscreen.
This correction discards that clip's rendered frames, reproduces crop -> optical velocity -> CC
-> shake/flash from the locked plan, and applies the same neon title last so it remains readable.
All other frames pass through; the normalized audio is stream-copied.
"""
from __future__ import annotations

import gc
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import om_hybrid.aura_edit as ae  # noqa: E402

FPS, W, H, BOX_Y, BOX_H = 30, 1080, 1920, 360, 1200
FF = "/var/tmp/baby2_pydeps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2"
TITLE_START, TITLE_FRAMES = 366, 67


def add_stable_title(frame: np.ndarray, layers) -> np.ndarray:
    base = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    comp = Image.alpha_composite(base, layers[0])
    comp = Image.alpha_composite(comp, layers[1])
    return cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)


def rebuild_first_clip(plan: dict) -> list[np.ndarray]:
    ae.get_ffmpeg = lambda: FF
    mc = plan["montage_clips"][0]
    with tempfile.TemporaryDirectory(prefix="baby2_title_fix_") as td:
        raw = ae._slice_clip_frames_30fps(plan["sources"]["movie"], float(mc["start_s"]),
                                          float(mc["src_dur_s"]), Path(td), "first_clip")
        cropped = ae._crop_9x10_smart(raw, W, BOX_H, zoom_start=1.02, zoom_end=1.09,
                                      detect_fn=None, cx_override=mc.get("cx_override"))
        del raw
        vel = ae._velocity_resample_optical(cropped, TITLE_FRAMES)
        del cropped
        gc.collect()
        graded = [ae.apply_viral_4k_quality_cc(f, strength=1.08, sat_boost=0.40) for f in vel]
        del vel
        gc.collect()
        shaken = ae._apply_impact_shake_and_flash(
            graded,
            shake_px=float(mc.get("shake_px", 16.0)),
            flash_peak=float(mc.get("flash_peak", 0.35)),
            shockwave=bool(mc.get("shockwave", True)),
            whip_dir=str(mc.get("whip_dir", "none")),
            clip_start_s=12.2,
            drop_s=12.2,
            bpm=float(plan["bpm"]),
        )
        del graded
        gc.collect()
    layers = ae._prepare_roto_hero_bg_layer(W, BOX_H, "BABY DRIVER", "#FF2E63")
    return [add_stable_title(f, layers) for f in shaken]


def save_audit(frames: list[np.ndarray], out: Path) -> None:
    ids = [0, 6, 12, 18, 24, 33, 39, 45, 54, 66]
    sheet = Image.new("RGB", (216 * 5, 384 * 2), "black")
    for i, n in enumerate(ids):
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[BOX_Y:BOX_Y + BOX_H] = frames[n]
        im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).resize((216, 384))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 216, 25), fill="black")
        d.text((5, 5), f"f{TITLE_START + n} {(TITLE_START + n) / FPS:.2f}s", fill="white")
        sheet.paste(im, ((i % 5) * 216, (i // 5) * 384))
    sheet.save(out, quality=94)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: fix_first_drop_title.py INPUT_MP4 OUTPUT_MP4")
    src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    plan_path = Path(__file__).resolve().parents[2] / "styleB/plan_baby_driver_style2_v2.json"
    plan = json.loads(plan_path.read_text())
    first = rebuild_first_clip(plan)
    if len(first) != TITLE_FRAMES:
        raise SystemExit(f"First clip has {len(first)} frames, expected {TITLE_FRAMES}")
    audit = out.parent / "drop_title_fixed_audit.jpg"
    save_audit(first, audit)

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {src}")
    log = Path("/var/tmp/style2_baby_driver_v2/qa/title_fix_ffmpeg.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FF, "-hide_banner", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-i", str(src), "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-threads", "2",
           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
           "-metadata", "title=Baby Driver | Style 2 Movie Focus", str(out)]
    count = 0
    with log.open("wb") as logf:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
        assert proc.stdin is not None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if TITLE_START <= count < TITLE_START + TITLE_FRAMES:
                replacement = np.zeros((H, W, 3), dtype=np.uint8)
                replacement[BOX_Y:BOX_Y + BOX_H] = first[count - TITLE_START]
                frame = replacement
            proc.stdin.write(frame.tobytes())
            count += 1
        proc.stdin.close()
        rc = proc.wait()
    cap.release()
    if rc != 0 or count != 900:
        raise SystemExit(f"ffmpeg rc={rc}; frames={count}; expected=900; see {log}")
    report = {"output": str(out), "frames": count, "rebuilt_frame_range": [TITLE_START, TITLE_START + TITLE_FRAMES],
              "title": "BABY DRIVER", "title_mode": "same neon title applied after impact shake; stable/full-width",
              "audio": "stream copy", "audit_sheet": str(audit), "ffmpeg_log": str(log)}
    (out.parent / "title_fix_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
