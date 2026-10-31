from PIL import Image, ImageDraw, ImageFont
import subprocess, os, tempfile
FF='/usr/bin/ffmpeg'
if not os.path.exists(FF):
    import sys;sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg;FF=ensure_ffmpeg()
items={
9:([0.25,2.15,4.00,4.67,6.91,9.07,9.63,11.88,14.03,15.43,17.58,19.83],[(0,'tent / #4'),(3,'dad / #3'),(6,'track / #2'),(9,'hoop / #1')]),
10:([0.25,2.60,5.20,5.87,7.80,9.80,10.43,12.50,14.72,16.23,18.00,19.90],[(0,'bowling / #4'),(3,'dock / #3'),(6,'pool table / #2'),(9,'chair / #1')]),
11:([0.25,2.10,4.10,4.77,7.00,9.10,9.73,11.60,13.65,15.13,17.30,19.70],[(0,'beach / #4'),(3,'dog-walk / #3'),(6,'pool flip / #2'),(9,'stairs / #1')]),
}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15)
for ep,(ts,groups) in items.items():
    video=f'/home/user/dl/EP{ep}_Type2_Replacement_Final_v2.mp4'
    frames=[]
    with tempfile.TemporaryDirectory() as td:
        for i,t in enumerate(ts):
            p=f'{td}/f{i}.jpg'
            subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-ss',f'{t:.3f}','-i',video,'-frames:v','1','-q:v','3',p],check=True)
            im=Image.open(p).convert('RGB').resize((324,576))
            frames.append(im)
    W=4*(324+12)+24; H=4*(576+36)+24
    canvas=Image.new('RGB',(W,H),'#111111');d=ImageDraw.Draw(canvas)
    for i,(t,im) in enumerate(zip(ts,frames)):
        r,c=divmod(i,4);x=12+c*(324+12);y=12+r*(576+36)
        canvas.paste(im,(x,y))
        if c==0:
            group=dict(groups)[(i//3)*3]
            d.text((x,y+578),f'{group} | t={t:.2f}',font=font,fill='#ffe066')
        else:d.text((x,y+578),f't={t:.2f}',font=font,fill='#cccccc')
    out=f'/home/user/studio/type2/EP{ep}_replacement_v2_dense_QA.jpg'
    canvas.save(out,quality=90)
    print(out)
