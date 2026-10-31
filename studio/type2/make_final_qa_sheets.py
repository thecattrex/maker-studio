from PIL import Image,ImageDraw,ImageFont
import subprocess,os,math,sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();OUT='/home/user/studio/type2';TMP='/tmp/type2_final_qa';os.makedirs(TMP,exist_ok=True)
DATA={
 'EP10':('/home/user/dl/EP10_Type2_Final_2026-10-28.mp4',[
  ('#4 CONE RUN TRIP',0.00,4.60),('#3 ICY STEP SLIP',4.76,2.70),
  ('#2 PULL-UP BAR FAIL',7.62,5.20),('#1 YARD TUMBLE',12.98,4.80)]),
 'EP11':('/home/user/dl/EP11_Type2_Final_2026-10-28.mp4',[
  ('#4 RAINY PATH SLIP',0.00,4.40),('#3 RINK STUMBLE',4.56,4.80),
  ('#2 POOL EDGE FALL',9.52,5.50),('#1 ZIPLINE WIPEOUT',15.18,6.90)])}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
for ep,(vid,clips) in DATA.items():
 info=probe(vid);print(ep,info)
 cols=12;cw,ch=162,288;gap=7;head=42;label_h=27;row_h=ch+label_h+gap
 canv=Image.new('RGB',(cols*(cw+gap)+14,head+len(clips)*row_h+12),(12,15,22));d=ImageDraw.Draw(canv)
 d.text((12,11),f'{ep} fresh final | {info["duration"]:.2f}s | 30fps | dense visual QC (not audio listening)',font=font,fill='white')
 for r,(label,start,dur) in enumerate(clips):
  y0=head+r*row_h
  d.text((12,y0),label,font=small,fill='#f0d36a')
  y=y0+label_h
  ts=[start+0.12+(dur-0.24)*i/(cols-1) for i in range(cols)]
  for i,t in enumerate(ts):
   p=f'{TMP}/{ep}_{r}_{i}.jpg'
   subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-ss',f'{t:.3f}','-i',vid,'-frames:v','1','-vf',f'scale={cw}:{ch}:flags=lanczos',p],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   x=7+i*(cw+gap)
   if os.path.exists(p):
    im=Image.open(p).convert('RGB');canv.paste(im,(x,y));d.text((x+3,y+ch-17),f'{t:.2f}',font=small,fill='white')
   else:d.rectangle((x,y,x+cw,y+ch),fill='#222')
 out=f'{OUT}/{ep}_final_2026-10-28_dense_QA.jpg';canv.save(out,quality=92);print(out)
