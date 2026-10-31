import cv2, os, glob
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
files=glob.glob('/home/user/dl/src/tiktok/*.mp4')+['/home/user/dl/src/imgur/b0wKmlw.mp4']
# selected promising and potentially clean/clear
sel=['7439407416669654315','7464381359377616170']
font=ImageFont.load_default()
for id in sel:
 p=next((x for x in files if id in x),None)
 if not p: continue
 cap=cv2.VideoCapture(p); fps=cap.get(cv2.CAP_PROP_FPS) or 30; n=cap.get(cv2.CAP_PROP_FRAME_COUNT); dur=n/fps
 step=.5 if dur<25 else 1.0
 times=[]; t=0
 while t<dur:
  times.append(t); t+=step
 thumbs=[]
 for t in times:
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,frame=cap.read()
  if not ok: continue
  h,w=frame.shape[:2]; tw=180; th=round(h*tw/w)
  im=Image.fromarray(cv2.cvtColor(cv2.resize(frame,(tw,th)),cv2.COLOR_BGR2RGB))
  # set exact tile height to 280 max incl label
  im.thumbnail((180,245))
  tile=Image.new('RGB',(190,280),'#101319'); tile.paste(im,((190-im.width)//2,5))
  d=ImageDraw.Draw(tile); d.text((6,255),f'{t:.1f}s',font=font,fill='white')
  thumbs.append(tile)
 cap.release()
 cols=8; rows=(len(thumbs)+cols-1)//cols
 sheet=Image.new('RGB',(cols*190,rows*280),'#101319'); d=ImageDraw.Draw(sheet)
 d.text((8,2),f'{id} • {dur:.1f}s • frames every {step}s',font=font,fill='#f6d354')
 for i,im in enumerate(thumbs): sheet.paste(im,((i%cols)*190,(i//cols)*280+18))
 sheet.save(f'/home/user/studio/type2/fullscan_{id}.jpg',quality=90)
 print(id,p,dur,len(thumbs))
