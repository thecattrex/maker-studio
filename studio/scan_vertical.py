import json, subprocess, sys

QUERIES = [
    "trampoline fail shorts",
    "skateboard fail shorts",
    "bike crash fail shorts",
    "slip and fall fail shorts",
    "ladder fall fail shorts",
    "gym fail shorts",
]

def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=120).stdout

cands = {}
for q in QUERIES:
    out = run(["python3", "-m", "yt_dlp", "--flat-playlist", "--print", "%(id)s|%(duration)s|%(title)s",
               f"ytsearch8:{q}", "--no-warnings"])
    for line in out.strip().splitlines():
        try:
            vid, dur, title = line.split("|", 2)
            dur = float(dur)
        except Exception:
            continue
        if 5 <= dur <= 45:
            cands[vid] = (dur, title)

print(f"{len(cands)} candidates, checking orientation...", file=sys.stderr)
vert = []
for vid, (dur, title) in list(cands.items()):
    out = run(["python3", "-m", "yt_dlp", "-J", "--no-warnings", f"https://youtube.com/watch?v={vid}"])
    try:
        j = json.loads(out)
    except Exception:
        continue
    fmts = [f for f in j.get("formats", []) if f.get("vcodec") not in (None, "none") and f.get("height")]
    if not fmts:
        continue
    best = max(fmts, key=lambda f: (f.get("height", 0)))
    w, h = best.get("width") or 0, best.get("height") or 0
    if h >= w * 1.35:
        vert.append((vid, w, h, round(dur, 1), title[:60]))
        print("VERT", vid, w, h, round(dur, 1), title[:60])
print("\n--- vertical list ---")
for v in vert:
    print("|".join(map(str, v)))
