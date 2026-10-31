#!/usr/bin/env python3
"""Compile screened source moments + plans/configs for Type-2 EP8 and EP9.
All selected source audio is intentionally omitted; Type-2 series mix is applied separately.
Burned-in captions/numerals selected for removal are patched with FFmpeg delogo.
"""
import json, os, subprocess, sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg, probe
ROOT='/home/user/studio/type2'; FF=ensure_ffmpeg(); AS='/home/user/dl/src/tiktok'; OUT='/home/user/dl'
DUR=3.05
# Source order is #1..#5; established countdown playback order is 3,5,2,4,1.
EPISODES={
 8:[
  {'id':'7583500055944891678','ss':3.25,'label':'SKATE BAIL','color':'&H000000FF&'},
  {'id':'7519546021622451511','ss':3.50,'label':'PATIO CHAIR SLIP','color':'&H000011FF&'},
  {'id':'7427950019468266798','ss':9.60,'label':'POOL PLUNGE','color':'&H0000A5FF&'},
  {'id':'7493260955791445294','ss':3.10,'label':'MAT FLIP FAIL','color':'&H0000D7FF&'},
  {'id':'7445406555673169198','ss':6.20,'label':'CART EXIT FAIL','color':'&H00FFFFFF&'},
 ],
 9:[
  {'id':'7421957784075324718','ss':0.00,'label':'COSTUME WIPEOUT','color':'&H000000FF&','source_crop':'crop=608:1080:100:0'},
  {'id':'7519546021622451511','ss':3.50,'label':'COFFEE CHAIR FAIL','color':'&H000011FF&'},
  {'id':'7533709287076400439','ss':5.50,'label':'BEDROOM TRIP','color':'&H0000A5FF&','focus':[0.5,0.95]},
  {'id':'7475170551514860846','ss':5.30,'label':'BENCH BAIL','color':'&H0000D7FF&'},
  {'id':'7574125669496474893','ss':0.00,'label':'RIVER MISSTEP','color':'&H00FFFFFF&'},
 ]
}
SFX_BY_N={3:('yeet',2.25,-7.0),5:('slap',2.25,-7.0),2:('oof',2.10,-7.5),4:('ba_drum_tss',1.75,-8.0),1:('fail',2.30,-6.0)}
for ep, clips in EPISODES.items():
 inputs=[]; fc=[]
 for i,c in enumerate(clips):
  path=f"{AS}/tt_{c['id']}.mp4"
  if not os.path.exists(path): raise FileNotFoundError(path)
  d=probe(path)['duration']
  if c['ss']+DUR>d: raise ValueError(f"EP{ep} {c['id']} trim ends past source ({d})")
  inputs += ['-i',path]
  chain=f'[{i}:v]trim=start={c["ss"]}:duration={DUR},setpts=PTS-STARTPTS,fps=30'
  if c.get('source_crop'): chain+=','+c['source_crop']
  chain+=',scale=1080:1920:flags=lanczos,setsar=1'
  for x,y,w,h in c.get('delogos',[]): chain+=f',delogo=x={x}:y={y}:w={w}:h={h}:show=0'
  chain+=f',format=yuv420p[v{i}]';fc.append(chain)
 fc.append(''.join(f'[v{i}]' for i in range(5))+'concat=n=5:v=1:a=0[outv]')
 source=f'{OUT}/type2_ep{ep}_source.mp4'
 silent_src=f'{OUT}/type2_ep{ep}_source_a.mp4'
 subprocess.run([FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[outv]','-an','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',source],check=True)
 # run.py's renderer requires an audio stream; provide only digital silence.
 subprocess.run([FF,'-hide_banner','-v','error','-y','-i',source,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',silent_src],check=True)
 os.replace(silent_src,source)
 items=[]
 for i,c in enumerate(clips):
  items.append({'n':i+1,'ss':round(i*DUR,4),'dur':DUR,'label':c['label'],'color':c['color'],'focus':c.get('focus',[0.5,0.55]),'zoom_to':1.0,'sfx':[]})
 plan={'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],'band':360,'bottom':132,'gap':0.25,'items':items,'music':None,'music_ss':0.0,'music_vol':0.0,'clip_vol':0.0,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-10.0,'ladder':'asc','order':[2,4,1,3,0]}
 json.dump(plan,open(f'{ROOT}/plan_ep{ep}.json','w'),indent=2)
 silent=f'{ROOT}/assets/ep{ep}_source_silence.wav'
 subprocess.run([FF,'-hide_banner','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','4.0','-c:a','pcm_s16le',silent],check=True)
 cfg=json.load(open(f'{ROOT}/config_ep7.json'));cfg['clips']=[]
 for n in [3,5,2,4,1]:
  c=clips[n-1]; key,at,peak=SFX_BY_N[n]
  cfg['clips'].append({'n':n,'ss':0.0,'dur':DUR,'label':c['label'],'color':c['color'],'sfx':{'key':key,'at':at,'peak_db':peak},'audio_file':silent})
 cfg['music']['file']='assets/c2_48.wav';cfg['frame']={'w':1080,'h':1920,'band':360,'bottom':132};cfg['gap']=0.25;cfg['ladder']='asc'
 json.dump(cfg,open(f'{ROOT}/config_ep{ep}.json','w'),indent=2)
 print(f'EP{ep}: {source} {probe(source)["duration"]:.2f}s | plan/config ready')
