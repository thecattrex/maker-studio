"""t1.py — TYPE 1 engine: ek continuous movie scene, no narration.

    python3 t1.py build projects/<name>    # plan.json se render
    python3 t1.py check projects/<name>    # QC

Type 1 rules (SPEC se):
  - EK continuous scene, uncut. Beech me montage/cut nahi.
  - Hook = pehle 4-5 s me scene ka peak, phir scene apne start se.
  - Narration nahi. Movie ka apna Hindi dub audio (jo source me hai).
  - Text: band header (1-2 line, accent word) + action captions + impact words.
  - Background music NAHI (Type 2 ka selected C2 bed yahan mix nahi hota).
"""
import json, os, subprocess, sys, time

STUDIO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, STUDIO)

FFMPEG = os.environ.get("FFMPEG") or ("/tmp/vidtools/ffmpeg"
                                      if os.path.exists("/tmp/vidtools/ffmpeg") else "ffmpeg")


def _load(pdir):
    with open(os.path.join(pdir, "plan.json")) as f:
        return json.load(f)


def cmd_build(pdir, name=None):
    import render, textkit
    from render import Segment, Timeline

    p = _load(pdir)
    src = p["source"]
    if not os.path.exists(src):
        sys.exit(f"source nahi mila: {src}")

    W, H = p.get("size", [1080, 1920])
    sc = p["scene"]
    hk = p.get("hook") or {}
    hdr = p.get("header") or {}

    # 9:10 content band (Type 1 reference 720x800 = 9:10 ka hisaab):
    #   upar/neeche black 360px  |  white header band  |  square video
    top_black = int(p.get("band", 360))
    bot_black = int(p.get("bottom_band", 360))
    video_y = top_black
    video_h = (H - top_black - bot_black)

    tl = Timeline(name="t1", size=(W, H))
    tl.look = p.get("look", "film")
    tl.frame = (0, video_y, W, video_h)

    kw = dict(fit=p.get("fit", "crop"), focus=tuple(p.get("focus", (0.5, 0.45))),
              zoom=1.0, mute=False, grade=bool(p.get("grade", True)),
              bright=float(p.get("bright", 0.0)))

    if hk.get("dur"):
        tl.add(Segment(src=src, ss=float(hk["ss"]), dur=float(hk["dur"]), **kw))
        off = float(hk["dur"])
    else:
        off = 0.0
    tl.add(Segment(src=src, ss=float(sc["ss"]), dur=float(sc["dur"]), **kw))
    total = tl.duration()

    ov = tl.overlay
    if hdr and hdr.get("line1"):
        for key in ("line1", "line2"):
            txt = hdr.get(key)
            if not txt:
                continue
            ov.add(0.0, total, "Title",
                   "{\\an5\\pos(%d,%d)\\fs%d\\fsp2\\bord0\\shad0\\c%s}%s"
                   % (W // 2, int(hdr.get(key + "_y")),
                      int(hdr.get(key + "_size")),
                      hdr.get(key + "_color", "&H00FFFFFF&"),
                      textkit.esc(txt)))

    # ---- CAPTIONS -----------------------------------------------------
    # Priority 1: `cap_words` = [[["WORD", s, e], ...], ...]  (Groq word timings)
    #             -> karaoke: pura sentence + bola ja raha word highlight
    # Priority 2: `cap_chunks` = [{"text","t0","t1"}] -> purana word build
    cs = p.get("cap_style", {})
    cap_n = 0
    cw = p.get("cap_words")
    if cw:
        groups = [[(w[0], float(w[1]) + off, float(w[2]) + off) for w in sent]
                  for sent in cw]
        n = ov.word_caps_kara(groups,
                              y=int(cs.get("y", 1260)),
                              size=int(cs.get("size", 60)),
                              font=cs.get("font", "Inter Black"),
                              fsp=float(cs.get("fsp", -1.5)),
                              bord=int(cs.get("bord", 4)),
                              shad=int(cs.get("shad", 3)),
                              max_line_chars=int(cs.get("line_chars", 26)),
                              lead=float(cs.get("lead", 0.25)),
                              tail=float(cs.get("tail", 0.45)),
                              scale=int(cs.get("scale", 122)))
        print(f"captions {n} events (karaoke)")
        cap_n = n
    else:
        chunks = []
        for c in p.get("cap_chunks", []):
            words = c["text"].split()
            t0, t1 = float(c["t0"]), float(c["t1"])
            step = (t1 - t0) / max(1, len(words))
            chunks.append([(w, t0 + i * step, t0 + (i + 1) * step)
                           for i, w in enumerate(words)])
        if chunks:
            n = ov.word_caps(chunks,
                             y=int(cs.get("y", 1330)),
                             size=int(cs.get("size", 58)),
                             max_line_chars=int(cs.get("line_chars", 24)),
                             max_words=int(cs.get("words", 4)),
                             hold=float(cs.get("hold", 0.4)))
            print(f"captions {n} events (legacy)")
            cap_n = n
    for im in p.get("impacts", []):
        ov.impact(max(0.0, float(im["t"]) + off), float(im.get("dur", 2.4)),
                  im["text"], y=int(im.get("y", 900)),
                  size=int(im.get("size", 76)), color=im.get("color"),
                  glow=False, scale_pop=False)

    # Type 1: koi music nahi. Bas clip ki apni audio.
    tl.original_vol = float(p.get("clip_vol", 1.0))
    tl.master_gain_db = float(p.get("master_gain_db", 0.0))

    import templates
    os.makedirs(os.path.join(pdir, "out"), exist_ok=True)
    templates.save_overlay(tl, os.path.join(pdir, "subs.ass"))
    out = os.path.join(pdir, "out",
                       f"{name or p.get('name', 't1')}_{time.strftime('%m%d-%H%M')}.mp4")
    print(f"content y{video_y}..{video_y + video_h} ({W}x{video_h})  "
          f"scene {sc['ss']}+{sc['dur']}s  "
          f"hook {(str(hk.get('ss')) + '+' + str(hk.get('dur')) + 's') if hk.get('dur') else 'NONE'}  "
          f"total {total:.2f}s  caps {cap_n}  look {tl.look}  music NONE")
    tl.build(out, crf=int(p.get("crf", 23)))
    print("out:", out)
    return out


def cmd_check(pdir):
    import glob
    import numpy as np
    outs = sorted(glob.glob(os.path.join(pdir, "out", "*.mp4")))
    if not outs:
        sys.exit("koi render nahi")
    F = outs[-1]
    r = subprocess.run([FFMPEG, "-v", "error", "-i", F, "-vn", "-ac", "1", "-ar", "44100",
                        "-f", "s16le", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768
    print(f"{os.path.basename(F)}  {len(a) / 44100:.2f}s")
    print(f"  peak {np.abs(a).max():.3f}  clipped {int((np.abs(a) > 0.99).sum())}  "
          f"rms {20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9):.1f} dB")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return
    cmd, pdir = argv[1], argv[2].rstrip("/")
    if cmd == "build":
        cmd_build(pdir, argv[3] if len(argv) > 3 else None)
    elif cmd == "check":
        cmd_check(pdir)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
