"""transcribe.py — audio se word-level timing, Groq Whisper Large-v3 se.

Key kahan se aati hai (pehla jo mile):
  1. env var GROQ_API_KEY
  2. ~/.config/groq/key

Use:
    python3 transcribe.py <video> <start> <dur> [--out words.json] [--lang hi]

Output JSON:
    {"file":.., "start":.., "dur":.., "text":"..",
     "words":[{"w":"...","s":0.12,"e":0.44}, ...],     # seconds, clip ke ANDAR
     "segments":[{"s":..,"e":..,"text":".."}, ...]}
"""
import argparse, json, os, subprocess, sys, tempfile

STUDIO = os.path.dirname(os.path.abspath(__file__))
API = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL = os.environ.get("GROQ_MODEL", "whisper-large-v3")
FFMPEG = os.environ.get("FFMPEG") or (
    "/tmp/vidtools/ffmpeg" if os.path.exists("/tmp/vidtools/ffmpeg") else "ffmpeg")


def api_key():
    k = os.environ.get("GROQ_API_KEY")
    if k:
        return k.strip()
    p = os.path.expanduser("~/.config/groq/key")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit("Groq key nahi mili — ~/.config/groq/key me daalo ya GROQ_API_KEY set karo")


def extract(src, start, dur, out):
    """16 kHz mono mp3 — Groq ko yahi chahiye, file chhoti rehti hai."""
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
                        "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                        "-b:a", "64k", "-y", out], capture_output=True)
    if r.returncode != 0 or not os.path.exists(out):
        sys.exit(f"audio extract fail: {r.stderr.decode()[-300:]}")


def post(mp3, lang="hi", prompt=None):
    import json as _j
    import urllib.request
    boundary = "----studio" + os.urandom(8).hex()
    fields = [("model", MODEL), ("language", lang), ("response_format", "verbose_json"),
              ("temperature", "0"),
              ("timestamp_granularities[]", "word"),
              ("timestamp_granularities[]", "segment")]
    if prompt:
        fields.append(("prompt", prompt))
    body = b""
    for k, v in fields:
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                 f"{v}\r\n").encode()
    data = open(mp3, "rb").read()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode()
    body += data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {api_key()}",
        "User-Agent": "studio/1.0",     # iske bina groq 403 deta hai
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return _j.loads(r.read())


def run(src, start, dur, out_path, lang="hi", prompt=None):
    with tempfile.TemporaryDirectory() as td:
        mp3 = os.path.join(td, "a.mp3")
        extract(src, start, dur, mp3)
        size = os.path.getsize(mp3) / 1e6
        print(f"  audio {dur:.1f}s, {size:.2f} MB -> groq/{MODEL}")
        d = post(mp3, lang, prompt)
    if "error" in d:
        sys.exit(f"groq error: {d['error']}")
    res = {
        "file": src, "start": start, "dur": dur,
        "text": (d.get("text") or "").strip(),
        "words": [{"w": w.get("word", "").strip(),
                   "s": round(float(w.get("start", 0)), 3),
                   "e": round(float(w.get("end", 0)), 3)}
                  for w in d.get("words", [])],
        "segments": [{"s": round(float(s.get("start", 0)), 3),
                      "e": round(float(s.get("end", 0)), 3),
                      "text": (s.get("text") or "").strip()}
                     for s in d.get("segments", [])],
    }
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        json.dump(res, open(out_path, "w"), indent=1, ensure_ascii=False)
        print(f"  saved {out_path}")
    print(f"  words {len(res['words'])} | segments {len(res['segments'])}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("start", type=float)
    ap.add_argument("dur", type=float)
    ap.add_argument("--out", default=None)
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--prompt", default=None)
    a = ap.parse_args()
    r = run(a.video, a.start, a.dur, a.out, a.lang, a.prompt)
    print(r["text"][:200])


if __name__ == "__main__":
    main()
