#!/bin/bash
cd /tmp
python3 -m yt_dlp -f 'bv*[height<=1080]+ba/b' --merge-output-format mp4 -o '/tmp/chick.%(ext)s' 'https://youtube.com/shorts/VDMeoFrevyA' 2>&1 | tail -6
ls -la /tmp/chick.* 2>/dev/null
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/chick.mp4
ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 /tmp/chick.mp4
