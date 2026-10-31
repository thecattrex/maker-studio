#!/usr/bin/env python3
import os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep14_15_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();IDS=['xbmo2w6']
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12);TW,TH,COLS,G=190,230,6,5
c=Image.new('RGB',(COLS*(TW+G)+G,len(IDS)*2*(TH+28)+60),(11,15,24));d=ImageDraw.Draw(c);d.text((G,12),'EP14–EP15 fresh candidates • final screening',font=font,fill='white')
for r,vid in enumerate(IDS):
 p=f'{ROOT}/{vid}/{vid}.mp4';info=probe(p);dur=info['duration'];n=12;ts=[dur*i/(n-1) for i in range(n)];base=52+r*2*(TH+28);d.text((G,base),f'{vid} | {dur:.1f}s | {info["width"]}x{info["height"]}',font=small,fill=(249,216,91))
 for j,t in enumerate(ts):
  tmp=f'/tmp/ep14_{vid}_{j}.jpg';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',p,'-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tile=Image.new('RGB',(TW,TH+20),(3,4,8))
  if os.path.exists(tmp):
   im=Image.open(tmp).convert('RGB');im.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(im,((TW-im.width)//2,(TH-im.height)//2))
  ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white');x=G+(j%COLS)*(TW+G);y=base+18+(j//COLS)*(TH+28);c.paste(tile,(x,y))
out=f'{OUT}/EP14_EP15_candidates_group17.jpg';c.save(out,quality=90);print(out)
