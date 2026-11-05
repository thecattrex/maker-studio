# Style A — Permanent Correction Log

This file stores **user-approved corrections**, not guesses made by the editor. Scope is Style A unless a row explicitly says otherwise. A correction becomes reusable only when it is written here and, where possible, linked to a plan check or render QA check in `rules.json`.

| Date | Correction / accepted rule | Verification for later edits |
|---|---|---|
| 2026-11-05 | **TDK v1 is the reference rule.** Use shot-first planning; do not chase a cut count and then repeatedly fill it with a small shot pool. | Plan review: shot coverage, uniqueness, motion and dialogue mapping before render. |
| 2026-11-05 | **Dialogue must show the real speaker on camera.** No muted talking face; mouth movement must be natural and visible where the line is spoken. | Dedicated dialogue-shot mapping plus frame contact sheet; automatic face metrics alone are not sufficient. |
| 2026-11-05 | **Freeze is zero tolerance.** Every shot needs visible movement. | Decode/frame-uniqueness scan plus visual contact-sheet review. |
| 2026-11-05 | **One song, continuous.** Do not fix a flat edit by adding or changing songs; fix section choice, pacing, dialogue pockets and musical response. | Plan validator permits one logical song; audio QA checks contour and beat alignment. |
| 2026-11-05 | **Credits/names/source artifacts are zero.** | Source-selection review and final-frame inspection. |
| 2026-11-05 | **Ending must be designed, not abrupt.** | Plan and final-frame review before delivery. |

## How a new correction is saved

1. Record the exact accepted correction and its scope in this file.
2. Turn it into a deterministic check in `rules.json` / `validate_plan.py` when it can be measured.
3. If human viewing is necessary (for example, actual speaker visibility), keep it as an explicit contact-sheet gate instead of pretending an unreliable detector solved it.
4. Commit the correction together with the relevant plan/code change. Do not commit footage, masters, songs, credentials or Drive-only manifests.
