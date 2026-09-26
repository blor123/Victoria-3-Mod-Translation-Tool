import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.i18n.language_definition import LANGUAGES
from app.models import OverwritePolicy
from app.snapshots import capture_localization
from app.translation.prompt_manager import active_prompt, default_prompt
from app.translation_update import analyze_legacy, analyze_with_snapshot, build_merged_translation_zip


class V16CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.config = ConfigManager(self.root / "config.json")
    def tearDown(self): self.temp.cleanup()

    def _yml(self, root: Path, name: str, body: str, header="l_english:") -> Path:
        root.mkdir(parents=True, exist_ok=True); path = root / name; path.write_text(f'{header}\n{body}', encoding="utf-8-sig"); return path

    def test_five_prompt_languages_are_packaged_and_target_is_independent(self):
        texts = {code: default_prompt(code) for code in LANGUAGES}
        self.assertEqual(len(texts), 5); self.assertTrue(all("YML" in value for value in texts.values()))
        self.config.update(language="ja-JP", prompt_language="en-US")
        prompt = active_prompt(self.config)
        self.assertIn("Target translation language: Japanese", prompt); self.assertIn("This ZIP contains", prompt)

    def test_snapshot_and_legacy_analysis_do_not_guess_changes(self):
        old = self.root / "old"; new = self.root / "new"; translated = self.root / "translated"
        self._yml(old, "a_english.yml", ' keep:0 "Same"\n changed:0 "Old"\n deleted:0 "Gone"\n')
        self._yml(new, "a_english.yml", ' keep:0 "Same"\n changed:0 "New"\n added:0 "Added"\n')
        self._yml(translated, "a_korean.yml", ' keep:0 "유지"\n changed:0 "이전"\n deleted:0 "삭제 유지"\n', "l_korean:")
        full = analyze_with_snapshot(capture_localization(old), new)
        self.assertEqual(full.counts, {"NEW": 1, "CHANGED": 1, "DELETED": 1, "UNCHANGED": 1})
        legacy = analyze_legacy(translated, new); statuses = {item.key: item.status for item in legacy.items}
        self.assertEqual(statuses["added"], "NEW"); self.assertEqual(statuses["changed"], "EXISTING_UNKNOWN"); self.assertEqual(statuses["deleted"], "DELETION_CANDIDATE")

    def test_merge_replaces_adds_and_retains_deleted_entries(self):
        existing = self.root / "mod"; korean = existing / "localization" / "korean"
        self._yml(korean, "a_korean.yml", ' keep:0 "유지"\n changed:0 "이전"\n deleted:0 "삭제 항목 유지"\n', "l_korean:")
        update = self.root / "returned.zip"
        with zipfile.ZipFile(update, "w") as archive: archive.writestr("localization/korean/a_korean.yml", '\ufeffl_korean:\n changed:0 "새 번역"\n added:0 "추가 번역"\n')
        output = self.root / "merged.zip"; report = build_merged_translation_zip(existing, update, output, "korean", "l_korean:")
        self.assertEqual((report.replaced, report.added, report.preserved), (1, 1, 2))
        with zipfile.ZipFile(output) as archive: text = archive.read("localization/korean/a_korean.yml").decode("utf-8-sig")
        self.assertIn('changed:0 "새 번역"', text); self.assertIn('added:0 "추가 번역"', text); self.assertIn('deleted:0 "삭제 항목 유지"', text)

    def test_sidebar_and_notification_geometry(self):
        window = MainWindow(self.config); window.show(); QApplication.processEvents()
        self.assertEqual(window.stack.count(), 13); self.assertTrue(window.sidebar.children.isVisible()); self.assertTrue(window.sidebar.api_children.isVisible())
        self.assertLess(window.sidebar.layout.indexOf(window.sidebar.buttons[4]), window.sidebar.layout.indexOf(window.sidebar.parent_button))
        window.sidebar.parent_button.click(); self.assertFalse(window.sidebar.children.isVisible()); window.sidebar.select(2); self.assertTrue(window.sidebar.children.isVisible())
        for index in range(30): window.activity_manager.add("INFO", f"item {index}")
        window._toggle_notifications(); QApplication.processEvents(); panel = window.notifications
        self.assertEqual(panel.width(), 360); self.assertLessEqual(panel.height(), 460); self.assertGreaterEqual(panel.x(), 0); self.assertLessEqual(panel.x() + panel.width(), window.centralWidget().width())
        window.close()

    def test_quick_translation_build_and_apply_workflow(self):
        source = self._yml(self.root / "source", "a_english.yml", ' key:0 "English"\n'); package = self.root / "package.zip"
        window = MainWindow(self.config); page = window.quick_page; page.add_sources([source]); page.export_edit.setText(str(package))
        with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok): page._build()
        self.assertTrue(package.exists())
        translated = self.root / "translated.zip"
        with zipfile.ZipFile(translated, "w") as archive: archive.writestr("localization/korean/a_korean.yml", '\ufeffl_korean:\n key:0 "한국어"\n')
        install = self.root / "install"; page.translation_zip.setText(str(translated)); page.install_edit.setText(str(install))
        with patch("app.gui.pages.quick_translation_page.confirm_install", return_value=OverwritePolicy.BACKUP_AND_OVERWRITE), patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok): page._apply()
        self.assertTrue((install / "localization" / "korean" / "a_korean.yml").exists()); window.close()


if __name__ == "__main__": unittest.main()
