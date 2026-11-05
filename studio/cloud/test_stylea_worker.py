from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloud.stylea_worker import _load_plan, _out_name, _resolve_assets


class StyleAWorkerSetupTests(unittest.TestCase):
    def test_inline_plan_has_stable_identity(self) -> None:
        plan = {"name": "inline", "sources": {}}
        loaded, hash1 = _load_plan({"plan": plan})
        _, hash2 = _load_plan({"plan": plan})
        self.assertEqual(loaded, plan)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_plan_path_cannot_escape_repository(self) -> None:
        with self.assertRaises(ValueError):
            _load_plan({"plan_path": "../outside.json"})

    def test_local_assets_resolve_without_download_or_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "shot.mp4"
            voice = root / "voice.wav"
            song = root / "song.wav"
            for path in (video, voice, song):
                path.write_bytes(b"fixture")
            plan = {
                "sources": {"shot": str(video), "voice": str(voice)},
                "song_path": str(song),
            }
            sources, resolved_song, cache = _resolve_assets(plan, {}, root / "cache")
            self.assertEqual(Path(sources["shot"]), video)
            self.assertEqual(Path(sources["voice"]), voice)
            self.assertEqual(resolved_song, song)
            self.assertEqual(cache["cache_hits"], 0)
            self.assertEqual(cache["new_downloads"], 0)

    def test_output_name_is_sanitized(self) -> None:
        name = _out_name({"name": "style A"}, {"out_name": "../../My Master"})
        self.assertEqual(name, "My_Master.mp4")
        self.assertNotIn("/", name)


if __name__ == "__main__":
    unittest.main()
