import os,subprocess,json,re
from pathlib import Path
import numpy as np,soundfile as sf,torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
ROOT=Path('/home/user/studio/type2/assets/ep7');A=ROOT/'audio';V=ROOT/'video';FF='/tmp/vidtools/ffmpeg'
items=[
 dict(n=3,key='track_wipeout',src='/home/user/dl/src/youtube/ep7/martin_wheelie_ZPNKBNSdJoE.mp4',ss=17.0,dur=3.15,crop_y=35,label='TRACK TUMBLE'),
 dict(n=4,key='outdoor_slip',src='/home/user/dl/src/tiktok/tt_7494033019607551275.mp4',ss=5.2,dur=3.15,crop_y=200,label='MUDDY MISSTEP'),
 dict(n=5,key='treadmill',src='/home/user/dl/src/tiktok/tt_7420821555338317088.mp4',ss=0.6,dur=3.15,crop_y=230,label='TREADMILL SLIP'),
]
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode: raise RuntimeError((r.stderr or '')[-2500:])
 return r
os.environ['OMP_NUM_THREADS']='4';torch.set_num_threads(4)
model=get_model('htdemucs');model.cpu().eval()
for it in items:
 raw=A/f"{it['key']}_raw.wav"
 run([FF,'-hide_banner','-v','error','-y','-ss',str(it['ss']),'-i',it['src'],'-t',str(it['dur']),'-vn','-ac','2','-ar','44100','-c:a','pcm_s16le',str(raw)])
 audio,sr=sf.read(raw,dtype='float32',always_2d=True); n=round(it['dur']*sr)
 if len(audio)<n:audio=np.pad(audio,((0,n-len(audio)),(0,0)))
 audio=audio[:n];wav=torch.from_numpy(audio.T.copy());mean=wav.mean();std=wav.mean(0).std();wav=(wav-mean)/(std+1e-8)
 with torch.inference_mode():pred=apply_model(model,wav[None],device='cpu',shifts=0,split=True,overlap=.25,progress=False)[0]
 pred=pred*std+mean;vocals=pred[model.sources.index('vocals')].cpu().numpy().T
 s44=A/f"{it['key']}_vocals_44100.wav";sf.write(s44,vocals,sr,subtype='PCM_16')
 s48=A/f"{it['key']}_vocals.wav";run([FF,'-hide_banner','-v','error','-y','-i',str(s44),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(s48)])
 info=subprocess.run([FF,'-hide_banner','-i',it['src']],capture_output=True,text=True);m=re.search(r'Video:.*?(\d{2,5})x(\d{2,5})',info.stderr,re.S);sw,sh=map(int,m.groups());ch=round(sw*1428/1080);cy=it['crop_y']
 video=V/f"{it['n']}_{it['key']}.mp4";vf=f'crop={sw}:{ch}:0:{cy},scale=1080:1428:flags=lanczos,fps=30,setsar=1,format=yuv420p'
 run([FF,'-hide_banner','-v','error','-y','-ss',str(it['ss']),'-i',it['src'],'-t',str(it['dur']),'-vf',vf,'-an','-c:v','libx264','-preset','medium','-crf','17','-r','30','-movflags','+faststart',str(video)])
 print(f"DONE {it['key']} video={video} audio={s48} crop y={cy}/{sh-ch}")
