"""Find source material on the internet (YouTube via yt-dlp), and download it."""
import glob
import json
import os
import sys

from util import ensure_ffmpeg, log, probe, run, slug

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

# YouTube search filters (sp=)
SHORT = "EgIYAQ%253D%253D"      # under 4 minutes
MEDIUM = "EgIYAw%253D%253D"     # 4-20 minutes
SORT_VIEWS = "CAMSAhAB"         # sort by view count


def _ytdlp():
    return [sys.executable, "-m", "yt_dlp", "--no-warnings"]


def search(query, n=12, short=True, sort_views=False, min_dur=4, max_dur=None,
           min_views=0):
    """Return candidate videos: id, title, duration, views, url."""
    sp = []
    if short:
        sp.append(SHORT)
    if sort_views:
        sp.append(SORT_VIEWS)
    url = "https://www.youtube.com/results?search_query=" + \
          query.replace(" ", "+") + ("&sp=" + "+".join(sp) if sp else "")
    cmd = _ytdlp() + ["--flat-playlist", "--playlist-end", str(max(n * 4, 20)),
                      "--print", "%(id)s\t%(duration)s\t%(view_count)s\t%(title)s\t%(uploader)s",
                      url]
    r = run(cmd, timeout=180)
    out = []
    for line in (r.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 5 or not parts[0] or parts[0] == "NA":
            continue
        try:
            d = float(parts[1])
        except ValueError:
            continue
        vc = 0
        try:
            vc = int(parts[2])
        except ValueError:
            pass
        if d < min_dur or (max_dur and d > max_dur) or vc < min_views:
            continue
        out.append({"id": parts[0], "duration": d, "views": vc,
                    "title": parts[3], "uploader": parts[4],
                    "url": f"https://www.youtube.com/watch?v={parts[0]}"})
        if len(out) >= n:
            break
    return out


def download(url, outdir=None, max_h=1080, section=None):
    """Download a video. Returns local path (+ info)."""
    ensure_ffmpeg()
    from util import FFMPEG
    outdir = outdir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")
    os.makedirs(outdir, exist_ok=True)
    vid = None
    cmd = _ytdlp() + ["--no-playlist", "--ffmpeg-location", os.path.dirname(FFMPEG),
                      "-f", f"bv*[height<={max_h}]+ba/b[height<={max_h}]/b",
                      "--merge-output-format", "mp4",
                      "--user-agent", UA,
                      "-o", os.path.join(outdir, "%(id)s.%(ext)s")]
    if section:
        cmd += ["--download-sections", f"*{section[0]}-{section[1]}"]
    cmd += [url]
    r = run(cmd, timeout=1800)
    if r.returncode != 0:
        # retry with a generic client (helps with some age/format walls)
        r2 = run(cmd[:-1] + ["--extractor-args", "youtube:player_client=android", url],
                 timeout=1800)
        if r2.returncode != 0:
            raise RuntimeError("download failed:\n" + ((r2.stderr or r.stderr or "")[-1500:]))
    return {"path": _best_file(outdir, url), "info": probe(_best_file(outdir, url))}


def _best_file(outdir, url):
    """Pick the downloaded file that has BOTH video and audio (prefer merged)."""
    from urllib.parse import parse_qs, urlparse
    u = urlparse(url)
    q = parse_qs(u.query)
    vid = (q.get("v") or [None])[0]
    if not vid:
        import re as _re
        m = _re.match(r"^/(?:shorts/)?([A-Za-z0-9_-]{6,})", u.path or "")
        if m and "youtu" in (u.netloc or ""):
            vid = m.group(1)
    pats = []
    if vid:
        pats.append(os.path.join(outdir, vid + ".*"))
    pats.append(os.path.join(outdir, "*"))
    cands = []
    for pat in pats:
        for p in glob.glob(pat):
            if p.endswith((".part", ".ytdl", ".json")):
                continue
            if p not in cands:
                cands.append(p)
    def rank(p):
        i = probe(p)
        score = 0
        if i.get("width"):
            score += 10
        if i.get("has_audio"):
            score += 20                       # audio is mandatory
        if ".f" not in os.path.basename(p):   # merged file, not a fragment
            score += 5
        return (score, os.path.getsize(p))
    if not cands:
        raise RuntimeError("no file downloaded")
    return max(cands, key=rank)


def guess_queries(topic, mode="rank"):
    """Turn a topic into good search queries."""
    t = topic.strip()
    if mode == "rank":
        return [
            f"{t} compilation 2026",
            f"best {t} moments",
            f"{t} top moments compilation",
            f"{t} fails compilation",
        ]
    return [
        f"{t} edit 4k",
        f"{t} best scenes",
        f"{t} fight scene 4k",
        f"{t} movie clip",
    ]


def find_hindi_source(movie, scene=None, log_fn=log, strict=True):
    """Find a clip of the movie whose audio is genuinely HINDI (dubbed).

    We do not dub anything ourselves - we locate the existing Hindi version.
    """
    base = f"{movie} hindi dubbed {scene or 'scene'}".strip()
    queries = [
        base,
        f"{movie} hindi dubbed movie clip",
        f"{movie} full movie hindi dubbed",
        f"{movie} हिंदी में",
        f"{movie} movie explained hindi",          # usually uses the hindi dub audio
    ]
    seen, cands = set(), []
    for q in queries:
        log_fn(f"  hindi search: {q}")
        try:
            for c in search(q, n=8, short=False, min_dur=45, max_dur=4000):
                if c["id"] in seen:
                    continue
                seen.add(c["id"])
                cands.append(c)
        except Exception as e:
            log_fn(f"  (failed: {e})")
    if not cands:
        return []

    HINDI = ("hindi", "हिंदी", "dubbed", "डब", "explained in hindi", "in hindi")
    ENGLISH_ONLY = ("trailer", "official", "teaser", "review", "reaction")

    def score(c):
        t = c["title"].lower()
        s = 0.0
        if any(h in t for h in HINDI):
            s += 10.0
        if strict and not any(h in t for h in HINDI):
            s -= 8.0                      # strongly deprioritise pure-English uploads
        if any(k in t for k in ENGLISH_ONLY):
            s -= 3.0
        s += min(4.0, (c["views"] ** 0.28) / 12)
        if 300 <= c["duration"] <= 2400:
            s += 1.5
        return s

    cands.sort(key=lambda c: -score(c))
    return cands


def find_source(topic, mode="rank", prefer_dur=(120, 1800), log_fn=log):
    """Search several queries and return the best download candidate."""
    seen = set()
    cands = []
    for q in guess_queries(topic, mode):
        log_fn(f"  search: {q}")
        try:
            for c in search(q, n=6, short=False, min_dur=prefer_dur[0],
                            max_dur=prefer_dur[1]):
                if c["id"] in seen:
                    continue
                seen.add(c["id"])
                cands.append(c)
        except Exception as e:
            log_fn(f"  (search failed: {e})")
    if not cands:
        return None
    # score: views get you the reliable payoff moments, duration sanity
    def score(c):
        v = c["views"] ** 0.35
        ideal = 400
        d = 1.0 / (1 + abs(c["duration"] - ideal) / 900)
        return v * d
    cands.sort(key=lambda c: -score(c))
    return cands
