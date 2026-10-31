"""Type 1 + word-by-word blur captions. Trial me — asli t1.py chhua nahi."""
import os, subprocess, sys
sys.path.insert(0, "/home/user/studio")
import json, textkit, templates
from render import Segment, Timeline

W, H = 1080, 1920
BAND = 360
SRC = "/home/user/media/kgf_source.mp4"
PROJ = "/home/user/studio/projects/t1_kgf"
OUT = os.path.join(PROJ, "out", "kgf_blur.mp4")

SCENE = (127.0, 55.0)
HOOK = (168.4, 4.6)

# (sentence, start, end)  — times audio landmarks se (Groq word timing)
SENTS = [
    ("SAB, WO MERA LADKA HAI",                    0.00,  1.60),
    ("ANDHERE MEIN BAITHA THA USKO",              1.60,  3.06),
    ("MAJAK MEIN POLICE WALE KO MAARNE KE LIYE",  3.06,  5.00),
    ("LEKIN WO KUCH NAHI KARTA",                  5.00,  6.78),
    ("MAINE POLICE SE USKO CHHUDA DIYA HAI",      6.78,  8.52),
    ("AB BATAO... KYUN DAR GAYA THA MAIN",        8.52, 14.36),
    ("NAAM KAMANE GAYA THA",                     14.54, 20.34),
    ("KISI KO MAARA TO POLICE DHOONDHEGA",       20.62, 26.28),
    ("POLICE WALE KO KOI MAARA TO",              26.28, 29.14),
    ("TUMHARE JAISA DHOONDHEGA",                 29.14, 33.56),
    ("AUR KYA CHAHIYE TEREKO",                   35.00, 40.04),
]

def split_words(text, t0, t1):
    """Char-length ke hisaab se word times — lamba shabd zyada der."""
    ws = text.split()
    tr = [max(1, len(w)) for w in ws]
    tot = sum(tr)
    out, acc = [], 0
    for w, n in zip(ws, tr):
        a = t0 + (t1 - t0) * acc / tot
        acc += n
        b = t0 + (t1 - t0) * acc / tot
        out.append((w, round(a, 3), round(b, 3)))
    return out

def main():
    tl = Timeline(name="t1blur", size=(W, H))
    tl.look = "ai"
    kw = dict(fit="crop", focus=(0.5, 0.45), zoom=1.0, mute=False,
              grade=True, bright=0.07)
    tl.add(Segment(src=SRC, ss=HOOK[0], dur=HOOK[1], **kw))
    off = HOOK[1]
    tl.add(Segment(src=SRC, ss=SCENE[0], dur=SCENE[1], **kw))
    tl.frame = (0, BAND, W, 1200)
    total = tl.duration()

    ov = tl.overlay
    ov.add(0.0, total, "Title",
           "{\\an5\\pos(540,150)\\fs230\\fsp2\\bord0\\shad0\\c&H002222D6&}KGF")
    ov.add(0.0, total, "Title",
           "{\\an5\\pos(540,282)\\fs128\\fsp2\\bord0\\shad0\\c&H00FFFFFF&}CHAPTER 1")

    groups = [split_words(t, a + off, b + off) for t, a, b in SENTS]
    n = ov.word_caps_blur(groups, y=1260, size=66, max_line_chars=22,
                          max_words=4, blur=30, kf=7, bord=5, shad=3)
    print(f"  caption events {n}")
    for w in ov.warnings:
        print("  [!]", w)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    templates.save_overlay(tl, os.path.join(PROJ, "subs_blur.ass"))
    tl.master_gain_db = 0.0
    print("  rendering...")
    tl.build(OUT, crf=23)
    print("  out:", OUT)

if __name__ == "__main__":
    main()
