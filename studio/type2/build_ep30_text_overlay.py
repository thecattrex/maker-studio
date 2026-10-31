#!/usr/bin/env python3
"""Restore the approved Type-2 EP30 title, ranking ladder and event captions."""
import os, shutil, subprocess
import imageio_ffmpeg
import sys
sys.path.insert(0, '/home/user/studio')
from textkit import Overlay, ass_filter

SRC = '/home/user/studio/out/EP30_Type2_Final_2026-10-29.mp4'
ARCHIVE = '/home/user/studio/out/EP30_Type2_Final_NoText_2026-10-29.mp4'
OUT = SRC
TMP = '/home/user/studio/out/EP30_Type2_Final_2026-10-29_text_render_tmp.mp4'
ASS = '/home/user/studio/work/ep30-type2-restored-2026-10-29.ass'
FF = imageio_ffmpeg.get_ffmpeg_exe()
TOTAL = 17.95

if not os.path.exists(ARCHIVE):
    shutil.copy2(SRC, ARCHIVE)

ov = Overlay()
# Series-style dark header band, matching the EP28/29 two-line title treatment.
ov.panel(0.0, TOTAL, 0, 0, 1080, 340, alpha='&H45&', color='&H000000&', layer=1)
ov.add(0.0, TOTAL, 'Title',
       r'{\an5\pos(540,112)\fs100\fsp2\bord9\bordcolor&H000000&\shad0}'
       r'{\c&H00FFFFFF&}RANKING  {\c&H002828F0&}FUNNIEST', layer=4)
ov.add(0.0, TOTAL, 'Title',
       r'{\an5\pos(540,232)\fs112\fsp2\bord9\bordcolor&H000000&\shad0}'
       r'{\c&H0000D7FF&}FALLS', layer=4)
ov.add(0.0, TOTAL, 'Small',
       r'{\an9\pos(1020,34)\fs30\b1\c&H00FFFFFF&\bord4\bordcolor&H000000&\shad0}EP 30', layer=5)

items = [
    {'n': 1, 'label': 'PARTNER TUMBLE', 'color': '&H000000FF&'},
    {'n': 2, 'label': 'TRAMPOLINE FALL', 'color': '&H000011FF&'},
    {'n': 3, 'label': 'SNOW BAR SLIP', 'color': '&H0000A5FF&'},
    {'n': 4, 'label': 'BALL TUMBLE', 'color': '&H00FFFFFF&'},
]
# Current clip in the countdown: #4, #3, #2, then #1. Previously played
# labels remain in the ladder, as in the EP28/29 Type-2 reference files.
spans = [
    (0.00, 2.15, 3, set(), {3}),
    (2.15, 6.55, 2, {3}, {2, 3}),
    (6.55, 8.70, 1, {2, 3}, {1, 2, 3}),
    (8.70, TOTAL, 0, {1, 2, 3}, {0, 1, 2, 3}),
]
for a, b, active, done, labels_on in spans:
    ov.rank_side_list(a, b, items, x=54, y0=520, gap=188, size=54,
                      num_w=74, active=active, done=done,
                      labels_on=labels_on)

# Explain the action for the current clip in a legible lower pill, without
# covering the central landing/action region.
captions = [
    (0.00, 2.15, 'TUMBLES OFF THE EXERCISE BALL'),
    (2.15, 6.55, 'SLIPS FROM THE BAR INTO SNOW'),
    (6.55, 8.70, 'TRAMPOLINE JUMP ENDS IN A FALL'),
    (8.70, TOTAL, 'PARTNER BALANCE ENDS IN A TUMBLE'),
]
for a, b, text in captions:
    ov.pill(a, b, text, x=540, y=1770, size=31)

os.makedirs(os.path.dirname(ASS), exist_ok=True)
ov.write(ASS, t1=106, t2=54, t3=76, t4=44, t5=34, t6=30,
         h1=54, a1=40, i1=96, d1=54, r1=62, r2=40, cy=38)
flt = ass_filter(ASS)
cmd = [FF, '-hide_banner', '-v', 'error', '-y', '-i', SRC,
       '-vf', flt, '-map', '0:v:0', '-map', '0:a:0',
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-r', '30', '-c:a', 'copy', '-movflags', '+faststart', TMP]
p = subprocess.run(cmd, capture_output=True, text=True)
if p.returncode:
    raise RuntimeError(f'ffmpeg overlay render failed ({p.returncode})\n{p.stderr[-6000:]}')
os.replace(TMP, OUT)
print(f'Wrote {OUT}\nOverlay: {ASS}\nArchive: {ARCHIVE}')
