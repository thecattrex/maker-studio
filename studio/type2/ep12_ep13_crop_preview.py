#!/usr/bin/env python3
import os,sys,subprocess,math
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/dl/src/ep12_13_candidates';OUT='/home/user/studio/type2'
# id, source start, duration, crop x,y,w,h
SPECS=[
 ('x9ejedo',0.0,3.7,(0,70,480,635)),
 ('x9rxxiq',0.5,6.5,(242,0,363,480)),
 ('x9wy8kc',4.0,5.1,(0,120,480,635)),
 ('xa64o2o',5.0,6.0,(0,100,480,635)),
 ('x99erwy',7.5,5.0,(0,80,480,635)),
 ('x9q3d02',0.0,4.1,(0,100,480,635)),
 ('xb8cze6',0.3,5.0,(0,100,480,635)),
 ('x8ihsjz',6.0,6.0,(108,300,500,661)),
 ('x99bals',0.0,6.4,(0,100,480,635)),
 ('xbfbsli',0.0,4.6,(0,60,480,635)),
 ('x9bi13o',3.0,6.3,(0,150,420,556)),
 ('xa1xumo',0.0,8.5,(0,100,480,635)),
 ('x99erwy',7.5,5.0,(0,150,480,635)),
 ('x9o5ajg',7.5,4.6,(13,80,453,600)),
]
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15);SM=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
TW,TH=155,205;COLS=8;G=5
for gi in range(math.ceil(len(SPECS)/4)):
 subset=SPECS[gi*4:(gi+1)*4];blocks=[]
 for id,ss,dur,crop in subset:
  p=f'{ROOT}/{id}/{id}.mp4';inf=probe(p);x,y,w,h=crop
  if x+w>inf['width'] or y+h>inf['height']:
   print('INVALID',id,crop,inf['width'],inf['height']);continue
  n=min(16,max(6,int(dur/0.4)));ts=[ss+(dur-0.12)*i/(n-1) for i in range(n)]
  rows=math.ceil(n/COLS);block=Image.new('RGB',(COLS*(TW+G)+G,25+rows*(TH+22)),(13,16,24));dr=ImageDraw.Draw(block)
  dr.text((G,5),f'{id} | {ss:.1f}–{ss+dur:.1f}s | crop {crop}',font=SM,fill='white')
  for j,t in enumerate(ts):
   tmp=f'/tmp/crop_{id}_{j}.jpg';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',p,'-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(TW,TH+18),(6,8,12))
   if os.path.exists(tmp) and os.path.getsize(tmp)>100:
    src=Image.open(tmp).convert('RGB').crop((x,y,x+w,y+h));src.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(src,((TW-src.width)//2,(TH-src.height)//2))
   ImageDraw.Draw(tile).text((3,TH+2),f'{t:.2f}s',font=SM,fill='white')
   xx=G+(j%COLS)*(TW+G);yy=25+(j//COLS)*(TH+22);block.paste(tile,(xx,yy))
  blocks.append(block)
 H=sum(b.height for b in blocks)+G*(len(blocks)+1);W=COLS*(TW+G)+G;canvas=Image.new('RGB',(W,H),(13,16,24));yy=G
 for b in blocks:canvas.paste(b,(0,yy));yy+=b.height+G
 out=f'{OUT}/EP12_EP13_crop_previews_group{gi+1}.jpg';canvas.save(out,quality=90);print(out,canvas.size)
