#!/usr/bin/env python3
"""Create EP21/EP22 source bases and Type-2 ranking plans; retain all source audio."""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
ASSETS = os.path.join(ROOT, 'assets')
os.makedirs(ASSETS, exist_ok=True)
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}
MUSIC = os.path.join(ASSETS, 'c2_48.wav')
SFX_DIR = '/home/user/studio/trial/sfx'
BASE = '/home/user/dl/src/ep21_22_candidates'

# Listed strongest -> lightest; the Type-2 plan plays [4,3,2,1], making the
# strongest payoff the final clip. All windows end immediately after the fall.
EPISODES = {
 21: [
  {'id':'UUhUFLhlC4s','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/UUhUFLhlC4s',
   'ss':0.0,'dur':1.20,'crop':(0,80,360,480),'label':'BEACH CHAIR vs WAVE','sfx':('quack',1.00),
   'note':'Wave sweeps the seated person and chair into the surf; cuts at the first landing/splash, no aftermath.'},
  {'id':'GAqJAgcozdM','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/GAqJAgcozdM',
   'ss':5.90,'dur':5.20,'crop':(0,160,360,480),'label':'BACKYARD CHAIR FAIL','sfx':('yeet',4.95),
   'note':'Single tumble onto lawn; top AFV caption/logo removed by crop, cut shortly after impact.'},
  {'id':'xamvx3y','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xamvx3y',
   'ss':49.00,'dur':6.90,'crop':(0,80,360,480),'label':'TIRE SWING WIPEOUT','sfx':('bruh',6.70),
   'note':'Rope-swing fall onto concrete; source ends at 55.90s, about 0.1s after the fall.'},
  {'id':'x91v6vu','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x91v6vu',
   'ss':0.00,'dur':5.15,'crop':(0,0,360,480),'label':'CAMP CHAIR COLLAPSE','sfx':('oof',5.00),
   'note':'Camp chair gives way and the man lands on grass; focused crop keeps both him and chair in view.'},
  ],
 22: [
  {'id':'UVhrfjHAHU8','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/UVhrfjHAHU8',
   'ss':1.50,'dur':5.20,'crop':(0,70,360,480),'label':'CAMPING CHAIR DOUBLE FAIL','sfx':('yeet',5.00),
   'note':'Chair tips and the pair tumble onto grass; top watermark cropped, ends at the landing.'},
  {'id':'Rcl11XQzDfI','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/Rcl11XQzDfI',
   'ss':0.0,'dur':2.75,'crop':(0,160,360,480),'label':'CHAIR PULL PRANK','sfx':('record_scratch',2.45),
   'note':'One chair-pull prank; burned-in title removed with a top crop and cut just after he reaches the ground.'},
  {'id':'x9o5ajg','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9o5ajg',
   'ss':5.20,'dur':3.40,'crop':(0,72,360,470),'label':'MOMS RACE WIPEOUT','sfx':('ba_drum_tss',3.15),
   'note':'Two runners tumble on grass during a friendly race; crop removes phone/player UI and source logo.'},
  {'id':'xbdix3m','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xbdix3m',
   'ss':28.00,'dur':5.25,'crop':(0,80,360,480),'label':'TABLETOP STUNT FAIL','sfx':('slap',5.05),
   'note':'Short setup and tabletop slip onto the floor; top watermark cropped, cut after the fall.'},
  ],
}

def build_base(ep, clips):
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
        c['base_ss']=round(offset,4);offset+=c['dur']
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=1[outv][outa]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),
         '-map','[outv]','-map','[outa]','-c:v','libx264','-preset','fast','-crf','17',
         '-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
         '-movflags','+faststart',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError((r.stderr or '')[-4000:])
    info=probe(out)
    if not info.get('has_audio') or abs(info['duration']-offset)>0.12: raise RuntimeError(f'base validation failed {info}')
    return out,info

def make_plan(clips):
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
        base,info=build_base(ep,clips);plan=make_plan(clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_natural_audio.json')
        with open(planpath,'w') as f:json.dump(plan,f,indent=2)
        manifest={'episode':ep,'clips':[{k:c[k] for k in ['id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note']} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
                  'source_audio_subjectively_auditioned':False,'song_presence_claimed':False,'reuse_rights_checked':False,
                  'source_id_history_check':'Compared against available EP15 remake and EP16-EP20 source manifests; no selected source ID is reused.'}
        mpath=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
        with open(mpath,'w') as f:json.dump(manifest,f,indent=2)
        print(json.dumps({'episode':ep,'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
