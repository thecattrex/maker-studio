#!/usr/bin/env python3
"""Build fresh EP12/EP13 Type-2 silent sources and ranking plans.

Only new one-off source IDs are used. All original clip audio is muted; the
series soundtrack and impact SFX are laid in by run.py from the approved plan.
"""
import json,os,subprocess,sys
sys.path.insert(0,'/home/user/studio')
from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/studio/type2';AS=os.path.join(ROOT,'assets')
PAD_TOP=246;PAD_FRAC=PAD_TOP/1920;SFX_DIR='/home/user/studio/trial/sfx'
TITLE=[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]]
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'}
# Rank order #1 strongest -> #4 lighter. Playback order is #4 -> #1.
EPISODES={
 12:[
  {'id':'x9bi13o','ss':3.0,'dur':6.3,'label':'CHALLENGE FLOOR FAIL','crop':(0,150,420,556),'sfx':('fail',2.45)},
  {'id':'x9q3d02','ss':0.0,'dur':4.1,'label':'BIKE WHEELIE WIPEOUT','crop':(0,100,480,635),'sfx':('yeet',2.55)},
  {'id':'x9ejedo','ss':0.0,'dur':3.7,'label':'POGO STICK FAIL','crop':(0,70,480,635),'sfx':('oof',1.8)},
  {'id':'x9rxxiq','ss':0.5,'dur':6.5,'label':'SKATEBOARD SHUVIT FAIL','crop':(242,0,363,480),'sfx':('ba_drum_tss',5.0)},
 ],
 13:[
  {'id':'x9wy8kc','ss':4.0,'dur':5.1,'label':'TUMBLING ROUTINE FAIL','crop':(0,120,480,635),'sfx':('fail',3.8)},
  {'id':'x9o5ajg','ss':7.5,'dur':4.6,'label':'MOMS RACE WIPEOUT','crop':(13,80,453,600),'sfx':('yeet',0.9)},
  {'id':'xa1xumo','ss':1.5,'dur':5.8,'label':'SNOW TUBE WIPEOUT','crop':(0,100,480,635),'sfx':('oof',3.0)},
  {'id':'xbfbsli','ss':0.0,'dur':4.6,'label':'TABLE ROUTINE FAIL','crop':(0,60,480,635),'sfx':('ba_drum_tss',3.6)},
 ]
}

def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode: raise RuntimeError('COMMAND FAILED\n'+' '.join(cmd)+'\n'+(p.stderr or '')[-3000:])

def build(ep,items):
 raw=f'{AS}/ep{ep}_type2_fresh_raw.mp4';silent=f'{AS}/ep{ep}_type2_fresh_silent.mp4'
 args=[];filters=[];offset=0.0
 for i,c in enumerate(items):
  p=f"/home/user/dl/src/ep12_13_candidates/{c['id']}/{c['id']}.mp4"
  if not os.path.isfile(p):raise FileNotFoundError(p)
  inf=probe(p);x,y,w,h=c['crop']
  if c['ss']<0 or c['ss']+c['dur']>inf['duration']+0.03:raise ValueError(f"EP{ep} {c['id']} window out of bounds ({inf['duration']})")
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
 ppath=f'{ROOT}/plan_ep{ep}_fresh.json';json.dump(plan,open(ppath,'w'),indent=2)
 print(f'EP{ep} source {silent} | {probe(silent)["duration"]:.2f}s')
 print('plan',ppath)
 print([(c['id'],c['ss'],c['dur'],c['label'],c['sfx']) for c in items])
if __name__=='__main__':
 for ep,items in EPISODES.items():build(ep,items)
