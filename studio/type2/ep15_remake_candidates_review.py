#!/usr/bin/env python3
import os,sys,subprocess,math
sys.path.insert(0,'/home/user/studio');from util import probe,ensure_ffmpeg
from PIL import Image,ImageDraw,ImageFont
ROOT='/home/user/dl/src/ep15_remake_candidates';OUT='/home/user/studio/type2';FF=ensure_ffmpeg();IDS=['xbid4im','x9y7rwe','x9ejedo','x9y52lk','x9m3tj6','xakvkte','x9wy8kc','x9si5ze','x9weqas','xamvx3y','x9uf2f6','xa67tce','xb1a01a','xayplh6','xbglpb6','xa3ft5g','xa123a8']
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);sm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
W,H,G=190,250,7
for g in range(5):
 group=IDS[g*4:g*4+4];sheet=Image.new('RGB',(4*(W+G)+G,len(group)*(H+44)+50),(10,14,24));d=ImageDraw.Draw(sheet);d.text((G,8),f'EP15 remake screening • samples in proposed 4:5 center crop • group {g+1}',font=font,fill='white')
 for r,id in enumerate(group):
  p=f'{ROOT}/{id}/{id}.mp4';info=probe(p);w,h=info['width'],info['height'];ratio=1080/1428
  if w/h>ratio: ch=h;cw=int(round(h*ratio))
  else: cw=w;ch=int(round(w/ratio))
  cy=max(0,(h-ch)//2);cx=max(0,(w-cw)//2);base=35+r*(H+44)
  d.text((G,base),f'{id} | {info["duration"]:.2f}s | audio={info["has_audio"]} | crop {cx},{cy},{cw},{ch}',font=sm,fill=(250,218,94))
  for j,t in enumerate([0.08,info['duration']*.2,info['duration']*.4,info['duration']*.6,info['duration']*.8,max(0.1,info['duration']-.12)]):
   tmp=f'/tmp/remake_{id}_{j}.jpg';vf=f'crop={cw}:{ch}:{cx}:{cy}'
   subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',f'{t:.3f}','-i',p,'-vf',vf,'-frames:v','1',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   tile=Image.new('RGB',(W,H+18),(4,5,8))
   if os.path.exists(tmp):
    im=Image.open(tmp).convert('RGB');im.thumbnail((W,H),Image.Resampling.LANCZOS);tile.paste(im,((W-im.width)//2,(H-im.height)//2))
   ImageDraw.Draw(tile).text((3,H+3),f'{t:.1f}s',font=sm,fill='white');sheet.paste(tile,(G+j*(W+G),base+16))
 out=f'{OUT}/EP15_remake_candidate_group{g+1}.jpg';sheet.save(out,quality=92);print(out)
