"""
musicgen3.py — A1/A2 boost, B1/B2 funny layer, aur C1/C2 (comedy tracks from research)

Comedy research (MUSIC_PLAYBOOK.md me bhi save):
  • Staccato + alternating root/fifth oom-pah bass = "funny" ki #1 recipe
  • Funny instruments: BASSOON ("clown of the orchestra"), TUBA (staccato), pizzicato strings,
    clarinet, glockenspiel/xylophone, woodblock, slide whistle, kazoo, accordion, muted trumpet "wah-wah"
  • Techniques: dotted/lopsided rhythm, glissando, chromatic runs, stop-time, silence before punchline,
    melody doubled on mallets, melody bouncing between instruments, major key, lots of SPACE
"""
import numpy as np, os, importlib.util
from scipy.signal import butter, sosfilt

spec=importlib.util.spec_from_file_location("m2","/home/user/studio/musicgen2.py")
m2=importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
SR=m2.SR; Song=m2.Song; hz=m2.hz; ns=m2.ns; _mp=m2._mp; rng=m2.rng
pizz=m2.pizz; flute=m2.flute; harmonium=m2.harmonium; piano_off=m2.piano_off
rhodes=m2.rhodes; celesta=m2.celesta; vibes=m2.vibes; clav=m2.clav; ubass=m2.ubass
kick=m2.kick; snare=m2.snare; brush=m2.brush; hat=m2.hat; shaker=m2.shaker
rim=m2.rim; woodblock=m2.woodblock

# ---------------------------------------------------------------- NEW comedy instruments
def bassoon(f, dur, vel=1.0):
    """clown of the orchestra — reedy, nasal, staccato"""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,14):
        if f*k>6000: break
        y += (1.0/(k**0.85))*np.sin(2*np.pi*f*k*t + rng.uniform(0,6.28))
    y += 0.10*rng.normal(0,1,n)
    # nasal formant ~ 500 Hz + 1.1 kHz
    y = sosfilt(butter(2,[300,1500],'band',fs=SR,output='sos'),y)*1.0 + y*0.35
    # reed attack pitch dip
    dip=1-0.02*np.exp(-t/0.03)
    y*= 1+0.0*dip
    e=np.minimum(1,t/0.012)*np.exp(-t/max(0.06,dur*0.9))
    e[-min(ns(0.03),n):]*=np.linspace(1,0,min(ns(0.03),n))
    return _mp(y*e,vel)

def tuba(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*f*t)+0.55*np.sin(2*np.pi*f*2*t+0.4)+0.28*np.sin(2*np.pi*f*3*t+1.1)
       +0.12*np.sin(2*np.pi*f*4*t+2.0))
    br=sosfilt(butter(2,[150,1400],'band',fs=SR,output='sos'),rng.normal(0,1,n))*0.05
    e=np.minimum(1,t/0.02)*np.exp(-t/max(0.09,dur*1.1))
    r=min(ns(0.05),n); e[-r:]*=np.linspace(1,0,r)
    return _mp((y+br)*e,vel)

def clarinet(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,15,2):     # odd harmonics = hollow
        if f*k>7000: break
        y += (1.0/(k**0.9))*np.sin(2*np.pi*f*k*t)
    y=sosfilt(butter(2,[250,2600],'band',fs=SR,output='sos'),y)
    e=np.minimum(1,t/0.015)*np.exp(-t/max(0.08,dur*0.95))
    r=min(ns(0.04),n); e[-r:]*=np.linspace(1,0,r)
    return _mp(y*e,vel)

def glock(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    mod=np.sin(2*np.pi*f*3.01*t)*1.6*np.exp(-4*t)
    y=(np.sin(2*np.pi*f*t+mod)*np.exp(-2.4*t)
       +0.4*np.sin(2*np.pi*f*2.0*t)*np.exp(-4.5*t)
       +0.2*np.sin(2*np.pi*f*5.4*t)*np.exp(-7*t))
    a=min(ns(0.002),n); y[:a]*=np.linspace(0,1,a)
    return _mp(y,vel)

def slide_whistle(f1, f2, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    fr=f1*(f2/f1)**(t/dur)
    fr*=1+0.012*np.sin(2*np.pi*6.5*t)
    ph=2*np.pi*np.cumsum(fr)/SR
    y=np.sin(ph)+0.22*np.sin(2*ph)
    br=sosfilt(butter(2,[900,6000],'band',fs=SR,output='sos'),rng.normal(0,1,n))*0.06
    e=np.minimum(1,t/0.02)*np.minimum(1,(dur-t)/0.04)
    return _mp((y+br)*e,vel)

def wah_trumpet(f, dur, vel=1.0, wah=7.0):
    """muted trumpet 'wah' — brass + plunger filter sweep"""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,11):
        if f*k>7000: break
        y+=(1.0/(k**0.75))*np.sin(2*np.pi*f*k*t+rng.uniform(0,6.28))
    # sweeping bandpass = wah
    out=np.zeros(n)
    seg=ns(0.06)
    for i in range(0,n,seg):
        c=900+1400*(0.5+0.5*np.sin(2*np.pi*wah*t[i]/1.0))
        sos=butter(2,[max(200,c*0.45),min(7000,c*1.6)],'band',fs=SR,output='sos')
        out[i:i+seg]=sosfilt(sos,y[i:i+seg])
    e=np.minimum(1,t/0.02)*np.minimum(1,(dur-t)/0.05)
    return _mp(out*e,vel)

def kazoo(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,18):
        if f*k>9000: break
        y+=(1.0/(k**0.6))*np.sin(2*np.pi*f*k*t)
    # comb/nasal resonance
    y=sosfilt(butter(2,[450,2200],'band',fs=SR,output='sos'),y)*1.2
    y+=0.06*rng.normal(0,1,n)
    e=np.minimum(1,t/0.01)*np.exp(-t/max(0.08,dur))
    return _mp(y*e,vel)

def accordion(freqs, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for f in freqs:
        for det in (0.997,1.003):
            for k in range(1,8):
                y+=(1.0/(k**1.1))*np.sin(2*np.pi*f*det*k*t+rng.uniform(0,6.28))
    trem=1+0.10*np.sin(2*np.pi*5.5*t)
    e=np.minimum(1,t/0.03)*np.exp(-t/max(0.12,dur*1.2))
    r=min(ns(0.05),n); e[-r:]*=np.linspace(1,0,r)
    return _mp(y*trem*e,vel)

def banjo(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k,m in enumerate([1,2,2.7,4.1,5.6,7.2]):
        if f*m>9000: break
        y+=(0.9**k)*np.sin(2*np.pi*f*m*t+rng.uniform(0,6.28))*np.exp(-t/(0.28/(1+k*0.7)))
    nt=ns(0.01)
    nz=sosfilt(butter(2,4000,'low',fs=SR,output='sos'),rng.normal(0,1,nt))*np.exp(-np.arange(nt)/(0.002*SR))
    y[:nt]+=nz*0.25
    return _mp(y,vel)

def ratchet(dur=0.28, vel=1.0, rate=55):
    n=ns(dur); y=np.zeros(n)
    step=int(SR/rate)
    for i in range(0,n-step,step):
        c=rng.normal(0,1,step)*np.exp(-np.arange(step)/(0.0009*SR))
        c=sosfilt(butter(2,[1800,9000],'band',fs=SR,output='sos'),c)
        y[i:i+step]+=c
    return _mp(y,vel)

def timpani(f, dur, vel=1.0):
    n=ns(dur); t=np.arange(n)/SR
    fr=f*(1+0.35*np.exp(-20*t))
    ph=2*np.pi*np.cumsum(fr)/SR
    y=np.sin(ph)*np.exp(-3.2*t)+0.2*rng.normal(0,1,n)*np.exp(-30*t)
    return _mp(y,vel)

# ============================================================ A1b / A2b (boosted)
def A1b():
    s=m2.A1_monkeyflute()
    s.name="A1b_MonkeyFlute"
    return s

def A2b():
    s=m2.A2_monkeyalt()
    s.name="A2b_MonkeyAlt"
    return s

# ============================================================ B1f / B2f (funny layer added)
def add_funny_layer(s, style="glock"):
    """Dark/lo-fi vibe rakho, par comedy accents add karo:
       glockenspiel doubling, woodblock ticks, tuba staccato, slide whistle gliss,
       wah-trumpet 'sad trombone' after phrase, stop-time bar."""
    spb=s.spb
    # 1) glockenspiel/sparkle doubling on melody-ish notes every 2 bars
    for b in range(0, s.bars, 2):
        for st in (0, 6, 10):
            nt = ['Ab4','F4','Db5','Bb4','Ab4'][b % 5]
            if style=="glock":
                s.add('lead', glock(hz(nt)*2, 0.8, vel=0.13), s.T(b,st), 1.0, human=0.004)
            else:
                s.add('lead', kazoo(hz(nt), 0.22, vel=0.10), s.T(b,st), 1.0, human=0.004)
    # 2) woodblock "tiptoe" ticks on offbeats
    for b in range(s.bars):
        for st in (3, 11):
            s.add('drums', woodblock(f=980, dur=0.06, vel=0.11), s.T(b,st), 1.0, human=0.003)
    # 3) tuba staccato pickup at phrase ends (bar 2 and 4)
    for b in (1, 3):
        if b < s.bars:
            s.add('bass', tuba(hz('Db2'), 0.22, vel=0.30), s.T(b,12), 1.0, human=0.004)
            s.add('bass', tuba(hz('Ab2'), 0.18, vel=0.24), s.T(b,14), 1.0, human=0.004)
    # 4) slide whistle glide down at end of bar 3 (comic fall cue)
    if s.bars > 3:
        s.add('fx', slide_whistle(hz('Eb6'), hz('Eb4'), 0.55, vel=0.13), s.T(3,10), 1.0, human=0.002)
    # 5) "sad trombone" wah-wah-wah after a phrase (bar 5)
    if s.bars > 5:
        for i,(nt,dv) in enumerate([('Bb3',0.20),('A3',0.20),('Ab3',0.34)]):
            s.add('harm', wah_trumpet(hz(nt), dv, vel=0.16, wah=6.0), s.T(5, 12+i*2), 1.0, human=0.004)
    # 6) stop-time: bar 6 only ticks + glock (space for the joke)
    if s.bars > 6:
        for st in (0,4,8,12):
            s.add('drums', woodblock(f=1200, dur=0.05, vel=0.16), s.T(6,st), 1.0, human=0.002)
        s.add('harm', glock(hz('Db5'),0.9,vel=0.18), s.T(6,0),1.0, human=0.002)
    # 7) ba-da-ba-tsss fill at very end
    b=s.bars-1
    s.add('drums', snare(vel=0.55), s.T(b,8),1.0)
    s.add('drums', snare(vel=0.65), s.T(b,10),1.0)
    s.add('drums', snare(vel=0.75), s.T(b,12),1.0)
    s.add('drums', snare(vel=0.85), s.T(b,14),1.0)
    s.add('fx', ratchet(0.30, vel=0.16), s.T(b,6),1.0)
    return s

def B1f():
    s=m2.B1_nightharmonium(); add_funny_layer(s,"glock"); s.name="B1f_NightHarmonium_Fun"; return s
def B2f():
    s=m2.B2_nightrhodes(); add_funny_layer(s,"kazoo"); s.name="B2f_NightRhodes_Fun"; return s

# ============================================================ C1 / C2 — comedy
CH=['C','Am','F','G']
CHORD_NOTES={'C':['C3','E3','G3'],'Am':['A2','C3','E3'],'F':['F2','A2','C3'],'G':['G2','B2','D3']}
# jumpy dotted-rhythm tune, 4-bar phrase, C major
TUNE=[[('G4',0,3),('E4',3,1),('G4',4,2),('A4',6,2),('G4',8,3),('E4',11,1),('C5',12,4)],
      [('A4',0,2),('G4',2,2),('E4',4,3),('D4',7,1),('C4',8,4),('E4',12,2),('G4',14,2)],
      [('A4',0,3),('C5',3,1),('A4',4,2),('F4',6,2),('A4',8,3),('C5',11,1),('F5',12,4)],
      [('G4',0,2),('B4',2,2),('D5',4,3),('B4',7,1),('G4',8,4),('F4',12,2),('D4',14,2)]]

def _comedy_backbone(s, bars, tuba_vel=0.55, chord_bus='harm', chord_inst='pizz', space_bars=()):
    """oom-pah: root on 1&3, fifth on 2&4 (staccato) — research ka #1 funny recipe"""
    for b in range(bars):
        c=CH[b%4]; notes=CHORD_NOTES[c]
        root=notes[0]; fifth=notes[2]
        if b in space_bars:
            continue
        # tuba/bass staccato oom-pah
        s.add('bass', tuba(hz(root)/2, 0.26, vel=tuba_vel), s.T(b,0),1.0, human=0.004)
        s.add('bass', tuba(hz(fifth)/2, 0.20, vel=tuba_vel*0.8), s.T(b,4),1.0, human=0.004)
        s.add('bass', tuba(hz(root)/2, 0.24, vel=tuba_vel*0.9), s.T(b,8),1.0, human=0.004)
        s.add('bass', tuba(hz(fifth)/2, 0.18, vel=tuba_vel*0.75), s.T(b,12),1.0, human=0.004)
        # chord stabs on 2 and 4 (classic "chop")
        for st in (4,12):
            for nt in notes[1:]:
                if chord_inst=='pizz':
                    s.add(chord_bus, pizz(hz(nt),0.14,vel=0.26), s.T(b,st),1.0, human=0.003)
                else:
                    s.add(chord_bus, accordion([hz(nt)], 0.18, vel=0.16), s.T(b,st),1.0, human=0.003)

def C1_comedy_classic():
    """Approach 1: research wala asli comedy palette —
       pizzicato strings + bassoon + tuba + glockenspiel + clarinet + woodblock + slide whistle."""
    s=Song(132, 8, "C1_ComedyClassic", swing=0.09)
    _comedy_backbone(s, 8, tuba_vel=0.60)
    for b in range(8):
        tune=TUNE[b%4]
        # melody: pizz violin + glockenspiel doubling an octave up (mallets double = cartoon)
        for nt,st,dur in tune:
            v=0.55 if st in (0,8) else 0.42
            s.add('lead', pizz(hz(nt), max(0.12,dur*s.spb*0.7), vel=v), s.T(b,st),1.0, human=0.003)
            s.add('lead', glock(hz(nt)*2, max(0.25,dur*s.spb*1.2), vel=0.16), s.T(b,st),1.0, human=0.003)
        # bassoon staccato counter-line (clown) on offbeats
        if b>=2:
            for st in (2,6,10,14):
                nt=CHORD_NOTES[CH[b%4]][1]
                s.add('harm', bassoon(hz(nt)/2, 0.13, vel=0.24), s.T(b,st),1.0, human=0.004)
        # clarinet takes melody an octave up in second half (melody bounces between instruments)
        if b>=4:
            for nt,st,dur in tune:
                s.add('harm', clarinet(hz(nt)*2, max(0.12,dur*s.spb*0.6), vel=0.16), s.T(b,st),1.0, human=0.004)
        # drums: light kick + woodblock + shaker
        s.add('drums', kick(vel=0.45, dur=0.20), s.T(b,0),1.0)
        s.add('drums', kick(vel=0.32, dur=0.18), s.T(b,8),1.0)
        s.add('drums', woodblock(f=1150, vel=0.20), s.T(b,4),1.0, human=0.003)
        s.add('drums', woodblock(f=1000, vel=0.18), s.T(b,12),1.0, human=0.003)
        for k in range(0,16,2):
            s.add('drums', shaker(vel=0.18 if k%4 else 0.24), s.T(b,k),1.0, human=0.004)
    # STOP-TIME bar 3: sab band, sirf ticks (joke ke liye jagah)
    for st in (0,4,8,12):
        s.add('drums', woodblock(f=1250, vel=0.22), s.T(3,st),1.0, human=0.002)
    s.add('harm', glock(hz('C5'),0.7,vel=0.20), s.T(3,0),1.0)
    # slide whistle drop at end of bar 5 (fall cue)
    s.add('fx', slide_whistle(hz('C6'), hz('C4'), 0.6, vel=0.16), s.T(5,8),1.0, human=0.002)
    # ba-da-ba-tsss + ratchet at end
    for i,st in enumerate((8,10,12,14)):
        s.add('drums', snare(vel=0.5+0.1*i), s.T(7,st),1.0)
    s.add('drums', snare(vel=0.95), s.T(7,15),1.0)
    s.add('fx', ratchet(0.30, vel=0.18), s.T(7,6),1.0)
    s.add('drums', timpani(hz('C2'),0.5,vel=0.35), s.T(7,0),1.0)
    return s

def C2_comedy_toyband():
    """Approach 2: SAME tune + chords, naya combo — kazoo lead + accordion oom-pah +
       banjo comping + whistle double + ratchet/woodblock."""
    s=Song(132, 8, "C2_ComedyToyBand", swing=0.09)
    _comedy_backbone(s, 8, tuba_vel=0.34, chord_inst='acc')
    for b in range(8):
        tune=TUNE[b%4]
        for nt,st,dur in tune:
            v=0.52 if st in (0,8) else 0.40
            # kazoo lead + banjo doubling (toy-band colour)
            s.add('lead', kazoo(hz(nt), max(0.14,dur*s.spb*0.75), vel=v), s.T(b,st),1.0, human=0.003)
            s.add('lead', banjo(hz(nt)/2, max(0.16,dur*s.spb*0.8), vel=0.20), s.T(b,st),1.0, human=0.003)
        # accordion "chop" on 2 & 4 (already in backbone) + accordion pump on 16ths in 2nd half
        if b>=4:
            for st in (2,6,10,14):
                s.add('harm', accordion([hz(x) for x in CHORD_NOTES[CH[b%4]][1:]], 0.10, vel=0.10), s.T(b,st),1.0, human=0.004)
        # whistle double on the hook (octave up, thin)
        if b in (1,3,5,7):
            for nt,st,dur in tune[:3]:
                s.add('harm', slide_whistle(hz(nt)*2, hz(nt)*2*1.02, 0.12, vel=0.10), s.T(b,st),1.0, human=0.004)
        # percussion: woodblock tiptoe + ratchet + kick
        s.add('drums', kick(vel=0.40, dur=0.20), s.T(b,0),1.0)
        s.add('drums', kick(vel=0.30, dur=0.18), s.T(b,10),1.0)
        for st in (3,7,11,15):
            s.add('drums', woodblock(f=1400, vel=0.16), s.T(b,st),1.0, human=0.003)
        if b%2==1:
            s.add('fx', ratchet(0.16, vel=0.10), s.T(b,14),1.0)
    # STOP-TIME bar 6
    for st in (0,4,8,12):
        s.add('drums', woodblock(f=1500, vel=0.20), s.T(6,st),1.0, human=0.002)
    s.add('harm', glock(hz('G5'),0.6,vel=0.16), s.T(6,0),1.0)
    # slide whistle fall + fill
    s.add('fx', slide_whistle(hz('E6'), hz('E4'), 0.55, vel=0.14), s.T(4,10),1.0, human=0.002)
    for i,st in enumerate((8,10,12,14)):
        s.add('drums', snare(vel=0.45+0.1*i), s.T(7,st),1.0)
    s.add('fx', ratchet(0.34, vel=0.16), s.T(7,4),1.0)
    return s

# ============================================================ run
if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/orig3",exist_ok=True)
    GA={'A1b':{'lead':1.32,'harm':0.50,'bass':1.18,'drums':0.80,'fx':0.25},
        'A2b':{'lead':1.30,'harm':0.48,'bass':1.12,'drums':0.78,'fx':0.25},
        'B1f':{'lead':1.05,'harm':0.62,'bass':0.92,'drums':0.82,'fx':0.55},
        'B2f':{'lead':1.05,'harm':0.62,'bass':0.90,'drums':0.82,'fx':0.55},
        'C1': {'lead':1.00,'harm':0.78,'bass':1.00,'drums':0.90,'fx':0.55},
        'C2': {'lead':1.00,'harm':0.78,'bass':1.00,'drums':0.90,'fx':0.55}}
    jobs=[(A1b,'A1b'),(A2b,'A2b'),(B1f,'B1f'),(B2f,'B2f'),(C1_comedy_classic,'C1'),(C2_comedy_toyband,'C2')]
    for fn,key in jobs:
        s=fn()
        p=f"/home/user/audio_preview/orig3/{s.name}.wav"
        m2.master(s,p,gains=GA[key]); print("OK",p,round(s.dur,1),"s")
