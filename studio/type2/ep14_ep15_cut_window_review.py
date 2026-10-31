#!/usr/bin/env python3
import os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep14_15_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,14);small=ImageFont.truetype(FONT,11);TW,TH,COLS,G=170,220,6,5
# Proposed full-source windows, sampled densely for visual approval; crops are preview-only.
clips={
'x9um1u0':(4.0,8.8,'crop=460:818:0:25'),
'xa1goko':(0.0,4.8,'crop=457:812:0:20'),
'x9f8kva':(4.0,14.0,None),
'xapidry':(6.0,17.0,'crop=450:800:0:0'),
'xayt822':(2.0,11.7,'crop=270:480:289:0'),
'xbrd6tq':(0.0,10.2,'crop=448:796:0:30'),
'xbmm542':(7.0,22.9,None),
'xaolx2e':(2.0,12.0,'crop=450:800:0:0'),
'xbqy0iy':(0.0,56.5,'crop=450:800:0:20'),
'x9gw0h4':(0.0,15.77,'crop=427:760:26:60'),
'xbntrrq':(0.0,15.35,None),
}
groups=[['x9um1u0','xa1goko','x9f8kva','xapidry'],['xayt822','xbrd6tq','xbmm542','xaolx2e'],['xbqy0iy','x9gw0h4','xbntrrq']]
for gi,ids in enumerate(groups,1):
 H=40+len(ids)*2*(TH+23);c=Image.new('RGB',(COLS*(TW+G)+G,H),(10,14,24));d=ImageDraw.Draw(c);d.text((G,10),f'EP14–EP15 • proposed crop-window frames • group {gi}',font=font,fill='white')
 for r,vid in enumerate(ids):
  a,b,crop=clips[vid];info=probe(f'{ROOT}/{vid}/{vid}.mp4');base=40+r*2*(TH+23);d.text((G,base),f'{vid} | proposed {a:.1f}–{b:.1f}s | {info["width"]}x{info["height"]}',font=small,fill=(250,218,94))
  times=[a+(b-a)*i/11 for i in range(12)]
  for j,t in enumerate(times):
   tmp=f'/tmp/ep14_cut_{vid}_{j}.jpg';cmd=[FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',f'{ROOT}/{vid}/{vid}.mp4']
   if crop:cmd+=['-vf',crop]
   cmd+=['-frames:v','1',tmp];subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(TW,TH+18),(4,5,8))
   if os.path.exists(tmp):
    im=Image.open(tmp).convert('RGB');im.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(im,((TW-im.width)//2,(TH-im.height)//2))
   ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white');x=G+(j%COLS)*(TW+G);y=base+15+(j//COLS)*(TH+23);c.paste(tile,(x,y))
 out=f'{OUT}/EP14_EP15_cut_window_group{gi}.jpg';c.save(out,quality=91);print(out)
