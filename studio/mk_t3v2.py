#!/usr/bin/env python3
"""Build Type-3 projects from narration mp3s + a b-roll reel."""
import json
import os
import shutil
import sys

STUDIO = "/home/user/studio"
sys.path.insert(0, STUDIO)

SPEC = {
    "phineas_ferb": {
        "src_dir": "/tmp/t3a", "reel": "/tmp/t3a/reel.mp4", "reel_dur": 43.2,
        "header": [
            {"text": "PHINEAS", "color": "white", "hi": "PHINEAS",
             "hi_color": "yellow", "size": 148, "y": 112},
            {"text": "AND FERB", "color": "white", "hi": "FERB",
             "hi_color": "red", "size": 118, "y": 202},
        ],
        "lines": [
            ("01_hook", "01.mp3",
             "104 DIN KI GARMI KI CHHUTTI - AUR DO SAUTELE BHAI, PHINEAS AUR FERB, HAR DIN KUCH NAYA BANATE HAIN."),
            ("02_what", "02.mp3",
             "AAJ ROLLERCOASTER, KAL ROBOT, PARSON PURA BEACH - AUR SAB KUCH GHAR KE PICHHWADE MEIN."),
            ("03_candace", "03.mp3",
             "BEHAN CANDACE HAR ROZ UNHE MAAN KE SAAMNE PAKADWANA CHAHTI HAI - PAR MAAN KO KABHI KUCH DIKHTA NAHI."),
            ("04_perry", "04.mp3",
             "KYUNKI PALTU PLATYPUS PERRY ASAL MEIN EK SECRET AGENT HAI - AUR DR. DOOFENSHMIRTZ KI MACHINE HAR BAAR SAARA SABOOT MITA DETI HAI."),
            ("05_end", "05.mp3",
             "YAHI IS SHOW KA JAADU HAI - EK HI FORMULA, 104 BAAR - AUR HAR BAAR MAZA."),
        ],
    },
    "danapur_platform": {
        "src_dir": "/tmp/t3b", "reel": "/tmp/t3b/reel.mp4", "reel_dur": 45.0,
        "header": [
            {"text": "DANAPUR", "color": "white", "hi": "DANAPUR",
             "hi_color": "red", "size": 160, "y": 112},
            {"text": "PLATFORM 3", "color": "white", "hi": "3",
             "hi_color": "yellow", "size": 118, "y": 208},
        ],
        "lines": [
            ("01_hook", "01.mp3",
             "DANAPUR STATION. RAAT 2:40. PLATFORM 3 PAR EK TRAIN AATI HAI - JO KISI TIMETABLE MEIN NAHI HAI."),
            ("02_see", "02.mp3",
             "RAHUL NE USE DEKHA. COACH KHAALI THA - PAR HAR KHIDKI SE EK HI AADMI JHANK RAHA THA."),
            ("03_door", "03.mp3",
             "TRAIN RUKI. DARWAZA KHULA. AUR ANDAR SE AAWAZ AAYI - RAHUL, TERI SEAT KHAALI HAI."),
            ("04_name", "04.mp3",
             "WO USKA NAAM KAISE JAANTI THI? RAHUL NE PEECHE DEKHA - STATION PAR KOI NAHI THA. SIRF EK BOARD: DANAPUR, BAND."),
            ("05_end", "05.mp3",
             "AGLI SUBAH LOGON KO USKI CHAPPAL PLATFORM 3 PAR MILI. AUR RAHUL AAJ BHI WAHIN HAI - US TRAIN MEIN. HAR RAAT."),
        ],
    },
}


def build(name):
    import transcribe as T
    spec = SPEC[name]
    pdir = os.path.join(STUDIO, "projects", name)
    os.makedirs(os.path.join(pdir, "narr"), exist_ok=True)

    wt, narr = {}, []
    at = 0.3
    for nid, fn, cap in spec["lines"]:
        dst = os.path.join(pdir, "narr", fn)
        shutil.copy(os.path.join(spec["src_dir"], fn), dst)
        r = T.post(dst, lang="hi")
        words = [[round(w["start"], 3), round(w["end"], 3)] for w in r.get("words", [])]
        dur = float(r.get("duration") or (words[-1][1] if words else 3.0))
        wt[nid] = {"dur": dur, "words": words}
        narr.append({"id": nid, "at": round(at, 2), "file": f"narr/{fn}",
                     "caption": cap, "lang": "hi"})
        print(f"{nid}: {dur:.2f}s  at {at:.2f}  ({len(words)} words)")
        at += dur + 0.35

    json.dump(wt, open(os.path.join(pdir, "wordtimes.json"), "w"), indent=1)
    shutil.copy(spec["reel"], os.path.join(pdir, "source.mp4"))

    proj = {
        "name": name,
        "source": {"local": os.path.join(pdir, "source.mp4"), "url": "",
                   "note": "Pexels free-license stock b-roll"},
        "look": "film",
        "layout": {"size": [1080, 1920], "band": 360, "bottom_band": 360,
                   "cap_y": 1260, "cap_size": 60, "cap_line_chars": 26},
        "header": spec["header"],
        "audio": {"duck": 0.50, "master_gain_db": 2.5},
        "clips": [{"ss": 0.0, "dur": spec["reel_dur"], "focus": [0.5, 0.5],
                   "zoom_to": 1.02}],
        "narration": narr,
    }
    json.dump(proj, open(os.path.join(pdir, "project.json"), "w"), indent=1)
    print("written:", pdir, f"(total narration {at-0.35:.2f}s)")


if __name__ == "__main__":
    build(sys.argv[1])
