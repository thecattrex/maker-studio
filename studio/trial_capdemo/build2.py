"""Caption demo v2 — word-by-word blur-in.
  - size 66 (v1 tha 72) -> thoda chhota
  - Inter ExtraBold -> zyada bold
  - har WORD alag blur-in hota hai, sentence ek saath nahi
  - purana word sharp + white rehta hai, naya word yellow blur se sharp aata hai
"""
import os, subprocess

W, H = 1080, 1920
FPS = 30
FONT = "Inter ExtraBold"
FONTSDIR = "/home/user/assets/fonts"
OUT = "/home/user/studio/trial_capdemo"

WHITE = "&H00FFFFFF&"
YELLOW = "&H0000D7FF&"

SIZE = 66
BLUR = 30
KF = 7
T_IN = KF / FPS

SENTS = [
    ("YEH CAPTION KA STYLE HAI",  0.50, 3.00),
    ("HAR WORD ALAG AATA HAI",    3.05, 5.50),
    ("BLUR SE SHARP HOTA HAI",    5.55, 8.00),
    ("SIZE THODA CHHOTA HAI",     8.05, 9.80),
]

def esc(t):
    return (t.replace("\\", "\\\\").replace("{", "(").replace("}", ")"))

def build_ass(path):
    L = [
        "[Script Info]", "ScriptType: v4.00+",
        f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
        "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Cap,{FONT},{SIZE},{WHITE},&H000000FF,&H00000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,0,0,5,60,60,60,1",
        "", "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]

    def ts(x):
        h=int(x//3600); m=int((x%3600)//60); s=x%60
        return f"{h}:{m:02d}:{s:05.2f}"

    total_events = 0
    for text, t0, t1 in SENTS:
        words = text.split()
        dur = t1 - t0
        step = dur / (len(words) + 1)
        # ek sentence ka colour: alternate white / yellow per sentence
        idx = SENTS.index((text, t0, t1))
        base_col = WHITE if idx % 2 == 0 else YELLOW
        for i, w in enumerate(words):
            ws = t0 + i * step
            we = t1 - 0.10 if i == len(words)-1 else t0 + (i+1) * step + 0.001
            # purane words: sharp, sentence ka base colour
            prev = " ".join("{\\c" + base_col + "}" + esc(x) for x in words[:i])
            # naya word: yellow/white accent + blur-in
            new_col = YELLOW if base_col == WHITE else WHITE
            new = (f"{{\\c{new_col}\\blur{BLUR}\\alpha&HFF&"
                   f"\\t(0,{int(T_IN*1000)},\\blur0\\alpha&H00&)}}"
                   + esc(w))
            txt = (prev + " " if prev else "") + new
            tags = f"\\an5\\pos({W//2},{H//2})\\fn{FONT}\\fs{SIZE}"
            L.append(f"Dialogue: 0,{ts(ws)},{ts(we)},Cap,,0,0,0,,{{{tags}}}{txt}")
            total_events += 1
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"  ass: {total_events} word events")

def main():
    ass = os.path.join(OUT, "demo2.ass")
    build_ass(ass)
    out = os.path.join(OUT, "capdemo_v2.mp4")
    cmd = ["/tmp/vidtools/ffmpeg", "-v", "error", "-y",
           "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d=10",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-vf", f"ass={ass}:fontsdir={FONTSDIR}", "-t", "10",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-shortest", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1500:])
    print("  out:", out)

if __name__ == "__main__":
    main()
