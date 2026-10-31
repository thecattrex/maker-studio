"""
musicgen7.py — "PE-PE-PEP" motif, brass/wind palette, NO DRUMS.
Instruments: mouth organ (harmonica), french horn, saxophone, trumpet.
"""
import numpy as np, os, importlib.util
from scipy.signal import butter, sosfilt

spec=importlib.util.spec_from_file_location("m2","/home/user/studio/musicgen2.py")
m2=importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
SR=m2.SR; Song=m2.Song; hz=m2.hz; ns=m2.ns; _mp=m2._mp; rng=m2.rng

def _horn(f, dur, vel=1.0, harm=(1.0,0.55,0.34,0.20,0.12), form=(280,2600), decay=0.30, breath=0.04, vib=4.6, scoop=0.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k,a in enumerate(harm, start=1):
        if f*k>8000: break
        y+=a*np.sin(2*np.pi*f*k*t + rng.uniform(0,6.28))
    if scoop:  # pitch scoop into the note (brass/reed attack)
        dp=np.exp(-t/0.05)*scoop
        y2=np.zeros(n)
        for k,a in enumerate(harm, start=1):
            if f*k>8000: break
            ph=2*np.pi*np.cumsum(f*(1-dp)*k)/SR
            y2+=a*np.sin(ph)
        y=0.4*y+0.6*y2
    v=1+0.0045*np.minimum(1,t/0.30)*np.sin(2*np.pi*vib*t)
    y*=v
    y=sosfilt(butter(2,form,'band',fs=SR,output='sos'),y)*1.15+y*0.30
    y+=breath*sosfilt(butter(2,[900,5000],'band',fs=SR,output='sos'),rng.normal(0,1,n))
    e=np.minimum(1,t/0.018)*np.exp(-t/max(decay,dur*1.2))
    r=min(ns(0.05),n); e[-r:]*=np.linspace(1,0,r)
    return _mp(y*e,vel)

def trumpet(f,dur,vel=1.0):   return _horn(f,dur,vel,(1.0,0.62,0.40,0.26,0.16,0.10),(400,3400),0.34,0.03,5.2,0.020)
def french_horn(f,dur,vel=1.0): return _horn(f,dur,vel,(1.0,0.30,0.14,0.06,0.03),(180,1400),0.55,0.03,4.0,0.012)
def sax(f,dur,vel=1.0):      return _horn(f,dur,vel,(1.0,0.75,0.62,0.46,0.33,0.24,0.16,0.11),(350,2400),0.32,0.075,5.6,0.018)
def mouthorgan(f,dur,vel=1.0):
    """harmonica — double-detuned reed + tremolo, nasal"""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for det in (0.996,1.004):
        for k in range(1,15):
            if f*det*k>8000: break
            y+=(1.0/(k**0.9))*np.sin(2*np.pi*f*det*k*t+rng.uniform(0,6.28))
    y=sosfilt(butter(2,[420,3000],'band',fs=SR,output='sos'),y)
    y*=(1+0.16*np.sin(2*np.pi*6.2*t))
    y+=0.05*sosfilt(butter(2,[800,4500],'band',fs=SR,output='sos'),rng.normal(0,1,n))
    e=np.minimum(1,t/0.015)*np.exp(-t/max(0.16,dur*1.1))
    r=min(ns(0.04),n); e[-r:]*=np.linspace(1,0,r)
    return _mp(y*e,vel)

# "pe pe pep pep | pepe pepe peeee"
# 16-step bar
PEP=[(0,0.85),(2,0.75),(4,0.90),(5,0.80),(6,0.95),
     (8,0.85),(9,0.75),(10,0.88),(12,1.00)]   # 12 = held 'peeee'

ROOTS=['D3','Bb2','F2','C3']
MEL  =['D4','Bb3','F3','C4']
HIGH =['D5','Bb4','F4','C5']
LOW  =['D3','Bb2','F2','C3']

def P1_pep_brass():
    s=Song(126,8,"P1_PepBrass",swing=0.08)
    for b in range(8):
        r=ROOTS[b%4]; m=MEL[b%4]; h=HIGH[b%4]; lo=LOW[b%4]
        # mouth organ = rhythmic bed (short puffs), no drums
        for step,v in PEP:
            s.add('harm', mouthorgan(hz(m), 0.075, vel=0.30*v), s.T(b,step),1.0, human=0.003)
        # trumpet = the main "PE" line
        for step,v in PEP:
            dur = 0.60 if step==12 else 0.09
            s.add('lead', trumpet(hz(h), dur, vel=0.55*v), s.T(b,step),1.0, human=0.002)
        # sax = answer phrase on the off half (call & response)
        if b>=1:
            for step in (3,7,11,14,15):
                s.add('harm', sax(hz(m), 0.09, vel=0.22), s.T(b,step),1.0, human=0.003)
        # french horn = sustained pad root (soft, warm)
        s.add('bass', french_horn(hz(lo)/2, s.bar*0.95, vel=0.30), s.T(b,0),1.0, human=0.003)
        # mouth organ bass pump on the long note
        s.add('bass', mouthorgan(hz(lo)/2, 0.34, vel=0.34), s.T(b,12),1.0, human=0.003)
    # horn swell as fill (no drums)
    s.add('bass', french_horn(hz('D2'), s.bar*1.8, vel=0.34), s.T(6,8),1.0, human=0.002)
    s.add('harm', sax(hz('A4'), 0.55, vel=0.20), s.T(7,14),1.0, human=0.003)
    return s

def P2_pep_harmonica():
    """mouth organ leads the PE line, brass answers"""
    s=Song(132,8,"P2_PepHarmonica",swing=0.08)
    for b in range(8):
        r=ROOTS[b%4]; m=MEL[b%4]; h=HIGH[b%4]; lo=LOW[b%4]
        # mouth organ LEAD
        for step,v in PEP:
            dur = 0.55 if step==12 else 0.085
            s.add('lead', mouthorgan(hz(h), dur, vel=0.52*v), s.T(b,step),1.0, human=0.002)
        # trumpet/sax stabs answer in the gaps
        for step in (1,3,5,7,13,15):
            inst = trumpet if step%4==1 else sax
            s.add('harm', inst(hz(m), 0.07, vel=0.20), s.T(b,step),1.0, human=0.003)
        # french horn + trumpet section chord on 0 (brass pad)
        if b%2==0:
            for nt in (lo, m):
                s.add('bass', french_horn(hz(nt)/2, s.bar*0.9, vel=0.22), s.T(b,0),1.0, human=0.003)
        else:
            s.add('bass', french_horn(hz(lo)/2, s.bar*0.9, vel=0.28), s.T(b,0),1.0, human=0.003)
    s.add('harm', trumpet(hz('D5'), 0.8, vel=0.26), s.T(6,8),1.0, human=0.002)
    return s

if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/pep",exist_ok=True)
    G={'lead':1.15,'harm':0.62,'bass':0.82,'drums':0.0,'fx':0.2}
    for fn in (P1_pep_brass,P2_pep_harmonica):
        s=fn(); p=f"/home/user/audio_preview/pep/{s.name}.wav"
        m2.master(s,p,gains=G); print("OK",p,round(s.dur,1),"s")
