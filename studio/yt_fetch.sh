#!/usr/bin/env bash
# yt_fetch.sh — one-pass YouTube fetch. Run this on YOUR OWN machine (home IP).
#
# Why: the sandbox runs on a Google Cloud datacenter IP, which YouTube gates with
# "Sign in to confirm you're not a bot". A normal home connection is not gated.
#
# Setup (once):
#   pip install -U "yt-dlp[default]"
#   # ffmpeg must be installed (ffmpeg.org, or: winget install ffmpeg / brew install ffmpeg)
#
# Use:
#   1. edit targets.txt  (one line per clip:  URL  start  duration  name)
#   2. bash yt_fetch.sh
#   3. upload the produced folder, or drop the files into the chat/workspace
#
# Rule: everything downloads in ONE pass. No probing, no retrying.
#       Probing with -F/--skip-download spends the same allowance as a download
#       and is what triggered the block in the first place.

set -u
TARGETS="${1:-targets.txt}"
OUT="${2:-./yt_clips}"
mkdir -p "$OUT"
ok=0; fail=0

while IFS='|' read -r url start dur name; do
  # skip blanks and comments
  case "$url" in ''|\#*) continue;; esac
  url=$(echo "$url" | xargs); start=$(echo "$start" | xargs)
  dur=$(echo "$dur" | xargs);   name=$(echo "$name" | xargs)
  [ -z "$name" ] && name="clip_$ok"

  # yt-dlp wants HH:MM:SS-HH:MM:SS for --download-sections
  end=$(python3 - "$start" "$dur" <<'PY'
import sys
def s(x):
    x = x.strip()
    if ':' in x:
        p = [float(i) for i in x.split(':')]
        while len(p) < 3: p.insert(0, 0)
        return p[0]*3600 + p[1]*60 + p[2]
    return float(x)
a, d = s(sys.argv[1]), float(sys.argv[2])
b = a + d
h = lambda t: "%02d:%02d:%06.3f" % (int(t//3600), int(t%3600//60), t%60)
print("%s-%s" % (h(a), h(b)))
PY
)

  echo "--> $name  ($start + ${dur}s)"
  yt-dlp \
    --no-warnings --no-progress --retries 2 --fragment-retries 3 \
    --no-playlist --no-overwrites \
    -f "bv*[height<=1080][vcodec^=avc1]+ba/bv*[height<=1080]+ba/b" \
    --merge-output-format mp4 \
    --download-sections "$end" --force-keyframes-at-cuts \
    -o "$OUT/${name}.%(ext)s" \
    "$url"

  f=$(ls "$OUT/${name}".mp4 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    info=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$f" 2>/dev/null)
    aud=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$f" 2>/dev/null)
    echo "    OK  ${info:-?}  audio=${aud:-NONE}  $(du -h "$f" | cut -f1)"
    ok=$((ok+1))
  else
    echo "    FAILED — agar 'Sign in to confirm' aaya to ruk jao, aaj aur mat try karo."
    fail=$((fail+1))
  fi
done < "$TARGETS"

echo
echo "done: $ok ok, $fail failed -> $OUT"
