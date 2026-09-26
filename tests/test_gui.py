import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from app.config.config_manager import ConfigManager  # noqa: E402
from app.gui.main_window import MainWindow  # noqa: E402
from app.gui.project_wizard import ProjectWizard  # noqa: E402
from app.gui.theme import apply_theme  # noqa: E402
from app.models import OverwritePolicy  # noqa: E402


class GuiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        apply_theme(cls.application)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = ConfigManager(self.root / "config.json")
        self.config.update(open_export_folder_after_creation=False)
        self.window = MainWindow(self.config)

    def tearDown(self) -> None:
        self.window.close()
        self.temp.cleanup()

    def test_main_window_structure_and_navigation(self) -> None:
        self.assertEqual(self.window.stack.count(), 13)
        self.assertEqual(self.window.minimumSize(), QSize(1000, 650))
        self.assertIn("v2.1.2", self.window.windowTitle())
        self.window.navigate(2)
        self.assertEqual(self.window.stack.currentIndex(), 2)
        self.assertTrue(self.window.sidebar.buttons[2].isChecked())

    def test_late_update_callbacks_are_ignored_after_close(self) -> None:
        self.window.close()
        self.window._update_failed("late network error", False)
        self.window._update_finished(None, False)

    def test_package_page_creates_zip_through_existing_core(self) -> None:
        source = self.root / "한글 원본_english.yml"
        source.write_bytes(b"\xef\xbb\xbfl_english:\n key:0 \"English\"\n")
        destination = self.root / "output" / "translation.zip"
        page = self.window.package_page
        page.source_paths = [source]
        page.source_edit.setText(str(source))
        page.export_edit.setText(str(destination))

        page._create_package()

        self.assertTrue(destination.exists())
        with zipfile.ZipFile(destination) as archive:
            self.assertEqual(archive.namelist(), ["localization/korean/한글 원본_korean.yml"])
        self.assertFalse(page.result.isHidden())
        self.assertEqual(self.config.data["activities"][0]["metadata"]["status"], "package_ready")
        with zipfile.ZipFile(destination) as archive:
            self.assertIn(b"l_korean:", archive.read("localization/korean/한글 원본_korean.yml"))
        self.assertIn(b"l_english:", source.read_bytes())

    def test_prompt_copy_uses_packaged_prompt_resource(self) -> None:
        with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok):
            self.window.package_page._copy_prompt()
        clipboard = QApplication.clipboard().text()
        self.assertIn("Victoria 3 localization", clipboard)
        self.assertIn("l_korean", clipboard)

    def test_apply_page_installs_zip_through_existing_core(self) -> None:
        package = self.root / "translated.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("wrapper/localization/korean/test_korean.yml", b"translated")
        install_root = self.root / "설치 대상"
        page = self.window.apply_page
        page.import_edit.setText(str(package))
        page.install_edit.setText(str(install_root))

        with patch(
            "app.gui.pages.translation_apply_page.confirm_install",
            return_value=OverwritePolicy.BACKUP_AND_OVERWRITE,
        ):
            page._apply_translation()

        target = install_root / "localization" / "korean" / "test_korean.yml"
        self.assertEqual(target.read_bytes(), b"translated")
        self.assertEqual(self.config.data["activities"][0]["metadata"]["status"], "applied")

    def test_settings_are_saved(self) -> None:
        page = self.window.settings_page
        page.backup.setChecked(False)
        page.open_folder.setChecked(False)
        page.remember_paths.setChecked(False)
        page.save()
        reloaded = ConfigManager(self.root / "config.json")
        self.assertFalse(reloaded.data["create_backup"])
        self.assertFalse(reloaded.data["open_export_folder_after_creation"])
        self.assertFalse(reloaded.data["remember_recent_paths"])

    def test_reset_buttons_clear_ui_without_deleting_files(self) -> None:
        source = self.root / "keep_english.yml"; source.write_text('l_english:\n key:0 "Keep"\n', encoding="utf-8")
        package = self.window.package_page; package.add_sources([source]); package.export_edit.setText(str(self.root / "out.zip")); package.reset_all()
        self.assertEqual(package.source_paths, []); self.assertEqual(package.export_edit.text(), ""); self.assertTrue(source.exists())
        apply = self.window.apply_page; apply.import_edit.setText(str(self.root / "translated.zip")); apply.install_edit.setText(str(self.root)); apply.reset_all(); self.assertEqual(apply.import_edit.text(), ""); self.assertTrue(self.root.exists())

    def test_project_wizard_detects_localization_and_target(self) -> None:
        mod = self.root / "Workshop Mod"; localization = mod / "localization" / "english"; localization.mkdir(parents=True); (localization / "a_english.yml").write_text('l_english:\n a:0 "A"\n', encoding="utf-8")
        wizard = ProjectWizard(self.config); wizard.name_edit.setText("Test Mod"); wizard.root_edit.setText(str(mod)); wizard._detect(); data = wizard.data()
        self.assertEqual(Path(data["localization_path"]), localization); self.assertEqual(Path(data["install_path"]), mod); self.assertEqual(data["target_language"], "korean")

    def test_all_languages_load_and_change_is_persisted(self) -> None:
        expected = {"ko-KR": "홈", "en-US": "Home", "zh-CN": "主页", "zh-TW": "首頁", "ja-JP": "ホーム"}
        for code, label in expected.items():
            page = self.window.settings_page
            page.language.setCurrentIndex(page.language.findData(code))
            QApplication.processEvents()
            self.assertEqual(self.config.data["language"], code)
            self.assertEqual(self.window.sidebar.buttons[0].text(), label)

    def test_duplicate_sources_are_removed_in_preview(self) -> None:
        source = self.root / "same_english.yml"
        source.write_bytes(b"l_english:\n key:0 \"Value\"\n")
        page = self.window.package_page
        page.add_sources([source, source, self.root])
        self.assertEqual(page.target_list.count(), 1)


if __name__ == "__main__":
    unittest.main()
