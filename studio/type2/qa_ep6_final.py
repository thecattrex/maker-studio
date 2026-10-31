#!/usr/bin/env python3
"""Measured audio QA for the rendered EP6 Type-2 file."""
import json, os, subprocess, sys, wave
import numpy as np
from scipy.signal import correlate, correlation_lags

ROOT=os.path.dirname(os.path.abspath(__file__))
FF='/tmp/vidtools/ffmpeg'
VIDEO='/home/user/dl/type2_ep6_v2.mp4'
CFG=json.load(open(os.path.join(ROOT,'config_ep6.json')))

def decode(path):
    p=subprocess.run([FF,'-v','error','-i',path,'-vn','-ac','2','-ar','48000','-f','f32le','-'],capture_output=True,check=True)
    return np.frombuffer(p.stdout,dtype=np.float32).reshape(-1,2).mean(axis=1)

def wav48(path):
    with wave.open(path,'rb') as w:
        assert w.getframerate()==48000
        a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
        return a.reshape(-1,w.getnchannels()).mean(axis=1)

def peak_corr(x, ref, center_s, search_s=0.06):
    active=np.where(np.abs(ref)>0.005)[0]
    if not len(active): return (float('nan'),None)
    a,b=active[0],active[-1]+1
    ref=ref[a:b]
    expected=int(round(center_s*48000))+a
    rad=int(search_s*48000)
    lo=max(0,expected-rad); hi=min(len(x)-len(ref),expected+rad)
    best=(-2,None)
    rnorm=np.linalg.norm(ref)+1e-12
    for shift in range(-rad,rad+1,48):  # 1 ms; anchored at the exact expected onset
        k=expected+shift
        if k<0 or k+len(ref)>len(x): continue
        v=x[k:k+len(ref)]
        corr=float(np.dot(v,ref)/(np.linalg.norm(v)*rnorm+1e-12))
        if corr>best[0]: best=(corr,k-a)
    return best[0],best[1]/48000 if best[1] is not None else None

x=decode(VIDEO)
voice=wav48(CFG['voice']['file'])
# rendered timeline timing is read from build's measured black-gap output.
voice_ts=[0.0,3.3833,7.3500,11.2167]
print('duration',len(x)/48000,'s')
print('voice NCC / observed insert start:')
for t in voice_ts:
    c,obs=peak_corr(x,voice,t,0.05)
    print(f'  expected {t:.4f}s  corr={c:.4f}  insert={obs:.4f}s  error={obs-t:+.4f}s')
# Chicken scream sample alignment.
scream=wav48(os.path.join(ROOT,'assets','scream48.wav'))
c,obs=peak_corr(x,scream,15.300,0.06)
print(f'chicken scream expected 15.3000s corr={c:.4f} insert={obs:.4f}s error={obs-15.3:+.4f}s')
# Signal peaks/loudness (sample peak; EBU integrated loudness parsed from ffmpeg).
print('sample_peak_dBFS',20*np.log10(np.max(np.abs(x))+1e-12))
r=subprocess.run([FF,'-hide_banner','-nostats','-i',VIDEO,'-filter_complex','ebur128=peak=true','-f','null','-'],capture_output=True,text=True)
print('ebur128_tail')
print('\n'.join((r.stderr or '').splitlines()[-13:]))
# Verify the required impact SFX correlations near their configured event times.
clip_starts=[0.0,4.0,7.9667,11.8333,16.2]
for i,cfgc in enumerate(CFG['clips']):
    s=cfgc['sfx']; path=os.path.join(CFG['sfx_dir'],s['key']+'.mp3')
    ref=decode(path)
    t=clip_starts[i]+float(s['at'])
    remaining=max(1,len(x)-int(round(t*48000)))
    ref=ref[:remaining]  # last impact's tail is intentionally faded at video end
    corr,obs=peak_corr(x,ref,t,0.09)
    print(f"sfx #{cfgc['n']} {s['key']} expected {t:.4f}s corr={corr:.4f} insert={obs:.4f}s delta={obs-t:+.4f}s")
# Search for unintended I-got-this voice-like match after the chicken insert.
# For this locked recipe, no voice is permitted at/after the chicken cue.
active=np.where(np.abs(voice)>0.005)[0]; a,b=active[0],active[-1]+1; vref=voice[a:b]
mx=0.0; mt=None
for k in range(int(15.0*48000),len(x)-len(vref),1200):
    seg=x[k:k+len(vref)]
    c=float(np.dot(seg,vref)/(np.linalg.norm(seg)*np.linalg.norm(vref)+1e-12))
    if c>mx: mx,mt=c,k/48000
print(f'voice-match max after 15.0s (no voice expected): corr={mx:.4f} at {mt:.3f}s')
