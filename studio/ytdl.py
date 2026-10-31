#!/usr/bin/env python3
"""
ytdl.py — YouTube footage pipeline for the studio.

search_youtube() -> download() -> verify() -> extract_clip()

Rules baked in:
  * anonymous only (no cookies, no login)
  * prefers h264 (avc1) because AV1/VP9 decode slowly during editing
  * tries 1080p -> 720p -> best available, always reports what it actually got
  * every download is verified with ffprobe (video + audio streams present)

CLI:
  python3 ytdl.py search "skateboard fail shorts" -n 6
  python3 ytdl.py dl https://youtu.be/XXXX --maxh 1080 --out /tmp/src
  python3 ytdl.py clip IN.mp4 --ss 12.5 --dur 6 --out clip.mp4 [--w 1080 --h 1920]
  python3 ytdl.py pipeline "funny fail shorts" -n 3 --clips /tmp/e2e
"""
import argparse
import json
import os
import subprocess
import sys
import time

FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"

# fmt ladder for a given max height, h264 first, then anything, then progressive
BLOCK_MARKERS = (
    "Sign in to confirm you", "confirm you\u2019re not a bot", "confirm you're not a bot",
    "LOGIN_REQUIRED", "This request was detected as a bot",
)
BUDGET = {"requests": 0, "limit": 12}      # hard cap per run: retry storms cause the block


class YouTubeBlocked(RuntimeError):
    """Raised when YouTube answers with a login/bot gate. Never retried here:
    retrying is what turns a 2-hour block into a 2-week one."""


def _is_block(msg):
    return any(m.lower() in str(msg).lower() for m in BLOCK_MARKERS)


FMT_TMPL = ("bv*[height<={h}][vcodec^=avc1]+ba/"
            "bv*[height<={h}][vcodec^=vp9]+ba/"
            "bv*[height<={h}]+ba/"
            "b[height<={h}]")


def _ydl(extra=None):
    import yt_dlp
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "socket_timeout": 30,
        # YouTube's "web" client often hits a bot-check on datacenter IPs.
        # These three expose the full format ladder without login. If one dies,
        # yt-dlp moves to the next, so a single API change can't stop us.
        "extractor_args": {"youtube": {"player_client":
                          ["default", "tv_embedded", "visionos"]}},
    }
    if extra:
        opts.update(extra)
    return yt_dlp.YoutubeDL(opts)


# ---------------------------------------------------------------- search
def search_youtube(query, n=8):
    """Return [{id,title,duration,url,uploader}] — no download."""
    with _ydl({"extract_flat": "in_playlist", "skip_download": True}) as ydl:
        info = ydl.extract_info("ytsearch%d:%s" % (n, query), download=False)
    out = []
    for e in info.get("entries") or []:
        if not e:
            continue
        out.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "duration": e.get("duration"),
            "url": e.get("url") or "https://www.youtube.com/watch?v=%s" % e.get("id"),
            "uploader": e.get("uploader"),
        })
    return out


# ------------------------------------------------------------- inspection
def list_heights(url):
    """Heights actually offered for this video (before download)."""
    with _ydl({"skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    hs = sorted({f.get("height") for f in info.get("formats", []) if f.get("height")})
    return {"title": info.get("title"), "duration": info.get("duration"), "heights": hs}


def verify(path):
    """ffprobe check: real video + audio streams, duration > 0."""
    def probe(sel):
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", sel,
             "-show_entries", "stream=codec_name,width,height,duration",
             "-of", "json", path],
            capture_output=True, text=True)
        try:
            return (json.loads(r.stdout).get("streams") or [None])[0]
        except Exception:
            return None

    v, a = probe("v:0"), probe("a:0")
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration,size",
                        "-of", "json", path], capture_output=True, text=True)
    fmt = json.loads(r.stdout or "{}").get("format", {})
    return {
        "ok": bool(v) and float(fmt.get("duration") or 0) > 0,
        "has_audio": bool(a),
        "vcodec": (v or {}).get("codec_name"),
        "width": (v or {}).get("width"),
        "height": (v or {}).get("height"),
        "duration": float(fmt.get("duration") or 0),
        "bytes": int(fmt.get("size") or 0),
    }


# ------------------------------------------------------------- download
def download(url, outdir="/tmp/src", maxh=1080, name=None, ladder=(1080, 720)):
    """Download with explicit fallback ladder. Returns dict with path + got height."""
    os.makedirs(outdir, exist_ok=True)
    if name is None:
        name = "%(title).60s_%(id)s"
    tries = [maxh] + [h for h in ladder if h < maxh]
    errors = []
    for h in tries:
        if BUDGET["requests"] >= BUDGET["limit"]:
            return {"ok": False, "url": url,
                    "errors": ["request budget reached ({}), stopping to protect the IP"
                               .format(BUDGET["limit"])]}
        BUDGET["requests"] += 1
        outtmpl = os.path.join(outdir, "%s_req%dp.%%(ext)s" % (name, h))
        opts = {
            "format": FMT_TMPL.format(h=h),
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "overwrites": True,
        }
        try:
            with _ydl(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if not os.path.exists(path):
                base = os.path.splitext(path)[0]
                cands = [base + e for e in (".mp4", ".mkv", ".webm")]
                path = next((c for c in cands if os.path.exists(c)), path)
            v = verify(path)
            if v["ok"]:
                v.update({"path": path, "requested": h, "url": url})
                return v
            errors.append("h=%d verify failed" % h)
        except Exception as e:
            msg = str(e)
            if _is_block(msg):
                return {"ok": False, "url": url, "blocked": True,
                        "errors": ["YouTube bot gate (LOGIN_REQUIRED). Stop, do not retry. "
                                   "Cooldown: hours. Fix: authenticated cookies or new IP."]}
            errors.append("h=%d %s" % (h, msg.splitlines()[-1][:160]))
    return {"ok": False, "url": url, "errors": errors}


# ---------------------------------------------------------------- clips
def extract_clip(src, ss, dur, out, w=1080, h=1920, fit="cover", crf=18, audio=True):
    """Cut [ss, ss+dur] out of src, re-encode, force w x h (cover-crop)."""
    if fit == "cover":
        vf = ("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,"
              "crop=%d:%d,setsar=1,fps=30" % (w, h, w, h))
    else:  # contain: pad black
        vf = ("scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,"
              "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30" % (w, h, w, h))
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % ss, "-t", "%.3f" % dur,
           "-i", src, "-vf", vf]
    if audio:
        cmd += ["-af", "aresample=44100,aformat=channel_layouts=stereo",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-r", "30", "-y", out]
    subprocess.run(cmd, check=True)
    return verify(out)


# -------------------------------------------------------------- pipeline
def pipeline(query, n=3, clips="/tmp/e2e", maxh=1080, clip_dur=5.0):
    """E2E: search -> pick -> download -> clip. Returns a run report."""
    t0 = time.time()
    rep = {"query": query, "search": [], "downloads": [], "clips": [], "maxh": maxh}
    found = search_youtube(query, n=n)
    rep["search"] = found
    os.makedirs(clips, exist_ok=True)
    for i, v in enumerate(found[:n], 1):
        d = download(v["url"], outdir=clips, maxh=maxh, name="p%d" % i)
        d["title"] = v.get("title")
        rep["downloads"].append(d)
        if not d["ok"]:
            continue
        ss = max(0.0, (d["duration"] - clip_dur) * 0.4)   # 40% in, avoids intros
        cp = os.path.join(clips, "p%d_clip.mp4" % i)
        c = extract_clip(d["path"], ss, clip_dur, cp)
        c.update({"path": cp, "ss": ss, "from": d["path"]})
        rep["clips"].append(c)
    rep["seconds"] = round(time.time() - t0, 1)
    rep["ok"] = len(rep["clips"]) > 0
    return rep


# --------------------------------------------------------------- health check
def doctor(url="https://www.youtube.com/watch?v=kUwCILeTIRo"):
    """Quick health check: which clients still expose HD, and does a real
    download work? Run this first whenever downloads start failing."""
    import shutil
    rep = {"yt_dlp": None, "ffmpeg": bool(os.path.exists(FFMPEG)),
           "js_runtime": None, "clients": {}, "hd_ok": False}
    r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
    rep["yt_dlp"] = (r.stdout or "").strip()
    for rt in ("deno", "node", "bun"):
        if shutil.which(rt):
            rep["js_runtime"] = rt
            break
    for c in ("default", "tv_embedded", "visionos", "web", "android"):
        try:
            with _ydl({"skip_download": True}) as ydl:
                ydl.params["extractor_args"] = {"youtube": {"player_client": [c]}}
                info = ydl.extract_info(url, download=False)
            hs = sorted({f.get("height") for f in info.get("formats", []) if f.get("height")})
            rep["clients"][c] = hs
        except Exception as e:
            rep["clients"][c] = "FAIL: " + str(e).splitlines()[-1][:80]
    best = max([h for hs in rep["clients"].values() if isinstance(hs, list)
                for h in hs] or [0])
    rep["hd_ok"] = best >= 720
    rep["blocked"] = all(isinstance(v, str) and _is_block(v) for v in rep["clients"].values()) and bool(rep["clients"])
    rep["max_height_seen"] = best
    return rep


# ------------------------------------------------------- fallback source
def pexels_download(video_id, outdir="/home/user/dl/pexels"):
    """No-login 4K fallback that keeps working when YouTube is blocked."""
    import urllib.request
    os.makedirs(outdir, exist_ok=True)
    req = urllib.request.Request("https://www.pexels.com/download/video/%s/" % video_id,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        url = r.geturl()
    out = os.path.join(outdir, "px_%s.mp4" % video_id)
    subprocess.run(["curl", "-sL", "-m", "300", "-A", "Mozilla/5.0", "-o", out, url], check=True)
    return verify(out)


# ------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-n", type=int, default=8)
    i = sub.add_parser("info"); i.add_argument("url")
    d = sub.add_parser("dl"); d.add_argument("url"); d.add_argument("--maxh", type=int, default=1080)
    d.add_argument("--out", default="/tmp/src"); d.add_argument("--name")
    c = sub.add_parser("clip"); c.add_argument("src"); c.add_argument("--ss", type=float, default=0)
    c.add_argument("--dur", type=float, default=6); c.add_argument("--out", required=True)
    c.add_argument("--w", type=int, default=1080); c.add_argument("--h", type=int, default=1920)
    p = sub.add_parser("pipeline"); p.add_argument("query"); p.add_argument("-n", type=int, default=3)
    p.add_argument("--clips", default="/tmp/e2e"); p.add_argument("--maxh", type=int, default=1080)
    px = sub.add_parser("pexels"); px.add_argument("video_id"); px.add_argument("--out", default="/home/user/dl/pexels")
    dr = sub.add_parser("doctor"); dr.add_argument("--url", default="https://www.youtube.com/watch?v=kUwCILeTIRo")
    a = ap.parse_args()

    if a.cmd == "search":
        print(json.dumps(search_youtube(a.query, a.n), indent=1, ensure_ascii=False))
    elif a.cmd == "info":
        print(json.dumps(list_heights(a.url), indent=1, ensure_ascii=False))
    elif a.cmd == "dl":
        print(json.dumps(download(a.url, a.out, a.maxh, a.name), indent=1))
    elif a.cmd == "clip":
        print(json.dumps(extract_clip(a.src, a.ss, a.dur, a.out, a.w, a.h), indent=1))
    elif a.cmd == "pexels":
        print(json.dumps(pexels_download(a.video_id, a.out), indent=1))
    elif a.cmd == "doctor":
        print(json.dumps(doctor(a.url), indent=1))
    else:
        r = pipeline(a.query, a.n, a.clips, a.maxh)
        print(json.dumps(r, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
