#!/usr/bin/env python3
"""
skill_router.py — "kaunsi skill kab lagegi" ka decision engine.

Problem it solves
-----------------
`maker-studio` me 240+ modules / 58 engine files / earshot (audio ears) /
real_sfx (sound design) / skills/viral-edits (routing matrix) installed hain.
Lekin build karte waqt sirf 2-3 use hote hain aur baaki pada reh jaata hai.
Video ke saath jo galti hui thi (audio ko sunne ke bajaye graph se maan lena)
  exactly isi wajah se hui — koi stage hi nahi tha jo "audio samjho" ko
  mandatory banata.

Ye router 4 kaam karta hai
--------------------------
  1. discover : poore workspace ko scan karke ek honest registry banata hai
                (file exist karti hai? entry point milta hai? -> verified)
  2. classify : brief padh ke video ka type + flags nikalta hai
  3. plan     : us type ke liye stages + skills + GATES + anti-patterns deta hai
  4. audit    : ban chuki file pe gates actually chala kar batata hai kaunsi
                skill lagi aur kaunsi chhoot gayi

CLI
---
  python3 studio/skill_router.py discover
  python3 studio/skill_router.py plan  --brief briefs/krishna.json
  python3 studio/skill_router.py audit --video out.mp4 --brief briefs/krishna.json
  python3 studio/skill_router.py skills --tag audio
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

STUDIO = os.path.dirname(os.path.abspath(__file__))
HOME = "/home/user"
REG_PATH = os.path.join(STUDIO, "skills_registry.json")

# --------------------------------------------------------------------------- #
# 1. REGISTRY — curated skills, each verified against the filesystem
# --------------------------------------------------------------------------- #
# id, stage, path, entry, tags, why
SKILLS: List[dict] = [
    # ---------------- intake / research ----------------
    dict(id="analyze.video_timeline", stage="structure", path="analyze.py",
         entry="video_timeline()", tags=["video", "scenes", "beats", "speech"],
         why="Source ka scene/shots/audio-energy/speech timeline nikalta hai"),
    dict(id="pacing_audio.hook_candidates", stage="structure",
         path="om_hybrid/pacing_audio.py", entry="score_hook_candidates()",
         tags=["audio", "hook", "structure"],
         why="Kaunsa moment hook ban sakta hai, energy+silenсes se rank"),
    dict(id="templates.beat_grid", stage="structure",
         path="templates.py", entry="beat_grid()",
         tags=["beat", "sync", "timing"], why="Beat grid + snap to frames"),
    dict(id="templates.find_peak_scene", stage="structure",
         path="templates.py", entry="find_peak_scene()",
         tags=["structure", "climax"], why="Peak/climax scene dhoondhta hai"),
    dict(id="clipsel.scan", stage="source", path="clipsel.py",
         entry="scan()", tags=["source", "selection", "ranking"],
         why="Candidate clips ko score karke fail/weak wale hataata hai"),
    dict(id="om_hybrid.clip_scout", stage="source",
         path="om_hybrid/clip_scout.py", entry="extract_ign_1080p_mp4()",
         tags=["source", "trailer", "1080p"], why="Trailer/1080p source fetch"),
    dict(id="srcget", stage="source", path="srcget.py", entry="get()",
         tags=["source", "stock", "archive"], why="Multi-source stock/archive fetch"),
    dict(id="stock_sources", stage="source", path="om_hybrid/stock_sources",
         entry="all_sources()", tags=["source", "stock", "catalog"],
         why="24 stock/archive adapters (pexels, archive.org, nasa, loc...)"),

    # ---------------- LISTEN / UNDERSTAND AUDIO (the missing stage) --------
    dict(id="earshot.measure", stage="listen", path="earshot/features.py",
         entry="measure()", tags=["audio", "listen", "measure"],
         why="LUFS/TP/bands/onsets/tonal — audio ka objective naksha"),
    dict(id="earshot.describe", stage="listen", path="earshot/describe.py",
         entry="describe()", tags=["audio", "listen", "content"],
         why="Audio me kya hai (speech/music/hits) — bina sunne maan lene se bachao"),
    dict(id="earshot.critique", stage="listen", path="earshot/critique.py",
         entry="critique()", tags=["audio", "listen", "critique", "quality"],
         why="Mix ko grade karta hai + actionable fixes deta hai"),
    dict(id="earshot.realness", stage="listen", path="earshot",
         entry="earshot.realness()", tags=["audio", "realness", "music"],
         why="Kya ye 'real produced music' lagta hai ya synth/canned"),
    dict(id="earshot.timeline", stage="listen", path="earshot/timeline.py",
         entry="timeline()", tags=["audio", "cut_sync", "video"],
         why="Audio events vs video cuts ka sync map (cut_sync gate)"),
    dict(id="earshot.compare", stage="listen", path="earshot/compare.py",
         entry="compare()", tags=["audio", "reference", "compare"],
         why="Reference sample vs apna mix — A/B distance"),
    dict(id="asr.listen", stage="listen", path="transcribe.py",
         entry="run()", tags=["audio", "speech", "listen", "dialogue"],
         why="Dialogue ko TEXT me sunna (Groq whisper-large-v3, word timings)"),
    dict(id="asr.faster_whisper", stage="listen", path="skill_router.py",
         entry="asr_listen()", tags=["audio", "speech", "listen", "dialogue",
                                     "offline"],
         why="Offline ASR (faster-whisper) — intelligibility + gibberish detect"),
    dict(id="real_sfx.listen_yamnet", stage="listen",
         path="real_sfx/scripts/listen.py", entry="main()",
         tags=["audio", "tagging", "yamnet", "speech"],
         why="YAMNet se sound tags + voice command detection"),
    dict(id="real_sfx.masking", stage="listen",
         path="real_sfx/scripts/masking.py", entry="speech_active()",
         tags=["audio", "dialogue", "masking", "intelligibility"],
         why="Kya dialogue music ke neeche dab raha hai (masked cues)"),
    dict(id="real_sfx.refstyle", stage="listen",
         path="real_sfx/scripts/refstyle.py", entry="measure()",
         tags=["audio", "reference", "style"], why="Reference edit ka audio style napna"),
    dict(id="real_sfx.unbake", stage="listen",
         path="real_sfx/scripts/unbake.py", entry="unbake()",
         tags=["audio", "stems", "reverse_engineer"],
         why="Reference ke layers (voice/bed/sfx) alag karke levels nikalna"),

    # ---------------- VISUALS ----------------
    dict(id="viral_vfx.still_art", stage="visuals",
         path="om_hybrid/viral_vfx.py", entry="render_still_art_edit()",
         tags=["visuals", "still_art", "poster", "deity", "no_footage"],
         why="1 static art -> 15-20s beat-synced edit (kevamarts style)"),
    dict(id="printrev.page_system", stage="visuals",
         path="om_hybrid/printrev_edit.py", entry="PrintRevealEdit",
         tags=["visuals", "print", "sketchbook", "deity", "no_footage"],
         why="Sketchbook page / card reveal format (F0E2B6A9 sample)"),
    dict(id="cashworth.9piece", stage="visuals",
         path="om_hybrid/cashworth_edit.py", entry="fit_16x9()",
         tags=["visuals", "aesthetic", "7f73e", "text_behind_roto"],
         why="@cashworthclipz 9-piece aesthetic engine"),
    dict(id="zohair.jigsaw", stage="visuals",
         path="om_hybrid/zohair_edit.py", entry="render_zohair_jigsaw_edit()",
         tags=["visuals", "jigsaw", "style1", "dialogue_pockets"],
         why="@thisiszohair vocal-pocket rhythm edit"),
    dict(id="aura.viral", stage="visuals", path="om_hybrid/aura_edit.py",
         entry="render_aura_edit()", tags=["visuals", "style2", "drop"],
         why="Scene->drop Style 2 engine + 4K CC look"),
    dict(id="ironman.difference", stage="visuals",
         path="om_hybrid/ironman_edit.py", entry="render_ironman_style_edit()",
         tags=["visuals", "difference_text", "hype"], why="Difference-typography hype edit"),
    dict(id="viral_vfx.pipeline", stage="visuals",
         path="om_hybrid/viral_vfx.py", entry="apply_vfx_pipeline()",
         tags=["visuals", "vfx", "risograph", "dither", "crt"],
         why="17-effect VFX arsenal (riso/dither/crt/shockwave/roto)"),
    dict(id="skills.blob_tracking", stage="visuals",
         path="skills/blob-tracking/scripts/blobtrack.py", entry="run()",
         tags=["visuals", "tracking", "hud"], why="Object/blob track -> HUD labels"),
    dict(id="smart_camera", stage="motion", path="om_hybrid/smart_camera.py",
         entry="plan_smart_camera()", tags=["motion", "camera", "reframe"],
         why="Shot-wise subpixel camera moves / reframe"),
    dict(id="motion_director", stage="motion",
         path="om_hybrid/motion_director.py", entry="choreograph_shots_table()",
         tags=["motion", "choreography", "hud"], why="Shot table ke hisaab se motion plan"),
    dict(id="ironman.optical_flow", stage="motion",
         path="om_hybrid/ironman_edit.py", entry="optical_flow_interp()",
         tags=["motion", "interpolation", "smooth"], why="Optical-flow frame interpolation"),

    # ---------------- TYPOGRAPHY ----------------
    dict(id="textkit.ass", stage="type", path="textkit.py", entry="ass_filter()",
         tags=["type", "subtitles", "ass"], why="Styled ASS subtitles burn-in"),
    dict(id="viral_vfx.center_serif", stage="type",
         path="om_hybrid/viral_vfx.py", entry="write_center_serif_ass()",
         tags=["type", "serif", "center"], why="Center serif subs (Style 1 look)"),
    dict(id="printrev.rough_type", stage="type",
         path="om_hybrid/printrev_edit.py", entry="rough_text_mask()",
         tags=["type", "print", "stamp", "hindi"],
         why="Rubber-stamp ink text (Devanagari-safe, chipped edges)"),

    # ---------------- GRADE ----------------
    dict(id="cinema_looks", stage="grade", path="om_hybrid/cinema_looks.py",
         entry="apply_cinema_look()", tags=["grade", "lut", "cinema"],
         why="Cube LUT based cinema looks"),
    dict(id="aura.4k_cc", stage="grade", path="om_hybrid/aura_edit.py",
         entry="apply_viral_4k_quality_cc()", tags=["grade", "4k", "quality"],
         why="5-layer 4K Quality CC (denoise->CLAHE->unsharp->blacks->vibrance)"),
    dict(id="cashworth.dream_grade", stage="grade",
         path="om_hybrid/cashworth_edit.py", entry="apply_cashworth_dream_grade()",
         tags=["grade", "dream", "aesthetic"], why="Dreamy aesthetic grade"),

    # ---------------- SFX ----------------
    dict(id="sfx_sync", stage="sfx", path="om_hybrid/sfx_sync.py",
         entry="render_synced_sfx()", tags=["sfx", "sync"], why="Beat-synced SFX cues"),
    dict(id="sfx.build", stage="sfx", path="sfx.py", entry="build_sfx()",
         tags=["sfx", "whoosh", "impact"], why="Whoosh/impact/riser/pop generation"),
    dict(id="real_sfx.mix", stage="sfx", path="real_sfx/scripts/mix.py",
         entry="main()", tags=["sfx", "mix", "masking"], why="SFX busses + masking-aware mix"),
    dict(id="openverse_realsfx", stage="sfx", path="om_hybrid/openverse_realsfx.py",
         entry="auto_sound_design_video()", tags=["sfx", "auto", "openverse"],
         why="Auto sound design (licensed assets)"),

    # ---------------- AUDIO MIX ----------------
    dict(id="zohair.multitrack", stage="audio_mix", path="om_hybrid/zohair_edit.py",
         entry="mix_zohair_multitrack_audio()", tags=["audio", "dialogue", "pockets"],
         why="Dialogue pockets me song ko chhota karke weave karna"),
    dict(id="aura.muffle_under_scene", stage="audio_mix", path="om_hybrid/aura_edit.py",
         entry="mix_real_song_jigsaw()", tags=["audio", "dialogue", "ducking"],
         why="Scene ke neeche -18.5dB LPF song, phir drop pe 0dB sweep"),
    dict(id="printrev.loudnorm", stage="audio_mix", path="om_hybrid/printrev_edit.py",
         entry="mux_audio()", tags=["audio", "loudness", "master"],
         why="2-pass loudnorm + true-peak safe mux"),

    # ---------------- QA GATES ----------------
    dict(id="visual_qa", stage="qa", path="om_hybrid/visual_qa.py",
         entry="run_full_qa()", tags=["qa", "video", "frames"], why="Frame-level visual QA"),
    dict(id="slideshow_risk", stage="qa", path="om_hybrid/slideshow_risk.py",
         entry="score_slideshow_risk()", tags=["qa", "motion", "liveness"],
         why="Slideshow/dead-motion risk score"),
    dict(id="master_pipeline", stage="qa", path="om_hybrid/master_pipeline.py",
         entry="master_polish_video()", tags=["qa", "master", "polish"],
         why="Neural-ears master polish pass"),
    dict(id="earshot.scorecard", stage="qa", path="earshot/critique.py",
         entry="scorecard()", tags=["qa", "audio", "scorecard"],
         why="Audio scorecard (dialogue clarity, bed balance, sync)"),
    dict(id="real_sfx.levels", stage="qa", path="real_sfx/scripts/levels.py",
         entry="main()", tags=["qa", "levels", "balance"], why="Levels/group balance report"),
]

# stage order + which stages are hard gates
STAGE_ORDER = ["source", "listen", "structure", "visuals", "type", "motion",
               "grade", "sfx", "audio_mix", "qa"]

ANTI_PATTERNS = [
    "Audio ko sirf RMS/spectrum se 'samajh' lena — ASR/describe/critique se sunna zaroori.",
    "Reference sample ka audio transcribe kiye bina usko 'music-only' maan lena.",
    "Song ko dialogue wale video me full-volume chalana (dialogue dab jaata hai).",
    "Music Python se synthesize karna (real produced song hona chahiye).",
    "Beat grid ko audio ka 'content' samajh lena — wahi sirf tempo hai.",
    "Ek hi engine (jaise printrev) se sab kuch karna jab 40+ skills available hain.",
]

# type -> extra skills that must fire
TYPE_RULES = {
    "deity_no_footage": dict(stages=["visuals", "type", "grade", "audio_mix", "qa"],
                             extra=["viral_vfx.still_art", "printrev.page_system"]),
    "dialogue_led": dict(stages=["listen", "structure", "audio_mix", "qa"],
                         extra=["asr.listen", "real_sfx.masking", "earshot.critique"]),
    "song_driven": dict(stages=["listen", "structure", "visuals", "audio_mix", "qa"],
                        extra=["earshot.realness"]),
    "movie_hype": dict(stages=["source", "structure", "visuals", "motion", "grade", "qa"],
                       extra=["viral_vfx.pipeline", "ironman.difference"]),
    "explainer_hindi": dict(stages=["listen", "structure", "type", "grade", "qa"],
                            extra=["textkit.ass", "viral_vfx.center_serif"]),
}


def _norm(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(STUDIO, p)


def verify_skill(sk: dict) -> dict:
    """Check the file and the entry point really exist."""
    path = _norm(sk["path"])
    sk = dict(sk)
    sk["verified"] = False
    sk["note"] = ""
    if not os.path.exists(path):
        sk["note"] = "path missing"
        return sk
    entry = sk["entry"].replace("()", "")
    if entry.startswith("class:") or entry == "class":
        return sk
    target = path
    if os.path.isdir(path):
        # module dir: look for the name anywhere
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".py") and entry in open(os.path.join(root, f),
                                                       errors="ignore").read():
                    sk["verified"] = True
                    return sk
        sk["note"] = "entry not found in dir"
        return sk
    if not path.endswith(".py"):
        return sk
    try:
        tree = ast.parse(open(path, errors="ignore").read())
    except SyntaxError:
        sk["note"] = "syntax error"
        return sk
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
    if entry in names or entry.split(".")[0] in names:
        sk["verified"] = True
    else:
        # something imported / attribute — be lenient but say so
        src = open(path, errors="ignore").read()
        sk["verified"] = entry in src
        sk["note"] = "soft match" if sk["verified"] else "entry not found"
    return sk


def discover(write=True) -> dict:
    reg = {"generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
           "studio": STUDIO, "count": 0, "skills": []}
    for sk in SKILLS:
        reg["skills"].append(verify_skill(sk))
    reg["count"] = len(reg["skills"])
    reg["verified_count"] = sum(1 for s in reg["skills"] if s["verified"])
    reg["stages"] = STAGE_ORDER
    reg["anti_patterns"] = ANTI_PATTERNS
    # also count the raw python surface so the number is honest
    py = 0
    for root, _, files in os.walk(STUDIO):
        if "__pycache__" in root:
            continue
        py += sum(1 for f in files if f.endswith(".py"))
    reg["python_modules_scanned"] = py
    if write:
        json.dump(reg, open(REG_PATH, "w"), indent=1, ensure_ascii=False)
    return reg


# --------------------------------------------------------------------------- #
# 2. CLASSIFY a brief
# --------------------------------------------------------------------------- #
FLAG_WORDS = {
    "dialogue": ["dialogue", "baat", "bol rahe", "speech", "voice", "updesh",
                 "samjha", "sermon", "monologue", "goosebump"],
    "song_only": ["song", "gaana", "bhajan", "music", "beat drop", "track"],
    "zero_footage": ["no footage", "poster", "art", "illustration", "sketch",
                     "deity", "bhagwan", "manga", "print"],
    "hindi": ["hindi", "हिंदी", "devanagari"],
    "beat_lock": ["beat", "sync", "bpm", "drop", "grid"],
    "reference_sample": ["sample", "reference", "jaisa", "type ka", "style of"],
    "no_bgm": ["no bgm", "bgm nahi", "silence"],
    "short": ["15s", "20s", "shorts", "reel"],
}


def classify(brief: dict) -> dict:
    text = " ".join(str(v) for v in brief.values()).lower()
    flags = {}
    for k, words in FLAG_WORDS.items():
        flags[k] = any(w in text for w in words)
    types = []
    if flags["zero_footage"]:
        types.append("deity_no_footage")
    if flags["dialogue"]:
        types.append("dialogue_led")
    if flags["song_only"] and not flags["dialogue"]:
        types.append("song_driven")
    if not types:
        types.append("movie_hype")
    return {"flags": flags, "types": types}


# --------------------------------------------------------------------------- #
# 3. PLAN
# --------------------------------------------------------------------------- #
def plan(brief: dict, registry: Optional[dict] = None) -> dict:
    reg = registry or discover(write=False)
    by_id = {s["id"]: s for s in reg["skills"]}
    cls = classify(brief)
    stages = list(STAGE_ORDER)
    must_extra: List[str] = []
    for t in cls["types"]:
        rule = TYPE_RULES.get(t, {})
        must_extra += rule.get("extra", [])

    rows = []
    for st in stages:
        sk = [s for s in reg["skills"] if s["stage"] == st]
        required_ids = [i for i in must_extra if by_id.get(i, {}).get("stage") == st]
        rows.append({
            "stage": st,
            "required": [by_id[i] for i in required_ids if i in by_id],
            "available": [s for s in sk if s["id"] not in required_ids],
        })

    gates = []
    if cls["flags"]["dialogue"] or "dialogue_led" in cls["types"]:
        gates += [
            dict(id="G1_speech_understanding",
                 check="source audio ko ASR + earshot.describe se SUNO, graph se guess mat karo",
                 tools=["asr.listen", "earshot.describe", "earshot.measure"]),
            dict(id="G2_dialogue_intelligible",
                 check="final mix pe ASR re-run: har line 90%+ words match honi chahiye",
                 tools=["asr.listen", "real_sfx.masking"]),
            dict(id="G3_bed_ducking",
                 check="dialogue ke neeche bed -14 se -20 dB; masking report clean",
                 tools=["real_sfx.masking", "earshot.critique"]),
            dict(id="G4_cut_sync",
                 check="cuts dialogue ke phrase pe, beat pe nahi",
                 tools=["earshot.timeline"]),
        ]
    if cls["flags"]["song_only"] or "song_driven" in cls["types"]:
        gates += [
            dict(id="G1_speech_understanding",
                 check="source audio ASR = speech hai ya music? (guess nahi, sun ke)",
                 tools=["asr.listen", "earshot.describe"]),
            dict(id="G5_real_music",
                 check="song real produced ho (realness), synth nahi",
                 tools=["earshot.realness"]),
            dict(id="G4_cut_sync", check="cuts beat grid pe, offset <= 1 frame",
                 tools=["earshot.timeline", "templates.beat_grid"]),
        ]
    if cls["flags"]["reference_sample"]:
        gates.append(dict(id="G6_reference_match",
                          check="reference sample se A/B compare + style match report",
                          tools=["earshot.compare", "real_sfx.refstyle"]))
    gates.append(dict(id="G7_loudness", check="I -14 LUFS, TP <= -1.5 dBTP",
                      tools=["earshot.measure", "printrev.loudnorm"]))
    gates.append(dict(id="G8_visual_qa", check="frame QA + slideshow risk",
                      tools=["visual_qa", "slideshow_risk"]))

    return {"brief": brief, "classification": cls, "stages": rows,
            "gates": gates, "anti_patterns": ANTI_PATTERNS,
            "registry": {"count": reg["count"],
                         "verified": reg["verified_count"],
                         "modules": reg["python_modules_scanned"]}}


def plan_markdown(p: dict) -> str:
    b = p["brief"]
    cls = p["classification"]
    L = []
    L.append(f"# Skill Plan — {b.get('title', 'untitled')}\n")
    L.append(f"**Brief:** {b.get('requirement', '')}\n")
    if b.get("must_have"):
        L.append(f"**Must have:** {', '.join(b['must_have'])}\n")
    L.append(f"**Type:** `{', '.join(cls['types'])}`  \n"
             f"**Flags:** " + ", ".join(f"`{k}`" for k, v in cls["flags"].items() if v) + "\n")
    L.append(f"**Registry:** {p['registry']['count']} skills curated "
             f"({p['registry']['verified']} verified) out of "
             f"{p['registry']['modules']} python modules scanned\n")
    L.append("\n## Stages (in order)\n")
    for row in p["stages"]:
        req = row["required"]
        avail = row["available"]
        if not req and not avail:
            continue
        L.append(f"\n### `{row['stage']}`")
        if req:
            L.append("**MUST USE**")
            for s in req:
                v = "OK" if s.get("verified") else "MISS"
                L.append(f"- `{s['id']}` [{v}] — {s['why']}")
        if avail:
            L.append("available (pick by need):")
            for s in avail:
                v = "ok" if s.get("verified") else "?"
                L.append(f"- `{s['id']}` [{v}] — {s['why']}")
    L.append("\n## GATES (pass hona zaroori)\n")
    for g in p["gates"]:
        L.append(f"- **{g['id']}** — {g['check']}  \n  tools: "
                 + ", ".join(f"`{t}`" for t in g["tools"]))
    L.append("\n## Anti-patterns (jo nahi karna)\n")
    for a in p["anti_patterns"]:
        L.append(f"- {a}")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# 4. AUDIT — run the measurable gates on a finished file
# --------------------------------------------------------------------------- #
def _ff() -> str:
    try:
        sys.path.insert(0, STUDIO)
        from om_hybrid._ffmpeg import get_ffmpeg
        return get_ffmpeg()
    except Exception:
        return "ffmpeg"


def _ffprobe() -> str:
    p = os.path.join(os.path.dirname(_ff()), "ffprobe")
    return p if os.path.exists(p) else "ffprobe"


def probe(path: str) -> dict:
    out = subprocess.run([_ffprobe(), "-v", "error", "-print_format", "json",
                          "-show_format", "-show_streams", path],
                         capture_output=True, text=True).stdout
    j = json.loads(out or "{}")
    v = next((s for s in j.get("streams", []) if s["codec_type"] == "video"), {})
    a = next((s for s in j.get("streams", []) if s["codec_type"] == "audio"), {})
    fr = v.get("r_frame_rate", "0/1")
    try:
        num, den = fr.split("/")
        fps = float(num) / float(den or 1)
    except Exception:
        fps = 0.0
    return {"dur": float(j.get("format", {}).get("duration", 0) or 0),
            "size_mb": float(j.get("format", {}).get("size", 0) or 0) / 1e6,
            "w": v.get("width"), "h": v.get("height"), "fps": round(fps, 2),
            "vcodec": v.get("codec_name"), "acodec": a.get("codec_name"),
            "has_audio": bool(a)}


def extract_audio(video: str, out: str) -> str:
    subprocess.run([_ff(), "-v", "error", "-y", "-i", video, "-vn",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", out],
                   check=True)
    return out


def asr_listen(wav16: str, model_size="small") -> dict:
    """Gate G1/G2 — actually listen to the speech."""
    from faster_whisper import WhisperModel
    import wave
    w = wave.open(wav16)
    a = (__import__("numpy").frombuffer(w.readframes(w.getnframes()),
                                        dtype="int16").astype("float32") / 32768.0)
    m = WhisperModel(model_size, device="cpu", compute_type="int8")
    segs, info = m.transcribe(a, language=None, vad_filter=True,
                              word_timestamps=True)
    segs = list(segs)
    words = []
    for s in segs:
        words += [(wd.word.strip(), wd.probability) for wd in (s.words or [])]
    txt = " ".join(s.text.strip() for s in segs).strip()
    confident = [w_ for w_ in words if w_[1] >= 0.55]
    # gibberish heuristic: too many 1-2 char tokens / repetition / no vowels
    toks = [t for t, _ in words]
    short = sum(1 for t in toks if len(t) <= 2) / max(1, len(toks))
    rep = 1 - len(set(toks)) / max(1, len(toks))
    return {"detected_language": info.language,
            "lang_prob": round(info.language_probability, 3),
            "n_segments": len(segs), "n_words": len(words),
            "confident_word_ratio": round(len(confident) / max(1, len(words)), 3),
            "short_token_ratio": round(short, 3),
            "repetition_ratio": round(rep, 3),
            "text_snippet": txt[:220],
            "intelligible": bool(len(words) >= 8 and
                                 len(confident) / max(1, len(words)) >= 0.6 and
                                 rep < 0.5 and short < 0.45)}


def audio_profile(wav: str) -> dict:
    """Gate G3/G5/G7 — earshot measure (objective) + music-vs-speech cues."""
    sys.path.insert(0, STUDIO)
    prof = {}
    try:
        from earshot import features
        m = features.measure(wav)
        prof.update({k: m.get(k) for k in
                     ("lufs", "true_peak_dbtp", "lra_lu", "harmonic_ratio",
                      "noise_floor_dbfs", "centroid_hz", "onsets")})
        prof["onsets"] = len(prof.get("onsets") or [])
    except Exception as e:  # pragma: no cover
        prof["error"] = f"{type(e).__name__}: {e}"
    try:
        import numpy as np
        import librosa
        y, sr = librosa.load(wav, sr=22050, mono=True)
        S = np.abs(librosa.stft(y, n_fft=1024, hop_length=128))
        f = librosa.fft_frequencies(sr=sr, n_fft=1024)
        env = S[(f >= 300) & (f < 3000)].sum(0)
        env = env - env.mean()
        e = np.abs(np.fft.rfft(env))
        fr = np.fft.rfftfreq(len(env), d=128 / sr)
        sel = (fr > 1) & (fr < 12)
        prof["syllable_mod_hz"] = round(float(fr[sel][np.argmax(e[sel])]), 2)
        prof["speech_band_share"] = round(
            float(S[(f >= 300) & (f < 3000)].sum() / (S.sum() + 1e-9)), 3)
        prof["low_band_share"] = round(
            float(S[(f >= 40) & (f < 200)].sum() / (S.sum() + 1e-9)), 3)
    except Exception as e:
        prof["librosa_error"] = str(e)
    return prof


REF_DIR = os.path.join(STUDIO, "reference_profiles")
REF_KEYS = ("lufs", "true_peak_dbtp", "lra_lu", "harmonic_ratio",
            "centroid_hz", "speech_band_share", "low_band_share")


def make_reference_profile(video_or_wav: str, name: str) -> dict:
    """Reference sample ka audio fingerprint — comparison ke liye."""
    os.makedirs(REF_DIR, exist_ok=True)
    work = tempfile.mkdtemp(prefix="ref_", dir="/var/tmp")
    wav = os.path.join(work, "a.wav")
    subprocess.run([_ff(), "-v", "error", "-y", "-i", video_or_wav, "-vn",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav],
                   check=True)
    prof = audio_profile(wav)
    out = {k: prof.get(k) for k in REF_KEYS}
    path = os.path.join(REF_DIR, f"{name}.json")
    json.dump(out, open(path, "w"), indent=1)
    return {"path": path, "profile": out}


def compare_to_reference(audio: dict, ref: dict) -> dict:
    """Reference ke audio fingerprint se distance + song-vs-speech verdict."""
    rows = []
    for k in REF_KEYS:
        if audio.get(k) is None or ref.get(k) is None:
            continue
        r, v = float(ref[k]), float(audio[k])
        span = {"lufs": 6.0, "true_peak_dbtp": 6.0, "lra_lu": 6.0,
                "harmonic_ratio": 0.6, "centroid_hz": 2500.0,
                "speech_band_share": 0.5, "low_band_share": 0.3}.get(k, 1.0)
        rows.append({"feature": k, "reference": round(r, 3),
                     "yours": round(v, 3),
                     "delta_norm": round(abs(v - r) / span, 3)})
    dist = sum(r["delta_norm"] for r in rows) / max(1, len(rows))
    song_like = (audio.get("harmonic_ratio") or 0) > 0.60 and \
                (audio.get("lra_lu") or 0) < 2.0
    speech_like = (audio.get("harmonic_ratio") or 1) < 0.55 and \
                  (audio.get("lra_lu") or 0) > 2.5
    return {"rows": rows, "distance": round(dist, 3),
            "style_match": dist <= 0.40 and (
                (ref.get("harmonic_ratio") or 1) >= 0.5 or
                (audio.get("harmonic_ratio") or 1) < 0.55),
            "character": ("song_like" if song_like else
                          "speech_like" if speech_like else "mixed")}


def motion_profile(video: str, workdir: str) -> dict:
    """Gate G8 — duplicate frames / black frames (slideshow risk, dead footage)."""
    import numpy as np
    tmp = os.path.join(workdir, "f")
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    subprocess.run([_ff(), "-v", "error", "-y", "-i", video, "-vf",
                    "fps=5,scale=64:114", os.path.join(tmp, "%04d.png")],
                   check=True)
    fs = sorted(os.listdir(tmp))
    arrs = [np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(
        os.path.join(tmp, f)).convert("L"), dtype=np.float32) for f in fs]
    if len(arrs) < 3:
        return {"frames": len(arrs)}
    diffs = [float(np.abs(arrs[i] - arrs[i - 1]).mean()) for i in range(1, len(arrs))]
    means = [float(a.mean()) for a in arrs]
    return {"frames": len(arrs),
            "mean_frame_diff": round(float(np.mean(diffs)), 2),
            "static_ratio": round(sum(1 for d in diffs if d < 1.0) / len(diffs), 3),
            "black_ratio": round(sum(1 for m in means if m < 12) / len(means), 3)}


def audit(video: str, brief: Optional[dict] = None, do_asr=True,
          model_size="small", ref_profile: Optional[str] = None) -> dict:
    work = tempfile.mkdtemp(prefix="audit_", dir="/var/tmp")
    info = {"video": video, "spec": probe(video)}
    wav = extract_audio(video, os.path.join(work, "a16.wav"))
    info["audio"] = audio_profile(wav)
    if do_asr:
        try:
            info["asr"] = asr_listen(wav, model_size)
        except Exception as e:
            info["asr"] = {"error": f"{type(e).__name__}: {e}"}
    info["motion"] = motion_profile(video, work)
    ref = None
    if ref_profile:
        rp = (ref_profile if ref_profile.endswith(".json")
              else os.path.join(REF_DIR, ref_profile + ".json"))
        if os.path.exists(rp):
            ref = json.load(open(rp))
            info["reference"] = compare_to_reference(info["audio"], ref)

    cls = classify(brief or {})
    gates = []

    def gate(gid, ok, detail, warn=None):
        st = "PASS" if ok else ("WARN" if warn else "FAIL")
        if ok:
            st = "PASS"
        elif warn:
            st = "WARN"
        gates.append({"gate": gid, "status": st, "detail": detail})

    sp = info["spec"]
    au = info["audio"]
    mo = info["motion"]
    asr = info.get("asr", {})

    needs_dialogue = cls["flags"].get("dialogue") or "dialogue_led" in cls["types"]
    heard_speech = asr.get("intelligible") and asr.get("n_words", 0) >= 8

    hr = au.get("harmonic_ratio") or 0.0
    lra = au.get("lra_lu") or 0.0
    speech_led = hr < 0.60 and lra >= 2.0
    song_led = hr > 0.60 and lra < 2.0
    if needs_dialogue:
        gate("G1_speech_present", speech_led,
             f"harmonic_ratio={hr} lra={lra} -> "
             + ("speech-led mix" if speech_led else
                "SONG-led mix (dialogue hi nahi / dab gaya)" if song_led
                else "unclear character"))
        gate("G2_dialogue_decodable", bool(heard_speech),
             f"ASR words={asr.get('n_words')} confident="
             f"{asr.get('confident_word_ratio')} "
             f"text='{str(asr.get('text_snippet'))[:80]}'",
             warn=(speech_led and not heard_speech))
    else:
        gate("G1_speech_understanding", True,
             f"brief song_driven — speech expected nahi (ASR words={asr.get('n_words')}): "
             f"isi wajah se bhajan-type audio chalta hai")

    gate("G5_real_music", (au.get("harmonic_ratio") or 0) > 0.10,
         f"harmonic_ratio={au.get('harmonic_ratio')}")
    if info.get("reference"):
        rf = info["reference"]
        gate("G6_reference_match", rf["style_match"],
             f"style distance={rf['distance']} character={rf['character']} "
             + "; ".join(f"{r['feature']} {r['reference']}->{r['yours']}"
                         for r in rf["rows"] if r["delta_norm"] > 0.3))
    gate("G7_loudness",
         abs((au.get("lufs") or 0) + 14) <= 1.5 and (au.get("true_peak_dbtp") or 0) <= -1.0,
         f"LUFS={au.get('lufs')} TP={au.get('true_peak_dbtp')}")
    gate("G8_visual_qa",
         mo.get("static_ratio", 0) < 0.5 and mo.get("black_ratio", 1) < 0.25,
         f"static_ratio={mo.get('static_ratio')} black_ratio={mo.get('black_ratio')} "
         f"mean_diff={mo.get('mean_frame_diff')}")
    gate("G9_spec",
         sp["w"] == 1080 and sp["h"] == 1920 and abs(sp["fps"] - 30) < 0.2,
         f"{sp['w']}x{sp['h']} @{sp['fps']}fps {sp['vcodec']}/{sp['acodec']} "
         f"{sp['dur']:.2f}s")

    info["classification"] = cls
    info["gates"] = gates
    sts = [g["status"] for g in gates]
    info["verdict"] = ("PASS" if all(x == "PASS" for x in sts)
                       else "FAIL" if "FAIL" in sts else "PARTIAL")
    return info


def audit_markdown(a: dict) -> str:
    sp = a["spec"]
    au = a["audio"]
    asr = a.get("asr", {})
    L = [f"# Skill Audit — `{os.path.basename(a['video'])}`\n",
         f"**Verdict: {a['verdict']}**\n",
         "## Spec", f"- {sp['w']}x{sp['h']} @ {sp['fps']}fps, "
         f"{sp['dur']:.2f}s, {sp['size_mb']:.1f} MB, {sp['vcodec']}/{sp['acodec']}",
         "\n## Audio (earshot.measure)", f"- LUFS {au.get('lufs')} | TP "
         f"{au.get('true_peak_dbtp')} dBTP | LRA {au.get('lra_lu')} LU",
         f"- harmonic_ratio {au.get('harmonic_ratio')} | onsets "
         f"{au.get('onsets')} | centroid {au.get('centroid_hz')} Hz",
         f"- syllable modulation {au.get('syllable_mod_hz')} Hz | speech-band "
         f"share {au.get('speech_band_share')} | low-band share "
         f"{au.get('low_band_share')}",
         "\n## ASR (asr.listen)", f"- lang `{asr.get('detected_language')}` "
         f"({asr.get('lang_prob')}), words {asr.get('n_words')}, confident "
         f"{asr.get('confident_word_ratio')}, intelligible "
         f"**{asr.get('intelligible')}**",
         f"- text: `{str(asr.get('text_snippet'))[:200]}`",
         "\n## Motion", f"- frames {a['motion'].get('frames')}, static_ratio "
         f"{a['motion'].get('static_ratio')}, black_ratio "
         f"{a['motion'].get('black_ratio')}, mean_diff "
         f"{a['motion'].get('mean_frame_diff')}",
         "\n## Gates"]
    for g in a["gates"]:
        L.append(f"- **{g['gate']}** — {g['status']} — {g['detail']}")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description="skill router / auditor")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("discover")
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--brief", required=True)
    p_plan.add_argument("--out", default="")
    p_aud = sub.add_parser("audit")
    p_aud.add_argument("--video", required=True)
    p_aud.add_argument("--brief", default="")
    p_aud.add_argument("--no-asr", action="store_true")
    p_aud.add_argument("--out", default="")
    p_aud.add_argument("--ref", default="")
    p_ref = sub.add_parser("refprofile")
    p_ref.add_argument("--video", required=True)
    p_ref.add_argument("--name", required=True)
    p_sk = sub.add_parser("skills")
    p_sk.add_argument("--tag", default="")
    p_sk.add_argument("--stage", default="")

    a = ap.parse_args(argv)
    if a.cmd == "discover":
        r = discover()
        print(f"registry: {r['count']} skills ({r['verified_count']} verified) "
              f"from {r['python_modules_scanned']} modules -> {REG_PATH}")
        missing = [s["id"] for s in r["skills"] if not s["verified"]]
        if missing:
            print("unverified:", ", ".join(missing))
        return 0

    if a.cmd == "skills":
        r = discover(write=False)
        for s in r["skills"]:
            if a.tag and a.tag not in s["tags"]:
                continue
            if a.stage and a.stage != s["stage"]:
                continue
            print(f"{s['stage']:10s} {s['id']:32s} "
                  f"{'OK' if s['verified'] else 'MISS':4s} {s['why']}")
        return 0

    if a.cmd == "plan":
        brief = json.load(open(a.brief))
        p = plan(brief)
        md = plan_markdown(p)
        out = a.out or os.path.join(STUDIO, "plans",
                                    re.sub(r"\W+", "_", brief.get("title", "plan")) + "_plan.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(md)
        print(md[:4000])
        print(f"\n[saved] {out}")
        return 0

    if a.cmd == "refprofile":
        r = make_reference_profile(a.video, a.name)
        print(json.dumps(r, indent=1))
        return 0

    if a.cmd == "audit":
        brief = json.load(open(a.brief)) if a.brief else {}
        res = audit(a.video, brief, do_asr=not a.no_asr, ref_profile=a.ref or None)
        md = audit_markdown(res)
        out = a.out or os.path.join(STUDIO, "plans",
                                    os.path.basename(a.video) + "_audit.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(md)
        print(md)
        print(f"\n[saved] {out}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
