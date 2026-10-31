#!/bin/bash
cd /tmp
for id in tztvQjqMR_U HG3gevu51Rc yFK4EHfPsbA; do
  python3 -m yt_dlp -f 'bv*[height<=1440]+ba/b' --merge-output-format mp4 -o "/tmp/s_${id}.%(ext)s" "https://youtube.com/watch?v=$id" --no-warnings >/dev/null 2>&1
  if [ -f "/tmp/s_${id}.mp4" ]; then
    printf "%-14s %s  dur=%s\n" "$id" "$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 /tmp/s_${id}.mp4)" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/s_${id}.mp4)"
    ffmpeg -v error -ss 5 -i "/tmp/s_${id}.mp4" -frames:v 1 -vf scale=300:-1 -y "/tmp/s_${id}.jpg"
  else
    echo "$id FAILED"
  fi
done
python3 - <<'PY'
from PIL import Image
import glob
fs=sorted(glob.glob('/tmp/s_*.jpg'))
ims=[Image.open(f) for f in fs]
if ims:
    h=max(i.size[1] for i in ims); W=sum(i.size[0] for i in ims)
    sh=Image.new("RGB",(W,h),"white"); x=0
    for i in ims: sh.paste(i,(x,0)); x+=i.size[0]
    sh.save('/tmp/comps.jpg',quality=85); print(sh.size)
PY
