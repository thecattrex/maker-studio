#!/usr/bin/env python3
"""Clip-specific correction: keep ANSEL ELGORT z-depth title readable on a tight close-up.

The cloud render already applied the established roto title at its default y=13%.
On this close-up the person mask hides it. This pass preserves the same title/glow/roto
grammar, moves only the title to the top-safe position on montage clip 1, and copies
the already-normalized audio stream without another audio encode.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from om_hybrid.aura_edit import _hex_rgb, _pick_font  # noqa: E402
from om_hybrid.viral_vfx import PersonSegmenter  # noqa: E402

FPS, W, H, BOX_Y, BOX_H = 30, 1080, 1920, 360, 1200
TITLE, ACCENT, TITLE_Y = "ANSEL ELGORT", "#FF2E63", -40


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        p = Path("/var/tmp/dune2_pydeps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2")
        return str(p) if p.exists() else "ffmpeg"


def title_layers(bw: int, bh: int) -> tuple[Image.Image, Image.Image]:
    font = _pick_font(176)
    dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
    tw = dummy.textlength(TITLE, font=font)
    if tw > bw * 0.90:
        font = _pick_font(int(176 * (bw * 0.90) / tw))
        tw = dummy.textlength(TITLE, font=font)
    tx = int((bw - tw) * 0.5)
    ar, ag, ab = _hex_rgb(ACCENT)
    glow = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    fg = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    gd, fd = ImageDraw.Draw(glow), ImageDraw.Draw(fg)
    gd.text((tx, TITLE_Y), TITLE, font=font, fill=(ar, ag, ab, 240),
            stroke_width=8, stroke_fill=(ar, ag, ab, 190))
    for d in range(8, 0, -2):
        fd.text((tx + d, TITLE_Y + d), TITLE, font=font, fill=(18, 10, 6, 200))
    fd.text((tx, TITLE_Y), TITLE, font=font, fill=(255, 248, 232, 252))
    return glow.filter(ImageFilter.GaussianBlur(14)), fg


def composite(frame: np.ndarray, mask: np.ndarray, layers: tuple[Image.Image, Image.Image]) -> np.ndarray:
    box = frame[BOX_Y:BOX_Y + BOX_H]
    base = Image.fromarray(cv2.cvtColor(box, cv2.COLOR_BGR2RGB)).convert("RGBA")
    comp = Image.alpha_composite(base, layers[0])
    comp = Image.alpha_composite(comp, layers[1])
    bg = cv2.cvtColor(np.array(comp.convert("RGB")), cv2.COLOR_RGB2BGR)
    out = np.clip(bg.astype(np.float32) * (1.0 - mask) + box.astype(np.float32) * mask, 0, 255).astype(np.uint8)
    frame[BOX_Y:BOX_Y + BOX_H] = out
    return frame


def clip_range(plan: dict) -> tuple[int, int, int]:
    scene = int(round(float(plan["scene_segments"][0]["dur_s"]) * FPS))
    start = scene + int(plan.get("pre_drop_black_frames", 0))
    c = plan["montage_clips"][0]
    if "dur_s" in c:
        n = max(10, int(round(float(c["dur_s"]) * FPS)))
    else:
        n = max(12, int(round(float(c.get("beats", 2)) * 60.0 / float(plan["bpm"]) * FPS)))
    total = start + sum(
        max(10, int(round(float(c["dur_s"]) * FPS))) if "dur_s" in c
        else max(12, int(round(float(c.get("beats", 2)) * 60.0 / float(plan["bpm"]) * FPS)))
        for c in plan["montage_clips"]
    )
    return start, start + n, total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--plan", type=Path, default=Path(__file__).resolve().parents[2] / "styleB/plan_baby_driver_ansel_style2.json")
    ap.add_argument("--sheet-only", action="store_true")
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text())
    start, end, total = clip_range(plan)
    cap = cv2.VideoCapture(str(args.input))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {args.input}")
    seg = PersonSegmenter()
    layers = title_layers(W, BOX_H)

    if args.sheet_only:
        ids = [start, start + 6, start + 12, start + 18, start + 27, start + 39, start + 51, end - 1]
        sheet = Image.new("RGB", (216 * 4, 384 * 2), "black")
        for i, n in enumerate(ids):
            cap.set(cv2.CAP_PROP_POS_FRAMES, n)
            ok, frame = cap.read()
            if not ok:
                raise SystemExit(f"Cannot decode frame {n}")
            mask = seg.mask(np.ascontiguousarray(frame[BOX_Y:BOX_Y + BOX_H]), feather_px=7)
            frame = composite(frame, mask, layers)
            im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((216, 384))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 216, 24), fill="black")
            d.text((5, 5), f"f{n}  {n / FPS:.2f}s", fill="white")
            sheet.paste(im, ((i % 4) * 216, (i // 4) * 384))
        cap.release()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.output, quality=94)
        print(args.output)
        return

    ff = ffmpeg_exe()
    log_path = Path("/var/tmp/style2_baby_driver/qa/title_fix_ffmpeg.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ff, "-hide_banner", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-i", str(args.input), "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-threads", "2",
           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
           "-metadata", "title=Baby Driver — Ansel Elgort | Style 2", str(args.output)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with log_path.open("wb") as log:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log, stderr=log)
        assert proc.stdin is not None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if start <= count < end:
                mask = seg.mask(np.ascontiguousarray(frame[BOX_Y:BOX_Y + BOX_H]), feather_px=7)
                frame = composite(frame, mask, layers)
            proc.stdin.write(frame.tobytes())
            count += 1
        proc.stdin.close()
        rc = proc.wait()
    cap.release()
    if rc != 0 or count != total:
        raise SystemExit(f"ffmpeg rc={rc}; decoded {count}, expected {total}; see {log_path}")
    print(json.dumps({"output": str(args.output), "frames": count, "title_clip_range": [start, end],
                      "audio": "stream copy", "title_y": TITLE_Y, "log": str(log_path)}, indent=2))


if __name__ == "__main__":
    main()
