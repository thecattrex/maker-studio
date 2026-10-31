#!/usr/bin/env python3
"""Build EP14/EP15 Type-2 silent cut assets and familiar ranking plans.

Original source audio is deliberately muted. The approved Type-2 BGM/SFX are
added later by run.py ranking, matching EP12/EP13's validated path.
"""
import json,os,subprocess,sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/studio/type2';AS=os.path.join(ROOT,'assets');SRC='/home/user/dl/src/ep14_15_candidates'
PAD_TOP=246;PAD_FRAC=PAD_TOP/1920;SFX_DIR='/home/user/studio/trial/sfx'
TITLE=[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]]
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'}
# Rank order #1 strongest -> #4 lighter; playback order is #4 -> #1.
EPISODES={
 14:[
  {'id':'xbqy0iy','ss':11.0,'dur':5.0,'label':'TRAMPOLINE WIPEOUT','crop':(0,100,480,635),'sfx':('fail',3.0)},
  {'id':'x9um1u0','ss':4.2,'dur':4.2,'label':'OVEN CAKE DROP','crop':(0,150,480,635),'sfx':('oof',2.2)},
  {'id':'xapidry','ss':5.5,'dur':8.0,'label':'WATERSLIDE SPILL','crop':(0,80,480,635),'sfx':('yeet',3.0)},
  {'id':'xa1goko','ss':0.0,'dur':4.2,'label':'BOTTLE BURST','crop':(0,60,480,635),'sfx':('ba_drum_tss',1.0)},
 ],
 15:[
  {'id':'xayt822','ss':2.5,'dur':5.3,'label':'BOAT-SIDE TUMBLE','crop':(289,60,270,357),'sfx':('yeet',1.5)},
  {'id':'xbmm542','ss':12.5,'dur':8.3,'label':'TRAY FLIP','crop':(0,170,480,635),'sfx':('ba_drum_tss',6.0)},
  {'id':'xaolx2e','ss':2.0,'dur':6.8,'label':'SAUCE BOTTLE FAIL','crop':(0,100,480,635),'sfx':('oof',3.2)},
  {'id':'x9spdi4','ss':32.0,'dur':7.8,'label':'TREADMILL TROUBLE','crop':(0,60,480,635),'sfx':('fail',3.3)},
 ]
}

def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError('COMMAND FAILED\n'+' '.join(cmd)+'\n'+(p.stderr or '')[-3000:])

def build(ep,items):
 raw=f'{AS}/ep{ep}_type2_raw.mp4';silent=f'{AS}/ep{ep}_type2_silent.mp4';args=[];filters=[];offset=0.0
 for i,c in enumerate(items):
  p=f"{SRC}/{c['id']}/{c['id']}.mp4"
  if not os.path.isfile(p):raise FileNotFoundError(p)
  inf=probe(p);x,y,w,h=c['crop']
  if c['ss']<0 or c['ss']+c['dur']>inf['duration']+0.03:raise ValueError(f"EP{ep} {c['id']} source window out of bounds ({inf['duration']})")
  if x+w>inf['width'] or y+h>inf['height']:raise ValueError(f"EP{ep} {c['id']} crop {c['crop']} exceeds {inf['width']}x{inf['height']}")
  if abs(w/h-1080/1428)>0.002:raise ValueError(f"EP{ep} {c['id']} crop aspect {w/h:.5f} != {1080/1428:.5f}")
  args+=['-i',p]
  filters.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=1080:1428:flags=lanczos,pad=1080:1920:0:{PAD_TOP}:color=black,fps=30,setsar=1,format=yuv420p[v{i}]')
  c['offset']=round(offset,6);offset+=c['dur']
 filters.append(''.join(f'[v{i}]' for i in range(len(items)))+f'concat=n={len(items)}:v=1:a=0[outv]')
 run([FF,'-hide_banner','-v','error','-y',*args,'-filter_complex',';'.join(filters),'-map','[outv]','-an','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',raw])
 run([FF,'-hide_banner','-v','error','-y','-i',raw,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',silent])
 os.remove(raw)
 planitems=[]
 for n,c in enumerate(items,1):
  key,at=c['sfx'];planitems.append({'n':n,'ss':c['offset'],'dur':c['dur'],'label':c['label'],'color':COLORS[n],'focus':[0.5,0.5],'zoom_to':1.0,'crop_top':PAD_FRAC,'crop_bottom':PAD_FRAC,'sfx':[{'at':at,'key':key}]})
 plan={'title':TITLE,'band':360,'bottom':132,'gap':0.16,'items':planitems,'music':f'{AS}/c2_48.wav','music_ss':0.0,'music_vol':0.17,'clip_vol':0.0,'sfx_dir':SFX_DIR,'sfx_peak_db':-7.5,'ladder':'asc','order':[3,2,1,0],'title_size':116}
 ppath=f'{ROOT}/plan_ep{ep}_type2.json';json.dump(plan,open(ppath,'w'),indent=2)
 print(f'EP{ep} silent source {silent} | {probe(silent)["duration"]:.2f}s')
 print('plan',ppath)
 print([(c['id'],c['ss'],c['dur'],c['crop'],c['label'],c['sfx']) for c in items])
if __name__=='__main__':
 os.makedirs(AS,exist_ok=True)
 for ep,items in EPISODES.items():build(ep,items)
