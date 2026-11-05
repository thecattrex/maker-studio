#!/usr/bin/env python3
"""Render a Style A plan (plan_oppenheimer_v2.json) through zohair_jigsaw.

usage: python3 styleA/render_plan.py <plan.json> <out.mp4>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from om_hybrid.zohair_edit import render_zohair_jigsaw_edit  # noqa: E402


def main() -> int:
    plan_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2])
    p = json.loads(plan_p.read_text())
    res = render_zohair_jigsaw_edit(
        out_p,
        sources=p["sources"],
        song_path=p["song_path"],
        song_offset_s=float(p["song_offset_s"]),
        visual_cuts=p["visual_cuts"],
        dialogue_events=p["dialogue_events"],
        sfx_events=p.get("sfx_events") or [],
        outro_black_s=float(p.get("outro_black_s", 0.0)),
    )
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
