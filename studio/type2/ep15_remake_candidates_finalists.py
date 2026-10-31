#!/usr/bin/env python3
import os,sys,subprocess,math
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
from PIL import Image,ImageDraw,ImageFont
FF=ensure_ffmpeg();ROOT='/home/user/dl/src/ep15_remake_candidates';OUT='/home/user/studio/type2';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11);W,H,G=190,250,6
IDS=['xbglpb6','x9bi13o','x95yj4a']
for g in range(1):
 group=IDS;sheet=Image.new('RGB',(4*(W+G)+G,len(group)*(H+44)+50),(10,14,24));d=ImageDraw.Draw(sheet);d.text((G,8),'EP15 remake finalist screen • full source across proposed 4:5 crop',font=font,fill='white')
 for r,id in enumerate(group):
  p=f'{ROOT}/{id}/{id}.mp4';info=probe(p);w,h=info['width'],info['height'];ratio=1080/1428
  if w/h>ratio:ch=h;cw=round(h*ratio)
  else:cw=w;ch=round(w/ratio)
  cx=(w-cw)//2;cy=(h-ch)//2;base=35+r*(H+44);d.text((G,base),f'{id} | {info["duration"]:.2f}s | audio={info["has_audio"]} | crop {cx},{cy},{cw},{ch}',font=sm,fill=(250,218,94))
  ts=[0.1,info['duration']*.2,info['duration']*.4,info['duration']*.6,info['duration']*.8,info['duration']-.1]
  for j,t in enumerate(ts):
   tmp=f'/tmp/ep15_fin_{id}_{j}.jpg';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(t),'-i',p,'-vf',f'crop={cw}:{ch}:{cx}:{cy}','-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);tile=Image.new('RGB',(W,H+18),(4,5,8))
   if os.path.exists(tmp):
    im=Image.open(tmp).convert('RGB');im.thumbnail((W,H),Image.Resampling.LANCZOS);tile.paste(im,((W-im.width)//2,(H-im.height)//2))
   ImageDraw.Draw(tile).text((3,H+3),f'{t:.1f}s',font=sm,fill='white');sheet.paste(tile,(G+j*(W+G),base+16))
out=f'{OUT}/EP15_remake_finalist_screen.jpg';sheet.save(out,quality=92);print(out)
