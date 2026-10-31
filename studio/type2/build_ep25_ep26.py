#!/usr/bin/env python3
"""Build EP25/EP26 Type-2 natural-audio sources and ranking plans."""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
ASSETS = os.path.join(ROOT, 'assets')
SFX_DIR = '/home/user/studio/trial/sfx'
BASE = '/home/user/dl/src/ep25_26_candidates'
MUSIC = os.path.join(ASSETS, 'c2_48.wav')
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}
os.makedirs(ASSETS, exist_ok=True)

# Ordered strongest -> lightest. The standard ranking plan plays [4,3,2,1].
# Windows are intentionally short and target the visible landing/fail.
EPISODES = {
 25: [
  {'id':'xbp3jtu','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xbp3jtu',
   'ss':2.20,'dur':5.30,'crop':(0,80,360,480),'label':'UNICORN FLOAT FAIL','sfx':('record_scratch',5.00),
   'note':'A woman loses balance trying to board an inflatable unicorn and splashes into the pool; cut at the landing.'},
  {'id':'xaa6p8k','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xaa6p8k',
   'ss':1.40,'dur':5.00,'crop':(0,80,360,480),'label':'PULL-UP BAR OOPS','sfx':('yeet',4.75),
   'note':'A gym pull-up attempt ends in a short fall onto the indoor floor/mat; crop keeps the bar and landing together.'},
  {'id':'x9pulw4','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9pulw4',
   'ss':1.20,'dur':4.30,'crop':(0,80,360,480),'label':'LAWN CHAIR FAIL','sfx':('bruh',3.95),
   'note':'A man leans back in a garden chair that gives way; cut at his grass landing, before the longer recovery.'},
  {'id':'x9tqvnu','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9tqvnu',
   'ss':1.40,'dur':4.70,'crop':(0,80,360,480),'label':'SHORELINE SLIP','sfx':('quack',4.55),
   'note':'A woman loses her footing on the sandy lakeshore and drops into shallow water; edit stops at the splash.'},
  ],
 26: [
  {'id':'x85zjwf','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x85zjwf',
   'ss':3.60,'dur':5.30,'crop':(24,120,360,480),'label':'POOL FLOAT FAIL','sfx':('oof',5.00),
   'note':'A woman tries to climb onto an inflatable chair and tumbles into the pool; crop keeps the float and splash visible.'},
  {'id':'x8o67k3','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x8o67k3',
   'ss':11.50,'dur':5.00,'crop':(1,0,270,480),'label':'TRAMPOLINE SPILL','sfx':('fail',4.80),
   'note':'A trampoline backflip loses balance and lands on the springy mat; cut just after the fall.'},
  {'id':'x77y27u','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x77y27u',
   'ss':13.30,'dur':5.20,'crop':(0,50,216,288),'label':'GATE JUMP WIPEOUT','sfx':('yeet',5.00),
   'note':'A woman tries to clear an old low gate and lands on the grass; tighter vertical crop retains the setup and landing.'},
  {'id':'x92r1ps','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x92r1ps',
   'ss':6.50,'dur':4.30,'crop':(24,120,360,480),'label':'MUDDY PATH SLIP','sfx':('ba_drum_tss',4.10),
   'note':'After-rain muddy path slip ends in a soft muddy landing; edit stops before extended recovery.'},
  ],
}


def make_base(ep, clips):
    out=os.path.join(ASSETS, f'ep{ep}_natural_audio_source.mp4')
    inputs=[]; fc=[]; offset=0.0
    for i,c in enumerate(clips):
        c['path']=os.path.join(BASE,c['id'],c['id']+'.mp4')
        info=probe(c['path'])
        if not info.get('has_audio'):
            raise RuntimeError(f"{ep}/{c['id']} has no source audio")
        x,y,w,h=c['crop']
        if x+w>info['width'] or y+h>info['height']:
            raise RuntimeError(f"bad crop {c['id']}: {c['crop']} vs {info['width']}x{info['height']}")
        if c['ss']+c['dur']>info['duration']+0.03:
            raise RuntimeError(f"window out of range {c['id']}: {info['duration']:.2f}s")
        if not os.path.exists(os.path.join(SFX_DIR,c['sfx'][0]+'.mp3')):
            raise RuntimeError(f"missing SFX {c['sfx'][0]}")
        inputs += ['-i',c['path']]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=480:636:flags=lanczos,fps=30,setsar=1,format=yuv420p[v{i}]')
        fc.append(f'[{i}:a]atrim=start={c["ss"]}:duration={c["dur"]},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={c["dur"]}[a{i}]')
        c['base_ss']=round(offset,4);c['source_info']={k:info[k] for k in ('duration','width','height','fps','vcodec','acodec')}
        offset+=c['dur']
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=1[outv][outa]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),
         '-map','[outv]','-map','[outa]','-c:v','libx264','-preset','fast','-crf','17',
         '-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
         '-movflags','+faststart',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError((r.stderr or '')[-4000:])
    info=probe(out)
    if not info.get('has_audio') or abs(info['duration']-offset)>0.12:
        raise RuntimeError(f'base validation failed: {info}; expected {offset:.2f}s')
    return out,info


def plan_for(clips):
    items=[]
    for n,c in enumerate(clips,1):
        items.append({'n':n,'ss':c['base_ss'],'dur':c['dur'],'label':c['label'],
                      'color':COLORS[n],'focus':[0.5,0.5],'zoom_to':1.0,
                      'crop_top':0.0,'crop_bottom':0.0,
                      'sfx':[{'at':c['sfx'][1],'key':c['sfx'][0]}]})
    return {'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],
            'band':360,'bottom':132,'gap':0.16,'items':items,'music':MUSIC,
            'music_ss':0.0,'music_vol':0.17,'clip_vol':0.68,'sfx_dir':SFX_DIR,
            'sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0],'title_size':116}

if __name__=='__main__':
    for ep,clips in EPISODES.items():
        base,info=make_base(ep,clips);plan=plan_for(clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_natural_audio.json')
        with open(planpath,'w') as f:json.dump(plan,f,indent=2)
        manifest={'episode':ep,'clips':[{k:c[k] for k in ['id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note','source_info']} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
                  'source_audio_subjectively_auditioned':False,'song_presence_claimed':False,'reuse_rights_checked':False,
                  'source_id_history_check':'Compared against available EP15–EP24 source manifests; selected IDs are not reused.'}
        mpath=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
        with open(mpath,'w') as f:json.dump(manifest,f,indent=2)
        print(json.dumps({'episode':ep,'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
