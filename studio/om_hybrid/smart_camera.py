"""smart_camera.py — Shot-Aware Face/Two-Shot Tracking + Sub-Pixel Lanczos4 Camera.

Upgrades OpenMontage's `face_tracker` + `auto_reframe` with:
  1. Hard camera-cut segmentation BEFORE smoothing (never smears pan across a cut!).
  2. Multi-face / Two-Shot awareness: if two speakers fit inside the 9:10 vertical
     crop window, centers their group midpoint so neither face is clipped; otherwise
     tracks the dominant foreground face smoothly.
  3. Caption-Collision Guard: checks whether detected faces dip into the lower
     caption zone and nudges vertical focus (`fy`) or recommends a safer `caption_y`.
  4. Native-FPS sub-pixel `cv2.warpAffine(..., INTER_LANCZOS4)` rendering with
     optional 4-frame cinema dip-to-black between cold-open hook and main scene.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ._ffmpeg import get_ffmpeg


def smoothstep(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def detect_shots(
    video_path: str,
    start_s: float = 0.0,
    end_s: float | None = None,
    diff_thresh: float = 17.0,
    min_shot_frames: int = 8,
) -> dict[str, Any]:
    """Detect frame-exact hard camera cuts within [start_s, end_s]."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 23.976
    sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    f0 = max(0, int(round(start_s * fps)))
    f1 = n_total if end_s is None else min(n_total, int(round(end_s * fps)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0)

    cuts = [f0]
    prev = None
    for f in range(f0, f1):
        ok, img = cap.read()
        if not ok:
            f1 = f
            break
        g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (160, 90)).astype(np.float32)
        if prev is not None:
            diff = float(np.mean(np.abs(g - prev)))
            if diff > diff_thresh and (f - cuts[-1]) >= min_shot_frames:
                cuts.append(f)
        prev = g
    cap.release()
    if cuts[-1] != f1:
        cuts.append(f1)

    shots = [
        {
            "index": i,
            "f_start": a,
            "f_end": b,
            "t_start": round(a / fps, 3),
            "t_end": round(b / fps, 3),
            "dur": round((b - a) / fps, 3),
        }
        for i, (a, b) in enumerate(zip(cuts[:-1], cuts[1:]))
    ]
    return {
        "width": sw,
        "height": sh,
        "fps": fps,
        "f_start": f0,
        "f_end": f1,
        "shots": shots,
    }


def _make_face_detector():
    """Return a callable `detect(bgr) -> list[(cx, cy, w, h, conf)]` in normalized [0..1] coords."""
    models_dir = Path(__file__).resolve().parent / "models"
    tflite_path = models_dir / "blaze_face_short_range.tflite"

    # 1) Modern MediaPipe Tasks API (0.10.20+ / 2026+) with bundled BlazeFace TFLite
    if tflite_path.exists():
        try:
            import mediapipe as mp  # type: ignore

            try:
                from mediapipe.tasks.python import BaseOptions  # type: ignore
                from mediapipe.tasks.python import vision as mp_vision  # type: ignore
            except ImportError:
                BaseOptions = mp.tasks.BaseOptions  # type: ignore
                mp_vision = mp.tasks.vision  # type: ignore

            opts = mp_vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=str(tflite_path)),
                min_detection_confidence=0.45,
            )
            detector = mp_vision.FaceDetector.create_from_options(opts)

            def _mp_tasks_detect(bgr: np.ndarray):
                h, w = bgr.shape[:2]
                rgb = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                res = detector.detect(mp_img)
                out = []
                for d in getattr(res, "detections", []) or []:
                    bb = d.bounding_box
                    bw = bb.width / max(1.0, float(w))
                    bh = bb.height / max(1.0, float(h))
                    cx = (bb.origin_x + bb.width * 0.5) / max(1.0, float(w))
                    cy = (bb.origin_y + bb.height * 0.5) / max(1.0, float(h))
                    score = float(d.categories[0].score) if getattr(d, "categories", None) else 0.75
                    out.append((cx, cy, bw, bh, score))
                return out

            return _mp_tasks_detect, "mediapipe_blazeface"
        except Exception:
            pass

    # 2) Classic MediaPipe solutions API (older 0.10.x builds)
    try:
        import mediapipe as mp  # type: ignore

        mp_fd = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.45
        )

        def _mp_detect(bgr: np.ndarray):
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            res = mp_fd.process(rgb)
            out = []
            if res.detections:
                for d in res.detections:
                    bb = d.location_data.relative_bounding_box
                    cx = bb.xmin + bb.width * 0.5
                    cy = bb.ymin + bb.height * 0.5
                    out.append((cx, cy, bb.width, bb.height, float(d.score[0])))
            return out

        return _mp_detect, "mediapipe"
    except Exception:
        pass

    # 3) Bundled OpenCV Haar Cascade fallback (works even on OpenCV 5.0 wheels without cv2/data/)
    def _load_cascade(xml_name: str):
        for candidate in (
            models_dir / xml_name,
            Path(getattr(getattr(cv2, "data", None), "haarcascades", "")) / xml_name,
        ):
            if candidate.is_file():
                cas = cv2.CascadeClassifier(str(candidate))
                if not cas.empty():
                    return cas
        return None

    frontal = _load_cascade("haarcascade_frontalface_default.xml")
    profile = _load_cascade("haarcascade_profileface.xml")

    def _cv_detect(bgr: np.ndarray):
        h, w = bgr.shape[:2]
        scale = 640.0 / max(1, w)
        small = cv2.resize(bgr, (640, max(1, int(round(h * scale)))))
        gray = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        sh_s, sw_s = gray.shape[:2]
        min_sz = max(24, int(sh_s * 0.08))

        boxes = []
        for cas, base_conf in ((frontal, 0.85), (profile, 0.65)):
            if cas is None or cas.empty():
                continue
            rects = cas.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(min_sz, min_sz))
            for (x, y, rw, rh) in rects:
                boxes.append((
                    (x + rw * 0.5) / sw_s,
                    (y + rh * 0.5) / sh_s,
                    rw / sw_s,
                    rh / sh_s,
                    base_conf,
                ))
        # Deduplicate overlapping frontal/profile hits
        boxes.sort(key=lambda b: b[2] * b[3] * b[4], reverse=True)
        kept = []
        for b in boxes:
            if all(abs(b[0] - k[0]) > 0.08 or abs(b[1] - k[1]) > 0.08 for k in kept):
                kept.append(b)
        return kept

    return _cv_detect, "opencv_haar"


def plan_smart_camera(
    video_path: str,
    start_s: float,
    end_s: float,
    band_w: int = 1080,
    band_h: int = 1200,
    sample_per_shot: int = 6,
    zoom_range: tuple[float, float] = (1.00, 1.055),
) -> dict[str, Any]:
    """Build a shot-segmented sub-pixel camera table + caption-collision check.

    Returns:
      {
        "detector": "mediapipe" | "opencv_haar",
        "fps": float,
        "shots_table": [[f_start, f_end, fx0, fx1, fy0, fy1, z0, z1], ...],
        "recommended_caption_y": int,
        "collision_warnings": [...]
      }
    """
    shot_meta = detect_shots(video_path, start_s=start_s, end_s=end_s)
    sw, sh, fps = shot_meta["width"], shot_meta["height"], shot_meta["fps"]
    base_scale = max(band_w / max(1, sw), band_h / max(1, sh))
    crop_w_norm = (band_w / base_scale) / max(1, sw)  # ~0.5625 for 16:9 -> 9:10

    detect_fn, det_name = _make_face_detector()
    cap = cv2.VideoCapture(video_path)

    shots_table = []
    collision_warnings = []
    lowest_face_bottom_band = 0.0

    for sh_info in shot_meta["shots"]:
        a, b = sh_info["f_start"], sh_info["f_end"]
        n = max(1, b - a)
        step = max(1, n // max(1, sample_per_shot))
        sample_frames = list(range(a, b, step))[:sample_per_shot]

        xs, ys, max_bottoms = [], [], []
        for f_idx in sample_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ok, frame = cap.read()
            if not ok:
                continue
            dets = detect_fn(frame)
            if not dets:
                continue
            # Sort largest/most confident faces first
            dets.sort(key=lambda d: (d[2] * d[3]) * d[4], reverse=True)
            if len(dets) >= 2:
                # Two-shot check: if top 2 faces fit inside 88% of crop_w_norm, center both!
                d0, d1 = dets[0], dets[1]
                left_edge = min(d0[0] - d0[2] * 0.5, d1[0] - d1[2] * 0.5)
                right_edge = max(d0[0] + d0[2] * 0.5, d1[0] + d1[2] * 0.5)
                if (right_edge - left_edge) <= crop_w_norm * 0.88:
                    cx = 0.5 * (left_edge + right_edge)
                    cy = 0.5 * (d0[1] + d1[1])
                    f_bot = max(d0[1] + d0[3] * 0.5, d1[1] + d1[3] * 0.5)
                else:
                    cx, cy = d0[0], d0[1]
                    f_bot = d0[1] + d0[3] * 0.5
            else:
                d0 = dets[0]
                cx, cy = d0[0], d0[1]
                f_bot = d0[1] + d0[3] * 0.5

            # Convert desired normalized center `cx` into `focus_x` in [0..1]
            # where x0_norm = (1 - crop_w_norm) * fx  and  cx = x0_norm + crop_w_norm/2
            denom = max(1e-4, 1.0 - crop_w_norm)
            fx = (cx - 0.5 * crop_w_norm) / denom
            fx = max(0.05, min(0.95, fx))
            fy = max(0.25, min(0.65, cy))
            xs.append(fx)
            ys.append(fy)
            max_bottoms.append(f_bot)

        if xs:
            if len(xs) >= 3:
                fx0 = float(np.median(xs[: max(1, len(xs) // 2)]))
                fx1 = float(np.median(xs[len(xs) // 2 :]))
            else:
                fx0 = fx1 = float(np.median(xs))
            # Clamp excessive intra-shot whip unless truly tracking movement
            if abs(fx1 - fx0) < 0.03:
                fx0 = fx1 = 0.5 * (fx0 + fx1)
            fy0 = fy1 = float(np.median(ys))
            shot_bot = max(max_bottoms)
            lowest_face_bottom_band = max(lowest_face_bottom_band, shot_bot)
            if shot_bot > 0.74:
                collision_warnings.append(
                    f"Shot {sh_info['index']} [{sh_info['t_start']}-{sh_info['t_end']}s]: "
                    f"face bottom reaches {shot_bot:.2f} of height (close to lower caption zone)."
                )
        else:
            fx0, fx1, fy0, fy1 = 0.50, 0.50, 0.46, 0.46

        z0, z1 = zoom_range
        # Shorter shots get subtler push-in so motion pace feels natural
        if sh_info["dur"] < 2.2:
            z1 = z0 + (z1 - z0) * 0.55
        shots_table.append([
            a, b,
            round(fx0, 3), round(fx1, 3),
            round(fy0, 3), round(fy1, 3),
            round(z0, 4), round(z1, 4),
        ])

    cap.release()
    rec_cap_y = 1405 if lowest_face_bottom_band <= 0.74 else 1455
    return {
        "detector": det_name,
        "width": sw,
        "height": sh,
        "fps": fps,
        "shots_table": shots_table,
        "recommended_caption_y": rec_cap_y,
        "collision_warnings": collision_warnings,
    }


def render_subpixel_segments(
    src_path: str,
    out_raw_mp4: str,
    segments_frames: list[tuple[int, int]],
    shots_table: list[list[float]],
    grade_vf: str = "eq=contrast=1.08:saturation=1.12:gamma=0.97,unsharp=5:5:0.45:5:5:0.0",
    canvas_size: tuple[int, int] = (1080, 1920),
    top_band: int = 360,
    band_size: tuple[int, int] = (1080, 1200),
    fps_num_den: tuple[int, int] = (24000, 1001),
    dip_frames: int = 4,
    seam_mode: str = "dip",
) -> None:
    """Render 1 or more frame segments with sub-pixel Lanczos4 motion & HyperFrames seam cuts.

    `seam_mode` options between segments (adapted from `heygen-com/hyperframes` Cut-the-Curve):
      - "dip": classic cinema dip-to-black (`dip_frames` each side)
      - "zoom_through": forward Z velocity-matched push (1.0->1.18 exit, 0.84->1.0 entry + peak blur)
      - "whip_pan": lateral speed-ramp whip with 1D horizontal motion-blur streak
      - "rack_focus": DSLR focus-pull Gaussian blur-cut across the seam
    """
    W, H = canvas_size
    BAND_W, BAND_H = band_size
    fps_num, fps_den = fps_num_den
    seam_len = max(4, dip_frames) if seam_mode != "dip" else dip_frames

    def _params(f_idx: int):
        for a, b, fx0, fx1, fy0, fy1, z0, z1 in shots_table:
            if a <= f_idx < b:
                u = smoothstep((f_idx - a) / max(1, b - a - 1))
                return (
                    fx0 + (fx1 - fx0) * u,
                    fy0 + (fy1 - fy0) * u,
                    z0 + (z1 - z0) * u,
                )
        return 0.50, 0.46, 1.00

    cap = cv2.VideoCapture(src_path)
    sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    base_scale = max(BAND_W / max(1, sw), BAND_H / max(1, sh))

    cmd = [
        get_ffmpeg(), "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", f"{fps_num}/{fps_den}", "-i", "-",
        "-vf", grade_vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-threads", "2",
        out_raw_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    n_segs = len(segments_frames)

    for seg_i, (f_start, f_end) in enumerate(segments_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(f_start))
        seg_len = int(f_end) - int(f_start)
        for i, f_idx in enumerate(range(int(f_start), int(f_end))):
            ok, frame = cap.read()
            if not ok:
                break
            fx, fy, z = _params(f_idx)

            # Determine seam phase: ("out", p in 0..1) or ("in", p in 0..1)
            seam_phase = None
            seam_p = 0.0
            if n_segs > 1 and seam_len > 0:
                if seg_i < n_segs - 1 and i >= seg_len - seam_len:
                    seam_phase = "out"
                    seam_p = (i - (seg_len - seam_len) + 1) / float(seam_len)
                elif seg_i > 0 and i < seam_len:
                    seam_phase = "in"
                    seam_p = i / float(max(1, seam_len))

            if seam_mode == "zoom_through" and seam_phase is not None:
                if seam_phase == "out":
                    z *= 1.0 + 0.18 * (seam_p ** 2.6)
                else:
                    z *= 0.85 + 0.15 * (1.0 - ((1.0 - seam_p) ** 2.6))

            sc = base_scale * z
            crop_w, crop_h = BAND_W / sc, BAND_H / sc
            x0 = max(0.0, min(sw - crop_w, (sw - crop_w) * fx))
            y0 = max(0.0, min(sh - crop_h, (sh - crop_h) * fy))

            tx_extra = 0.0
            if seam_mode == "whip_pan" and seam_phase is not None:
                if seam_phase == "out":
                    tx_extra = -0.22 * BAND_W * (seam_p ** 2.8)
                else:
                    tx_extra = 0.22 * BAND_W * ((1.0 - seam_p) ** 2.8)

            M = np.array([[sc, 0.0, -x0 * sc + tx_extra], [0.0, sc, -y0 * sc]], dtype=np.float32)
            band_img = cv2.warpAffine(
                frame, M, (BAND_W, BAND_H),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_REPLICATE,
            )

            if seam_phase is not None:
                peak = seam_p if seam_phase == "out" else (1.0 - seam_p)
                if seam_mode == "dip":
                    alpha = 1.0 - peak
                    band_img = (band_img.astype(np.float32) * max(0.0, alpha)).astype(np.uint8)
                elif seam_mode == "zoom_through":
                    k = int(round(1 + 16 * (peak ** 2))) | 1
                    if k >= 3:
                        band_img = cv2.GaussianBlur(band_img, (k, k), 0)
                elif seam_mode == "whip_pan":
                    kx = max(1, int(round(1 + 48 * (peak ** 1.8))))
                    band_img = cv2.blur(band_img, (kx, 1))
                elif seam_mode == "rack_focus":
                    k = int(round(1 + 24 * (peak ** 1.6))) | 1
                    if k >= 3:
                        band_img = cv2.GaussianBlur(band_img, (k, k), 0)

            canvas.fill(0)
            canvas[top_band : top_band + BAND_H, 0:W] = band_img
            assert proc.stdin is not None
            proc.stdin.write(canvas.tobytes())

    if proc.stdin:
        proc.stdin.close()
    rc = proc.wait()
    cap.release()
    if rc != 0:
        raise RuntimeError(f"render_subpixel_segments failed with exit code {rc}")
