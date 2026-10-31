"""
musicgen6.py — TUTU motif but using C1 / C2 funny palettes, WITHOUT any drums.

C1 palette: pizzicato strings + glockenspiel + bassoon + tuba + clarinet + slide whistle
C2 palette: kazoo + banjo + accordion + slide whistle + ratchet
No kick, no snare, no hat, no shaker. Sirf melodic/plucked/reed instruments.
"""
import numpy as np, os, importlib.util

spec=importlib.util.spec_from_file_location("m3","/home/user/studio/musicgen3.py")
m3=importlib.util.module_from_spec(spec); spec.loader.exec_module(m3)
m2=m3.m2
SR=m2.SR; Song=m2.Song; hz=m2.hz; ns=m2.ns; _mp=m2._mp; rng=m2.rng
pizz=m2.pizz; clarinet=m3.clarinet; bassoon=m3.bassoon; tuba=m3.tuba
glock=m3.glock; kazoo=m3.kazoo; accordion=m3.accordion; banjo=m3.banjo
slide=m3.slide_whistle; woodblock=m3.woodblock; ratchet=m3.ratchet

# "tu-tu | tu-tu-tu-tu | tu-tu | tu-tu-tu-tu-tu"
MOTIF=[(0,0.95),(2,0.70),
       (4,0.85),(5,0.80),(6,0.88),(7,0.95),
       (10,0.75),(12,0.90),
       (13,0.82),(14,0.88),(15,1.00)]

# 4-bar loop, A minor-ish (funny but not christmas)
ROOTS=['A2','G2','F2','E2']
LEAD =['A4','G4','F4','E4']
ALT  =['E5','D5','C5','B4']

def T4_tutu_c1():
    """C1 palette, no drums."""
    s=Song(138,8,"T4_TutuC1",swing=0.07)
    for b in range(8):
        r=ROOTS[b%4]; ld=LEAD[b%4]; al=ALT[b%4]
        # tuba: staccato notes on the motif (acts as bass groove, not a drum)
        for step,v in [(0,0.85),(4,0.60),(8,0.70),(12,0.62)]:
            s.add('bass', tuba(hz(r)/2, 0.20, vel=0.50*v), s.T(b,step),1.0, human=0.003)
            s.add('bass', tuba(hz(r)/2, 0.16, vel=0.34*v), s.T(b,step+2),1.0, human=0.003)
        # TUTU lead: pizz strings + glock octave double
        for step,v in MOTIF:
            nt = al if (b%2==1 and step>=10) else ld
            s.add('lead', pizz(hz(nt), 0.13, vel=0.60*v), s.T(b,step),1.0, human=0.002)
            s.add('lead', glock(hz(nt)*2, 0.22, vel=0.10*v), s.T(b,step),1.0, human=0.002)
        # bassoon staccato ostinato in the gaps (clown counterpoint)
        if b>=2:
            for step in (1,3,5,9,11):
                s.add('harm', bassoon(hz(r)*2, 0.085, vel=0.20), s.T(b,step),1.0, human=0.003)
        # clarinet answers the motif an octave up in 2nd half
        if b>=4:
            for step,v in MOTIF[-4:]:
                s.add('harm', clarinet(hz(ld)*2, 0.09, vel=0.16*v), s.T(b,step),1.0, human=0.003)
        # woodblock ticks (instrument, not drum kit)
        for step in (7,15):
            s.add('harm', woodblock(f=1250, dur=0.05, vel=0.13), s.T(b,step),1.0, human=0.002)
    # slide whistle glide as an accent, no drums
    s.add('fx', slide(hz('A5'), hz('A4'), 0.45, vel=0.12), s.T(5,12),1.0, human=0.002)
    return s

def T5_tutu_c2():
    """C2 toy-band palette, no drums."""
    s=Song(138,8,"T5_TutuC2",swing=0.07)
    for b in range(8):
        r=ROOTS[b%4]; ld=LEAD[b%4]; al=ALT[b%4]
        # accordion pump on the motif = the "groove", no drums
        for step,v in MOTIF:
            s.add('harm', accordion([hz(r),hz(r)*1.5], 0.075, vel=0.17*v), s.T(b,step),1.0, human=0.003)
        # TUTU lead: kazoo + banjo octave below
        for step,v in MOTIF:
            nt = al if (b%2==1 and step>=10) else ld
            s.add('lead', kazoo(hz(nt), 0.13, vel=0.50*v), s.T(b,step),1.0, human=0.002)
            s.add('lead', banjo(hz(nt)/2, 0.16, vel=0.20*v), s.T(b,step),1.0, human=0.002)
        # tuba only on downbeats (quiet anchor)
        s.add('bass', tuba(hz(r)/2, 0.26, vel=0.34), s.T(b,0),1.0, human=0.003)
        s.add('bass', tuba(hz(r)/2, 0.22, vel=0.26), s.T(b,8),1.0, human=0.003)
        # ratchet accent (toy, not drum kit)
        if b%2==1:
            s.add('fx', ratchet(0.10, vel=0.10), s.T(b,14),1.0)
        # whistle chirps
        if b in (3,7):
            s.add('fx', slide(hz('E6'), hz('G6'), 0.12, vel=0.09), s.T(b,6),1.0, human=0.002)
    return s

if __name__=="__main__":
    os.makedirs("/home/user/audio_preview/tutu",exist_ok=True)
    G={'lead':1.20,'harm':0.60,'bass':0.80,'drums':0.0,'fx':0.55}
    for fn in (T4_tutu_c1,T5_tutu_c2):
        s=fn(); p=f"/home/user/audio_preview/tutu/{s.name}.wav"
        m2.master(s,p,gains=G); print("OK",p,round(s.dur,1),"s")
