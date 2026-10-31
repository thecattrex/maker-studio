import os,subprocess,io
from PIL import Image,ImageDraw
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
items=[
 ('EP31 tube: ZPSQ95cwR9A',['/home/user/dl/src/ep31_32_candidates/ZPSQ95cwR9A.mp4'],[0.0,1.5,3.5,4.8,5.4]),
 ('EP31 checkered: x9vknx8',['/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4'],[9.5,10.4,11.4,12.4,13.0]),
 ('EP31 ice fishing: x9vknx8',['/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4'],[22.0,23.0,24.0,25.0,26.2]),
 ('EP31 icy stairs: x9vknx8',['/home/user/dl/src/ep31_32_candidates/x9vknx8.mp4'],[46.0,47.0,48.0,49.0,50.2]),
 ('EP32 stepping stones: CkE5',['/home/user/dl/src/ep31_32_candidates/CkE5ZDeXKw0.mp4'],[3.5,4.5,5.5,6.5,7.4]),
 ('EP32 muddy puddle: cUy',['/home/user/dl/src/ep31_32_candidates/cUyKOmxgOOo.mp4'],[6.0,7.0,8.0,9.0,10.0]),
 ('EP32 wave splash: x9qcpns',['/home/user/dl/src/ep31_32_candidates/x9qcpns.mp4'],[110.0,111.5,113.0,114.5,115.0]),
 ('EP32 paddleboard: x9qcpns',['/home/user/dl/src/ep31_32_candidates/x9qcpns.mp4'],[212.0,213.5,215.0,216.5,218.0]),
 ('EP32 pool-entry: YFOd',['/home/user/dl/src/ep31_32_candidates/YFOdUHuUEf4.mp4'],[0.1,1.5,3.0,4.5,6.0]),
]
W=1000; cellw=200; cellh=180; out=Image.new('RGB',(W,len(items)*cellh),(16,16,16));d=ImageDraw.Draw(out)
for r,(title,plist,ts) in enumerate(items):
 p=plist[0]; y=r*cellh; d.text((5,y+2),title,fill='white')
 for i,t in enumerate(ts):
  z=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',p,'-frames:v','1','-vf','scale=200:150:force_original_aspect_ratio=decrease,pad=200:150:(ow-iw)/2:(oh-ih)/2:color=black','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if z.stdout:
   im=Image.open(io.BytesIO(z.stdout)).convert('RGB'); out.paste(im,(i*cellw,y+20))
  d.text((i*cellw,y+173),f'{t:.1f}s',fill='yellow')
out.save('/home/user/studio/type2/EP31_EP32_proposed_detail2.jpg',quality=90)
print(out.size)
