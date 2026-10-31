import os,subprocess,io,sys,glob,math
from PIL import Image,ImageDraw
import imageio_ffmpeg
sys.path.insert(0,'/home/user/studio');from util import probe
FF=imageio_ffmpeg.get_ffmpeg_exe(); root='/home/user/dl/src/ep33_34_candidates'
ids=['V4nMZ526wAw','SVvmsBpxhaY','8a9ne-ABev0','5kSzTZe5jj4','e8f5U_M9O0c','n1Y43D-fqwo','ok-I1AoXDKk']
for ident in ids:
 p=f'{root}/{ident}.mp4';info=probe(p);dur=info['duration'];step=.5 if dur<12 else .75;ts=[round(i*step,2) for i in range(int(dur/step)+1) if i*step<dur]
 cw,ch=180,160;cols=6;rows=math.ceil(len(ts)/cols);out=Image.new('RGB',(cols*cw,rows*ch+24),(12,12,12));d=ImageDraw.Draw(out);d.text((4,2),f'{ident} {dur:.2f}s | {info["width"]}x{info["height"]}',fill='white')
 for i,t in enumerate(ts):
  r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',p,'-frames:v','1','-vf','scale=180:130:force_original_aspect_ratio=decrease,pad=180:130:(ow-iw)/2:(oh-ih)/2:color=black','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)).convert('RGB');x=(i%cols)*cw;y=24+(i//cols)*ch;out.paste(im,(x,y));d.text((x+2,y+134),f'{t:.1f}s',fill='yellow')
 out.save(f'/home/user/studio/type2/detail_{ident}.jpg',quality=88)
 print(ident,len(ts),out.size)
