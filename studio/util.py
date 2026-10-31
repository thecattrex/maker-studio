"""Shared helpers: ffmpeg discovery, probing, process running."""
import json
import os
import re
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
STUDIO = os.path.join(HOME, "studio")
CACHE = os.path.join(STUDIO, "cache")
ASSETS = os.path.join(HOME, "assets")
FONTS = os.path.join(ASSETS, "fonts")


def find_tool(name):
    for c in (os.environ.get(name.upper()), f"/tmp/vidtools/{name}",
              os.path.join(ASSETS, "bin", name), shutil.which(name)):
        if c and os.path.exists(c):
            return c
    return None


FFMPEG = find_tool("ffmpeg")


def ensure_ffmpeg():
    """Download a static ffmpeg into /tmp if it disappeared (sandbox reset)."""
    global FFMPEG
    if FFMPEG and os.path.exists(FFMPEG):
        return FFMPEG
    os.makedirs("/tmp/vidtools", exist_ok=True)
    url = ("https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
           "ffmpeg-master-latest-linux64-gpl.tar.xz")
    run(["curl", "-sL", "--max-time", "300", "-o", "/tmp/ff.tar.xz", url])
    run(["tar", "-xf", "/tmp/ff.tar.xz", "-C", "/tmp",
         "ffmpeg-master-latest-linux64-gpl/bin/ffmpeg"])
    shutil.move("/tmp/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg", "/tmp/vidtools/ffmpeg")
    run(["rm", "-rf", "/tmp/ff.tar.xz", "/tmp/ffmpeg-master-latest-linux64-gpl"])
    os.chmod("/tmp/vidtools/ffmpeg", 0o755)
    FFMPEG = "/tmp/vidtools/ffmpeg"
    return FFMPEG


def run(cmd, timeout=1800, check=False, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(map(str, cmd))}\n"
                           f"{(r.stderr or '')[-2500:]}")
    return r


def ensure_dirs():
    for d in (CACHE, os.path.join(STUDIO, "out"), os.path.join(STUDIO, "work"),
              os.path.join(STUDIO, "clips")):
        os.makedirs(d, exist_ok=True)


def probe(path):
    """Duration / size / codecs straight from `ffmpeg -i` (no ffprobe needed)."""
    ensure_ffmpeg()
    r = run([FFMPEG, "-hide_banner", "-i", path])
    txt = (r.stderr or "") + (r.stdout or "")
    dur = 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", txt)
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    vm = re.search(r"Video:\s*([\w\-]+).*?(\d{2,5})x(\d{2,5})", txt, re.S)
    am = re.search(r"Audio:\s*([\w\-]+)", txt)
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", txt)
    return {"duration": round(dur, 3),
            "width": int(vm.group(2)) if vm else None,
            "height": int(vm.group(3)) if vm else None,
            "fps": float(fps.group(1)) if fps else None,
            "vcodec": vm.group(1) if vm else None,
            "acodec": am.group(1) if am else None,
            "has_audio": bool(am),
            "path": path}


def slug(s, n=48):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return (s[:n] or "x")


def cache_path(kind, key):
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, f"{kind}-{slug(key, 60)}.json")


def load_cache(kind, key):
    p = cache_path(kind, key)
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            return None
    return None


def save_cache(kind, key, data):
    json.dump(data, open(cache_path(kind, key), "w"), ensure_ascii=False)


def ffmpeg_cmd(args):
    return [ensure_ffmpeg(), "-hide_banner", "-nostdin", "-y", *args]


def log(*a):
    print(*a, file=sys.stderr, flush=True)
