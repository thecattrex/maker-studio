"""Templates: turn analyzed sources into a Timeline.

  cine  -> movie/series clip edit: beat-cut montage + song + captions + punch-ins
  rank  -> "top N" countdown: header, live rank column, labels, boom moments
"""
import math
import os

import numpy as np

from render import Segment, Timeline
from textkit import esc
from util import CACHE, log, probe, ensure_ffmpeg


# --------------------------------------------------------------------- helpers
def beat_grid(music_info, fallback=0.5):
    beat = music_info["beat_interval"] if music_info else fallback
    off = music_info["phase"] if music_info else 0.0
    return beat, off


def snap(d, beat, minb=1, maxb=8):
    """Snap a duration to a whole number of beats."""
    n = max(minb, min(maxb, round(d / beat)))
    return n * beat, n


def pick_fit(src_w, src_h, kind="cine"):
    """Near-vertical sources fill the frame; wide ones get the 4:5 + blur treatment
    (cine crops in tight around the action instead)."""
    ar = (src_w or 16) / (src_h or 9)
    if ar <= 1.3:
        return "crop"
    return "crop" if kind == "cine" else "fill"


def focus_of(shot):
    fx = shot.get("face_x")
    fy = shot.get("face_y")
    if fx is None:
        return (0.5, 0.5)
    return (float(np.clip(fx, 0.25, 0.75)), float(np.clip(fy, 0.3, 0.7)))


def best_shots(shots, want, min_dur=0.6, prefer_motion=True):
    """Pick shots spread over the clip, weighted by motion (chronological output)."""
    usable = [s for s in shots
              if s["dur"] >= min_dur and 28 <= (s.get("bright") or 120) <= 225]
    if not usable:
        usable = shots[:]
    if prefer_motion and len(usable) > want:
        order = sorted(usable, key=lambda s: -s["motion_peak"])
        keep = set(id(s) for s in order[: max(want * 2, want + 4)])
        usable = [s for s in usable if id(s) in keep]
    # even spread in time
    if len(usable) > want:
        idx = np.linspace(0, len(usable) - 1, want).round().astype(int)
        usable = [usable[i] for i in dict.fromkeys(idx)]
    return usable


def words_in(speech, a, b):
    if not speech:
        return []
    return [w for w in speech["words"] if w["end"] > a and w["start"] < b]


# --------------------------------------------------------------------- CINE
def flash(ov, t, dur=0.08, alpha="&H30&", layer=8):
    """2-frame white flash on a cut."""
    ov.panel(t, t + dur, 0, 0, 1080, 1920, alpha=alpha,
             color="&HFFFFFF&", layer=layer)


CUT_PATTERN = [0.35, 0.5, 0.35, 0.8, 0.35, 0.5, 0.35, 1.2,
               0.35, 0.5, 0.35, 0.8, 0.5, 0.35, 0.6, 2.0]


def pool_sources(analyses):
    """Merge several analyzed sources into one pool (each shot keeps its own file)."""
    if not analyses:
        raise RuntimeError("no sources")
    packed = []
    for a in analyses:
        path = a["timeline"]["path"]
        ctop, cbot = a.get("bars", (0.0, 0.0))
        for sh in a["shots"]:
            sh = dict(sh)
            sh["src_path"] = path
            sh["crop_top"] = ctop
            sh["crop_bottom"] = cbot
            sh["_w"] = a["timeline"].get("width")
            sh["_h"] = a["timeline"].get("height")
            packed.append(sh)
    merged = dict(analyses[0])
    merged["shots"] = packed
    return merged


def build_cine(sources, music_info=None, music_path=None, title=None,
               subtitle=None, target=22.0, captions=True, watermark=None,
               fit=None, mood="hype", seed=3, hook=True):
    """Beat/onset-cut edit that KEEPS the real audio. No invented sfx.

    If a music file is supplied we cut to its onsets; otherwise we cut on the
    source's own audio transients so picture and sound stay related.
    """
    tl = Timeline(music=music_path, music_vol=0.22, name="cine")

    shots = []
    for s_ in sources:
        for sh in s_["shots"]:
            sh = dict(sh)
            sh["src_path"] = sh.get("src_path") or s_["timeline"]["path"]
            sh.setdefault("crop_top", s_.get("bars", (0.0, 0.0))[0])
            sh.setdefault("crop_bottom", s_.get("bars", (0.0, 0.0))[1])
            sh["_w"] = s_["timeline"].get("width")
            sh["_h"] = s_["timeline"].get("height")
            shots.append(sh)
    shots = [s for s in shots if s["dur"] > 0.4]
    if not shots:
        raise RuntimeError("no usable shots")

    # cut points: prefer real audio onsets in the source, else even spacing
    cut_times, t_acc = [], 0.0
    onsets = []
    for s_ in sources:
        en = s_.get("energy")
        if en and en.get("rms"):
            import numpy as _np
            r = _np.array(en["rms"], dtype=float)
            ts = _np.array(en["t"], dtype=float)
            thr = _np.percentile(r, 88)
            for i in range(2, len(r) - 2):
                if r[i] >= thr and r[i] >= r[i - 1] and r[i] >= r[i + 1]:
                    onsets.append(float(ts[i]))
    onsets = sorted(set(round(o, 2) for o in onsets))

    # build cut plan: alternate short/long so it breathes like a real edit
    target = min(target, (music_info or {}).get("duration", target) - 0.3)
    plan, i, t_used = [], 0, 0.0
    pool = sorted(shots, key=lambda s: -s.get("motion_peak", 0))
    while t_used < target - 0.3:
        # length: snap to next onset if available and close, else pattern
        base = [0.35, 0.5, 0.35, 0.8, 0.35, 0.5, 0.35, 1.2][i % 8]
        if onsets:
            cands = [o for o in onsets if abs(o - base) < 0.25]
            if cands:
                base = cands[0]
        if t_used + base > target:
            break
        plan.append((pool[i % len(pool)], base))
        t_used += base
        i += 1
    if not plan:
        raise RuntimeError("empty plan")

    for i, (s, d) in enumerate(plan):
        peak = s.get("motion_peak_t", s["start"] + s["dur"] * 0.5)
        ss = float(np.clip(peak - d * 0.6, s["start"],
                           max(s["start"], s["end"] - d - 0.02)))
        seg = Segment(src=s["src_path"], ss=ss, dur=d,
                      fit=fit or pick_fit(s.get("_w"), s.get("_h"), "cine"),
                      focus=focus_of(s), zoom=1.12 if i % 2 == 0 else 1.0,
                      zoom_to=None, speed=1.0, mute=False, grade=True,
                      crop_top=s.get("crop_top", 0.0),
                      crop_bottom=s.get("crop_bottom", 0.0))
        tl.add(seg)

    total = tl.duration()
    ov = tl.overlay
    zones = sources[0].get("zones") or {} if sources else {}

    # cinematic title: stacked, letter-spaced, centred in the upper third
    if title:
        lines = [title] if isinstance(title, str) else list(title)
        end_t = min(2.6, max(1.4, total * 0.28))
        ov.center_block(0.20, end_t, lines, size=78, gap=96, mid_y=420, spacing=10)
    if subtitle:
        ov.tagline(0.5, min(2.9, max(1.7, total * 0.32)), subtitle.upper(),
                   y=560, size=32)

    # captions: bottom third but above the UI strip, only if there is speech
    if captions and sources and sources[0].get("speech"):
        words = sources[0]["speech"]["words"]
        if words:
            ov.captions(words, y=1560, max_words=2, max_chars=15)

    if watermark:
        ov.watermark(watermark, x=1030, y=1770, size=28)
    return tl



# --------------------------------------------------------------------- PEAK
def find_peak_scene(src, want=26.0, pad_head=1.2):
    """Find ONE continuous high-energy stretch (not a montage)."""
    tl = src["timeline"]
    dur = tl["duration"]
    ts = np.array([s["t"] for s in tl["samples"]], dtype=float)
    mo = np.array([s["motion"] for s in tl["samples"]], dtype=float)
    if len(mo) < 8:
        return {"start": 0.0, "end": min(want, dur), "peak_t": min(want, dur) / 2}

    mo = mo / (np.percentile(mo, 92) + 1e-6)
    mo = np.clip(mo, 0, 1.5)

    en = src.get("energy") or {}
    if en.get("rms"):
        et = np.array(en["t"], dtype=float)
        er = np.array(en["rms"], dtype=float)
        er = er / (np.percentile(er, 92) + 1e-6)
        er = np.clip(np.interp(ts, et, er), 0, 1.5)
        score = 0.55 * mo + 0.45 * er
    else:
        score = mo

    dt = float(ts[1] - ts[0]) if len(ts) > 1 else 0.125
    k = max(3, int(round(1.5 / max(1e-3, dt))))
    smooth = np.convolve(score, np.ones(k) / k, mode="same")

    win = min(want, dur)
    per_win = max(4, int(win / max(1e-3, dt)))
    best, best_t = -1.0, 0.0
    step = max(1, per_win // 60)
    for i in range(0, max(1, len(ts) - per_win), step):
        t0 = ts[i]
        if t0 + win > dur:
            break
        sel = (ts >= t0) & (ts < t0 + win)
        if sel.sum() < 4:
            continue
        v = float(smooth[sel].mean()) * 0.75
        tg = (ts >= t0 + win * 0.75) & (ts <= t0 + win)
        if tg.any():
            v += float(smooth[tg].mean()) * 0.25
        if v > best:
            best, best_t = v, float(t0)

    start, end = best_t, min(dur, best_t + win)
    cuts = sorted(set(round(c, 2) for c in
                      ([0.0, dur] + [s["start"] for s in src.get("shots", [])])))
    prev_cut = max([c for c in cuts if c <= start + 0.4], default=0.0)
    next_cut = min([c for c in cuts if c >= end - 0.4], default=dur)
    start = max(0.0, prev_cut - pad_head * 0.25)
    end = min(dur, max(start + win * 0.85, next_cut))

    inside = (ts >= start) & (ts <= end)
    peak_t = float(ts[inside][int(np.argmax(smooth[inside]))]) if inside.any() \
        else start + win / 2
    return {"start": round(start, 2), "end": round(end, 2),
            "peak_t": round(peak_t, 2), "score": round(best, 3)}


def build_peak(src, title=None, subtitle=None, hook_dur=4.6, target=30.0,
               watermark=None, fit=None, hook_text=None, music_path=None,
               music_vol=0.0, text_mode="auto"):
    """ONE continuous scene with a teaser hook taken from its own peak.

    [0 .. hook_dur]  = the payoff moment, shown first
    [hook_dur ..]    = the same scene played from its start, uncut
    """
    tl = Timeline(music=music_path, music_vol=music_vol, name="peak")
    scene = find_peak_scene(src, want=max(18.0, target - hook_dur - 0.4))
    s0, s1, peak = scene["start"], scene["end"], scene["peak_t"]

    w, h = src["timeline"]["width"], src["timeline"]["height"]
    use_fit = fit or pick_fit(w, h, "cine")
    ctop, cbot = src.get("bars", (0.0, 0.0))

    focus = (0.5, 0.45)
    for sh in src.get("shots", []):
        if sh["start"] <= peak <= sh["end"] and sh.get("face_x"):
            focus = focus_of(sh)
            break

    ov = tl.overlay
    h_end = min(s1, max(s0 + hook_dur, peak + 1.2))
    h_start = max(s0, h_end - hook_dur)
    if h_end - h_start < 1.5:
        h_start, h_end = s0, min(s1, s0 + hook_dur)

    tl.add(Segment(src=src["timeline"]["path"], ss=h_start, dur=h_end - h_start,
                   fit=use_fit, focus=focus, zoom=1.0, mute=False, grade=True,
                   crop_top=ctop, crop_bottom=cbot))

    body = min(s1 - s0, max(12.0, target - (h_end - h_start)))
    tl.add(Segment(src=src["timeline"]["path"], ss=s0, dur=body,
                   fit=use_fit, focus=focus, zoom=1.0, mute=False, grade=True,
                   crop_top=ctop, crop_bottom=cbot))

    total = tl.duration()
    if title:
        lines = [title] if isinstance(title, str) else list(title)
        ov.center_block(0.15, min(2.4, total * 0.2), lines,
                        size=76, gap=94, mid_y=330, spacing=12)
    if subtitle:
        ov.tagline(0.45, min(2.7, total * 0.24), subtitle.upper(), y=470, size=30)
    if hook_text:
        ov.lower_title(0.2, max(0.6, h_end - h_start - 0.1), hook_text, y=1600, size=46)
    if watermark:
        ov.watermark(watermark, x=1030, y=1770, size=28)
    src["scene"] = scene
    return tl



# --------------------------------------------------------------------- SCENE EDIT
def build_scene_edit(src, ss, dur, header=None, emoji=None, captions=None,
                     impacts=None, watermark=None, rounded=True,
                     header_dur=None, sub_text=None, layout="card",
                     hook_at=None, hook_dur=0.0):
    """One continuous scene + real text editing (header, action captions, impacts)."""
    tl = Timeline(name="scene")
    srcp = src["timeline"]["path"]
    w, h = src["timeline"]["width"], src["timeline"]["height"]
    ctop, cbot = src.get("bars", (0.0, 0.0))

    focus = (0.5, 0.45)
    for sh in src.get("shots", []):
        if sh["start"] <= ss + dur / 2 <= sh["end"] and sh.get("face_x"):
            focus = focus_of(sh)
            break

    LAYOUTS = {                      # (box_w, box_h, box_y, radius)
        "card": (1010, 860, 300, 34),   # mild crop, full width
        "tall": (1010, 1300, 300, 42),  # reference-style tall box (2.3x crop)
        "full": (1080, 1920, 0, 0),     # full-bleed 9:16
    }
    if rounded:
        from analyze import rounded_mask
        bw, bh, by, br = LAYOUTS[layout]
        tl.rounded_frame = rounded_mask(os.path.join(CACHE, "mask.png"),
                                        box_w=bw, box_h=bh, box_y=by, radius=br)
        tl.rounded_frame["bg"] = "blur" if layout in ("card", "tall") else "none"
        use_fit = "crop"
    else:
        use_fit = pick_fit(w, h, "cine")

    seg_kw = dict(fit=use_fit, focus=focus, zoom=1.0, mute=False, grade=True,
                  crop_top=ctop, crop_bottom=cbot)
    off = 0.0
    if hook_at is not None and hook_dur > 0:
        tl.add(Segment(src=srcp, ss=hook_at, dur=hook_dur, **seg_kw))
        off = hook_dur
    tl.add(Segment(src=srcp, ss=ss, dur=dur, **seg_kw))
    total = tl.duration()
    ov = tl.overlay

    if header:
        lines = list(header) if isinstance(header, (list, tuple)) else [header]
        ov.header(0.0, header_dur or total, lines[0],
                  lines[1] if len(lines) > 1 else "",
                  size=54, y=120, gap=64, emoji=emoji)
    if sub_text:
        ov.tagline(0.2, min(3.4, total), sub_text, y=228, size=26)
    for c in (captions or []):
        ov.action_caption(max(0.0, c["t0"] + off), min(total, c["t1"] + off), c["text"],
                          y=c.get("y", 1100), size=c.get("size", 44),
                          paren=c.get("paren", True))
    for im in (impacts or []):
        ov.impact(max(0.0, im["t"] + off), im.get("dur", 1.4), im["text"],
                  y=im.get("y", 980), size=im.get("size", 96),
                  color=im.get("color"))
    if watermark:
        ov.watermark(watermark, x=1030, y=1770, size=28)
    return tl



# ---------------------------------------------------------------- PLAN EDITOR
def build_plan_edit(src_path, plan, words=None, watermark=None, layout="card"):
    """Cut-list + text layers driven by a JSON plan (all times in seconds).

    plan = {
      "clips": [{"ss":79.5,"dur":21.6,"fit":"crop","layout":"card"}, ...],
      "texts": [{"t":0,"dur":3.2,"kind":"impact|header|action|tagline",
                 "text":"...","y":760,"size":104}],
      "dialogue": {"clip": 2, "y":1150, "size":54, "max_words":3}
    }
    `clip` in `dialogue` is the index of the clip whose SOURCE audio carries the
    speech; word times are mapped onto the final timeline automatically.
    """
    from util import probe
    info = probe(src_path)
    size = tuple(plan.get("size", (1080, 1920)))
    tl = Timeline(name="plan", size=size)
    tl.look = plan.get("look")
    band = int(plan.get("band", 0))
    if band:
        tl.frame = (0, band, size[0], size[1] - band - int(plan.get("bottom_band", 0)))
    ctop = cbot = 0.0
    try:
        from analyze import detect_bars
        ctop, cbot = detect_bars(src_path)
    except Exception:
        pass

    LAYOUTS = {"card": (1010, 860, 300, 34), "tall": (1010, 1300, 300, 42)}
    first = plan["clips"][0].get("layout", plan.get("layout", layout))
    if tl.frame:
        first = "none"          # band layout — never wrap in a rounded card
    if first in LAYOUTS:
        from analyze import rounded_mask
        bw, bh, by, br = LAYOUTS[first]
        tl.rounded_frame = rounded_mask(os.path.join(CACHE, "mask.png"),
                                        box_w=bw, box_h=bh, box_y=by, radius=br)
        tl.rounded_frame["bg"] = "blur" if bw < 1080 else "none"
        default_fit = "crop"
    else:
        default_fit = pick_fit(info["width"], info["height"], "cine")

    spans = []                      # (global_start, global_end, src_ss, src_dur)
    clock = 0.0
    for c in plan["clips"]:
        ss, dur = float(c["ss"]), float(c["dur"])
        tl.add(Segment(src=src_path, ss=ss, dur=dur,
                       fit=c.get("fit", default_fit),
                       focus=tuple(c.get("focus", (0.5, 0.45))),
                       zoom=c.get("zoom", 1.0), zoom_to=c.get("zoom_to"),
                       bright=c.get("bright", 0.0), mute=False, grade=True,
                       crop_top=ctop, crop_bottom=cbot,
                       crop_left=float(c.get("crop_left", 0.0)),
                       crop_right=float(c.get("crop_right", 0.0))))
        spans.append((clock, clock + dur, ss, dur))
        clock += dur
    total = tl.duration()

    ov = tl.overlay
    caps_lines = plan.get("cap_lines")
    if caps_lines:
        ov.yellow_caps(caps_lines, y=int(plan.get("cap_y", size[1] - 140)),
                       size=int(plan.get("cap_size", 38)),
                       max_words=int(plan.get("cap_max_words", 4)),
                       cx=size[0] // 2)

    COLORS = {"white": "&H00FFFFFF&", "red": "&H2E2EF7&",
              "yellow": "&H0000D7FF&", "black": "&H000000&"}

    def _col(v, dflt="white"):
        return COLORS.get(str(v).lower(), v if str(v).startswith("&H") else COLORS[dflt])

    top = plan.get("top_text")
    if top:
        ty = int(plan.get("band_text_y", 74))
        hgap = int(plan.get("header_gap", 84))
        hsize = int(plan.get("header_size", 58))
        lines = [top] if isinstance(top[0], str) else list(top)
        for i, ln in enumerate(lines):
            parts, fsz = [], hsize
            if isinstance(ln, dict):
                txt   = str(ln.get("text", "")).upper()
                col   = _col(ln.get("color", "white"))
                fsz   = int(ln.get("size", hsize))
                hi    = str(ln.get("hi", "")).upper()
                hicol = _col(ln.get("hi_color", "yellow"))
                if hi and hi in txt:
                    bef, _, aft = txt.partition(hi)
                    if bef:
                        parts.append("{\\c" + col + "}" + esc(bef))
                    parts.append("{\\c" + hicol + "}" + esc(hi))
                    if aft:
                        parts.append("{\\c" + col + "}" + esc(aft))
                else:
                    parts.append("{\\c" + col + "}" + esc(txt))
                ypos = int(ln.get("y", ty + i * hgap))
            else:
                words = [ln] if isinstance(ln, str) else list(ln)
                for j, w in enumerate(words):
                    c = "&H00FFFFFF&" if j == 0 else "&H0000D7FF&"
                    parts.append("{\\c" + c + "}" + esc(str(w).upper()))
                ypos = ty + i * hgap
            ov.add(0.0, total, "Title",
                   "{\\an5\\pos(%d,%d)\\fs%d\\fsp2\\bord8"
                   "\\bordcolor&H000000&\\shad2\\4c&H000000&}%s"
                   % (size[0] // 2, ypos, fsz, " ".join(parts)))

    for tx in plan.get("texts", []):
        t0 = float(tx["t"]); dur = float(tx.get("dur", 2.0))
        kind, txt = tx.get("kind", "impact"), tx.get("text", "")
        if kind == "impact":
            ov.impact(t0, dur, txt, y=tx.get("y", 760), size=tx.get("size", 104))
        elif kind == "header":
            lines = txt if isinstance(txt, list) else [txt]
            ov.header(t0, t0 + dur, lines[0], lines[1] if len(lines) > 1 else "",
                      size=tx.get("size", 54), y=tx.get("y", 120))
        elif kind == "action":
            ov.action_caption(t0, t0 + dur, txt, y=tx.get("y", 1100),
                              size=tx.get("size", 44))
        elif kind == "tagline":
            ov.tagline(t0, t0 + dur, txt, y=tx.get("y", 228), size=tx.get("size", 26))
        elif kind == "rank":
            num = tx.get("num")
            ov.badge(t0, t0 + dur, num, tx.get("total", 5), x=tx.get("x", 850),
                     y=tx.get("y", 1080), size=tx.get("size", 96))
            if tx.get("label"):
                ov.label_bar(t0, t0 + dur, tx["label"], x=tx.get("x", 850),
                             y=tx.get("ly", 1215), size=tx.get("lsize", 34))
        elif kind == "dialogue":     # manual override, global time
            ov.dialogue_caps([{"w": w, "s": t0 + i * 0.001, "e": t0 + dur}
                              for i, w in enumerate(txt.split())],
                             lambda t: t, y=tx.get("y", 1150),
                             size=tx.get("size", 54))

    d = plan.get("dialogue")
    if d and words:
        idx = int(d.get("clip", 0))
        g0, g1, ss, dur = spans[idx]

        def to_global(t, g0=g0, ss=ss, dur=dur):
            if t < ss - 0.05 or t > ss + dur + 0.05:
                return None
            return g0 + max(0.0, t - ss)

        ov.dialogue_caps(words, to_global, y=d.get("y", 1150),
                         size=d.get("size", 54), max_words=d.get("max_words", 3),
                         max_dur=d.get("max_dur", 2.2))

    for vo in plan.get("voice", []):
        tl.sfx.append((round(float(vo.get("at", 0.0)), 3), vo["path"],
                        float(vo.get("gain", 1.0))))
    tl.original_vol = float(plan.get("duck", 1.0))

    if watermark:
        ov.watermark(watermark, x=1030, y=1770, size=28)
    return tl



# ---------------------------------------------------------- RANKING (ref-A)
def build_ranking(src_path, items, title=("RANKING", "INSANE PARKOUR FAILS"),
                  band=300, bottom=250, gap=0.22, size=(1080, 1920),
                  watermark=None, order=None, title_size=116, ladder="play",
                  music=None, music_vol=0.67, music_ss=10.0,
                  clip_vol=0.55, sfx_dir=None, sfx_peak_db=-11.0):
    """Reference-A layout: black title band on top, video full width below,
    persistent numbered list on the left, clips in a shuffled order (1 last).

    items: [{"ss":..,"dur":..,"n":1,"label":"..","focus":[x,y],"color":"..",
             "sfx":[{"at":..,"key":".."}]}]

    Audio parameters are caller-configurable. Current Type-2 production uses the
    selected C2 bed (`studio/type2/assets/c2_48.wav`) at about 17%, plus the
    dedicated Type-2 phrase/chicken/SFX mixer. Do not use historical QKThr/67%
    prototype values for new production. Generic callers should pass explicit
    music/music_vol/clip_vol rather than relying on legacy defaults.

      music      explicit background track, starts at `music_ss`
      music_vol  explicit caller setting
      clip_vol   explicit caller setting
      sfx        1 per clip MAX, placed `at` seconds into the clip
      sfx_peak_db absolute peak level for every sfx (auto-normalised)
    """
    from util import probe
    from analyze import detect_bars
    info = probe(src_path)
    W, H = size
    tl = Timeline(name="ranking", size=size,
                  music=(music if music and os.path.exists(music) else None),
                  music_vol=music_vol)
    tl.music_ss = float(music_ss)
    tl.original_vol = clip_vol
    tl.master_gain_db = 3.5
    try:
        ctop, cbot = detect_bars(src_path)
    except Exception:
        ctop = cbot = 0.0

    vid_h = H - band - bottom
    tl.frame = (0, band, W, vid_h)
    clock = 0.0
    seq = order if order else list(range(len(items)))
    spans = []                     # (global_start, n, label, played_before[])
    played = []
    sfx_jobs = []                  # (global_time, key)
    for step, i in enumerate(seq):
        it = dict(items[i])
        it.setdefault("n", i + 1)
        if step:                    # black beat so each clip visibly ends
            tl.add_gap(gap)
            clock += gap
        tl.add(Segment(src=src_path, ss=float(it["ss"]), dur=float(it["dur"]),
                       fit="crop", focus=tuple(it.get("focus", (0.5, 0.45))),
                       zoom=1.0, zoom_to=it.get("zoom_to", 1.0),
                       mute=False, grade=True,
                       crop_top=float(it.get("crop_top", ctop)),
                       crop_bottom=float(it.get("crop_bottom", cbot))))
        for sx in (it.get("sfx") or []):
            sfx_jobs.append((clock + float(sx["at"]), sx["key"]))
        spans.append((clock, int(it["n"]), it.get("label", ""), list(played)))
        played.append(int(it["n"]) - 1)
        clock += float(it["dur"])
    total = tl.duration()

    ov = tl.overlay
    # title in the top band, always on screen (per-word colours like the ref)
    for ln, y in zip(title, (int(band * 0.33), int(band * 0.72))):
        if not ln:
            continue
        words = list(ln) if isinstance(ln, (list, tuple)) else [(ln, "&H00FFFFFF&")]
        parts = []
        for w, c in words:
            if isinstance(c, dict):
                c = c.get("color", "&H00FFFFFF&")
            parts.append("{\\c" + str(c) + "}" + esc(str(w).upper()))
        ov.add(0.0, total, "Title",
               "{\\an5\\pos(540," + str(y) + f")\\fs{title_size}\\fsp2\\bord9"
               "\\bordcolor&H000000&\\shad0}" + " ".join(parts))

    # persistent side list
    all_items = [{"n": it.get("n", idx + 1), "label": it.get("label", ""),
                  "color": it.get("color", "&H00FFFFFF&")}
                 for idx, it in enumerate(items)]
    # ladder: row order down the left edge. "play" = old behaviour (play order),
    # "desc" = 5..1 top-down (normal countdown), "asc" = 1..5 top-down.
    if ladder == "desc":
        all_items = sorted(all_items, key=lambda d: -int(d["n"]))
    elif ladder == "asc":
        all_items = sorted(all_items, key=lambda d: int(d["n"]))
    for k, (g0, n, label, before) in enumerate(spans):
        dur = (spans[k + 1][0] - g0) if k + 1 < len(spans) else total - g0
        ov.rank_side_list(g0, g0 + dur, all_items, x=86, y0=band + 168, gap=232,
                     size=101, num_w=96, active=n - 1, done=set(before),
                     labels_on=set(before) | {n - 1})
    if watermark:
        ov.watermark(watermark, x=1030, y=H - 40, size=26)

    # ---- sfx: 1 per clip, auto-normalised to an absolute peak level ----
    if sfx_dir and sfx_jobs:
        from util import probe as _probe
        for gt, key in sfx_jobs:
            path = os.path.join(sfx_dir, key + ".mp3")
            if not os.path.exists(path):
                log(f"  sfx missing, skipping: {key}")
                continue
            pk = _peak_db(path)
            gain = 10 ** ((sfx_peak_db - pk) / 20.0)
            tl.add_sfx(gt, key, gain=round(gain, 4), path=path)
    return tl


def _peak_db(path):
    """Peak level of an audio file in dBFS."""
    from util import run
    exe = ensure_ffmpeg()
    r = run([exe, "-v", "error", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    err = (r.stderr or "") + (r.stdout or "")
    import re as _re
    m = _re.search(r"max_volume:\s*(-?[\d.]+) dB", err)
    return float(m.group(1)) if m else -6.0


def build_rank(src, music_info=None, music_path=None, title_lines=None,
               tagline=None, labels=None, count=5, watermark=None,
               per_item=6.5, fit=None, labels_mode="levels",
               endcard="FOLLOW FOR MORE", endcard_time=1.2, hook=True,
               text_mode="auto"):
    """Top-N countdown. Text stays minimal + sits in the frame's empty area."""
    tl = Timeline(music=music_path, music_vol=0.36, name="rank")
    labels_mode = "custom" if labels else labels_mode

    picks = best_shots(src["shots"], count + 4, min_dur=max(1.5, per_item * 0.5))
    ded, seen = [], set()
    for p in picks:
        key = (p.get("src_path"), round(p["start"], 1))
        if key in seen:
            continue
        seen.add(key)
        ded.append(p)
    picks = ded[:count]
    if not picks:
        raise RuntimeError("no usable clips")

    w, h = src["timeline"]["width"], src["timeline"]["height"]
    use_fit = fit or pick_fit(w, h, "rank")
    ctop, cbot = src.get("bars", (0.0, 0.0))
    zones = src.get("zones") or {}
    ov = tl.overlay

    # auto: if the source already has its own scoreboard on the left, stay minimal
    own_scoreboard = zones.get("left_busy", 0) >= 2
    if text_mode == "auto":
        text_mode = "minimal" if own_scoreboard else "full"
    X = 742 if zones.get("free_right", True) else 250   # text column

    if hook:
        best = max(picks, key=lambda q: q.get("motion_peak", 0))
        hd = 1.15
        hs = float(np.clip(best.get("motion_peak_t", best["start"]) - hd * 0.55,
                           best["start"], max(best["start"], best["end"] - hd)))
        tl.add(Segment(src=best.get("src_path") or src["timeline"]["path"], ss=hs,
                       dur=hd, fit=use_fit, focus=focus_of(best), zoom=1.0,
                       zoom_to=1.10, mute=False, grade=True,
                       crop_top=best.get("crop_top", ctop),
                       crop_bottom=best.get("crop_bottom", cbot)))

    LEVELS = [35, 50, 60, 80, 100]
    FILLER = {"i", "got", "this", "bro", "so", "and", "the", "is", "it's", "its",
              "oh", "yeah", "a", "to", "of", "he", "she", "that", "was", "my",
              "you", "we", "they", "in", "on", "at", "for", "but", "with", "his",
              "her", "when", "then", "as", "did", "do", "just", "like", "all"}

    def label_for(i):
        if labels_mode == "custom" and labels and i < len(labels):
            return labels[i].strip()
        if labels_mode == "speech" and src.get("speech"):
            a = picks[i]["start"] - 0.4
            ws = [x["w"] for x in src["speech"]["words"] if a < x["start"] < a + 2.4]
            words = [x.strip(".,!?'\"") for x in ws]
            while words and words[0].lower() in FILLER:
                words.pop(0)
            txt = " ".join(words[:3]).strip(" ,.!?")
            if txt:
                return (txt[0].upper() + txt[1:])[:24]
        return f"Level {LEVELS[i] if i < len(LEVELS) else 40 + i * 10}"

    item_times = []
    for i, p in enumerate(picks):
        seg_dur = min(per_item, max(2.4, p["dur"]))
        peak = p.get("motion_peak_t", p["start"] + seg_dur * 0.5)
        ss = float(np.clip(peak - seg_dur * 0.55, p["start"],
                           max(p["start"], p["end"] - seg_dur - 0.03)))
        ss = min(ss, max(0.0, src["timeline"]["duration"] - seg_dur - 0.05))
        tl.add(Segment(src=p.get("src_path") or src["timeline"]["path"], ss=ss,
                       dur=seg_dur, fit=use_fit, focus=focus_of(p), zoom=1.0,
                       zoom_to=1.10, mute=False, grade=True,
                       crop_top=p.get("crop_top", ctop),
                       crop_bottom=p.get("crop_bottom", cbot)))
        t0 = tl.duration() - seg_dur
        item_times.append((t0, t0 + seg_dur))

    end_t = tl.duration() + endcard_time
    score_end = end_t - endcard_time

    # ---------------- end card
    p = max(picks, key=lambda q: q.get("motion_peak", 0))
    tl.add(Segment(src=p.get("src_path") or src["timeline"]["path"],
                   ss=min(p["start"] + p["dur"] * 0.55,
                          max(0.0, src["timeline"]["duration"] - 0.35)),
                   dur=0.35, fit=use_fit, focus=focus_of(p), mute=True, grade=True,
                   freeze=True, freeze_to=endcard_time,
                   crop_top=p.get("crop_top", ctop),
                   crop_bottom=p.get("crop_bottom", cbot)))
    ov.panel(score_end, end_t, 0, 0, 1080, 1920, alpha="&H7A&")
    first, _, rest = endcard.partition(" ")
    ov.center_block(score_end + 0.1, end_t, [first, "*" + (rest or "MORE")],
                    size=88, gap=104, mid_y=880)

    # ---------------- title (top, only 2s, never overlaps source header)
    lines = (title_lines or ["RANKING THE BEST"])[:2]
    t_end = min(2.1, max(1.2, tl.duration() * 0.18))
    ov.center_block(0.0, t_end, lines, size=84, gap=98, mid_y=250)
    if tagline:
        ov.tagline(0.3, min(2.4, t_end + 0.3), tagline, y=372, size=34)

    # ---------------- per-item marker
    if text_mode == "minimal":
        # source already shows its own ranking -> add nothing that could clash
        pass
    else:
        for i, (a, b) in enumerate(item_times):
            active = (a, min(b, score_end))
            ov.badge(active[0], active[1], num=i + 1, total=len(picks),
                     x=X, y=1120, size=124, w=180, h=180)
            lbl = label_for(i)
            if lbl:
                ov.label_bar(active[0], active[1], lbl, x=X, y=1268,
                             size=38, width=320)

    if watermark:
        ov.watermark(watermark, x=1030, y=1770, size=30)
    return tl


def save_overlay(tl, path):
    tl.overlay.path = path
    tl.overlay.write(path)
    return path
