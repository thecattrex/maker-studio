import subprocess,io
from PIL import Image,ImageDraw
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe();root='/home/user/dl/src/ep33_34_candidates'
clips=[
('EP33 #4 CHAIR FALL','SVvmsBpxhaY.mp4',0.0,5.6,(0,128,576,768),[0,1.2,3.0,4.6,5.5]),
('EP33 #3 GYM MAT','8a9ne-ABev0.mp4',3.2,7.2,(0,160,720,960),[3.2,4.1,5.2,6.4,7.2]),
('EP33 #2 SNOW TUBE','wrylswYMWhE.mp4',6.4,9.7,(0,240,1080,1440),[6.4,7.2,8.0,9.0,9.7]),
('EP33 #1 OBSTACLE COURSE','5kSzTZe5jj4.mp4',10.0,14.2,(0,320,1440,1920),[10.0,11.0,12.0,13.0,14.2]),
('EP34 #4 MUD RUN','n1Y43D-fqwo.mp4',5.2,8.6,(0,160,720,960),[5.2,6.0,7.0,8.0,8.6]),
('EP34 #3 MUD HILL','VVJOJTud5BI.mp4',22.0,26.2,(0,80,352,469),[22.0,23.0,24.0,25.0,26.2]),
('EP34 #2 WATER SLIDE','e8f5U_M9O0c.mp4',0.0,5.1,(0,200,1080,1440),[0.0,0.8,1.8,3.2,5.1]),
('EP34 #1 ROPE SWING','ok-I1AoXDKk.mp4',1.0,5.7,(0,400,2160,2880),[1.0,2.0,3.0,4.5,5.7]),
]
cw,ch=200,180;out=Image.new('RGB',(cw*5,ch*len(clips)),(12,12,12));d=ImageDraw.Draw(out)
for r,(title,filename,ss,end,crop,ts) in enumerate(clips):
 path=f'{root}/{filename}';x0,y0=0,r*ch;d.text((4,y0+2),title,fill='white')
 x,y,w,h=crop
 for j,t in enumerate(ts):
  proc=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',path,'-frames:v','1','-vf',f'crop={w}:{h}:{x}:{y},scale=200:150:flags=lanczos','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if proc.stdout:
   im=Image.open(io.BytesIO(proc.stdout)).convert('RGB');out.paste(im,(j*cw,y0+20))
  d.text((j*cw+2,y0+160),f'{t:.1f}s',fill='yellow')
out.save('/home/user/studio/type2/EP33_EP34_crop_review.jpg',quality=90);print(out.size)
