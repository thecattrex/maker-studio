#!/usr/bin/env python3
import os,sys,math,subprocess,json
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep12_13_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg()
ids=['x9s26xm','xa16vus','x8ihsjz','xa64o2o','xb4fq36','x9rxxiq','x8ctzxy','x9wy8kc','xa0shno','x8fx5gw','xb8cze6','x8mdbfj','x9y52lk','x9ejedo','xbfbsli','x99bals','x9p4g1k','x9yd16y','x99erwy','x9bo89y','xa0stk6','x9q3d02','x93u712','x7vvtx7','x9y2syg','x9o5ajg','x9bi13o','xa1xumo']
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
TW,TH=156,245;COLS=8;G=6;ROW_H=TH+48
for group in range(math.ceil(len(ids)/4)):
 chosen=ids[group*4:(group+1)*4]
 canvas=Image.new('RGB',(COLS*(TW+G)+G,len(chosen)*ROW_H+50),(13,16,24));dr=ImageDraw.Draw(canvas)
 dr.text((G,14),f'EP12–EP13 fresh source screening • group {group+1}',font=font,fill='white')
 for ri,id in enumerate(chosen):
  p=f'{ROOT}/{id}/{id}.mp4'; info=probe(p);dur=info['duration']
  n=min(16,max(5,math.ceil(dur/1.6)))
  # sample from 2% to 96% to include full setup and end
  ts=[(dur-0.2)*i/(n-1)+0.1 for i in range(n)] if n>1 else [dur/2]
  y=48+ri*ROW_H;dr.text((G,y),f'{id}  {dur:.1f}s  {info["width"]}x{info["height"]}  {info["acodec"]}',font=small,fill=(245,211,96))
  for j,t in enumerate(ts):
   tmp=f'/tmp/ep12_{id}_{j}.jpg'
   subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',p,'-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(TW,TH+22),(6,8,12))
   if os.path.exists(tmp) and os.path.getsize(tmp)>100:
    src=Image.open(tmp).convert('RGB');src.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(src,((TW-src.width)//2,(TH-src.height)//2))
   ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white')
   x=G+j*(TW+G);canvas.paste(tile,(x,y+18));ImageDraw.Draw(canvas).rectangle((x,y+18,x+TW-1,y+TH+39),outline=(70,84,107))
 out=f'{OUT}/EP12_EP13_candidates_group{group+1}.jpg';canvas.save(out,quality=90);print(out)
