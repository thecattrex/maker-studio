#!/usr/bin/env python3
"""Build versioned EP10/EP11 Type-2 drafts from fresh, unique source clips.

Keeps the previously praised four-clip ranking layout. Source audio is fully
muted; only the series BGM and one impact SFX per clip are included.
"""
import json, os, subprocess, sys
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe

ROOT='/home/user/studio/type2'
ASSETS=os.path.join(ROOT,'assets')
FF=ensure_ffmpeg()
PAD_TOP=246
PAD_FRAC=PAD_TOP/1920
TITLE=[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]]
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'}
SFX_DIR='/home/user/studio/trial/sfx'

# Clips stored in rank order (#1 strongest -> #4), with precise source crop and
# selected source-time window. Frame crops normalize to the locked 1080x1428 view.
EPISODES={
 10:[
  {'id':'xapnfqm','path':'/home/user/dl/src/dailymotion_more/xapnfqm.mp4','ss':2.4,'dur':4.8,'label':'YARD TUMBLE','crop':(1080,1428,0,250),'sfx':('fail',1.9)},
  {'id':'x9i49e6','path':'/home/user/dl/src/dailymotion_more/x9i49e6.mp4','ss':6.2,'dur':5.2,'label':'PULL-UP BAR FAIL','crop':(680,899,0,270),'sfx':('oof',3.2)},
  {'id':'x9t3594','path':'/home/user/dl/src/dailymotion_more/x9t3594.mp4','ss':0.3,'dur':2.7,'label':'ICY STEP SLIP','crop':(720,952,600,64),'sfx':('ba_drum_tss',1.7)},
  {'id':'xbgrqde','path':'/home/user/dl/src/dailymotion_more/xbgrqde.mp4','ss':1.4,'dur':4.6,'label':'CONE RUN TRIP','crop':(474,628,0,220),'sfx':('yeet',3.3)},
 ],
 11:[
  {'id':'x9uf2f6','path':'/home/user/dl/src/dailymotion_more/x9uf2f6.mp4','ss':0.0,'dur':6.9,'label':'ZIPLINE WIPEOUT','crop':(2160,2856,0,600),'sfx':('fail',5.2)},
  {'id':'7507692898574552342','path':'/home/user/dl/src/tiktok/tt_7507692898574552342.mp4','ss':8.4,'dur':5.5,'label':'POOL EDGE FALL','crop':(850,1124,115,450),'sfx':('ba_drum_tss',3.1)},
  {'id':'7488031370086780190','path':'/home/user/dl/src/tiktok/tt_7488031370086780190.mp4','ss':0.2,'dur':4.8,'label':'RINK STUMBLE','crop':(1080,1428,0,0),'sfx':('oof',4.1)},
  {'id':'xbe8qie','path':'/home/user/dl/src/dailymotion_more/xbe8qie.mp4','ss':0.2,'dur':4.4,'label':'RAINY PATH SLIP','crop':(480,635,0,70),'sfx':('slap',2.7)},
 ]
}

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError('CMD FAILED\n'+' '.join(cmd)+'\n'+(p.stderr or '')[-5000:])
    return p

def build(ep, clips):
    out_source=f'{ASSETS}/ep{ep}_fresh_silent.mp4'
    raw=f'/tmp/ep{ep}_fresh_raw.mp4'
    inputs=[]; chains=[]
    cursor=0.0
    for i,c in enumerate(clips):
        if not os.path.isfile(c['path']): raise FileNotFoundError(c['path'])
        info=probe(c['path'])
        if c['ss'] < 0 or c['ss']+c['dur'] > info['duration']+0.03:
            raise ValueError(f"EP{ep} {c['id']} crop window outside source: {info['duration']}")
        cw,ch,cx,cy=c['crop']
        if cx+cw>info['width'] or cy+ch>info['height']:
            raise ValueError(f"EP{ep} {c['id']} crop {c['crop']} outside {info['width']}x{info['height']}")
        inputs += ['-i',c['path']]
        chains.append(
          f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,'
          f'crop={cw}:{ch}:{cx}:{cy},scale=1080:1428:flags=lanczos,'
          f'pad=1080:1920:0:{PAD_TOP}:color=black,fps=30,setsar=1,format=yuv420p[v{i}]')
        c['offset']=round(cursor,6)
        cursor+=c['dur']
    chains.append(''.join(f'[v{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=0[outv]')
    run([FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(chains),
         '-map','[outv]','-an','-c:v','libx264','-crf','17','-preset','fast',
         '-pix_fmt','yuv420p','-r','30','-movflags','+faststart',raw])
    run([FF,'-hide_banner','-v','error','-y','-i',raw,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo',
         '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k',
         '-shortest','-movflags','+faststart',out_source])
    os.remove(raw)

    items=[]
    for n,c in enumerate(clips,1):
        key,at=c['sfx']
        items.append({'n':n,'ss':c['offset'],'dur':c['dur'],'label':c['label'],'color':COLORS[n],
                      'focus':[0.5,0.5],'zoom_to':1.0,
                      'crop_top':PAD_FRAC,'crop_bottom':PAD_FRAC,
                      'sfx':[{'at':at,'key':key}]})
    plan={'title':TITLE,'band':360,'bottom':132,'gap':0.16,'items':items,
          'music':f'{ASSETS}/c2_48.wav','music_ss':0.0,'music_vol':0.17,
          'clip_vol':0.0,'sfx_dir':SFX_DIR,'sfx_peak_db':-7.5,
          'ladder':'asc','order':[3,2,1,0], 'title_size':116}
    ppath=f'{ROOT}/plan_ep{ep}_fresh.json'
    with open(ppath,'w') as f: json.dump(plan,f,indent=2)
    print(f'EP{ep}: {out_source} ({probe(out_source)["duration"]:.3f}s)')
    print(f'plan: {ppath}; rank-order trims:',[(c['id'],c['ss'],c['dur'],c['crop']) for c in clips])

if __name__=='__main__':
    for ep,clips in EPISODES.items(): build(ep,clips)
