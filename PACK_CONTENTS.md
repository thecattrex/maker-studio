# Pack contents and exclusions

## Included

- Reusable studio code, CLI scripts, Type-1/2/3 specifications, learnings, playbooks, configs, project examples and historical text manifests.
- The central Type-2 source-ID history, including EP35's final and replaced IDs.
- Reusable Type-2 series audio (`c2_48.wav`, `scream48.wav`) and the saved SFX library.
- The font files referenced by the maker specifications.
- `START_HERE.md`, which carries the user preferences, current state, guardrails, build/QA workflow, and a map of the project.

## Excluded intentionally

- Original/source movie clips, candidate downloads and other episode media.
- Rendered MP4 deliverables, contact sheets, thumbnails, generated QA frames.
- Regenerable `work/`, `cache/` and `out/` folders.
- Per-project narration MP3s and reference-audio captures; they are episode-specific, not required to understand the maker.
- Temporary files, credentials and git internals.

The new chat should treat missing source media as missing. It must not assume the assets can be recovered by bypassing a platform restriction; use normally accessible official/authorized assets or ask the user for their permitted files.
