# Skill Audit — `Krishna_PrintReveal_Bhajan_9x16.mp4`

**Verdict: FAIL**

## Spec
- 1080x1920 @ 30.0fps, 15.32s, 14.3 MB, h264/aac

## Audio (earshot.measure)
- LUFS -16.1 | TP -5.2 dBTP | LRA 0.8 LU
- harmonic_ratio 0.824 | onsets 94 | centroid 1336 Hz
- syllable modulation 6.45 Hz | speech-band share 0.617 | low-band share 0.086

## ASR (asr.listen)
- lang `en` (0.346), words 0, confident 0.0, intelligible **False**
- text: ``

## Motion
- frames 77, static_ratio 0.289, black_ratio 0.026, mean_diff 4.4

## Gates
- **G1_speech_present** — FAIL — harmonic_ratio=0.824 lra=0.8 -> SONG-led mix (dialogue hi nahi / dab gaya)
- **G2_dialogue_decodable** — FAIL — ASR words=0 confident=0.0 text=''
- **G5_real_music** — PASS — harmonic_ratio=0.824
- **G6_reference_match** — FAIL — style distance=0.417 character=song_like true_peak_dbtp -0.9->-5.2; lra_lu 5.2->0.8; harmonic_ratio 0.221->0.824
- **G7_loudness** — FAIL — LUFS=-16.1 TP=-5.2
- **G8_visual_qa** — PASS — static_ratio=0.289 black_ratio=0.026 mean_diff=4.4
- **G9_spec** — PASS — 1080x1920 @30.0fps h264/aac 15.32s