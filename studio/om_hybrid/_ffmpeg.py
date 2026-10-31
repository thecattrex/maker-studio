"""_ffmpeg.py — Self-healing FFmpeg + FFprobe resolver for container snapshots.

In Arena sandboxes, `/home/user` persists across turns while `/tmp/vidtools/{ffmpeg,ffprobe}`
can reset when a container resumes from snapshot. `get_ffmpeg()` and `get_ffprobe()`
locate the binaries immediately if present, or run `studio/bootstrap.sh` once on demand
so tools never fail with `FileNotFoundError`.
"""
from __future__ import annotations

import os
import shutil
import subprocess

_CACHED_FFMPEG: str | None = None
_CACHED_FFPROBE: str | None = None


def _run_bootstrap() -> None:
    boot = "/home/user/studio/bootstrap.sh"
    if os.path.exists(boot):
        subprocess.run(["bash", boot], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_ffmpeg() -> str:
    global _CACHED_FFMPEG
    if _CACHED_FFMPEG and os.path.exists(_CACHED_FFMPEG):
        return _CACHED_FFMPEG

    candidates = [
        os.environ.get("FFMPEG", ""),
        "/tmp/vidtools/ffmpeg",
        "/home/user/bin/ffmpeg",
        shutil.which("ffmpeg") or "",
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.access(c, os.X_OK):
            _CACHED_FFMPEG = c
            return c

    _run_bootstrap()
    for c in ("/tmp/vidtools/ffmpeg", "/home/user/bin/ffmpeg"):
        if os.path.exists(c) and os.access(c, os.X_OK):
            _CACHED_FFMPEG = c
            return c
    return "ffmpeg"


def get_ffprobe() -> str:
    global _CACHED_FFPROBE
    if _CACHED_FFPROBE and os.path.exists(_CACHED_FFPROBE):
        return _CACHED_FFPROBE

    candidates = [
        os.environ.get("FFPROBE", ""),
        "/tmp/vidtools/ffprobe",
        "/home/user/bin/ffprobe",
        shutil.which("ffprobe") or "",
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.access(c, os.X_OK):
            _CACHED_FFPROBE = c
            return c

    _run_bootstrap()
    for c in ("/tmp/vidtools/ffprobe", "/home/user/bin/ffprobe"):
        if os.path.exists(c) and os.access(c, os.X_OK):
            _CACHED_FFPROBE = c
            return c
    return "ffprobe"
