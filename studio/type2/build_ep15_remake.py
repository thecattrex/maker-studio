#!/usr/bin/env python3
"""Build EP15 replacement source with the selected four fresh windows.
Source audio is kept and synchronized; no source audio is muted. The Dailymotion
sources are visually reviewed, but this script does not claim human listening.
"""
import json,os,subprocess,sys
sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/studio/type2';CAND='/home/user/dl/src/ep15_remake_candidates';ASSETS=os.path.join(ROOT,'assets')
# Rank order strongest to weakest, in the order used by the ladder/title plan.
CLIPS=[
 {'id':'x9lorig','ss':0.0,'dur':5.5,'crop':(0,106,480,635),'label':'BENCH PRANK','sfx':('fail',2.2)},
 {'id':'x95yj4a','ss':0.0,'dur':10.0,'crop':(0,138,608,804),'label':'FAILED CATCH','sfx':('oof',5.7)},
 {'id':'x9weqas','ss':0.0,'dur':6.3,'crop':(0,106,480,635),'label':'HOT TRAY DROP','sfx':('slap',3.9)},
 {'id':'x9m3tj6','ss':0.0,'dur':5.7,'crop':(0,106,480,635),'label':'BEER & PASTA','sfx':('oof',3.4)},
]
OUT=os.path.join(ASSETS,'ep15_remake_natural_audio_source.mp4');os.makedirs(ASSETS,exist_ok=True)
inputs=[];fc=[];offset=0.0
for i,c in enumerate(CLIPS):
 p=f"{CAND}/{c['id']}/{c['id']}.mp4";c['path']=p;info=probe(p);x,y,w,h=c['crop']
 if not info.get('has_audio'):raise RuntimeError(f"{c['id']} has no source audio")
 if c['ss']+c['dur']>info['duration']+0.03:raise RuntimeError(f"window out of range {c['id']}: {info['duration']}")
 if x+w>info['width'] or y+h>info['height']:raise RuntimeError(f"bad crop {c['id']} {c['crop']} vs {info['width']}x{info['height']}")
 inputs += ['-i',p]
 fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=480:636:flags=lanczos,fps=30,setsar=1,format=yuv420p[v{i}]')
 fc.append(f'[{i}:a]atrim=start={c["ss"]}:duration={c["dur"]},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={c["dur"]}[a{i}]')
 c['base_ss']=round(offset,4);offset+=c['dur']
fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(CLIPS)))+f'concat=n={len(CLIPS)}:v=1:a=1[outv][outa]')
cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[outv]','-map','[outa]','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',OUT]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode:raise RuntimeError((r.stderr or '')[-4000:])
info=probe(OUT);assert info['has_audio'] and abs(info['duration']-offset)<0.12
# Stable four-clip Type-2 ladder, played #4 → #1; source audio is foreground, BGM deliberately very low.
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'}
items=[]
for i,c in enumerate(CLIPS,1):
 items.append({'n':i,'ss':c['base_ss'],'dur':c['dur'],'label':c['label'],'color':COLORS[i],
               'focus':[0.5,0.5],'zoom_to':1.0,'crop_top':0.0,'crop_bottom':0.0,
               'sfx':[{'at':c['sfx'][1],'key':c['sfx'][0]}]})
plan={
 'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],
 'band':360,'bottom':132,'gap':0.16,'items':items,
 'music':os.path.join(ASSETS,'c2_48.wav'),'music_ss':0.0,'music_vol':0.035,
 'clip_vol':0.68,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-17.0,
 'ladder':'asc','order':[3,2,1,0],'title_size':116
}
planpath=os.path.join(ROOT,'plan_ep15_remake_natural_audio.json');json.dump(plan,open(planpath,'w'),indent=2)
manifest={'clips':[{k:c[k] for k in ['id','ss','dur','crop','label','base_ss','path']} for c in CLIPS],
          'base_source':OUT,'duration':info['duration'],'plan':planpath,
          'history_audit':'x9bi13o and x9ejedo/x9wy8kc excluded as prior final sources; x9m3tj6/x9weqas/x95yj4a absent from audited prior episode source records; x9lorig appears in old EP10/11 candidate rejection note only and was not in audited final build sources; its overlay-free crop was re-reviewed.'}
json.dump(manifest,open(os.path.join(ROOT,'EP15_remake_source_manifest.json'),'w'),indent=2)
print(json.dumps({'source':OUT,'duration':info['duration'],'has_audio':info['has_audio'],'plan':planpath,'clips':manifest['clips']},indent=2))
