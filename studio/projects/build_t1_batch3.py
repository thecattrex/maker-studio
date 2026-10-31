"""build_t1_batch3.py — Builds 3 Hook-First Type-1 English Movie Shorts (20-25s).

Structure per video (per t1.py / FORMAT_MEMORY.md + user's explicit instruction):
  1. [0.0s .. hook_dur] COLD-OPEN HOOK / PUNCHLINE FIRST (fully captioned + punch motion)
  2. Smooth 4-frame cinema dip-to-black + click-free audio fade into:
  3. [hook_dur .. total] FULL CONTINUOUS UNCUT SCENE from its start -> full payoff
  4. Native 23.976fps sub-pixel Lanczos4 camera motion, verified explicit fonts,
     original English movie audio only (zero BGM), normalized to ~-15 LUFS / <= -1.5 dBFS TP.
"""
import os, sys, json, subprocess

STUDIO = "/home/user/studio"
sys.path.insert(0, STUDIO)
import textkit

FFMPEG = "/home/user/bin/ffmpeg"
SCRATCH = "/home/user/studio/_scratch"
SAMPLES = "/home/user/studio/samples"
os.makedirs(SAMPLES, exist_ok=True)

W, H = 1080, 1920
TOP_BAND, BAND_H = 360, 1200
FPS_NUM, FPS_DEN = 24000, 1001
FPS = FPS_NUM / FPS_DEN


VIDEOS = [
    # =========================================================================
    # 1. TOY STORY 5 ($1.15B #3 2026 Box Office — Tom Hanks & Tim Allen)
    # =========================================================================
    {
        "slug": "t1_toy_story_5",
        "out": os.path.join(SAMPLES, "type1_toy_story_5_hook_first.mp4"),
        "src": os.path.join(SCRATCH, "ts5_deserve.mp4"),
        "movie_tag": "TOY STORY 5",
        "hdr1": "30 YEARS OF FRIENDSHIP...",
        "hdr2_red": "RIPPED ",
        "hdr2_white": "OFF HIS BADGE",
        "grade_vf": "eq=contrast=1.07:saturation=1.10:brightness=0.02:gamma=0.96,unsharp=5:5:0.45:5:5:0.0",
        "vol_db": 10.5,
        "hook_frames": (1016, 1090),   # 42.376s .. 45.462s (3.09s)
        "scene_frames": (781, 1270),   # 32.574s .. 52.969s (20.40s) -> Total = 23.48s
        "shots": [
            (779,  866,  0.56, 0.58, 0.45, 0.45, 1.00, 1.050),
            (866,  933,  0.44, 0.46, 0.46, 0.45, 1.00, 1.055),
            (933,  1037, 0.56, 0.59, 0.44, 0.43, 1.00, 1.075),
            (1037, 1143, 0.48, 0.50, 0.46, 0.45, 1.02, 1.068),
            (1143, 1197, 0.48, 0.50, 0.45, 0.45, 1.01, 1.050),
            (1197, 1237, 0.46, 0.46, 0.46, 0.45, 1.01, 1.050),
            (1237, 1275, 0.53, 0.58, 0.48, 0.50, 1.00, 1.035),
        ],
        # Spoken dialogue groups in source timestamps (mapped automatically onto hook & scene!)
        "kara_src": [
            [("WHY?", 32.72, 32.92), ("WHY", 33.10, 33.22), ("JUST", 33.22, 33.36), ("YOU?", 33.36, 33.60)],
            [("LOOK,", 33.72, 33.90), ("I", 34.00, 34.08), ("JUST", 34.08, 34.22), ("HAVE", 34.22, 34.36),
             ("MORE", 34.36, 34.54), ("FIELD", 34.54, 34.78), ("EXPERIENCE", 34.78, 35.18),
             ("THAN", 35.18, 35.48), ("YOU.", 35.48, 35.68)],
            [("THAT", 35.72, 35.86), ("IS", 35.86, 35.98), ("ALL.", 35.98, 36.28)],
            [("YOU", 37.28, 37.50), ("DON'T", 37.50, 37.70), ("THINK", 37.70, 37.90),
             ("I", 37.90, 38.12), ("CAN", 38.12, 38.30), ("DO", 38.30, 38.52), ("IT?", 38.52, 38.70)],
            [("NO,", 38.78, 39.00), ("I", 39.10, 39.20), ("JUST", 39.20, 39.34), ("THINK", 39.34, 39.50),
             ("I", 39.50, 39.62), ("CAN", 39.62, 39.76), ("DO", 39.76, 39.90), ("IT", 39.90, 40.00),
             ("A", 40.00, 40.10), ("LITTLE", 40.10, 40.28), ("BIT...", 40.28, 40.62)],
            # 42.58..43.20 -> Impact "BETTER."
            [("YOU", 43.66, 44.06), ("DON'T", 44.06, 44.46),
             ("DESERVE", 44.46, 44.86), ("THIS!", 44.86, 45.30)],
            [("BUZZ,", 45.46, 45.64), ("COME", 45.70, 45.84), ("ON!", 45.84, 46.12)],
            [("JESSIE", 46.22, 46.46), ("PUT", 46.46, 46.76), ("ME", 46.76, 47.18),
             ("IN", 47.18, 47.40), ("CHARGE,", 47.40, 47.72)],
            [("WHICH", 47.74, 47.98), ("IS", 47.98, 48.10), ("WHY", 48.10, 48.26),
             ("YOU", 48.26, 48.44), ("SHOULD", 48.44, 48.62), ("STAY", 48.62, 48.88),
             ("HERE", 48.88, 49.22), ("AND", 49.22, 49.44), ("WATCH", 49.44, 49.68),
             ("THE", 49.68, 49.86), ("ROOM.", 49.86, 50.14)],
            [("THERE", 50.22, 50.34), ("IS", 50.34, 50.46), ("NO", 50.46, 50.64),
             ("ROOM", 50.64, 50.86), ("WITHOUT", 50.86, 51.12), ("JESSIE!", 51.12, 51.55)],
        ],
        "impacts_src": [
            (42.54, 43.24, "BETTER.", "&H0000D7FF&", 104),
            (51.94, 52.86, "BUZZ, NO!", "&H002E2EF7&", 102),
        ],
        "actions_src": [
            (40.92, 42.34, "(STARES DEAD IN HIS EYES)"),
        ],
    },

    # =========================================================================
    # 2. PROJECT HAIL MARY ($684.5M #7 2026 Box Office — Ryan Gosling)
    # =========================================================================
    {
        "slug": "t1_project_hail_mary",
        "out": os.path.join(SAMPLES, "type1_project_hail_mary_hook_first.mp4"),
        "src": os.path.join(SCRATCH, "phm_personal.mp4"),
        "movie_tag": "PROJECT HAIL MARY",
        "hdr1": "WHISPERING ABOUT HIS",
        "hdr2_red": "ALIEN ",
        "hdr2_white": "ROOMMATE",
        "grade_vf": "eq=contrast=1.08:saturation=1.12:brightness=0.015:gamma=0.97,unsharp=5:5:0.45:5:5:0.0",
        "vol_db": 10.5,
        "hook_frames": (1132, 1201),   # 47.214s .. 50.092s (2.88s — ends right on "HE'S RIGHT HERE!")
        "scene_frames": (708, 1222),   # 29.530s .. 50.968s (21.44s) -> Total = 24.32s
        "shots": [
            (708,  1095, 0.44, 0.46, 0.46, 0.45, 1.02, 1.082),
            (1095, 1160, 0.44, 0.46, 0.47, 0.47, 1.02, 1.050),
            (1160, 1225, 0.46, 0.48, 0.47, 0.47, 1.04, 1.085),
        ],
        "kara_src": [
            [("PERSONAL", 29.58, 29.94), ("SPACE", 29.94, 30.32), ("IS", 30.32, 30.90),
             ("AT", 30.90, 31.20), ("A", 31.20, 31.46), ("PREMIUM.", 31.46, 31.95)],
            [("WHO", 32.42, 32.54), ("IS", 32.54, 32.68), ("GRACE", 32.68, 32.86),
             ("TALKING", 32.86, 33.14), ("TO?", 33.14, 33.42), ("QUESTION.", 33.44, 33.85)],
            [("THERE'S", 35.20, 35.46), ("NO", 35.46, 35.60), ("WAY", 35.60, 35.74),
             ("YOU", 35.74, 35.88), ("CAN", 35.88, 36.02), ("HEAR", 36.02, 36.16),
             ("ME", 36.16, 36.30), ("RIGHT", 36.30, 36.48), ("NOW.", 36.48, 36.75)],
            [("CAN", 37.08, 37.22), ("HEAR.", 37.22, 37.48), ("WHO", 37.60, 37.72),
             ("ARE", 37.72, 37.88), ("YOU", 37.88, 38.04), ("TALKING", 38.04, 38.28), ("TO?", 38.28, 38.58)],
            [("YOU", 38.82, 38.98), ("CAN", 38.98, 39.14), ("HEAR", 39.14, 39.30), ("THIS?", 39.30, 39.60)],
            [("YES.", 39.96, 40.28), ("GRACE", 40.48, 40.64), ("SAY,", 40.64, 40.84),
             ("'YOU", 40.84, 41.02), ("CAN", 41.02, 41.18), ("HEAR", 41.18, 41.36), ("THIS.'", 41.36, 41.70)],
            [("WHAT", 42.32, 42.52), ("ABOUT", 42.52, 42.72), ("THIS?", 42.72, 43.02)],
            [("YES.", 43.18, 43.52)],
            [("OH", 43.72, 43.86), ("MY", 43.86, 44.04), ("GOD,", 44.04, 44.28),
             ("LOOK", 44.38, 44.58), ("AT", 44.58, 44.70), ("THIS.", 44.70, 44.88)],
            [("LOOK", 44.92, 45.04), ("HOW", 45.04, 45.16), ("FAR", 45.16, 45.34),
             ("AWAY", 45.34, 45.54), ("HE", 45.54, 45.66), ("IS!", 45.66, 45.90)],
            [("THAT", 47.36, 47.70), ("IS", 47.70, 47.84), ("WHERE", 47.84, 48.02),
             ("HE", 48.02, 48.16), ("IS—", 48.16, 48.44)],
            [("HELLO,", 48.58, 48.80), ("GRACE.", 48.80, 49.12)],
            # 49.24..49.98 -> Impact "HE'S RIGHT HERE!"
            [("HELLO,", 50.08, 50.28), ("GRACE", 50.32, 50.52), ("FRIEND.", 50.52, 50.85)],
        ],
        "impacts_src": [
            (49.22, 49.98, "HE'S RIGHT HERE!", "&H002E2EF7&", 96),
        ],
        "actions_src": [
            (34.05, 35.02, "(WHISPERS ACROSS THE SHIP)"),
        ],
    },

    # =========================================================================
    # 3. THE DRAMA (2026 A24 Hit — Zendaya)
    # =========================================================================
    {
        "slug": "t1_the_drama_zendaya",
        "out": os.path.join(SAMPLES, "type1_the_drama_zendaya_hook_first.mp4"),
        "src": os.path.join(SCRATCH, "drama_emma.mp4"),
        "movie_tag": "THE DRAMA",
        "hdr1": "FIRST LOVE AT 30?!",
        "hdr2_red": "ZENDAYA'S ",
        "hdr2_white": "EXCUSE",
        "grade_vf": "eq=contrast=1.08:saturation=1.12:gamma=0.97,unsharp=5:5:0.45:5:5:0.0",
        "vol_db": 11.5,
        "hook_frames": (724, 813),     # 30.197s .. 33.909s (3.71s)
        "scene_frames": (303, 813),    # 12.638s .. 33.909s (21.27s) -> Total = 24.98s
        "shots": [
            (297, 314, 0.46, 0.46, 0.45, 0.45, 1.00, 1.030),
            (314, 364, 0.48, 0.49, 0.45, 0.44, 1.00, 1.050),
            (364, 411, 0.47, 0.47, 0.45, 0.44, 1.00, 1.050),
            (411, 466, 0.48, 0.49, 0.45, 0.44, 1.00, 1.050),
            (466, 507, 0.48, 0.48, 0.45, 0.45, 1.00, 1.050),
            (507, 591, 0.47, 0.48, 0.45, 0.44, 1.00, 1.060),
            (591, 638, 0.46, 0.47, 0.45, 0.44, 1.01, 1.055),
            (638, 796, 0.49, 0.50, 0.45, 0.43, 1.00, 1.078),
            (796, 815, 0.45, 0.46, 0.45, 0.45, 1.02, 1.055),
        ],
        "kara_src": [
            [("SO", 12.64, 12.84), ("YOU'RE", 12.84, 13.06), ("SAYING", 13.06, 13.38),
             ("CHARLIE", 13.38, 13.86), ("IS", 13.86, 14.20), ("YOUR", 14.20, 14.44),
             ("FIRST...", 14.44, 15.48), ("LOVE?", 15.52, 15.90)],
            [("YEAH.", 16.26, 16.82)],
            [("YOUR", 17.06, 17.18), ("FIRST", 17.18, 17.40), ("LOVE", 17.40, 17.78),
             ("OR", 17.78, 17.94), ("YOUR", 17.94, 18.08), ("FIRST", 18.08, 18.30), ("CRUSH?", 18.30, 18.72)],
            [("BOTH,", 21.46, 21.94), ("I", 22.04, 22.22), ("THINK.", 22.22, 22.56)],
            [("WHAT?!", 23.62, 23.98), ("IS", 24.06, 24.16), ("THAT", 24.16, 24.28),
             ("INSANE?", 24.28, 24.58), ("AT", 24.64, 24.80), ("30?!", 24.80, 25.18)],
            [("WELL,", 25.64, 25.80), ("I", 25.80, 25.90), ("MEAN,", 25.90, 26.08),
             ("LIKE,", 26.08, 26.26), ("I", 26.26, 26.38), ("WAS", 26.38, 26.56),
             ("28", 26.56, 27.00), ("WHEN", 27.00, 27.30), ("WE", 27.30, 27.46),
             ("MET,", 27.46, 27.72), ("SO...", 27.72, 28.85)],
            [("I", 30.22, 30.62), ("DON'T", 30.62, 30.78), ("KNOW...", 30.78, 31.12)],
            [("I", 31.28, 31.42), ("USED", 31.42, 31.74), ("TO", 31.74, 32.14),
             ("BE", 32.14, 32.32), ("UGLY.", 32.32, 32.78)],
        ],
        "impacts_src": [
            (32.94, 33.86, "OH, COME ON!", "&H0000D7FF&", 102),
        ],
        "actions_src": [
            (19.35, 21.05, "(AWKWARD SILENCE...)"),
        ],
    },
]


MOTION_WORKER = r"""
import sys, json, subprocess, cv2, numpy as np

cfg = json.loads(sys.argv[1])
W, H = 1080, 1920
TOP_BAND, BAND_W, BAND_H = 360, 1080, 1200
FPS_NUM, FPS_DEN = 24000, 1001

def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)

shots = cfg["shots"]
def shot_params(f_idx):
    for a, b, fx0, fx1, fy0, fy1, z0, z1 in shots:
        if a <= f_idx < b:
            u = smoothstep((f_idx - a) / max(1, b - a - 1))
            return (fx0 + (fx1 - fx0) * u,
                    fy0 + (fy1 - fy0) * u,
                    z0  + (z1  - z0)  * u)
    return 0.5, 0.46, 1.0

cap = cv2.VideoCapture(cfg["src"])
sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
base_scale = max(BAND_W / sw, BAND_H / sh)

cmd = [
    cfg["ffmpeg"], "-y", "-v", "error",
    "-f", "rawvideo", "-pix_fmt", "bgr24",
    "-s", f"{W}x{H}", "-r", f"{FPS_NUM}/{FPS_DEN}", "-i", "-",
    "-vf", cfg["grade_vf"],
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
    "-pix_fmt", "yuv420p", "-threads", "2",
    cfg["raw_v"]
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
canvas = np.zeros((H, W, 3), dtype=np.uint8)

segments = [tuple(cfg["hook_frames"]), tuple(cfg["scene_frames"])]
for seg_i, (f_start, f_end) in enumerate(segments):
    cap.set(cv2.CAP_PROP_POS_FRAMES, f_start)
    n_seg = f_end - f_start
    for i, f_idx in enumerate(range(f_start, f_end)):
        ok, frame = cap.read()
        if not ok:
            break
        fx, fy, z = shot_params(f_idx)
        sc = base_scale * z
        crop_w, crop_h = BAND_W / sc, BAND_H / sc
        x0 = max(0.0, min(sw - crop_w, (sw - crop_w) * fx))
        y0 = max(0.0, min(sh - crop_h, (sh - crop_h) * fy))
        M = np.array([[sc, 0.0, -x0 * sc], [0.0, sc, -y0 * sc]], dtype=np.float32)
        band_img = cv2.warpAffine(frame, M, (BAND_W, BAND_H), flags=cv2.INTER_LANCZOS4,
                                  borderMode=cv2.BORDER_REPLICATE)
        # Clean 4-frame cinema dip-to-black at the hook->scene seam!
        alpha = 1.0
        if seg_i == 0 and i >= n_seg - 4:
            alpha = (n_seg - 1 - i) / 4.0
        elif seg_i == 1 and i < 4:
            alpha = (i + 1) / 4.0
        if alpha < 0.999:
            band_img = (band_img.astype(np.float32) * alpha).astype(np.uint8)

        canvas.fill(0)
        canvas[TOP_BAND:TOP_BAND + BAND_H, 0:W] = band_img
        proc.stdin.write(canvas.tobytes())

proc.stdin.close()
rc = proc.wait()
cap.release()
if rc != 0:
    raise RuntimeError(f"Motion worker failed: {rc}")
"""


def map_src_windows(cfg):
    """Return [(win_src_t0, win_src_t1, timeline_offset_t0), ...] for hook then scene."""
    hf0, hf1 = cfg["hook_frames"]
    sf0, sf1 = cfg["scene_frames"]
    ht0, ht1 = hf0 / FPS, hf1 / FPS
    st0, st1 = sf0 / FPS, sf1 / FPS
    hook_dur = (hf1 - hf0) / FPS
    return [
        (ht0, ht1, 0.0),
        (st0, st1, hook_dur),
    ]


def build_ass_for_video(cfg, ass_path):
    hf0, hf1 = cfg["hook_frames"]
    sf0, sf1 = cfg["scene_frames"]
    hook_dur = (hf1 - hf0) / FPS
    scene_dur = (sf1 - sf0) / FPS
    total = hook_dur + scene_dur

    ov = textkit.Overlay(playres=(W, H))

    # 1. Persistent 2-line Top Hook Header
    ov.add(0.0, total, "Title",
           r"{\an5\fnAnton\fs90\fsp2\bord0\shad0\c&H00FFFFFF&"
           r"\move(540,164,540,134,0,260)\blur16\alpha&HFF&\t(0,260,\blur0\alpha&H00&)}"
           + textkit.esc(cfg["hdr1"]), layer=5)
    ov.add(0.08, total, "Title",
           r"{\an5\fnAnton\fs122\fsp2\bord0\shad0"
           r"\move(540,284,540,254,0,280)\blur16\alpha&HFF&\t(0,280,\blur0\alpha&H00&)}"
           r"{\c&H002E2EF7&}" + textkit.esc(cfg["hdr2_red"])
           + r"{\c&H00FFFFFF&}" + textkit.esc(cfg["hdr2_white"]), layer=5)

    windows = map_src_windows(cfg)

    # 2. Map karaoke groups onto BOTH Cold-Open Hook & Main Scene!
    for win_t0, win_t1, tl_off in windows:
        win_groups = []
        for grp in cfg["kara_src"]:
            mapped = []
            for word, ws, we in grp:
                if we <= win_t0 + 0.04 or ws >= win_t1 - 0.04:
                    continue
                cs = max(win_t0, ws) - win_t0 + tl_off
                ce = min(win_t1 - 0.04, we) - win_t0 + tl_off
                if ce > cs + 0.03:
                    mapped.append((word, round(cs, 3), round(ce, 3)))
            if mapped:
                win_groups.append(mapped)

        if win_groups:
            ov.word_caps_kara(
                win_groups,
                y=1405,
                size=64,
                font="Archivo Black",
                fsp=-0.5,
                bord=8,
                shad=4,
                max_line_chars=19,
                lead=0.10,
                tail=0.20,
                blur=18,
                kf=5,
                scale=118,
                an=2,
            )

        # 3. Map Impact words onto BOTH Hook & Main Scene
        for is0, ie0, itxt, icol, isz in cfg["impacts_src"]:
            if ie0 <= win_t0 + 0.04 or is0 >= win_t1 - 0.04:
                continue
            cs = max(win_t0, is0) - win_t0 + tl_off
            ce = min(win_t1 - 0.03, ie0) - win_t0 + tl_off
            ov.add(cs, ce, "Impact",
                   rf"{{\an2\pos(540,1405)\fnAnton\fs{isz}\fsp3\c{icol}"
                   r"\bord9\3c&H000000&\3a&H00&\shad4\4c&H000000&\4a&H60&"
                   r"\fscx78\fscy78\blur16\alpha&HFF&"
                   r"\t(0,115,\fscx108\fscy108\blur0\alpha&H00&)"
                   r"\t(115,205,\fscx100\fscy100)}" + textkit.esc(itxt), layer=6)

        # 4. Map Action Beats
        for as0, ae0, atxt in cfg["actions_src"]:
            if ae0 <= win_t0 + 0.04 or as0 >= win_t1 - 0.04:
                continue
            cs = max(win_t0, as0) - win_t0 + tl_off
            ce = min(win_t1 - 0.03, ae0) - win_t0 + tl_off
            ov.add(cs, ce, "ActionCap",
                   r"{\an2\pos(540,1400)\fnBarlow Condensed\b1\fs58\fsp3\c&H00E8E8E8&"
                   r"\bord8\3c&H000000&\3a&H00&\shad3\4c&H000000&\4a&H70&"
                   r"\blur14\alpha&HFF&\t(0,140,\blur0\alpha&H00&)}" + textkit.esc(atxt), layer=4)

    # 5. Subtle movie label in bottom black band
    ov.add(0.2, total, "Small",
           r"{\an5\pos(540,1648)\fnBebas Neue\fs46\fsp6\c&H00969696&\bord0\shad0"
           r"\alpha&HFF&\t(0,350,\alpha&H20&)}" + textkit.esc(cfg["movie_tag"]), layer=2)

    ov.write(ass_path)


def build_one(cfg):
    pdir = os.path.join(STUDIO, "projects", cfg["slug"])
    os.makedirs(pdir, exist_ok=True)
    raw_v = os.path.join(SCRATCH, f"{cfg['slug']}_raw.mp4")
    ass_path = os.path.join(pdir, "subs.ass")

    hf0, hf1 = cfg["hook_frames"]
    sf0, sf1 = cfg["scene_frames"]
    ht0, hdur = hf0 / FPS, (hf1 - hf0) / FPS
    st0, sdur = sf0 / FPS, (sf1 - sf0) / FPS
    total = hdur + sdur

    print(f"\n==================== {cfg['slug']} (hook={hdur:.2f}s + scene={sdur:.2f}s = {total:.2f}s) ====================")
    worker_payload = dict(cfg)
    worker_payload["ffmpeg"] = FFMPEG
    worker_payload["raw_v"] = raw_v
    r = subprocess.run([sys.executable, "-c", MOTION_WORKER, json.dumps(worker_payload)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Motion error ({cfg['slug']}): {r.stderr}")
    print("  [1/3] Sub-pixel Lanczos4 motion video rendered.")

    build_ass_for_video(cfg, ass_path)
    with open(os.path.join(pdir, "plan_meta.json"), "w") as f:
        json.dump({k: v for k, v in cfg.items() if k not in ("kara_src",)}, f, indent=2)
    print("  [2/3] ASS captions & hook-first overlay written.")

    # Concat exact hook audio + scene audio with clean micro-fades at seam, burn ASS, calibrate loudness
    vol = cfg["vol_db"]
    fc = (
        f"[0:v]ass={ass_path}:fontsdir=/home/user/assets/fonts:shaping=complex[vout];"
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=0.05,afade=t=out:st={hdur-0.12:.4f}:d=0.12[ah];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=0.08,afade=t=out:st={sdur-0.28:.4f}:d=0.28[as];"
        f"[ah][as]concat=n=2:v=0:a=1,"
        f"highpass=f=70,"
        f"acompressor=threshold=-22dB:ratio=2.4:attack=8:release=120:makeup=3.0dB,"
        f"volume={vol}dB,"
        f"alimiter=limit=0.81:level=false:attack=5:release=50[aout]"
    )
    cmd = [
        FFMPEG, "-y", "-v", "warning",
        "-i", raw_v,
        "-ss", f"{ht0:.4f}", "-t", f"{hdur:.4f}", "-i", cfg["src"],
        "-ss", f"{st0:.4f}", "-t", f"{sdur:.4f}", "-i", cfg["src"],
        "-filter_complex_threads", "1",
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-threads", "2",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        "-shortest",
        cfg["out"],
    ]
    r2 = subprocess.run(cmd, capture_output=True, text=True)
    if r2.returncode != 0:
        raise RuntimeError(f"Mux error ({cfg['slug']}): {r2.stderr}")
    os.remove(raw_v)
    print(f"  [3/3] Final muxed -> {cfg['out']}")


if __name__ == "__main__":
    for v in VIDEOS:
        build_one(v)
