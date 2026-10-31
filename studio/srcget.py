#!/usr/bin/env python3
"""srcget — tested clip sources se seedha download.

Har subcommand ek aisa source hai jo 2026-10-24 ko sandbox se VERIFY hua
(actual file download hua, sirf 200 nahi).

    python3 srcget.py tiktok https://www.tiktok.com/@espn/video/7488031370086780190
    python3 srcget.py pexels 5039768
    python3 srcget.py coverr "skateboard fall" 4
    python3 srcget.py mixkit fail 3
    python3 srcget.py imgur funny 3
    python3 srcget.py wiki "crash test" 3
    python3 srcget.py peertube "bicycle crash" 2
    python3 srcget.py ia "fail compilation" 2
    python3 srcget.py nbc https://www.today.com/video/...
    python3 srcget.py vimeo 76979871

Sab kuch ~/dl/src/<source>/ me girta hai, aur ek line per file print hoti hai:
    OK  <path>  <w>x<h>  <seconds>
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request

DEST = os.path.expanduser("~/dl/src")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
IMGUR_ID = "546c25a59c58ad7"          # public web client-id, gallery read


def get(url, timeout=40, headers=None, data=None):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h, data=data)
    return urllib.request.urlopen(req, timeout=timeout).read()


def save(name, data, sub):
    d = os.path.join(DEST, sub)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(data)
    return p


def probe(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                              "-show_entries", "stream=width,height",
                              "-show_entries", "format=duration",
                              "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.split()
        wh = out[0] if out else "?"
        dur = out[-1] if len(out) > 1 else "?"
        return wh.replace(",", "x"), f"{float(dur):.2f}s"
    except Exception:
        return "?", "?"


def report(path):
    if os.path.exists(path) and os.path.getsize(path) > 100_000:
        wh, dur = probe(path)
        print(f"OK  {path}  {wh}  {dur}")
        return True
    print(f"--  {path}  (failed/too small)")
    return False


# ---------------------------------------------------------------- tiktok
def tiktok(arg):
    """Web player ka 1080p, binA download-watermark."""
    m = re.search(r"/video/(\d{15,21})", arg) or re.search(r"(\d{15,21})", arg)
    handle = None
    mh = re.search(r"@([\w.\-]+)/video/", arg)
    if mh:
        handle = mh.group(1)
    if not m:
        return print("bad tiktok url/id")
    vid = m.group(1)
    if not handle:
        try:
            o = json.loads(get(f"https://www.tiktok.com/oembed?url=https://www.tiktok.com/@x/video/{vid}"))
            handle = re.search(r"@([\w.\-]+)", o.get("author_url", "")).group(1)
        except Exception:
            return print("handle not found — poora URL do")
    html = get(f"https://www.tiktok.com/@{handle}/video/{vid}").decode("utf-8", "ignore")
    mm = re.search(r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.S)
    if not mm:
        return print("page data nahi mila")
    it = json.loads(mm.group(1))["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
    gears = [g for g in (it["video"].get("bitrateInfo") or []) if g.get("PlayAddr")]
    best = max(gears, key=lambda g: (g["PlayAddr"]["Height"], g["Bitrate"]))
    for u in best["PlayAddr"]["UrlList"]:
        try:
            data = get(u, 120)
        except Exception:
            continue
        report(save(f"tt_{vid}.mp4", data, "tiktok"))
        return
    print("-- download fail")


# ---------------------------------------------------------------- pexels
def pexels(vid, name=None):
    """pexels.com/download/video/<id>/ 302 -> videos.pexels.com (4K/1080p)."""
    vid = re.search(r"(\d{5,10})", str(vid)).group(1)
    try:
        html = None
        req = urllib.request.Request(f"https://www.pexels.com/download/video/{vid}/",
                                     headers={"User-Agent": UA})
        # follow manually so we can see the CDN target
        import http.client
        url = f"https://www.pexels.com/download/video/{vid}/"
        for _ in range(4):
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                       timeout=60)
            url = r.geturl()
            if "videos.pexels.com" in url:
                data = r.read()
                report(save(name or f"px_{vid}.mp4", data, "pexels"))
                return
        print("-- redirect chain samajh nahi aaya")
    except Exception as e:
        print("--", e)


# ---------------------------------------------------------------- coverr
def coverr(query, n=3):
    """coverr.co/api/videos?query=... -> base_filename -> cdn 1080p."""
    d = json.loads(get("https://coverr.co/api/videos?page_size=%d&query=%s"
                       % (int(n), urllib.parse.quote(query))))
    for h in d.get("hits", [])[: int(n)]:
        bf = h.get("base_filename")
        if not bf:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", (h.get("title") or bf).lower()).strip("-")[:50]
        ok = False
        for res in ("1080p", "720p"):
            try:
                data = get(f"https://cdn.coverr.co/videos/{bf}/{res}.mp4", 120)
            except Exception:
                continue
            if report(save(f"cv_{slug}_{res}.mp4", data, "coverr")):
                ok = True
                break
        if not ok:
            print("--", h.get("title"))


# ---------------------------------------------------------------- mixkit
def mixkit(slug, n=3):
    """mixkit.co free pages -> assets.mixkit.co/videos/<id>/<id>-720.mp4"""
    html = get(f"https://mixkit.co/free-stock-video/{slug.strip('/')}/").decode("utf-8", "ignore")
    ids = list(dict.fromkeys(re.findall(r"assets\.mixkit\.co/videos/(\d+)/\1-(?:720|1080)\.mp4", html)))
    for vid in ids[: int(n)]:
        for res in ("1080", "720"):
            try:
                data = get(f"https://assets.mixkit.co/videos/{vid}/{vid}-{res}.mp4", 90)
            except Exception:
                continue
            if report(save(f"mk_{vid}_{res}.mp4", data, "mixkit")):
                break


# ---------------------------------------------------------------- imgur
def imgur(tag, n=3):
    """api.imgur.com gallery/t/<tag> -> i.imgur.com/<id>.mp4"""
    hdr = {"Authorization": f"Client-ID {IMGUR_ID}"}
    d = json.loads(get(f"https://api.imgur.com/3/gallery/t/{tag}/1", headers=hdr))
    items = d.get("data", {}).get("items") or d.get("data") or []
    got = 0
    for it in items:
        for im in (it.get("images") or [it]):
            if got >= int(n):
                return
            u = im.get("mp4")
            if not u:
                continue
            try:
                data = get(u, 90)
            except Exception:
                continue
            if report(save(u.rsplit("/", 1)[-1], data, "imgur")):
                got += 1


# ---------------------------------------------------------------- wikimedia
def wiki(query, n=3):
    """commons API, filetype:video — webm/mp4 direct upload.wikimedia.org se."""
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
         "&generator=search&gsrnamespace=6&gsrlimit=%d&gsrsearch=%s"
         "&prop=imageinfo&iiprop=url|size|mime" % (int(n), urllib.parse.quote(f"filetype:video {query}")))
    d = json.loads(get(u))
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        url = ii.get("url")
        if not url:
            continue
        try:
            data = get(url, 180)
        except Exception:
            continue
        report(save(re.sub(r"[^A-Za-z0-9._-]", "_", p["title"].replace("File:", "")), data, "wiki"))


# ---------------------------------------------------------------- peertube
def peertube(query, n=2, instance="framatube.org"):
    """Public PeerTube instance: search -> /api/v1/videos/<uuid> -> files[].fileUrl"""
    d = json.loads(get(f"https://{instance}/api/v1/search/videos?count={int(n)}&search="
                       + urllib.parse.quote(query)))
    for v in d.get("data", [])[: int(n)]:
        det = json.loads(get(f"https://{instance}/api/v1/videos/{v['uuid']}"))
        def _res(f):
            r = f.get("resolution")
            return r.get("id", 0) if isinstance(r, dict) else (r or 0)
        files = sorted(det.get("files", []), key=_res, reverse=True)
        if not files:
            continue
        f = files[0]
        try:
            data = get(f["fileUrl"], 300)
        except Exception:
            continue
        report(save(f"pt_{v['uuid'][:8]}_{_res(f)}.mp4", data, "peertube"))


# ---------------------------------------------------------------- archive.org
def ia(query, n=2):
    """archive.org advancedsearch -> metadata -> direct mp4/webm."""
    q = urllib.parse.quote(f'title:({query}) AND mediatype:movies')
    d = json.loads(get("https://archive.org/advancedsearch.php?q=" + q +
                       "&fl[]=identifier&fl[]=title&rows=%d&sort[]=downloads+desc&output=json" % int(n)))
    for doc in d["response"]["docs"][: int(n)]:
        ident = doc["identifier"]
        meta = json.loads(get(f"https://archive.org/metadata/{ident}"))
        for f in meta.get("files", []):
            sz = int(f.get("size") or 0)
            if f["name"].lower().endswith((".mp4", ".webm")) and 1_000_000 < sz < 400_000_000:
                try:
                    data = get(f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}", 300)
                except Exception:
                    continue
                report(save(re.sub(r"[^A-Za-z0-9._-]", "_", f["name"]), data, "archive"))
                break


# ---------------------------------------------------------------- nbc / news
def nbc(url):
    """NBC / Today pages ke andar direct mp4 (1080p) hota hai."""
    try:
        html = get(url).decode("utf-8", "ignore")
    except Exception:
        html = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                              capture_output=True, text=True).stdout
    urls = list(dict.fromkeys(re.findall(r"https://[^\"'\\ ]{20,200}\.mp4", html)))
    urls = [u for u in urls if "akamaized" in u or "nbcuni" in u]
    if not urls:
        return print("-- page me mp4 nahi mila")
    data = None
    for u in urls[:6]:                       # purane video URLs 404 dete hain
        try:
            data = get(u, 180)
            break
        except Exception:
            continue
    if not data:
        return print("-- saare mp4 URLs fail (expired)")
    report(save("news_" + re.sub(r"\W", "", url.rsplit("-", 1)[-1])[:24] + ".mp4", data, "news"))


# ---------------------------------------------------------------- vimeo
def vimeo(vid):
    """player.vimeo.com/video/<id>/config -> progressive | hls/dash (DRM ho to fail)."""
    cfg = json.loads(get(f"https://player.vimeo.com/video/{vid}/config"))
    files = cfg.get("request", {}).get("files", {})
    prog = files.get("progressive") or []
    if prog:
        url = max(prog, key=lambda x: x.get("height", 0))["url"]
        report(save(f"vimeo_{vid}.mp4", get(url, 200), "vimeo"))
        return
    hls = files.get("hls") or {}
    cdns = hls.get("cdns") or {}
    if cdns:
        url = cdns[hls.get("default_cdn", next(iter(cdns)))]["url"]
        d = os.path.join(DEST, "vimeo")
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, f"vimeo_{vid}.mp4")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-user_agent", UA, "-i", url, "-c", "copy", out],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return report(out)
        return print("-- HLS fail (DRM?):", r.stderr.strip()[:120])
    print("-- koi playable stream nahi")


CMDS = {"tiktok": tiktok, "pexels": pexels, "coverr": coverr, "mixkit": mixkit,
        "imgur": imgur, "wiki": wiki, "peertube": peertube, "ia": ia,
        "nbc": nbc, "vimeo": vimeo}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(1)
    CMDS[sys.argv[1]](*sys.argv[2:])
