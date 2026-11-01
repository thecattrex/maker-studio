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
    apply_vfx_pipeline,
    auto_sound_design_video,
    composite_motion_overlay,
    detect_silences,
    ensure_realsfx_ready,
    extract_ign_1080p_mp4,
    list_cinema_looks,
    list_sfx_bank,
    list_sources,
    list_viral_vfx,
    master_polish_video,
    plan_jigsaw_music_pockets,
    plan_smart_camera,
    render_still_art_edit,
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

    sub.add_parser("vfx-list", help="List all 17 S01..S11 viral edit tools & blueprints")

    p_vfx = sub.add_parser("vfx", help="Apply any S01..S11 viral VFX shader/roto/shake to a video")
    p_vfx.add_argument("video")
    p_vfx.add_argument("--effect", required=True, help="e.g. blob_tracking | red_ribbon_roto | text_behind_subject | fight_club_shake | risograph_2tone | dither_1bit | receipt_ticket | crt_phosphor | datamosh_optical | silhouette_double_exp | roto_clone_pop | flashlight_glow | bass_shockwave | center_match_strobe")
    p_vfx.add_argument("--out", required=True)
    p_vfx.add_argument("--params-json", default="{}", help="JSON dict of effect parameters")
    p_vfx.add_argument("--windows-json", default="", help="Optional JSON [[t0,t1], ...] active time windows")

    p_art = sub.add_parser("still-art", help="Turn 1 static image/drawing into a kevamarts S08 motion edit")
    p_art.add_argument("image")
    p_art.add_argument("--out", required=True)
    p_art.add_argument("--title-top", default="GOD'S")
    p_art.add_argument("--title-main", default="WISDOM")
    p_art.add_argument("--dur", type=float, default=15.4)
    p_art.add_argument("--layout", choices=["9:16_center_16:9", "16:9"], default="9:16_center_16:9")

    p_pkt = sub.add_parser("music-pockets", help="Find low-energy instrumental pockets in a song for dialogue (S04 rule)")
    p_pkt.add_argument("music")
    p_pkt.add_argument("--min-gap", type=float, default=0.50)

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
    elif args.cmd == "vfx-list":
        items = list_viral_vfx()
        print(json.dumps({"count": len(items), "effects": items}, indent=2))
    elif args.cmd == "vfx":
        params = json.loads(args.params_json) if args.params_json else {}
        wins = json.loads(args.windows_json) if args.windows_json else None
        print(json.dumps(apply_vfx_pipeline(args.video, args.out, effect=args.effect, params=params, windows=wins), indent=2))
    elif args.cmd == "still-art":
        print(json.dumps(render_still_art_edit(args.image, args.out, title_top=args.title_top, title_main=args.title_main, dur_s=args.dur, layout=args.layout), indent=2))
    elif args.cmd == "music-pockets":
        pockets = plan_jigsaw_music_pockets(args.music, min_gap_s=args.min_gap)
        print(json.dumps({"count": len(pockets), "pockets": pockets}, indent=2))


if __name__ == "__main__":
    main()
