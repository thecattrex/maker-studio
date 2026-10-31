#!/usr/bin/env python3
"""studio — no-UI shorts factory.

  python3 run.py search "parkour fails"
  python3 run.py rank  --source <url|file> --count 5 --title "Ranking the Best" --line2 "Parkour Saves" --music synth:hype
  python3 run.py cine  --source <url|file> --title "THE LAST FIGHT" --music synth:phonk
  python3 run.py auto  --topic "parkour saves" --count 5
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

import templates
from analyze import analyze, shots as make_shots, moments as make_moments
from music import detect_beats, make_track
from render import Timeline
from util import (CACHE, FFMPEG, STUDIO, ensure_dirs, ensure_ffmpeg, ffmpeg_cmd,
                  log, probe, run, slug)

OUT = os.path.join(STUDIO, "out")
WORK = os.path.join(STUDIO, "work")


# --------------------------------------------------------------------- music
def prep_music(spec, mood="hype", seconds=30.0):
    if not spec:
        return None, None          # silence by default: keep the clip's real audio
    os.makedirs(WORK, exist_ok=True)
    if spec.startswith("synth:"):
        kind = spec.split(":", 1)[1] or mood
        path = os.path.join(WORK, f"music_{kind}.wav")
        info = make_track(kind, filename=path, min_seconds=max(16.0, seconds + 3))
    else:
        path = spec
        if spec.startswith("http"):
            import discover
            d = discover.download(spec, outdir=os.path.join(WORK, "music"))
            path = d["path"]
        wav = os.path.join(WORK, "music_in.wav")
        run(ffmpeg_cmd(["-i", path, "-vn", "-ac", "2", "-ar", "44100", wav]), check=True)
        path = wav
    beats = detect_beats(path)
    log(f"  music: {os.path.basename(path)}  {beats['bpm']} bpm  {beats['duration']}s")
    return path, beats


# --------------------------------------------------------------------- helpers
def _stage(mode, path, out, model="small", lang=None, max_asr=480.0):
    cmd = [sys.executable, os.path.join(STUDIO, "analyze.py"), mode, path,
           "--out", out, "--model", model, "--max-asr", str(max_asr)]
    if lang:
        cmd += ["--lang", lang]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5400)
    if r.returncode != 0:
        raise RuntimeError(f"{mode} stage failed:\n{(r.stderr or '')[-1500:]}")
    return json.load(open(out)) if os.path.exists(out) else {}


def detect_language(path, seconds=40):
    """Quick language check on the first N seconds of audio."""
    from util import probe as _probe
    if not _probe(path).get("has_audio"):
        return "no_audio"
    try:
        import subprocess
        wav = os.path.join(WORK, "_lang.wav")
        os.makedirs(WORK, exist_ok=True)
        subprocess.run([FFMPEG, "-v", "error", "-t", str(seconds), "-i", path,
                        "-vn", "-ac", "1", "-ar", "16000", wav, "-y"], timeout=180)
        from faster_whisper import WhisperModel
        m = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2)
        segs, info = m.transcribe(wav, vad_filter=True, beam_size=1)
        list(segs)
        return info.language
    except Exception as e:
        log("  language check failed:", str(e)[:120])
        return None


def load_source(src, model="small", lang=None):
    """Download if needed, then analyze in isolated stages (low RAM)."""
    if os.path.exists(src):
        path = src
    else:
        import discover
        log(f"  downloading {src}")
        path = discover.download(src)["path"]
    log(f"  analyzing {os.path.basename(path)} ...")
    t0 = time.time()
    os.makedirs(WORK, exist_ok=True)
    tag = slug(os.path.basename(path))
    vjson = os.path.join(WORK, f"an_{tag}.json")
    ajson = os.path.join(WORK, f"asr_{tag}.json")
    if not os.path.exists(vjson):
        _stage("video", path, vjson)
    vid = json.load(open(vjson))
    sp = None
    if not os.path.exists(ajson):
        try:
            _stage("asr", path, ajson, model=model, lang=lang)
        except Exception as e:
            log("  speech stage failed:", str(e)[:200])
    if os.path.exists(ajson):
        sp = json.load(open(ajson)).get("speech")
    a = {"timeline": vid["timeline"], "shots": vid["shots"],
         "moments": vid["moments"], "speech": sp,
         "energy": vid.get("energy"), "zones": vid.get("zones") or {}}
    try:
        from analyze import detect_bars
        a["bars"] = detect_bars(path)
    except Exception:
        a["bars"] = (0.0, 0.0)
    a["timeline"]["path"] = path
    log(f"  done in {time.time() - t0:.1f}s | {len(a['shots'])} shots | "
        f"{len(a['moments'])} moments | speech={'yes' if sp else 'no'}")
    return a


def contact_sheet(video, out_png=None, n=9):
    """QC sheet for a finished render."""
    ensure_ffmpeg()
    from util import probe as pr
    d = pr(video)["duration"]
    tmp = os.path.join(WORK, "qc")
    os.makedirs(tmp, exist_ok=True)
    files = []
    for i in range(n):
        t = d * (i + 0.5) / n
        f = os.path.join(tmp, f"q{i:02d}.jpg")
        run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
             "-vf", "scale=360:-2", "-q:v", "3", f, "-y"])
        if os.path.exists(f):
            files.append(f)
    if not files:
        return None
    inputs, chains, labels = [], [], []
    for i, f in enumerate(files):
        inputs += ["-i", f]
        chains.append(f"[{i}:v]scale=360:640:force_original_aspect_ratio=decrease,"
                      f"pad=360:640:(ow-iw)/2:(oh-ih)/2:color=black[v{i}]")
        labels.append(f"[v{i}]")
    cols, rows = 3, 3
    layout = "|".join(f"{(i % cols) * 360}_{(i // cols) * 640}" for i in range(len(files)))
    fc = ";".join(chains) + f";{''.join(labels)}xstack=inputs={len(files)}:layout={layout}:fill=black"
    out_png = out_png or video.replace(".mp4", "_sheet.jpg")
    run([FFMPEG, "-v", "error", *inputs, "-filter_complex", fc, "-frames:v", "1",
         "-q:v", "3", out_png, "-y"])
    return out_png


def finish(tl, name, qc=True):
    os.makedirs(OUT, exist_ok=True)
    ass = os.path.join(WORK, f"{slug(name)}.ass")
    templates.save_overlay(tl, ass)
    out = os.path.join(OUT, f"{slug(name)}_{time.strftime('%m%d-%H%M')}.mp4")
    tl.build(out)
    msgs = [f"out: {out}"]
    if qc:
        sh = contact_sheet(out)
        msgs.append(f"qc: {sh}")
    return out, msgs


# --------------------------------------------------------------------- modes
def cmd_search(a):
    import discover
    for mode in ("rank",) if not a.mode else (a.mode,):
        for q in discover.guess_queries(a.query, mode):
            log(f"\n[{q}]")
            try:
                for c in discover.search(q, n=a.n, short=not a.long):
                    log(f"  {c['duration']:6.0f}s  {c['views']:>12,}  {c['title'][:60]}")
                    print(c["url"])
            except Exception as e:
                log("  err:", e)


def cmd_rank(a):
    # Ye PURANA builder hai. Type 2 ka locked audio `ranking` me hai
    # (music 0.67 @10s, clip 0.55, +3.5 dB). Galti se na chale.
    if not getattr(a, "legacy", False):
        sys.exit(
            "\n[STOP] 'rank' purana builder hai — music 36%, clip 100%, "
            "music 0s se.\n"
            "        Type 2 locked audio wala yahi hai:\n"
            "            python3 run.py ranking <plan.json> <source>\n"
            "        Purana jaan-boojh ke chalaana ho to:  --legacy\n")
    ensure_dirs()
    music, beats = prep_music(a.music, "hype",
                              a.count * a.per_item + 4 if a.count else 24)
    srcs = [load_source(s.strip()) for s in a.source.split(",") if s.strip()]
    src = templates.pool_sources(srcs) if len(srcs) > 1 else srcs[0]
    title_lines = [a.title] if a.title else ["RANKING THE BEST"]
    if a.line2:
        title_lines.append(a.line2)
    tl = templates.build_rank(src, music_info=beats, music_path=music,
                              title_lines=title_lines, tagline=a.tagline,
                              labels=a.labels.split(",") if a.labels else None,
                              count=a.count, watermark=a.watermark,
                              per_item=a.per_item, labels_mode=a.labels_mode)
    out, msgs = finish(tl, a.name or f"rank-{a.source[-11:]}")
    for m in msgs:
        log(m)
    print(out)


def cmd_cine(a):
    ensure_dirs()
    music, beats = prep_music(a.music, a.mood, a.length)
    src = load_source(a.source)
    for s in src["shots"]:
        s["src_path"] = src["timeline"]["path"]
    tl = templates.build_cine([src], music_info=beats, music_path=music,
                              title=a.title, subtitle=a.subtitle,
                              target=a.length, watermark=a.watermark,
                              mood=a.mood)
    out, msgs = finish(tl, a.name or f"cine-{a.source[-11:]}")
    for m in msgs:
        log(m)
    print(out)


def cmd_peak(a):
    ensure_dirs()
    srcs = []
    if a.hindi and not os.path.exists(a.source):
        import discover
        log(f"looking for the HINDI version of: {a.movie or a.source}")
        cands = discover.find_hindi_source(a.movie or a.source, a.scene)
        for c in cands[:5]:
            log(f"  {c['duration']:6.0f}s {c['views']:>10,}  {c['title'][:60]}")
        for c in cands[:4]:
            try:
                d = discover.download(c["url"])
            except Exception as e:
                log("  download failed:", str(e)[:120])
                continue
            if d["info"]["duration"] < 45:
                continue
            # verify the AUDIO really is Hindi before using it
            lang = detect_language(d["path"])
            log(f"  candidate: {os.path.basename(d['path'])}  audio={lang}")
            if lang == "no_audio":
                log("    -> file has no audio track, skipping")
                continue
            if a.hindi and lang not in ("hi", "ur", None):
                log("    -> not hindi, skipping")
                continue
            log(f"  using source: {os.path.basename(d['path'])}")
            srcs = [load_source(d["path"])]
            break
        if not srcs:
            log("  no hindi source found - falling back to the given source")
    if not srcs:
        srcs = [load_source(s.strip()) for s in a.source.split(",") if s.strip()]
    src = templates.pool_sources(srcs) if len(srcs) > 1 else srcs[0]

    music, beats = prep_music(a.music, "chill", a.length)
    tl = templates.build_peak(src, title=a.title, subtitle=a.subtitle,
                              hook_dur=a.hook, target=a.length,
                              watermark=a.watermark, hook_text=a.hook_text,
                              music_path=music,
                              music_vol=a.music_vol if music else 0.0)
    out, msgs = finish(tl, a.name or f"peak-{os.path.basename(a.source)[:20]}")
    for m in msgs:
        log(m)
    print(out)


def cmd_scene(a):
    """Continuous scene + hand-written editing (captions from a script file)."""
    ensure_dirs()
    src = load_source(a.source)
    caps, impacts = [], []
    if a.script and os.path.exists(a.script):
        import json as _json
        data = _json.load(open(a.script))
        caps = data.get("captions", [])
        impacts = data.get("impacts", [])
        header = data.get("header")
        emoji = data.get("emoji")
        sub = data.get("sub_text")
    else:
        header = a.header.split("|") if a.header else None
        emoji, sub = a.emoji, a.sub_text
    tl = templates.build_scene_edit(
        src, ss=a.start, dur=a.dur, header=header, emoji=emoji,
        captions=caps, impacts=impacts, watermark=a.watermark,
        rounded=not a.no_rounded, sub_text=sub, layout=a.layout,
        hook_at=a.hook_at, hook_dur=a.hook_dur,
        header_dur=a.header_dur)
    out, msgs = finish(tl, a.name or f"scene-{a.start:.0f}")
    for m in msgs:
        log(m)
    print(out)


def cmd_ranking(a):
    """Ref-A style ranking: top title band + side list + shuffled clips."""
    ensure_dirs()
    cfg = json.load(open(a.plan))
    items = cfg["items"]
    order = cfg.get("order")
    title = cfg["title"]
    tl = templates.build_ranking(a.source, items, title=title,
                                 band=cfg.get("band", 360), bottom=cfg.get("bottom", 132),
                                 gap=cfg.get("gap", 0.25), watermark=a.watermark,
                                 order=order,
                                 ladder=cfg.get("ladder", "play"),
                                 title_size=cfg.get("title_size", 116),
                                 music=cfg.get("music"),
                                 music_vol=cfg.get("music_vol", 0.67),
                                 music_ss=cfg.get("music_ss", 10.0),
                                 clip_vol=cfg.get("clip_vol", 0.55),
                                 sfx_dir=cfg.get("sfx_dir"),
                                 sfx_peak_db=cfg.get("sfx_peak_db", -11.0))
    out, msgs = finish(tl, a.name or "ranking")
    for m in msgs:
        log(m)
    print(out)


def cmd_plan(a):
    """Plan-driven edit: clip list + text layers + word-level dialogue captions."""
    ensure_dirs()
    plan = json.load(open(a.plan))
    # Type 3 ka ekmatra engine `t3.py` hai. Yahan se banane pe caption engine
    # (word_caps), side-bar crop aur music-guard nahi lagte -> galat output.
    if plan.get("voice") or plan.get("narration"):
        raise SystemExit(
            "\n[STOP] Ye plan Type 3 ka hai (narration/voice mila).\n"
            "       run.py plan sirf Type 1/2 ke liye hai.\n"
            "       Type 3 ke liye:  python3 t3.py build projects/<name>\n")
    words = None
    if plan.get("words"):
        words = json.load(open(plan["words"]))
    tl = templates.build_plan_edit(a.source, plan, words=words,
                                   watermark=a.watermark, layout=a.layout)
    out, msgs = finish(tl, a.name or "plan")
    for m in msgs:
        log(m)
    print(out)


def cmd_auto(a):
    ensure_dirs()
    import discover
    log(f"finding: {a.topic}")
    cands = discover.find_source(a.topic, mode="rank")
    if not cands:
        log("nothing found")
        return
    for c in cands[:5]:
        log(f"  cand {c['duration']:5.0f}s {c['views']:>11,}  {c['title'][:52]}")
    sources, used = [], set()
    for c in cands:
        if len(sources) >= max(1, a.sources):
            break
        try:
            d = discover.download(c["url"])
        except Exception as ex:
            log("  download failed:", str(ex)[:160])
            continue
        if d["info"]["duration"] < 40 or d["path"] in used:
            continue
        used.add(d["path"])
        log(f"  source {len(sources) + 1}: {os.path.basename(d['path'])} "
            f"({d['info']['duration']:.0f}s)")
        sources.append(load_source(d["path"]))
    if not sources:
        raise SystemExit("could not download a usable source")

    src = templates.pool_sources(sources) if len(sources) > 1 else sources[0]

    music, beats = prep_music(a.music, "hype", a.count * a.per_item + 4)
    lines = [a.title or "RANKING THE BEST", a.line2 or a.topic.upper()[:22]]
    tl = templates.build_rank(src, music_info=beats, music_path=music,
                              title_lines=lines, tagline=a.tagline,
                              count=a.count, watermark=a.watermark,
                              per_item=a.per_item,
                              labels_mode=a.labels_mode)
    out, msgs = finish(tl, a.name or f"auto-{a.topic}")
    for m in msgs:
        log(m)
    print(out)


# --------------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(prog="studio")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="find source videos")
    s.add_argument("query")
    s.add_argument("-n", type=int, default=6)
    s.add_argument("--mode", choices=["rank", "cine"])
    s.add_argument("--long", action="store_true", help="allow 4-20 min videos")
    s.set_defaults(fn=cmd_search)

    r = sub.add_parser("rank", help="top-N countdown short")
    r.add_argument("--source", required=True,
                   help="url/file, or several separated by commas")
    r.add_argument("--count", type=int, default=5)
    r.add_argument("--title", default="RANKING THE BEST")
    r.add_argument("--line2", default=None)
    r.add_argument("--tagline", default="(Last one is crazy \U0001F631)")
    r.add_argument("--labels", default=None, help="comma separated")
    r.add_argument("--music", default=None,
                   help="apna music file/URL (default: no music)")
    r.add_argument("--per-item", type=float, default=6.5)
    r.add_argument("--watermark", default="@studio")
    r.add_argument("--labels-mode", default="levels",
                   choices=["levels", "speech", "custom"])
    r.add_argument("--name", default=None)
    r.add_argument("--legacy", action="store_true",
                   help="purana builder (music 0.36, clip 1.0) — Type 2 "
                        "locked audio ke liye 'ranking' use karo")
    r.set_defaults(fn=cmd_rank)

    c = sub.add_parser("cine", help="movie-clip style edit")
    c.add_argument("--source", required=True)
    c.add_argument("--title", default=None)
    c.add_argument("--subtitle", default=None)
    c.add_argument("--length", type=float, default=28.0)
    c.add_argument("--mood", default="phonk", choices=["hype", "phonk", "chill"])
    c.add_argument("--music", default=None,
                   help="apna music file/URL (default: no music)")
    c.add_argument("--watermark", default="@studio")
    c.add_argument("--name", default=None)
    c.set_defaults(fn=cmd_cine)

    pk = sub.add_parser("peak", help="ONE continuous peak scene + teaser hook")
    pk.add_argument("--source", required=True, help="url/file of the clip (or movie name with --hindi)")
    pk.add_argument("--movie", default=None, help="movie name for hindi search")
    pk.add_argument("--scene", default=None, help="scene hint, e.g. 'chase'")
    pk.add_argument("--hindi", action="store_true",
                    help="use the existing HINDI dubbed version (no self-dubbing)")
    pk.add_argument("--title", default=None)
    pk.add_argument("--subtitle", default=None)
    pk.add_argument("--hook-text", default=None)
    pk.add_argument("--hook", type=float, default=4.6, help="hook length in seconds")
    pk.add_argument("--length", type=float, default=30.0)
    pk.add_argument("--music", default=None)
    pk.add_argument("--music-vol", type=float, default=0.12)
    pk.add_argument("--watermark", default="@studio")
    pk.add_argument("--name", default=None)
    pk.set_defaults(fn=cmd_peak)

    sc = sub.add_parser("scene", help="continuous scene + text editing")
    sc.add_argument("--source", required=True)
    sc.add_argument("--start", type=float, required=True)
    sc.add_argument("--dur", type=float, default=30.0)
    sc.add_argument("--script", default=None, help="json with header/captions/impacts")
    sc.add_argument("--header", default=None, help="'LINE ONE|LINE TWO'")
    sc.add_argument("--emoji", default=None)
    sc.add_argument("--sub-text", default=None)
    sc.add_argument("--header-dur", type=float, default=None)
    sc.add_argument("--no-rounded", action="store_true")
    sc.add_argument("--hook-at", type=float, default=None, help="source sec for the hook")
    sc.add_argument("--hook-dur", type=float, default=0.0)
    sc.add_argument("--layout", default="card", choices=["card", "tall", "full"])
    sc.add_argument("--watermark", default="@studio")
    sc.add_argument("--name", default=None)
    sc.set_defaults(fn=cmd_scene)

    rk = sub.add_parser("ranking", help="ref-A ranking layout")
    rk.add_argument("--source", required=True)
    rk.add_argument("--plan", required=True)
    rk.add_argument("--watermark", default="@studio")
    rk.add_argument("--name", default=None)
    rk.set_defaults(fn=cmd_ranking)

    pl = sub.add_parser("plan", help="plan-driven edit (JSON cut list + text)")
    pl.add_argument("--source", required=True)
    pl.add_argument("--plan", required=True)
    pl.add_argument("--watermark", default="@studio")
    pl.add_argument("--layout", default="card", choices=["card", "tall", "full"])
    pl.add_argument("--name", default=None)
    pl.set_defaults(fn=cmd_plan)

    au = sub.add_parser("auto", help="search + download + edit, all by itself")
    au.add_argument("--topic", required=True)
    au.add_argument("--count", type=int, default=5)
    au.add_argument("--title", default="RANKING THE BEST")
    au.add_argument("--line2", default=None)
    au.add_argument("--tagline", default="(Last one is crazy \U0001F631)")
    au.add_argument("--music", default=None,
                    help="apna music file/URL (default: no music)")
    au.add_argument("--per-item", type=float, default=6.5)
    au.add_argument("--watermark", default="@studio")
    au.add_argument("--sources", type=int, default=1,
                    help="how many compilations to pool clips from")
    au.add_argument("--labels-mode", default="levels",
                    choices=["levels", "speech", "custom"])
    au.add_argument("--name", default=None)
    au.set_defaults(fn=cmd_auto)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
