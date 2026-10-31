#!/usr/bin/env python3
import os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep14_15_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,14);small=ImageFont.truetype(FONT,11);TW,TH,COLS,G=180,235,6,5
spec={'x9spdi4':(25,40.8,None),'xa1tu8u':(0,6.28,None),'xbqy0iy':(10,22,'crop=450:800:0:20'),'xbmo2w6':(8,24,'crop=337:600:70:0'),'x9gw0h4':(0,15.77,'crop=388:690:46:95')}
H=45+len(spec)*2*(TH+22);c=Image.new('RGB',(COLS*(TW+G)+G,H),(10,14,24));d=ImageDraw.Draw(c);d.text((G,10),'EP14–EP15 • alternate crop-window review',font=font,fill='white')
for r,(vid,(a,b,crop)) in enumerate(spec.items()):
 info=probe(f'{ROOT}/{vid}/{vid}.mp4');base=45+r*2*(TH+22);d.text((G,base),f'{vid} | proposed {a:.1f}–{b:.1f}s | {info["width"]}x{info["height"]}',font=small,fill=(250,218,94));times=[a+(b-a)*i/11 for i in range(12)]
 for j,t in enumerate(times):
  tmp=f'/tmp/ep14_alt_{vid}_{j}.jpg';cmd=[FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',f'{ROOT}/{vid}/{vid}.mp4']
  if crop:cmd+=['-vf',crop]
  cmd+=['-frames:v','1',tmp];subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tile=Image.new('RGB',(TW,TH+18),(4,5,8))
  if os.path.exists(tmp):
   im=Image.open(tmp).convert('RGB');im.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(im,((TW-im.width)//2,(TH-im.height)//2))
  ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white');x=G+(j%COLS)*(TW+G);y=base+15+(j//COLS)*(TH+22);c.paste(tile,(x,y))
out=f'{OUT}/EP14_EP15_cut_window_group4.jpg';c.save(out,quality=91);print(out)
