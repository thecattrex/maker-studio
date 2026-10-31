#!/bin/bash
cd /tmp
for id in J1BKm2FVi1I iIFpoGfiFv4; do
  echo "=== $id ==="
  python3 -m yt_dlp -f 'bv*[height<=1080]+ba/b' --merge-output-format mp4 -o "/tmp/cand_${id}.%(ext)s" "https://youtube.com/shorts/$id" --no-warnings 2>&1 | tail -2
  ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of csv=p=0 "/tmp/cand_${id}.mp4" 2>/dev/null
  ls -la "/tmp/cand_${id}.mp4" 2>/dev/null
done
