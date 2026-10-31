"""
musicgen2.py — Approach 1 (asli instruments + article rules) aur Approach 2 (same notes, naya combo)

Rules jo follow hue (dekho MUSIC_PLAYBOOK.md):
  • melody alag register + alag timbre (masking zero)
  • hook 2 instruments pe double (octave/third)
  • 16th swing + velocity/timing humanize
  • build: sparse -> full -> variation + fill
  • ek high sustained note transition pe
  • -14 LUFS master (ffmpeg loudnorm baad me)
"""
import numpy as np, wave, os
from scipy.signal import lfilter, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(11)

NB = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,
      'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
def hz(n):
    if not isinstance(n,str): return float(n)
    return 440.0*2**((NB[n[:-1]]+12*(int(n[-1])+1)-69)/12)
def ns(d): return int(round(d*SR))

def soft_limit(x, d=1.0): return np.tanh(x*d)

# ------------------------------------------------------------------ instruments
def _mp(y, g=1.0):
    m=np.max(np.abs(y))+1e-9
    return g*y/m

def flute(f, dur, vel=1.0, breath=0.055, vib=5.3):
    n=ns(dur); t=np.arange(n)/SR
    vibamt=0.0045*np.minimum(1,t/0.35)*np.sin(2*np.pi*vib*t)
    ph=2*np.pi*np.cumsum(f*(1+vibamt))/SR
    y=np.sin(ph)+0.20*np.sin(2*ph)+0.07*np.sin(3*ph)+0.03*np.sin(4*ph)
    br=rng.normal(0,1,n)
    br=sosfilt(butter(2,[900,5200],'band',fs=SR,output='sos'),br)
    # chiff at attack
    chiff=np.exp(-np.arange(n)/(0.012*SR))*0.5
    y=y+breath*br*(0.7+0.6*chiff)
    a=min(ns(0.030),n); e=np.ones(n); e[:a]=np.linspace(0,1,a)**1.3
    r=min(ns(min(0.09,dur*0.45)),n); e[-r:]*=np.linspace(1,0,r)**1.6
    return _mp(y*e,vel)

def pizz(f, dur, vel=1.0, damp=0.988, bright=0.72, tau=None):
    """pizzicato — additive harmonic stack, koi delay-line nahi (no boing)."""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    base = tau if tau else max(0.18, dur*0.9)
    kmax = int(min(24, 9000.0/max(f,1)))
    for k in range(1, kmax+1):
        amp = (1.0/(k**1.05)) * (bright**(k-1))
        tk = base/(1.0+0.62*(k-1))
        y += amp*np.sin(2*np.pi*f*k*t + rng.uniform(0,6.28))*np.exp(-t/max(tk,1e-4))
    nt=ns(0.012)
    nz=sosfilt(butter(2,3000,'low',fs=SR,output='sos'),rng.normal(0,1,nt))
    nz*=np.exp(-np.arange(nt)/(0.0035*SR))
    y[:nt]+=nz*0.22
    a=min(ns(0.003),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def harmonium(freqs, dur, vel=1.0):
    """reed organ — detuned saws + wobble + breath"""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for f in freqs:
        for det in (0.9965,1.0,1.0035):
            for k in range(1,10):
                y+=(1.0/(k**1.25))*np.sin(2*np.pi*f*det*k*t+rng.uniform(0,6.28))
    wob=1+0.055*np.sin(2*np.pi*4.6*t)+0.03*np.sin(2*np.pi*0.63*t)
    y*=wob
    y+=0.02*rng.normal(0,1,n)
    y=sosfilt(butter(2,3000,'low',fs=SR,output='sos'),y)
    a=min(ns(0.11),n); e=np.ones(n); e[:a]=np.linspace(0,1,a)**1.4
    r=min(ns(min(0.6,dur*0.5)),n); e[-r:]*=np.linspace(1,0,r)**1.1
    return _mp(y*e,vel)

def piano_off(f, dur, vel=1.0, detune=0.004):
    """thoda out-of-tune echoing piano (QKThr detail)"""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for d_,g in [(1.0,1.0),(1+detune,0.55),(1-detune,0.45)]:
        y+=g*(np.sin(2*np.pi*f*d_*t)+0.35*np.sin(2*np.pi*2*f*d_*t)*np.exp(-3*t))
    y*=np.exp(-1.5*t)
    a=min(ns(0.006),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def rhodes(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    mod=np.sin(2*np.pi*f*2.01*t)*2.0*np.exp(-2.6*t)
    y=np.sin(2*np.pi*f*t+mod)*np.exp(-1.5*t)
    y+=0.18*np.sin(2*np.pi*f*3.0*t)*np.exp(-4.5*t)
    a=min(ns(0.004),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def celesta(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*f*t)*np.exp(-2.0*t)
       +0.50*np.sin(2*np.pi*2*f*t)*np.exp(-3.2*t)
       +0.24*np.sin(2*np.pi*3.01*f*t)*np.exp(-5.0*t)
       +0.10*np.sin(2*np.pi*4.2*f*t)*np.exp(-7.0*t))
    a=min(ns(0.003),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def vibes(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    trem=1+0.22*np.sin(2*np.pi*5.2*t+0.4)
    y=(np.sin(2*np.pi*f*t)+0.22*np.sin(2*np.pi*4*f*t)*np.exp(-6*t))*np.exp(-1.1*t)*trem
    a=min(ns(0.004),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def clav(f, dur, vel=1.0):
    """clavinet stab — additive + short band noise, no delay-line."""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,14):
        if f*k>9000: break
        tk=0.055/(1.0+0.10*(k-1))
        y+=(1.0/(k**1.15))*np.sin(2*np.pi*f*k*t+rng.uniform(0,6.28))*np.exp(-t/tk)
    nt=ns(0.02)
    nz=sosfilt(butter(2,[600,4500],'band',fs=SR,output='sos'),rng.normal(0,1,nt))
    nz*=np.exp(-np.arange(nt)/(0.006*SR))
    y[:nt]+=nz*0.30
    y=sosfilt(butter(2,[280,6500],'band',fs=SR,output='sos'),y)
    a=min(ns(0.002),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def ubass(f, dur, vel=1.0):
    """upright bass — sine body + harmonics + pluck click. No delay-line."""
    n=ns(dur); t=np.arange(n)/SR
    body = np.sin(2*np.pi*f*t)*np.exp(-t/max(0.55,dur*0.8))
    h2   = 0.34*np.sin(2*np.pi*f*2*t+0.6)*np.exp(-t/0.42)
    h3   = 0.16*np.sin(2*np.pi*f*3*t+1.2)*np.exp(-t/0.26)
    h4   = 0.08*np.sin(2*np.pi*f*4*t+2.1)*np.exp(-t/0.16)
    sub  = 0.30*np.sin(2*np.pi*f*0.5*t)*np.exp(-t/0.50)
    y = body+h2+h3+h4+sub
    nt=ns(0.014)
    nz=sosfilt(butter(2,[200,1600],'band',fs=SR,output='sos'),rng.normal(0,1,nt))
    nz*=np.exp(-np.arange(nt)/(0.004*SR))
    y[:nt]+=nz*0.26
    y=sosfilt(butter(2,900,'low',fs=SR,output='sos'),y)
    a=min(ns(0.004),n); y[:a]*=np.linspace(0,1,a)
    r=min(ns(0.08),n); y[-r:]*=np.linspace(1,0,r)
    return _mp(y,vel)

# ------------------------------------------------------------------ drums
def kick(dur=0.32, vel=1.0, p=1.0):
    n=ns(dur); t=np.arange(n)/SR
    fr=46+95*np.exp(-24*t); ph=2*np.pi*np.cumsum(fr)/SR
    body=np.sin(ph)*np.exp(-7.0*t)
    click=rng.normal(0,1,n)*np.exp(-150*t)*0.22*p
    return vel*(body+click)

def snare(dur=0.20, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    nz=sosfilt(butter(2,[1400,9000],'band',fs=SR,output='sos'),rng.normal(0,1,n))*np.exp(-20*t)
    tone=np.sin(2*np.pi*185*t)*np.exp(-28*t)*0.40
    return vel*(nz*0.75+tone)

def brush(dur=0.26, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    nz=sosfilt(butter(2,[1200,7000],'band',fs=SR,output='sos'),rng.normal(0,1,n))
    e=(1-np.exp(-60*t))*np.exp(-11*t)
    return vel*nz*e*0.55

def hat(dur=0.05, vel=1.0, open_=False):
    n=ns(dur if not open_ else 0.17); t=np.arange(n)/SR
    y=sosfilt(butter(3,7500,'high',fs=SR,output='sos'),rng.normal(0,1,n))
    y*=np.exp(-(34 if not open_ else 13)*t)
    return vel*y*0.5

def shaker(dur=0.065, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=sosfilt(butter(3,5200,'high',fs=SR,output='sos'),rng.normal(0,1,n))
    e=np.exp(-24*t)*(1-np.exp(-110*t))
    return vel*y*e*0.32

def rim(dur=0.05, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*1700*t)+0.6*np.sin(2*np.pi*2600*t))*np.exp(-55*t)
    return vel*y*0.4

def woodblock(f=1050, dur=0.08, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*f*2.6*t))*np.exp(-42*t)
    return vel*y*0.45

# ------------------------------------------------------------------ song container
class Song:
    def __init__(self, bpm, bars, name, swing=0.06):
        self.bpm=bpm; self.spb=60.0/bpm; self.bars=bars; self.swing=swing
        self.bar=4*self.spb
        self.dur=bars*self.bar+1.6
        self.n=ns(self.dur); self.name=name
        self.bus={k:np.zeros(self.n) for k in ('lead','harm','bass','drums','fx')}
    def T(self, bar, step):
        """16th grid + swing on off-steps"""
        sw = self.swing*self.spb/4 if step%2 else 0
        return bar*self.bar + step*self.spb/4 + sw
    def add(self, bus, sig, t, g=1.0, human=0.006):
        t=max(0.0, t+rng.normal(0,human))
        i=ns(t); j=min(self.n,i+len(sig))
        if i>=self.n: return
        self.bus[bus][i:j]+=sig[:j-i]*g

def reverb_ir(rt=1.1, pre=0.014):
    n=ns(rt); t=np.arange(n)/SR
    ir=rng.normal(0,1,n)*np.exp(-6.9*t/rt)
    ir=sosfilt(butter(2,5000,'low',fs=SR,output='sos'),ir)
    ir=np.concatenate([np.zeros(ns(pre)),ir])
    return ir/np.max(np.abs(ir))

def master(song, path, gains=None, wet=None, wide=0.12):
    gains=gains or {'lead':1.0,'harm':0.62,'bass':0.85,'drums':0.80,'fx':0.30}
    wet  =wet  or {'lead':0.22,'harm':0.30,'bass':0.04,'drums':0.10,'fx':0.5}
    ir=reverb_ir()
    L=np.zeros(song.n); R=np.zeros(song.n); mono=np.zeros(song.n)
    for k,v in song.bus.items():
        w=fftconvolve(v,ir)[:song.n]*wet[k]
        mono+=v*gains[k]
        L+=(v*(1-wide*0.5)+w*0.9)*gains[k]
        R+=(v*(1+wide*0.5)+w*1.05)*gains[k]
    # glue compressor (simple envelope-follower)
    a=np.exp(-1/(SR*0.008)); r=np.exp(-1/(SR*0.12))
    env=0.0; g=np.zeros(song.n)
    mx=0.0
    for i in range(0,song.n,4):
        v=abs(mono[i]); env = a*env+(1-a)*v if v>env else r*env+(1-r)*v
        g[i:i+4]=env
    g=np.repeat(g[::4],4)[:song.n]
    thr=0.22
    gr=np.where(g>thr, (thr/np.maximum(g,1e-6))**0.45, 1.0)
    gr=sosfilt(butter(2,8,'low',fs=SR,output='sos'),gr)
    L*=gr; R*=gr
    mx=max(np.max(np.abs(L)),np.max(np.abs(R)))+1e-9
    L/=mx; R/=mx
    L=soft_limit(L*1.10,1.0)*0.90
    R=soft_limit(R*1.10,1.0)*0.90
    st=np.stack([L,R],1)
    f=ns(0.015); st[:f]*=np.linspace(0,1,f)[:,None]
    f2=ns(0.45); st[-f2:]*=np.linspace(1,0,f2)[:,None]
    pcm=(np.clip(st,-1,1)*32767).astype('<i2')
    with wave.open(path,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return path

# ================================================================== A1 — Approach 1
def A1_monkeyflute():
    """Monkeys palette (flute + pizz violin/viola/cello + shaker), mera apna melody."""
    s=Song(142, 8, "A1_MonkeyFlute", swing=0.07)
    chords=[['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['E2','G2','B3'],
            ['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['A2','C3','E3']]
    mel=[[('A4',0),('C5',2),('E5',4),('C5',6),('A4',8),('G4',10),('E4',12),('G4',14)],
         [('F4',0),('A4',2),('C5',4),('A4',6),('F4',8),('E4',10),('C4',12),('E4',14)],
         [('G4',0),('B4',2),('D5',4),('B4',6),('G4',8),('F4',10),('D4',12),('F4',14)],
         [('A4',0),('C5',2),('E5',4),('A5',6),('E5',8),('C5',10),('A4',12),('E4',14)],
         [('A4',0),('C5',2),('E5',4),('C5',6),('A4',8),('G4',10),('E4',12),('G4',14)],
         [('F4',0),('A4',2),('C5',4),('A4',6),('F4',8),('E4',10),('C4',12),('E4',14)],
         [('G4',0),('B4',2),('D5',4),('B4',6),('G4',8),('F4',10),('D4',12),('F4',14)],
         [('A4',0),('C5',2),('E5',4),('A5',6),('G5',8),('E5',10),('C5',12),('A4',14)]]
    for b in range(8):
        c=chords[b]; full = b>=2
        # bass: pizz cello on 1 & 3 (root, fifth)
        s.add('bass', pizz(hz(c[0]),0.42,damp=0.993,bright=0.42,vel=0.95), s.T(b,0), 1.0)
        if full:
            s.add('bass', pizz(hz(c[0]),0.34,damp=0.991,bright=0.42,vel=0.75), s.T(b,8), 0.95)
            s.add('bass', pizz(hz(c[2]) if len(c)>2 else hz(c[0]),0.24,damp=0.99,bright=0.5,vel=0.45), s.T(b,12),0.75)
        # harmony: viola/violin staccato chords on off-beats (Monkeys ka signature)
        if full:
            for st in (2,6,10,14):
                for j,nt in enumerate(c[1:]):
                    s.add('harm', pizz(hz(nt)+j*0,0.16,damp=0.985,bright=0.62,vel=0.30-j*0.05), s.T(b,st), 1.0, human=0.004)
        # lead flute: melody + hook doubled an octave below by violin pizz
        for nt,st in mel[b]:
            v=0.62 if st in (0,4,8,12) else 0.48
            s.add('lead', flute(hz(nt),0.26,vel=v), s.T(b,st), 1.0, human=0.003)
            if full:
                s.add('lead', pizz(hz(nt)/2,0.20,damp=0.986,bright=0.7,vel=0.26), s.T(b,st), 1.0, human=0.003)
        # percussion: shaker 16ths + light kick/snare
        for k in range(16):
            sv = 0.45 if k%4==0 else (0.30 if k%2 else 0.20)
            s.add('drums', shaker(vel=sv), s.T(b,k), 1.0, human=0.004)
        if full:
            s.add('drums', kick(vel=0.55,dur=0.22), s.T(b,0), 1.0)
            s.add('drums', kick(vel=0.34,dur=0.20), s.T(b,10), 1.0)
            s.add('drums', rim(vel=0.30), s.T(b,8), 1.0)
        # build: bar 2 me ek high sustained note (article rule)
        if b==1:
            s.add('lead', flute(hz('A5'), s.bar*1.0, vel=0.20, breath=0.08), s.T(b,0), 1.0, human=0)
        # fill bar 7
        if b==6:
            for k in range(4):
                s.add('drums', woodblock(f=1150, vel=0.35+0.1*k), s.T(b,12+k), 1.0)
    return s

# ================================================================== A2 — Approach 2
def A2_monkeyalt():
    """SAME melody + chords, naya combo: celesta lead + vibes octave double + clav comping + upright bass + brush kit."""
    s=Song(142, 8, "A2_MonkeyAlt", swing=0.07)
    chords=[['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['E2','G2','B3'],
            ['A2','C3','E3'],['F2','A2','C3'],['G2','B2','D3'],['A2','C3','E3']]
    mel=[[('A4',0),('C5',2),('E5',4),('C5',6),('A4',8),('G4',10),('E4',12),('G4',14)],
         [('F4',0),('A4',2),('C5',4),('A4',6),('F4',8),('E4',10),('C4',12),('E4',14)],
         [('G4',0),('B4',2),('D5',4),('B4',6),('G4',8),('F4',10),('D4',12),('F4',14)],
         [('A4',0),('C5',2),('E5',4),('A5',6),('E5',8),('C5',10),('A4',12),('E4',14)],
         [('A4',0),('C5',2),('E5',4),('C5',6),('A4',8),('G4',10),('E4',12),('G4',14)],
         [('F4',0),('A4',2),('C5',4),('A4',6),('F4',8),('E4',10),('C4',12),('E4',14)],
         [('G4',0),('B4',2),('D5',4),('B4',6),('G4',8),('F4',10),('D4',12),('F4',14)],
         [('A4',0),('C5',2),('E5',4),('A5',6),('G5',8),('E5',10),('C5',12),('A4',14)]]
    for b in range(8):
        c=chords[b]; full=b>=1
        # upright bass: root + fifth walking
        s.add('bass', ubass(hz(c[0])/2,0.55,vel=0.95), s.T(b,0),1.0)
        s.add('bass', ubass(hz(c[0])/2,0.40,vel=0.70), s.T(b,8),0.95)
        if b%2==1: s.add('bass', ubass(hz(c[1])/2,0.30,vel=0.55), s.T(b,14),0.85)
        # clav comping: 16th chord stabs (rhythmic, article: distinct timbre from lead)
        for st in (0,3,6,10,13):
            s.add('harm', clav(hz(c[1])*2,0.12,vel=0.20), s.T(b,st),1.0,human=0.004)
            s.add('harm', clav(hz(c[2])*2,0.12,vel=0.16), s.T(b,st),1.0,human=0.004)
        # lead: celesta melody, doubled by vibes an octave down (2 families = colour)
        for nt,st in mel[b]:
            v=0.60 if st in (0,4,8,12) else 0.46
            s.add('lead', celesta(hz(nt),0.55,vel=v), s.T(b,st),1.0,human=0.003)
            if full:
                s.add('lead', vibes(hz(nt)/2,0.45,vel=0.30), s.T(b,st),1.0,human=0.004)
        # brush kit: soft swing
        if full:
            s.add('drums', kick(vel=0.55,dur=0.24), s.T(b,0),1.0)
            s.add('drums', kick(vel=0.40,dur=0.22), s.T(b,9),1.0)
            s.add('drums', brush(vel=0.32), s.T(b,4),1.0)
            s.add('drums', brush(vel=0.34), s.T(b,12),1.0)
        for k in range(0,16,2):
            s.add('drums', hat(vel=0.16 if k%4 else 0.22), s.T(b,k),1.0,human=0.005)
        if b==0:  # intro shimmer
            s.add('fx', celesta(hz('E6'),1.2,vel=0.18), 0.0,1.0,human=0)
        if b==5:
            for k in range(4):
                s.add('drums', brush(vel=0.20+0.06*k), s.T(b,12+k),1.0)
    return s

# ================================================================== B1 — Approach 1
def B1_nightharmonium():
    """QKThr palette: harmonium + upright bass + brushed kit + out-of-tune piano. Db major, 61 BPM."""
    s=Song(61, 5, "B1_NightHarmonium", swing=0.03)
    prog=[['Db3','F3','Ab3','C4'],
          ['Ab2','C3','Eb3','Gb3'],
          ['Db3','F3','Ab3','C4'],
          ['Gb2','Bb2','Db3','F3'],
          ['Db3','F3','Ab3','C4']]
    mel=[('Ab4',0,3),('Gb4',6,2),('F4',9,3),('Eb4',13,3),
         ('C4',0,3),('Eb4',4,2),('Gb4',7,3),('Ab4',12,4),
         ('F4',0,2),('Ab4',3,2),('C5',6,3),('Ab4',10,3),('F4',14,2),
         ('Db4',0,3),('F4',4,3),('Bb4',8,3),('Ab4',12,2),
         ('Db4',0,4),('Ab3',6,3),('F3',10,4)]
    for b in range(5):
        c=prog[b]
        # harmonium: sustained chord + wobble
        s.add('harm', harmonium([hz(x) for x in c], s.bar*0.98, vel=0.42), s.T(b,0), 1.0, human=0.002)
        # out-of-tune piano echo (QKThr detail) — comes and goes
        if b in (1,3,4):
            for k,nt in enumerate(c[1:]):
                s.add('lead', piano_off(hz(nt)*2, 2.2, vel=0.14+0.03*k, detune=0.006), s.T(b,4+k*3),1.0, human=0.012)
        # melody long phrases (piano-ish lead synth)
        if b in (0,2,4):
            for nt,st,dur in mel:
                if (b==0 and st<13) or (b==2 and 0<=st<=14) or (b==4):
                    if b==0 and st>10: continue
                    if b==2 and st<3: continue
                    if b==4 and st>2 and st<10: continue
                    s.add('lead', piano_off(hz(nt), dur*s.spb*0.9, vel=0.40), s.T(b,st),1.0, human=0.006)
        # upright bass root notes
        s.add('bass', ubass(hz(c[0])/2, 1.5, vel=0.85), s.T(b,0),1.0, human=0.006)
        if b%2: s.add('bass', ubass(hz(c[1])/2, 0.9, vel=0.45), s.T(b,10),0.8, human=0.008)
        # brushed kit: sparse, dark
        if b>=1:
            s.add('drums', kick(vel=0.42,dur=0.40), s.T(b,0),1.0)
            s.add('drums', brush(vel=0.24), s.T(b,6),1.0)
            s.add('drums', brush(vel=0.26), s.T(b,12),1.0)
            if b%2==0: s.add('drums', kick(vel=0.28,dur=0.40), s.T(b,10),1.0)
        for k in (4,12):
            s.add('drums', hat(vel=0.10, open_=False), s.T(b,k),1.0,human=0.006)
    # tape hiss / room
    hiss=rng.normal(0,1,s.n)*0.006
    hiss=sosfilt(butter(2,[400,5000],'band',fs=SR,output='sos'),hiss)
    s.bus['fx']+=hiss
    return s

# ================================================================== B2 — Approach 2
def B2_nightrhodes():
    """SAME chords + melody, naya combo: Rhodes lead + vibes + upright bass, no harmonium."""
    s=Song(66, 5, "B2_NightRhodes", swing=0.04)
    prog=[['Db3','F3','Ab3','C4'],
          ['Ab2','C3','Eb3','Gb3'],
          ['Db3','F3','Ab3','C4'],
          ['Gb2','Bb2','Db3','F3'],
          ['Db3','F3','Ab3','C4']]
    mel=[('Ab4',0,3),('Gb4',6,2),('F4',9,3),('Eb4',13,3),
         ('C4',0,3),('Eb4',4,2),('Gb4',7,3),('Ab4',12,4),
         ('F4',0,2),('Ab4',3,2),('C5',6,3),('Ab4',10,3),('F4',14,2),
         ('Db4',0,3),('F4',4,3),('Bb4',8,3),('Ab4',12,2),
         ('Db4',0,4),('Ab3',6,3),('F3',10,4)]
    for b in range(5):
        c=prog[b]
        # Rhodes chord bed (soft attack) — lower register than lead (no masking)
        if b>=1:
            for k,nt in enumerate(c):
                s.add('harm', rhodes(hz(nt), 2.4, vel=0.24-0.03*k), s.T(b,0)+k*0.012, 1.0, human=0.006)
        # vibes arpeggio shimmer (texture, article: doublings for richness)
        if b>=2:
            for st in (2,6,10,14):
                s.add('harm', vibes(hz(c[(st//2)%4])*2, 0.9, vel=0.16), s.T(b,st),1.0,human=0.006)
        # lead: Rhodes melody (long phrases) + vibes octave double
        if b in (0,2,4):
            for nt,st,dur in mel:
                if b==0 and st>10: continue
                if b==2 and st<3: continue
                if b==4 and 2<st<10: continue
                s.add('lead', rhodes(hz(nt), dur*s.spb*0.95, vel=0.46), s.T(b,st),1.0, human=0.006)
                s.add('lead', vibes(hz(nt)*2, dur*s.spb*0.9, vel=0.12), s.T(b,st)+0.008,1.0, human=0.008)
        # upright bass
        s.add('bass', ubass(hz(c[0])/2, 1.6, vel=0.90), s.T(b,0),1.0, human=0.006)
        if b%2==0: s.add('bass', ubass(hz(c[2])/2, 0.7, vel=0.40), s.T(b,12),0.75, human=0.01)
        # brush kit
        if b>=1:
            s.add('drums', kick(vel=0.40,dur=0.38), s.T(b,0),1.0)
            s.add('drums', brush(vel=0.26), s.T(b,6),1.0)
            s.add('drums', brush(vel=0.28), s.T(b,12),1.0)
        for k in (4,10,14):
            s.add('drums', hat(vel=0.09), s.T(b,k),1.0,human=0.007)
    return s

if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/orig2",exist_ok=True)
    for fn in (A1_monkeyflute, A2_monkeyalt, B1_nightharmonium, B2_nightrhodes):
        s=fn(); p=f"/home/user/audio_preview/orig2/{s.name}.wav"
        master(s,p); print("OK",p,round(s.dur,1),"s")
