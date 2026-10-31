"""
musicgen8.py — 5 options, "brass/reed street-funk" vibe (ref: 124 BPM fails-reel bed).
Palette: sax, trumpet, french horn, mouth organ (+ tuba, bassoon, pizz, accordion, woodblock, ratchet).
NO DRUM KIT, no bells/glock.
"""
import numpy as np, os, importlib.util

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

m2 = _load("m2", "/home/user/studio/musicgen2.py")
m3 = _load("m3", "/home/user/studio/musicgen3.py")
m7 = _load("m7", "/home/user/studio/musicgen7.py")
SR = m2.SR; Song = m2.Song; hz = m2.hz; ns = m2.ns
tuba = m3.tuba; bassoon = m3.bassoon; pizz = m2.pizz
accordion = m3.accordion; woodblock = m2.woodblock; ratchet = m3.ratchet
sax = m7.sax; trumpet = m7.trumpet; french_horn = m7.french_horn; mouthorgan = m7.mouthorgan

BPM = 124
BARS = 8
# E major: I - vi - IV - V, 1 bar each
PROG = [
    (['E2'], ['E3', 'G#3', 'B3']),
    (['C#2'], ['C#3', 'E3', 'G#3']),
    (['A1'], ['A2', 'C#3', 'E3']),
    (['B1'], ['B2', 'D#3', 'F#3']),
]
def bar_chords(b): return PROG[b % 4]

OUT = "/home/user/audio_preview/brass"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- O1 sax strut
def O1_sax_strut():
    s = Song(BPM, BARS, "O1_SaxStrut", swing=0.14)
    riff = [(0, 'E4', .13), (2, 'G#4', .12), (3, 'A4', .10), (6, 'B4', .26),
            (8, 'A4', .12), (10, 'G#4', .12), (11, 'F#4', .10), (14, 'E4', .30)]
    riff2 = [(0, 'B4', .13), (2, 'C#5', .12), (3, 'B4', .10), (6, 'G#4', .26),
             (8, 'F#4', .12), (10, 'E4', .12), (11, 'F#4', .10), (13, 'G#4', .18)]
    for b in range(BARS):
        lo, ch = bar_chords(b)
        line = riff if (b % 4) < 2 else riff2
        for st, nt, d in line:
            s.add('lead', sax(hz(nt), d, vel=0.62), s.T(b, st), 1.0, human=0.002)
        for st in (0, 8, 14):                       # tuba staccato bass
            s.add('bass', tuba(hz(lo[0]), 0.13, vel=0.62), s.T(b, st), 1.0, human=0.002)
        for st in (4, 12):                          # pizz comp
            for nt in ch:
                s.add('harm', pizz(hz(nt), 0.16, vel=0.30), s.T(b, st), 1.0, human=0.004)
        s.add('harm', french_horn(hz(ch[0]) * 2, s.bar * 0.9, vel=0.16), s.T(b, 0), 1.0, human=0.004)
        for st in (2, 6, 10, 14):
            s.add('fx', woodblock(980, 0.05, vel=0.18), s.T(b, st), 1.0, human=0.002)
    # last bar: sax hold + rise
    b = BARS
    s.add('lead', sax(hz('E5'), 1.2, vel=0.55), s.T(b - 1, 12), 1.0)
    return m2.master(s, f"{OUT}/O1_SaxStrut.wav",
                     gains={'lead': 1.05, 'harm': 0.55, 'bass': 0.95, 'drums': 0.0, 'fx': 0.35},
                     wet={'lead': 0.26, 'harm': 0.30, 'bass': 0.05, 'drums': 0.0, 'fx': 0.30})

# ------------------------------------------------------------- O2 brass bounce
def O2_brass_bounce():
    s = Song(BPM, BARS, "O2_BrassBounce", swing=0.06)
    hook = [(0, 'B4', .10), (1, 'B4', .10), (4, 'C#5', .10), (6, 'B4', .10),
            (8, 'G#4', .20), (11, 'A4', .10), (12, 'G#4', .10), (14, 'F#4', .20)]
    ans = [(2, 'E4', .12), (5, 'F#4', .12), (8, 'E4', .12), (10, 'D#4', .12), (13, 'E4', .26)]
    for b in range(BARS):
        lo, ch = bar_chords(b)
        for st, nt, d in hook:
            s.add('lead', trumpet(hz(nt), d, vel=0.55), s.T(b, st), 1.0, human=0.002)
        for st, nt, d in ans:                        # french horn answer
            s.add('harm', french_horn(hz(nt) * 0.5, d, vel=0.40), s.T(b, st), 1.0, human=0.003)
        for st in (0, 2, 4, 6, 8, 10, 12, 14):       # bassoon ostinato
            s.add('bass', bassoon(hz(lo[0]) * 2, 0.10, vel=0.50), s.T(b, st), 1.0, human=0.002)
        for nt in ch:                                # mouth organ pad
            s.add('harm', mouthorgan(hz(nt), s.bar * 0.92, vel=0.17), s.T(b, 0), 1.0, human=0.005)
        for st in (3, 7, 11, 15):
            s.add('fx', woodblock(1200, 0.045, vel=0.15), s.T(b, st), 1.0, human=0.002)
    s.add('lead', trumpet(hz('E5'), 0.9, vel=0.5), s.T(BARS - 1, 12), 1.0)
    return m2.master(s, f"{OUT}/O2_BrassBounce.wav",
                     gains={'lead': 1.0, 'harm': 0.62, 'bass': 0.80, 'drums': 0.0, 'fx': 0.30},
                     wet={'lead': 0.24, 'harm': 0.30, 'bass': 0.06, 'drums': 0.0, 'fx': 0.30})

# ---------------------------------------------------------- O3 harmonica shuffle
def O3_harmonica_shuffle():
    s = Song(BPM, BARS, "O3_HarmonicaShuffle", swing=0.18)
    line = [(0, 'E4', .22), (3, 'G#4', .14), (6, 'B4', .30), (8, 'A4', .14),
            (10, 'G#4', .14), (12, 'F#4', .14), (14, 'E4', .34)]
    line2 = [(0, 'B4', .22), (3, 'C#5', .14), (6, 'D#5', .28), (8, 'C#5', .14),
             (10, 'B4', .14), (12, 'G#4', .14), (14, 'F#4', .30)]
    for b in range(BARS):
        lo, ch = bar_chords(b)
        for st, nt, d in (line if (b % 4) < 2 else line2):
            s.add('lead', mouthorgan(hz(nt), d, vel=0.55), s.T(b, st), 1.0, human=0.003)
        walk = [(0, lo[0]), (3, lo[0]), (6, ch[1]), (10, ch[2]), (13, ch[1])]
        for st, nt in walk:
            s.add('bass', tuba(hz(nt) / 2, 0.16, vel=0.60), s.T(b, st), 1.0, human=0.002)
        for st in (0, 4, 8, 12):                     # accordion pump
            s.add('harm', accordion([hz(n) for n in ch], 0.13, vel=0.26), s.T(b, st), 1.0, human=0.004)
        for st in (2, 6, 10, 14):
            s.add('fx', woodblock(760, 0.05, vel=0.20), s.T(b, st), 1.0, human=0.002)
        s.add('harm', sax(hz(ch[0]), 0.10, vel=0.16), s.T(b, 15), 1.0, human=0.003)
    s.add('lead', mouthorgan(hz('E5'), 1.0, vel=0.5), s.T(BARS - 1, 12), 1.0)
    return m2.master(s, f"{OUT}/O3_HarmonicaShuffle.wav",
                     gains={'lead': 1.05, 'harm': 0.58, 'bass': 0.95, 'drums': 0.0, 'fx': 0.34},
                     wet={'lead': 0.22, 'harm': 0.28, 'bass': 0.05, 'drums': 0.0, 'fx': 0.30})

# ------------------------------------------------------------- O4 big-band stabs
def O4_bigband_stabs():
    s = Song(BPM, BARS, "O4_BigBandStabs", swing=0.10)
    hits = [0, 3, 6, 10, 12]
    fill = [(13, 'E4'), (14, 'F#4'), (15, 'G#4')]
    for b in range(BARS):
        lo, ch = bar_chords(b)
        for st in hits:                              # full section stab
            d = 0.11 if st != 10 else 0.22
            for i, nt in enumerate(ch):
                s.add('harm', trumpet(hz(nt) * 2, d, vel=0.34), s.T(b, st), 1.0, human=0.002)
                s.add('harm', sax(hz(nt), d, vel=0.30), s.T(b, st), 1.0, human=0.002)
            s.add('bass', french_horn(hz(lo[0]), d * 1.2, vel=0.45), s.T(b, st), 1.0, human=0.002)
        for st, nt in fill:                          # sax run into next bar
            s.add('lead', sax(hz(nt), 0.09, vel=0.45), s.T(b, st), 1.0, human=0.002)
        for st in (0, 2, 4, 6, 8, 10, 12, 14):       # pizz bass 8ths
            s.add('bass', pizz(hz(lo[0]) * 2, 0.14, vel=0.42), s.T(b, st), 1.0, human=0.003)
        for st in (1, 5, 9, 13):                     # ratchet (instrument, not drum kit)
            s.add('fx', ratchet(0.20, vel=0.16), s.T(b, st), 1.0, human=0.002)
    for i, nt in enumerate(PROG[0][1]):
        s.add('harm', trumpet(hz(nt) * 2, 0.9, vel=0.36), s.T(BARS - 1, 12), 1.0)
    return m2.master(s, f"{OUT}/O4_BigBandStabs.wav",
                     gains={'lead': 0.95, 'harm': 0.85, 'bass': 0.95, 'drums': 0.0, 'fx': 0.35},
                     wet={'lead': 0.24, 'harm': 0.30, 'bass': 0.07, 'drums': 0.0, 'fx': 0.30})

# ------------------------------------------------------------ O5 unison street
def O5_unison_street():
    s = Song(BPM, BARS, "O5_UnisonStreet", swing=0.0)
    hook = [(0, 'E4', .18), (2, 'G#4', .18), (4, 'B4', .18), (6, 'E5', .34),
            (8, 'D#5', .18), (10, 'C#5', .18), (12, 'B4', .18), (14, 'G#4', .28)]
    hook_b = [(0, 'F#4', .18), (2, 'A4', .18), (4, 'C#5', .18), (6, 'E5', .34),
              (8, 'D#5', .18), (10, 'B4', .18), (12, 'A4', .18), (14, 'F#4', .28)]
    for b in range(BARS):
        lo, ch = bar_chords(b)
        line = hook if (b % 4) in (0, 3) else hook_b
        for st, nt, d in line:
            s.add('lead', sax(hz(nt), d, vel=0.42), s.T(b, st), 1.0, human=0.002)
            s.add('harm', trumpet(hz(nt), d, vel=0.34), s.T(b, st), 1.0, human=0.002)
            s.add('harm', french_horn(hz(nt) / 2, d, vel=0.30), s.T(b, st), 1.0, human=0.002)
            s.add('harm', mouthorgan(hz(nt) * 2, d, vel=0.14), s.T(b, st), 1.0, human=0.003)
        for st in (0, 2, 4, 6, 8, 10, 12, 14):       # tuba octave 8ths
            s.add('bass', tuba(hz(lo[0]) / (2 if st % 4 else 1), 0.12, vel=0.55), s.T(b, st), 1.0, human=0.002)
        for st in (4, 12):
            s.add('fx', woodblock(1050, 0.06, vel=0.26), s.T(b, st), 1.0, human=0.002)
    for nt in PROG[0][1]:
        s.add('harm', trumpet(hz(nt), 1.0, vel=0.36), s.T(BARS - 1, 12), 1.0)
        s.add('lead', sax(hz(nt), 1.0, vel=0.34), s.T(BARS - 1, 12), 1.0)
    return m2.master(s, f"{OUT}/O5_UnisonStreet.wav",
                     gains={'lead': 0.95, 'harm': 0.75, 'bass': 0.95, 'drums': 0.0, 'fx': 0.30},
                     wet={'lead': 0.24, 'harm': 0.30, 'bass': 0.05, 'drums': 0.0, 'fx': 0.30})

if __name__ == "__main__":
    for fn in (O1_sax_strut, O2_brass_bounce, O3_harmonica_shuffle, O4_bigband_stabs, O5_unison_street):
        p = fn()
        import wave
        w = wave.open(p)
        print(f"{os.path.basename(p):26s} {w.getnframes()/w.getframerate():5.2f}s")
