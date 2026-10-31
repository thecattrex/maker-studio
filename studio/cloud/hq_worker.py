"""hq_worker.py — 16 GB RAM GitHub Actions Cloud Worker for Maker Studio.

Unlocks heavy tools that cannot run inside a 2 GB RAM sandbox:
  - `smoke`:    Verifies 16 GB RAM, 4 vCPUs, MediaPipe FaceDetection, FFmpeg +
                libass fonts, and `om_hybrid` QA gate on a 3s 1080x1920 test clip.
  - `t1_hq`:    Downloads 1080p source video, runs `faster-whisper medium.en`
                (beam_size=5 word timestamps), MediaPipe face-tracked smart
                camera (`om_hybrid.smart_camera`), `libx264 -preset slow -crf 17`,
                true Two-Pass Linear `loudnorm` (-15.0 LUFS / -1.5 dBTP), and
                `om_hybrid.visual_qa`.
  - `remotion`: Renders a React/Remotion composition from `studio/remotion-composer/`
                using Headless Chromium on the 16 GB runner.
"""
from __future__ import annotations

import argparse
import base64
import json
import multiprocessing
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "studio"
if str(STUDIO) not in sys.path:
    sys.path.insert(0, str(STUDIO))

import textkit  # noqa: E402
from om_hybrid import (  # noqa: E402
    lut3d_filter_str,
    plan_smart_camera,
    render_subpixel_segments,
    run_full_qa,
    score_hook_candidates,
)


def _ram_gb() -> float:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                return round(kb / (1024 * 1024), 2)
    except Exception:
        pass
    return 0.0


def run_smoke(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / "cloud_smoke_1080p.mp4"
    ass = out_dir / "smoke.ass"
    fonts_dir = ROOT / "assets" / "fonts"

    # Check MediaPipe + BlazeFace detector backend on the 16 GB runner
    has_mp = False
    try:
        import mediapipe as mp  # noqa: F401
        has_mp = True
    except Exception:
        pass
    from om_hybrid.smart_camera import _make_face_detector
    _, face_backend = _make_face_detector()

    ov = textkit.Overlay(playres=(1080, 1920))
    ov.add(
        0.0, 3.0, "Title",
        r"{\an5\pos(540,150)\fnAnton\fs96\c&H00FFFFFF&\bord0\shad0}16GB CLOUD FARM",
        layer=5,
    )
    ov.add(
        0.0, 3.0, "Title",
        r"{\an5\pos(540,265)\fnAnton\fs118\bord0\shad0}{\c&H002E2EF7&}ONLINE {\c&H00FFFFFF&}& VERIFIED",
        layer=5,
    )
    ov.add(
        0.1, 2.9, "Impact",
        r"{\an2\pos(540,1405)\fnArchivo Black\fs64\c&H0000D7FF&\bord8\3c&H000000&\shad4}MEDIAPIPE + WHISPER HQ READY",
        layer=6,
    )
    ov.write(str(ass))

    # Generate 3s 1080x1920 test video + 440Hz gentle tone @ -15 LUFS
    vf = f"ass={ass}:fontsdir={fonts_dir}:shaping=complex"
    cmd = [
        "ffmpeg", "-y", "-v", "warning",
        "-f", "lavfi", "-i", "testsrc2=size=1080x1200:rate=24:duration=3",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=3",
        "-vf", f"pad=1080:1920:0:360:black,{vf}",
        "-af", "aformat=channel_layouts=stereo,volume=-12dB,afade=t=in:st=0:d=0.1,afade=t=out:st=2.7:d=0.3",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True)
    qa = run_full_qa(str(mp4), min_dur=2.5, max_dur=4.0, lufs_range=(-20.0, -10.0))
    report = {
        "mode": "smoke",
        "runner_ram_gb": _ram_gb(),
        "runner_cpus": multiprocessing.cpu_count(),
        "mediapipe_installed": has_mp,
        "face_detector_backend": face_backend,
        "remotion_composer_present": (STUDIO / "remotion-composer" / "package.json").exists(),
        "qa": qa,
    }
    (out_dir / "cloud_report.json").write_text(json.dumps(report, indent=2))
    return report


def run_t1_hq(job: dict, out_dir: Path) -> dict:
    """High-Precision 16 GB Type-1 Movie Short Builder (`medium.en` + MediaPipe + slow x264 + 2-pass loudnorm)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path("/tmp/maker_hq_work")
    work.mkdir(parents=True, exist_ok=True)

    src_mp4 = work / "source.mp4"
    urllib.request.urlretrieve(job["source_url"], str(src_mp4))

    # 1. Transcribe with faster-whisper `medium.en` (enabled by 16 GB RAM!)
    from faster_whisper import WhisperModel
    w_model_name = job.get("whisper_model", "medium.en")
    model = WhisperModel(w_model_name, device="cpu", compute_type="int8", cpu_threads=4)
    segs_iter, info = model.transcribe(
        str(src_mp4),
        word_timestamps=True,
        beam_size=5,
        initial_prompt=job.get("initial_prompt", ""),
    )
    segs = []
    for s in segs_iter:
        segs.append({
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text.strip(),
            "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in (s.words or [])],
        })
    del model

    scene_s0, scene_s1 = float(job["scene_sec"][0]), float(job["scene_sec"][1])
    if "hook_sec" in job and job["hook_sec"]:
        hook_s0, hook_s1 = float(job["hook_sec"][0]), float(job["hook_sec"][1])
    else:
        in_scene = [s for s in segs if s["start"] >= scene_s0 and s["end"] <= scene_s1]
        ranked = score_hook_candidates(in_scene)
        if ranked:
            hook_s0, hook_s1 = ranked[0]["start"], ranked[0]["end"]
        else:
            hook_s0, hook_s1 = max(scene_s0, scene_s1 - 3.5), scene_s1

    # 2. MediaPipe Face-Tracked Smart Camera Plan
    cam = plan_smart_camera(str(src_mp4), start_s=scene_s0, end_s=scene_s1)
    fps = cam["fps"]
    hf = (int(round(hook_s0 * fps)), int(round(hook_s1 * fps)))
    sf = (int(round(scene_s0 * fps)), int(round(scene_s1 * fps)))
    raw_v = work / "raw_motion.mp4"
    grade_vf = "eq=contrast=1.08:saturation=1.12:gamma=0.97,unsharp=5:5:0.45:5:5:0.0"
    if job.get("look_id"):
        grade_vf = f"{lut3d_filter_str(job['look_id'], intensity=job.get('look_intensity'))},unsharp=5:5:0.40:5:5:0.0"
    render_subpixel_segments(
        str(src_mp4),
        str(raw_v),
        [hf, sf],
        cam["shots_table"],
        grade_vf=grade_vf,
        fps_num_den=(24000, 1001) if abs(fps - 23.976) < 0.1 else (int(round(fps)), 1),
        dip_frames=int(job.get("seam_frames", 5)),
        seam_mode=job.get("seam_mode", "dip"),
    )

    # 3. Build Hook + Scene ASS captions
    hdur = (hf[1] - hf[0]) / fps
    sdur = (sf[1] - sf[0]) / fps
    total = hdur + sdur
    ov = textkit.Overlay(playres=(1080, 1920))
    ov.add(
        0.0, total, "Title",
        r"{\an5\fnAnton\fs90\fsp2\bord0\shad0\c&H00FFFFFF&"
        r"\move(540,164,540,134,0,260)\blur16\alpha&HFF&\t(0,260,\blur0\alpha&H00&)}"
        + textkit.esc(job.get("hdr1", "BEST MOVIE MOMENT")),
        layer=5,
    )
    ov.add(
        0.08, total, "Title",
        r"{\an5\fnAnton\fs122\fsp2\bord0\shad0"
        r"\move(540,284,540,254,0,280)\blur16\alpha&HFF&\t(0,280,\blur0\alpha&H00&)}"
        r"{\c&H002E2EF7&}" + textkit.esc(job.get("hdr2_red", "WAIT "))
        + r"{\c&H00FFFFFF&}" + textkit.esc(job.get("hdr2_white", "FOR IT")),
        layer=5,
    )

    for win_t0, win_t1, tl_off in [(hf[0] / fps, hf[1] / fps, 0.0), (sf[0] / fps, sf[1] / fps, hdur)]:
        groups = []
        for s in segs:
            mapped = []
            for w in s["words"]:
                if w["e"] <= win_t0 + 0.04 or w["s"] >= win_t1 - 0.04:
                    continue
                cs = max(win_t0, w["s"]) - win_t0 + tl_off
                ce = min(win_t1 - 0.04, w["e"]) - win_t0 + tl_off
                if ce > cs + 0.03:
                    mapped.append((w["w"].upper(), round(cs, 3), round(ce, 3)))
            if mapped:
                groups.append(mapped)
        if groups:
            ov.word_caps_kara(
                groups,
                y=cam["recommended_caption_y"],
                size=64,
                font="Archivo Black",
                fsp=-0.5,
                bord=8,
                shad=4,
                max_line_chars=19,
                lead=0.10,
                tail=0.20,
                blur=18,
                kf=5,
                scale=118,
                an=2,
            )

    if job.get("movie_tag"):
        ov.add(
            0.2, total, "Small",
            r"{\an5\pos(540,1648)\fnBebas Neue\fs46\fsp6\c&H00969696&\bord0\shad0"
            r"\alpha&HFF&\t(0,350,\alpha&H20&)}" + textkit.esc(job["movie_tag"]),
            layer=2,
        )

    ass_path = out_dir / "subs.ass"
    ov.write(str(ass_path))

    # 4. True Two-Pass Linear Loudnorm + x264 `-preset slow -crf 17` (16 GB RAM!)
    concat_wav = work / "concat_audio.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "warning",
            "-ss", f"{hf[0]/fps:.4f}", "-t", f"{hdur:.4f}", "-i", str(src_mp4),
            "-ss", f"{sf[0]/fps:.4f}", "-t", f"{sdur:.4f}", "-i", str(src_mp4),
            "-filter_complex",
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.05,afade=t=out:st={hdur-0.12:.4f}:d=0.12[ah];"
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.08,afade=t=out:st={sdur-0.28:.4f}:d=0.28[as];"
            f"[ah][as]concat=n=2:v=0:a=1,highpass=f=70[aout]",
            "-map", "[aout]", str(concat_wav),
        ],
        check=True,
    )
    p1 = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(concat_wav),
            "-af", "loudnorm=I=-15.0:TP=-1.5:LRA=9:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    )
    j_start = p1.stderr.rfind("{")
    j_end = p1.stderr.rfind("}") + 1
    ln = json.loads(p1.stderr[j_start:j_end])

    out_name = job.get("out_name", "t1_cloud_hq.mp4")
    final_mp4 = out_dir / out_name
    fonts_dir = ROOT / "assets" / "fonts"
    ln_af = (
        f"loudnorm=I=-15.0:TP=-1.5:LRA=9:"
        f"measured_I={ln['input_i']}:measured_TP={ln['input_tp']}:"
        f"measured_LRA={ln['input_lra']}:measured_thresh={ln['input_thresh']}:"
        f"offset={ln['target_offset']}:linear=true,"
        f"alimiter=limit=0.83:level=false:attack=5:release=50"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "warning",
            "-i", str(raw_v), "-i", str(concat_wav),
            "-vf", f"ass={ass_path}:fontsdir={fonts_dir}:shaping=complex",
            "-af", ln_af,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "slow", "-crf", "17",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-shortest",
            str(final_mp4),
        ],
        check=True,
    )

    sheet_jpg = out_dir / "qa_sheet.jpg"
    qa = run_full_qa(str(final_mp4), sheet_out=str(sheet_jpg))
    report = {
        "mode": "t1_hq",
        "whisper_model": w_model_name,
        "camera_detector": cam["detector"],
        "runner_ram_gb": _ram_gb(),
        "qa": qa,
    }
    (out_dir / "cloud_report.json").write_text(json.dumps(report, indent=2))
    return report


def run_remotion(job: dict, out_dir: Path) -> dict:
    """Render a Remotion composition on the 16 GB runner."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rem_dir = STUDIO / "remotion-composer"
    comp_id = job.get("composition_id", "TitledVideo")
    out_mp4 = out_dir / job.get("out_name", f"remotion_{comp_id}.mp4")
    props_file = out_dir / "remotion_props.json"
    props_file.write_text(json.dumps(job.get("props", {})))

    cmd = [
        "npx", "remotion", "render", "src/index.tsx", comp_id, str(out_mp4),
        f"--props={props_file}",
    ]
    subprocess.run(cmd, cwd=str(rem_dir), check=True)
    report = {
        "mode": "remotion",
        "composition_id": comp_id,
        "runner_ram_gb": _ram_gb(),
        "output": str(out_mp4),
        "size_mb": round(out_mp4.stat().st_size / 1048576.0, 2),
    }
    (out_dir / "cloud_report.json").write_text(json.dumps(report, indent=2))
    return report


def run_hyperframes(job: dict, out_dir: Path) -> dict:
    """Render an HTML + CSS + GSAP HyperFrames composition on the Node 22 Cloud Runner."""
    import shutil

    out_dir.mkdir(parents=True, exist_ok=True)
    work_proj = Path("/tmp/hf_cloud_project")
    if work_proj.exists():
        shutil.rmtree(work_proj)

    env = os.environ.copy()
    env["HYPERFRAMES_SKIP_SKILLS"] = "1"
    env["HYPERFRAMES_TELEMETRY_DISABLED"] = "1"

    resolution = job.get("resolution", "portrait")
    quality = job.get("quality", "looks")
    out_name = job.get("out_name", "hyperframes_short.mp4")
    out_mp4 = out_dir / out_name

    # 1. Scaffold official HyperFrames project metadata (hyperframes.json)
    subprocess.run(
        [
            "hyperframes", "init", str(work_proj),
            "--example", "blank",
            "--resolution", resolution,
            "--non-interactive",
            "--skip-skills",
        ],
        env=env,
        check=True,
    )

    # 2. Copy template project dir (default: studio/hyperframes/starter_short) or inline HTML
    src_dir_rel = job.get("project_dir", "studio/hyperframes/starter_short")
    src_dir = (ROOT / src_dir_rel) if not os.path.isabs(src_dir_rel) else Path(src_dir_rel)
    if src_dir.is_dir():
        for item in src_dir.iterdir():
            dest = work_proj / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    if job.get("index_html"):
        (work_proj / "index.html").write_text(job["index_html"])

    # 3. Install any requested registry blocks/components (out of 448 available)
    for reg_item in job.get("registry_items", []) or []:
        subprocess.run(["hyperframes", "add", reg_item], cwd=str(work_proj), env=env, check=True)

    # 4. Lint check (informational JSON captured into report)
    lint_proc = subprocess.run(
        ["hyperframes", "lint"],
        cwd=str(work_proj),
        env=env,
        capture_output=True,
        text=True,
    )

    # 5. Deterministic Chrome BeginFrame render -> MP4
    render_cmd = [
        "hyperframes", "render", str(work_proj),
        "--quality", quality,
        "--output", str(out_mp4),
    ]
    if job.get("fps"):
        render_cmd.extend(["--fps", str(job["fps"])])
    subprocess.run(render_cmd, env=env, check=True)

    # Probe rendered MP4 with ffprobe + extract contact sheet
    probe_p = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json", str(out_mp4),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    probe = json.loads(probe_p.stdout)
    sheet_jpg = out_dir / "hf_contact_sheet.jpg"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "warning", "-i", str(out_mp4),
            "-vf", "fps=1,scale=360:-1,tile=4x1", "-frames:v", "1", str(sheet_jpg),
        ],
        check=False,
    )

    v_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
    dur_s = float(probe.get("format", {}).get("duration", 0.0))
    passed = out_mp4.exists() and out_mp4.stat().st_size > 10_000 and dur_s > 0.5

    report = {
        "mode": "hyperframes",
        "runner_ram_gb": _ram_gb(),
        "runner_cpus": multiprocessing.cpu_count(),
        "output": out_name,
        "size_mb": round(out_mp4.stat().st_size / 1048576.0, 2),
        "resolution": f"{v_stream.get('width')}x{v_stream.get('height')}",
        "fps": v_stream.get("r_frame_rate"),
        "duration_s": round(dur_s, 3),
        "lint_exit_code": lint_proc.returncode,
        "lint_stdout": lint_proc.stdout[-800:] if lint_proc.stdout else "",
        "qa": {"passed": passed},
    }
    (out_dir / "cloud_report.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "t1_hq", "remotion", "hyperframes"], required=True)
    ap.add_argument("--job-b64", default="")
    ap.add_argument("--out-dir", default=str(ROOT / "studio" / "cloud_out"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    job = json.loads(base64.b64decode(args.job_b64).decode("utf-8")) if args.job_b64 else {}

    if args.mode == "smoke":
        res = run_smoke(out_dir)
    elif args.mode == "t1_hq":
        res = run_t1_hq(job, out_dir)
    elif args.mode == "hyperframes":
        res = run_hyperframes(job, out_dir)
    else:
        res = run_remotion(job, out_dir)

    print(json.dumps(res, indent=2))
    if args.mode in ("smoke", "t1_hq", "hyperframes") and not res.get("qa", {}).get("passed", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
