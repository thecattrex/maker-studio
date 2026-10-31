#!/bin/bash
# Pre-cut + text-remove + normalise the 4 new clips to 1080x1428
set -e
SRC=/tmp/s_HG3gevu51Rc.mp4
OUT=/tmp/nc
mkdir -p $OUT

# A  0.0-3.4   trampoline jump   (content 265..1217)
ffmpeg -v error -ss 0.0 -t 3.4 -i $SRC -vf "crop=720:952:0:265,scale=1080:1428:flags=lanczos,fps=30,setsar=1" -an -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -y $OUT/A.mp4

# B  8.2-11.6  pool surfboard     (content 232..1071 ; crop width to 634)
ffmpeg -v error -ss 8.2 -t 3.4 -i $SRC -vf "crop=634:839:43:232,scale=1080:1428:flags=lanczos,fps=30,setsar=1" -an -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -y $OUT/B.mp4

# C  24.9-27.9 golf cart          (content 240..1192 ; delogo 'dip sa USA comedy')
ffmpeg -v error -ss 24.9 -t 3.0 -i $SRC -vf "delogo=x=185:y=1065:w=360:h=60,crop=720:952:0:240,scale=1080:1428:flags=lanczos,fps=30,setsar=1" -an -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -y $OUT/C.mp4

# D  33.5-36.3 tube flip          (content 250..1202 ; delogo text + AFV logo)
ffmpeg -v error -ss 33.5 -t 2.8 -i $SRC -vf "delogo=x=185:y=1070:w=360:h=60,delogo=x=478:y=226:w=120:h=42,crop=720:952:0:250,scale=1080:1428:flags=lanczos,fps=30,setsar=1" -an -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -y $OUT/D.mp4

for f in A B C D; do
  printf "%s  " $f
  ffprobe -v error -show_entries stream=width,height,r_frame_rate:format=duration -of csv=p=0 $OUT/$f.mp4 | tr '\n' ' '
  echo
done

printf "file '%s'\n" $OUT/A.mp4 $OUT/B.mp4 $OUT/C.mp4 $OUT/D.mp4 > $OUT/list.txt
ffmpeg -v error -f concat -safe 0 -i $OUT/list.txt -c copy -y /tmp/nc_src.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/nc_src.mp4
