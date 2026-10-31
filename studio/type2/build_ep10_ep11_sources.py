#!/usr/bin/env python3
"""Build EP10/11 silent source reels from reviewed single-incident trims."""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe
ROOT='/home/user/studio/type2'; AS='/home/user/dl/src/tiktok'; OUT='/home/user/dl'; FF=ensure_ffmpeg()

# Entries indexed by ranking number (#1 best through #4). Every trim preserves
# the visible setup and payoff; source audio is muted for the series mix.
EPISODES={
 10:[
  {'id':'7472944008008912170','ss':3.0,'dur':5.7,'label':'BARREL CHAIR FAIL'},
  {'id':'7493260955791445294','ss':0.0,'dur':5.2,'label':'ROWER WIPEOUT'},
  {'id':'7498827321005329710','ss':2.0,'dur':4.8,'label':'RIVER ROCK SLIP'},
  {'id':'7130347507925732654','ss':2.8,'dur':3.25,'label':'CARTWHEEL WIPEOUT'},
 ],
 11:[
  {'id':'7355989140976209198','ss':0.0,'dur':5.8,'label':'HANDSTAND WALL FAIL'},
  {'id':'7475170551514860846','ss':2.7,'dur':5.8,'label':'BENCH COLLAPSE'},
  {'id':'7449565789432057134','ss':3.3,'dur':3.4,'label':'SLIDE EXIT FAIL'},
  {'id':'7494033019607551275','ss':4.4,'dur':3.6,'label':'LOG-STEP SLIP'},
 ]
}
SFX={4:('yeet',-7.0),3:('ba_drum_tss',-8.0),2:('oof',-7.5),1:('fail',-6.0)}
TITLE=[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]]
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H0000D7FF&'}
for ep,items in EPISODES.items():
    # Build silent source in #1..#4 order, and let plan order play #4..#1.
    inputs=[];fc=[]
    for i,c in enumerate(items):
        path=f"{AS}/tt_{c['id']}.mp4"
        if not os.path.exists(path): raise FileNotFoundError(path)
        d=float(probe(path)['duration'])
        if c['ss']+c['dur']>d: raise ValueError(f"EP{ep} {c['id']} trim ends past source ({d})")
        inputs += ['-i',path]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,fps=30,scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p[v{i}]')
    fc.append(''.join(f'[v{i}]' for i in range(len(items)))+f'concat=n={len(items)}:v=1:a=0[outv]')
    source=f'{OUT}/type2_ep{ep}_source_v1.mp4'
    raw=f'{OUT}/type2_ep{ep}_source_v1_silent.mp4'
    subprocess.run([FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[outv]','-an','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',raw],check=True)
    subprocess.run([FF,'-hide_banner','-v','error','-y','-i',raw,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',source],check=True)
    os.remove(raw)
    silent=f'{ROOT}/assets/ep{ep}_source_silence.wav'
    subprocess.run([FF,'-hide_banner','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','9.0','-c:a','pcm_s16le',silent],check=True)
    # Ranking storyboard in #1..#4 list order. Playback is #4 -> #1.
    plan_items=[];offset=0.0
    for n,c in enumerate(items,1):
        plan_items.append({'n':n,'ss':round(offset,4),'dur':c['dur'],'label':c['label'],'color':COLORS[n], 'focus':[0.5,0.55],'zoom_to':1.0,'sfx':[]})
        offset+=c['dur']
    plan={'title':TITLE,'band':360,'bottom':132,'gap':0.16,'items':plan_items,'music':None,'music_ss':0.0,'music_vol':0.0,'clip_vol':0.0,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0]}
    with open(f'{ROOT}/plan_ep{ep}.json','w') as f: json.dump(plan,f,indent=2)
    playback=[(4,items[3]),(3,items[2]),(2,items[1]),(1,items[0])]
    cfg=json.load(open(f'{ROOT}/config_ep9.json'))
    cfg['clips']=[]
    for n,c in playback:
        key,peak=SFX[n]
        cfg['clips'].append({'n':n,'ss':0.0,'dur':c['dur'],'label':c['label'],'color':COLORS[n], 'sfx':{'key':key,'at':round(max(0,c['dur']-0.7),3),'peak_db':peak},'audio_file':silent})
    cfg['master']['lufs']=-14.2
    with open(f'{ROOT}/config_ep{ep}.json','w') as f: json.dump(cfg,f,indent=2)
    print(f'EP{ep}: {source} {probe(source)["duration"]:.2f}s, selected:',[(c['id'],c['ss'],c['dur']) for c in reversed(items)])
