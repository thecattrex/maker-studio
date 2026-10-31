#!/usr/bin/env python3
"""Rebuild EP30 with the locked EP28/29 Type-2 ranking frame and text workflow."""
import os, subprocess, sys
import imageio_ffmpeg
sys.path.insert(0, '/home/user/studio')
from util import probe
from templates import build_ranking, save_overlay

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = '/home/user/studio/type2'
OUTDIR = '/home/user/studio/out'
BASE = os.path.join(ROOT, 'assets', 'ep30_ep29style_base.mp4')
VIDEO_ONLY = os.path.join(OUTDIR, 'EP30_Type2_EP29Style_video_only.mp4')
OUT = os.path.join(OUTDIR, 'EP30_Type2_Final_EP29Style_2026-10-29.mp4')
MIXED_AUDIO = os.path.join(OUTDIR, 'EP30_Type2_Final_NoText_2026-10-29.mp4')

# Keep the approved clip windows and order. Each crop is converted to the same
# 480x636 source frame used by the established EP28/29 Type-2 build method.
CLIPS = [
    {'id':'exercise_ball', 'path':'/home/user/dl/src/ep30_remake_youtube/xWiSiOthUUY.mp4',
     'ss':0.00, 'dur':2.15, 'crop':(60,0,360,480), 'label':'BALL TUMBLE', 'rank':4,
     'note':'Square-source crop keeps the person and ball centered.'},
    {'id':'snowy_bar', 'path':'/home/user/dl/src/ep28_29_candidates/x7mzfun/x7mzfun.mp4',
     'ss':1.50, 'dur':4.40, 'crop':(100,0,360,480), 'label':'SNOW BAR SLIP', 'rank':3,
     'note':'Crop favors the person hanging from the bar and preserves the landing.'},
    {'id':'trampoline', 'path':'/home/user/dl/src/ep30_remake_youtube/msrOHSgBZbo.mp4',
     'ss':7.40, 'dur':2.15, 'crop':(420,720,660,880), 'label':'TRAMPOLINE FALL', 'rank':2,
     'note':'4:5 crop removes the source title/sidebar and most baked-in graphic clutter while retaining setup and fall.'},
    {'id':'partner_gym', 'path':'/home/user/dl/src/ep28_29_candidates/x7ubaq2/x7ubaq2.mp4',
     'ss':3.25, 'dur':9.25, 'crop':(8,0,360,480), 'label':'PARTNER TUMBLE', 'rank':1,
     'note':'Near-full portrait crop keeps both partners and the tumble.'},
]
W,H,FPS = 480,636,30


def make_base():
    inputs=[]; fc=[]
    for i,c in enumerate(CLIPS):
        if not os.path.isfile(c['path']):
            raise FileNotFoundError(c['path'])
        x,y,w,h=c['crop']
        info=probe(c['path'])
        if x+w>info['width'] or y+h>info['height']:
            raise ValueError(f"crop out of bounds for {c['id']}: {c['crop']} / {info['width']}x{info['height']}")
        inputs += ['-i',c['path']]
        fc.append(f'[{i}:v]trim=start={c["ss"]}:duration={c["dur"]},setpts=PTS-STARTPTS,'
                  f'crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p[v{i}]')
        c['timeline_start']=round(sum(x['dur'] for x in CLIPS[:i]),3)
        c['timeline_end']=round(c['timeline_start']+c['dur'],3)
    fc.append(''.join(f'[v{i}]' for i in range(len(CLIPS))) + f'concat=n={len(CLIPS)}:v=1:a=0[outv]')
    os.makedirs(os.path.dirname(BASE),exist_ok=True)
    cmd=[FF,'-hide_banner','-v','error','-y',*inputs,'-filter_complex_threads','2',
         '-filter_complex',';'.join(fc),'-map','[outv]','-an','-c:v','libx264',
         '-preset','medium','-crf','17','-pix_fmt','yuv420p','-r',str(FPS),
         '-movflags','+faststart',BASE]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode:
        raise RuntimeError('base render failed:\n'+r.stderr[-6000:])
    return BASE


def render_ep29_layout(base):
    # Title string and all positional/font sizes are copied from the locked EP28/29
    # reference-A recipe: band=360, bottom=132, title=116, ladder 101/70.
    title = (
        [[('Ranking ', '&H00FFFFFF&'), ('Funniest', '&H002828F0&')],
         [('Falls', '&H0000D7FF&')]]
    )
    items=[]
    for c in CLIPS:
        items.append({'ss':c['timeline_start'], 'dur':c['dur'], 'n':c['rank'],
                      'label':c['label'], 'color':{
                          1:'&H000000FF&',2:'&H000011FF&',3:'&H0000A5FF&',4:'&H00FFFFFF&'
                      }[c['rank']], 'focus':(0.5,0.5), 'zoom_to':1.0,
                      'crop_top':0.0, 'crop_bottom':0.0, 'sfx':[]})
    tl=build_ranking(base, items, title=title, band=360, bottom=132, gap=0.0,
                     size=(1080,1920), watermark='@studio', order=[0,1,2,3],
                     title_size=116, ladder='asc', music=None, music_vol=0.0,
                     clip_vol=0.0, sfx_dir=None)
    ass_path = '/home/user/studio/work/ep30-ep29style-restored-2026-10-29.ass'
    save_overlay(tl, ass_path)
    # build_ranking adds zero-length black-gap segments when gap=0. Drop those
    # exact zero-duration entries so the clip cuts stay direct and total length
    # remains 17.95 seconds; no extra black beat is inserted.
    tl.segments = [seg for seg in tl.segments if seg.out_dur() > 0.01]
    # Video-only layout render. The locked mixed audio from the approved cut is
    # remuxed without reprocessing below, preserving BGM/SFX/source mix exactly.
    for seg in tl.segments:
        seg.mute=True
    tl.music=None
    tl.sfx=[]
    tl.original_vol=0.0
    tl.master_gain_db=0.0
    tl.build(VIDEO_ONLY, crf=18, preset='medium', loudnorm=False)


def remux_audio():
    if not os.path.isfile(MIXED_AUDIO):
        raise FileNotFoundError(MIXED_AUDIO)
    cmd=[FF,'-hide_banner','-v','error','-y','-i',VIDEO_ONLY,'-i',MIXED_AUDIO,
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy',
         '-movflags','+faststart',OUT]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode:
        raise RuntimeError('audio remux failed:\n'+r.stderr[-6000:])
    return probe(OUT)

if __name__=='__main__':
    base=make_base()
    render_ep29_layout(base)
    info=remux_audio()
    print({'output':OUT,'base':base,'duration':info.get('duration'),
           'width':info.get('width'),'height':info.get('height'),
           'has_audio':info.get('has_audio'),'bytes':os.path.getsize(OUT),
           'clips':CLIPS})
