#!/usr/bin/env python3
"""Prepare the approved EP6 Type-2 clips without changing speed.
Video cuts are source-time trims, source text/logo cleanup (where needed), then
source-aspect crop and 1080x1428 conform. Audio is Demucs vocal stem to retain
speech/laughter while discarding source backing tracks; the identified song in
clip 1 is muted during its lyric interval. All source files remain untouched.
"""
import os, subprocess
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(ROOT, "assets", "ep6")
FF = "/tmp/vidtools/ffmpeg"
# Play order 3 -> 5 -> 2 -> 4 -> 1. Clip durations are exact 30-fps frame counts.
ITEMS = [
    dict(n=3, name="clip3", source="/home/user/dl/src/tiktok/tt_6863209571322744070.mp4", ss=0.00, dur=110/30, crop=(576,762,0,260), delogo=None),
    dict(n=5, name="clip5", source="/home/user/dl/src/tiktok/tt_7418606752553356587.mp4", ss=2.00, dur=110/30, crop=(435,576,94,0), delogo=None),
    dict(n=2, name="clip2", source="/home/user/dl/src/imgur/b0wKmlw.mp4", ss=6.50, dur=108/30, crop=(646,854,0,0), delogo=(490,705,190,135)),
    dict(n=4, name="clip4", source="/home/user/dl/src/tiktok/tt_7464233129004502318.mp4", ss=0.00, dur=96/30, crop=(720,952,0,180), delogo=(210,900,315,120)),
    dict(n=1, name="clip1", source="/home/user/dl/src/tiktok/tt_6702952481954991366.mp4", ss=0.40, dur=108/30, crop=(576,762,0,130), delogo=None),
]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or "")[-3000:])

def main():
    os.makedirs(ASSET, exist_ok=True)
    video_parts=[]
    vocals_parts=[]
    offset=0.0
    for it in ITEMS:
        if not os.path.exists(it["source"]):
            raise FileNotFoundError(it["source"])
        ow=os.path.join(ASSET, f"ep6_{it['n']}_clean.mp4")
        cw,ch,cx,cy=it["crop"]
        filters=[]
        if it["delogo"]:
            x,y,w,h=it["delogo"]
            filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}:show=0")
        filters += [f"crop={cw}:{ch}:{cx}:{cy}", "scale=1080:1428:flags=lanczos", "fps=30", "setsar=1", "format=yuv420p"]
        run([FF,"-hide_banner","-v","error","-y","-ss",f"{it['ss']:.6f}","-i",it["source"],"-t",f"{it['dur']:.6f}","-vf",",".join(filters),"-an","-c:v","libx264","-preset","medium","-crf","17","-r","30","-movflags","+faststart",ow])
        video_parts.append(ow)
        it["timeline_ss"]=round(offset,6)
        offset += it["dur"]

        stem=os.path.join(ASSET,"stems",it["name"],"vocals.wav")
        audio,sr=sf.read(stem,dtype="float32",always_2d=True)
        i0=round(it["ss"]*sr); n=round(it["dur"]*sr)
        seg=audio[i0:i0+n].copy()
        if len(seg)<n:
            seg=np.pad(seg,((0,n-len(seg)),(0,0)))
        if it["n"]==1:
            # Full-source ASR confirmed a sung track in this pool clip at ~2.18s.
            # Mask that song-vocal span within the selected 0.40–4.00s window.
            local0=max(0.0,2.05-it["ss"])
            local1=min(it["dur"],4.00-it["ss"])
            a=round(local0*sr); b=round(local1*sr)
            fade=round(0.025*sr)
            seg[a:b]=0
            if a>=fade and fade:
                seg[a-fade:a] *= np.linspace(1,0,fade,endpoint=False,dtype=np.float32)[:,None]
            if b+fade<=len(seg) and fade:
                seg[b:b+fade] *= np.linspace(0,1,fade,endpoint=False,dtype=np.float32)[:,None]
        vocals_parts.append(seg)
        print(f"prepared #{it['n']}: {it['ss']:.2f}+{it['dur']:.3f}s; concat ss={it['timeline_ss']:.3f}")

    listing=os.path.join(ASSET,"video_concat.txt")
    with open(listing,"w") as f:
        for p in video_parts:
            f.write("file '"+p.replace("'","'\\''")+"'\n")
    src=os.path.join(ASSET,"rc5_src.mp4")
    run([FF,"-hide_banner","-v","error","-y","-f","concat","-safe","0","-i",listing,"-c:v","copy","-an","-movflags","+faststart",src])
    aud=np.concatenate(vocals_parts,axis=0)
    audio44=os.path.join(ASSET,"rc5_clean_audio_44100.wav")
    sf.write(audio44,aud,44100,subtype="PCM_16")
    audio48=os.path.join(ASSET,"rc5_clean_audio.wav")
    run([FF,"-hide_banner","-v","error","-y","-i",audio44,"-ar","48000","-ac","2","-c:a","pcm_s16le",audio48])
    print("VIDEO",src)
    print("AUDIO",audio48)

if __name__=="__main__": main()
