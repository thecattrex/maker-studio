#!/usr/bin/env python3
"""Rebuild EP8/EP9 source montages with full setup-to-payoff trims.
Selected source audio is muted; the series mix is added by build.py.
"""
import json, os, subprocess, sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg, probe
ROOT='/home/user/studio/type2'; FF=ensure_ffmpeg(); AS='/home/user/dl/src/tiktok'; OUT='/home/user/dl'
EPISODES={
 8:[
  {'id':'7130347507925732654','ss':2.30,'dur':3.30,'label':'DOG TACKLE','color':'&H000000FF&','focus':[0.5,0.55]},
  {'id':'7498827321005329710','ss':2.20,'dur':3.30,'label':'RIVER MISSTEP','color':'&H000011FF&','focus':[0.5,0.55]},
  {'id':'7044628780048059653','ss':2.30,'dur':3.30,'label':'DOORSTEP SLIP','color':'&H0000A5FF&','focus':[0.5,0.50]},
  {'id':'7427950019468266798','ss':5.50,'dur':4.20,'label':'POOL COUNTDOWN','color':'&H0000D7FF&','focus':[0.5,0.55]},
  {'id':'7068065282706754821','ss':0.30,'dur':3.30,'label':'ICE WALK FAIL','color':'&H00FFFFFF&','focus':[0.5,0.55]},
 ],
 9:[
  {'id':'7519546021622451511','ss':3.50,'dur':3.30,'label':'COFFEE CHAIR FAIL','color':'&H000000FF&','focus':[0.5,0.55]},
  {'id':'7405391209096645931','ss':19.50,'dur':4.80,'label':'CABINET CRASH','color':'&H000011FF&','focus':[0.5,0.55]},
  {'id':'7148547839449419054','ss':0.00,'dur':3.50,'label':'DOG-WALK SLIP','color':'&H0000A5FF&','focus':[0.5,0.55]},
  {'id':'7471830784375065899','ss':0.00,'dur':4.50,'label':'DOCK FALL','color':'&H0000D7FF&','focus':[0.5,0.55]},
 ]
}
SFX_BY_N={3:('yeet',-7.0),5:('slap',-7.0),2:('oof',-7.5),4:('ba_drum_tss',-8.0),1:('fail',-6.0)}
for ep,clips in EPISODES.items():
  inputs=[];fc=[];items=[]; offset=0.0
  for i,c in enumerate(clips):
    path=f"{AS}/tt_{c['id']}.mp4"
    if not os.path.exists(path): raise FileNotFoundError(path)
    d=probe(path)['duration']
    if c['ss']+c['dur']>d: raise ValueError(f"EP{ep} {c['id']} trim ends past source ({d})")
    inputs += ['-i',path]
    chain=f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,fps=30'
    if c.get('source_crop'): chain+=','+c['source_crop']
    chain+=',scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p'
    chain+=f'[v{i}]';fc.append(chain)
    items.append({'n':i+1,'ss':round(offset,4),'dur':c['dur'],'label':c['label'],'color':c['color'],'focus':c['focus'],'zoom_to':1.0,'sfx':[]})
    offset+=c['dur']
  fc.append(''.join(f'[v{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=0[outv]')
  source=f'{OUT}/type2_ep{ep}_source_v5.mp4';silent_src=f'{OUT}/type2_ep{ep}_source_v5_a.mp4'
  subprocess.run([FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[outv]','-an','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',source],check=True)
  subprocess.run([FF,'-hide_banner','-v','error','-y','-i',source,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',silent_src],check=True)
  os.replace(silent_src,source)
  play_order=[3,5,2,4,1] if ep==8 else [3,4,2,1]
  order=[n-1 for n in play_order]
  plan={'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],'band':360,'bottom':132,'gap':0.16,'items':items,'music':None,'music_ss':0.0,'music_vol':0.0,'clip_vol':0.0,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-10.0,'ladder':'asc','order':order}
  with open(f'{ROOT}/plan_ep{ep}.json','w') as f:json.dump(plan,f,indent=2)
  silence=f'{ROOT}/assets/ep{ep}_source_silence.wav'
  subprocess.run([FF,'-hide_banner','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','4.5','-c:a','pcm_s16le',silence],check=True)
  cfg=json.load(open(f'{ROOT}/config_ep7.json'));cfg['clips']=[]
  for n in play_order:
    c=clips[n-1];key,peak=SFX_BY_N[n];dur=c['dur']
    cfg['clips'].append({'n':n,'ss':0.0,'dur':dur,'label':c['label'],'color':c['color'],'sfx':{'key':key,'at':round(max(0.0,dur-0.75),3),'peak_db':peak},'audio_file':silence})
  cfg['music']['file']='assets/c2_48.wav';cfg['frame']={'w':1080,'h':1920,'band':360,'bottom':132};cfg['gap']=0.16;cfg['ladder']='asc'
  with open(f'{ROOT}/config_ep{ep}.json','w') as f:json.dump(cfg,f,indent=2)
  print(f'EP{ep}: {source} {probe(source)["duration"]:.2f}s | trims:',[(c['id'],c['ss'],c['dur']) for c in clips])
