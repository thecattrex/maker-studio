#!/usr/bin/env python3
"""Build fresh Type-2 episodes 16 and 17 with source audio retained.
The script records each source window/crop and writes the two cut plans.
No subjective audio-listening claim is made; QA uses technical decode/loudness only.
"""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
CAND = '/home/user/dl/src/ep16_17_candidates'
ASSETS = os.path.join(ROOT, 'assets')
os.makedirs(ASSETS, exist_ok=True)

# Items are ranked strongest -> lightest. Playback order in the plans is 4 -> 3 -> 2 -> 1.
EPISODES = {
    16: [
        {'id':'xbd1am2', 'ss':16.0, 'dur':7.9, 'crop':(0,80,360,476), 'label':'POOL FLOAT WIPEOUT', 'sfx':('yeet',7.6)},
        {'id':'x9ges2a', 'ss':0.0, 'dur':4.6, 'crop':(0,80,360,476), 'label':'LOG OBSTACLE FAIL', 'sfx':('oof',4.3)},
        {'id':'xb30002', 'ss':0.0, 'dur':3.1, 'crop':(0,80,360,476), 'label':'PARENTS RACE SLIP', 'sfx':('slap',2.9)},
        {'id':'xa5vaae', 'ss':54.8, 'dur':2.9, 'crop':(0,72,360,476), 'label':'MILKSHAKE SPILL', 'sfx':('ba_drum_tss',2.7)},



    ],
    17: [
        {'id':'x9n9g9c', 'ss':0.0, 'dur':5.2, 'crop':(60,82,360,476), 'label':'BOX PRANK FAIL', 'sfx':('fail',4.9)},
        {'id':'x9pupdu', 'ss':0.0, 'dur':4.0, 'crop':(0,80,360,476), 'label':'DRAGON TUBE SPLASH', 'sfx':('slap',3.8)},
        {'id':'xa5rh3k', 'ss':0.0, 'dur':7.5, 'crop':(0,78,360,476), 'label':'SPINNING CHAIR FAIL', 'sfx':('oof',7.3)},
        {'id':'x8lvlqt', 'ss':0.0, 'dur':4.8, 'crop':(0,20,272,360), 'label':'INFLATABLE POOL FAIL', 'sfx':('yeet',4.6)},
    ],
}
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}

def build_base(ep, clips):
    out = os.path.join(ASSETS, f'ep{ep}_natural_audio_source.mp4')
    inputs, fc, offset = [], [], 0.0
    for i,c in enumerate(clips):
        path = f"{CAND}/{c['id']}/{c['id']}.mp4"
        c['path'] = path
        info = probe(path)
        x,y,w,h = c['crop']
        if not info.get('has_audio'):
            raise RuntimeError(f"{c['id']} has no source audio")
        if c['ss'] + c['dur'] > info['duration'] + 0.03:
            raise RuntimeError(f"window out of range: {c['id']} ({info['duration']:.2f}s)")
        if x+w > info['width'] or y+h > info['height']:
            raise RuntimeError(f"bad crop for {c['id']}: {c['crop']} vs {info['width']}x{info['height']}")
        inputs += ['-i', path]
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
    return out, info

def make_plan(ep, clips):
    items=[]
    for n,c in enumerate(clips,1):
        items.append({'n':n,'ss':c['base_ss'],'dur':c['dur'],'label':c['label'],
                      'color':COLORS[n],'focus':[0.5,0.5],'zoom_to':1.0,
                      'crop_top':0.0,'crop_bottom':0.0,
                      'sfx':[{'at':c['sfx'][1],'key':c['sfx'][0]}]})
    return {'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],
            'band':360,'bottom':132,'gap':0.16,'items':items,'music':os.path.join(ASSETS,'c2_48.wav'),
            'music_ss':0.0,'music_vol':0.17,'clip_vol':0.68,'sfx_dir':'/home/user/studio/trial/sfx',
            'sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0],'title_size':116}

if __name__ == '__main__':
    summaries={}
    for ep,clips in EPISODES.items():
        base,info=build_base(ep,clips)
        plan=make_plan(ep,clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_natural_audio.json')
        json.dump(plan,open(planpath,'w'),indent=2)
        manifest={'episode':ep,'clips':[{k:c[k] for k in ['id','ss','dur','crop','label','base_ss','path','sfx']} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'history_audit':'Each of these eight source IDs was checked against the available EP7–EP15 builders, manifests, and progress records; no prior local match was found. The two episode lists are disjoint.'}
        mpath=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
        json.dump(manifest,open(mpath,'w'),indent=2)
        summaries[ep]={'base_source':base,'duration':info['duration'],'plan':planpath,'manifest':mpath,'clips':manifest['clips']}
    print(json.dumps(summaries,indent=2))
