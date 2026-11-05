# Maker Studio — 5 / 90 / 5 Cloud Workflow

## Locked split

- **Sandbox 5%** — writing/planning, looking at frames, small non-render tests and creative verification.
- **GitHub 90%** — GitHub Actions performs the real render/encode/automated QA; the existing public repository permanently versions code, plans, rules and approved corrections.
- **Drive 5%** — final masters and QA sheets. Source footage, songs, masters and credentials are never committed to the public repository.

The workflow is **manual-only** (`workflow_dispatch`). Editing code or saving a rule does not automatically render a video.

## One-time no-video setup verification

```bash
python3 studio/gh_farm.py run \
  --mode setup_check \
  --out-dir /home/user/studio/samples/setup_check
```

This checks runner RAM/CPU/disk, FFmpeg/FFprobe, Python media imports, the Style A engine import and the persistent rule files. It writes `setup_report.json` and explicitly reports `video_rendered: false`.

## Style A cloud render (only when explicitly requested)

The versioned plan contains edit decisions. Large media is supplied separately through URL overrides, so local `/var/tmp/...` paths are not assumed to exist on GitHub.

Example job JSON (replace names/URLs with the actual project values):

```json
{
  "plan_path": "studio/styleA/your_plan.json",
  "source_urls": {
    "a01_bus": "https://example.invalid/path/a01_bus.mp4",
    "d1_dawn": "https://example.invalid/path/d1_dawn.mp4",
    "vox_d1_dawn": "https://example.invalid/path/d1_dawn.wav"
  },
  "song_url": "https://example.invalid/path/song.wav",
  "out_name": "StyleA_master.mp4",
  "correction_id": "optional-versioned-correction-id"
}
```

Run through the existing controller:

```bash
python3 studio/gh_farm.py run \
  --mode stylea_plan \
  --job-file /path/to/job.json \
  --cache-key stylea-project-name \
  --out-dir /home/user/studio/samples/stylea_master
```

The runner:

1. Validates the plan before downloading or rendering.
2. Downloads each URL into a content-addressed asset cache, or reuses an existing cached asset.
3. Auto-detects pre-baked audio dialogue sources and sets the vocal bypass appropriately.
4. Runs the existing `zohair_jigsaw` engine and automated visual/audio QA.
5. Uploads the master, QA sheet, validation report and cloud report as a seven-day GitHub artifact.
6. Arena retrieves the artifact and uploads the approved deliverable to Drive `movies`.

## Corrections and reuse

- Use the **same `--cache-key`** for a project correction to restore its downloaded source/song assets. Use a new key for a different project.
- Save the accepted plan change and correction permanently; do not leave important decisions only in a job payload or chat.
- Record user-approved rules in `studio/styleA/CORRECTIONS.md` and `studio/styleA/rules.json`.
- Run `studio/styleA/validate_plan.py` locally for a fast structural check. Speaker visibility and natural motion still require frame review; the validator does not pretend to solve those visually.
- The current cache prevents repeated **downloads**. It does not falsely claim shot-level or audio-only rerender avoidance; any such correction mode must be implemented and verified separately before being relied upon.
- GitHub Actions caches are ephemeral and subject to GitHub's cache eviction policy. They are a speed optimization, not the master archive. Drive remains the master location.

## Public-repository safety

- No push/PR render triggers; only repository writers can manually dispatch.
- `permissions: contents: read` and one queued render at a time.
- No tokens in job JSON, plans, logs, the repository or correction history.
- No self-hosted runner is required for this setup.
