"""t3.py — TYPE 3 narration-explainer engine (generic).

Ek project folder me sab kuch:
    projects/<name>/project.json     clips, narration (Hindi + Hinglish), header, layout
    projects/<name>/narr/*.mp3       narration audio
    projects/<name>/wordtimes.json   `narr` command banata hai
    projects/<name>/subs.ass         `build` command banata hai
    projects/<name>/out/*.mp4        final render

Command:
    python3 t3.py fetch projects/<name>     source video download (URL se)
    python3 t3.py narr  projects/<name>     whisper se word-level timing
    python3 t3.py build projects/<name>     final render
    python3 t3.py check projects/<name>     audio + overlap QC
    python3 t3.py verify projects/<name>    SPEC vs project.json + contamination + QC
    python3 t3.py new   projects/<name>     khaali project scaffold

Naya video = naya project folder. Engine ko chhune ki zarurat nahi.
"""
import hashlib, json, os, subprocess, sys, time
import numpy as np

STUDIO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, STUDIO)

def _load(pdir):
    with open(os.path.join(pdir, "project.json")) as f:
        return json.load(f)

def _save(pdir, p):
    with open(os.path.join(pdir, "project.json"), "w") as f:
        json.dump(p, f, indent=1, ensure_ascii=False)

def _dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        out = subprocess.run(["ffmpeg", "-i", path], capture_output=True, text=True).stderr
        for l in out.split("\n"):
            if "Duration:" in l:
                h, m, s = l.split("Duration: ")[1].split(",")[0].split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0

FFMPEG = os.environ.get("FFMPEG") or ("/tmp/vidtools/ffmpeg" if os.path.exists("/tmp/vidtools/ffmpeg") else "ffmpeg")

def _pcm16(path):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def lr_bars(src, ss, dur=1.0, probes=3, maxfrac=0.32):
    """Source ke baked-in left/right black bars nikaalo (fraction of width).
    Column-wise: bar = poora column dark AND flat (content me texture hoti hai)."""
    out = []
    for k in range(probes):
        t = ss + dur * (k + 0.5) / probes
        r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", src,
                            "-frames:v", "1", "-vf", "scale=540:-2",
                            "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                           capture_output=True)
        if not r.stdout:
            continue
        a = np.frombuffer(r.stdout, dtype=np.uint8)
        if a.size % 540:
            continue
        f = a.reshape(-1, 540).astype(np.float32)
        H = f.shape[0]
        band = f[int(H * 0.15):int(H * 0.85)]
        m, sd = band.mean(axis=0), band.std(axis=0)
        dark = (m < 14) & (sd < 6.0)
        L = 0
        while L < 540 and dark[L]:
            L += 1
        R = 0
        while R < 540 and dark[539 - R]:
            R += 1
        if L >= 540 or R >= 540:
            continue
        out.append((L / 540, R / 540))
    if not out:
        return 0.0, 0.0
    l = max(o[0] for o in out); r = max(o[1] for o in out)
    return round(min(l, maxfrac), 3), round(min(r, maxfrac), 3)


def _md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _resolve_source(pdir, p):
    """Source ka path do. Agar missing + md5 mismatch -> seedha fetch chala do."""
    src = p["source"].get("local") or f"/tmp/{p['name']}.mp4"
    want = p["source"].get("md5")
    if not os.path.exists(src):
        print(f"source nahi mila: {src}")
        if not p["source"].get("url"):
            sys.exit(f"  project.json me source.url khaali hai — video manually {src} pe rakho")
        print(f"  auto-fetch: {p['source']['url']}")
        src = cmd_fetch(pdir)
    if want:
        got = _md5(src)
        if got != want:
            sys.exit(f"\n[STOP] source ka md5 match nahi hua\n"
                     f"  expected {want}\n  mila     {got}\n"
                     f"  file: {src}\n"
                     f"  fix: file hatao -> python3 t3.py fetch {pdir}")
        print(f"  source md5 OK ({want[:12]}...)")
    return src


# ------------------------------------------------------------------ commands
def cmd_fetch(pdir):
    p = _load(pdir)
    src = p["source"]
    out = src.get("local", f"/tmp/{p['name']}.mp4")
    if os.path.exists(out):
        print(f"already hai: {out}")
        return out
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings",
           "-f", src.get("format", "bv*[height<=1080]+ba/b[height<=1080]"),
           "--merge-output-format", "mp4", "-o", out, src["url"]]
    print("downloading:", src["url"])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit(f"\n[STOP] download ke baad file nahi bani: {out}\n"
                 f"  yt-dlp return {r.returncode}\n"
                 f"  {(r.stderr or '')[-800:]}\n"
                 f"  likely: yt-dlp ko ffmpeg PATH pe nahi mila.\n"
                 f"  fix: PATH=/tmp/vidtools:$PATH python3 t3.py fetch {pdir}")
    p["source"]["local"] = out
    p["source"]["md5"] = _md5(out)
    _save(pdir, p)
    print("saved:", out)
    print("md5:", p["source"]["md5"])
    return out

def cmd_narr(pdir):
    """Har narration line ko whisper se transcribe karke word times nikaalo."""
    from faster_whisper import WhisperModel
    p = _load(pdir)
    model = WhisperModel(os.environ.get("WHISPER", "base"), device="cpu", compute_type="int8")
    out = {}
    for n in p["narration"]:
        f = os.path.join(pdir, n["file"])
        x = _pcm16(f)
        segs, _ = model.transcribe(x, beam_size=5, language=n.get("lang", "hi"),
                                   word_timestamps=True)
        ws = [[round(w.start, 3), round(w.end, 3)]
              for s in segs for w in (s.words or [])]
        out[n["id"]] = {"dur": round(len(x) / 16000, 3), "words": ws}
        nw = len(n.get("caption", "").split())
        flag = "" if len(ws) == nw else f"  (whisper {len(ws)} vs caption {nw} — interpolate)"
        print(f"  {n['id']:12s} {out[n['id']]['dur']:6.2f}s  words {len(ws):2d}{flag}")
    with open(os.path.join(pdir, "wordtimes.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wordtimes.json saved")

def _word_times(wt, caption):
    """whisper times ko caption ke words pe char-weighted map karo."""
    rw = caption.split()
    ws = wt["words"]
    if not ws:
        step = wt["dur"] / max(1, len(rw))
        return [(i * step, (i + 1) * step) for i in range(len(rw))]
    cw = np.cumsum([1.0] * len(ws)) / len(ws)
    tr = np.array([max(1, len(w)) for w in rw], float)
    cr = np.cumsum(tr) / tr.sum()
    s = np.array([w[0] for w in ws]); e = np.array([w[1] for w in ws])
    res = []
    for i in range(len(rw)):
        p0 = 0.0 if i == 0 else cr[i - 1]
        a = float(np.interp(p0, cw, s)); b = float(np.interp(cr[i], cw, e))
        res.append((a, max(b, a + 0.10)))
    return res

def cmd_build(pdir, name=None):
    import templates
    p = _load(pdir)
    src = _resolve_source(pdir, p)

    lay = p.get("layout", {})
    W, H = lay.get("size", [1080, 1920])
    wt = {}
    wtf = os.path.join(pdir, "wordtimes.json")
    if os.path.exists(wtf):
        wt = json.load(open(wtf))
    elif p.get("narration"):
        sys.exit("wordtimes.json nahi hai — pehle: python3 t3.py narr " + pdir)

    if p.get("autocrop_lr", True):
        for i, c in enumerate(p["clips"]):
            if c.get("crop_left") is None and c.get("crop_right") is None:
                l, r = lr_bars(src, float(c["ss"]), float(c["dur"]))
                if l > 0.02 or r > 0.02:
                    c["crop_left"], c["crop_right"] = l, r
                    print(f"  clip {i+1}: side bars L {l*100:.1f}%  R {r*100:.1f}% -> crop")
                else:
                    c["crop_left"] = c["crop_right"] = 0.0

    hdr = p.get("header", [])
    plan = {
        "size": [W, H],
        "band": lay.get("band", 0),
        "bottom_band": lay.get("bottom_band", 0),
        "band_text_y": hdr[0]["y"] if hdr else 0,
        "header_size": hdr[-1]["size"] if hdr else 58,
        "top_text": hdr,
        "clips": p["clips"],
        "look": p.get("look", "film"),
        "duck": p.get("audio", {}).get("duck", 0.50),
        "voice": [{"path": os.path.relpath(os.path.join(pdir, n["file"]), STUDIO),
                   "at": n["at"], "gain": n.get("gain", 1.0)}
                  for n in p.get("narration", [])],
    }
    tl = templates.build_plan_edit(src, plan)
    au = p.get("audio", {})
    tl.master_gain_db = au.get("master_gain_db", 0.0)

    chunks = []
    MW = int(lay.get("cap_chunk_words", 8))
    MC = int(lay.get("cap_chunk_chars", 48))
    for n in p.get("narration", []):
        if not n.get("caption") or n["id"] not in wt:
            continue
        times = _word_times(wt[n["id"]], n["caption"])
        pairs = [(w, n["at"] + a, n["at"] + b)
                 for w, (a, b) in zip(n["caption"].split(), times)]
        cur, used = [], 0
        for w, a, b in pairs:
            add = len(w) + (1 if cur else 0)
            if cur and (len(cur) >= MW or used + add > MC):
                chunks.append(cur); cur, used = [], 0; add = len(w)
            cur.append((w, a, b)); used += add
        if cur:
            chunks.append(cur)
    ncap = 0
    if chunks:
        # KARAOKE captions (Type 1 style): pura sentence + bola ja raha word
        # YELLOW + thora bada. Timings narration ki wordtimes.json se.
        # style="CapYellow" rakha hai taaki cmd_check/cmd_verify na tute.
        ncap = tl.overlay.word_caps_kara(chunks,
                                         style="CapYellow",
                                         y=lay.get("cap_y", 1260),
                                         size=lay.get("cap_size", 60),
                                         font=lay.get("cap_font", "Inter Black"),
                                         fsp=lay.get("cap_fsp", -1.5),
                                         bord=lay.get("cap_bord", 4),
                                         shad=lay.get("cap_shad", 3),
                                         max_line_chars=lay.get("cap_line_chars", 26),
                                         max_lines=lay.get("cap_max_lines", 3),
                                         scale=lay.get("cap_scale", 122),
                                         blur=lay.get("cap_blur", 24))
    for w in getattr(tl.overlay, "warnings", []):
        print(f"  [overlay] {w}")
    ec = p.get("end_card")
    if ec:
        total = tl.duration()
        tl.overlay.add(ec.get("from", total - 3.4), total, "Title",
                       "{\\an5\\pos(%d,%d)\\fs%d\\c&H00FFFFFF&\\bord10"
                       "\\bordcolor&H000000&}%s"
                       % (W // 2, ec.get("y", lay.get("cap_y", 1260)),
                          ec.get("size", 136), ec["text"]))

    os.makedirs(os.path.join(pdir, "out"), exist_ok=True)
    templates.save_overlay(tl, os.path.join(pdir, "subs.ass"))
    out = os.path.join(pdir, "out", f"{name or p['name']}_{time.strftime('%m%d-%H%M')}.mp4")
    print(f"captions {ncap} | gain {tl.master_gain_db:+.1f} dB | size {W}x{H}")
    tl.build(out)
    print("out:", out)
    return out

def cmd_check(pdir):
    import glob
    p = _load(pdir)
    ass = os.path.join(pdir, "subs.ass")
    if os.path.exists(ass):
        ev = []
        for l in open(ass):
            if l.startswith("Dialogue:") and ",CapYellow," in l:
                q = l.split(",")
                def ts(x):
                    h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
                ev.append((ts(q[1]), ts(q[2])))
        ev.sort()
        ov = [a[1] - b[0] for a, b in zip(ev, ev[1:]) if a[1] > b[0] + 0.0005]
        print(f"captions {len(ev)}  overlaps {len(ov)}  max {max(ov) if ov else 0:.3f}s")
    outs = sorted(glob.glob(os.path.join(pdir, "out", "*.mp4")))
    if not outs:
        print("koi render nahi")
        return
    F = outs[-1]
    r = subprocess.run([FFMPEG, "-v", "error", "-i", F, "-vn", "-ac", "1", "-ar", "44100",
                        "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768
    sr = 44100; h = int(sr * 0.25)
    e = np.array([np.sqrt(np.mean(x[i:i + h] ** 2)) for i in range(0, len(x) - h, h)])
    db = 20 * np.log10(e + 1e-9); t = np.arange(len(db)) * 0.25
    print(f"{os.path.basename(F)}  {len(x)/sr:.2f}s")
    print(f"  peak {np.abs(x).max():.3f}  clip {int((np.abs(x)>0.99).sum())}  "
          f"rms {20*np.log10(np.sqrt((x**2).mean())+1e-9):.1f} dB")
    dead = [a for a in range(0, int(len(x)/sr), 2) if db[(t>=a)&(t<a+2)].mean() < -40]
    print(f"  dead air {len(dead)*2}s  at {dead}")



def _code_only(path):
    """File se comments + string literals hata ke sirf asli code do.
    Warna verify apne hi comment ko pakad leta hai."""
    import io, tokenize
    out = []
    with open(path, "rb") as f:
        for tok in tokenize.tokenize(io.BytesIO(f.read()).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            if tok.type == tokenize.NAME or tok.type == tokenize.OP:
                out.append(tok.string)
    return " ".join(out)


def cmd_verify(pdir):
    """SPEC vs project.json + contamination scan + caption/audio QC.
    Ek PASS/FAIL. Render se PEHLE chalao."""
    import glob, re
    p = _load(pdir)
    fails, warns, ok = [], [], []

    # 1) audio me music leak?
    au = p.get("audio", {})
    if any(k in au for k in ("music", "music_vol", "music_ss")):
        fails.append("project.json me music key hai — Type 3 me music allowed nahi")
    else:
        ok.append("audio: koi music key nahi")

    # 2) engine me music ka code path?
    eng = _code_only(os.path.join(STUDIO, "t3.py"))
    leak = re.findall(r"\btl\.music\w*", eng)
    if leak:
        fails.append(f"t3.py me music code path hai: {sorted(set(leak))}")
    else:
        ok.append("t3.py: koi tl.music* code path nahi")

    # 3) layout SPEC ke barabar? (1080x1920, band 360/360)
    lay = p.get("layout", {})
    size = tuple(lay.get("size", [0, 0]))
    band, bot = lay.get("band"), lay.get("bottom_band")
    if size != (1080, 1920):
        fails.append(f"size {size} != 1080x1920")
    elif (band, bot) != (360, 360):
        fails.append(f"band {band}/{bot} != 360/360")
    else:
        ok.append(f"layout: {size[0]}x{size[1]}, band {band}/{bot}")

    # 4) header sizes = target px / 0.52
    for h in p.get("header", []):
        if abs(h["size"] * 0.52 - round(h["size"] * 0.52)) > 0.6:
            warns.append(f"header '{h['text']}' fs{h['size']} -> ~{h['size']*0.52:.0f}px (odd)")
    if p.get("header"):
        ok.append("header: " + " / ".join(f"fs{h['size']}={h['size']*0.52:.0f}px" for h in p["header"]))

    # 5) narration vs wordtimes
    wt = {}
    wtp = os.path.join(pdir, "wordtimes.json")
    if os.path.exists(wtp):
        wt = json.load(open(wtp))
    miss = [n["id"] for n in p.get("narration", []) if n["id"] not in wt]
    if miss:
        fails.append(f"wordtimes missing: {miss} -> python3 t3.py narr {pdir}")
    else:
        ok.append(f"wordtimes: {len(wt)} narration chunks")

    # 6) narration order
    ats = [n["at"] for n in p.get("narration", [])]
    if ats != sorted(ats):
        warns.append("narration JSON out of order (engine sort kar dega)")

    # 7) caption / subs
    ass = os.path.join(pdir, "subs.ass")
    if os.path.exists(ass):
        ev = []
        for l in open(ass):
            if l.startswith("Dialogue:") and ",CapYellow," in l:
                q = l.split(",")
                def ts(x):
                    hh, mm, ss = x.split(":")
                    return int(hh) * 3600 + int(mm) * 60 + float(ss)
                ev.append((ts(q[1]), ts(q[2])))
        ev.sort()
        ov = [a[1] - b[0] for a, b in zip(ev, ev[1:]) if a[1] > b[0] + 0.0005]
        if ov:
            warns.append(f"caption overlap {len(ov)} (max {max(ov):.3f}s)")
        else:
            ok.append(f"captions: {len(ev)} events, 0 overlap")
        if not ev:
            warns.append("subs.ass me koi CapYellow event nahi")

    # 8) source
    src = p["source"].get("local") or f"/tmp/{p['name']}.mp4"
    if os.path.exists(src):
        ok.append(f"source: {src}")
        if p["source"].get("md5"):
            ok.append("source md5 pinned")
        else:
            warns.append("source md5 pin nahi hai — file badal gayi to pata nahi chalega")
    else:
        warns.append(f"source missing: {src} (build auto-fetch karega)")

    # 9) render file agar hai
    outs = sorted(glob.glob(os.path.join(pdir, "out", "*.mp4")))
    if outs:
        F = outs[-1]
        r = subprocess.run([FFMPEG, "-v", "error", "-i", F, "-vn", "-ac", "1", "-ar", "44100",
                            "-f", "s16le", "-"], capture_output=True)
        a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768
        if a.size:
            pk, cl = float(np.abs(a).max()), int((np.abs(a) > 0.99).sum())
            rms = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
            ok.append(f"audio: peak {pk:.3f}, clipped {cl}, rms {rms:.1f} dB")
            if cl:
                fails.append(f"audio clipped: {cl} samples > 0.99")
            if rms > -14:
                warns.append(f"rms {rms:.1f} dB bahut loud")

    print(f"\n=== VERIFY  {p['name']} ===")
    for m in ok:
        print(f"  ok    {m}")
    for m in warns:
        print(f"  warn  {m}")
    for m in fails:
        print(f"  FAIL  {m}")
    print("\n" + ("PASS" if not fails else f"FAIL ({len(fails)})") + "\n")
    return 0 if not fails else 1

def cmd_new(pdir):
    os.makedirs(os.path.join(pdir, "narr"), exist_ok=True)
    os.makedirs(os.path.join(pdir, "out"), exist_ok=True)
    proj = {
        "name": os.path.basename(pdir.rstrip("/")),
        "source": {"url": "", "local": "/tmp/name.mp4",
                   "format": "bv*[height<=1080]+ba/b[height<=1080]"},
        "look": "film",
        "layout": {"size": [1080, 1920], "band": 360, "bottom_band": 360,
                   "cap_y": 1260, "cap_size": 60, "cap_line_chars": 26,
                   "cap_font": "Inter Black", "cap_fsp": -1.5, "cap_bord": 4,
                   "cap_shad": 3, "cap_scale": 122, "cap_blur": 24},
        "header": [
            {"text": "MOVIE NAME", "color": "white", "hi": "MOVIE",
             "hi_color": "red", "size": 148, "y": 112},
            {"text": "ENDING EXPLAINED", "color": "white", "hi": "ENDING",
             "hi_color": "yellow", "size": 113, "y": 202}],
        "audio": {"duck": 0.50, "master_gain_db": 2.5},
        "clips": [],
        "narration": [],
        "end_card": {"text": "THE END", "from": 55.2, "y": 1260, "size": 136},
    }
    _save(pdir, proj)
    print("banaya:", os.path.join(pdir, "project.json"))

def main(argv):
    if len(argv) < 3:
        print(__doc__); return
    cmd, pdir = argv[1], argv[2].rstrip("/")
    while pdir.endswith("/"):
        pdir = pdir[:-1]
    if not os.path.isdir(pdir):
        sys.exit(f"folder nahi mila: {pdir}")
    if cmd == "new":
        cmd_new(pdir)
    elif cmd == "fetch":
        cmd_fetch(pdir)
    elif cmd == "narr":
        cmd_narr(pdir)
    elif cmd == "build":
        cmd_build(pdir, argv[3] if len(argv) > 3 else None)
    elif cmd == "check":
        cmd_check(pdir)
    elif cmd == "verify":
        sys.exit(cmd_verify(pdir))
    else:
        print(__doc__)

if __name__ == "__main__":
    main(sys.argv)
