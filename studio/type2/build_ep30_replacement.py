#!/usr/bin/env python3
"""Render replacement EP30 with 4 safe fall clips, source audio retained."""
import json, os, subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = '/home/user/studio/type2'
OUT = '/home/user/studio/out/EP30_Type2_Final_2026-10-29.mp4'
PRE = '/home/user/studio/out/EP30_Type2_Final_2026-10-29_premix.mp4'
MUSIC = '/home/user/studio/type2/assets/c2_48.wav'
SFX_DIR = '/home/user/studio/trial/sfx'

# ss is relative to each clip's first decoded frame (timestamps are reset before trimming).
# End points are set to approximately 0.1 s after the visible landing/impact.
CLIPS = [
    {
        'id':'xWiSiOthUUY','platform':'YouTube Shorts',
        'url':'https://www.youtube.com/shorts/xWiSiOthUUY',
        'path':'/home/user/dl/src/ep30_remake_youtube/xWiSiOthUUY.mp4',
        'ss':0.00,'end':2.15,'label':'Exercise-ball tumble',
        'sfx':'yeet','impact_in_source':2.05,
        'crop':None,
        'note':'Adult loses balance on an exercise ball and tumbles onto a padded gym mat; full setup and landing are visible.'
    },
    {
        'id':'x7mzfun','platform':'Dailymotion',
        'url':'https://www.dailymotion.com/video/x7mzfun',
        'path':'/home/user/dl/src/ep28_29_candidates/x7mzfun/x7mzfun.mp4',
        'ss':1.50,'end':5.90,'label':'Snowy bar slip',
        'sfx':'ba_drum_tss','impact_in_source':5.75,
        'crop':None,
        'note':'A person hangs from a bar, slips and lands in snow; ends immediately after contact.'
    },
    {
        'id':'msrOHSgBZbo','platform':'YouTube Shorts',
        'url':'https://www.youtube.com/shorts/msrOHSgBZbo',
        'path':'/home/user/dl/src/ep30_remake_youtube/msrOHSgBZbo.mp4',
        'ss':7.40,'end':9.55,'label':'Trampoline mat tumble',
        'sfx':'quack','impact_in_source':9.43,
        'crop':[360,280,720,1280],
        'note':'A trampoline-park jump ends on the padded mat; crop removes the ranking title and most of the sidebar.'
    },
    {
        'id':'x7ubaq2','platform':'Dailymotion',
        'url':'https://www.dailymotion.com/video/x7ubaq2',
        'path':'/home/user/dl/src/ep28_29_candidates/x7ubaq2/x7ubaq2.mp4',
        'ss':3.25,'end':12.50,'label':'Gymnastics partner tumble',
        'sfx':'oof','impact_in_source':12.38,
        'crop':None,
        'note':'A partner balance attempt on a gymnastics mat ends with a tumble onto the padded floor; includes the setup and ends just after the landing.'
    },
]

W,H,FPS = 1080,1920,30

def run():
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    inputs=[]
    for c in CLIPS:
        if not os.path.exists(c['path']): raise FileNotFoundError(c['path'])
        c['dur']=round(c['end']-c['ss'],3)
        if c['dur'] <= 0: raise ValueError(c)
        inputs += ['-i',c['path']]
    # Loop music for the whole cut; then add four impact cues.
    inputs += ['-stream_loop','-1','-i',MUSIC]
    sfx_names=['yeet','ba_drum_tss','quack','oof']
    for key in sfx_names: inputs += ['-i',os.path.join(SFX_DIR,key+'.mp3')]
    total=round(sum(c['dur'] for c in CLIPS),3)
    fc=[]
    elapsed=0.0
    for i,c in enumerate(CLIPS):
        d=c['dur']; ss=c['ss']
        if c['crop']:
            x,y,w,h=c['crop']
            fc.append(f'[{i}:v]setpts=PTS-STARTPTS,trim=start={ss}:duration={d},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p[v{i}]')
            # The cropped portrait fills the frame; no extra blur/letterboxing needed.
        else:
            fc.append(f'[{i}:v]setpts=PTS-STARTPTS,trim=start={ss}:duration={d},setpts=PTS-STARTPTS,split=2[bgsrc{i}][fgsrc{i}]')
            fc.append(f'[bgsrc{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=24,eq=brightness=-0.23:saturation=1.10[bg{i}]')
            fc.append(f'[fgsrc{i}]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[fg{i}]')
            fc.append(f'[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2:shortest=1,fps={FPS},setsar=1,format=yuv420p[v{i}]')
        fc.append(f'[{i}:a]asetpts=PTS-STARTPTS,atrim=start={ss}:duration={d},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume=0.84,apad,atrim=duration={d}[a{i}]')
        c['timeline_start']=round(elapsed,3)
        c['timeline_end']=round(elapsed+d,3)
        c['sfx_at']=round(elapsed + c['impact_in_source'] - ss,3)
        elapsed += d
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(CLIPS))) + f'concat=n={len(CLIPS)}:v=1:a=1[basev][basea]')
    music_i=len(CLIPS)
    fc.append(f'[{music_i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total},asetpts=PTS-STARTPTS,volume=0.17[bgm]')
    for j,key in enumerate(sfx_names):
        delay=int(round(CLIPS[j]['sfx_at']*1000))
        input_i=music_i+1+j
        fc.append(f'[{input_i}:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.65,adelay={delay}|{delay},atrim=duration={total}[sfx{j}]')
    fc.append('[basea][bgm][sfx0][sfx1][sfx2][sfx3]amix=inputs=6:duration=first:normalize=0,alimiter=limit=0.88:attack=5:release=60,aresample=48000[amixout]')
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,
         '-filter_complex_threads','2','-filter_complex',';'.join(fc),
         '-map','[basev]','-map','[amixout]','-t',str(total),
         '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),
         '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',PRE]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(f'ffmpeg premix failed ({p.returncode})\nSTDERR={p.stderr[-6000:]}\nSTDOUT={p.stdout[-2000:]}')
    # Normalize the mix in a separate audio-only pass to keep peak control robust without adding renderer load.
    cmd2=[FF,'-hide_banner','-v','error','-y','-i',PRE,'-map','0:v:0','-map','0:a:0','-c:v','copy',
          '-af','loudnorm=I=-14:LRA=11:TP=-1.5','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
          '-movflags','+faststart',OUT]
    p2=subprocess.run(cmd2,capture_output=True,text=True)
    if p2.returncode: raise RuntimeError(f'ffmpeg loudness pass failed ({p2.returncode})\nSTDERR={p2.stderr[-6000:]}\nSTDOUT={p2.stdout[-2000:]}')
    os.remove(PRE)
    manifest={
        'episode':30,'remake':True,'final':OUT,'duration_seconds':total,
        'format':'1080x1920, 30 fps, H.264 + AAC stereo',
        'visual_edit':'4 replacement clips, setup through fall/impact; no added titles, speed changes, or punch-in zooms; YouTube source title/sidebar trimmed where present.',
        'audio_mix':{'source_audio_retained':True,'source_gain':0.84,'bgm_file':MUSIC,'bgm_gain':0.17,'sfx_gain':1.65,'loudnorm_target_lufs':-14,'true_peak_limit_db':-1.5,'subjectively_auditioned':False,'song_free_claimed':False},
        'rights_clearance_checked':False,
        'clips':[]
    }
    for c in CLIPS:
        manifest['clips'].append({k:c[k] for k in ['id','platform','url','ss','end','dur','label','crop','timeline_start','timeline_end','impact_in_source','sfx','sfx_at','note','path']})
    mpath=os.path.join(ROOT,'EP30_remake_source_manifest.json')
    with open(mpath,'w') as f: json.dump(manifest,f,indent=2)
    print(json.dumps({'output':OUT,'duration':total,'manifest':mpath,'clips':manifest['clips']},indent=2))

if __name__=='__main__': run()
