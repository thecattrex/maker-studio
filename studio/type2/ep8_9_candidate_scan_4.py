import os,subprocess,math,sys
sys.path.insert(0,'/home/user/studio');from util import probe
from PIL import Image,ImageDraw,ImageFont
base='/home/user/dl/src/tiktok'; out='/home/user/studio/type2/ep8_9_candidate_scan_4.jpg'
ids=['7583500055944891678','7294317549473238314','7401261275373735211','7421290638873873706','7483668217068555551','7489504031984012590','7522215425824820510','7539729192255065366','7437277242612337966','7442854366744153375','7438851725764889902','7564894911040916791']
ff='/tmp/vidtools/ffmpeg'; font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; f=ImageFont.truetype(font,17);sm=ImageFont.truetype(font,14)
W=1500; tw=230; th=220; gap=10; cols=6; rows=math.ceil(len(ids)/2); H=55+rows*(th+55+gap)
im=Image.new('RGB',(W,H),(12,15,23));d=ImageDraw.Draw(im);d.text((18,15),'EP8–EP9 candidates • 3 sampled frames each • ID last 6 digits',font=f,fill='white')
for i,id in enumerate(ids):
 p=f'{base}/tt_{id}.mp4'; dur=probe(p)['duration']
 x=12+(i%cols)*(tw+gap); y=48+(i//cols)*(th+55+gap)
 d.text((x,y),f'...{id[-6:]} ({dur:.1f}s)',font=sm,fill=(255,255,255))
 for j,t in enumerate([dur*.2,dur*.5,dur*.8]):
  tmp=f'/tmp/cand4_{id}_{j}.jpg';subprocess.run([ff,'-hide_banner','-v','error','-y','-ss',str(t),'-i',p,'-frames:v','1',tmp],capture_output=True)
  box=Image.new('RGB',(tw//3,th),(0,0,0))
  if os.path.exists(tmp) and os.path.getsize(tmp)>100:
   src=Image.open(tmp).convert('RGB');src.thumbnail(box.size,Image.Resampling.LANCZOS);box.paste(src,((box.width-src.width)//2,(box.height-src.height)//2))
  xx=x+j*(tw//3);im.paste(box,(xx,y+24));d.text((xx+4,y+th+26),f'{t:.1f}',font=sm,fill=(180,190,205))
im.save(out,quality=90);print(out)
