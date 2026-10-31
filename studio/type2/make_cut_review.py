from PIL import Image,ImageDraw,ImageFont
import subprocess,os,math,sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg(); OUT='/home/user/studio/type2'; TEMP='/tmp/type2_crop_review';os.makedirs(TEMP,exist_ok=True)
items={
 'EP10':[
  ('rain slip','/home/user/dl/src/dailymotion_more/xbe8qie.mp4',0.2,4.0,'crop=480:635:0:70'),
  ('icy steps','/home/user/dl/src/dailymotion_more/x9t3594.mp4',0.3,3.8,'crop=720:952:600:64'),
  ('pull-up bar','/home/user/dl/src/dailymotion_more/x9i49e6.mp4',6.5,5.7,'crop=680:899:0:270'),
  ('yard tumble','/home/user/dl/src/dailymotion_more/xapnfqm.mp4',0.0,6.5,'crop=1080:1428:0:250'),
 ],
 'EP11':[
  ('cone trip','/home/user/dl/src/dailymotion_more/xbgrqde.mp4',1.4,5.0,'crop=480:635:0:150'),
  ('rink stumble','/home/user/dl/src/tiktok/tt_7488031370086780190.mp4',0.0,8.6,'crop=1080:1428:0:0'),
  ('water plunge','/home/user/dl/src/tiktok/tt_7507692898574552342.mp4',8.4,6.0,'crop=850:1124:115:450'),
  ('zipline sand','/home/user/dl/src/dailymotion_more/x9uf2f6.mp4',0.0,8.5,'crop=2160:2856:0:600'),
 ]
}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
for ep,clips in items.items():
 cols=10;cw,ch=160,212;gap=8; title_h=45; row_h=ch+30
 canv=Image.new('RGB',(cols*(cw+gap)+12,title_h+len(clips)*row_h+12),(13,16,24));d=ImageDraw.Draw(canv);d.text((12,12),ep+' crop/window review (dense samples; visual only)',font=font,fill='white')
 for r,(name,path,ss,dur,crop) in enumerate(clips):
  try:info=probe(path)
  except Exception as e:print('bad',path,e);continue
  # for rink full source use 10 samples over time, others across window
  if name=='rink stumble': ts=[0.2,1.0,1.7,2.4,3.1,3.8,4.5,5.2,6.0,7.0]
  else:ts=[ss+dur*i/9 for i in range(10)]
  d.text((12,title_h+r*row_h),name+' | '+os.path.basename(path),font=small,fill='#efce62')
  y0=title_h+r*row_h+20
  for i,t in enumerate(ts):
   tmp=f'{TEMP}/{ep}_{r}_{i}.jpg';vf=f'{crop},scale={cw}:{ch}:flags=lanczos'
   cmd=[FF,'-hide_banner','-loglevel','error','-y','-ss',f'{t:.3f}','-i',path,'-frames:v','1','-vf',vf,tmp]
   subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   x=12+i*(cw+gap)
   if os.path.exists(tmp):
    im=Image.open(tmp).convert('RGB');canv.paste(im,(x,y0));d.text((x+3,y0+ch-18),f'{t:.1f}s',font=small,fill='white')
   else: d.rectangle((x,y0,x+cw,y0+ch),fill='#222')
 canv.save(f'{OUT}/{ep}_new_cut_review.jpg',quality=92);print(f'{OUT}/{ep}_new_cut_review.jpg')
