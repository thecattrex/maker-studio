#!/usr/bin/env python3
"""Build EP19 and EP20 Type-2 source bases/plans, preserving each source audio track."""
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

# Listed strongest -> lightest. The Type-2 plan orders [4,3,2,1], so the
# strongest payoff closes each episode. Crops target the existing 480x636 viewport.
EPISODES = {
 19: [
    {'id':'x93gy2c','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x93gy2c',
     'path':'/home/user/dl/src/ep19_20_candidates/x93gy2c/x93gy2c.mp4',
     'ss':0.0,'dur':6.35,'crop':(0,53,272,360),'label':'POOL FLIP FAIL','sfx':('dramatic_vine',6.20),
     'note':'One failed flip from the ledge into the pool; crop keeps the takeoff and splash in view.'},
    {'id':'xvmwObWgeiM','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/xvmwObWgeiM',
     'path':'/home/user/dl/src/ep19_20_candidates/xvmwObWgeiM/xvmwObWgeiM.mp4',
     'ss':0.0,'dur':4.72,'crop':(0,80,360,480),'label':'OFFICE CHAIR WIPEOUT','sfx':('record_scratch',4.56),
     'note':'Single office-chair fall; crop removes the top banner while retaining the landing.'},
    {'id':'x9ec08o','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9ec08o',
     'path':'/home/user/dl/src/ep19_20_candidates/x9ec08o/x9ec08o.mp4',
     'ss':14.30,'dur':3.60,'crop':(0,110,360,480),'label':'DINNER CHAIR PRANK','sfx':('bruh',3.48),
     'note':'Single chair-pull prank window; cut shortly after the seated man reaches the floor.'},
    {'id':'xa750ce','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xa750ce',
     'path':'/home/user/dl/src/ep18_candidates/dailymotion/xa750ce.mp4',
     'ss':0.0,'dur':5.00,'crop':(0,80,360,480),'label':'COUCH SHOW-AND-FALL','sfx':('oof',4.84),
     'note':'Woman demonstrating the couch leans back and lands on its soft cushions; short landing tail.'},
  ],
 20: [
    {'id':'xbpdewm','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xbpdewm',
     'path':'/home/user/dl/src/ep16_17_candidates/xbpdewm/xbpdewm.mp4',
     'ss':11.00,'dur':4.00,'crop':(0,80,360,480),'label':'ARCADE PUNCH WIPEOUT','sfx':('yeet',3.88),
     'note':'Single arcade punch-and-stumble event; crop follows the fall to the floor and ends quickly.'},
    {'id':'xbpwkiy','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xbpwkiy',
     'path':'/home/user/dl/src/ep16_17_candidates/xbpwkiy/xbpwkiy.mp4',
     'ss':11.50,'dur':2.85,'crop':(15,10,330,440),'label':'INFLATABLE WATER-PARK SLIP','sfx':('quack',2.75),
     'note':'Isolated one-attempt slip onto the inflatable; bottom caption removed by crop.'},
    {'id':'q6Bj99n58T0','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/q6Bj99n58T0',
     'path':'/home/user/dl/src/ep19_20_candidates/q6Bj99n58T0/q6Bj99n58T0.mp4',
     'ss':0.0,'dur':2.72,'crop':(0,80,360,480),'label':'SHOP STOOL SPILL','sfx':('slap',2.55),
     'note':'Single overhead security-camera chair fall; cut around the landing, with no extended aftermath.'},
    {'id':'CWy7jX7LTWM','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/CWy7jX7LTWM',
     'path':'/home/user/dl/src/ep19_20_candidates/CWy7jX7LTWM/CWy7jX7LTWM.mp4',
     'ss':0.0,'dur':5.45,'crop':(0,90,408,538),'label':'EGG CHAIR TOPPLE','sfx':('ba_drum_tss',5.33),
     'note':'Single outdoor egg-chair topple; ends just after the chair and rider tip over.'},
  ],
}

def build_base(ep, clips):
    out = os.path.join(ASSETS, f'ep{ep}_natural_audio_source.mp4')
    inputs, fc, offset = [], [], 0.0
    for i,c in enumerate(clips):
        info = probe(c['path'])
        if not info.get('has_audio'):
            raise RuntimeError(f"{ep}/{c['id']} has no source audio")
        x,y,w,h = c['crop']
        if x+w > info['width'] or y+h > info['height']:
            raise RuntimeError(f"bad crop for {c['id']}: {c['crop']} vs {info['width']}x{info['height']}")
        if c['ss'] + c['dur'] > info['duration'] + 0.03:
            raise RuntimeError(f"window out of range: {c['id']} ({info['duration']:.2f}s)")
        if not os.path.exists(os.path.join(SFX_DIR, c['sfx'][0] + '.mp3')):
            raise RuntimeError(f"missing SFX: {c['sfx'][0]}")
        inputs += ['-i', c['path']]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=480:636:flags=lanczos,fps=30,setsar=1,format=yuv420p[v{i}]')
        fc.append(f'[{i}:a]atrim=start={c["ss"]}:duration={c["dur"]},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={c["dur"]}[a{i}]')
        c['base_ss'] = round(offset,4)
        offset += c['dur']
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=1:a=1[outv][outa]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),
         '-map','[outv]','-map','[outa]','-c:v','libx264','-preset','fast','-crf','17',
         '-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
         '-movflags','+faststart',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or '')[-4000:])
    info=probe(out)
    if not info.get('has_audio') or abs(info['duration']-offset)>0.12:
        raise RuntimeError(f'base validation failed: {info}')
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

if __name__ == '__main__':
    for ep,clips in EPISODES.items():
        base,info=build_base(ep,clips)
        plan=make_plan(clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_natural_audio.json')
        with open(planpath,'w') as f:json.dump(plan,f,indent=2)
        manifest={'episode':ep,'clips':[{k:c[k] for k in ['id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note']} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
                  'source_audio_subjectively_auditioned':False,'song_presence_claimed':False,'reuse_rights_checked':False,
                  'source_id_history_check':'Compared against currently available EP16-EP18 selected source manifests; no selected source ID is reused.'}
        mpath=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
        with open(mpath,'w') as f:json.dump(manifest,f,indent=2)
        print(json.dumps({'episode':ep,'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
