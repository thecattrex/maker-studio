#!/usr/bin/env python3
import os,subprocess,math,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/dl/src/ep12_13_candidates';OUT='/home/user/studio/type2'
# Selected plausible leads + fence-jump backup; dense sampled frames are visual triage only.
SPECS=[
 ('x9ejedo',0,9.2,0.35),('x9rxxiq',0,14,0.5),('x9wy8kc',0,9.1,0.3),
 ('xa64o2o',0,18.6,0.5),('x99erwy',0,12.5,0.35),('x9q3d02',0,9.1,0.3),
 ('xb8cze6',0,7.3,0.25),('x8ihsjz',0,14.8,0.5),('x9s26xm',0,30,0.6),
]
TW,TH=145,215;COLS=7;G=5;FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
for gi in range(3):
 subset=SPECS[gi*3:(gi+1)*3]
 # Each candidate starts a labeled block; all sampled frames in timestamp order.
 maxrows=sum(math.ceil(len([t for t in range(0,1)]) / 1) for _ in [])
 blocks=[]
 for id,start,end,step in subset:
  p=f'{ROOT}/{id}/{id}.mp4';inf=probe(p); end=min(end,inf['duration']-0.03)
  ts=[];t=start+0.08
  while t<=end:ts.append(round(t,2));t+=step
  rows=math.ceil(len(ts)/COLS);height=26+rows*(TH+24)
  block=Image.new('RGB',(COLS*(TW+G)+G,height),(13,16,24));d=ImageDraw.Draw(block)
  d.text((G,5),f'{id} | {inf["duration"]:.1f}s | {inf["width"]}x{inf["height"]} | sample every {step}s',font=FONT,fill='white')
  for j,t in enumerate(ts):
   tmp=f'/tmp/qc_{id}_{j}.jpg'
   subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(t),'-i',p,'-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(TW,TH+21),(6,8,12))
   if os.path.exists(tmp) and os.path.getsize(tmp)>100:
    src=Image.open(tmp).convert('RGB');src.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(src,((TW-src.width)//2,(TH-src.height)//2))
   ImageDraw.Draw(tile).text((3,TH+3),f'{t:.2f}s',font=FONT,fill='white')
   x=G+(j%COLS)*(TW+G);y=24+(j//COLS)*(TH+24);block.paste(tile,(x,y))
  blocks.append(block)
 H=sum(b.height for b in blocks)+G*(len(blocks)+1);W=COLS*(TW+G)+G
 canvas=Image.new('RGB',(W,H),(13,16,24));y=G
 for b in blocks:canvas.paste(b,(0,y));y+=b.height+G
 out=f'{OUT}/EP12_EP13_dense_candidate_QC_group{gi+1}.jpg';canvas.save(out,quality=90);print(out,canvas.size)
