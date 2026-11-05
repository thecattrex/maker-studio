#!/usr/bin/env python3
"""Verify the GitHub Style A setup WITHOUT creating or rendering any video."""
from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "studio"


def _ram_gb() -> float:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / (1024 * 1024), 2)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def _tool_version(command: str) -> dict[str, object]:
    executable = shutil.which(command)
    if not executable:
        return {"available": False}
    proc = subprocess.run(
        [executable, "-version"], capture_output=True, text=True, timeout=30, check=False
    )
    return {
        "available": proc.returncode == 0,
        "path": executable,
        "version": (proc.stdout or proc.stderr).splitlines()[0]
        if (proc.stdout or proc.stderr)
        else "unknown",
    }


def run_setup_check(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    required_files = [
        ".github/workflows/cloud_render.yml",
        "studio/cloud/hq_worker.py",
        "studio/cloud/stylea_worker.py",
        "studio/cloud/requirements-base.txt",
        "studio/styleA/validate_plan.py",
        "studio/styleA/rules.json",
        "studio/styleA/CORRECTIONS.md",
    ]
    files = {name: (ROOT / name).is_file() for name in required_files}

    required_modules = ["numpy", "scipy", "cv2", "soundfile", "PIL", "requests", "mediapipe"]
    modules = {name: importlib.util.find_spec(name) is not None for name in required_modules}

    import_code = (
        "import sys; "
        f"sys.path.insert(0, {str(STUDIO)!r}); "
        "from om_hybrid.zohair_edit import render_zohair_jigsaw_edit; "
        "print('Style A engine import OK')"
    )
    try:
        engine = subprocess.run(
            [sys.executable, "-c", import_code],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        engine_report: dict[str, object] = {
            "passed": engine.returncode == 0,
            "detail": (engine.stdout or engine.stderr).strip()[-1200:],
        }
    except subprocess.TimeoutExpired:
        engine_report = {"passed": False, "detail": "engine import timed out"}

    # Validate the rule file itself, not any project media plan.
    validation_code = (
        "import sys,json; "
        f"sys.path.insert(0, {str(STUDIO)!r}); "
        "from styleA.validate_plan import _load_rules; "
        "r=_load_rules(); assert len(r['rules']) >= 1; "
        "print(json.dumps({'schema_version': r['schema_version'], 'rules': len(r['rules'])}))"
    )
    rules = subprocess.run(
        [sys.executable, "-c", validation_code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    ffmpeg = _tool_version("ffmpeg")
    ffprobe = _tool_version("ffprobe")
    passed = (
        all(files.values())
        and all(modules.values())
        and bool(ffmpeg["available"])
        and bool(ffprobe["available"])
        and bool(engine_report["passed"])
        and rules.returncode == 0
    )
    report: dict[str, object] = {
        "mode": "setup_check",
        "passed": passed,
        "video_rendered": False,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "runner_ram_gb": _ram_gb(),
        "runner_cpus": multiprocessing.cpu_count(),
        "disk_free_gb": round(shutil.disk_usage(out_dir).free / (1024 ** 3), 2),
        "required_files": files,
        "required_modules": modules,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "engine_import": engine_report,
        "rules_check": {
            "passed": rules.returncode == 0,
            "detail": (rules.stdout or rules.stderr).strip()[-1200:],
        },
        "workflow": "manual workflow_dispatch only",
        "asset_cache": os.environ.get("MAKER_ASSET_CACHE", "/tmp/maker_stylea_cache"),
    }
    (out_dir / "setup_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "studio" / "cloud_out")
    args = parser.parse_args()
    report = run_setup_check(args.out_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
