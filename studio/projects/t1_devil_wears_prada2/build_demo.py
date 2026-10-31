import os, sys, subprocess
import cv2
import numpy as np

STUDIO = "/home/user/studio"
sys.path.insert(0, STUDIO)
import textkit

FFMPEG = "/home/user/bin/ffmpeg"
PROJ = "/home/user/studio/projects/t1_devil_wears_prada2"
SRC = "/tmp/t1_cands/dwp2.mp4"
RAW_V = "/tmp/t1_cands/dwp2_motion_band_v2.mp4"
ASS_PATH = os.path.join(PROJ, "subs.ass")
OUT_PATH = "/home/user/studio/samples/type1_devil_wears_prada2_demo.mp4"

W, H = 1080, 1920
TOP_BAND, BOT_BAND = 360, 360
BAND_W, BAND_H = 1080, 1200  # 9:10 central band (y = 360..1560)

START_F = 878   # 36.620s
END_F   = 1452  # 60.560s -> 574 frames = 23.94s @ 23.976fps
FPS_NUM, FPS_DEN = 24000, 1001
FPS = FPS_NUM / FPS_DEN
T0_SRC = START_F / FPS

# Exact hard-cut shot table [f_start, f_end, fx0, fx1, fy0, fy1, z0, z1]
SHOTS = [
    # Shot 0: Amari + Andy as speakerphone answers ("Hi, good morning, Miranda")
    (878,  910,  0.46, 0.48, 0.48, 0.48, 1.00, 1.035),
    # Shot 1: Miranda medium close-up firing Ashley on speakerphone
    (910,  1071, 0.46, 0.47, 0.46, 0.44, 1.00, 1.068),
    # Shot 2: Amari + Andy jaw-drop reaction (fx=0.61->0.64 keeps BOTH faces generously framed!)
    (1071, 1156, 0.61, 0.64, 0.46, 0.45, 1.00, 1.042),
    # Shot 3: Miranda cold stare ("Happy? You just cost Cornell's summa cum laude her job.")
    (1156, 1301, 0.49, 0.49, 0.47, 0.45, 1.015, 1.072),
    # Shot 4: Wide shot — Miranda & Nigel walking across office
    (1301, 1362, 0.32, 0.38, 0.48, 0.48, 1.02, 1.045),
    # Shot 5: Miranda walks past stunned Andy & Amari out glass door
    (1362, 1452, 0.50, 0.51, 0.47, 0.47, 1.00, 1.040),
]

def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)

def shot_params(f_idx):
    for a, b, fx0, fx1, fy0, fy1, z0, z1 in SHOTS:
        if a <= f_idx < b:
            u = smoothstep((f_idx - a) / max(1, b - a - 1))
            fx = fx0 + (fx1 - fx0) * u
            fy = fy0 + (fy1 - fy0) * u
            z  = z0  + (z1  - z0)  * u
            return fx, fy, z
    return 0.5, 0.47, 1.0

def render_motion_video():
    cap = cv2.VideoCapture(SRC)
    sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, START_F)

    cmd = [
        FFMPEG, "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", f"{FPS_NUM}/{FPS_DEN}", "-i", "-",
        "-vf", "eq=contrast=1.08:saturation=1.12:gamma=0.98,unsharp=5:5:0.45:5:5:0.0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
        RAW_V
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    base_scale = max(BAND_W / sw, BAND_H / sh)

    for f_idx in range(START_F, END_F):
        ok, frame = cap.read()
        if not ok:
            break
        fx, fy, z = shot_params(f_idx)
        sc = base_scale * z
        crop_w = BAND_W / sc
        crop_h = BAND_H / sc
        x0 = max(0.0, min(sw - crop_w, (sw - crop_w) * fx))
        y0 = max(0.0, min(sh - crop_h, (sh - crop_h) * fy))

        M = np.array([[sc, 0.0, -x0 * sc], [0.0, sc, -y0 * sc]], dtype=np.float32)
        band_img = cv2.warpAffine(frame, M, (BAND_W, BAND_H), flags=cv2.INTER_LANCZOS4,
                                  borderMode=cv2.BORDER_REPLICATE)
        canvas.fill(0)
        canvas[TOP_BAND:TOP_BAND + BAND_H, 0:W] = band_img
        proc.stdin.write(canvas.tobytes())

    proc.stdin.close()
    rc = proc.wait()
    cap.release()
    if rc != 0:
        raise RuntimeError(f"Motion encode failed: {rc}")
    print("Rendered motion band video v2 ->", RAW_V)

def build_ass():
    total = (END_F - START_F) / FPS
    ov = textkit.Overlay(playres=(W, H))

    # 1. Persistent 2-line Top Header in top black band (y=0..360) with smooth slide+blur entrance
    ov.add(0.0, total, "Title",
           r"{\an5\fnAnton\fs94\fsp2\bord0\shad0\c&H00FFFFFF&"
           r"\move(540,164,540,134,0,260)\blur16\alpha&HFF&\t(0,260,\blur0\alpha&H00&)}"
           "HIRED LAST NIGHT...", layer=5)
    ov.add(0.08, total, "Title",
           r"{\an5\fnAnton\fs126\fsp2\bord0\shad0"
           r"\move(540,284,540,254,0,280)\blur16\alpha&HFF&\t(0,280,\blur0\alpha&H00&)}"
           r"{\c&H002E2EF7&}FIRED {\c&H00FFFFFF&}ON SPEAKER", layer=5)

    def R(t):
        return round(max(0.0, t - T0_SRC), 3)

    # 2. Verbatim English word-level karaoke groups at y=1405 (well inside the video band, never straddling border!)
    groups = [
        [("HI,", R(36.78), R(37.24)), ("GOOD", R(37.30), R(37.46)),
         ("MORNING,", R(37.46), R(37.66)), ("MIRANDA.", R(37.66), R(37.92))],

        [("YES,", R(38.58), R(38.80)), ("ASHLEY,", R(38.86), R(39.32)),
         ("FLAG", R(39.42), R(39.56)), ("ON", R(39.56), R(39.68)),
         ("THE", R(39.68), R(39.80)), ("PLAY.", R(39.80), R(40.06))],

        [("WE", R(40.18), R(40.30)), ("DON'T", R(40.30), R(40.46)),
         ("NEED", R(40.46), R(40.64)), ("YOU", R(40.64), R(40.78)),
         ("THIS", R(40.78), R(40.94)), ("MORNING...", R(40.94), R(41.30))],

        [("SO", R(43.08), R(43.24)), ("PACK", R(43.24), R(43.52)),
         ("UP", R(43.52), R(43.68)), ("YOUR", R(43.68), R(43.84)),
         ("THINGS,", R(43.84), R(44.32))],

        [("AND", R(44.80), R(45.08)), ("HR", R(45.08), R(45.88)),
         ("WILL", R(45.88), R(46.10)), ("BE", R(46.10), R(46.24)),
         ("IN", R(46.24), R(46.38)), ("TO", R(46.38), R(46.52)),
         ("SEE", R(46.52), R(46.72)), ("YOU", R(46.72), R(46.90)),
         ("SHORTLY.", R(46.90), R(47.25))],

        [("YOU", R(50.26), R(50.42)), ("JUST", R(50.42), R(50.62)),
         ("COST", R(50.62), R(51.02)), ("CORNELL'S", R(51.02), R(51.96)),
         ("SUMMA", R(51.96), R(52.24)), ("CUM", R(52.24), R(52.42)),
         ("LAUDE", R(52.42), R(52.72)), ("HER", R(52.72), R(52.90)),
         ("JOB.", R(52.90), R(53.30))],

        [("FIRST", R(54.58), R(54.84)), ("IN", R(54.84), R(55.08)),
         ("HER", R(55.08), R(55.22)), ("FAMILY", R(55.22), R(55.56)),
         ("TO", R(55.56), R(55.74)), ("GO", R(55.74), R(55.90)),
         ("TO", R(55.90), R(56.08)), ("COLLEGE,", R(56.08), R(56.38)),
         ("I", R(56.38), R(56.54)), ("BELIEVE.", R(56.54), R(56.92))],

        [("ANYWAY,", R(58.02), R(58.58)), ("COME", R(58.90), R(59.06)),
         ("ALONG.", R(59.06), R(59.42)), ("COME", R(59.68), R(59.90)),
         ("ON.", R(59.90), R(60.20))],
    ]

    n = ov.word_caps_kara(
        groups,
        y=1405,
        size=64,
        font="Archivo Black",
        fsp=-0.5,
        bord=8,
        shad=4,
        max_line_chars=19,
        lead=0.12,
        tail=0.26,
        blur=18,
        kf=5,
        scale=118,
        an=2
    )
    print("Karaoke caption events:", n)

    # 3. Cold punch phrase "OR EVER." (41.40..42.75s) — red accent impact in exact speech window!
    ov.add(R(41.40), R(42.80), "Impact",
           r"{\an2\pos(540,1405)\fnAnton\fs98\fsp3\c&H002E2EF7&"
           r"\bord9\3c&H000000&\3a&H00&\shad4\4c&H000000&\4a&H60&"
           r"\fscx82\fscy82\blur16\alpha&HFF&"
           r"\t(0,120,\fscx107\fscy107\blur0\alpha&H00&)"
           r"\t(120,210,\fscx100\fscy100)}"
           "OR EVER.", layer=6)

    # 4. Clean Action Caption in the exact silent beat (47.42..48.44s) — zero overlap!
    ov.add(R(47.42), R(48.44), "ActionCap",
           r"{\an2\pos(540,1400)\fnBarlow Condensed\b1\fs58\fsp3\c&H00E8E8E8&"
           r"\bord8\3c&H000000&\3a&H00&\shad3\4c&H000000&\4a&H70&"
           r"\blur14\alpha&HFF&\t(0,140,\blur0\alpha&H00&)}"
           "(HANGS UP COLDLY)", layer=4)

    # 5. Miranda's single-word dagger at 48.55s ("HAPPY?")
    ov.add(R(48.54), R(49.60), "Impact",
           r"{\an2\pos(540,1405)\fnAnton\fs104\fsp3\c&H0000D7FF&"
           r"\bord9\3c&H000000&\3a&H00&\shad4\4c&H000000&\4a&H60&"
           r"\fscx78\fscy78\blur16\alpha&HFF&"
           r"\t(0,120,\fscx108\fscy108\blur0\alpha&H00&)"
           r"\t(120,210,\fscx100\fscy100)}"
           "HAPPY?", layer=6)

    # 6. Subtle movie tag in bottom black band
    ov.add(0.2, total, "Small",
           r"{\an5\pos(540,1648)\fnBebas Neue\fs46\fsp6\c&H00969696&\bord0\shad0"
           r"\alpha&HFF&\t(0,350,\alpha&H20&)}"
           "THE DEVIL WEARS PRADA 2", layer=2)

    ov.write(ASS_PATH)
    print("Wrote ASS v2 ->", ASS_PATH)

if __name__ == "__main__":
    render_motion_video()
    build_ass()
