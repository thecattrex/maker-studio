import subprocess,io,os
from PIL import Image,ImageDraw
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
clips=[
('EP31 #4 ICY STAIRS', '/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4',46.5,50.4,(0,100,480,636)),
('EP31 #3 CHECKERED SLIP','/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4',9.7,13.5,(0,100,480,636)),
('EP31 #2 ICE WALKER','/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4',22.0,26.6,(0,100,480,636)),
('EP31 #1 SNOW TUBE','/home/user/dl/src/ep31_32_candidates/ZPSQ95cwR9A.mp4',0.0,5.5,(400,0,544,720)),
('EP32 #4 STONE SPLASH','/home/user/dl/src/ep31_32_candidates/CkE5ZDeXKw0.mp4',3.5,7.5,(0,100,1080,1440)),
('EP32 #3 MUD PUDDLE','/home/user/dl/src/ep31_32_candidates/cUyKOmxgOOo.mp4',6.3,9.9,(0,160,720,960)),
('EP32 #2 ROPE SWING','/home/user/dl/src/ep31_32_candidates/xas342m.mp4',0.2,5.9,(0,80,480,636)),
('EP32 #1 PADDLEBOARD','/home/user/dl/src/ep31_32_candidates/x9qcpns.mp4',212.7,217.2,(290,0,270,360)),
]
cols=5; cw=200; ch=180; out=Image.new('RGB',(cols*cw,len(clips)*ch),(16,16,16)); d=ImageDraw.Draw(out)
for row,(title,path,a,b,crop) in enumerate(clips):
 x0,y0=0,row*ch; d.text((4,y0+2),title,fill='white'); n=5
 for j in range(n):
  t=a+(b-a)*j/(n-1); x,y,w,h=crop
  vf=f'crop={w}:{h}:{x}:{y},scale=200:150:flags=lanczos'
  r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',path,'-frames:v','1','-vf',vf,'-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)).convert('RGB'); out.paste(im,(j*cw,y0+20))
  d.text((j*cw+4,y0+160),f'{t:.2f}',fill='yellow')
out.save('/home/user/studio/type2/EP31_EP32_crop_review.jpg',quality=90)
print(out.size)
