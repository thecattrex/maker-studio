import cv2, os, math
from PIL import Image,ImageDraw,ImageFont
ids=['7500269399866182942','7437277242612337966','7401261275373735211','7432405164033658154','7421290638873873706','7539729192255065366','7505158573698338094','7542922954640805142','7171238283438198062','7483668217068555551','7519307664057208077','7522215425824820510','7525273978169085215','7508981054980607274','7507352685969050926','7294317549473238314','7522708732074052919','7484411214404144414','7564894911040916791']
font=ImageFont.load_default(); tw,th=145,258; labelh=25
for groupno in range(4):
 group=ids[groupno*5:(groupno+1)*5]; tiles=[]; maxcols=10
 for id in group:
  p=f'/home/user/dl/src/tiktok/tt_{id}.mp4'; c=cv2.VideoCapture(p); fps=c.get(cv2.CAP_PROP_FPS) or 30; dur=c.get(cv2.CAP_PROP_FRAME_COUNT)/fps; n=min(10,max(4,int(dur/1.2)))
  times=[(dur-0.4)*i/(n-1) for i in range(n)]; row=[]
  for t in times:
   c.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,b=c.read()
   if not ok: continue
   h,w=b.shape[:2]; scale=min(tw/w,th/h); im=Image.fromarray(cv2.cvtColor(cv2.resize(b,(round(w*scale),round(h*scale))),cv2.COLOR_BGR2RGB)); tile=Image.new('RGB',(tw,th+labelh),'#111318');tile.paste(im,((tw-im.width)//2,0));ImageDraw.Draw(tile).text((3,th+4),f'{t:.1f}s',font=font,fill='white');row.append(tile)
  c.release()
  # Pad each clip to fixed columns
  row += [Image.new('RGB',(tw,th+labelh),'#111318') for _ in range(maxcols-len(row))]
  tiles.append(row)
 canvas=Image.new('RGB',(maxcols*tw,len(group)*(th+labelh+24)),'#111318'); d=ImageDraw.Draw(canvas)
 for r,(id,row) in enumerate(zip(group,tiles)):
  y=r*(th+labelh+24);d.text((3,y),f'{id} • {cv2.VideoCapture(f"/home/user/dl/src/tiktok/tt_{id}.mp4").get(cv2.CAP_PROP_FRAME_COUNT)/max(1,cv2.VideoCapture(f"/home/user/dl/src/tiktok/tt_{id}.mp4").get(cv2.CAP_PROP_FPS)):.1f}s',font=font,fill='#f6d354')
  for j,im in enumerate(row):canvas.paste(im,(j*tw,y+18))
 out=f'/home/user/studio/type2/unseen_group_{groupno+1}.jpg';canvas.save(out,quality=90);print(out)
