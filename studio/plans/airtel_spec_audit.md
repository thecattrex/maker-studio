# Skill Audit — `airtel_SPEC_EkDhaaga_BrandFilm_9x16.mp4`

**Verdict: PASS**

## Spec
- 1080x1920 @ 30.0fps, 14.86s, 6.0 MB, h264/aac

## Audio (earshot.measure)
- LUFS -14.3 | TP -2.2 dBTP | LRA 2.7 LU
- harmonic_ratio 0.886 | onsets 29 | centroid 568 Hz
- syllable modulation 2.15 Hz | speech-band share 0.422 | low-band share 0.215

## ASR (asr.listen)
- lang `en` (0.346), words 0, confident 0.0, intelligible **False**
- text: ``

## Motion
- frames 74, static_ratio 0.37, black_ratio 0.959, mean_diff 2.57

## Gates
- **G1_speech_understanding** — PASS — brief music-led — speech expected nahi (ASR words=0), isliye G1 dialogue gate N/A
- **G5_real_music** — PASS — harmonic_ratio=0.886
- **G7_loudness** — PASS — LUFS=-14.3 TP=-2.2
- **G8_visual_qa** — PASS — static_ratio=0.37 dead_frame_ratio=0.041 mean_luma=7.5 mean_diff=2.57
- **G9_spec** — PASS — 1080x1920 @30.0fps h264/aac 14.86s