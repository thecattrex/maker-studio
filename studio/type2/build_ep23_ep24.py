#!/usr/bin/env python3
"""Build EP23/EP24 Type-2 natural-audio source bases, plans, and manifests."""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

FF = ensure_ffmpeg()
ROOT = '/home/user/studio/type2'
ASSETS = os.path.join(ROOT, 'assets')
SFX_DIR = '/home/user/studio/trial/sfx'
BASE = '/home/user/dl/src/ep23_24_candidates'
MUSIC = os.path.join(ASSETS, 'c2_48.wav')
COLORS = {1:'&H000000FF&', 2:'&H000011FF&', 3:'&H0000A5FF&', 4:'&H00FFFFFF&'}
os.makedirs(ASSETS, exist_ok=True)

# Ordered best-to-lightest; render order [3,2,1,0] makes the strongest last.
EPISODES = {
 23: [
  {'id':'x9ri64o','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9ri64o',
   'ss':7.00,'dur':5.80,'crop':(60,180,360,480),'label':'SEESAW TUMBLE','sfx':('quack',5.60),
   'note':'Adult and child topple from a spring seesaw onto grass; cut at the landing with no aftermath.'},
  {'id':'xbpdexu','platform':'Dailymotion','url':'https://www.dailymotion.com/video/xbpdexu',
   'ss':0.00,'dur':3.25,'crop':(60,180,360,480),'label':'ADVENTURE PARK OOPS','sfx':('yeet',3.10),
   'note':'Dad loses balance onto a padded trampoline-zone surface while helping his daughter; cut at the soft landing.'},
  {'id':'ylJ4CCO3xHY','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/ylJ4CCO3xHY',
   'ss':0.00,'dur':3.15,'crop':(0,80,360,480),'label':'PLAZA SLIP','sfx':('record_scratch',2.95),
   'note':'Brief low-height slip onto a wet plaza; the edit cuts at the fall, before the subject gets up.'},
  {'id':'x9cdhvc','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9cdhvc',
   'ss':0.00,'dur':4.60,'crop':(92,220,360,480),'label':'SCOOTER GRASSPLANT','sfx':('bruh',4.45),
   'note':'Rider tumbles off a scooter onto grass; crop keeps the rider and scooter together, then cuts just after the landing.'},
  ],
 24: [
  {'id':'x6rskrf','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x6rskrf',
   'ss':3.15,'dur':2.05,'crop':(246,0,360,480),'pre_scale':'853x480','label':'INFLATABLE CAMEL FAIL','sfx':('oof',1.90),
   'note':'Rider slips from the inflatable camel into the water; short vertical center crop, ending at the splash.'},
  {'id':'x8p4ov6','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x8p4ov6',
   'ss':0.40,'dur':6.10,'crop':(24,100,360,480),'label':'BOUQUET BUSH LANDING','sfx':('ba_drum_tss',5.80),
   'note':'At a wedding bouquet toss, a guest ends up in the shrub bed; edit stops at the tumble, before recovery.'},
  {'id':'x87tkod','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x87tkod',
   'ss':4.50,'dur':2.05,'crop':(1,0,270,480),'label':'SLIDE WIPEOUT','sfx':('bruh',1.90),
   'note':'Adult slips off the backyard water-slide board onto the soft tarp; cut at the landing.'},
  {'id':'x9h0ngc','platform':'Dailymotion','url':'https://www.dailymotion.com/video/x9h0ngc',
   'ss':3.50,'dur':3.00,'crop':(60,80,360,480),'label':'SWING TUMBLE','sfx':('oof',2.60),
   'note':'Wedding swing tip-over onto gravel; crop removes source caption text, keeps the full landing visible, and cuts just after impact.'},
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
        if c.get('pre_scale'):
            sw,sh=map(int,c['pre_scale'].split('x'))
            if x+w>sw or y+h>sh:
                raise RuntimeError(f"bad post-scale crop {c['id']}: {c['crop']} vs {sw}x{sh}")
            vf=f'scale={sw}:{sh}:flags=lanczos,crop={w}:{h}:{x}:{y}'
        else:
            if x+w>info['width'] or y+h>info['height']:
                raise RuntimeError(f"bad crop {c['id']}: {c['crop']} vs {info['width']}x{info['height']}")
            vf=f'crop={w}:{h}:{x}:{y}'
        if c['ss']+c['dur']>info['duration']+0.03:
            raise RuntimeError(f"window out of range {c['id']}: {info['duration']:.2f}s")
        if not os.path.exists(os.path.join(SFX_DIR,c['sfx'][0]+'.mp3')):
            raise RuntimeError(f"missing SFX {c['sfx'][0]}")
        inputs += ['-i',c['path']]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,{vf},scale=480:636:flags=lanczos,fps=30,setsar=1,format=yuv420p[v{i}]')
        fc.append(f'[{i}:a]atrim=start={c["ss"]}:duration={c["dur"]},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={c["dur"]}[a{i}]')
        c['base_ss']=round(offset,4); c['source_info']={k:info[k] for k in ('duration','width','height','fps','vcodec','acodec')}
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
        raise RuntimeError(f'base validation failed {info}; expected {offset:.3f}s')
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
        base,info=make_base(ep,clips); plan=plan_for(clips)
        planpath=os.path.join(ROOT,f'plan_ep{ep}_natural_audio.json')
        with open(planpath,'w') as f:json.dump(plan,f,indent=2)
        manifest={'episode':ep,'clips':[{k:c[k] for k in ['id','platform','url','ss','dur','crop','label','base_ss','path','sfx','note','source_info'] if k in c} for c in clips],
                  'base_source':base,'duration':info['duration'],'plan':planpath,
                  'source_audio_retained':True,'clip_volume':0.68,'bgm_volume':0.17,'sfx_peak_db':-10.0,
                  'source_audio_subjectively_auditioned':False,'song_presence_claimed':False,'reuse_rights_checked':False,
                  'source_id_history_check':'Compared against available EP15–EP22 source manifests; selected IDs are not reused.'}
        mpath=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
        with open(mpath,'w') as f:json.dump(manifest,f,indent=2)
        print(json.dumps({'episode':ep,'base_source':base,'info':info,'plan':planpath,'manifest':mpath,'clips':manifest['clips']},indent=2))
