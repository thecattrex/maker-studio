import os,subprocess,io,sys
from PIL import Image,ImageDraw
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
items=[
 ('EP31 tube: ZPSQ95cwR9A.mp4', '/home/user/dl/src/ep31_32_candidates/ZPSQ95cwR9A.mp4', [0.0,1.0,2.0,3.0,4.0,4.8,5.2,5.5]),
 ('EP31 checkered: x9vknx8.mp4', '/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4', [9.5,10.0,10.5,11.0,11.5,12.0,12.5,13.0]),
 ('EP31 ice fishing: x9vknx8.mp4', '/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4', [22.0,22.6,23.2,23.8,24.4,25.0,25.6,26.2,26.6]),
 ('EP31 stairs: x9vknx8.mp4', '/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4', [46.0,46.6,47.2,47.8,48.4,49.0,49.6,50.2]),
 ('EP32 stepping stones: CkE5ZDeXKw0.mp4', '/home/user/dl/src/ep31_32_candidates/CkE5ZDeXKw0.mp4', [3.5,4.1,4.7,5.3,5.9,6.5,7.1,7.6]),
 ('EP32 muddy splash: cUyKOmxgOOo.mp4', '/home/user/dl/src/ep31_32_candidates/cUyKOmxgOOo.mp4', [6.0,6.6,7.2,7.8,8.4,9.0,9.6,10.1]),
 ('EP32 wave splash: x9qcpns.mp4', '/home/user/dl/src/ep31_32_candidates/x9qcpns.mp4', [110.5,111.2,111.9,112.6,113.3,114.0,114.7,115.0]),
 ('EP32 paddleboard: x9qcpns.mp4', '/home/user/dl/src/ep31_32_candidates/x9qcpns.mp4', [212.0,212.7,213.4,214.1,214.8,215.5,216.2,216.9,217.6,218.0]),
 ('EP32 pool entry: YFOdUHuUEf4.mp4', '/home/user/dl/src/ep31_32_candidates/YFOdUHuUEf4.mp4', [0.3,0.9,1.5,2.1,2.7,3.3,3.9,4.5,5.1,5.7,6.3,6.9,7.5]),
]
cellw,cellh=210,180; cols=5; rows=sum((len(ts)+cols-1)//cols for _,_,ts in items)
out=Image.new('RGB',(cols*cellw,rows*cellh),(18,18,18)); d=ImageDraw.Draw(out); row=0
for title,path,ts in items:
 d.text((4,row*cellh+2),title,fill='white'); idx=0
 for t in ts:
  x=(idx%cols)*cellw; y=row*cellh+22+(idx//cols)*0 # item row per 5 frames
  r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',path,'-frames:v','1','-vf','scale=200:145:force_original_aspect_ratio=decrease,pad=200:145:(ow-iw)/2:(oh-ih)/2:color=black','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)).convert('RGB'); out.paste(im,(x+5,y+18))
   d.text((x+5,y+164),f'{t:.1f}s',fill='yellow')
  idx+=1
 row+=(len(ts)+cols-1)//cols
out.save('/home/user/studio/type2/EP31_EP32_proposed_detail.jpg',quality=90)
print(out.size,rows)
