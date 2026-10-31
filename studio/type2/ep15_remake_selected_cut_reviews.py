#!/usr/bin/env python3
"""Frame-based taste-profile review for the four intended EP15 remake windows.
This is visual review only; it is not a claim of audio listening."""
import os,sys,subprocess,math
sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg,probe
from PIL import Image,ImageDraw,ImageFont
FF=ensure_ffmpeg();ROOT='/home/user/dl/src/ep15_remake_candidates';OUT='/home/user/studio/type2';FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,13);sm=ImageFont.truetype(FONT,11)
# rank order (#1 strongest first); source windows and exact 4:5 crop x,y,w,h
SPECS=[
 ('x9lorig',0.0,5.5,(0,106,480,635),'#1 bench prank: setup → collapse → recovery'),
 ('x95yj4a',0.0,10.0,(0,138,608,804),'#2 couple trend: setup → failed catch → laughter'),
 ('x9weqas',0.0,6.3,(0,106,480,635),'#3 chef tray: setup → drop → reaction'),
 ('x9m3tj6',0.0,5.7,(0,106,480,635),'#4 beer spill: setup → spill → aftermath'),
]
W,H,G,COLS=160,214,5,6
for id,a,b,(x,y,w,h),desc in SPECS:
 p=f'{ROOT}/{id}/{id}.mp4';info=probe(p);dur=b-a;step=max(0.28,dur/18);times=[];t=a
 while t<=b+1e-6:times.append(round(t,3));t+=step
 if times[-1]<b-0.02:times.append(b)
 rows=math.ceil(len(times)/COLS);sheet=Image.new('RGB',(COLS*(W+G)+G,rows*(H+22)+52),(10,14,24));d=ImageDraw.Draw(sheet);d.text((G,7),f'{id} | {desc}',font=font,fill='white');d.text((G,26),f'window {a:.2f}–{b:.2f}s; crop x={x},y={y},w={w},h={h}; source audio track={info["has_audio"]}',font=sm,fill=(250,218,94))
 for j,t in enumerate(times):
  tmp=f'/tmp/ep15_selected_{id}_{j}.jpg';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',p,'-vf',f'crop={w}:{h}:{x}:{y}','-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tile=Image.new('RGB',(W,H+18),(4,5,8))
  if os.path.exists(tmp):
   im=Image.open(tmp).convert('RGB');im.thumbnail((W,H),Image.Resampling.LANCZOS);tile.paste(im,((W-im.width)//2,(H-im.height)//2))
  ImageDraw.Draw(tile).text((3,H+3),f'{t:.2f}s',font=sm,fill='white');sheet.paste(tile,(G+(j%COLS)*(W+G),47+(j//COLS)*(H+22)))
 out=f'{OUT}/EP15_selected_review_{id}.jpg';sheet.save(out,quality=92);print(out)
