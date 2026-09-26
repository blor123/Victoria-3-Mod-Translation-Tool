import tempfile
import unittest
import zipfile
from pathlib import Path

from PySide6.QtWidgets import QScrollArea

from app.activity import ActivityManager
from app.config.config_manager import ConfigManager
from app.i18n.language_definition import target_language
from app.projects import detect_project_paths
from app.snapshots import SnapshotManager, capture_localization, compare_snapshot
from app.translation.incremental_builder import build_incremental_package


class V15CoreTests(unittest.TestCase):
    def _write(self, path, values):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text("l_english:\n" + "\n".join(f' {key}:0 "{value}"' for key, value in values.items()) + "\n", encoding="utf-8")

    def test_diff_and_incremental_japanese_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "mod" / "localization" / "english"; source = root / "bank_english.yml"
            self._write(source, {"same":"Same", "changed":"Bank", "deleted":"Old"}); old = capture_localization(root)
            self._write(source, {"same":"Same", "changed":"Commercial Bank", "new":"Financial Center"}); current = capture_localization(root); diff = compare_snapshot(old, current)
            self.assertEqual(diff.counts, {"NEW":1, "CHANGED":1, "DELETED":1, "UNCHANGED":1})
            destination = Path(temp) / "incremental.zip"; build_incremental_package(diff, root, destination, target_language("ja-JP"), 3)
            with zipfile.ZipFile(destination) as archive:
                name = "localization/japanese/bank_japanese.yml"; text = archive.read(name).decode("utf-8-sig"); self.assertIn("l_japanese:", text); self.assertIn("Commercial Bank", text); self.assertNotIn('same:0', text); self.assertNotIn('deleted:0', text)

    def test_snapshot_storage_is_project_scoped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "localization" / "english"; self._write(root / "a_english.yml", {"a":"A"}); manager = SnapshotManager(Path(temp) / "data")
            project = {"id":"project-one", "localization_path":str(root)}; path = manager.save(project, target_language("ko-KR")); self.assertTrue(path.exists()); self.assertEqual(manager.latest("project-one")["entries"][0]["key"], "a")

    def test_activity_clear_survives_restart_and_new_event_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"; config = ConfigManager(config_path); config.add_recent_activity("old", "package", "ready")
            first = ActivityManager(config); self.assertEqual(len(first.records), 1); first.clear(); second = ActivityManager(ConfigManager(config_path)); self.assertEqual(second.records, [])
            new = second.add("PACKAGE_CREATED", "new"); self.assertEqual(len(second.records), 1); self.assertNotEqual(new["message"], "old")
            update = second.add("UPDATE_AVAILABLE", "v2", dedupe_key="update-v2"); second.remove(update["id"]); restarted = ActivityManager(ConfigManager(config_path)); self.assertEqual(restarted.add("UPDATE_AVAILABLE", "v2", dedupe_key="update-v2"), {}); self.assertEqual(len(restarted.records), 1)

    def test_project_path_detection_and_reset_does_not_delete(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = Path(temp) / "한글 Mod"; source = mod / "localization" / "english" / "a_english.yml"; self._write(source, {"a":"A"})
            detected = detect_project_paths(mod, target_language("ko-KR")); self.assertEqual(detected.localization_path, source.parent); self.assertEqual(detected.yml_count, 1); self.assertEqual(detected.proposed_target_path, mod / "localization" / "korean")

    def test_settings_page_is_scrollable(self):
        from app.gui.pages.settings_page import SettingsPage
        with tempfile.TemporaryDirectory() as temp: self.assertIsInstance(SettingsPage(ConfigManager(Path(temp) / "config.json")), QScrollArea)


if __name__ == "__main__": unittest.main()
