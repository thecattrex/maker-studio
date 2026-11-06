#!/usr/bin/env python3
"""No-prompt encoded-master ASR for Baby Driver Style 2 movie-focus v2.
Run after run_encoded_qa.py. The first ASR segment may merge two short Baby lines;
acceptance is four dialogue lines, not an arbitrary ASR segment count.
"""
from __future__ import annotations

import json
import re
import sys
import wave
from pathlib import Path

sys.path.insert(0, "/var/tmp/baby2_pydeps")
import numpy as np  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

OUT = Path(__file__).resolve().parent
WAV = Path("/var/tmp/style2_baby_driver_v2/qa/encoded_full.wav")
MODEL = Path("/var/tmp/baby2_hf/faster-whisper-small.en")
DIALOGUE_DUR = 10.8
ACT1_DUR = 12.2


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.lower().replace("i'm", "im"))


def segments(model, audio):
    raw, _ = model.transcribe(audio, language="en", beam_size=3, best_of=3,
                              word_timestamps=True, condition_on_previous_text=False,
                              vad_filter=False)
    out = []
    for s in raw:
        out.append({
            "start": float(s.start), "end": float(s.end), "text": s.text.strip(),
            "avg_logprob": float(s.avg_logprob),
            "words": [{"start": float(w.start), "end": float(w.end),
                       "word": w.word, "probability": float(w.probability)}
                      for w in (s.words or [])],
        })
    return out


def main() -> None:
    with wave.open(str(WAV), "rb") as w:
        sr = w.getframerate()
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    model = WhisperModel(str(MODEL), device="cpu", compute_type="int8",
                         cpu_threads=1, num_workers=1, local_files_only=True)
    dialogue = segments(model, audio[:int(DIALOGUE_DUR * sr)])
    act1 = segments(model, audio[:int(ACT1_DUR * sr)])
    full = segments(model, audio)
    dialogue_text = norm(" ".join(s["text"] for s in dialogue))
    act1_text = norm(" ".join(s["text"] for s in act1))
    tokens = dialogue_text.split()
    no_next_line = all(x not in act1_text for x in ["chauffeur", "show fur", "oh like"])
    checks = {
        "i_dont_know_if_i_ever_get_off": all(t in tokens for t in ["dont", "know", "ever", "off"]),
        "they_call_i_go_you_know": all(t in tokens for t in ["they", "call", "go", "know"]),
        "so_what_is_it_you_do": all(t in tokens for t in ["what", "do"]),
        "im_a_driver": "driver" in tokens,
        "no_fifth_line_or_chauffeur": no_next_line,
    }
    passed = all(checks.values())
    report = {
        "passed": passed,
        "method": "faster-whisper small.en; no prompt; condition_on_previous_text=false; vad_filter=false",
        "dialogue_duration_s": DIALOGUE_DUR,
        "act1_duration_s": ACT1_DUR,
        "dialogue_segments": dialogue,
        "act1_segments_including_music_pickup": act1,
        "dialogue_normalized_text": dialogue_text,
        "act1_normalized_text": act1_text,
        "checks": checks,
        "expected_clean_lines": 4,
        "note": "The two short opening Baby lines may appear as one ASR segment. The 1.4 s reaction bridge must not contain Deborah's offscreen chauffeur line.",
        "full_master_segments": full,
        "post_drop_note": "Post-drop words belong to the continuous real song; Act 2 contains no source-film dialogue/audio.",
    }
    (OUT / "encoded_asr.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "full_master_segments"}, indent=2))
    print("FULL MASTER ASR:")
    for s in full:
        print(f"{s['start']:.2f}-{s['end']:.2f} {s['text']}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
