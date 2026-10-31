#!/usr/bin/env python3
"""Build EP33 and EP34 in the accepted EP29-style Type-2 ranking layout."""
import os, sys, json, subprocess, hashlib, wave
from datetime import datetime, timezone
import numpy as np
import imageio_ffmpeg
sys.path.insert(0, '/home/user/studio')
from util import probe
from templates import build_ranking, save_overlay

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = '/home/user/studio/type2'
OUTDIR = '/home/user/studio/out'
SRC = '/home/user/dl/src/ep33_34_candidates'
ASSETS = os.path.join(ROOT, 'assets')
SFXDIR = '/home/user/studio/trial/sfx'
BGM = os.path.join(ASSETS, 'c2_48.wav')
SR = 48000
W, H, FPS = 480, 636, 30
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

EPISODES = {
 33: {
  'slug':'craziest_fails', 'title': [[('Ranking','&H00FFFFFF&'),('Craziest','&H002828F0&')],[('Fails','&H0000D7FF&')]],
  'title_text':'RANKING CRAZIEST FAILS',
  'clips':[
   {'id':'SVvmsBpxhaY','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/SVvmsBpxhaY','path':f'{SRC}/SVvmsBpxhaY.mp4','ss':0.0,'end':5.8,'crop':[0,128,576,768],'label':'CHAIR FAIL','rank':4,'impact':5.55,'sfx':'oof','sfx_at':5.70,'note':'Chair tips during a casual outdoor sit; the adult lands on grass. Clip ends just after the fall.'},
   {'id':'8a9ne-ABev0','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/8a9ne-ABev0','path':f'{SRC}/8a9ne-ABev0.mp4','ss':2.5,'end':7.2,'crop':[0,100,720,960],'label':'GYM MAT','rank':3,'impact':6.95,'sfx':'yeet','sfx_at':4.60,'note':'Gymnastics attempt ends on a padded mat; setup and landing are retained.'},
   {'id':'wrylswYMWhE','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/wrylswYMWhE','path':f'{SRC}/wrylswYMWhE.mp4','ss':8.5,'end':11.65,'crop':[0,240,1080,1440],'label':'SNOW TUBE','rank':2,'impact':11.5,'sfx':'quack','sfx_at':3.15,'note':'Snow-tubing collision sends a rider off their feet into soft snow; edit ends 0.15 seconds after the visible impact.'},
   {'id':'n1Y43D-fqwo','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/n1Y43D-fqwo','path':f'{SRC}/n1Y43D-fqwo.mp4','ss':4.4,'end':8.6,'crop':[0,160,720,960],'label':'MUD RUN','rank':1,'impact':8.35,'sfx':'ba_drum_tss','sfx_at':4.10,'note':'Mud-run participant loses footing and falls on the soft muddy track; clip stops after the landing.'},
  ]},
 34: {
  'slug':'outdoor_wipeouts', 'title': [[('Ranking','&H00FFFFFF&'),('Outdoor','&H002828F0&')],[('Wipeouts','&H0000D7FF&')]],
  'title_text':'RANKING OUTDOOR WIPEOUTS',
  'clips':[
   {'id':'e8f5U_M9O0c','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/e8f5U_M9O0c','path':f'{SRC}/e8f5U_M9O0c.mp4','ss':0.0,'end':3.4,'crop':[0,200,1080,1440],'label':'WATER SLIDE','rank':4,'impact':3.2,'sfx':'slap','sfx_at':3.35,'note':'Inflatable water-slide ride ends in an awkward splashdown; no speed change.'},
   {'id':'5kSzTZe5jj4','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/5kSzTZe5jj4','path':f'{SRC}/5kSzTZe5jj4.mp4','ss':9.8,'end':14.0,'crop':[0,320,1440,1920],'label':'OBSTACLE RACE','rank':3,'impact':13.8,'sfx':'yeet','sfx_at':4.15,'note':'Two competitors tackle the final inflatable obstacle and splash into the pool; cut just after landing.'},
   {'id':'VVJOJTud5BI','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/VVJOJTud5BI','path':f'{SRC}/VVJOJTud5BI.mp4','ss':21.5,'end':26.2,'crop':[0,80,352,469],'label':'MUD HILL','rank':2,'impact':26.0,'sfx':'bruh','sfx_at':4.65,'note':'A person loses balance while running down a muddy slope and lands in the soft mud; cut immediately after impact.'},
   {'id':'ok-I1AoXDKk','platform':'YouTube Shorts','url':'https://www.youtube.com/shorts/ok-I1AoXDKk','path':f'{SRC}/ok-I1AoXDKk.mp4','ss':0.8,'end':5.7,'crop':[0,400,2160,2880],'label':'ROPE SWING','rank':1,'impact':5.55,'sfx':'quack','sfx_at':4.90,'note':'Rope-swing attempt ends with a controlled splash into the lake; setup through splashdown.'},
  ]},
}

def run(cmd, label):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'{label} failed ({p.returncode}):\n{p.stderr[-5000:]}')
    return p


def base_render(ep, spec):
    base = os.path.join(ASSETS, f'ep{ep}_ep29style_base.mp4')
    inputs, filters = [], []
    cursor = 0.0
    for i,c in enumerate(spec['clips']):
        if not os.path.isfile(c['path']): raise FileNotFoundError(c['path'])
        info = probe(c['path']); x,y,w,h = c['crop']
        if x+w > info['width'] or y+h > info['height']:
            raise ValueError(f"Crop out of bounds: EP{ep} {c['id']} {c['crop']} for {info['width']}x{info['height']}")
        dur = round(c['end']-c['ss'], 6)
        inputs += ['-i', c['path']]
        filters.append(f'[{i}:v]trim=start={c["ss"]}:duration={dur},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p[v{i}]')
        c['dur'] = dur
        c['timeline_start'] = round(cursor, 3)
        c['timeline_end'] = round(cursor+dur, 3)
        cursor += dur
    filters.append(''.join(f'[v{i}]' for i in range(len(spec['clips']))) + f'concat=n={len(spec["clips"])}:v=1:a=0[outv]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[outv]','-an','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-r',str(FPS),'-movflags','+faststart',base]
    run(cmd,f'EP{ep} base render')
    return base


def make_video(ep, spec, base):
    out = os.path.join(OUTDIR, f'EP{ep}_Type2_Final_EP29Style_2026-10-31.mp4')
    video_only = os.path.join(OUTDIR, f'EP{ep}_Type2_EP29Style_video_only.mp4')
    ass = os.path.join('/home/user/studio/work', f'ep{ep}-ep29style-2026-10-29.ass')
    items=[]
    for c in spec['clips']:
        items.append({'ss':c['timeline_start'],'dur':c['dur'],'n':c['rank'],'label':c['label'],'color':{1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'}[c['rank']],'focus':(0.5,0.5),'zoom_to':1.0,'sfx':[]})
    tl=build_ranking(base,items,title=spec['title'],band=360,bottom=132,gap=0.0,size=(1080,1920),watermark='@studio',order=[0,1,2,3],title_size=116,ladder='asc',music=None,music_vol=0.0,clip_vol=0.0,sfx_dir=None)
    save_overlay(tl,ass)
    tl.segments=[seg for seg in tl.segments if seg.out_dur()>0.01]
    for seg in tl.segments: seg.mute=True
    tl.music=None; tl.sfx=[]; tl.original_vol=0.0; tl.master_gain_db=0.0
    tl.build(video_only,crf=18,preset='medium',loudnorm=False)
    return video_only,out,ass


def decode_audio(path, ss=0.0, dur=None):
    cmd=[FF,'-hide_banner','-v','error','-i',path]
    if ss: cmd += ['-ss',str(ss)]
    if dur is not None: cmd += ['-t',str(dur)]
    cmd += ['-vn','-ac','2','-ar',str(SR),'-f','f32le','-']
    p=subprocess.run(cmd,capture_output=True)
    if p.returncode: raise RuntimeError(f'audio decode failed for {path}: {p.stderr[-2000:].decode(errors="replace")}')
    return np.frombuffer(p.stdout,dtype=np.float32).reshape(-1,2).copy()


def read_wav(path):
    with wave.open(path,'rb') as w:
        if w.getframerate()!=SR: raise ValueError(f'BGM sample rate {w.getframerate()} != {SR}')
        ch=w.getnchannels(); raw=w.readframes(w.getnframes())
    x=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768.0
    x=x.reshape(-1,ch)
    if ch==1: x=np.repeat(x,2,axis=1)
    elif ch>2: x=x[:,:2]
    return x


def mixed_wav(ep,spec):
    total=sum(c['dur'] for c in spec['clips']); n=int(round(total*SR)); mix=np.zeros((n,2),np.float32)
    for c in spec['clips']:
        a=decode_audio(c['path'],c['ss'],c['dur'])
        need=int(round(c['dur']*SR)); a=a[:need]
        if len(a)<need: a=np.pad(a,((0,need-len(a)),(0,0)))
        i=int(round(c['timeline_start']*SR)); mix[i:i+need]+=a*0.84
    music=read_wav(BGM)[:n]
    if len(music)<n: music=np.pad(music,((0,n-len(music)),(0,0)))
    music=music*0.17
    fade=min(int(0.35*SR),n)
    if fade: music[-fade:]*=np.linspace(1.0,0.0,fade,endpoint=True,dtype=np.float32)[:,None]
    mix += music
    for c in spec['clips']:
        sfx=decode_audio(os.path.join(SFXDIR,c['sfx']+'.mp3'))
        i=int(round((c['timeline_start']+c['sfx_at'])*SR))
        if i>=n: continue
        avail=min(len(sfx),n-i)
        if avail<=0: continue
        sfx=sfx[:avail]
        peak=float(np.max(np.abs(sfx))) if sfx.size else 0.0
        if peak>1e-8: sfx*= (10**(-8.0/20))/peak
        fade_n=min(int(.08*SR),len(sfx))
        if fade_n: sfx[-fade_n:]*=np.linspace(1.0,0.0,fade_n,endpoint=True,dtype=np.float32)[:,None]
        mix[i:i+len(sfx)] += sfx
    # Smooth saturation followed by hard peak safety cap.
    mix=np.tanh(mix*0.95)/0.95
    peak=float(np.max(np.abs(mix)))
    cap=10**(-1.5/20)
    if peak>cap: mix*=cap/peak
    path=os.path.join(OUTDIR,f'EP{ep}_audio_mix_48k.wav')
    with wave.open(path,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(mix,-1,1).__mul__(32767).astype(np.int16).tobytes())
    return path,total


def finalize(ep,spec,video_only,out,audio,total):
    run([FF,'-hide_banner','-v','error','-y','-i',video_only,'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',out],f'EP{ep} final mux')
    # Full decode sanity check.
    run([FF,'-hide_banner','-v','error','-i',out,'-f','null','-'],f'EP{ep} full decode QA')
    info=probe(out)
    if info['width']!=1080 or info['height']!=1920 or not info['has_audio'] or abs(info['duration']-total)>0.12:
        raise RuntimeError(f'EP{ep} output check failed: {info}, expected ~{total:.3f}s')
    return info


def manifest(ep,spec,info,out,ass):
    # Audit source IDs against all pre-existing EP15–EP32 source manifests.
    old=[]
    import glob
    for f in glob.glob(os.path.join(ROOT,'*manifest*.json')):
        bn=os.path.basename(f)
        if not (bn.startswith(tuple(f'EP{i}' for i in list(range(15,27))+[28,29,30,31,32]))): continue
        try: d=json.load(open(f))
        except: continue
        old += [str(x.get('id')) for x in d.get('clips',[]) if x.get('id')]
    oldset=set(old)
    current_ids=[c['id'] for c in spec['clips']]
    repeated=[i for i in current_ids if i in oldset]
    if repeated: raise RuntimeError(f'EP{ep} source IDs conflict with EP15–EP32: {repeated}')
    clips=[]
    for c in spec['clips']:
        cc={k:c[k] for k in ['id','platform','url','ss','end','dur','crop','label','rank','impact','sfx','sfx_at','timeline_start','timeline_end','note']}
        cc['type2_label']=c['label']
        cc['source_audio_subjectively_auditioned']=False
        clips.append(cc)
    data={
      'episode':ep,'final':out,'duration_seconds':round(info['duration'],3),
      'format':'1080x1920, 30 fps, H.264 + AAC stereo',
      'visual_edit':'4 fresh fail/splash moments; EP29/EP30 locked Type-2 reference-A frame, 360px black title band, 1080x1428 central video frame, 132px black footer, 116 title, 101/70 ladder, @studio watermark; no added pills, zooms, or speed-ups.',
      'audio_mix':{'source_audio_retained':True,'source_gain':0.84,'bgm_file':BGM,'bgm_gain':0.17,'sfx_peak_dbfs':-8.0,'subjectively_auditioned':False,'song_free_claimed':False,'rights_clearance_checked':False},
      'source_id_history_check':{'manifests_checked':'EP15–EP26, EP28–EP32 existing manifests; EP27 manifest unavailable.','prior_source_id_count':len(oldset),'reused_prior_ids':[],'within_episode_repeat_note':'EP31 uses three distinct moments from the same new Dailymotion compilation x9vknx8; moments do not overlap.' if ep==31 else 'No source moment overlaps another clip; all IDs are new relative to EP15–EP32.'},
      'source_id_history_check_ep27_note':'EP27 final exists in Drive, but its source manifest was not found in the workspace or Drive search, so EP27 source IDs could not be verified.',
      'clips':clips,
      'measured_output':{'duration_seconds':round(info['duration'],3),'width':info['width'],'height':info['height'],'fps':info['fps'],'video_codec':info['vcodec'],'audio_codec':info['acodec'],'has_audio':info['has_audio'],'bytes':os.path.getsize(out),'full_decode_passed':True},
      'type2_text_overlay':{'enabled':True,'workflow':'templates.build_ranking / EP28-EP30 reference-A layout','ass_file':ass,'title':spec['title_text'],'title_size':116,'layout':{'top_band_px':360,'video_window_px':[0,360,1080,1428],'bottom_band_px':132,'ladder_x':86,'ladder_y0':528,'ladder_gap':232,'rank_number_size':101,'rank_label_size':70,'watermark':'@studio'},'countdown_display_order':[4,3,2,1],'clip_labels':[c['label'] for c in spec['clips']],'extra_caption_pills':False},
      'reuse_rights_checked':False,'source_audio_subjectively_auditioned':False
    }
    path=os.path.join(ROOT,f'EP{ep}_source_manifest.json')
    with open(path,'w') as f: json.dump(data,f,indent=2,ensure_ascii=False)
    return path


def main():
    results=[]
    for ep,spec in EPISODES.items():
        base=base_render(ep,spec)
        video_only,out,ass=make_video(ep,spec,base)
        audio,total=mixed_wav(ep,spec)
        info=finalize(ep,spec,video_only,out,audio,total)
        mf=manifest(ep,spec,info,out,ass)
        results.append({'episode':ep,'output':out,'manifest':mf,'duration':info['duration'],'size':os.path.getsize(out),'clips':[{'id':c['id'],'ss':c['ss'],'end':c['end'],'dur':c['dur'],'timeline_start':c['timeline_start'],'timeline_end':c['timeline_end']} for c in spec['clips']]})
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
