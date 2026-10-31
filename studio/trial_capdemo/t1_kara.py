"""Type 1 + karaoke captions (full sentence, bola ja raha word yellow).

Word timing = Groq whisper-large-v3, Devanagari prompt ke saath (1:1 word map).
"""
import os, subprocess, sys
sys.path.insert(0, "/home/user/studio")
import json, textkit, templates
from render import Segment, Timeline

W, H = 1080, 1920
BAND = 360
SRC = "/home/user/media/kgf_source.mp4"
PROJ = "/home/user/studio/projects/t1_kgf"
OUT = os.path.join(PROJ, "out", "kgf_kara.mp4")

SCENE = (127.0, 55.0)
HOOK = (168.4, 4.6)
OFF = HOOK[1]                       # scene clip-me +4.6 s

# (word, start, end) — clip-relative, Groq se
SENTS = [
    [("SAB,",0.00,0.70),("WO",0.70,0.78),("MERA",0.78,0.98),
     ("LADKA",0.98,1.20),("HAI",1.20,1.40)],

    [("ANDHERE",1.34,2.30),("MEIN",2.30,2.40),("BAITHA",2.40,2.64),
     ("THA",2.64,2.78),("USKO",2.78,3.14)],

    [("MAJAK",3.10,3.76),("MEIN",3.76,3.84),("POLICE",3.84,4.06),
     ("WALE",4.06,4.24),("KO",4.24,4.34),("MAARNE",4.34,4.62),
     ("KE",4.62,4.72),("LIYE",4.72,5.06)],

    [("LEKIN",4.78,5.34),("WO",5.34,5.46),("KUCH",5.46,5.62),
     ("NAHI",5.62,5.72),("KARTA",5.72,6.16)],

    [("MAINE",6.12,7.00),("POLICE",7.00,7.32),("SE",7.32,7.42),
     ("USKO",7.42,7.62),("CHHUDA",7.62,7.98),("DIYA",7.98,8.24),
     ("HAI",8.24,8.48)],

    [("OE,",13.18,13.90),("KIDHAR",13.90,14.06),("GAYA",14.06,14.24),
     ("THA",14.24,14.38),("MAIN",14.38,14.48),("TU",14.48,14.70)],

    [("NAAM",17.46,17.92),("KAMANE",17.92,18.40),("GAYA",18.40,18.74),
     ("THA",18.74,19.52)],

    [("US",20.00,20.34),("POLICE",20.34,20.58),("WALE",20.58,20.74),
     ("KO",20.74,20.84),("KYUN",20.84,20.92),("MAARA",20.92,21.12),
     ("RE",21.12,21.44)],

    [("KISI",22.96,23.34),("KO",23.34,23.48),("MAARA",23.48,23.92),
     ("TO",23.92,24.08),("POLICE",24.08,25.68),("DHOONDHEGA",25.68,26.56)],

    [("POLICE",27.46,27.94),("WALE",27.94,28.28),("KO",28.28,28.42),
     ("KOI",28.42,28.52),("MAARA",28.52,28.90),("TO",28.90,29.18),
     ("TUMHARE",29.18,31.94),("JAISA",31.94,32.10),("DHOONDHEGA",32.10,32.95)],
]

FS, FSP, BORD, SHAD, Y = 60, -1.5, 4, 3, 1260
MIN_W = 0.16
LEAD  = 0.28        # sentence 0.28 s pehle dikhta hai
TAIL  = 0.45



MAXC = 26


def wrap_lines(words, maxc):
    """2 line me balanced break — dono line lagbhag barabar."""
    if not words:
        return [0]
    total = len(" ".join(words))
    if total <= maxc:
        return [len(words)]
    best, best_score = None, 1e9
    for k in range(1, len(words)):
        a = " ".join(words[:k]); b = " ".join(words[k:])
        score = max(len(a), len(b))
        if score > maxc:
            score += (score - maxc) * 4      # overflow pe bhaari penalty
        if score < best_score:
            best, best_score = k, score
    return [best, len(words) - best]


def hms(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_groups():
    """word times ko sanitize karo: min duration, overlap hatao"""
    out = []
    for sent in SENTS:
        g = [[w, s + OFF, e + OFF] for w, s, e in sent]
        for i in range(len(g)):
            if i + 1 < len(g) and g[i][2] > g[i + 1][1]:
                g[i][2] = g[i + 1][1]
        out.append(g)
    return out


def main():
    tl = Timeline(name="t1kara", size=(W, H))
    tl.look = "ai"
    kw = dict(fit="crop", focus=(0.5, 0.45), zoom=1.0, mute=False,
              grade=True, bright=0.07)
    tl.add(Segment(src=SRC, ss=HOOK[0], dur=HOOK[1], **kw))
    tl.add(Segment(src=SRC, ss=SCENE[0], dur=SCENE[1], **kw))
    tl.frame = (0, BAND, W, 1200)
    total = tl.duration()

    ov = tl.overlay
    ov.add(0.0, total, "Title",
           "{\\an5\\pos(540,150)\\fs230\\fsp2\\bord0\\shad0\\c&H002222D6&}KGF")
    ov.add(0.0, total, "Title",
           "{\\an5\\pos(540,282)\\fs128\\fsp2\\bord0\\shad0\\c&H00FFFFFF&}CHAPTER 1")

    groups = build_groups()

    # sentence overlap hatao: agla sentence pichle ke khatam hone ke baad hi
    cursor = 0.0
    for g in groups:
        if g[0][1] < cursor:
            d = cursor - g[0][1]
            for w in g:
                w[1] += d
                w[2] += d
        cursor = g[-1][2] + 0.06

    # har sentence ka display window — koi overlap nahi, last word pura dikhe
    wins = []
    for k, g in enumerate(groups):
        st = g[0][1] - LEAD
        if k:
            st = max(st, groups[k - 1][-1][2] + 0.02)
        en = g[-1][2] + TAIL
        if k + 1 < len(groups):
            en = min(en, groups[k + 1][0][1] - LEAD - 0.02)
        en = max(en, g[-1][2])
        wins.append((st, en))

    caps = []                                  # (start, end, text)
    for g, (t_start, t_end) in zip(groups, wins):
        n = len(g)
        lines = wrap_lines([w for w, _, _ in g], MAXC)
        for i in range(n):
            a = t_start if i == 0 else max(g[i][1], t_start)
            b = min(g[i + 1][1], t_end) if i + 1 < n else t_end
            out, k = [], 0
            for ln in lines:
                buf = []
                for _ in range(ln):
                    w = g[k][0]
                    if k == i:
                        buf.append(r"{\c&H0000D7FF&\fscy122}" + w +
                                   r"{\c&H00FFFFFF&\fscy100}")
                    else:
                        buf.append(w)
                    k += 1
                out.append(" ".join(buf))
            head = (rf"{{\an2\pos(540,{Y})\fn Inter Black\fs{FS}"
                    rf"\bord{BORD}\shad{SHAD}\3c&H000000&\4c&H000000&\fsp{FSP}")
            if i == 0:
                head += r"\blur24\alpha&HFF&\t(0,260,\blur0\alpha&H00&)"
            head += "}"
            caps.append([a, b, head + r"\N".join(out)])

    # kooch bhi overlap na ho: har event agle ke start pe khatam
    caps.sort(key=lambda c: c[0])
    for i in range(len(caps) - 1):
        caps[i][1] = min(caps[i][1], caps[i + 1][0])
    ev = 0
    for a, b, txt in caps:
        if b - a < 0.03:                     # zero-length event na bane
            b = a + 0.03
        ov.add(a, b, "Cap", txt)
        ev += 1
    print(f"  caption events {ev}")
    for w in ov.warnings:
        print("  [!]", w)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    templates.save_overlay(tl, os.path.join(PROJ, "subs_kara.ass"))
    tl.master_gain_db = 0.0
    print("  rendering...")
    tl.build(OUT, crf=23)
    print("  out:", OUT)


if __name__ == "__main__":
    main()
