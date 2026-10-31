import os,glob,subprocess,io,sys
from PIL import Image,ImageDraw
import imageio_ffmpeg
sys.path.insert(0,'/home/user/studio');from util import probe
FF=imageio_ffmpeg.get_ffmpeg_exe();root='/home/user/dl/src/ep33_34_candidates'; files=sorted(glob.glob(root+'/*.mp4'))
cw,ch=200,190;cols=4;out=Image.new('RGB',(cols*cw,len(files)*ch),(15,15,15));d=ImageDraw.Draw(out)
for row,p in enumerate(files):
 info=probe(p);dur=info['duration']; ts=[dur*x for x in (.12,.38,.64,.88)]; y=row*ch
 d.text((4,y+2),f'{os.path.basename(p)} {dur:.1f}s',fill='white')
 for i,t in enumerate(ts):
  r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',p,'-frames:v','1','-vf','scale=200:150:force_original_aspect_ratio=decrease,pad=200:150:(ow-iw)/2:(oh-ih)/2:color=black','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)).convert('RGB');x=i*cw;out.paste(im,(x,y+20));d.text((x+3,y+172),f'{t:.1f}s',fill='yellow')
out.save('/home/user/studio/type2/EP33_EP34_candidate_overview.jpg',quality=88)
print(out.size)
