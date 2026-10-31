import os,subprocess,re
from pathlib import Path
import numpy as np,soundfile as sf,torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
A=Path('/home/user/studio/type2/assets/ep7');AD=A/'audio';V=A/'video';FF='/tmp/vidtools/ffmpeg'
src='/home/user/dl/src/youtube/ep7/marc_spanish_crash_p3qDo4sNxlc.mp4';ss=0.0;dur=3.15
os.environ['OMP_NUM_THREADS']='4';torch.set_num_threads(4);model=get_model('htdemucs');model.cpu().eval()
raw=AD/'spanish_crash_raw.wav';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(dur),'-vn','-ac','2','-ar','44100','-c:a','pcm_s16le',str(raw)],check=True)
a,sr=sf.read(raw,dtype='float32',always_2d=True);n=round(dur*sr);a=a[:n];w=torch.from_numpy(a.T.copy());m=w.mean();std=w.mean(0).std();w=(w-m)/(std+1e-8)
with torch.inference_mode():pred=apply_model(model,w[None],device='cpu',shifts=0,split=True,overlap=.25,progress=False)[0]
voc=(pred*std+m)[model.sources.index('vocals')].cpu().numpy().T;p44=AD/'spanish_crash_vocals_44100.wav';sf.write(p44,voc,sr,subtype='PCM_16')
p48=AD/'spanish_crash_vocals.wav';subprocess.run([FF,'-hide_banner','-v','error','-y','-i',str(p44),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(p48)],check=True)
# vertical content frame, centered crop to Type-2's 1080x1428 clip window
cy=246;vf=f'crop=1080:1428:0:{cy},scale=1080:1428:flags=lanczos,fps=30,setsar=1,format=yuv420p';video=V/'2_spanish_crash.mp4';subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(dur),'-vf',vf,'-an','-c:v','libx264','-preset','medium','-crf','17','-r','30','-movflags','+faststart',str(video)],check=True)
print(video,p48)
