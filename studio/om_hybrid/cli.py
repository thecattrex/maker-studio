"""cli.py — Command-Line Interface for Studio x OpenMontage Hybrid (`om_hybrid`).

Usage:
  python3 /home/user/studio/om_hybrid/cli.py sources
  python3 /home/user/studio/om_hybrid/cli.py search "ocean storm" --per-source 3
  python3 /home/user/studio/om_hybrid/cli.py ign <ign_video_url>
  python3 /home/user/studio/om_hybrid/cli.py analyze <video.mp4> --start 10 --end 35
  python3 /home/user/studio/om_hybrid/cli.py qa <final_short.mp4> [--sheet /tmp/qa.jpg]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if STUDIO not in sys.path:
    sys.path.insert(0, STUDIO)

from om_hybrid import (  # noqa: E402
    analyze_energy,
    apply_cinema_look,
    auto_sound_design_video,
    composite_motion_overlay,
    detect_silences,
    ensure_realsfx_ready,
    extract_ign_1080p_mp4,
    list_cinema_looks,
    list_sfx_bank,
    list_sources,
    master_polish_video,
    plan_smart_camera,
    render_synced_sfx,
    run_full_qa,
    search_openverse_audio,
    search_openverse_images,
    search_stock_clips,
)


def main() -> None:
    ap = argparse.ArgumentParser(prog="om_hybrid")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sources", help="List all 16 free/public stock footage adapters")

    p_s = sub.add_parser("search", help="Search free stock video sources")
    p_s.add_argument("query")
    p_s.add_argument("--sources", nargs="*", default=None)
    p_s.add_argument("--per-source", type=int, default=3)
    p_s.add_argument("--download-dir", default=None)

    p_i = sub.add_parser("ign", help="Extract 1080p MP4 from IGN video URL")
    p_i.add_argument("url")

    p_a = sub.add_parser("analyze", help="Smart camera plan + silence + energy analysis")
    p_a.add_argument("video")
    p_a.add_argument("--start", type=float, default=0.0)
    p_a.add_argument("--end", type=float, default=25.0)

    p_q = sub.add_parser("qa", help="Run full decode + EBUR128 + occlusion QA")
    p_q.add_argument("video")
    p_q.add_argument("--sheet", default=None)

    sub.add_parser("looks", help="List HyperFrames-adapted 3D .cube cinema looks")

    p_g = sub.add_parser("grade", help="Apply a 3D .cube cinema look to a video")
    p_g.add_argument("video")
    p_g.add_argument("--look", default="teal-orange-blockbuster")
    p_g.add_argument("--intensity", type=float, default=None)
    p_g.add_argument("--out", required=True)

    p_sl = sub.add_parser("sfx-list", help="List shipped Earshot procedural studio SFX (252 sounds)")
    p_sl.add_argument("--kind", default=None)
    p_sl.add_argument("--category", default=None)

    p_sr = sub.add_parser("sfx-render", help="Render a procedural SFX synced to cut_time_s")
    p_sr.add_argument("sfx_id")
    p_sr.add_argument("--out", required=True)
    p_sr.add_argument("--cut-time", type=float, default=0.0)
    p_sr.add_argument("--dur", type=float, default=None)
    p_sr.add_argument("--apex", type=float, default=None)

    p_ova = sub.add_parser("openverse-audio", help="Search Openverse 5M+ open audio (CC0/CC-BY)")
    p_ova.add_argument("query")
    p_ova.add_argument("--license", default=None)
    p_ova.add_argument("--limit", type=int, default=5)
    p_ova.add_argument("--download-dir", default=None)

    p_ovi = sub.add_parser("openverse-images", help="Search Openverse 800M+ open images")
    p_ovi.add_argument("query")
    p_ovi.add_argument("--license", default=None)
    p_ovi.add_argument("--limit", type=int, default=5)
    p_ovi.add_argument("--download-dir", default=None)

    sub.add_parser("realsfx-setup", help="Initialize Clipwing Real-SFX + 78 CC0 uisfx sounds + index")

    p_rm = sub.add_parser("realsfx-mix", help="Auto-detect moments & sound-design video via Real-SFX")
    p_rm.add_argument("video")
    p_rm.add_argument("--out", required=True)
    p_rm.add_argument("--hyperframes-dir", default=None)

    p_ms = sub.add_parser("master", help="Unified 6-layer Master Pipeline (Grade + SFX + QA + AI Ears) for ANY video")
    p_ms.add_argument("video")
    p_ms.add_argument("--out", required=True)
    p_ms.add_argument("--preset", choices=["movie", "cinema", "motion", "reaction", "scifi", "none"], default="movie")
    p_ms.add_argument("--hyperframes-dir", default=None)
    p_ms.add_argument("--openverse-query", default=None)
    p_ms.add_argument("--no-sfx", action="store_true")

    p_ovl = sub.add_parser("overlay", help="Composite HyperFrames/Remotion motion graphic over live video")
    p_ovl.add_argument("base_mp4")
    p_ovl.add_argument("overlay_mp4")
    p_ovl.add_argument("--out", required=True)
    p_ovl.add_argument("--at", type=float, default=0.0)
    p_ovl.add_argument("--mode", choices=["screen", "colorkey", "alpha"], default="screen")

    args = ap.parse_args()

    if args.cmd == "sources":
        cat = list_sources()
        avail = [c["name"] for c in cat if c["status"] == "available"]
        unavail = [c["name"] for c in cat if c["status"] != "available"]
        print(json.dumps({"available_zero_key": avail, "needs_env_key": unavail}, indent=2))
    elif args.cmd == "search":
        res = search_stock_clips(
            args.query,
            sources=args.sources,
            per_source=args.per_source,
            download_dir=args.download_dir,
        )
        print(json.dumps(res, indent=2))
    elif args.cmd == "ign":
        print(json.dumps(extract_ign_1080p_mp4(args.url), indent=2))
    elif args.cmd == "analyze":
        cam = plan_smart_camera(args.video, start_s=args.start, end_s=args.end)
        sil = detect_silences(args.video)
        eng = analyze_energy(args.video)
        out = {
            "camera_plan": cam,
            "silences_summary": {k: sil[k] for k in ("total_duration", "silence_count", "silence_seconds", "dead_air_ratio")},
            "energy_summary": {k: eng[k] for k in ("peak_sec", "peak_lufs", "best_window_start_s", "best_window_end_s") if k in eng},
        }
        print(json.dumps(out, indent=2))
    elif args.cmd == "qa":
        print(json.dumps(run_full_qa(args.video, sheet_out=args.sheet), indent=2))
    elif args.cmd == "looks":
        print(json.dumps(list_cinema_looks(), indent=2))
    elif args.cmd == "grade":
        print(json.dumps(apply_cinema_look(args.video, args.out, look_id=args.look, intensity=args.intensity), indent=2))
    elif args.cmd == "sfx-list":
        items = list_sfx_bank(kind=args.kind, category=args.category)
        print(json.dumps({"count": len(items), "items": items}, indent=2))
    elif args.cmd == "sfx-render":
        print(json.dumps(render_synced_sfx(args.sfx_id, args.out, cut_time_s=args.cut_time, dur=args.dur, apex=args.apex), indent=2))
    elif args.cmd == "openverse-audio":
        print(json.dumps(search_openverse_audio(args.query, license_type=args.license, limit=args.limit, download_dir=args.download_dir), indent=2))
    elif args.cmd == "openverse-images":
        print(json.dumps(search_openverse_images(args.query, license_type=args.license, limit=args.limit, download_dir=args.download_dir), indent=2))
    elif args.cmd == "realsfx-setup":
        print(json.dumps(ensure_realsfx_ready(install_uisfx=True), indent=2))
    elif args.cmd == "realsfx-mix":
        print(json.dumps(auto_sound_design_video(args.video, args.out, hyperframes_dir=args.hyperframes_dir), indent=2))
    elif args.cmd == "master":
        print(
            json.dumps(
                master_polish_video(
                    args.video,
                    args.out,
                    preset=args.preset,
                    enable_sfx=not args.no_sfx,
                    openverse_seed_query=args.openverse_query,
                    hyperframes_dir=args.hyperframes_dir,
                ),
                indent=2,
            )
        )
    elif args.cmd == "overlay":
        print(json.dumps(composite_motion_overlay(args.base_mp4, args.overlay_mp4, args.out, at_s=args.at, mode=args.mode), indent=2))


if __name__ == "__main__":
    main()
