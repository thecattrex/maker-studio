import os,subprocess,math
from PIL import Image,ImageDraw,ImageFont
items=[
('R1_Morbidelli','/home/user/dl/src/youtube/ep7/morbidelli_kxsdIyuAFR0.mp4',42.54),
('R2_Ortola_wrong_bike','/home/user/dl/src/youtube/ep7/ortola_pYbW8hBkQgs.mp4',24.66),
('R3_Aldeguer_paddock','/home/user/dl/src/youtube/ep7/aldeguer_pIuwntprK3A.mp4',27.86),
('R4_Martin_wheelie','/home/user/dl/src/youtube/ep7/martin_wheelie_ZPNKBNSdJoE.mp4',53.94),
('F1_Treadmill','/home/user/dl/src/tiktok/tt_7420821555338317088.mp4',9.54),
('F2_AFV_slip','/home/user/dl/src/tiktok/tt_7494033019607551275.mp4',18.79),
]
ff='/tmp/vidtools/ffmpeg'; out='/home/user/studio/type2'; font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(font,18);small=ImageFont.truetype(font,14)
for name,path,dur in items:
 ts=[0.2+i for i in range(int(dur)) if .2+i<dur-.1]; cols=5; tw=170;th=270;gap=12; rows=math.ceil(len(ts)/cols); H=66+rows*(th+gap);W=cols*(tw+gap)+20
 im=Image.new('RGB',(W,H),(13,16,24));d=ImageDraw.Draw(im);d.text((20,20),name+' • every ~1 second',font=f,fill='white')
 for i,t in enumerate(ts):
  tmp=f'/tmp/dense_{name}_{i}.jpg';subprocess.run([ff,'-hide_banner','-v','error','-y','-ss',str(t),'-i',path,'-frames:v','1',tmp],capture_output=True)
  box=Image.new('RGB',(tw,th),(5,6,9))
  if os.path.exists(tmp) and os.path.getsize(tmp)>100:
   src=Image.open(tmp).convert('RGB');src.thumbnail((tw,th),Image.Resampling.LANCZOS);box.paste(src,((tw-src.width)//2,(th-src.height)//2))
  x=10+(i%cols)*(tw+gap);y=58+(i//cols)*(th+gap);im.paste(box,(x,y));d.rectangle((x,y,x+tw-1,y+th-1),outline=(75,88,112),width=1);d.text((x+6,y+th-22),f'{t:.1f}s',font=small,fill=(245,245,245))
 im.save(os.path.join(out,name+'.jpg'),quality=90)
 print(name,rows,W,H)
