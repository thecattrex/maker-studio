#!/usr/bin/env python3
import os, subprocess, json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

ROOT=Path('/home/user/studio/type2'); A=ROOT/'assets/ep7'; V=A/'video'; AD=A/'audio'; FF='/tmp/vidtools/ffmpeg'
# Rank ordering: 1 is finale; per selected source, actual target point + 3.15 s.
items=[
 dict(n=1,key='pack_collision',src='/home/user/dl/src/youtube/ep7/ortola_pYbW8hBkQgs.mp4',ss=0.75,dur=3.15,label='PACK WIPEOUT',color='&H000000FF&',crop_y_frac=.127),
 dict(n=2,key='grid_fall',src='/home/user/dl/src/youtube/ep7/morbidelli_kxsdIyuAFR0.mp4',ss=1.65,dur=3.15,label='GRID MISFIRE',color='&H000011FF&',crop_y_frac=.127),
 dict(n=3,key='paddock_tumble',src='/home/user/dl/src/youtube/ep7/aldeguer_pIuwntprK3A.mp4',ss=0.15,dur=3.15,label='PADDOCK WOBBLE',color='&H0000A5FF&',crop_y_frac=.127),
 dict(n=4,key='box_jump',src='/home/user/dl/src/tiktok/tt_7510338874955156742.mp4',ss=2.65,dur=3.15,label='BOX-JUMP BAIL',color='&H0000D7FF&',crop_y_frac=.104),
 dict(n=5,key='treadmill',src='/home/user/dl/src/tiktok/tt_7420821555338317088.mp4',ss=2.35,dur=3.15,label='TREADMILL SLIP',color='&H00FFFFFF&',crop_y_frac=.178),
]
# video crop ratio = 1080x1428. Crop vertical window preserving width; offset per source chosen to keep action and drop top TikTok caption where applicable.
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode: raise RuntimeError(' '.join(map(str,cmd[:8]))+'\n'+(r.stderr or '')[-2000:])
 return r

# model loads once, CPU inference on the selected audio excerpts only
os.environ['OMP_NUM_THREADS']='4'; torch.set_num_threads(4)
model=get_model('htdemucs'); model.cpu().eval()
reports=[]
for it in items:
 src=it['src']; key=it['key']; dur=it['dur']; ss=it['ss']
 # extract exact source interval as stereo 44.1kHz audio
 raw=AD/f'{key}_raw.wav'
 run([FF,'-hide_banner','-v','error','-y','-ss',f'{ss:.6f}','-i',src,'-t',f'{dur:.6f}','-vn','-ac','2','-ar','44100','-c:a','pcm_s16le',str(raw)])
 audio,sr=sf.read(raw,dtype='float32',always_2d=True)
 n=int(round(dur*sr))
 if len(audio)<n: audio=np.pad(audio,((0,n-len(audio)),(0,0)))
 audio=audio[:n]
 wav=torch.from_numpy(audio.T.copy())
 ref=wav.mean(0); mean=ref.mean(); std=ref.std()
 wav=(wav-mean)/(std+1e-8)
 with torch.inference_mode():
  pred=apply_model(model,wav[None],device='cpu',shifts=0,split=True,overlap=0.25,progress=False)[0]
 pred=pred*std+mean
 vocals=pred[model.sources.index('vocals')].cpu().numpy().T
 # save source vocals only; no backing/instrumental track is carried into the edit
 stem44=AD/f'{key}_vocals_44100.wav'; sf.write(stem44,vocals,sr,subtype='PCM_16')
 stem48=AD/f'{key}_vocals.wav'; run([FF,'-hide_banner','-v','error','-y','-i',str(stem44),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(stem48)])
 # conform visual cut to portrait 1080x1428; no zoom or speed change
 info=subprocess.run([FF,'-hide_banner','-i',src],capture_output=True,text=True)
 import re
 m=re.search(r'Video:.*?(\d{2,5})x(\d{2,5})',info.stderr,re.S); sw,sh=map(int,m.groups())
 ch=round(sw*1428/1080); cy=min(max(0,round((sh-ch)*it['crop_y_frac'])),sh-ch)
 video=V/f"{it['n']}_{key}.mp4"
 vf=f'crop={sw}:{ch}:0:{cy},scale=1080:1428:flags=lanczos,fps=30,setsar=1,format=yuv420p'
 run([FF,'-hide_banner','-v','error','-y','-ss',f'{ss:.6f}','-i',src,'-t',f'{dur:.6f}','-vf',vf,'-an','-c:v','libx264','-preset','medium','-crf','17','-r','30','-movflags','+faststart',str(video)])
 reports.append({**it,'audio':str(stem48),'video':str(video),'crop':{'x':0,'y':cy,'w':sw,'h':ch},'duration':len(vocals)/sr})
 print(f"DONE #{it['n']} {key} {dur:.2f}s crop y={cy}, stem={stem48}")
(A/'source_assets.json').write_text(json.dumps(reports,indent=2))
print('ASSETS',A/'source_assets.json')
