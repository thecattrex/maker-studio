# A–Z workspace audit and cleanup — 2026-10-31

## Result

A full local workspace pass was completed under the user's rule: delete only verified disposable material; preserve reusable maker/settings, positive lessons, source-ID history, user assets, and anything uncertain. **Drive finals and `/home/user/uploads` were not touched. No video build, render, or upload was run.**

### Removed in this pass

- **84 files / 31,469,958 bytes (~30.01 MiB)**. The first 83 removals totaled 31,469,949 bytes; the last was a 9-byte file whose contents were literally `Not Found`.
- Cleared the regenerable pip download/index cache (~29.6 MB); removed its empty directory tree. Kept `.deno` (~92 MiB) because it is the working Deno runtime, not safely disposable project scratch.
- Removed saved TikTok/profile HTML and an EP28/29 candidate-search JSON after confirming selected source IDs remain in episode records.
- Removed Type 2 candidate metadata/search outputs, download/build/render/audio logs, and review-only sheets. All 19 available EP15–EP34 source manifests remain intact; together they hold 74 selected clip IDs. Earlier episode progress notes, specs, configs and plans remain too.
- Removed an unreferenced tiny black-frame MP4 cache. Kept the referenced `studio/cache/bar.jpg` generator/cache path.
- Removed `/home/user/dl/TYPE2_SPEC.md` only after comparing it with current `/home/user/studio/type2/TYPE2_SPEC.md`: the current spec already carries forward the reusable selection, audio, QA, timing, and source guidance. The older file's one-off deliverable record was stale; no Drive item was changed.
- Removed two old review/contact sheets (Type 2 sample sheet and SFX contact sheet). The underlying reusable SFX audio, SFX manifest/map, and trial SFX library were preserved.
- Removed `/home/user/ffmpeg-static.tar.xz` after verifying it was a failed 9-byte `Not Found` download.
- Also pruned six empty directories (`MUSIC`, empty candidate/cache/staging folders); the source-ID-like `test_xvmwObWgeiM` directory's ID remains documented in the EP19 builder and manifest. No non-empty directory was removed.

The exact deleted file paths and byte sizes are recorded in `A_Z_CLEANUP_REMOVED_2026-10-31.tsv`.

## Verified preserved

- `/home/user/uploads` and all Drive finals/permissions.
- Current C2 master and engine WAV, all retained SFX, “I got this” audio, chicken/scream assets, narration, Type 3 reference audio, fonts, active project data, scripts, specs, configs/plans, and prior progress/source records.
- All Type 2 builder scripts and episode-specific configs/plans were kept because they may still contain useful logic or older source history; their redundancy was not proven and their storage cost is small. This includes the EP33/34 one-off builder, which remains **non-canonical** because it omits the recurring phrase/chicken workflow.
- Root candidate-generation scripts were kept because they contain source IDs and/or potentially reusable selection logic. They are not proven to be current workflow tools.
- Old description drafts were retained as historical text, but marked **do not copy for current videos**: they name an old music track, include unverified generic claims, and one includes a placeholder email.
- Root `WORKSPACE.md` and `TODO.md` were marked as historical snapshots so their stale paths/settings are not mistaken for current instructions. Current authority is `FORMAT_MEMORY.md`, `SPEC.md`, and `type2/TYPE2_SPEC.md`.

## Remaining footprint

The workspace is approximately **117 MiB** after cleanup. Main remaining categories are `.deno` runtime (~92 MiB), `studio` (~8.8 MiB), user uploads (~8.9 MiB), fonts (~5.9 MiB), reusable assets/audio, and preserved project/source-history files. No further removals were made from these categories because they are needed, user-owned, or not proven disposable.

## Verification boundaries / next-safe-use notes

- Parsed all **127 Python source files** in `studio`, `tools`, and the workspace root with Python AST: zero syntax errors. `tools/watch.py --help` also passed. Earlier core maker compilation/import checks passed. This is syntax/CLI verification, not a line-by-line semantic review or successful runtime test of every legacy script.
- Old episode-specific scripts were intentionally retained rather than guessed away.
- The saved candidate HTML, candidate-search files, generated review sheets, and pip cache were disposable; they are not source footage or Drive deliverables.
- Before reusing any legacy config, reconcile deleted QKThr/C1 references and confirm the active Type 2 structure/audio against the current spec. The current Type 2 BGM is C2 at about 17%; the EP33/34 one-off builder is not the canonical audio workflow.
- Before any future Type 1 render, resolve the layout conflict noted in `FORMAT_MEMORY.md` against the accepted reference.
- Per standing instruction, do not resume EP33/34 building/rendering/uploading unless explicitly requested.
