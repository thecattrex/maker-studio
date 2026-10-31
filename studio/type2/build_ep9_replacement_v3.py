import json,os,subprocess,sys,tempfile
sys.path.insert(0,'/home/user/studio');from util import ensure_ffmpeg,probe
FF=ensure_ffmpeg();ROOT='/home/user/studio/type2';AS='/home/user/dl/src/tiktok';OUT='/home/user/dl'
# New unique sources for the previously overlaid/unclear EP9 track and hoop beats.
clips=[
 {'id':'7421957784075324718','ss':0.0,'dur':5.3,'label':'DRIVEWAY SLIP','crop':"crop=608:1080:350:0,scale=1080:1920:flags=lanczos"},
 {'id':'7442854366744153375','ss':3.2,'dur':3.8,'label':'SOCCER WIPEOUT','crop':'scale=1080:1920:flags=lanczos'},
 {'id':'7507500402800151851','ss':16.3,'dur':4.8,'label':'DAD PRANK PAYBACK','crop':'scale=1080:1920:flags=lanczos'},
 {'id':'7350440630297824554','ss':0.0,'dur':4.2,'label':'WIND-BLOWN TENT','crop':'scale=1080:1920:flags=lanczos'},
]
inputs=[];fc=[];items=[];offset=0.0
for i,c in enumerate(clips):
 p=f"{AS}/tt_{c['id']}.mp4"
 if not os.path.exists(p):raise FileNotFoundError(p)
 d=probe(p)['duration']
 if c['ss']+c['dur']>d:raise ValueError(f"{c['id']} window exceeds {d}")
 inputs += ['-ss',str(c['ss']),'-t',str(c['dur']),'-i',p]
 fc.append(f'[{i}:v]fps=30,setsar=1,{c["crop"]},setsar=1,format=yuv420p[v{i}]')
 it={'n':i+1,'ss':round(offset,4),'dur':c['dur'],'label':c['label'],'color':{1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H0000D7FF&'}[i+1],'focus':[0.5,0.55],'zoom_to':1.0,'sfx':[]}
 if i==0: it['crop_top']=0.0
 if i==1: it['crop_top']=0.0
 if i==2: it['crop_bottom']=0.30
 if i==3: it.update({'crop_top':0.06,'crop_bottom':0.28})
 items.append(it);offset+=c['dur']
fc.append(''.join(f'[v{i}]' for i in range(4))+'concat=n=4:v=1:a=0[outv]')
source=f'{OUT}/EP9_Type2_Replacement_Source_v3.mp4'
subprocess.run([FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[outv]','-an','-c:v','libx264','-crf','17','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',source],check=True)
silence=f'{ROOT}/assets/ep9_replacement_source_silence_v3.wav'
subprocess.run([FF,'-hide_banner','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','30','-c:a','pcm_s16le',silence],check=True)
plan={'title':[[['Ranking Best','&H00FFFFFF&'],['Fail','&H002828F0&']],[['Moments','&H0000D7FF&']]],'band':360,'bottom':132,'gap':0.16,'items':items,'music':None,'music_ss':0.0,'music_vol':0.0,'clip_vol':0.0,'sfx_dir':'/home/user/studio/trial/sfx','sfx_peak_db':-10.0,'ladder':'asc','order':[3,2,1,0]}
with open(f'{ROOT}/plan_ep9_replacement_v3.json','w') as f:json.dump(plan,f,indent=2)
cfg=json.load(open(f'{ROOT}/config_ep9_replacement_v2.json'))
# Keep series soundtrack/SFX and rebuild clip metadata against new rank order.
ranked=[(4,clips[3]),(3,clips[2]),(2,clips[1]),(1,clips[0])]
sfx={4:('yeet',-7.0),3:('ba_drum_tss',-8.0),2:('oof',-7.5),1:('fail',-6.0)}
cfg['clips']=[]
for n,c in ranked:
 key,peak=sfx[n]
 cfg['clips'].append({'n':n,'ss':0.0,'dur':c['dur'],'label':c['label'],'color':{1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H0000D7FF&'}[n],'sfx':{'key':key,'at':max(0,c['dur']-0.7),'peak_db':peak},'audio_file':silence})
with open(f'{ROOT}/config_ep9_replacement_v3.json','w') as f:json.dump(cfg,f,indent=2)
print(source,probe(source)['duration'],[(c['id'],c['ss'],c['dur']) for c in clips])
