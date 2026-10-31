"""Analyze a video: shots, motion, faces, loudness, speech. Everything cached as JSON.

A "shot" is a continuous camera take. A "moment" is a candidate highlight inside a shot,
scored by motion + audio energy (the thing you'd clip for a fail/hype compilation).
"""
import glob
import os
import wave

import numpy as np

from util import (FFMPEG, CACHE, ensure_ffmpeg, load_cache, log, probe, run,
                  save_cache)

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")


def _cv2():
    import cv2
    cv2.setNumThreads(2)
    return cv2


# ---------------------------------------------------------------- video brain
def video_timeline(path, sample_fps=8.0, cache=True, proxy_w=480):
    """Codec-agnostic: ffmpeg extracts small JPEGs, cv2 does motion/faces/scene."""
    if cache:
        hit = load_cache("vtl", path + f"@{sample_fps}")
        if hit:
            return hit

    cv2 = _cv2()
    info = probe(path)
    if not info["duration"]:
        raise RuntimeError(f"cannot read {path}")

    pdir = os.path.join(CACHE, "proxy")
    os.makedirs(pdir, exist_ok=True)
    for f in glob.glob(os.path.join(pdir, "*.jpg")):
        os.remove(f)
    r = run([FFMPEG, "-v", "error", "-i", path, "-an",
             "-vf", f"fps={sample_fps},scale='min({proxy_w},iw)':-2",
             "-q:v", "6", os.path.join(pdir, "f%06d.jpg"), "-y"], timeout=900)
    files = sorted(glob.glob(os.path.join(pdir, "f*.jpg")))
    if not files:
        raise RuntimeError("no frames decoded: " + (r.stderr or "")[-400:])

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    samples, hist_prev = [], None
    prev_gray = None
    for i, f in enumerate(files):
        frame = cv2.imread(f, cv2.IMREAD_COLOR)
        if frame is None:
            continue
        h, w = frame.shape[:2]
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion = float(np.mean(cv2.absdiff(g, prev_gray))) if (
            prev_gray is not None and prev_gray.shape == g.shape) else 0.0
        prev_gray = g
        hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8],
                            [0, 256, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        scene = float(cv2.compareHist(hist_prev, hist, cv2.HISTCMP_BHATTACHARYYA)) if (
            hist_prev is not None) else 0.0
        hist_prev = hist
        faces = cascade.detectMultiScale(g, 1.15, 5, minSize=(20, 20)) if cascade else ()
        fx = fy = 0.5
        fw = fh = 0.0
        if len(faces):
            b = max(faces, key=lambda q: q[2] * q[3])
            fx = (b[0] + b[2] / 2) / w
            fy = (b[1] + b[3] / 2) / h
            fw = b[2] / w
            fh = b[3] / h
        samples.append({"t": round(i / sample_fps, 2), "motion": round(motion, 2),
                        "bright": round(float(np.mean(g)), 1),
                        "scene": round(scene, 3),
                        "fx": round(float(fx), 3), "fy": round(float(fy), 3),
                        "fw": round(float(fw), 3), "fh": round(float(fh), 3)})

    if not samples:
        raise RuntimeError("no frames decoded")

    m = np.array([s["motion"] for s in samples], dtype=float)
    if len(m) > 3:
        k = np.array([1, 2, 3, 2, 1], dtype=float)
        k /= k.sum()
        m = np.convolve(m, k, mode="same")
    for s, v in zip(samples, m):
        s["motion"] = round(float(v), 2)

    res = {"path": path, "duration": info["duration"], "fps": info["fps"],
           "width": info["width"], "height": info["height"],
           "sample_fps": sample_fps, "samples": samples}
    if cache:
        save_cache("vtl", path + f"@{sample_fps}", res)
    return res


def scene_cuts(timeline, thresh=0.32, min_gap=0.45):
    cuts = [0.0]
    for s in timeline["samples"]:
        if s["scene"] >= thresh and s["t"] - cuts[-1] >= min_gap:
            cuts.append(s["t"])
    if timeline["duration"] - cuts[-1] < min_gap:
        cuts.pop()
    cuts.append(timeline["duration"])
    return cuts


def shots(timeline, thresh=0.32, min_dur=0.8, max_dur=12.0):
    """List of shots with motion stats + best face position."""
    cuts = scene_cuts(timeline, thresh)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a < min_dur:
            continue
        chunk = [s for s in timeline["samples"] if a <= s["t"] < b]
        if not chunk:
            continue
        mo = np.array([s["motion"] for s in chunk])
        faces = [(s["fx"], s["fy"], s["fw"]) for s in chunk if s["fw"] > 0]
        out.append({
            "start": round(a, 2), "end": round(b, 2), "dur": round(b - a, 2),
            "motion_mean": round(float(mo.mean()), 2),
            "motion_peak": round(float(mo.max()), 2),
            "motion_peak_t": round(float(chunk[int(mo.argmax())]["t"]), 2),
            "bright": round(float(np.mean([s["bright"] for s in chunk])), 1),
            "face_x": round(float(np.median([f[0] for f in faces])), 3) if faces else None,
            "face_y": round(float(np.median([f[1] for f in faces])), 3) if faces else None,
            "face_ratio": round(len(faces) / len(chunk), 2),
        })
    # split very long shots at their calmest point
    fixed = []
    for s in out:
        while s["dur"] > max_dur:
            chunk = [x for x in timeline["samples"] if s["start"] <= x["t"] < s["end"]]
            mid = [x for x in chunk if s["start"] + max_dur * 0.4 < x["t"] < s["start"] + max_dur * 0.7]
            cut = min(mid, key=lambda x: x["motion"])["t"] if mid else s["start"] + s["dur"] / 2
            a = dict(s); b = dict(s)
            a["end"], b["start"] = round(cut, 2), round(cut, 2)
            for x in (a, b):
                x["dur"] = round(x["end"] - x["start"], 2)
            fixed += [a]
            s = b
        fixed.append(s)
    return fixed


# ---------------------------------------------------------------- audio brain
def load_wav(path, sr=22050):
    wav = os.path.join(CACHE, "tmp.wav")
    os.makedirs(CACHE, exist_ok=True)
    run([FFMPEG, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
         "-c:a", "pcm_s16le", wav, "-y"], check=True)
    with wave.open(wav) as w:
        n = w.getnframes()
        y = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return y, sr


def audio_energy(path, win=0.05, cache=True):
    hit = load_cache("aen", path)
    if hit:
        return hit
    y, sr = load_wav(path)
    hop = int(sr * win)
    n = len(y) // hop
    if n < 2:
        return {"win": win, "rms": [], "t": []}
    r = np.array([float(np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2)))
                  for i in range(n)])
    res = {"win": win, "t": [round(i * win, 2) for i in range(n)],
           "rms": [round(float(v), 4) for v in r]}
    if cache:
        save_cache("aen", path, res)
    return res


def speech(path, lang=None, model="small", cache=True):
    """Word-level transcript (faster-whisper). Returns None if silent."""
    hit = load_cache("asr", path + f"@{lang}@{model}")
    if hit:
        return hit
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=2)
    segs, info = m.transcribe(path, language=lang, vad_filter=True, beam_size=5,
                              word_timestamps=True, condition_on_previous_text=False)
    words, texts = [], []
    for s in segs:
        for w in (s.words or []):
            words.append({"w": w.word.strip(), "start": round(w.start, 2),
                          "end": round(w.end, 2)})
        texts.append(s.text.strip())
    res = {"language": info.language,
           "language_prob": round(info.language_probability, 3),
           "text": " ".join(texts).strip(), "words": words}
    if cache:
        save_cache("asr", path + f"@{lang}@{model}", res)
    return res if res["text"] else None


# ---------------------------------------------------------------- moments
def moments(timeline, energy=None, min_dur=1.2, max_dur=6.0, top=None):
    """Score candidate highlight windows by motion + loudness."""
    dur = timeline["duration"]
    ts = np.array([s["t"] for s in timeline["samples"]])
    mo = np.array([s["motion"] for s in timeline["samples"]])
    if mo.max() > 0:
        mo = mo / (np.percentile(mo, 95) + 1e-6)
    base = np.clip(mo, 0, 2)

    if energy and energy["rms"]:
        et = np.array(energy["t"])
        er = np.array(energy["rms"])
        er = er / (np.percentile(er, 95) + 1e-6)
        el = np.interp(ts, et, er)
        score = 0.6 * base + 0.4 * np.clip(el, 0, 2)
    else:
        score = base

    out = []
    step = 0.4
    t = 0.0
    while t + min_dur <= dur:
        w = np.clip(max_dur, min_dur, 6.0)
        sel = (ts >= t) & (ts < t + w)
        if sel.sum() >= 3:
            s = float(score[sel].mean())
            peak_i = int(np.where(sel)[0][np.argmax(score[sel])])
            out.append({"start": round(t, 2), "end": round(min(t + w, dur), 2),
                        "score": round(s, 3), "peak_t": round(float(ts[peak_i]), 2)})
        t += step
    out.sort(key=lambda x: -x["score"])
    # suppress overlaps
    picked = []
    for c in out:
        if all(min(c["end"], p["end"]) - max(c["start"], p["start"]) < 0.35 for p in picked):
            picked.append(c)
        if top and len(picked) >= top:
            break
    return picked


def analyze(path, need_speech=True, lang=None, model="small"):
    tl = video_timeline(path)
    en = audio_energy(path) if probe(path)["has_audio"] else None
    sp = None
    if need_speech and en:
        try:
            sp = speech(path, lang=lang, model=model)
        except Exception as e:  # noqa
            log("asr failed:", e)
    return {"timeline": tl, "energy": en, "speech": sp,
            "shots": shots(tl), "moments": moments(tl, en)}


def detect_bars(path, samples=6, dark=34, cap_top=0.24, cap_bot=0.20,
                run_frac=0.10):
    """Height fraction of black banner bars at top & bottom.

    A row is "banner" when most of its pixels are dark. We treat a solid block
    of *real content* rows (a run of >=10% of the height) as the frame, so white
    caption text sitting inside a black banner doesn't end the scan early.
    """
    import cv2
    import statistics
    cv2 = _cv2()
    info = probe(path)
    dur = info["duration"] or 1
    tops, bots = [], []
    for i in range(samples):
        t = dur * (i + 0.5) / samples
        tmp = os.path.join(CACHE, "bar.jpg")
        run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
             "-vf", "scale=320:-2", "-q:v", "4", tmp, "-y"])
        im = cv2.imread(tmp, cv2.IMREAD_GRAYSCALE)
        if im is None:
            continue
        n = len(im)
        content = ((im < dark).mean(axis=1) < 0.5)   # row has real picture
        runlen = max(6, int(n * run_frac))

        top = 0
        limit = int(n * cap_top)
        i0 = 0
        while i0 < limit:
            if content[i0:i0 + runlen].all():
                top = i0
                break
            i0 += 1
        else:
            top = 0

        bot = 0
        limit = int(n * cap_bot)
        i1 = n
        while i1 > n - limit:
            if content[i1 - runlen:i1].all():
                bot = n - i1
                break
            i1 -= 1
        else:
            bot = 0

        tops.append(top / n)
        bots.append(bot / n)
    if not tops:
        return 0.0, 0.0
    ct, cb = statistics.median(tops), statistics.median(bots)
    return round(ct if ct > 0.015 else 0.0, 3), round(cb if cb > 0.015 else 0.0, 3)


# ---------------------------------------------------------------- frame quality
def frame_quality(path, times, w=320):
    """Per-timestamp quality: brightness, contrast and sharpness.

    Sharpness = variance of the Laplacian. Blurry / black / washed-out frames
    score badly, so we can skip them when picking clips automatically.
    """
    import cv2
    cv2 = _cv2()
    out = []
    tmp = os.path.join(CACHE, "fq.jpg")
    for t in times:
        run([FFMPEG, "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-i", path,
             "-frames:v", "1", "-vf", f"scale={w}:-2", "-q:v", "4", tmp, "-y"])
        im = cv2.imread(tmp, cv2.IMREAD_GRAYSCALE)
        if im is None:
            out.append({"t": t, "bright": 0.0, "contrast": 0.0, "sharp": 0.0})
            continue
        lap = cv2.Laplacian(im, cv2.CV_64F)
        out.append({"t": round(float(t), 2),
                    "bright": round(float(im.mean()), 1),
                    "contrast": round(float(im.std()), 1),
                    "sharp": round(float(lap.var()), 1)})
    return out


# ---------------------------------------------------------------- text zones
def text_zones(path, samples=8):
    """Find where the SOURCE already has text/graphics, so our overlays avoid it.

    Splits the frame into a 3x4 grid, then measures edge density + how "flat"
    each cell is. Any cell with lots of edges = busy/text area -> avoid.
    Returns a list of recommended anchor boxes in 1080x1920 space.
    """
    import cv2
    cv2 = _cv2()
    info = probe(path)
    dur = info["duration"] or 1
    cols, rows = 3, 4
    acc = np.zeros((rows, cols))
    n = 0
    for i in range(samples):
        t = dur * (i + 0.5) / samples
        tmp = os.path.join(CACHE, "zone.jpg")
        run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
             "-vf", "scale=360:-2", "-q:v", "4", tmp, "-y"])
        im = cv2.imread(tmp, cv2.IMREAD_GRAYSCALE)
        if im is None:
            continue
        h, w = im.shape
        edges = cv2.Laplacian(im, cv2.CV_32F, ksize=3)
        e = np.abs(edges)
        for r in range(rows):
            for c in range(cols):
                cell = e[r * h // rows:(r + 1) * h // rows, c * w // cols:(c + 1) * w // cols]
                acc[r, c] += float(cell.mean())
        n += 1
    if n == 0:
        return {"busy": [[0] * cols for _ in range(rows)],
                "free_right": True, "free_left": True}
    acc /= n
    thr = float(np.percentile(acc, 62))
    busy = [[1 if acc[r, c] > thr else 0 for c in range(cols)] for r in range(rows)]
    # which vertical half is emptier?
    left = sum(busy[r][0] for r in range(rows))
    right = sum(busy[r][2] for r in range(rows))
    return {"busy": busy, "score": acc.round(1).tolist(),
            "free_right": right <= left, "free_left": left < right,
            "left_busy": left, "right_busy": right}


# ---------------------------------------------------------------- CLI stages
def _cli():
    """Run analysis in separate processes so ASR and OpenCV never share RAM."""
    import argparse
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["video", "asr", "full"])
    ap.add_argument("path")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--max-asr", type=float, default=480.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.mode == "video":
        tl = video_timeline(a.path)
        en = audio_energy(a.path) if probe(a.path)["has_audio"] else None
        res = {"timeline": tl, "shots": shots(tl),
               "moments": moments(tl, en), "energy": en,
               "zones": text_zones(a.path)}
        json.dump(res, open(a.out, "w"))
        print(f"shots={len(res['shots'])} moments={len(res['moments'])}")
    elif a.mode == "asr":
        sp = None
        if probe(a.path)["has_audio"]:
            wav = a.path
            dur = probe(a.path)["duration"]
            if a.max_asr and dur > a.max_asr:
                cut = os.path.join(CACHE, "asr_cut.wav")
                run([FFMPEG, "-v", "error", "-t", str(a.max_asr), "-i", a.path,
                     "-vn", "-ac", "1", "-ar", "16000", cut, "-y"], check=True)
                wav = cut
            sp = speech(wav, lang=a.lang, model=a.model)
        json.dump({"speech": sp}, open(a.out, "w"))
        print("asr:", "ok" if sp else "none")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ("video", "asr", "full"):
        _cli()


def rounded_mask(path, w=1080, h=1920, box_w=1010, box_h=1230, box_y=330, radius=40):
    """Write a soft rounded-rectangle alpha mask PNG (white = visible)."""
    import cv2
    import numpy as _np
    m = _np.zeros((h, w), dtype=_np.uint8)
    x0 = (w - box_w) // 2
    y0 = box_y
    r = radius
    cv2.rectangle(m, (x0 + r, y0), (x0 + box_w - r, y0 + box_h), 255, -1)
    cv2.rectangle(m, (x0, y0 + r), (x0 + box_w, y0 + box_h - r), 255, -1)
    for cx, cy in ((x0 + r, y0 + r), (x0 + box_w - r, y0 + r),
                   (x0 + r, y0 + box_h - r), (x0 + box_w - r, y0 + box_h - r)):
        cv2.circle(m, (cx, cy), r, 255, -1)
    cv2.imwrite(path, m)
    return {"path": path, "w": w, "h": h, "box_w": box_w, "box_h": box_h,
            "box_y": box_y, "radius": radius}
