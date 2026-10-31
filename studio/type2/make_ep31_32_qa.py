import subprocess,io,os,json
from PIL import Image,ImageDraw
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); outdir='/home/user/studio/out'; root='/home/user/studio/type2'
for ep in (31,32):
 p=f'{outdir}/EP{ep}_Type2_Final_EP29Style_2026-10-29.mp4'; m=json.load(open(f'{root}/EP{ep}_source_manifest.json')); clips=m['clips']
 cw,ch=360,640; cols=3; rows=4; sheet=Image.new('RGB',(cols*cw,rows*ch),(12,12,12)); d=ImageDraw.Draw(sheet)
 for i,c in enumerate(clips):
  a=c['timeline_start'];b=c['timeline_end'];ts=[a+min(.45,(b-a)*.12),(a+b)/2,b-.13]
  for j,t in enumerate(ts):
   r=subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',str(t),'-i',p,'-frames:v','1','-vf',f'scale={cw}:{ch}:flags=lanczos','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   if r.stdout:
    im=Image.open(io.BytesIO(r.stdout)).convert('RGB');sheet.paste(im,(j*cw,i*ch))
   d.text((j*cw+8,i*ch+8),f'{c["rank"]}: {c["label"]} | {t:.2f}s',fill='yellow',stroke_width=2,stroke_fill='black')
 pathout=f'{root}/EP{ep}_final_QA_sheet.jpg';sheet.save(pathout,quality=92);print(pathout)
