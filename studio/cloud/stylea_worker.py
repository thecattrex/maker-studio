"""Cloud runner for portable Style A plans.

The plan stays versioned in Git. Large media stays OUTSIDE Git and is resolved
from explicit URLs into a content-addressed cache. No function in this module
renders until run_stylea_plan() is called by the manually dispatched worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "studio"
if str(STUDIO) not in sys.path:
    sys.path.insert(0, str(STUDIO))

from styleA.validate_plan import validate_plan  # noqa: E402

_AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}
_MEDIA_SUFFIXES = _AUDIO_SUFFIXES | {".mp4", ".mov", ".mkv", ".webm"}


def _is_url(value: str) -> bool:
    return urlsplit(value).scheme in {"http", "https"}


def _suffix_for(url: str, default: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    return suffix if suffix in _MEDIA_SUFFIXES else default


def _cached_fetch(url: str, cache_dir: Path, default_suffix: str) -> tuple[Path, bool]:
    """Fetch once per URL; return (path, cache_hit)."""
    suffix = _suffix_for(url, default_suffix)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    target = cache_dir / f"{digest}{suffix}"
    if target.exists() and target.stat().st_size > 4096:
        return target, True

    # Import lazily to avoid a circular import with hq_worker's mode router.
    from cloud.hq_worker import _fetch_url_resilient

    cache_dir.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    partial.unlink(missing_ok=True)
    _fetch_url_resilient(url, partial)
    if not partial.exists() or partial.stat().st_size <= 4096:
        partial.unlink(missing_ok=True)
        raise RuntimeError("download produced an empty or invalid asset")
    partial.replace(target)
    return target, False


def _load_plan(job: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if isinstance(job.get("plan"), dict):
        plan = job["plan"]
        identity = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return plan, hashlib.sha256(identity).hexdigest()

    rel = job.get("plan_path")
    if not rel or Path(rel).is_absolute():
        raise ValueError("provide either an inline plan object or a repo-relative plan_path")
    candidate = (ROOT / rel).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("plan_path must stay inside the repository") from exc
    raw = candidate.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def _local_locator(value: str) -> Path | None:
    path = Path(value)
    candidates = [path] if path.is_absolute() else [ROOT / path, STUDIO / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _resolve_assets(
    plan: dict[str, Any], job: dict[str, Any], cache_dir: Path
) -> tuple[dict[str, str], Path, dict[str, Any]]:
    source_urls = job.get("source_urls") or {}
    if not isinstance(source_urls, dict):
        raise ValueError("source_urls must be an object keyed by source alias")

    sources: dict[str, str] = {}
    cache_hits = 0
    downloads = 0
    missing: list[str] = []
    for alias, locator in plan["sources"].items():
        url = source_urls.get(alias)
        if url is None and _is_url(locator):
            url = locator
        if url is not None:
            if not isinstance(url, str) or not _is_url(url):
                raise ValueError(f"source_urls[{alias!r}] must be an http(s) URL")
            path, hit = _cached_fetch(url, cache_dir, ".mp4")
            cache_hits += int(hit)
            downloads += int(not hit)
        else:
            local = _local_locator(locator)
            if local is None:
                missing.append(alias)
                continue
            path = local
        sources[alias] = str(path)
    if missing:
        raise FileNotFoundError(
            "no usable asset for source aliases: " + ", ".join(sorted(missing))
            + "; provide source_urls for these aliases"
        )

    song_url = job.get("song_url") or plan.get("song_url")
    song_locator = str(plan.get("song_path") or "")
    if song_url:
        if not _is_url(str(song_url)):
            raise ValueError("song_url must be an http(s) URL")
        song_path, hit = _cached_fetch(str(song_url), cache_dir, ".mp3")
        cache_hits += int(hit)
        downloads += int(not hit)
    elif song_locator and _is_url(song_locator):
        song_path, hit = _cached_fetch(song_locator, cache_dir, ".mp3")
        cache_hits += int(hit)
        downloads += int(not hit)
    else:
        local_song = _local_locator(song_locator) if song_locator else None
        if local_song is None:
            raise FileNotFoundError("song is unavailable; provide song_url for this run")
        song_path = local_song

    return sources, song_path, {
        "cache_dir": str(cache_dir),
        "cache_hits": cache_hits,
        "new_downloads": downloads,
    }


def _out_name(plan: dict[str, Any], job: dict[str, Any]) -> str:
    raw = str(job.get("out_name") or f"{plan.get('name', 'stylea_edit')}.mp4")
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(raw).name)
    if not name.lower().endswith(".mp4"):
        name += ".mp4"
    return name


def run_stylea_plan(job: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Validate, resolve cached assets, render and QA one Style A plan."""
    import multiprocessing

    out_dir.mkdir(parents=True, exist_ok=True)
    plan, plan_hash = _load_plan(job)
    validation = validate_plan(plan)
    (out_dir / "plan_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    if not validation["passed"]:
        raise ValueError("Style A plan validation failed; see plan_validation.json")

    cache_dir = Path(os.environ.get("MAKER_ASSET_CACHE", "/tmp/maker_stylea_cache"))
    work = Path("/tmp/stylea_plan_work")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    sources, song_path, cache_report = _resolve_assets(plan, job, cache_dir)

    dialogue_aliases = {event["src"] for event in plan.get("dialogue_events", [])}
    all_prebaked = bool(dialogue_aliases) and all(
        Path(sources[alias]).suffix.lower() in _AUDIO_SUFFIXES for alias in dialogue_aliases
    )
    prebaked = bool(job.get("prebaked_dialogue", all_prebaked))

    allowed_voice_env = {
        "ZX_VOX", "ZX_VOX_BYPASS", "ZX_VOX_HP", "ZX_VOX_PRES",
        "ZX_VOX_SAT", "ZX_MID", "ZX_GRO",
    }
    requested_env = job.get("voice_env") or {}
    if not isinstance(requested_env, dict):
        raise ValueError("voice_env must be an object")
    unknown_env = sorted(set(requested_env) - allowed_voice_env)
    if unknown_env:
        raise ValueError("unsupported voice_env keys: " + ", ".join(unknown_env))

    old_env = {key: os.environ.get(key) for key in allowed_voice_env}
    for key, value in requested_env.items():
        os.environ[key] = str(value)
    if prebaked:
        os.environ["ZX_VOX_BYPASS"] = "1"

    out_mp4 = out_dir / _out_name(plan, job)
    try:
        from om_hybrid.visual_qa import run_full_qa
        from om_hybrid.zohair_edit import render_zohair_jigsaw_edit

        render_report = render_zohair_jigsaw_edit(
            str(out_mp4),
            sources=sources,
            song_path=str(song_path),
            song_offset_s=float(plan.get("song_offset_s", 0.0)),
            visual_cuts=plan["visual_cuts"],
            dialogue_events=plan.get("dialogue_events", []),
            sfx_events=plan.get("sfx_events", []) or [],
            outro_black_s=float(plan.get("outro_black_s", 0.0)),
        )
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    qa = run_full_qa(
        str(out_mp4),
        expected_size=(1080, 1920),
        min_dur=2.0,
        max_dur=120.0,
        sheet_out=str(out_dir / "qa_sheet.jpg"),
    )
    report = {
        "mode": "stylea_plan",
        "plan_name": plan.get("name"),
        "plan_sha256": plan_hash,
        "correction_id": job.get("correction_id"),
        "runner_cpus": multiprocessing.cpu_count(),
        "prebaked_dialogue": prebaked,
        "asset_cache": cache_report,
        "plan_validation": validation,
        **render_report,
        "qa": qa,
        "note": "Automated QA does not replace the required speaker/motion contact-sheet review.",
    }
    (out_dir / "cloud_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
