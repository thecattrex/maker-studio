#!/usr/bin/env python3
"""Build fresh EP28/29 Type-2 remakes with retained source audio."""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
ASSETS = os.path.join(ROOT, 'assets')
BASE = '/home/user/dl/src/ep28_29_candidates'
SFX_DIR = '/home/user/studio/trial/sfx'
MUSIC = os.path.join(ASSETS, 'c2_48.wav')
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}
WHITE='&H00FFFFFF&'; RED='&H002828F0&'; YELLOW='&H0000D7FF&'
os.makedirs(ASSETS, exist_ok=True)

# Strongest-to-lightest entries; output order follows the series' [4,3,2,1] ladder.
# Source IDs are fresh versus the available EP15–EP26 source manifests.
EPISODES = {
 28: {
  'title': [[['Ranking ', WHITE], ['Funniest', RED]], [['Falls', YELLOW]]],
  'clips': [
   {'id':'x7ua30m','ss':6.50,'dur':3.70,'crop':(0,20,200,266),'label':'TRAMPOLINE DUNK FAIL','sfx':('yeet',3.60),
    'note':'A basketball dunk attempt at a trampoline park ends in a safe landing on the trampoline.'},
   {'id':'x7uo0pe','ss':1.00,'dur':4.20,'crop':(0,0,360,480),'label':'UNEQUAL BARS OOPS','sfx':('oof',3.15),
    'note':'A gymnastics bar attempt ends with a fall onto the mat; edit ends at the landing.'},
   {'id':'x8xqgfg','ss':0.50,'dur':3.80,'crop':(350,0,540,720),'label':'GRASS SLIP-UP','sfx':('ba_drum_tss',3.35),
    'note':'A man slips during a run on wet grass and lands in a soft patch; cut close to the landing.'},
   {'id':'x94jpao','ss':0.00,'dur':5.10,'crop':(0,60,272,360),'label':'WET GRASS TUMBLE','sfx':('fail',4.65),
    'note':'A runner loses footing on wet grass; tighter portrait crop keeps the tumble visible.'},
  ]},
 29: {
  'title': [[['Ranking ', WHITE], ['Epic', RED]], [['Water Fails', YELLOW]]],
  'clips': [
   {'id':'x85q67h','ss':19.50,'dur':5.20,'crop':(0,60,272,360),'label':'ROPE SWING SPLASH','sfx':('yeet',4.45),
    'note':'A rope-swing attempt falls short and ends in the river; cut at the splash.'},
   {'id':'x7tksr8','ss':4.00,'dur':5.80,'crop':(0,60,272,360),'label':'SURFBOARD WIPEOUT','sfx':('record_scratch',5.35),
    'note':'A woman loses balance on a pool surfboard and splashes into the pool.'},
   {'id':'x93l2i6','ss':8.00,'dur':3.20,'crop':(0,100,272,360),'label':'SWING DROP','sfx':('oof',2.75),
    'note':'A woman slips off a hanging swing over water; upper crop trims away the source sticker.'},
   {'id':'x7xvym2','ss':8.50,'dur':3.60,'crop':(60,0,360,480),'label':'BASKETBALL SLIP','sfx':('fail',3.25),
    'note':'A man slips while dribbling on an outdoor court; cut just after the fall.'},
  ]}
}


def make_base(ep, clips):
    out=os.path.join(ASSETS, f'ep{ep}_remake_natural_audio_source.mp4')
    inputs=[]; fc=[]; offset=0.0
    for i,c in enumerate(clips):
        c['path']=os.path.join(BASE,c['id'],c['id']+'.mp4')
        info=probe(c['path'])
        if not info.get('has_audio'):
            raise RuntimeError(f"{ep}/{c['id']} missing source audio")
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
        c['base_ss']=round(offset,4)
        c['source_info']={k:info[k] for k in ('duration','width','height','fps','vcodec','acodec','has_audio')}
        offset += c['dur']
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=1[outv][outa]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),
         '-map','[outv]','-map','[outa]','-c:v','libx264','-preset','fast','-crf','17',
         '-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
         '-movflags','+faststart',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError((r.stderr or '')[-4000:])
    info=probe(out)
    if not info.get('has_audio') or abs(info['duration']-offset)>0.15:
        raise RuntimeError(f'base validation failed: {info}; expected {offset:.2f}s')
    return out,info


def plan_for(ep, title, clips):
    items=[]
    for n,c in enumerate(clips,1):
        items.append({'n':n,'ss':c['base_ss'],'dur':c['dur'],'label':c['label'],
                      'color':COLORS[n],'focus':[0.5,0.5],'zoom_to':1.0,
                      'crop_top':0.0,'crop_bottom':0.0,
                      'sfx':[{'at':c['sfx'][1],'key':c['sfx'][0]}]})
    return {'title':title,'band':360,'bottom':132,'gap':0.16,'items':items,
            'music':MUSIC,'music_ss':0.0,'music_vol':0.17,'clip_vol':0.68,
            'sfx_dir':SFX_DIR,'sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0],
            'title_size':116}

if __name__=='__main__':
    for ep,spec in EPISODES.items():
        clips=spec['clips'];base,info=make_base(ep,clips)
        plan=plan_for(ep,spec['title'],clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_remake_natural_audio.json')
        with open(planpath,'w') as f:json.dump(plan,f,indent=2)
        manifest={'episode':ep,'remake':True,
                  'clips':[{k:c[k] for k in ('id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note','source_info') if k in c} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
                  'source_audio_subjectively_auditioned':False,'song_presence_claimed':False,
                  'reuse_rights_checked':False,
                  'source_id_history_check':'Checked against available EP15–EP26 source manifests; IDs not reused.'}
        for c in manifest['clips']:
            c['platform']='Dailymotion';c['url']=f"https://www.dailymotion.com/video/{c['id']}"
        mpath=os.path.join(ROOT,f'EP{ep}_remake_source_manifest.json')
        with open(mpath,'w') as f:json.dump(manifest,f,indent=2)
        print(json.dumps({'episode':ep,'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
