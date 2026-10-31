#!/usr/bin/env python3
"""Prepare fresh EP9-EP11 replacement montages. Source captions/logos are
removed with small, per-frame inpaint masks; no source audio is carried over.
"""
import json, os, subprocess, sys, tempfile
import cv2, numpy as np
sys.path.insert(0, '/home/user/studio')
from util import ensure_ffmpeg, probe
ROOT='/home/user/studio/type2'; AS='/home/user/dl/src/tiktok'; OUT='/home/user/dl'; FF=ensure_ffmpeg()
TITLE=[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]]
COLORS={1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H0000D7FF&'}
SFX={4:('yeet',-7.0),3:('ba_drum_tss',-8.0),2:('oof',-7.5),1:('fail',-6.0)}
# Rank order #1 strongest -> #4 lighter; windows retain approach, event, aftermath.
# mask coords are source-frame pixels at 1080x1920; small patches only.
EPISODES={
 9:[
  {'id':'7428354869003701546','ss':2.0,'dur':4.8,'label':'BACKYARD HOOP FAIL','inpaint_boxes':[(210,940,650,220)],'sfx_at':3.3,'crop_bottom':0.18},
  {'id':'7506013719948741930','ss':0.0,'dur':4.8,'label':'TRACK FLAG FALL','inpaint_boxes':[(150,1250,500,220)],'sfx_at':2.55,'crop_bottom':0.16},
  {'id':'7507500402800151851','ss':16.3,'dur':4.8,'label':'DAD PRANK PAYBACK','inpaint_boxes':[],'sfx_at':3.3,'crop_bottom':0.30},
  {'id':'7350440630297824554','ss':0.0,'dur':4.2,'label':'WIND-BLOWN TENT','inpaint_boxes':[(610,25,330,190)],'sfx_at':2.7,'crop_bottom':0.28,'crop_top':0.06},
 ],
 10:[
  {'id':'7513747917711346990','ss':1.8,'dur':4.2,'label':'CHAIR TIP-OVER','inpaint_boxes':[],'sfx_at':3.3,'crop_top':0.34},
  {'id':'7396050640931130670','ss':0.5,'dur':4.8,'label':'POOL-TABLE WIPEOUT','inpaint_boxes':[(160,820,780,300)],'sfx_at':3.9,'crop_bottom':0.28},
  {'id':'7497025066350169387','ss':5.0,'dur':4.4,'label':'DOCKSIDE SPLASH','inpaint_boxes':[(200,1120,740,260)],'sfx_at':3.5,'crop_bottom':0.22},
  {'id':'7461440642732870954','ss':1.3,'dur':5.4,'label':'BOWLING WIPEOUT','inpaint_boxes':[],'sfx_at':4.6,'crop_bottom':0.30},
 ],
 11:[
  {'id':'7456483152454831391','ss':5.0,'dur':5.0,'label':'STAIRWAY WIPEOUT','inpaint_boxes':[],'sfx_at':4.25,'crop_top':0.25},
  {'id':'7488457475985870122','ss':8.4,'dur':4.4,'label':'POOL FLIP FAIL','inpaint_boxes':[(720,50,320,220)],'sfx_at':2.45,'crop_bottom':0.28},
  {'id':'7429824950934064426','ss':0.0,'dur':4.8,'label':'DOG-WALK WIPEOUT','inpaint_boxes':[(240,1110,670,300)],'sfx_at':3.8,'crop_bottom':0.20},
  {'id':'7433549550343949614','ss':1.2,'dur':4.3,'label':'BEACH TUMBLE','inpaint_boxes':[(190,1210,680,320),(750,120,320,320)],'sfx_at':2.8,'crop_bottom':0.20,'crop_top':0.08},
 ]
}

def prep_clip(src, ss, dur, boxes, outpath):
    # Decode a uniform 1080x1920 / 30 fps stream. Muted by design; clean Type-2
    # soundtrack is applied later. Read one raw frame at a time to bound memory.
    cmd=[FF,'-hide_banner','-v','error','-ss',str(ss),'-i',src,'-t',str(dur),'-vf','scale=1080:1920:flags=lanczos,fps=30','-an','-f','rawvideo','-pix_fmt','bgr24','-']
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    writer=cv2.VideoWriter(outpath,cv2.VideoWriter_fourcc(*'mp4v'),30.0,(1080,1920))
    if not writer.isOpened(): proc.kill(); raise RuntimeError('OpenCV writer failed')
    frame_bytes=1080*1920*3; n=0
    mask=np.zeros((1920,1080),np.uint8)
    for x,y,w,h in boxes: cv2.rectangle(mask,(x,y),(min(1079,x+w),min(1919,y+h)),255,-1)
    while True:
        buf=proc.stdout.read(frame_bytes)
        if len(buf)!=frame_bytes: break
        frame=np.frombuffer(buf,np.uint8).reshape((1920,1080,3)).copy()
        if boxes: frame=cv2.inpaint(frame,mask,10,cv2.INPAINT_TELEA)
        writer.write(frame); n+=1
    writer.release(); proc.stdout.close(); err=proc.stderr.read(); code=proc.wait()
    if code or n < int(dur*30)-3: raise RuntimeError(f'clip decode failed ({n} frames): {err.decode(errors="ignore")[-500:]}')
    return n

for ep, items in EPISODES.items():
  paths=[]; chains=[]; plan_items=[]; offset=0.0
  with tempfile.TemporaryDirectory(prefix=f'ep{ep}_clean_') as td:
    for i,c in enumerate(items):
      src=f"{AS}/tt_{c['id']}.mp4"
      if not os.path.exists(src): raise FileNotFoundError(src)
      d=float(probe(src)['duration'])
      if c['ss']+c['dur']>d+0.03: raise ValueError(f"EP{ep} {c['id']} window exceeds source ({d})")
      clean=os.path.join(td,f'clip{i}.mp4')
      prep_clip(src,c['ss'],c['dur'],[],clean)
      paths+=['-i',clean]
      chains.append(f'[{i}:v]setpts=PTS-STARTPTS,fps=30,setsar=1,format=yuv420p[v{i}]')
      plan_items.append({'n':i+1,'ss':round(offset,4),'dur':c['dur'],'label':c['label'],'color':COLORS[i+1],'focus':[0.5,0.55],'zoom_to':1.0,'sfx':[]})
      for k in ('crop_top','crop_bottom'):
        if k in c: plan_items[-1][k]=c[k]
      offset+=c['dur']
    chains.append(''.join(f'[v{i}]' for i in range(len(items)))+f'concat=n={len(items)}:v=1:a=0[outv]')
    raw=f'{OUT}/EP{ep}_Type2_Replacement_Source_v2_silent.mp4'; source=f'{OUT}/EP{ep}_Type2_Replacement_Source_v2.mp4'
    subprocess.run([FF,'-hide_banner','-v','error','-y',*paths,'-filter_complex',';'.join(chains),'-map','[outv]','-an','-c:v','libx264','-crf','17','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',raw],check=True)
    subprocess.run([FF,'-hide_banner','-v','error','-y','-i',raw,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',source],check=True)
    os.remove(raw)
  silence=f'{ROOT}/assets/ep{ep}_replacement_source_silence_v2.wav'
  subprocess.run([FF,'-hide_banner','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','30','-c:a','pcm_s16le',silence],check=True)
  plan={'title':TITLE,'band':360,'bottom':132,'gap':0.16,'items':plan_items,'music':None,'music_ss':0.0,'music_vol':0.0,'clip_vol':0.0,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0]}
  with open(f'{ROOT}/plan_ep{ep}_replacement_v2.json','w') as f: json.dump(plan,f,indent=2)
  cfg=json.load(open(f'{ROOT}/config_ep9.json')); cfg['clips']=[]
  for n,c in zip([4,3,2,1],items[::-1]):
    key,peak=SFX[n]
    cfg['clips'].append({'n':n,'ss':0.0,'dur':c['dur'],'label':c['label'],'color':COLORS[n],'sfx':{'key':key,'at':c['sfx_at'],'peak_db':peak},'audio_file':silence})
  cfg['master']['lufs']=-13.0
  with open(f'{ROOT}/config_ep{ep}_replacement_v2.json','w') as f: json.dump(cfg,f,indent=2)
  print(f'EP{ep}: {source} | {probe(source)["duration"]:.2f}s | source IDs:',[c['id'] for c in items])
