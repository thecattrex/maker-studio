#!/usr/bin/env python3
import os,subprocess,sys,math
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
from PIL import Image,ImageDraw,ImageFont
FF=ensure_ffmpeg();ROOT='/home/user/dl/src/ep15_remake_candidates';OUT='/home/user/studio/type2';FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,13);sm=ImageFont.truetype(FONT,11)
SPECS={
 'x9ejedo':(0,8.5,0.5),
 'x9m3tj6':(0,5.8,0.3),
 'x9weqas':(0,7.0,0.35),
 'x9wy8kc':(0,8.8,0.55),
 'x9uf2f6':(0,14.0,0.9),
 'xamvx3y':(35,63.0,2.0),
}
W,H,G,COLS=150,205,5,6
for id,(a,b,step) in SPECS.items():
 p=f'{ROOT}/{id}/{id}.mp4';info=probe(p);w,h=info['width'],info['height'];cw=min(w,480);ch=int(round(cw/(1080/1428)));cy=max(0,min(h-ch,(h-ch)//2));cx=max(0,(w-cw)//2);times=[];t=a
 while t<=b+1e-6:times.append(round(t,3));t+=step
 rows=math.ceil(len(times)/COLS);sheet=Image.new('RGB',(COLS*(W+G)+G,rows*(H+22)+44),(10,14,24));d=ImageDraw.Draw(sheet);d.text((G,8),f'{id} | full candidate window {a:.1f}–{b:.1f}s | audio={info["has_audio"]} | 4:5 crop {cx},{cy},{cw},{ch}',font=font,fill='white')
 for j,t in enumerate(times):
  tmp=f'/tmp/remake_detail_{id}_{j}.jpg';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(t),'-i',p,'-vf',f'crop={cw}:{ch}:{cx}:{cy}','-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tile=Image.new('RGB',(W,H+18),(4,5,8))
  if os.path.exists(tmp):
   im=Image.open(tmp).convert('RGB');im.thumbnail((W,H),Image.Resampling.LANCZOS);tile.paste(im,((W-im.width)//2,(H-im.height)//2))
  ImageDraw.Draw(tile).text((3,H+3),f'{t:.2f}s',font=sm,fill='white');sheet.paste(tile,(G+(j%COLS)*(W+G),38+(j//COLS)*(H+22)))
 out=f'{OUT}/EP15_remake_detail_{id}.jpg';sheet.save(out,quality=92);print(out)
