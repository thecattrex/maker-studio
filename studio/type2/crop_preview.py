import cv2, os
from PIL import Image,ImageDraw,ImageFont
# id, crop y, chosen times
items=[
('7471830784375065899',180,[0.5,1.5,2.5,3.5,4.5,5.5]),
('7405391209096645931',210,[17.0,18.5,19.5,20.5,21.5,22.5,24.0]),
('7513747917711346990',500,[0.5,3.5,4.5,5.0,5.5,6.0]),
('7461440642732870954',0,[1.5,3.0,4.0,4.5,5.5,6.5]),
('7456483152454831391',350,[3.5,5.5,7.0,8.0,8.5,9.5,10.5]),
('7429454352235892010',400,[0.5,2.5,3.5,4.5,5.5,6.5]),
('7488031370086780190',0,[1.0,2.5,3.5,4.5,5.5,6.5,7.5,8.0]),
('7507692898574552342',420,[8.5,9.5,10.5,11.5,12.5,13.5,14.5]),
]
font=ImageFont.load_default(); tiles=[]
for id,y,times in items:
 p=f'/home/user/dl/src/tiktok/tt_{id}.mp4'; c=cv2.VideoCapture(p); w=int(c.get(3));h=int(c.get(4)); ch=round(w/0.7563); y=max(0,min(y,h-ch))
 for t in times:
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,bgr=c.read()
  if not ok:continue
  crop=bgr[y:y+ch,0:w]
  im=Image.fromarray(cv2.cvtColor(cv2.resize(crop,(260,344)),cv2.COLOR_BGR2RGB))
  tile=Image.new('RGB',(270,380),'#101319');tile.paste(im,(5,5));d=ImageDraw.Draw(tile);d.text((5,353),f'{id[-6:]} • {t:.1f}s y={y}',font=font,fill='white');tiles.append(tile)
 c.release()
cols=8;rows=(len(tiles)+cols-1)//cols
out=Image.new('RGB',(cols*270,rows*380),'#101319')
for i,im in enumerate(tiles):out.paste(im,((i%cols)*270,(i//cols)*380))
out.save('/home/user/studio/type2/crop_candidate_preview.jpg',quality=90)
