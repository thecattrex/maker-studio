# Music asset audit — 2026-10-31

## Verified current reusable Type-2 music
- `MUSIC_FINAL/C2_ComedyToyBand.mp3` is the selected track: the recent accepted Type-2 manifests EP30–EP34 reference `/home/user/studio/type2/assets/c2_48.wav`.
- Decoded `c2_48.wav` and `C2_ComedyToyBand.mp3` to 48 kHz stereo PCM: same duration (16.1455 s), RMS/peak and correlation 1.0000. They are the same musical master in two useful formats. Keep the MP3 master and WAV mixer asset.
- `MUSIC/C2_ComedyToyBand.mp3` is a byte-identical copy of the `MUSIC_FINAL` C2 MP3 (SHA-256 checked); it is redundant.
- Type 1 and Type 3 specs say no background music; Type 3 narration audio is kept separately.
- `studio/type2/TYPE2_SPEC.md` is newer than the old QKThr/67% lines in `studio/SPEC.md`; master SPEC was corrected to C2/17% plus the phrase/chicken recipe.

## Removed after verification
- Unused audition alternatives not referenced by accepted current manifests: A1, A2, B1, B2 and C1 tracks in `MUSIC/` and `MUSIC_FINAL/`.
- `MUSIC_FINAL/00_AUDITION_4_tracks.mp3` (comparison mix, not a production bed).
- Old QKThr MP3 and 30-second preview; the older QKThr/67% prototype settings were superseded by C2 in the newer locked Type-2 spec.
- Duplicate `MUSIC/C2_ComedyToyBand.mp3`.
- Removed 12 files total; **8,197,552 bytes (7.82 MiB)** freed.

## Preserved
- `MUSIC_FINAL/C2_ComedyToyBand.mp3` and `studio/type2/assets/c2_48.wav`.
- All narration MP3s, reference audio, SFX library, `got_this.wav` / `got_this_clean.wav`, chicken video/scream, and source-code/mix/config/spec files.

Some legacy experiment configs under `studio/clips/` and `studio/trial/sfx_map.json` still contain old QKThr/C1 paths and volumes. They are historical prototypes, not current makers; do not run them unchanged. The canonical Type-2 path is `studio/type2/build.py` + `mix.py` + `config.json` (C2 bed). No listening/audition or rights-clearance claim is made; this was a code/config/manifest, hash and decoded-audio identity audit.
