import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.activity import ActivityManager
from app.config.config_manager import ConfigManager
from app.i18n.language_definition import target_language
from app.projects import ProjectManager
from app.translation.package_builder import build_translation_package_report
from app.update.update_checker import check_for_update
from app.validation.localization_validator import validate_translation_zip


class V14CoreTests(unittest.TestCase):
    def test_all_ui_languages_have_target_mapping(self):
        self.assertEqual(target_language("ja-JP").filename_suffix, "japanese")
        self.assertEqual(target_language("zh-TW").localization_header, "l_simp_chinese:")

    def test_activity_delete_is_shared_and_project_metadata_only(self):
        with tempfile.TemporaryDirectory() as folder:
            config = ConfigManager(Path(folder) / "config.json"); activities = ActivityManager(config); projects = ProjectManager(config)
            record = activities.add("INFO", "test"); self.assertEqual(activities.unread_count(), 1); activities.remove(record["id"]); self.assertEqual(activities.records, [])
            source = Path(folder) / "source"; source.mkdir(); project = projects.save_project({"name": "P", "source_path": str(source)}); projects.remove(project["id"]); self.assertTrue(source.exists())

    def test_manifest_validation_detects_missing_key(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / "sample_english.yml"; source.write_text('l_english:\n key_one:0 "Hello $VALUE$"\n', encoding="utf-8")
            package = root / "request.zip"; build_translation_package_report([source], package, target_language("ko-KR"))
            result = root / "result.zip"
            with zipfile.ZipFile(result, "w") as archive: archive.writestr("localization/korean/sample_korean.yml", 'l_korean:\n other:0 "번역"\n')
            report = validate_translation_zip(result); self.assertIsNotNone(report); self.assertTrue(report.errors)

    def test_update_checker_uses_release_metadata(self):
        payload = json.dumps({"tag_name":"v9.0.0","html_url":"https://example.test/release","draft":False,"prerelease":False}).encode()
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): pass
        info = check_for_update("1.4.0", opener=lambda request, timeout: Response(payload)); self.assertEqual(info.version, "9.0.0")


if __name__ == "__main__": unittest.main()
