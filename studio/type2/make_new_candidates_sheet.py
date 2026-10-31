import sys,os,subprocess,tempfile,math
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ids=['7171238283438198062','7507352685969050926','7449358724952624417','7542922954640805142','7484411214404144414','7488031370086780190','7500269399866182942','7525273978169085215','7574125669496474893','7580687852028103967','7505158573698338094','7432405164033658154','7429454352235892010']
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15)
for batch in range(2):
 chunk=ids[batch*7:(batch+1)*7];framesets=[]
 for id in chunk:
  p=f'/home/user/dl/src/tiktok/tt_{id}.mp4';d=probe(p)['duration'];ts=[round((d-.1)*i/7,2) for i in range(8)];frames=[]
  with tempfile.TemporaryDirectory() as td:
   for i,t in enumerate(ts):
    f=f'{td}/{i}.jpg';subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',p,'-frames:v','1','-q:v','4',f],check=True)
    im=Image.open(f).convert('RGB');im.thumbnail((178,316));frames.append((im,t))
  framesets.append((id,d,frames))
 W=8*188+20;H=len(chunk)*352+20;out=Image.new('RGB',(W,H),'#111');draw=ImageDraw.Draw(out)
 for r,(id,d,frames) in enumerate(framesets):
  y=10+r*352;draw.text((8,y),f'{id} | {d:.1f}s',font=font,fill='#ffe066')
  for c,(im,t) in enumerate(frames):
   x=10+c*188;out.paste(im,(x,y+21));draw.text((x,y+338),f'{t:.1f}s',font=font,fill='white')
 op=f'/home/user/studio/type2/new_pool_batch{batch+1}.jpg';out.save(op,quality=88);print(op)
