"""
musicgen.py — 100% original instrumental tracks, generated from scratch with numpy/scipy.
Koi sample, koi library, koi third-party audio nahi. Isliye:
  • copyright = mera/tumhara apna
  • Content ID / Meta match = impossible (kisi database me hai hi nahi)
  • credit / description = zero requirement
  • YouTube, Instagram, Facebook — sab allowed

Usage:  python3 musicgen.py
Output: out/orig_<name>.wav (44.1k 16-bit stereo) + .mp3
"""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- basics
NOTE_BASE = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,
             'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}

def hz(n):
    if isinstance(n,(int,float)): return float(n)
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2**((NOTE_BASE[name] + 12*(octv+1) - 69)/12)

def ns(dur): return int(round(dur*SR))

def env_ad(n, a=0.005, d=0.2, curve=4.0):
    a_n = max(1,int(a*SR)); e = np.zeros(n)
    a_n = min(a_n,n)
    e[:a_n] = np.linspace(0,1,a_n)
    rest = n-a_n
    if rest>0:
        e[a_n:] = np.exp(-curve*np.arange(rest)/max(1,int(d*SR)))
    return e

def soft_limit(x, drive=1.0):
    return np.tanh(x*drive)

# ---------------------------------------------------------------- instruments
def ks_pluck(f, dur, damp=0.995, bright=0.6, vel=1.0):
    """Karplus-Strong plucked string — pizzicato / harp / banjo feel."""
    n = ns(dur); D = max(2, int(SR/f))
    exc = rng.uniform(-1,1,D)
    lp = np.copy(exc)
    for _ in range(2): lp = np.convolve(lp,[bright,1-bright])[:D]
    x = np.zeros(n); x[:D] = lp
    b = np.zeros(D+1); b[0] = 1.0
    a = np.zeros(D+1); a[0] = 1.0; a[D] = -damp
    y = lfilter(b, a, x)
    y *= np.minimum(1.0, dur/ (dur+0.02))
    y[:200] *= np.linspace(0,1,200)
    m = np.max(np.abs(y))+1e-9
    return vel*y/m

def marimba(f, dur, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    e = np.exp(-5.0*t)
    y = (np.sin(2*np.pi*f*t) + 0.45*np.sin(2*np.pi*2*f*t)*np.exp(-8*t)
         + 0.22*np.sin(2*np.pi*4*f*t)*np.exp(-14*t))
    return vel*y*e

def bell(f, dur, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    mod = np.sin(2*np.pi*f*2.0*t)*2.0*np.exp(-3*t)
    y = np.sin(2*np.pi*f*t + mod)*np.exp(-3.2*t)
    return vel*y

def pianoish(f, dur, vel=1.0):
    """Soft detuned pluck with body — QKThr type mellow keys."""
    n = ns(dur); t = np.arange(n)/SR
    y = np.zeros(n)
    for det,g in [(1.0,1.0),(1.0015,0.6),(0.9985,0.5)]:
        y += g*np.sin(2*np.pi*f*det*t + 0.3*np.sin(2*np.pi*f*det*2*t)*np.exp(-2*t))
    y += 0.25*ks_pluck(f, dur, damp=0.997, bright=0.35, vel=1.0)
    y *= np.exp(-1.7*t)
    y[:int(0.004*SR)] *= np.linspace(0,1,int(0.004*SR))
    return vel*y/(np.max(np.abs(y))+1e-9)

def saw_bass(f, dur, vel=1.0, cut=380):
    n = ns(dur); t = np.arange(n)/SR
    y = np.zeros(n)
    for k in range(1,12):
        if f*k > 6000: break
        y += np.sin(2*np.pi*f*k*t)/k
    sos = butter(2, cut, 'low', fs=SR, output='sos')
    y = sosfilt(sos, y)
    y *= env_ad(n, a=0.006, d=0.16, curve=3.0)
    return vel*y/(np.max(np.abs(y))+1e-9)

def sub808(f, dur, vel=1.0, drop=0.0):
    n = ns(dur); t = np.arange(n)/SR
    f0 = f*(1+drop)
    fr = f0*np.exp(-3.5*t)+f*(1-np.exp(-3.5*t))
    ph = 2*np.pi*np.cumsum(fr)/SR
    y = np.sin(ph)*env_ad(n, a=0.004, d=0.55, curve=2.2)
    return vel*y

def pad_chord(freqs, dur, vel=1.0, cut=1600):
    n = ns(dur); t = np.arange(n)/SR
    y = np.zeros(n)
    for f in freqs:
        for det in (0.996,1.0,1.004):
            for k in range(1,7):
                y += (1.0/(k*k))*np.sin(2*np.pi*f*det*k*t + rng.uniform(0,6.28))
    sos = butter(2, cut, 'low', fs=SR, output='sos')
    y = sosfilt(sos, y)
    e = np.minimum(1, t/0.35)*np.minimum(1,(dur-t)/0.5)
    return vel*y*e/(np.max(np.abs(y))+1e-9)

def stab(freqs, dur, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    y = np.zeros(n)
    for f in freqs:
        for k in range(1,9):
            y += np.sin(2*np.pi*f*k*t)*np.exp(-k*0.25)/k
    y *= env_ad(n, a=0.003, d=0.12, curve=6.0)
    return vel*y/(np.max(np.abs(y))+1e-9)

# ---------------------------------------------------------------- drums
def kick(dur=0.30, vel=1.0, punch=1.0):
    n = ns(dur); t = np.arange(n)/SR
    fr = 48 + 90*np.exp(-26*t)
    ph = 2*np.pi*np.cumsum(fr)/SR
    body = np.sin(ph)*np.exp(-7.5*t)
    click = rng.normal(0,1,n)*np.exp(-160*t)*0.25*punch
    return vel*(body+click)

def snare(dur=0.22, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    noise = rng.normal(0,1,n)
    sos = butter(2,[1200,8000],'band',fs=SR,output='sos')
    noise = sosfilt(sos,noise)*np.exp(-18*t)
    tone = np.sin(2*np.pi*190*t)*np.exp(-26*t)*0.45
    return vel*(noise*0.8+tone)

def hat(dur=0.06, vel=1.0, open_=False):
    n = ns(dur if not open_ else max(dur,0.18)); t = np.arange(n)/SR
    noise = rng.normal(0,1,n)
    sos = butter(3, 7000, 'high', fs=SR, output='sos')
    y = sosfilt(sos, noise)
    y *= np.exp(-(28 if not open_ else 12)*t)
    return vel*y*0.55

def clap(dur=0.25, vel=1.0):
    n = ns(dur); y = np.zeros(n)
    for k,off in enumerate([0,0.012,0.024]):
        i = ns(off)
        m = min(n,i+ns(0.12))
        seg = rng.normal(0,1,m-i)
        sos = butter(2,[900,5000],'band',fs=SR,output='sos')
        seg = sosfilt(sos,seg)*np.exp(-30*np.arange(m-i)/SR)
        y[i:m] += seg*(1.0-0.2*k)
    return vel*y*0.6

def woodblock(f=880, dur=0.09, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    y = (np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*f*2.7*t))*np.exp(-40*t)
    return vel*y*0.5

def shaker(dur=0.07, vel=1.0):
    n = ns(dur); t = np.arange(n)/SR
    sos = butter(3, 5000, 'high', fs=SR, output='sos')
    y = sosfilt(sos, rng.normal(0,1,n))
    e = np.exp(-22*t)*(1-np.exp(-90*t))
    return vel*y*e*0.3

def vinyl(dur, vel=0.06):
    n = ns(dur)
    y = rng.normal(0,1,n)*0.35
    sos = butter(2,[1200,6000],'band',fs=SR,output='sos')
    y = sosfilt(sos,y)
    crackle = (rng.random(n) > 0.9994).astype(float)*rng.normal(0,1,n)*1.5
    return vel*(y*0.5+crackle)

# ---------------------------------------------------------------- bus / mix
class Song:
    def __init__(self, bpm, bars, name):
        self.bpm=bpm; self.spb=60.0/bpm
        self.dur=bars*4*self.spb + 2.0
        self.n=ns(self.dur)
        self.bus={'drums':np.zeros(self.n),'bass':np.zeros(self.n),
                  'music':np.zeros(self.n),'fx':np.zeros(self.n)}
        self.name=name
    def add(self, bus, sig, t, gain=1.0):
        i=ns(t); j=min(self.n,i+len(sig))
        if i>=self.n: return
        self.bus[bus][i:j]+=sig[:j-i]*gain
    def beat(self,b): return b*4*self.spb
    def s16(self,b,step): return self.beat(b)+step*self.spb/4

def reverb_ir(rt=0.9, pre=0.012, damp=0.55):
    n=ns(rt); t=np.arange(n)/SR
    ir=rng.normal(0,1,n)*np.exp(-6.9*t/rt)
    sos=butter(2, 5200,'low',fs=SR,output='sos')
    ir=sosfilt(sos,ir)
    ir=np.concatenate([np.zeros(ns(pre)),ir])
    return ir/np.max(np.abs(ir))

def delay(sig, ds, fb=0.28, mix=0.3):
    out=np.copy(sig); d=ns(ds)
    for k in range(1,4):
        sh=np.zeros_like(sig); 
        if d*k < len(sig): sh[d*k:]=sig[:len(sig)-d*k]*(fb**(k-1))
        out+=sh*mix
    return out

def master(song, out_path, loudnorm=True):
    ir=reverb_ir()
    L=np.zeros(song.n); R=np.zeros(song.n)
    gains={'drums':0.95,'bass':0.9,'music':0.8,'fx':0.7}
    pans={'drums':0.0,'bass':0.0,'music':0.05,'fx':-0.1}
    for k,v in song.bus.items():
        g=gains[k]
        wet=fftconvolve(v,ir)[:song.n]*0.35
        dry=v
        # haas-free widening: tiny delay on one side for music/fx
        sL=dry*(1-max(0,pans[k]))+np.concatenate([np.zeros(ns(0.008)),dry[:-ns(0.008)]])*max(0,pans[k])
        sR=dry*(1+min(0,pans[k]))+np.concatenate([np.zeros(ns(0.011)),dry[:-ns(0.011)]])*abs(min(0,pans[k]))
        L+= (sL+wet*0.9)*g; R+= (sR+wet)*g
    # gentle glue
    mx=max(np.max(np.abs(L)),np.max(np.abs(R)))+1e-9
    L/=mx; R/=mx
    L=soft_limit(L*1.15,1.0)*0.92
    R=soft_limit(R*1.15,1.0)*0.92
    st=np.stack([L,R],1)
    # fade in/out
    f=ns(0.02); st[:f]*=np.linspace(0,1,f)[:,None]
    f2=ns(0.6); st[-f2:]*=np.linspace(1,0,f2)[:,None]
    pcm=(np.clip(st,-1,1)*32767).astype('<i2')
    import wave
    with wave.open(out_path,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path

# ---------------------------------------------------------------- songs
def song_monkeyfunk():
    """Comedic staccato — Monkeys Spinning Monkeys jaisi feel, par 100% original."""
    s=Song(140,8,"Monkeyfunk")
    # A minor pentatonic comedic riff
    chords=[['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['A2','C3','E3'],
            ['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['E2','G2','B2']]
    mel=[[  'A4',None,'C5',None,'E5',None,'C5',None,'A4',None,'G4',None,'E4',None,'G4',None],
         [  'F4',None,'A4',None,'C5',None,'A4',None,'F4',None,'E4',None,'C4',None,'E4',None],
         [  'G4',None,'B4',None,'D5',None,'B4',None,'G4',None,'F4',None,'D4',None,'F4',None],
         [  'A4',None,'C5','E5','A5',None,'E5',None,'C5',None,'A4',None,'E4','G4','A4',None]]
    for b in range(8):
        c=chords[b]
        # pizz bass on 1 and 3 (+walking pickup)
        s.add('bass', ks_pluck(hz(c[0]),0.34,damp=0.985,bright=0.75,vel=0.95), s.beat(b), 1.0)
        s.add('bass', ks_pluck(hz(c[0]) ,0.30,damp=0.983,bright=0.7,vel=0.8), s.beat(b)+s.spb*2, 0.9)
        if b%2==1:
            s.add('bass', ks_pluck(hz(c[1]),0.22,damp=0.98,bright=0.7,vel=0.6), s.beat(b)+s.spb*3.5, 0.8)
        # marimba melody (8th notes)
        m=mel[b%4]
        for i,nt in enumerate(m):
            if nt is None: continue
            s.add('music', marimba(hz(nt), 0.30, vel=0.55 if i%4 else 0.75), s.s16(b,i%16 if b%2 else i), 1.0)
        # drums
        s.add('drums', kick(vel=0.9), s.beat(b),1.0)
        s.add('drums', kick(vel=0.7), s.beat(b)+s.spb*2.5,0.9)
        s.add('drums', snare(vel=0.55), s.beat(b)+s.spb*1,1.0)
        s.add('drums', snare(vel=0.6), s.beat(b)+s.spb*3,1.0)
        for k in range(8):
            s.add('drums', shaker(vel=0.5 if k%2 else 0.35), s.s16(b,k*2),1.0)
            if k%2==1: s.add('drums', hat(vel=0.35), s.s16(b,k*2),1.0)
        if b%4==3:
            for k in range(4):
                s.add('drums', snare(vel=0.35+0.1*k), s.s16(b,12+k),1.0)
        # stab accents
        if b%4==0:
            s.add('music', stab([hz(x) for x in c],0.22,vel=0.30), s.beat(b),1.0)
    return s

def song_nightmood():
    """QKThr type — dark mellow keys, slow, moody."""
    s=Song(84,8,"Nightmood")
    prog=[['D3','F3','A3','C4'],['Bb2','D3','F3','A3'],['G2','Bb2','D3','F3'],['A2','C#3','E3','G3']]
    melody=[['D5',None,None,'C5',None,'A4',None,None,'F4',None,None,None,'A4',None,'C5',None],
            ['Bb4',None,None,'A4',None,'F4',None,None,'D4',None,None,None,'F4',None,'A4',None],
            ['G4',None,None,'F4',None,'D4',None,None,'Bb3',None,None,None,'D4',None,'F4',None],
            ['A4',None,None,'G4',None,'E4',None,None,'C#4',None,None,None,'E4',None,'G4',None]]
    for b in range(8):
        c=prog[b%4]
        # mellow pad + keys
        s.add('music', pad_chord([hz(x) for x in c], 4*s.spb, vel=0.40, cut=1300), s.beat(b),1.0)
        for k,nt in enumerate(c):
            s.add('music', pianoish(hz(nt), 1.4, vel=0.42-0.05*k), s.beat(b)+k*s.spb*0.06,1.0)
        m=melody[b%4]
        for i,nt in enumerate(m):
            if nt is None: continue
            s.add('music', pianoish(hz(nt),1.6,vel=0.55), s.s16(b,i),1.0)
        # sub bass + soft drums
        s.add('bass', sub808(hz(c[0])/2, 1.2, vel=0.75), s.beat(b),1.0)
        s.add('bass', saw_bass(hz(c[0])/2, 0.9, vel=0.35, cut=220), s.beat(b),1.0)
        s.add('drums', kick(vel=0.55,dur=0.42), s.beat(b),1.0)
        s.add('drums', kick(vel=0.35,dur=0.42), s.beat(b)+s.spb*2.5,0.9)
        s.add('drums', snare(vel=0.22), s.beat(b)+s.spb*2,1.0)
        for k in range(4):
            s.add('drums', hat(vel=0.16), s.s16(b,k*4+2),1.0)
    s.add('fx', vinyl(s.dur, vel=0.5), 0.0, 1.0)
    return s

def song_traptrouble():
    """Trap / 808 — aggressive, fail-clip energy, but original."""
    s=Song(142,8,"Traptrouble")
    prog=[['C#3','E3','G#3'],['A2','C#3','E3'],['F#2','A2','C#3'],['G#2','C3','D#3']]
    bells=[[ 'C#5',None,'G#4',None,'E5',None,'C#5',None,'G#4','E4',None,None,'C#5',None,'E5',None],
           [ 'A4',None,'E4',None,'C#5',None,'A4',None,'E4','C#4',None,None,'A4',None,'C#5',None],
           [ 'F#4',None,'C#4',None,'A4',None,'F#4',None,'C#4','A3',None,None,'F#4',None,'A4',None],
           [ 'G#4',None,'D#4',None,'B4',None,'G#4',None,'D#4','B3',None,None,'G#4',None,'B4',None]]
    for b in range(8):
        c=prog[b%4]
        # 808 sub on beats 1 and 3
        s.add('bass', sub808(hz(c[0])/2, 1.1, vel=0.95), s.beat(b),1.0)
        s.add('bass', sub808(hz(c[0])/2, 0.95, vel=0.85), s.beat(b)+s.spb*2,0.95)
        if b%2==1:
            s.add('bass', sub808(hz(c[0])/2, 0.6, vel=0.7), s.beat(b)+s.spb*3.5,0.9)
        # dark bells
        m=bells[b%4]
        for i,nt in enumerate(m):
            if nt is None: continue
            s.add('music', bell(hz(nt),0.9,vel=0.32), s.s16(b,i),1.0)
        # pad
        s.add('music', pad_chord([hz(x) for x in c], 4*s.spb, vel=0.22, cut=900), s.beat(b),1.0)
        # drums: kick 1 + 2.75, snare on 3, rolling hats
        s.add('drums', kick(vel=0.95), s.beat(b),1.0)
        s.add('drums', kick(vel=0.8), s.beat(b)+s.spb*2.75,1.0)
        s.add('drums', snare(vel=0.6), s.beat(b)+s.spb*2,1.0)
        s.add('drums', clap(vel=0.45), s.beat(b)+s.spb*2,1.0)
        for k in range(16):
            v=0.30 if k%4==0 else (0.18 if k%2 else 0.10)
            s.add('drums', hat(vel=v, open_=(k==14)), s.s16(b,k),1.0)
        if b%4==3:
            for k in range(6):
                s.add('drums', snare(vel=0.2+0.06*k), s.s16(b,10+k),1.0)
    return s

def song_rankmachine():
    """Game-show / countdown vibe — ranking reels ke liye."""
    s=Song(126,8,"Rankmachine")
    prog=[['E3','G#3','B3','D#4'],['C#3','E3','G#3','B3'],['A2','C#3','E3','G#3'],['B2','D#3','F#3','A3']]
    arp=[[0,2,1,3],[0,2,1,3],[0,2,1,3],[0,3,2,1]]
    lead=[[ 'E5',None,'D#5','E5',None,'B4',None,'G#4','E4',None,'G#4','B4',None,'E5',None,None],
          [ 'C#5',None,'B4','C#5',None,'G#4',None,'E4','C#4',None,'E4','G#4',None,'C#5',None,None],
          [ 'A4',None,'G#4','A4',None,'E4',None,'C#4','A3',None,'C#4','E4',None,'A4',None,None],
          [ 'B4',None,'A4','B4',None,'F#4',None,'D#4','B3',None,'D#4','F#4',None,'B4',None,None]]
    for b in range(8):
        c=prog[b%4]
        # stabs on 1 & 3
        s.add('music', stab([hz(x) for x in c],0.35,vel=0.55), s.beat(b),1.0)
        s.add('music', stab([hz(x) for x in c],0.28,vel=0.40), s.beat(b)+s.spb*3,1.0)
        # arpeggio 16ths
        a=arp[b%4]
        for k in range(8):
            nt=c[a[k%4]]
            s.add('music', marimba(hz(nt),0.22,vel=0.26), s.s16(b,k*2),1.0)
        # lead
        m=lead[b%4]
        for i,nt in enumerate(m):
            if nt is None: continue
            s.add('music', ks_pluck(hz(nt),0.28,damp=0.99,bright=0.8,vel=0.5), s.s16(b,i),1.0)
        # bass
        s.add('bass', saw_bass(hz(c[0])/2, 0.5, vel=0.75, cut=320), s.beat(b),1.0)
        s.add('bass', saw_bass(hz(c[0])/2, 0.4, vel=0.6, cut=320), s.beat(b)+s.spb*2,1.0)
        # drums big
        s.add('drums', kick(vel=1.0), s.beat(b),1.0)
        s.add('drums', kick(vel=0.8), s.beat(b)+s.spb*2,1.0)
        s.add('drums', clap(vel=0.6), s.beat(b)+s.spb*1,1.0)
        s.add('drums', snare(vel=0.45), s.beat(b)+s.spb*3,1.0)
        for k in range(16):
            s.add('drums', hat(vel=0.12 if k%2 else 0.22), s.s16(b,k),1.0)
        if b%4==3:
            for k in range(3):
                s.add('drums', woodblock(f=1100,vel=0.5), s.s16(b,12+k*2),1.0)
    return s

if __name__=="__main__":
    import os
    os.makedirs("/home/user/audio_preview/orig",exist_ok=True)
    for fn in [song_monkeyfunk, song_nightmood, song_traptrouble, song_rankmachine]:
        s=fn()
        p=f"/home/user/audio_preview/orig/{s.name}.wav"
        master(s,p)
        print("OK",p, round(len(s.bus['drums'])/SR,2),"s")
