#!/usr/bin/env python3
"""Separate full-length EP6 source audio into voice/vocal and accompaniment stems.
Model inference only; no source files are deleted. 48 kHz final mixing is done later.
"""
import os, subprocess
import numpy as np
import soundfile as sf
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(ROOT, "assets", "ep6")
RAW = os.path.join(ASSET, "raw_audio")
OUT = os.path.join(ASSET, "stems")
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
SOURCES = [
    ("clip3", "/home/user/dl/src/tiktok/tt_6863209571322744070.mp4"),
    ("clip5", "/home/user/dl/src/tiktok/tt_7418606752553356587.mp4"),
    ("clip2", "/home/user/dl/src/imgur/b0wKmlw.mp4"),
    ("clip4", "/home/user/dl/src/tiktok/tt_7464233129004502318.mp4"),
    ("clip1", "/home/user/dl/src/tiktok/tt_6702952481954991366.mp4"),
]
FF = "/tmp/vidtools/ffmpeg"
for name, src in SOURCES:
    raw = os.path.join(RAW, name + "_full.wav")
    if not os.path.exists(raw):
        subprocess.run([FF, "-hide_banner", "-v", "error", "-y", "-i", src,
                        "-vn", "-ac", "2", "-ar", "44100", raw], check=True)

model = get_model("htdemucs")
model.cpu().eval()
for name, _src in SOURCES:
    raw = os.path.join(RAW, name + "_full.wav")
    outdir = os.path.join(OUT, name)
    os.makedirs(outdir, exist_ok=True)
    vocal_out = os.path.join(outdir, "vocals.wav")
    accomp_out = os.path.join(outdir, "accompaniment.wav")
    if os.path.exists(vocal_out) and os.path.exists(accomp_out):
        print("SKIP", name)
        continue
    audio, sr = sf.read(raw, dtype="float32", always_2d=True)
    if sr != model.samplerate:
        raise RuntimeError(f"{name}: expected {model.samplerate}, got {sr}")
    # Demucs uses (channels, samples), stereo 44.1 kHz.
    wav = torch.from_numpy(audio.T.copy())
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std()
    wav = (wav - mean) / (std + 1e-8)
    with torch.inference_mode():
        pred = apply_model(model, wav[None], device="cpu", shifts=0,
                           split=True, overlap=0.25, progress=True)[0]
    pred = pred * std + mean
    # htdemucs source order: drums, bass, other, vocals.
    vocals = pred[model.sources.index("vocals")].cpu().numpy().T
    accompaniment = pred[[i for i, s in enumerate(model.sources) if s != "vocals"]].sum(0).cpu().numpy().T
    sf.write(vocal_out, vocals, sr, subtype="PCM_16")
    sf.write(accomp_out, accompaniment, sr, subtype="PCM_16")
    print("DONE", name, len(audio)/sr, "s; stems:", vocal_out, accomp_out)
