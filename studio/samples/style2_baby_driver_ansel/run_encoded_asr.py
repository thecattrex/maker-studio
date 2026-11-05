#!/usr/bin/env python3
"""No-prompt encoded-master ASR for Baby Driver Style 2.
Run after run_encoded_qa.py. Expects /var/tmp/style2_baby_driver/qa/encoded_full.wav.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

OUT = Path(__file__).resolve().parent
WAV = Path("/var/tmp/style2_baby_driver/qa/encoded_full.wav")
MODEL = Path("/var/tmp/style3_hf/models--Systran--faster-whisper-small.en/snapshots/d1d751a5f8271d482d14ca55d9e2deeebbae577f")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.lower().replace("i'm", "im"))


def segments(model, audio, **kwargs):
    raw, _ = model.transcribe(audio, language="en", beam_size=3, best_of=3,
                              word_timestamps=True, condition_on_previous_text=False,
                              vad_filter=False, **kwargs)
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
    sys.path.insert(0, "/var/tmp/style3_pydeps")
    from faster_whisper import WhisperModel
    sr, audio = wavfile.read(WAV)
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    else:
        audio = audio.astype(np.float32)
    model = WhisperModel(str(MODEL), device="cpu", compute_type="int8",
                         cpu_threads=1, num_workers=1, local_files_only=True)
    act1_dur = 8.2
    act1 = segments(model, audio[:int(act1_dur * sr)])
    full = segments(model, audio)
    act1_text = norm(" ".join(s["text"] for s in act1))
    checks = {
        "they_call_i_go": all(tok in act1_text.split() for tok in ["they", "call", "go"]),
        "so_what_is_it_you_do": all(tok in act1_text.split() for tok in ["what", "do"]),
        "im_a_driver": "driver" in act1_text.split(),
        "no_partial_fourth_line": "oh like" not in act1_text,
    }
    passed = all(checks.values()) and len(act1) == 3
    report = {
        "passed": passed,
        "method": "faster-whisper small.en; no prompt; condition_on_previous_text=false; vad_filter=false",
        "act1_duration_s": act1_dur,
        "act1_segments": act1,
        "act1_normalized_text": act1_text,
        "checks": checks,
        "expected_clean_lines": 3,
        "full_master_segments": full,
        "post_drop_note": "Any post-drop words are the continuous real song. The renderer does not include source-film dialogue/audio in Act 2.",
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
