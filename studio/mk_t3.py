#!/usr/bin/env python3
"""Build the Type-3 project `time_faster`: narration -> wordtimes -> project.json."""
import json
import os
import shutil
import sys

STUDIO = "/home/user/studio"
PDIR = os.path.join(STUDIO, "projects", "time_faster")
os.makedirs(os.path.join(PDIR, "narr"), exist_ok=True)
sys.path.insert(0, STUDIO)

LINES = [
    ("01_hook", "01.mp3", 0.3,
     "BACHPAN MEIN EK GARMI KI CHHUTTI... KITNI LAMBI LAGTI THI?",
     "बचपन में एक गर्मी की छुट्टी कितनी लंबी लगती थी?"),
    ("02_now", "02.mp3", 6.3,
     "AUR AB? PURA SAAL AANKH JHAPAKNE MEIN NIKAL JATA HAI.",
     "और अब? पूरा साल आँख झपकने में निकल जाता है।"),
    ("03_reason", "03.mp3", 12.3,
     "WAJAH HAI - DIMAAG NAYI CHEEZON KO BAHUT DETAIL MEIN SAVE KARTA HAI.",
     "वजह है - दिमाग़ नई चीज़ों को बहुत डिटेल में सेव करता है।"),
    ("04_new", "04.mp3", 18.3,
     "NAYI JAGAH, NAYA RASTA, NAYA KAAM - DIMAAG KO INHI MEIN MEHNAT LAGTI HAI.",
     "नई जगह, नया रास्ता, नया काम - दिमाग़ को इन्हीं में मेहनत लगती है।"),
    ("05_slow", "05.mp3", 24.3,
     "AUR JAB DIMAAG MEHNAT KARTA HAI, TO GHADI KI SUIYAN DHEEMI LAGTI HAIN.",
     "और जब दिमाग़ मेहनत करता है, तो घड़ी की सुइयाँ धीमी लगती हैं।"),
    ("06_routine", "06.mp3", 30.3,
     "LEKIN JAB ZINDAGI ROUTINE BAN JATI HAI, DIMAAG DIN SKIP KARNE LAGTA HAI.",
     "लेकिन जब ज़िंदगी रूटीन बन जाती है, दिमाग़ दिन स्किप करने लगता है।"),
    ("07_year", "07.mp3", 34.4,
     "ISILIYE SAAL CHHOTA NAHI HOTA - USMEIN NAYI YAADEIN KAM HOTI HAIN.",
     "इसीलिए साल छोटा नहीं होता - उसमें नई यादें कम होती हैं।"),
    ("08_tip", "08.mp3", 40.3,
     "TO HAR HAFTE KUCH NAYA KARO. SAMAY DHEEMA HO JAYEGA.",
     "तो हर हफ़्ते कुछ नया करो। समय धीमा हो जाएगा।"),
]


def main():
    import transcribe as T

    wt = {}
    narr = []
    for nid, fn, at, cap, hi in LINES:
        dst = os.path.join(PDIR, "narr", fn)
        shutil.copy(f"/tmp/t3n/{fn}", dst)
        r = T.post(dst, lang="hi")
        words = [[round(w["start"], 3), round(w["end"], 3)] for w in r.get("words", [])]
        dur = float(r.get("duration") or (words[-1][1] if words else 3.0))
        wt[nid] = {"dur": dur, "words": words}
        narr.append({"id": nid, "at": at, "file": f"narr/{fn}",
                     "caption": cap, "hindi": hi, "lang": "hi"})
        print(f"{nid}: {dur:.2f}s {len(words)} words")

    json.dump(wt, open(os.path.join(PDIR, "wordtimes.json"), "w"), indent=1)

    shutil.copy("/tmp/t3v/reel_t3.mp4", os.path.join(PDIR, "source.mp4"))

    proj = {
        "name": "time_faster",
        "source": {"local": os.path.join(PDIR, "source.mp4"),
                   "url": "", "note": "Pexels free-license stock reel"},
        "look": "film",
        "layout": {"size": [1080, 1920], "band": 360, "bottom_band": 360,
                   "cap_y": 1260, "cap_size": 60, "cap_line_chars": 26},
        "header": [
            {"text": "WHY TIME", "color": "white", "hi": "TIME",
             "hi_color": "yellow", "size": 148, "y": 112},
            {"text": "FEELS FASTER", "color": "white", "hi": "FASTER",
             "hi_color": "red", "size": 113, "y": 202},
        ],
        "audio": {"duck": 0.50, "master_gain_db": 2.5},
        "clips": [{"ss": 0.0, "dur": 46.1, "focus": [0.5, 0.5], "zoom_to": 1.02}],
        "narration": narr,
    }
    json.dump(proj, open(os.path.join(PDIR, "project.json"), "w"), indent=1)
    print("project written:", PDIR)


if __name__ == "__main__":
    main()
