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
    detect_silences,
    extract_ign_1080p_mp4,
    list_cinema_looks,
    list_sources,
    plan_smart_camera,
    run_full_qa,
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


if __name__ == "__main__":
    main()
