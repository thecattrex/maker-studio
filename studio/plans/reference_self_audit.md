# Skill Audit — `sample.mov`

**Verdict: FAIL**

## Spec
- 1080x1920 @ 30.0fps, 15.37s, 32.1 MB, hevc/aac

## Audio (earshot.measure)
- LUFS -14.6 | TP -0.9 dBTP | LRA 5.2 LU
- harmonic_ratio 0.221 | onsets 116 | centroid 1296 Hz
- syllable modulation 7.44 Hz | speech-band share 0.643 | low-band share 0.042

## ASR (asr.listen)
- lang `hi` (0.577), words 15, confident 0.933, intelligible **True**
- text: `ये नबूल सक्ता तुमे शोभा नहीं देगी यूध करना तुमहारा कर्टंगे है पार शक्तू उटाओ`

## Motion
- frames 77, static_ratio 0.211, black_ratio 0.039, mean_diff 10.32

## Gates
- **G1_speech_present** — PASS — harmonic_ratio=0.221 lra=5.2 -> speech-led mix
- **G2_dialogue_decodable** — PASS — ASR words=15 confident=0.933 text='ये नबूल सक्ता तुमे शोभा नहीं देगी यूध करना तुमहारा कर्टंगे है पार शक्तू उटाओ'
- **G5_real_music** — PASS — harmonic_ratio=0.221
- **G6_reference_match** — PASS — style distance=0.0 character=speech_like 
- **G7_loudness** — FAIL — LUFS=-14.6 TP=-0.9
- **G8_visual_qa** — PASS — static_ratio=0.211 black_ratio=0.039 mean_diff=10.32
- **G9_spec** — PASS — 1080x1920 @30.0fps hevc/aac 15.37s