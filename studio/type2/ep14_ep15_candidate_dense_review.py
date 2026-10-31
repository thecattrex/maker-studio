#!/usr/bin/env python3
import os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep14_15_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();
IDS=['x9um1u0','xa1goko','x9f8kva','xapidry','xayt822','x9spdi4','xa1tu8u','x9gw0h4']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,14);small=ImageFont.truetype(FONT,11);TW,TH,COLS,G=180,250,6,5
# Dense frame intervals focus on plausible payoff/action windows; timestamps retained.
windows={'x9um1u0':(0,8.9),'xa1goko':(0,7.2),'x9f8kva':(0,18),'xapidry':(0,33.3),'xayt822':(0,11.7),'x9spdi4':(18,40.8),'xa1tu8u':(0,6.28),'x9gw0h4':(0,15.77)}
crops={'x9gw0h4':'crop=427:760:26:60','xayt822':'crop=270:480:289:0','xapidry':'crop=450:800:0:0','x9um1u0':'crop=460:818:0:25','xa1goko':'crop=457:812:0:20','xa1tu8u':'crop=450:800:0:0'}
rows=[]
for vid in IDS:
 p=f'{ROOT}/{vid}/{vid}.mp4';info=probe(p);a,b=windows[vid];times=[a+(b-a)*i/23 for i in range(24)];rows.append((vid,info,times))
H=55+len(rows)*2*(TH+22);c=Image.new('RGB',(COLS*(TW+G)+G,H),(10,14,24));d=ImageDraw.Draw(c);d.text((G,12),'EP14–EP15 • dense candidate / proposed portrait-crop visual review',font=font,fill='white')
for r,(vid,info,times) in enumerate(rows):
 base=52+r*2*(TH+22);d.text((G,base),f'{vid} | {info["duration"]:.1f}s | {info["width"]}x{info["height"]}',font=small,fill=(250,218,94));
 for j,t in enumerate(times):
  tmp=f'/tmp/ep14_dense_{vid}_{j}.jpg';cmd=[FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',f'{ROOT}/{vid}/{vid}.mp4']
  if vid in crops:cmd+=['-vf',crops[vid]]
  cmd+=['-frames:v','1',tmp];subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tile=Image.new('RGB',(TW,TH+18),(4,5,8))
  if os.path.exists(tmp):
   im=Image.open(tmp).convert('RGB');im.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(im,((TW-im.width)//2,(TH-im.height)//2))
  ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white');x=G+(j%COLS)*(TW+G);y=base+16+(j//COLS)*(TH+22);c.paste(tile,(x,y))
out=f'{OUT}/EP14_EP15_dense_review1.jpg';c.save(out,quality=90);print(out)
