#!/usr/bin/env python3
import os,subprocess,json
from faster_whisper import WhisperModel
FF='/tmp/vidtools/ffmpeg';ROOT='/home/user/dl/src/ep15_remake_candidates';OUT='/home/user/studio/type2';
WINS={'x9weqas':(0,6.5),'x9m3tj6':(0,5.7),'x9ejedo':(0,5.2),'x9wy8kc':(0,8.8)}
model=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=2)
results=[]
for id,(ss,dur) in WINS.items():
 src=f'{ROOT}/{id}/{id}.mp4';wav=f'{OUT}/audio_review_{id}.wav'
 p=subprocess.run([FF,'-hide_banner','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(dur),'-vn','-ac','1','-ar','16000',wav],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
 segs,info=model.transcribe(wav,vad_filter=True,beam_size=2)
 seglist=[{'start':round(s.start,2),'end':round(s.end,2),'text':s.text.strip()} for s in segs]
 m=subprocess.run([FF,'-hide_banner','-i',wav,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
 import re
 summary=m[m.rfind('Integrated loudness:'):] if 'Integrated loudness:' in m else m[-500:]
 r={'id':id,'window':[ss,dur],'detected_language':info.language,'segments':seglist,'ebu_summary':summary};results.append(r)
 print(json.dumps(r,ensure_ascii=False),flush=True)
json.dump(results,open(f'{OUT}/EP15_remake_audio_review.json','w'),indent=2,ensure_ascii=False)
