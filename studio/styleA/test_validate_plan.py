from __future__ import annotations

import unittest

from styleA.validate_plan import validate_plan


def valid_plan() -> dict:
    return {
        "name": "validator_fixture",
        "engine": "zohair_jigsaw",
        "song_path": "/media/song.wav",
        "song_offset_s": 10.0,
        "total_s": 1.0,
        "outro_black_s": 0.0,
        "sources": {
            "shot_a": "/media/a.mp4",
            "shot_b": "/media/b.mp4",
            "voice": "/media/voice.wav",
        },
        "visual_cuts": [
            {"src": "shot_a", "start_s": 0.0, "dur_s": 0.5},
            {"src": "shot_b", "start_s": 0.0, "dur_s": 0.5},
        ],
        "dialogue_events": [
            {"src": "voice", "start_s": 0.0, "dur_s": 0.2, "timeline_s": 0.1}
        ],
        "sfx_events": [],
    }


class ValidatePlanTests(unittest.TestCase):
    def test_valid_plan_passes_without_media(self) -> None:
        report = validate_plan(valid_plan())
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["metrics"]["visual_cuts"], 2)
        self.assertEqual(report["metrics"]["unique_visual_sources"], 2)

    def test_unknown_source_is_an_error(self) -> None:
        plan = valid_plan()
        plan["visual_cuts"][0]["src"] = "missing"
        report = validate_plan(plan)
        self.assertFalse(report["passed"])
        self.assertTrue(any("unknown source" in error for error in report["errors"]))

    def test_second_song_collection_is_rejected(self) -> None:
        plan = valid_plan()
        plan["additional_songs"] = ["/media/other.mp3"]
        report = validate_plan(plan)
        self.assertFalse(report["passed"])
        self.assertTrue(any("one continuous song" in error for error in report["errors"]))

    def test_dialogue_cannot_extend_beyond_timeline(self) -> None:
        plan = valid_plan()
        plan["dialogue_events"][0]["timeline_s"] = 0.95
        plan["dialogue_events"][0]["dur_s"] = 0.4
        report = validate_plan(plan)
        self.assertFalse(report["passed"])
        self.assertTrue(any("beyond the video" in error for error in report["errors"]))

    def test_repetition_is_visible_as_a_warning(self) -> None:
        plan = valid_plan()
        plan["visual_cuts"] = [dict(plan["visual_cuts"][0]) for _ in range(4)]
        plan["total_s"] = 2.0
        report = validate_plan(plan)
        self.assertTrue(report["passed"], report["errors"])
        self.assertTrue(report["warnings"])
        self.assertEqual(report["metrics"]["unique_visual_source_ratio"], 0.25)


if __name__ == "__main__":
    unittest.main()
