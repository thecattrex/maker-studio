"""
musicgen9.py — 5 options, HAR EK KA ALAG RHYTHM/GROOVE, ~32s (lamba video bhi set ho).
No drum kit, no bells. Instruments: sax, trumpet, french horn, mouth organ
(+ tuba, bassoon, pizz, accordion, woodblock, ratchet).
"""
import numpy as np, os, importlib.util, wave

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

m2 = _load("m2", "/home/user/studio/musicgen2.py")
m3 = _load("m3", "/home/user/studio/musicgen3.py")
m7 = _load("m7", "/home/user/studio/musicgen7.py")
SR = m2.SR; Song = m2.Song; hz = m2.hz
tuba = m3.tuba; bassoon = m3.bassoon; pizz = m2.pizz
accordion = m3.accordion; woodblock = m2.woodblock; ratchet = m3.ratchet
sax = m7.sax; trumpet = m7.trumpet; french_horn = m7.french_horn; mouthorgan = m7.mouthorgan

OUT = "/home/user/audio_preview/brass2"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
def seg(s, b, steps, notes, inst, bus, vel, dur=None, octave=1):
    for st, nt, d in notes:
        f = hz(nt) * octave
        s.add(bus, inst(f, dur if dur else d, vel=vel), s.T(b, st), 1.0, human=0.002)

# ================================================================= O1 SWING
def O1():
    """124 bpm, triplet SWING. E major. I-vi-IV-V."""
    CH = [(['E2'], ['E3', 'G#3', 'B3']), (['C#2'], ['C#3', 'E3', 'G#3']),
          (['A1'], ['A2', 'C#3', 'E3']), (['B1'], ['B2', 'D#3', 'F#3'])]
    P1 = [(0, 'E4', .13), (2, 'G#4', .12), (3, 'A4', .10), (6, 'B4', .26),
          (8, 'A4', .12), (10, 'G#4', .12), (11, 'F#4', .10), (14, 'E4', .30)]
    P2 = [(0, 'B4', .13), (2, 'C#5', .12), (3, 'B4', .10), (6, 'G#4', .26),
          (8, 'F#4', .12), (10, 'E4', .12), (11, 'F#4', .10), (13, 'G#4', .20)]
    s = Song(124, 16, "O1_Swing", swing=0.30)     # heavy triplet shuffle
    for b in range(16):
        lo, ch = CH[b % 4]
        line = P1 if b < 8 else P2
        if b >= 2:
            seg(s, b, None, line, sax, 'lead', 0.62)
        for st in (0, 8, 14):
            s.add('bass', tuba(hz(lo[0]), 0.12, vel=0.62), s.T(b, st), 1.0, human=0.002)
        for st in (4, 12):                      # brushes of harmony on the "and"
            for nt in ch:
                s.add('harm', pizz(hz(nt), 0.16, vel=0.30), s.T(b, st), 1.0, human=0.004)
        s.add('harm', french_horn(hz(ch[0]) * 2, s.bar * 0.9, vel=0.15), s.T(b, 0), 1.0)
        if b % 4 == 3:
            for st in (13, 15):
                s.add('fx', woodblock(980, 0.05, vel=0.20), s.T(b, st), 1.0)
    s.add('lead', sax(hz('E5'), 1.1, vel=0.5), s.T(15, 8), 1.0)
    return m2.master(s, f"{OUT}/O1_Swing.wav",
                     gains={'lead': 1.05, 'harm': 0.55, 'bass': 0.95, 'drums': 0.0, 'fx': 0.3},
                     wet={'lead': 0.26, 'harm': 0.30, 'bass': 0.05, 'drums': 0.0, 'fx': 0.3})

# ============================================================== O2 STRAIGHT 16
def O2():
    """112 bpm, straight 16th funk, no swing. C# minor. i-VI-III-VII."""
    CH = [(['C#2'], ['C#3', 'E3', 'G#3']), (['A1'], ['A2', 'C#3', 'E3']),
          (['E2'], ['E3', 'G#3', 'B3']), (['B1'], ['B2', 'D#3', 'F#3'])]
    P1 = [(3, 'C#5', .09), (6, 'B4', .09), (7, 'A4', .09), (10, 'G#4', .22),
          (13, 'A4', .09), (14, 'B4', .09), (15, 'C#5', .16)]
    P2 = [(2, 'E5', .09), (3, 'D#5', .09), (6, 'C#5', .09), (9, 'B4', .22),
          (12, 'A4', .09), (13, 'G#4', .09), (14, 'A4', .12), (15, 'B4', .20)]
    s = Song(112, 16, "O2_Straight16", swing=0.0)
    for b in range(16):
        lo, ch = CH[b % 4]
        if b >= 2:
            seg(s, b, None, P1 if b < 9 else P2, mouthorgan, 'lead', 0.55)
        # 16th-note tuba ostinato with rests (funk feel)
        for st in (0, 3, 6, 7, 10, 12, 14, 15):
            s.add('bass', tuba(hz(lo[0]), 0.09, vel=0.58), s.T(b, st), 1.0, human=0.002)
        # clav-ish pizz stabs on the off-16ths
        for st in (2, 5, 9, 11, 13):
            s.add('harm', pizz(hz(ch[(st // 2) % 3]), 0.08, vel=0.26), s.T(b, st), 1.0, human=0.003)
        if b % 2 == 1:
            s.add('harm', trumpet(hz(ch[0]) * 2, 0.09, vel=0.30), s.T(b, 15), 1.0)
        for st in (4, 12):
            s.add('fx', ratchet(0.16, vel=0.14), s.T(b, st), 1.0)
    s.add('lead', mouthorgan(hz('C#5'), 0.9, vel=0.5), s.T(15, 8), 1.0)
    return m2.master(s, f"{OUT}/O2_Straight16.wav",
                     gains={'lead': 1.0, 'harm': 0.62, 'bass': 0.92, 'drums': 0.0, 'fx': 0.3},
                     wet={'lead': 0.24, 'harm': 0.28, 'bass': 0.05, 'drums': 0.0, 'fx': 0.3})

# ================================================================ O3 HALF-TIME
def O3():
    """84 bpm HALF-TIME (laid back). A major. IV-I-V-vi. Long tones."""
    CH = [(['A1'], ['A2', 'C#3', 'E3']), (['E2'], ['E3', 'G#3', 'B3']),
          (['B1'], ['B2', 'D#3', 'F#3']), (['C#2'], ['C#3', 'E3', 'G#3'])]
    P1 = [(0, 'E4', .8), (6, 'A4', .4), (10, 'C#5', .8)]
    P2 = [(0, 'B4', .8), (6, 'A4', .4), (10, 'G#4', .7), (14, 'F#4', .4)]
    s = Song(84, 12, "O3_HalfTime", swing=0.10)
    for b in range(12):
        lo, ch = CH[b % 4]
        if b >= 2:
            seg(s, b, None, P1 if b < 7 else P2, french_horn, 'lead', 0.55, octave=1)
        s.add('bass', tuba(hz(lo[0]), 0.55, vel=0.55), s.T(b, 0), 1.0)
        s.add('bass', tuba(hz(lo[0]) * 1.5, 0.30, vel=0.40), s.T(b, 10), 1.0)
        for nt in ch:                       # warm sustained pad
            s.add('harm', accordion([hz(nt)], s.bar * 0.95, vel=0.20), s.T(b, 0), 1.0)
        if b >= 2:                          # sax answer, sparse
            s.add('harm', sax(hz(ch[2]) * 2, 0.45, vel=0.30), s.T(b, 8), 1.0)
        s.add('fx', woodblock(640, 0.07, vel=0.22), s.T(b, 8), 1.0)
    s.add('lead', french_horn(hz('A4'), 1.6, vel=0.45), s.T(11, 8), 1.0)
    return m2.master(s, f"{OUT}/O3_HalfTime.wav",
                     gains={'lead': 1.0, 'harm': 0.66, 'bass': 0.95, 'drums': 0.0, 'fx': 0.28},
                     wet={'lead': 0.30, 'harm': 0.34, 'bass': 0.06, 'drums': 0.0, 'fx': 0.3})

# =================================================================== O4 MARCH
def O4():
    """116 bpm OOM-PAH 2-step march. E major. I-IV-I-V."""
    CH = [(['E2'], ['E3', 'G#3', 'B3']), (['A1'], ['A2', 'C#3', 'E3']),
          (['E2'], ['E3', 'G#3', 'B3']), (['B1'], ['B2', 'D#3', 'F#3'])]
    P1 = [(0, 'E4', .16), (2, 'E4', .16), (4, 'B4', .16), (6, 'G#4', .16),
          (8, 'F#4', .16), (10, 'G#4', .16), (12, 'A4', .30)]
    P2 = [(0, 'B4', .16), (2, 'B4', .16), (4, 'C#5', .16), (6, 'B4', .16),
          (8, 'A4', .16), (10, 'G#4', .16), (12, 'F#4', .20), (14, 'E4', .20)]
    s = Song(116, 16, "O4_March", swing=0.0)
    for b in range(16):
        lo, ch = CH[b % 4]
        if b >= 2:
            seg(s, b, None, P1 if b < 9 else P2, trumpet, 'lead', 0.55)
        s.add('bass', tuba(hz(lo[0]), 0.30, vel=0.62), s.T(b, 0), 1.0)   # oom
        s.add('bass', tuba(hz(lo[0]) * 1.5, 0.20, vel=0.45), s.T(b, 8), 1.0)
        for st in (4, 12):                                               # pah
            s.add('harm', accordion([hz(n) for n in ch], 0.13, vel=0.28), s.T(b, st), 1.0)
        s.add('harm', mouthorgan(hz(ch[0]), 0.12, vel=0.18), s.T(b, 14), 1.0)
        for st in (6, 14):
            s.add('fx', woodblock(1150, 0.05, vel=0.20), s.T(b, st), 1.0)
    s.add('lead', trumpet(hz('E5'), 0.9, vel=0.5), s.T(15, 8), 1.0)
    return m2.master(s, f"{OUT}/O4_March.wav",
                     gains={'lead': 1.0, 'harm': 0.62, 'bass': 0.95, 'drums': 0.0, 'fx': 0.28},
                     wet={'lead': 0.24, 'harm': 0.30, 'bass': 0.05, 'drums': 0.0, 'fx': 0.3})

# =================================================================== O5 CLAVE
def O5():
    """100 bpm 3-2 son clave groove. F# minor. ii-V-i-vi."""
    CH = [(['F#2'], ['F#3', 'A3', 'C#4']), (['B1'], ['B2', 'D#3', 'F#3']),
          (['E2'], ['E3', 'G#3', 'B3']), (['C#2'], ['C#3', 'E3', 'G#3'])]
    CLAVE = [0, 3, 6, 10, 12]
    P1 = [(0, 'F#4', .18), (3, 'A4', .14), (6, 'C#5', .30), (10, 'B4', .14), (12, 'A4', .30)]
    P2 = [(0, 'C#5', .18), (3, 'B4', .14), (6, 'G#4', .30), (10, 'A4', .14), (12, 'F#4', .30)]
    s = Song(100, 14, "O5_Clave", swing=0.0)
    for b in range(14):
        lo, ch = CH[b % 4]
        if b >= 2:
            seg(s, b, None, P1 if b < 8 else P2, sax, 'lead', 0.58)
        for st in (0, 6, 8, 12):                              # tumbao bass
            s.add('bass', tuba(hz(lo[0]), 0.16, vel=0.60), s.T(b, st), 1.0, human=0.002)
        for st in (2, 5, 7, 11, 14):                          # montuno
            for nt in ch:
                s.add('harm', pizz(hz(nt), 0.09, vel=0.24), s.T(b, st), 1.0, human=0.004)
        for st in CLAVE:                                      # clave stick
            s.add('fx', woodblock(1320, 0.055, vel=0.32), s.T(b, st), 1.0, human=0.001)
        s.add('harm', french_horn(hz(ch[0]) * 2, 0.35, vel=0.18), s.T(b, 8), 1.0)
        if b % 4 == 3:
            s.add('harm', trumpet(hz(ch[1]) * 2, 0.12, vel=0.32), s.T(b, 14), 1.0)
    s.add('lead', sax(hz('F#4'), 1.4, vel=0.5), s.T(13, 8), 1.0)
    return m2.master(s, f"{OUT}/O5_Clave.wav",
                     gains={'lead': 1.0, 'harm': 0.60, 'bass': 0.95, 'drums': 0.0, 'fx': 0.34},
                     wet={'lead': 0.26, 'harm': 0.30, 'bass': 0.05, 'drums': 0.0, 'fx': 0.30})

if __name__ == "__main__":
    for fn in (O1, O2, O3, O4, O5):
        p = fn(); w = wave.open(p)
        print(f"{os.path.basename(p):22s} {w.getnframes()/w.getframerate():5.2f}s")
