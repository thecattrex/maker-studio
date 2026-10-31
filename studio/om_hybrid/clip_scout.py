"""clip_scout.py — Multi-Source Free HD Stock & Official 1080p Movie Clip Scout.

Unifies:
  1. OpenMontage's 16 free/public stock footage adapters (`om_hybrid.stock_sources`:
     archive_org, wikimedia, nasa, noaa, esa, jaxa, loc, nara, dareful, coverr,
     mixkit, videvo, pond5_pd, pexels, pixabay_video, unsplash) — WITHOUT needing
     heavy CLIP/PyTorch embeddings.
  2. Official IGN 1080p (`zencoder` + `mediaconvert`) MP4 scene-clip extractor
     for Type-1 movie Shorts when YouTube/IMDb block datacenter IPs.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Any

from .stock_sources import SearchFilters, available_sources, get_source, source_catalog


def list_sources() -> list[dict[str, object]]:
    """Return status catalog of all 16 stock/archive media adapters."""
    return source_catalog()


def search_stock_clips(
    query: str,
    sources: list[str] | None = None,
    per_source: int = 4,
    kind: str = "video",
    min_duration: float | None = 3.0,
    max_duration: float | None = 90.0,
    download_dir: str | None = None,
    max_downloads: int = 3,
) -> list[dict[str, Any]]:
    """Search across available free/stock sources and optionally download top hits."""
    filters = SearchFilters(
        kind=kind,
        min_duration=min_duration,
        max_duration=max_duration,
        per_page=per_source,
    )
    if sources:
        active = [get_source(name) for name in sources if get_source(name).is_available()]
    else:
        active = available_sources()

    hits = []
    downloaded = 0
    for adapter in active:
        try:
            cands = adapter.search(query, filters)
        except Exception:
            continue
        for c in cands[:per_source]:
            row: dict[str, Any] = {
                "clip_id": c.clip_id,
                "source": c.source,
                "source_url": c.source_url,
                "download_url": c.download_url,
                "width": c.width,
                "height": c.height,
                "duration": c.duration,
                "license": c.license,
                "tags": c.source_tags[:140],
                "local_path": None,
            }
            if download_dir and downloaded < max_downloads and c.download_url:
                ext = ".mp4" if c.kind == "video" else ".jpg"
                dest = Path(download_dir) / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', c.clip_id)}{ext}"
                try:
                    adapter.download(c, dest)
                    row["local_path"] = str(dest)
                    downloaded += 1
                except Exception as e:
                    row["download_error"] = str(e)
            hits.append(row)
    return hits


def extract_ign_1080p_mp4(ign_video_page_url: str, timeout: int = 15) -> dict[str, Any]:
    """Extract direct 1920x1080 MP4 URLs (both `zencoder` and `mediaconvert`) from an IGN video page."""
    req = urllib.request.Request(ign_video_page_url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    mp4_1080 = sorted(
        set(
            re.findall(
                r"https://assets\.ign\.com/videos/(?:zencoder|mediaconvert)/[^\"'\s<>\\]+?/1920/[^\"'\s<>\\]+?\.mp4",
                html,
            )
        )
    )
    mp4_720 = sorted(
        set(
            re.findall(
                r"https://assets\.ign\.com/videos/(?:zencoder|mediaconvert)/[^\"'\s<>\\]+?/1280/[^\"'\s<>\\]+?\.mp4",
                html,
            )
        )
    )
    return {
        "page_url": ign_video_page_url,
        "mp4_1080p": mp4_1080,
        "mp4_720p": mp4_720,
        "best_mp4": (mp4_1080[0] if mp4_1080 else (mp4_720[0] if mp4_720 else None)),
    }
