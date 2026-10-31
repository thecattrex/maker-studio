#!/usr/bin/env python3
"""Build EP18 Type-2 source base and plan. Keeps original source audio.
All selected cuts target a very short post-fall tail (~0.1 s); no extended aftermath.
"""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
ASSETS = os.path.join(ROOT, 'assets')
os.makedirs(ASSETS, exist_ok=True)

# Ordered strongest -> lightest; the Type-2 plan plays [3,2,1,0] so the strongest is last.
CLIPS = [
    {
        'id':'x9uf2f6', 'platform':'Dailymotion',
        'url':'https://www.dailymotion.com/video/x9uf2f6',
        'path':'/home/user/dl/src/ep18_candidates/dailymotion/x9uf2f6.mp4',
        'ss':0.0, 'dur':5.4, 'crop':(0,80,360,476),
        'label':'ZIPLINE SAND FALL', 'sfx':('bruh',5.18),
        'note':'Adult rider falls onto sand; cut at the landing with only a short tail.'
    },
    {
        'id':'xa9xt92', 'platform':'Dailymotion',
        'url':'https://www.dailymotion.com/video/xa9xt92',
        'path':'/home/user/dl/src/ep18_candidates/dailymotion/xa9xt92.mp4',
        'ss':0.0, 'dur':4.2, 'crop':(360,0,540,720),
        'label':'FOAM PIT RAMP FAIL', 'sfx':('yeet',3.72),
        'note':'Single ramp attempt, lands in a padded foam pit; crop preserves approach and landing.'
    },
    {
        'id':'5ju9bmwmVoQ', 'platform':'YouTube Shorts',
        'url':'https://www.youtube.com/shorts/5ju9bmwmVoQ',
        'path':'/home/user/dl/src/ep18_candidates/youtube/5ju9bmwmVoQ.mp4',
        'ss':0.0, 'dur':3.9, 'crop':(0,80,360,476),
        'label':'STREAM BANK SLIP', 'sfx':('record_scratch',3.72),
        'note':'Person slips down the bank into water; crop removes top/bottom captions, retains small creator handle.'
    },
    {
        'id':'xaz36yq', 'platform':'Dailymotion',
        'url':'https://www.dailymotion.com/video/xaz36yq',
        'path':'/home/user/dl/src/ep16_17_candidates/xaz36yq/xaz36yq.mp4',
        'ss':0.0, 'dur':3.4, 'crop':(220,0,360,480),
        'label':'YARDWORK BACKWARD SPILL', 'sfx':('oof',3.22),
        'note':'Adult loses balance during a yard task; cut just after landing.'
    },
]
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}

def build_base():
    out = os.path.join(ASSETS, 'ep18_natural_audio_source.mp4')
    inputs, fc, offset = [], [], 0.0
    for i,c in enumerate(CLIPS):
        info = probe(c['path'])
        if not info.get('has_audio'):
            raise RuntimeError(f"{c['id']} has no source audio")
        x,y,w,h = c['crop']
        if x+w > info['width'] or y+h > info['height']:
            raise RuntimeError(f"bad crop for {c['id']}: {c['crop']} vs {info['width']}x{info['height']}")
        if c['ss'] + c['dur'] > info['duration'] + 0.03:
            raise RuntimeError(f"window out of range: {c['id']} ({info['duration']:.2f}s)")
        inputs += ['-i', c['path']]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=480:636:flags=lanczos,fps=30,setsar=1,format=yuv420p[v{i}]')
        fc.append(f'[{i}:a]atrim=start={c["ss"]}:duration={c["dur"]},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={c["dur"]}[a{i}]')
        c['base_ss'] = round(offset,4)
        offset += c['dur']
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(CLIPS))) + f'concat=n={len(CLIPS)}:v=1:a=1[outv][outa]')
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

def make_plan():
    items=[]
    for n,c in enumerate(CLIPS,1):
        items.append({'n':n,'ss':c['base_ss'],'dur':c['dur'],'label':c['label'],
                      'color':COLORS[n],'focus':[0.5,0.5],'zoom_to':1.0,
                      'crop_top':0.0,'crop_bottom':0.0,
                      'sfx':[{'at':c['sfx'][1],'key':c['sfx'][0]}]})
    return {'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],
            'band':360,'bottom':132,'gap':0.16,'items':items,'music':os.path.join(ASSETS,'c2_48.wav'),
            'music_ss':0.0,'music_vol':0.17,'clip_vol':0.68,'sfx_dir':'/home/user/studio/trial/sfx',
            'sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0],'title_size':116}

if __name__ == '__main__':
    base,info=build_base()
    plan=make_plan()
    planpath=os.path.join(ROOT,'plan_ep18_natural_audio.json')
    json.dump(plan,open(planpath,'w'),indent=2)
    manifest={'episode':18,'clips':[{k:c[k] for k in ['id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note']} for c in CLIPS],
              'base_source':base,'duration':info['duration'],'plan':planpath,
              'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
              'source_audio_subjectively_auditioned':False,
              'song_presence_claimed':False,
              'reuse_rights_checked':False,
              'history_audit':'Selected source IDs checked against available EP7–EP17 source manifests/builders. No selected source ID matched a prior episode.'}
    mpath=os.path.join(ROOT,'EP18_source_manifest.json')
    json.dump(manifest,open(mpath,'w'),indent=2)
    print(json.dumps({'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
