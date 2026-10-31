import os,glob,sys,subprocess,io
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
sys.path.insert(0,'/home/user/studio')
from util import probe
FF=imageio_ffmpeg.get_ffmpeg_exe(); ROOT='/home/user/dl/src/ep31_32_candidates'
files=[]
for p in sorted(glob.glob(ROOT+'/*.mp4')):
 name=os.path.basename(p)
 if name in ['x9fe7ig.mp4','x7v1dc7.mp4'] or name.startswith('YFOdUHuUEf4.f137'): continue
 try: info=probe(p)
 except: continue
 if info['duration']>220: continue
 files.append((p,info))
cellw,cellh=240,190
cols=4; rows=(len(files)+cols-1)//cols
out=Image.new('RGB',(cols*cellw,rows*cellh),(18,18,18)); d=ImageDraw.Draw(out)
for idx,(p,info) in enumerate(files):
 x=(idx%cols)*cellw;y=(idx//cols)*cellh
 name=os.path.basename(p).replace('.mp4','')
 d.text((x+4,y+2),f'{name}  {info["duration"]:.1f}s',fill='white')
 ts=[info['duration']*.18,info['duration']*.50,info['duration']*.82]
 for j,t in enumerate(ts):
  r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',p,'-frames:v','1','-vf','scale=76:140:force_original_aspect_ratio=decrease,pad=76:140:(ow-iw)/2:(oh-ih)/2:color=black','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)).convert('RGB'); out.paste(im,(x+4+j*78,y+26))
   d.text((x+4+j*78,y+168),f'{t:.1f}s',fill='yellow')
out.save('/home/user/studio/type2/EP31_32_candidate_overview.jpg',quality=88)
print(len(files),out.size)
