import cv2,os,glob
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
base=Path('/home/user'); out=base/'studio/type2'; W=1650; cardh=330; gap=18; items=[
('R1 • MOTOGP GRID FALL','Morbidelli before lights-out',base/'dl/src/youtube/ep7/morbidelli_kxsdIyuAFR0.mp4'),
('R2 • MOTOGP WRONG BIKE','Ortola grabs Nepa’s bike',base/'dl/src/youtube/ep7/ortola_pYbW8hBkQgs.mp4'),
('R3 • MOTOGP PADDOCK FALL','Aldeguer paddock crash',base/'dl/src/youtube/ep7/aldeguer_pIuwntprK3A.mp4'),
('R4 • MOTOGP WHEELIE FALL','Martin celebration goes wrong',base/'dl/src/youtube/ep7/martin_wheelie_ZPNKBNSdJoE.mp4'),
('F1 • TREADMILL FAIL','Shirley',base/'dl/src/tiktok/tt_7420821555338317088.mp4'),
('F2 • OUTDOOR SLIP','AFV Official',base/'dl/src/tiktok/tt_7494033019607551275.mp4'),
]
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; f1=ImageFont.truetype(font,24); f2=ImageFont.truetype(font,18)
H=70+len(items)*(cardh+gap); im=Image.new('RGB',(W,H),(13,16,24)); d=ImageDraw.Draw(im); d.text((25,20),'EP7 • ROAD-RACING SOURCE SCREEN',font=ImageFont.truetype(font,30),fill='white')
for i,(a,b,p) in enumerate(items):
 y=70+i*(cardh+gap); d.rounded_rectangle((18,y,W-18,y+cardh),radius=14,fill=(24,30,42),outline=(55,66,87),width=2); d.text((36,y+12),a+' — '+b,font=f1,fill=(244,247,251))
 cap=cv2.VideoCapture(str(p)); fps=cap.get(cv2.CAP_PROP_FPS) or 30; n=cap.get(cv2.CAP_PROP_FRAME_COUNT); dur=n/fps
 for j,frac in enumerate([.02,.22,.48,.74,.96]):
  t=max(0,min(dur-.05,dur*frac)); cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read(); box=Image.new('RGB',(300,235),(5,6,9))
  if ok:
   src=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)); src.thumbnail((300,235)); box.paste(src,((300-src.width)//2,(235-src.height)//2))
  x=35+j*320; im.paste(box,(x,y+52)); d.rectangle((x,y+52,x+299,y+286),outline=(75,88,112),width=1); d.text((x+5,y+261),f'{t:.1f}s',font=f2,fill=(224,229,239))
 cap.release()
im.save('/home/user/studio/type2/ep7_candidate_scan.jpg',quality=91)
print('saved',H)
