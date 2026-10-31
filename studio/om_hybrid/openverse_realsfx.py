"""openverse_realsfx.py — Openverse (5M+ Open Audio / 800M+ Images) + Clipwing Real-SFX Bridge.

Completes the 3-part sound-design stack alongside `Leonxlnx/earshot`:
  1. `Openverse` (`https://api.openverse.org/v1/`): Searches & downloads openly-licensed
     (CC0 / CC-BY) real recorded SFX, music, and images. Uses direct `api.openverse.org`
     on GitHub Cloud runners, with automatic <4s fallback to Openverse's upstream
     Wikimedia Commons + Internet Archive CC catalogs when datacenter IPs block Cloudflare.
  2. `Real SFX` (`Clipwing/skills/skills/real-sfx`, MIT + 78 CC0 `uisfx` cues):
     Reads a video (`find_moments.py`) or HyperFrames composition (`from_hyperframes.py`),
     places sounds on the exact frame (`mix.py --voice-safe --duck`), tunes tonal cues to
     musical key (`tonal.py`), and outputs both `*_sfx.mp4` and a separate `*_sfx_track.wav` stem.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from ._ffmpeg import get_ffmpeg, get_ffprobe
from .sfx_sync import render_synced_sfx

STUDIO_DIR = Path(__file__).resolve().parents[1]
REAL_SFX_DIR = STUDIO_DIR / "real_sfx"
STARTER_LIB_DIR = REAL_SFX_DIR / "starter_lib"
OPENVERSE_LIB_DIR = REAL_SFX_DIR / "openverse_cc0"

USER_AGENT = "MakerStudio-OpenverseClient/1.0 (https://github.com/thecattrex/maker-studio)"


def _http_json(url: str, timeout: float = 4.5, headers: dict[str, str] | None = None) -> dict[str, Any]:
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _safe_slug(text: str, max_len: int = 42) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return (s or "asset")[:max_len]


def _download_asset(url: str, dest_dir: Path, stem: str, default_ext: str) -> str | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    parsed = urllib.parse.urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if not ext or len(ext) > 6:
        ext = default_ext
    out_path = dest_dir / f"{stem}{ext}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as r, open(out_path, "wb") as f:
            shutil.copyfileobj(r, f)
        if out_path.stat().st_size < 512:
            out_path.unlink(missing_ok=True)
            return None
        return str(out_path)
    except Exception:
        out_path.unlink(missing_ok=True)
        return None


def search_openverse_audio(
    query: str,
    license_type: str | None = None,
    limit: int = 6,
    download_dir: str | None = None,
) -> dict[str, Any]:
    """Search Openverse `/v1/audio/` (with automatic Wikimedia + Archive.org CC fallback)."""
    params: dict[str, Any] = {"q": query, "page_size": max(1, min(20, limit))}
    if license_type:
        params["license"] = license_type

    api_url = f"https://api.openverse.org/v1/audio/?{urllib.parse.urlencode(params)}"
    results: list[dict[str, Any]] = []
    backend = "openverse_api"

    try:
        token = os.environ.get("OPENVERSE_ACCESS_TOKEN", "").strip()
        hdrs = {"Authorization": f"Bearer {token}"} if token else None
        data = _http_json(api_url, timeout=4.5, headers=hdrs)
        for it in (data.get("results") or [])[:limit]:
            dl_url = it.get("url") or ""
            alt_files = it.get("alt_files") or []
            if alt_files and isinstance(alt_files[0], dict) and alt_files[0].get("url"):
                dl_url = alt_files[0]["url"]
            results.append(
                {
                    "id": it.get("id"),
                    "title": it.get("title") or query,
                    "creator": it.get("creator") or "unknown",
                    "license": f"{it.get('license', 'cc')}-{it.get('license_version', '')}".strip("-"),
                    "source": it.get("source") or "openverse",
                    "duration_ms": it.get("duration"),
                    "url": dl_url,
                    "foreign_landing_url": it.get("foreign_landing_url"),
                }
            )
    except Exception:
        backend = "openverse_upstream_wikimedia_archive"
        # Upstream 1: Wikimedia Commons Real Audio (3.88M+ tracks indexed by Openverse)
        try:
            core_terms = [
                w for w in re.findall(r"[a-zA-Z0-9]+", query)
                if w.lower() not in {"sound", "sounds", "effect", "effects", "sfx", "audio"}
            ]
            clean_q = " ".join(core_terms) if core_terms else query
            wm_q = urllib.parse.urlencode(
                {
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"filetype:audio {clean_q}",
                    "gsrnamespace": "6",
                    "gsrlimit": str(max(2, limit)),
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime|extmetadata",
                    "format": "json",
                }
            )
            wm = _http_json(f"https://commons.wikimedia.org/w/api.php?{wm_q}", timeout=8.0)
            pages = list((wm.get("query", {}).get("pages") or {}).values())
            for pg in pages[:limit]:
                ii = (pg.get("imageinfo") or [{}])[0]
                meta = ii.get("extmetadata") or {}
                lic = (meta.get("LicenseShortName") or {}).get("value", "CC")
                if ii.get("url"):
                    results.append(
                        {
                            "id": f"wm_{pg.get('pageid')}",
                            "title": pg.get("title", "").replace("File:", ""),
                            "creator": re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "Wikimedia")),
                            "license": lic,
                            "source": "wikimedia_commons",
                            "duration_ms": None,
                            "url": ii["url"],
                            "foreign_landing_url": ii.get("descriptionurl"),
                        }
                    )
        except Exception:
            pass

        # Upstream 2: Internet Archive Open Audio
        if len(results) < limit:
            try:
                ia_q = urllib.parse.urlencode(
                    {
                        "q": f'({query}) AND mediatype:(audio)',
                        "fl[]": ["identifier", "title", "creator", "licenseurl"],
                        "rows": str(max(2, limit - len(results))),
                        "page": "1",
                        "output": "json",
                    },
                    doseq=True,
                )
                ia = _http_json(f"https://archive.org/advancedsearch.php?{ia_q}", timeout=8.0)
                for doc in (ia.get("response", {}).get("docs") or []):
                    ident = doc.get("identifier")
                    if not ident:
                        continue
                    md = _http_json(f"https://archive.org/metadata/{ident}", timeout=6.0)
                    audio_f = next(
                        (
                            f for f in (md.get("files") or [])
                            if str(f.get("name", "")).lower().endswith((".wav", ".mp3", ".ogg", ".flac"))
                        ),
                        None,
                    )
                    if audio_f:
                        results.append(
                            {
                                "id": f"ia_{ident}",
                                "title": doc.get("title") or ident,
                                "creator": str(doc.get("creator") or "Internet Archive"),
                                "license": doc.get("licenseurl") or "public-archive",
                                "source": "internet_archive",
                                "duration_ms": None,
                                "url": f"https://archive.org/download/{ident}/{urllib.parse.quote(audio_f['name'])}",
                                "foreign_landing_url": f"https://archive.org/details/{ident}",
                            }
                        )
            except Exception:
                pass

    if download_dir:
        dpath = Path(download_dir)
        for idx, r in enumerate(results):
            if r.get("url"):
                local_p = _download_asset(r["url"], dpath, f"{idx:02d}_{_safe_slug(r['title'])}", ".ogg")
                r["local_path"] = local_p

    return {"query": query, "backend": backend, "count": len(results), "results": results}


def search_openverse_images(
    query: str,
    license_type: str | None = None,
    limit: int = 6,
    download_dir: str | None = None,
) -> dict[str, Any]:
    """Search Openverse `/v1/images/` (with automatic Wikimedia Commons CC image fallback)."""
    params: dict[str, Any] = {"q": query, "page_size": max(1, min(20, limit))}
    if license_type:
        params["license"] = license_type

    api_url = f"https://api.openverse.org/v1/images/?{urllib.parse.urlencode(params)}"
    results: list[dict[str, Any]] = []
    backend = "openverse_api"

    try:
        token = os.environ.get("OPENVERSE_ACCESS_TOKEN", "").strip()
        hdrs = {"Authorization": f"Bearer {token}"} if token else None
        data = _http_json(api_url, timeout=4.5, headers=hdrs)
        for it in (data.get("results") or [])[:limit]:
            results.append(
                {
                    "id": it.get("id"),
                    "title": it.get("title") or query,
                    "creator": it.get("creator") or "unknown",
                    "license": f"{it.get('license', 'cc')}-{it.get('license_version', '')}".strip("-"),
                    "source": it.get("source") or "openverse",
                    "width": it.get("width"),
                    "height": it.get("height"),
                    "url": it.get("url"),
                    "thumbnail": it.get("thumbnail"),
                }
            )
    except Exception:
        backend = "openverse_upstream_wikimedia"
        wm_q = urllib.parse.urlencode(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": f'filetype:bitmap {query}',
                "gsrnamespace": "6",
                "gsrlimit": str(max(2, limit)),
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "format": "json",
            }
        )
        wm = _http_json(f"https://commons.wikimedia.org/w/api.php?{wm_q}", timeout=8.0)
        for pg in list((wm.get("query", {}).get("pages") or {}).values())[:limit]:
            ii = (pg.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            if ii.get("url"):
                results.append(
                    {
                        "id": f"wm_{pg.get('pageid')}",
                        "title": pg.get("title", "").replace("File:", ""),
                        "creator": re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "Wikimedia")),
                        "license": (meta.get("LicenseShortName") or {}).get("value", "CC"),
                        "source": "wikimedia_commons",
                        "width": ii.get("width"),
                        "height": ii.get("height"),
                        "url": ii["url"],
                        "thumbnail": ii.get("url"),
                    }
                )

    if download_dir:
        dpath = Path(download_dir)
        for idx, r in enumerate(results):
            if r.get("url"):
                r["local_path"] = _download_asset(r["url"], dpath, f"{idx:02d}_{_safe_slug(r['title'])}", ".jpg")

    return {"query": query, "backend": backend, "count": len(results), "results": results}


# Starter role -> SFX mapping so `real-sfx` always has a rich multi-role library ready immediately
_STARTER_SEEDS: list[tuple[str, str, str]] = [
    ("whoosh", "whoosh_swell.wav", "pro_whoosh_big/swell"),
    ("whoosh", "whoosh_windy.wav", "pro_whoosh_big/windy"),
    ("whoosh", "whoosh_bamboo.wav", "fit/whoosh.short/bamboo_swish"),
    ("whoosh", "swish_blade.wav", "swish/blade"),
    ("whoosh", "swish_bright.wav", "swish/bright"),
    ("whoosh", "swish_cane.wav", "swish/cane"),
    ("whoosh", "swish_soft.wav", "swish/soft"),
    ("whoosh", "whoosh_tonal.wav", "pro_whoosh_big/tonal"),
    ("hit", "hit_punch.wav", "cut_hit/punch"),
    ("hit", "hit_kick.wav", "cut_hit/kick"),
    ("hit", "hit_bamboo.wav", "fit/hit/bamboo_tok"),
    ("hit", "sting_glass.wav", "logo_sting/whoosh_glass"),
    ("riser", "riser_air.wav", "pro_riser/air_gate"),
    ("riser", "riser_dark.wav", "riser/dark"),
    ("drop", "subdrop_quick.wav", "pro_sub_drop/quick"),
    ("drop", "downlifter_sink.wav", "downlifter/sub_sink"),
    ("pop", "pop_lip.wav", "fit/pop/lip_pop"),
    ("pop", "pop_plop.wav", "fit/pop/mouth_plop"),
    ("click", "click_floss.wav", "fit/click/floss_lid"),
    ("click", "click_switch.wav", "fit/snap/switch_flip"),
    ("chime", "bell_small.wav", "fit/bell/small_bell"),
    ("glitch", "glitch_hit.wav", "glitch/hit"),
]


def ensure_realsfx_ready(install_uisfx: bool = True) -> dict[str, Any]:
    """Ensure `studio/real_sfx` has FFmpeg+FFprobe in PATH, populated starter library, optional CC0 `uisfx`, and fresh index."""
    ff_bin = Path(get_ffmpeg()).parent
    get_ffprobe()
    env = os.environ.copy()
    env["PATH"] = f"{ff_bin}:{env.get('PATH', '')}"

    # 1. Seed starter_lib if empty
    catalog_entries = []
    for role, fname, sfx_id in _STARTER_SEEDS:
        f_out = STARTER_LIB_DIR / role / fname
        if not f_out.exists():
            render_synced_sfx(sfx_id, str(f_out))
        catalog_entries.append({"file": f"{role}/{fname}", "type": role, "source": sfx_id})
    (STARTER_LIB_DIR / "catalog.json").write_text(json.dumps(catalog_entries, indent=2))

    # 2. Run setup.py init --library ... [--uisfx] --index --force
    cmd = [
        sys.executable,
        str(REAL_SFX_DIR / "scripts" / "setup.py"),
        "init",
        f"--library=main={STARTER_LIB_DIR}",
        "--index",
        "--force",
    ]
    if OPENVERSE_LIB_DIR.is_dir() and any(OPENVERSE_LIB_DIR.rglob("*.*")):
        cmd.append(f"--library=openverse={OPENVERSE_LIB_DIR}")
    if install_uisfx and shutil.which("npm"):
        cmd.append("--uisfx")

    subprocess.run(cmd, cwd=str(REAL_SFX_DIR), env=env, check=True)
    idx_file = REAL_SFX_DIR / "library_index.json"
    idx_data = json.loads(idx_file.read_text()) if idx_file.exists() else {}
    return {
        "ready": idx_file.exists(),
        "indexed_sounds": idx_data.get("count", 0),
        "uisfx_installed": (REAL_SFX_DIR / "vendor" / "node_modules" / "uisfx" / "manifest.json").exists(),
    }


def auto_sound_design_video(
    video_path: str,
    out_mp4: str,
    voice_safe: bool = True,
    duck: bool = True,
    hyperframes_dir: str | None = None,
) -> dict[str, Any]:
    """Run Clipwing `real-sfx` end-to-end: detect frame moments -> suggest cues -> mix MP4 + separate SFX WAV stem."""
    status = ensure_realsfx_ready(install_uisfx=True)
    ff_bin = Path(get_ffmpeg()).parent
    env = os.environ.copy()
    env["PATH"] = f"{ff_bin}:{env.get('PATH', '')}"

    work = Path(tempfile.mkdtemp(prefix="realsfx_work_"))
    abs_video = str(Path(video_path).resolve())
    abs_out = str(Path(out_mp4).resolve())
    Path(abs_out).parent.mkdir(parents=True, exist_ok=True)

    try:
        moments_dir = work / "moments"
        cues_json = work / "cues.json"
        if hyperframes_dir:
            mj = work / "hf_moments.json"
            subprocess.run(
                [sys.executable, "scripts/from_hyperframes.py", str(Path(hyperframes_dir).resolve()), "--video", abs_video, "--out", str(mj)],
                cwd=str(REAL_SFX_DIR), env=env, check=True,
            )
            subprocess.run(
                [sys.executable, "scripts/suggest_cues.py", str(mj), "--out", str(cues_json)],
                cwd=str(REAL_SFX_DIR), env=env, check=True,
            )
        else:
            subprocess.run(
                [sys.executable, "scripts/find_moments.py", abs_video, "--out", str(moments_dir), "--fine"],
                cwd=str(REAL_SFX_DIR), env=env, check=True,
            )
            subprocess.run(
                [sys.executable, "scripts/suggest_cues.py", str(moments_dir / "moments.json"), "--out", str(cues_json)],
                cwd=str(REAL_SFX_DIR), env=env, check=True,
            )

        cues_data = json.loads(cues_json.read_text())
        cues_data["video"] = abs_video
        cues_json.write_text(json.dumps(cues_data, indent=2))

        mix_cmd = [sys.executable, "scripts/mix.py", str(cues_json), "--out", abs_out]
        if voice_safe:
            mix_cmd.append("--voice-safe")
        if duck:
            mix_cmd.append("--duck")
        subprocess.run(mix_cmd, cwd=str(REAL_SFX_DIR), env=env, check=True)

        stem_base = abs_out[:-4] if abs_out.lower().endswith(".mp4") else abs_out
        sfx_wav = f"{stem_base}_sfx_track.wav"
        resolved_json = f"{stem_base}_resolved_cues.json"
        crit_out = ""
        if Path(resolved_json).exists() and Path(sfx_wav).exists():
            cp = subprocess.run(
                [sys.executable, "scripts/critique.py", resolved_json, sfx_wav],
                cwd=str(REAL_SFX_DIR), env=env, capture_output=True, text=True, check=False,
            )
            crit_out = cp.stdout[-1200:] if cp.stdout else ""

        return {
            "out_mp4": abs_out,
            "sfx_stem_wav": sfx_wav if Path(sfx_wav).exists() else None,
            "resolved_cues_json": resolved_json if Path(resolved_json).exists() else None,
            "indexed_sounds": status["indexed_sounds"],
            "critique_tail": crit_out,
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)
