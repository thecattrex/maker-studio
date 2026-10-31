#!/bin/bash
cd /tmp
echo "=== metadata ==="
python3 -m yt_dlp --print "%(title)s|%(uploader)s|%(duration)s|%(view_count)s" --no-warnings "https://youtube.com/shorts/5b5p4udHuew" 2>&1 | tail -3
python3 -m yt_dlp --print "%(description)s" --no-warnings "https://youtube.com/shorts/5b5p4udHuew" 2>&1 | head -20
echo "=== download ==="
python3 -m yt_dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o "/tmp/ref.%(ext)s" "https://youtube.com/shorts/5b5p4udHuew" 2>&1 | tail -3
ls -la /tmp/ref.* 2>/dev/null
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/ref.mp4
