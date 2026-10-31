"""
musicgen4.py — B1fl / B2fl : harmonium ki jagah FLUTE main instrument.
C1 / C2 waisa hi rakha (final picks).

Approach: same chords (Db major) + same melody, sirf lead/bed instrument flute.
  • flute chord bed = sustained low breathy flute (harmonium ka replacement)
  • flute melody (lead) + vibes/glock double
  • upright bass, brushed kit, out-of-tune piano echo, funny layer (same as B1f/B2f)
"""
import numpy as np, os, importlib.util
from scipy.signal import butter, sosfilt

spec=importlib.util.spec_from_file_location("m3","/home/user/studio/musicgen3.py")
m3=importlib.util.module_from_spec(spec); spec.loader.exec_module(m3)
m2=m3.m2
SR=m2.SR; Song=m2.Song; hz=m2.hz; ns=m2.ns; _mp=m2._mp; rng=m2.rng
flute=m2.flute; piano_off=m2.piano_off; vibes=m2.vibes; ubass=m2.ubass
kick=m2.kick; brush=m2.brush; hat=m2.hat; rhodes=m2.rhodes
glock=m3.glock; woodblock=m3.woodblock; add_funny_layer=m3.add_funny_layer

PROG=[['Db3','F3','Ab3','C4'],
      ['Ab2','C3','Eb3','Gb3'],
      ['Db3','F3','Ab3','C4'],
      ['Gb2','Bb2','Db3','F3'],
      ['Db3','F3','Ab3','C4']]

MEL=[('Ab4',0,3),('Gb4',6,2),('F4',9,3),('Eb4',13,3),
     ('C4',0,3),('Eb4',4,2),('Gb4',7,3),('Ab4',12,4),
     ('F4',0,2),('Ab4',3,2),('C5',6,3),('Ab4',10,3),('F4',14,2),
     ('Db4',0,3),('F4',4,3),('Bb4',8,3),('Ab4',12,2),
     ('Db4',0,4),('Ab3',6,3),('F3',10,4)]

def flute_bed(f, dur, vel=1.0):
    """sustained airy low flute — harmonium ki jagah chord bed.
       Do slightly detuned flute layers + slow breath swell = 'organ-ish' par flute timbre."""
    n=ns(dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for det,g in [(1.0,1.0),(1.0022,0.55),(0.9978,0.5)]:
        vib=0.0032*np.sin(2*np.pi*(4.4+0.3*det)*t+rng.uniform(0,6.28))
        ph=2*np.pi*np.cumsum(f*det*(1+vib))/SR
        y+=g*(np.sin(ph)+0.16*np.sin(2*ph)+0.05*np.sin(3*ph))
    br=sosfilt(butter(2,[700,4200],'band',fs=SR,output='sos'),rng.normal(0,1,n))
    y=y+br*0.10
    # slow swell in/out (breath)
    e=np.minimum(1,t/0.55)*np.minimum(1,(dur-t)/0.9)
    e*=0.75+0.25*np.sin(2*np.pi*0.28*t-1.2)
    return _mp(y*e,vel)

def B1fl():
    s=Song(61, 5, "B1fl_NightFlute", swing=0.03)
    for b in range(5):
        c=PROG[b]
        # flute chord bed (harmonium replacement) — low register, sustained
        for k,nt in enumerate(c):
            s.add('harm', flute_bed(hz(nt), s.bar*0.98, vel=0.30-0.03*k), s.T(b,0)+k*0.02, 1.0, human=0.004)
        # out-of-tune piano echo (QKThr detail) — comes and goes
        if b in (1,3,4):
            for k,nt in enumerate(c[1:]):
                s.add('lead', piano_off(hz(nt)*2, 2.2, vel=0.13+0.03*k, detune=0.006), s.T(b,4+k*3),1.0, human=0.012)
        # MAIN: flute melody (long phrases)
        if b in (0,2,4):
            for nt,st,dur in MEL:
                if b==0 and st>10: continue
                if b==2 and st<3: continue
                if b==4 and 2<st<10: continue
                s.add('lead', flute(hz(nt), dur*s.spb*0.95, vel=0.62, breath=0.06), s.T(b,st),1.0, human=0.006)
                s.add('lead', vibes(hz(nt)*2, dur*s.spb*0.9, vel=0.09), s.T(b,st)+0.006,1.0, human=0.008)
        # upright bass
        s.add('bass', ubass(hz(c[0])/2, 1.5, vel=0.85), s.T(b,0),1.0, human=0.006)
        if b%2: s.add('bass', ubass(hz(c[1])/2, 0.9, vel=0.42), s.T(b,10),0.8, human=0.008)
        # brushed kit
        if b>=1:
            s.add('drums', kick(vel=0.42,dur=0.40), s.T(b,0),1.0)
            s.add('drums', brush(vel=0.24), s.T(b,6),1.0)
            s.add('drums', brush(vel=0.26), s.T(b,12),1.0)
            if b%2==0: s.add('drums', kick(vel=0.26,dur=0.40), s.T(b,10),1.0)
        for k in (4,12):
            s.add('drums', hat(vel=0.10), s.T(b,k),1.0,human=0.006)
    # room hiss
    hiss=sosfilt(butter(2,[400,5000],'band',fs=SR,output='sos'),rng.normal(0,1,s.n))*0.006
    s.bus['fx']+=hiss
    add_funny_layer(s,"glock")
    return s

def B2fl():
    s=Song(66, 5, "B2fl_NightFlute_Alt", swing=0.04)
    for b in range(5):
        c=PROG[b]
        # flute bed (thinner, different voicing than B1fl)
        if b>=1:
            for k,nt in enumerate(c):
                s.add('harm', flute_bed(hz(nt), s.bar*0.70, vel=0.24-0.02*k), s.T(b,0)+k*0.03, 1.0, human=0.006)
        # vibes arpeggio shimmer
        if b>=2:
            for st in (2,6,10,14):
                s.add('harm', vibes(hz(c[(st//2)%4])*2, 0.9, vel=0.15), s.T(b,st),1.0,human=0.006)
        # MAIN: flute melody + glock octave sparkle (cartoon double, softer)
        if b in (0,2,4):
            for nt,st,dur in MEL:
                if b==0 and st>10: continue
                if b==2 and st<3: continue
                if b==4 and 2<st<10: continue
                s.add('lead', flute(hz(nt), dur*s.spb*0.9, vel=0.58, breath=0.075), s.T(b,st),1.0, human=0.006)
                s.add('lead', glock(hz(nt)*2, dur*s.spb*1.1, vel=0.11), s.T(b,st)+0.004,1.0, human=0.006)
        # upright bass
        s.add('bass', ubass(hz(c[0])/2, 1.6, vel=0.88), s.T(b,0),1.0, human=0.006)
        if b%2==0: s.add('bass', ubass(hz(c[2])/2, 0.7, vel=0.38), s.T(b,12),0.75, human=0.01)
        # brush kit
        if b>=1:
            s.add('drums', kick(vel=0.40,dur=0.38), s.T(b,0),1.0)
            s.add('drums', brush(vel=0.26), s.T(b,6),1.0)
            s.add('drums', brush(vel=0.28), s.T(b,12),1.0)
        for k in (4,10,14):
            s.add('drums', hat(vel=0.09), s.T(b,k),1.0,human=0.007)
    add_funny_layer(s,"kazoo")
    return s

if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/final",exist_ok=True)
    GA={'B1fl':{'lead':1.10,'harm':0.72,'bass':0.92,'drums':0.80,'fx':0.50},
        'B2fl':{'lead':1.10,'harm':0.70,'bass':0.90,'drums':0.80,'fx':0.50}}
    for fn,key in [(B1fl,'B1fl'),(B2fl,'B2fl')]:
        s=fn(); p=f"/home/user/audio_preview/final/{s.name}.wav"
        m2.master(s,p,gains=GA[key]); print("OK",p,round(s.dur,1),"s")
