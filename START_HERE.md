# MAKER CHAT — PORTABLE HANDOFF / START HERE

**Pack date:** 2026-10-31 (Asia/Kolkata)  
**Use:** Upload this ZIP into a new Arena chat and ask the assistant to read this file first, then inspect the bundled `studio/` project. This file is the operating handoff; the bundled specs and code are the detailed source of truth.

## What this pack is

This is a portable copy of the reusable video-maker workspace and its operating knowledge. It is not a literal copy of the Arena chat thread, account settings, connected apps, or conversation UI. The new assistant should use this pack to continue without asking the user to explain the maker workflow again.

## First actions in a new chat

1. Read this `START_HERE.md` completely.
2. Inspect `studio/SPEC.md`, `studio/TYPE2_SPEC.md` (inside `studio/type2/`), `studio/type2/README.md`, `studio/type2/LEARNINGS.md`, and the relevant engine files before making changes.
3. If code/assets are needed, unpack/copy the bundled `studio/` and `assets/fonts/` into the new workspace while preserving the paths. The archive omits generated caches and source-video downloads by design; create only the assets needed for the new task.
4. Do not automatically start a pending or cancelled job. Check the **Current status** section below.
5. Work in Hinglish unless the user requests another language. Do not make the user restate these rules.

## Permanent user preferences and guardrails

- Reply in **Hinglish**. Be direct and useful; do not make routine clip-approval checkpoints.
- For a new video task, research topics/scenes yourself using current evidence and cite current claims. View estimates are signals, never guarantees.
- Keep the three formats separate: **Type 1, Type 2 and Type 3 each use their own engine, layout, settings and audio rules.** Never transfer settings between types.
- The user's deliverable is an edited video, not raw footage plus a text overlay. Hook, pacing, captions, impact text and frame treatment matter.
- Proactively screen footage for AI/synthetic-looking or manipulated appearance. Review temporal action, not only a thumbnail. If uncertain, flag uncertainty; do not call footage authentic or claim forensic verification.
- Avoid severe injury/gore, unnecessary zoom/speed changes and unsupported claims about audio, rights, or review.
- Keep source-ID history and general lessons. For cleanup, remove genuinely episode-specific media/review artifacts when asked; preserve reusable specs, code, settings, assets, positive lessons and source-ID history. Avoid retaining whole episodes unnecessarily.
- **Do not touch Google Drive unless the user explicitly mentions Drive.** Local output is the default. Do not upload, replace, trash, or reorganize Drive files on implication alone.
- Do not touch `/home/user/uploads` unless explicitly requested.
- If a platform blocks a source, **do not bypass access controls, DRM, login restrictions, or platform blocks**. Do not obtain unofficial browser bots or evade restrictions. Use normally accessible official/authorized sources or ask the user for permitted files. No browser-bot tool was available in the source session.
- If a major ambiguity affects deletion, permissions, source rights, or output scope, ask one concise clarifying question; otherwise proceed.

## Canonical format guidance

### Type 1 — continuous movie scene

- The intended edit is one continuous scene with no added narration or montage; the film's own internal cuts are fine. A short hook may show the peak first, then replay the scene from its lead-in, as specified in `studio/SPEC.md` and `studio/t1.py`.
- Text treatment uses a persistent header, action captions and impact words. Preserve the movie's own audio; the user may specify English original audio for a particular job.
- **Important unresolved conflict:** `studio/SPEC.md` says rounded card + same-frame blurred backdrop, while current `studio/t1.py` lays video into a 9:10 band between black top/bottom bands. The accepted-reference layout must be checked against the actual reference videos before any Type-1 render; do not silently choose one. Reference IDs in the spec: `_6HF-smeZvc` and `zzY9iXVh5IA`.
- The general master spec mentions Hindi dub for Type 1. A later, task-specific instruction requested English movie audio for four 20–25 s Type-1 edits; that job was then explicitly put aside. Do not treat it as an active task or a permanent default. If the user reopens it, follow the then-current instruction and do not bypass source blocks.

### Type 2 — ranking / fails

- Read `studio/type2/TYPE2_SPEC.md` and `studio/type2/README.md` first. The reusable builder is `studio/type2/build.py` + `studio/type2/mix.py` + shared config. Historical episode-specific build scripts (including EP33/34 builders) are not canonical templates.
- The user values correct moment/label matching, source-audio checks, real temporal scene screening, and avoiding suspicious AI-looking footage. Type-2 music/SFX/phrase/chicken rules are recorded in the spec.
- Before choosing a source, check `studio/type2/SOURCE_ID_HISTORY.json` plus available episode manifests, and append selected/replaced IDs to the central history after a final is made.

### Type 3 — narration explainer

- `studio/t3.py` is the canonical Type-3 engine. The accepted reference project is `studio/projects/inception/` (Trial 3). Type 3 uses its own 1080×1920 canvas/content band, captions, Hindi narration and **no background music** as detailed in `studio/SPEC.md` and project settings. Do not transfer Type-2 music or interstitials into it.

## Build and QA workflow

- Read the relevant type's spec and engine before editing; inspect the relevant accepted reference when the spec/code disagree.
- Discover and evaluate source scenes; verify the exact action window and audio stream. For suspicious visuals, sample a sequence of frames across the action.
- Source provenance, rights clearance and platform availability are separate questions. Never claim a source is rights-cleared or AI-free unless that is actually established.
- Use the correct engine only. Render one process at a time; inspect captions, framing, timing, source audio and full-file decode. Keep QA claims limited to checks actually performed.
- Present the final requested artifact. Do not upload it to Drive unless explicitly asked.
- `studio/bootstrap.sh` describes dependency setup. Environment packages/binaries themselves are not included in the ZIP.

## Current status / do not resume without request

- **The four-movie Type-1 edit request is parked/cancelled.** The user said to leave it and asked for this maker handoff instead. No movie edits were rendered.
- During that research, a shortlist was gathered from reported Netflix 2026 Top-10 view counts through 25 Oct: *Swapped* 144.9M, *War Machine* 128.4M, *Apex* 118.0M, and *The Rip* 114.7M. These are streaming-view signals, not predictions for Shorts. Source: https://screenrant.com/netflix-movies-2026-most-watched/ . Do not resume unless asked.
- **EP35 is complete on Drive, but its local episode bundle was intentionally deleted to save space.** Local EP35 final, contact sheet, source bank, source clips, candidates, plan/config and render caches were removed. Its source-ID history and general Type-2 lessons remain in the bundled history/spec.
- The active EP35 Drive copy was not deleted by the cleanup. ID: `1CCsqJ9OfIl0WfKeJ1GJT2B9ozcGUId8h`. Do not modify or delete it unless the user explicitly asks for a Drive action.
- The previous EP35 Drive copy was moved to Trash during the earlier approved replacement. No Drive action is currently pending.

## Key reusable paths

- `studio/SPEC.md` — master type map and accepted locked decisions.
- `studio/MOTION_AND_TOOL_ROUTING.md` — mandatory playbook for applying camera choreography, velocity transitions, `.cube` cinema LUTs, HyperFrames/Remotion motion overlays, and `Openverse + earshot + Real-SFX` sound design across videos.
- `studio/UPGRADE_HANDOFF_LOG.md` — complete chronological record of all hybrid/cloud studio upgrades (`Phases 1–8+`).
- `studio/t1.py` — Type-1 engine; see unresolved layout note above.
- `studio/render.py`, `studio/templates.py`, `studio/textkit.py`, `studio/run.py` — shared rendering, text, and CLI.
- `studio/t3.py` — Type-3 engine.
- `studio/type2/TYPE2_SPEC.md`, `README.md`, `LEARNINGS.md`, `SOURCE_ID_HISTORY.json` — Type-2 rules and source record.
- `studio/type2/build.py`, `mix.py`, `config.json`, `plan.json` — reusable Type-2 path.
- `studio/type2/assets/c2_48.wav`, `scream48.wav`, `studio/trial/sfx/` — retained reusable audio assets.
- `assets/fonts/` — bundled fonts referenced by the specs/code.
- Generated `work/`, `cache/`, render outputs and original source clips are intentionally not part of this pack.
