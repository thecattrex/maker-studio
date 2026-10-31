import os, re, subprocess, sys

FF = "/tmp/vidtools/ffmpeg"
W, H = 1080, 1428
AR = W / H
FPS = 30

# name, file, ss, dur, fx, fy, lift
A = [
    ("a1", "7578543.mp4",  1.0, 9.0, 0.50, 0.50, "soft"),
    ("a2", "3978636.mp4",  2.0, 9.0, 0.50, 0.50, "soft"),
    ("a3", "35119462.mp4", 1.0, 9.0, 0.50, 0.45, "none"),
    ("a4", "8873275.mp4",  3.0, 9.0, 0.50, 0.50, "soft"),
    ("a5", "12369822.mp4", 0.2, 9.0, 0.50, 0.50, "none"),
]

B = [
    ("b1", "29639924.mp4", 0.5, 9.0, 0.50, 0.50, "night"),
    ("b2", "13685491.mp4", 2.0, 9.0, 0.50, 0.50, "night"),
    ("b3", "37773889.mp4", 1.0, 9.0, 0.50, 0.50, "night"),
    ("b4", "31946877.mp4", 0.5, 9.0, 0.50, 0.50, "night"),
    ("b5", "14259386.mp4", 0.5, 9.0, 0.50, 0.50, "night"),
]

LIFT = {
    "none": "",
    "soft": "eq=contrast=1.04:saturation=1.10,unsharp=5:5:0.5:5:5:0",
    "night": ("curves=all='0/0 0.10/0.17 0.35/0.46 0.7/0.80 1/1',"
              "eq=contrast=1.06:saturation=1.05:gamma=1.05,"
              "colorbalance=bs=0.06:bm=0.02,unsharp=5:5:0.6:5:5:0"),
}


def even(x):
    return int(x) // 2 * 2


def dims(p):
    e = subprocess.run([FF, "-hide_banner", "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Video:.*?(\d{2,4})x(\d{2,4})", e)
    return int(m.group(1)), int(m.group(2))


def build(src_dir, segs, out_reel):
    parts = []
    for name, f, ss, dur, fx, fy, lift in segs:
        p = os.path.join(src_dir, f)
        iw, ih = dims(p)
        ch = ih if ih * AR <= iw else even(iw / AR)
        cw = even(min(iw, ch * AR))
        ch = even(cw / AR)
        if ch > ih:
            ch = even(ih)
            cw = even(ch * AR)
        g = ("scale=1080:1428:flags=lanczos," + LIFT[lift] + "," if LIFT[lift]
             else "scale=1080:1428:flags=lanczos,")
        vf = (f"crop={cw}:{ch}:x='(iw-{cw})*{fx}':y='(ih-{ch})*{fy}',"
              f"{g}fps={FPS},setsar=1,format=yuv420p")
        out = os.path.join(src_dir, f"seg_{name}.mp4")
        r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", str(ss),
                            "-t", str(dur), "-i", p, "-an", "-vf", vf,
                            "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
                            "-threads", "2", out, "-y"], capture_output=True, text=True)
        print(name, f"{iw}x{ih}->{cw}x{ch}", "rc", r.returncode, r.stderr[-120:] if r.returncode else "")
        parts.append(out)

    with open(os.path.join(src_dir, "list.txt"), "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    if os.path.exists(out_reel):
        os.remove(out_reel)
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", os.path.join(src_dir, "list.txt"),
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "128k", "-shortest", "-threads", "2", out_reel, "-y"],
                       capture_output=True, text=True)
    print("concat rc", r.returncode, r.stderr[-200:] if r.returncode else "")


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "a":
        build("/tmp/t3a_src", A, "/tmp/t3a/reel.mp4")
    else:
        build("/tmp/t3b_src", B, "/tmp/t3b/reel.mp4")
