#!/bin/bash
cd /tmp
for id in ozXDtVwTbBQ XyFQD3WXxFI kCqAviVPkMs 3hk29N-Jc04 DUKHb59uBpo A6o2QUXEaNE; do
  python3 -m yt_dlp -f 'bv*[height<=1440]+ba/b' --merge-output-format mp4 -o "/tmp/f_${id}.%(ext)s" "https://youtube.com/watch?v=$id" --no-warnings >/dev/null 2>&1
  if [ -f "/tmp/f_${id}.mp4" ]; then
    printf "%-14s %s  dur=%s\n" "$id" "$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 /tmp/f_${id}.mp4)" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/f_${id}.mp4)"
  else
    echo "$id FAILED"
  fi
done
