"""Karaoke-style caption demo — blank black page.
Full sentence visible; jo word bola ja raha hai wo yellow + bada.
"""
import os, subprocess

W, H = 1080, 1920
FONT = "Inter Black"
FS   = 60
FSP  = -1.5          # letters close
BORD, SHAD = 4, 3
Y    = 1260
WHITE  = r"\c&H00FFFFFF&"
YELLOW = r"\c&H0000D7FF&"
BLACK  = r"\3c&H000000&\4c&H000000&"

# (text, total_start, total_end) — words baant ke timing
SENTS = [
    ("MAJAK MEIN POLICE WALE KO MAARNE KE LIYE", 0.30, 4.60),
    ("TUMHARE JAISA DHOONDHEGA",                 5.20, 8.20),
    ("AUR KYA CHAHIYE TEREKO",                   8.90, 11.60),
]

def split_times(words, t0, t1):
    """har word ko char-length ke hisaab se time do"""
    tot = sum(len(w) for w in words)
    out, t = [], t0
    for w in words:
        d = (t1 - t0) * len(w) / tot
        out.append((w, t, t + d))
        t += d
    return out

def hms(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def build_ass(path):
    L = []
    L.append("[Script Info]")
    L.append("ScriptType: v4.00+")
    L.append(f"PlayResX: {W}")
    L.append(f"PlayResY: {H}")
    L.append("WrapStyle: 0")
    L.append("ScaledBorderAndShadow: yes")
    L.append("")
    L.append("[V4+ Styles]")
    L.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
             "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
             "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
             "Alignment, MarginL, MarginR, MarginV, Encoding")
    L.append(f"Style: K,{FONT},{FS},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
             f"0,0,0,0,100,100,{FSP},0,1,{BORD},{SHAD},2,62,62,0,1")
    L.append("")
    L.append("[Events]")
    L.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
             "MarginV, Effect, Text")

    events = 0
    for text, t0, t1 in SENTS:
        words = text.split()
        tw = split_times(words, t0, t1)
        n = len(tw)
        for i in range(n):
            start = tw[0][1] - 0.30 if i == 0 else tw[i][1]
            end   = tw[i + 1][1] if i + 1 < n else tw[-1][2] + 0.60
            if i == 0:
                # poora sentence blur se andar aata hai
                head = (rf"{{\an2\pos({W//2},{Y}){BLACK}"
                        rf"\blur26\alpha&HFF&\t(0,300,\blur0\alpha&H00&)")
            else:
                head = rf"{{\an2\pos({W//2},{Y}){BLACK}}}"
            parts = []
            for j, (w, a, b) in enumerate(tw):
                if j == i:
                    parts.append(rf"{{\c&H0000D7FF&\fscy122}}{w}{{\r{WHITE}}}")
                else:
                    parts.append(w)
            body = " ".join(parts)
            txt = f"{head}{body}" if i == 0 else f"{head}{body}"
            L.append(f"Dialogue: 0,{hms(start)},{hms(end)},K,,0,0,0,,{txt}")
            events += 1
    open(path, "w").write("\n".join(L))
    return events

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ass = os.path.join(here, "kara.ass")
    n = build_ass(ass)
    out = os.path.join(here, "kara_demo.mp4")
    cmd = ["/tmp/vidtools/ffmpeg", "-y", "-v", "error",
           "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d=12:r=30",
           "-vf", f"ass={ass}:fontsdir=/home/user/assets/fonts",
           "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True)
    print(f"events {n} -> {out}")
