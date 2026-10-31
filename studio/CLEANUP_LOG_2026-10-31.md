# Workspace cleanup — 2026-10-31

User-authorized local cleanup only; no Drive files or `/home/user/uploads` were touched.

- Removed 3,896 generated/local episode media and temporary files (359,872,359 bytes, 343.2 MiB).
- By extension: {'.jpg': 3714, '.mp4': 11, '.pyc': 90, '.png': 6, '.ass': 74, '.gif': 1}.
- Removed review/contact/crop JPG/PNG/GIF images from `studio/type2`, `studio/work`, `dl`, root-level frame reviews, and generated candidate-frame folders (`candframes*`, `dense`, `tiktok_*`).
- Removed local episode/source/test MP4s from `dl` and the one-off `studio/type2/afv_crop0_test.mp4`; kept reusable `/home/user/sfx/chicken_face.mp4`. A later A–Z check removed the unreferenced tiny black-frame MP4 cache; it was not used by current code.
- Removed generated `.ass` work overlays and `.pyc` bytecode; source code, JSON plans/configs/manifests, specs, fonts, the selected C2 BGM, SFX, voice/chicken audio, active project metadata, and Drive finals were preserved.
- In a separate verified music cleanup, retained only the current C2 master plus `c2_48.wav` engine asset; removed unused music candidates, audition mix, old QKThr assets, and a byte-identical duplicate. See `studio/MUSIC_CLEANUP_AUDIT.md`.
- Source IDs/URLs/cut windows remain in per-episode manifests, including EP33/34. Their source MP4s will need to be fetched again for a re-render.

## Full A–Z continuation (same date)
- Removed 84 verified cache/candidate/review/log/stale-copy files totaling 31,469,958 bytes (~30.01 MiB), including the regenerated pip download cache, and pruned six empty directories. Exact file list: `studio/A_Z_CLEANUP_REMOVED_2026-10-31.tsv`.
- Kept `.deno` runtime; all 19 EP15–EP34 source manifests, maker scripts/configs/plans, old progress/source records, uploads, fonts, current music/SFX/voice/chicken assets, narration, reference audio and active projects.
- No Drive finals or permissions changed. Full classification and remaining cautions: `studio/A_Z_CLEANUP_AUDIT.md`.
