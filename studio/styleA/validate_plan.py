#!/usr/bin/env python3
"""Validate a Style A render plan without decoding or rendering any media.

Usage:
    python3 studio/styleA/validate_plan.py studio/styleA/plan.json
    python3 studio/styleA/validate_plan.py plan.json --report plan_validation.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

FPS = 30
RULES_PATH = Path(__file__).with_name("rules.json")


def _number(value: Any, label: str, errors: list[str], *, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be numeric")
        return 0.0
    if not math.isfinite(number) or number < minimum:
        errors.append(f"{label} must be finite and >= {minimum}")
        return 0.0
    return number


def _load_rules() -> dict[str, Any]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a portable validation report; never touches source media."""
    errors: list[str] = []
    warnings: list[str] = []
    rules = _load_rules()

    if not isinstance(plan, dict):
        return {
            "passed": False,
            "errors": ["plan root must be a JSON object"],
            "warnings": [],
            "manual_checks": [],
            "rules_schema_version": rules["schema_version"],
        }
    if plan.get("engine") != "zohair_jigsaw":
        errors.append("engine must be 'zohair_jigsaw' for the Style A cloud runner")

    # A path and a URL may describe two locators for the SAME logical song.
    # Extra song collections are forbidden so a second track cannot slip in.
    if not (plan.get("song_path") or plan.get("song_url")):
        errors.append("one song_path or song_url is required")
    for forbidden in ("songs", "additional_songs", "song_paths", "song_urls"):
        if plan.get(forbidden):
            errors.append(f"{forbidden} is not allowed: Style A uses one continuous song")

    sources = plan.get("sources")
    if not isinstance(sources, dict) or not sources:
        errors.append("sources must be a non-empty object")
        sources = {}
    for alias, locator in sources.items():
        if not isinstance(alias, str) or not alias.strip():
            errors.append("every source alias must be a non-empty string")
        if not isinstance(locator, str) or not locator.strip():
            errors.append(f"source {alias!r} must have a path or URL string")

    cuts = plan.get("visual_cuts")
    if not isinstance(cuts, list) or not cuts:
        errors.append("visual_cuts must be a non-empty array")
        cuts = []

    used_sources: list[str] = []
    expected_frames = 0
    for index, cut in enumerate(cuts):
        label = f"visual_cuts[{index}]"
        if not isinstance(cut, dict):
            errors.append(f"{label} must be an object")
            continue
        alias = cut.get("src")
        if alias not in sources:
            errors.append(f"{label}.src references unknown source {alias!r}")
        else:
            used_sources.append(alias)
        _number(cut.get("start_s"), f"{label}.start_s", errors)
        dur = _number(cut.get("dur_s"), f"{label}.dur_s", errors, minimum=0.001)
        expected_frames += max(2, int(round(dur * FPS)))
        if "src_dur_s" in cut:
            _number(cut["src_dur_s"], f"{label}.src_dur_s", errors, minimum=0.001)
        for zoom_key in ("zoom_start", "zoom_end"):
            if zoom_key in cut:
                _number(cut[zoom_key], f"{label}.{zoom_key}", errors, minimum=0.001)

    outro = _number(plan.get("outro_black_s", 0.0), "outro_black_s", errors)
    expected_frames += max(0, int(round(outro * FPS)))
    expected_duration = expected_frames / FPS
    if "total_s" in plan:
        declared = _number(plan["total_s"], "total_s", errors, minimum=0.001)
        if abs(declared - expected_duration) > 0.25:
            errors.append(
                f"total_s={declared:.3f}s differs from frame-rounded timeline "
                f"{expected_duration:.3f}s by more than 0.25s"
            )

    dialogue = plan.get("dialogue_events", [])
    if not isinstance(dialogue, list):
        errors.append("dialogue_events must be an array")
        dialogue = []
    for index, event in enumerate(dialogue):
        label = f"dialogue_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        alias = event.get("src")
        if alias not in sources:
            errors.append(f"{label}.src references unknown source {alias!r}")
        _number(event.get("start_s"), f"{label}.start_s", errors)
        dur = _number(event.get("dur_s"), f"{label}.dur_s", errors, minimum=0.001)
        timeline = _number(event.get("timeline_s"), f"{label}.timeline_s", errors)
        if timeline + dur > expected_duration + 0.25:
            errors.append(f"{label} extends beyond the video timeline")
        if "sub_t0" in event and "sub_t1" in event:
            sub0 = _number(event["sub_t0"], f"{label}.sub_t0", errors)
            sub1 = _number(event["sub_t1"], f"{label}.sub_t1", errors)
            if sub1 <= sub0:
                errors.append(f"{label}.sub_t1 must be after sub_t0")

    sfx = plan.get("sfx_events", []) or []
    if not isinstance(sfx, list):
        errors.append("sfx_events must be an array when present")
        sfx = []
    for index, event in enumerate(sfx):
        label = f"sfx_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        if event.get("src") not in sources:
            errors.append(f"{label}.src references unknown source {event.get('src')!r}")
        _number(event.get("start_s"), f"{label}.start_s", errors)
        _number(event.get("dur_s"), f"{label}.dur_s", errors, minimum=0.001)
        _number(event.get("timeline_s"), f"{label}.timeline_s", errors)

    unique_sources = len(set(used_sources))
    unique_ratio = unique_sources / len(cuts) if cuts else 0.0
    if cuts and unique_ratio < 0.50:
        warnings.append(
            f"only {unique_sources}/{len(cuts)} cuts use unique sources; "
            "confirm that heavy repetition is intentional under the v1 shot-first rule"
        )

    automatic_enforcement = {"plan_validator"}
    manual_checks = [
        {"id": rule["id"], "enforcement": rule["enforcement"]}
        for rule in rules["rules"]
        if rule["enforcement"] not in automatic_enforcement
    ]
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "manual_checks": manual_checks,
        "rules_schema_version": rules["schema_version"],
        "reference": rules["reference"],
        "metrics": {
            "visual_cuts": len(cuts),
            "unique_visual_sources": unique_sources,
            "unique_visual_source_ratio": round(unique_ratio, 4),
            "dialogue_events": len(dialogue),
            "sfx_events": len(sfx),
            "frame_rounded_duration_s": round(expected_duration, 3),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    report = validate_plan(plan)
    text = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
