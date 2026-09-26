import json
import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_round_trip_unicode_path_and_ignore_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "설정" / "config.json"
            manager = ConfigManager(path)
            manager.update(last_install_path="C:/한글 경로/번역")
            loaded = ConfigManager(path)
            self.assertEqual(loaded.data["last_install_path"], "C:/한글 경로/번역")

            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["unknown_future_key"] = "ignored"
            path.write_text(json.dumps(raw), encoding="utf-8")
            self.assertNotIn("unknown_future_key", ConfigManager(path).data)
            self.assertEqual(ConfigManager(path).data["language"], "ko-KR")

    def test_recent_activity_is_newest_first_and_limited_to_five(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manager = ConfigManager(Path(temp) / "config.json")
            for index in range(7):
                manager.add_recent_activity(f"Mod {index}", "번역 적용", "적용 완료")
            activities = manager.data["recent_activities"]
            self.assertEqual(len(activities), 5)
            self.assertEqual(activities[0]["name"], "Mod 6")
            self.assertEqual(activities[-1]["name"], "Mod 2")

    def test_legacy_gemini_default_is_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text('{"ai_model": "gemini-2.5-flash"}', encoding="utf-8")
            self.assertEqual(ConfigManager(path).data["ai_model"], "gemini-3.8-flash")


if __name__ == "__main__":
    unittest.main()
