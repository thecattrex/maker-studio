"""_ffmpeg.py — Self-healing FFmpeg resolver for container snapshots.

In Arena sandboxes, `/home/user` persists across turns while `/tmp/vidtools/ffmpeg`
can reset when a container resumes from snapshot. `get_ffmpeg()` locates FFmpeg
immediately if present, or runs `studio/bootstrap.sh` once on demand so tools
never fail with `FileNotFoundError: 'ffmpeg'`.
"""
from __future__ import annotations

import os
import shutil
import subprocess

_CACHED_FFMPEG: str | None = None


def get_ffmpeg() -> str:
    global _CACHED_FFMPEG
    if _CACHED_FFMPEG and os.path.exists(_CACHED_FFMPEG):
        return _CACHED_FFMPEG

    candidates = [
        os.environ.get("FFMPEG", ""),
        "/home/user/bin/ffmpeg",
        "/tmp/vidtools/ffmpeg",
        shutil.which("ffmpeg") or "",
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.access(c, os.X_OK):
            _CACHED_FFMPEG = c
            return c

    # Self-heal if `/tmp/vidtools/ffmpeg` was cleared by a container snapshot resume
    boot = "/home/user/studio/bootstrap.sh"
    if os.path.exists(boot):
        subprocess.run(["bash", boot], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for c in ("/home/user/bin/ffmpeg", "/tmp/vidtools/ffmpeg"):
            if os.path.exists(c) and os.access(c, os.X_OK):
                _CACHED_FFMPEG = c
                return c

    return "ffmpeg"
