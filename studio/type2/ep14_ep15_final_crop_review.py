#!/usr/bin/env python3
import os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
ROOT='/home/user/dl/src/ep14_15_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(FONT,14);small=ImageFont.truetype(FONT,11);TW,TH,COLS,G=170,220,6,5
# Episode, source start, duration, crop x/y/w/h, on-screen label, SFX placeholder
spec={
'x9um1u0':(14,4.2,4.2,(0,150,480,635),'OVEN CAKE DROP'),
'xa1goko':(14,0.0,4.2,(0,60,480,635),'BOTTLE BURST'),
'xapidry':(14,5.5,8.0,(0,80,480,635),'WATERSLIDE SPILL'),
'xbqy0iy':(14,11.0,5.0,(0,100,480,635),'TRAMPOLINE SPILL'),
'xayt822':(15,2.5,5.3,(289,60,270,357),'BOAT-SIDE TUMBLE'),
'xaolx2e':(15,2.0,6.8,(0,100,480,635),'SAUCE BOTTLE FAIL'),
'x9spdi4':(15,32.0,7.8,(0,60,480,635),'TREADMILL TROUBLE'),
'xbmm542':(15,12.5,8.3,(0,170,480,635),'TRAY FLIP'),
}
for ep in (14,15):
 ids=[v for v,s in spec.items() if s[0]==ep];H=45+len(ids)*2*(TH+22);c=Image.new('RGB',(COLS*(TW+G)+G,H),(10,14,24));d=ImageDraw.Draw(c);d.text((G,10),f'EP{ep} • exact 4:5 production crop preview • frames sampled in proposed trim',font=font,fill='white')
 for r,vid in enumerate(ids):
  e,a,dur,(x,y,w,h),label=spec[vid];info=probe(f'{ROOT}/{vid}/{vid}.mp4');base=45+r*2*(TH+22);d.text((G,base),f'{vid} | {a:.1f}–{a+dur:.1f}s | crop {x},{y},{w},{h} | {label}',font=small,fill=(250,218,94));times=[a+dur*i/11 for i in range(12)]
  for j,t in enumerate(times):
   tmp=f'/tmp/ep14_finalcrop_{vid}_{j}.jpg';cmd=[FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',f'{ROOT}/{vid}/{vid}.mp4','-vf',f'crop={w}:{h}:{x}:{y}','-frames:v','1',tmp];subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(TW,TH+18),(4,5,8))
   if os.path.exists(tmp):
    im=Image.open(tmp).convert('RGB');im.thumbnail((TW,TH),Image.Resampling.LANCZOS);tile.paste(im,((TW-im.width)//2,(TH-im.height)//2))
   ImageDraw.Draw(tile).text((4,TH+3),f'{t:.1f}s',font=small,fill='white');x0=G+(j%COLS)*(TW+G);y0=base+15+(j//COLS)*(TH+22);c.paste(tile,(x0,y0))
 out=f'{OUT}/EP{ep}_final_crop_review.jpg';c.save(out,quality=92);print(out)
