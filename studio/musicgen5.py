"""
musicgen5.py — "TUTU" rhythmic hook tracks.
User ka brief: "tutu tutututut tutu tututututu tutu" — staccato rhythmic motif.
Avoid: Christmas/jingle feel (no bells/glock, no major sleigh vibe). Use minor + punchy staccato.
"""
import numpy as np, os, importlib.util
from scipy.signal import butter, sosfilt

spec=importlib.util.spec_from_file_location("m2","/home/user/studio/musicgen2.py")
m2=importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
SR=m2.SR; Song=m2.Song; hz=m2.hz; ns=m2.ns; _mp=m2._mp; rng=m2.rng
kick=m2.kick; snare=m2.snare; hat=m2.hat; shaker=m2.shaker; woodblock=m2.woodblock
marimba=m2.celesta

# ---------------------------------------------------------------- new sounds
def stab_pluck(f, dur, vel=1.0, bright=0.9):
    """short punchy pluck — 'tu' sound. no delay-line, no bell shimmer."""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    kmax=int(min(18, 9000/max(f,1)))
    for k in range(1,kmax+1):
        amp=(bright**(k-1))/(k**0.9)
        y+=amp*np.sin(2*np.pi*f*k*t+rng.uniform(0,6.28))*np.exp(-t/(0.075/(1+0.35*(k-1))))
    nt=ns(0.008)
    nz=sosfilt(butter(2,[800,5000],'band',fs=SR,output='sos'),rng.normal(0,1,nt))
    nz*=np.exp(-np.arange(nt)/(0.0022*SR))
    y[:nt]+=nz*0.35
    sos=butter(2,6500,'low',fs=SR,output='sos'); y=sosfilt(sos,y)
    a=min(ns(0.0015),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def stab_brass(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,12):
        if f*k>7000: break
        y+=(1.0/(k**0.8))*np.sin(2*np.pi*f*k*t+rng.uniform(0,6.28))
    y=sosfilt(butter(2,[350,3800],'band',fs=SR,output='sos'),y)
    e=np.minimum(1,t/0.004)*np.exp(-t/0.055)
    return _mp(y*e,vel)

def sub808(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    fr=f*(1+0.6*np.exp(-18*t))
    ph=2*np.pi*np.cumsum(fr)/SR
    y=np.sin(ph)*np.exp(-t/max(0.25,dur*0.7))
    a=min(ns(0.003),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def clap(dur=0.20, vel=1.0):
    n=ns(dur); y=np.zeros(n)
    for k,off in enumerate([0,0.010,0.021]):
        i=ns(off); m=min(n,i+ns(0.10))
        seg=sosfilt(butter(2,[900,5200],'band',fs=SR,output='sos'),rng.normal(0,1,m-i))
        seg*=np.exp(-32*np.arange(m-i)/SR)
        y[i:m]+=seg*(1.0-0.2*k)
    return _mp(y,vel*0.7)

# ---------------------------------------------------------------- rhythm
# "tu-tu | tu-tu-tu-tu | tu-tu | tu-tu-tu-tu-tu"
MOTIF=[(0,0.95),(2,0.70),
       (4,0.85),(5,0.80),(6,0.88),(7,0.95),
       (10,0.75),(12,0.90),
       (13,0.82),(14,0.88),(15,1.00)]

def pick(bars, sc_root, sc_alt, mode="pluck"):
    """melody: root note on motif, second half of every 2nd bar jumps for hook"""
    out=[]
    for b in range(bars):
        for step,v in MOTIF:
            nt = sc_alt if (b%2==1 and step>=10) else sc_root
            out.append((b,step,nt,v))
    return out

def T1_tutu_trap():
    s=Song(144,8,"T1_TutuTrap",swing=0.0)
    # A minor: A, G, F, E
    roots=[('A2','A4'),('G2','G4'),('F2','F4'),('E2','E4')]
    for b,(root,lead) in enumerate([roots[i%4] for i in range(8)]):
        # 808 bass
        s.add('bass', sub808(hz(root),0.55,vel=0.95), s.T(b,0),1.0,human=0.002)
        s.add('bass', sub808(hz(root),0.45,vel=0.80), s.T(b,10),1.0,human=0.002)
        # lead: TUTU motif with stab pluck + brass octave double (punch)
        for bb,step,nt,v in [(b,st,ld,vv) for (bbb,st,vv) in [] ]: pass
        for step,v in MOTIF:
            note = hz(lead)*1.5 if (b%2==1 and step>=10) else hz(lead)
            s.add('lead', stab_pluck(note,0.14,vel=0.55*v), s.T(b,step),1.0,human=0.002)
            s.add('harm', stab_brass(hz(root)*2,0.10,vel=0.16*v), s.T(b,step),1.0,human=0.002)
        # drums
        s.add('drums', kick(vel=0.95,dur=0.26), s.T(b,0),1.0)
        s.add('drums', kick(vel=0.75,dur=0.24), s.T(b,6),1.0)
        s.add('drums', kick(vel=0.70,dur=0.22), s.T(b,10),1.0)
        s.add('drums', snare(vel=0.62), s.T(b,4),1.0)
        s.add('drums', snare(vel=0.66), s.T(b,12),1.0)
        s.add('drums', clap(vel=0.35), s.T(b,12),1.0)
        for k in range(16):
            if k%2==0: s.add('drums', hat(vel=0.16 if k%4 else 0.22, open_=(k==14)), s.T(b,k),1.0,human=0.003)
        # fill
        if b%4==3:
            for i,st in enumerate((8,9,10,11)):
                s.add('drums', snare(vel=0.35+0.1*i), s.T(b,st),1.0)
    return s

def T2_tutu_bounce():
    s=Song(132,8,"T2_TutuBounce",swing=0.05)
    roots=[('D3','D4'),('C3','C4'),('Bb2','Bb3'),('A2','A3')]
    for b,(root,lead) in enumerate([roots[i%4] for i in range(8)]):
        # bass: staccato 8ths oom-pah-ish but not circus
        s.add('bass', sub808(hz(root)/2,0.30,vel=0.9), s.T(b,0),1.0,human=0.003)
        s.add('bass', sub808(hz(root)/2,0.25,vel=0.7), s.T(b,8),1.0,human=0.003)
        # marimba TUTU
        for step,v in MOTIF:
            note = hz(lead)*1.5 if (b%2==1 and step>=10) else hz(lead)
            s.add('lead', marimba(note,0.20,vel=0.62*v), s.T(b,step),1.0,human=0.003)
            s.add('harm', stab_pluck(hz(root)*4,0.09,vel=0.13*v), s.T(b,step),1.0,human=0.003)
        # drums
        s.add('drums', kick(vel=0.70,dur=0.22), s.T(b,0),1.0)
        s.add('drums', kick(vel=0.55,dur=0.20), s.T(b,8),1.0)
        s.add('drums', snare(vel=0.42), s.T(b,4),1.0)
        s.add('drums', snare(vel=0.45), s.T(b,12),1.0)
        for k in range(0,16,2):
            s.add('drums', shaker(vel=0.16 if k%4 else 0.22), s.T(b,k),1.0,human=0.004)
    return s

def T3_tutu_comedy():
    s=Song(152,8,"T3_TutuComedy",swing=0.07)
    roots=[('E2','E4'),('D2','D4'),('C2','C4'),('B1','B3')]
    for b,(root,lead) in enumerate([roots[i%4] for i in range(8)]):
        s.add('bass', sub808(hz(root),0.28,vel=0.85), s.T(b,0),1.0,human=0.002)
        for step,v in MOTIF:
            note = hz(lead)*1.5 if (b%2==1 and step>=10) else hz(lead)
            # leading instrument bounces: brass first 4 bars, pluck next 4 (research rule)
            if b<4:
                s.add('lead', stab_brass(note,0.13,vel=0.52*v), s.T(b,step),1.0,human=0.002)
            else:
                s.add('lead', stab_pluck(note,0.13,vel=0.58*v), s.T(b,step),1.0,human=0.002)
            s.add('harm', woodblock(f=1500, dur=0.05, vel=0.10*v), s.T(b,step),1.0,human=0.002)
        # drums: snappy
        s.add('drums', kick(vel=0.85,dur=0.22), s.T(b,0),1.0)
        s.add('drums', kick(vel=0.60,dur=0.20), s.T(b,10),1.0)
        s.add('drums', snare(vel=0.55), s.T(b,4),1.0)
        s.add('drums', clap(vel=0.30), s.T(b,12),1.0)
        for k in range(0,16,2):
            s.add('drums', hat(vel=0.14 if k%4 else 0.20), s.T(b,k),1.0,human=0.003)
        if b%4==3:
            for i,st in enumerate((12,13,14,15)):
                s.add('drums', snare(vel=0.3+0.12*i), s.T(b,st),1.0)
    return s

if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/tutu",exist_ok=True)
    G={'lead':1.15,'harm':0.42,'bass':0.95,'drums':0.85,'fx':0.2}
    for fn in (T1_tutu_trap,T2_tutu_bounce,T3_tutu_comedy):
        s=fn(); p=f"/home/user/audio_preview/tutu/{s.name}.wav"
        m2.master(s,p,gains=G); print("OK",p,round(s.dur,1),"s")
