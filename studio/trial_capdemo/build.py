"""Caption style demo — blank black page, 10s.
Reference: HekAHosJBOE (blur font effect) — blur 30 -> 0 over 7 frames + opacity 0->100.
Font: Inter Bold (Helvetica ka closest). Type 3 se thoda bada.
Sentence colour: ek white, dusra yellow.
"""
import os, subprocess

W, H = 1080, 1920
FPS = 30
FONT = "Inter"          # \fn se exact naam
FONTSDIR = "/home/user/assets/fonts"
OUT = "/home/user/studio/trial_capdemo"

WHITE = "&H00FFFFFF&"
YELLOW = "&H0000D7FF&"

SIZE = 72               # Type 3 = 58 -> thoda bada
BLUR = 30               # reference ka value
KF = 7                  # 7 frames
T_IN = KF / FPS         # 0.233s

SENTS = [
    ("YEH CAPTION KA STYLE HAI", WHITE,  0.55, 3.00),
    ("BLUR SE SHARP AATA HAI",   YELLOW, 3.05, 5.50),
    ("COLOUR HAR SENTENCE MEIN", WHITE,  5.55, 8.00),
    ("BADALTA REHTA HAI",        YELLOW, 8.05, 9.70),
]

def esc(t):
    return (t.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
             .replace("\n", "\\N"))

def build_ass(path):
    L = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {W}",
        f"PlayResY: {H}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
        "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Cap,{FONT},{SIZE},{WHITE},&H000000FF,&H00000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,0,0,5,60,60,60,1",
        "",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]

    def ts(x):
        h = int(x // 3600); m = int((x % 3600) // 60); s = x % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    for text, colour, t0, t1 in SENTS:
        tin = T_IN
        tout = T_IN
        # BLUR-IN: dhundhla + transparent -> saaf + solid  (reference: 30 -> 0, 0 -> 100)
        # phir FADE-OUT: keyframes reverse
        tags = (
            f"\\an5\\pos({W//2},{H//2})\\fn{FONT}\\fs{SIZE}\\b1"
            f"\\c{colour}"
            f"\\blur{BLUR}\\alpha&HFF&"
            f"\\t(0,{int(tin*1000)},\\blur0\\alpha&H00&)"
            f"\\t({int((t1-t0-tout)*1000)},{int((t1-t0)*1000)},"
            f"\\blur{BLUR}\\alpha&HFF&)"
        )
        L.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{{{tags}}}{esc(text)}")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"  ass: {len(SENTS)} sentences")

def main():
    ass = os.path.join(OUT, "demo.ass")
    build_ass(ass)
    out = os.path.join(OUT, "capdemo.mp4")
    vf = f"ass={ass}:fontsdir={FONTSDIR}"
    cmd = ["/tmp/vidtools/ffmpeg", "-v", "error", "-y",
           "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d=10",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-vf", vf, "-t", "10",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-shortest", out]
    print("  rendering...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1200:])
    print("  out:", out)

if __name__ == "__main__":
    main()
