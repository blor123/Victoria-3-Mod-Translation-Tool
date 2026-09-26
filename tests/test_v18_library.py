import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.mod_library import LoadoutManager, ModFileIndexer, ModLibraryService
from app.mod_sources import ModImportManager
from app.mod_sources.descriptor import mod_entry_from_folder
from app.mod_sources.models import ModSource
from app.projects import ProjectManager


class V18LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])
    def setUp(self): self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.config = ConfigManager(self.root / "config.json")
    def tearDown(self): self.temp.cleanup()
    def _mod(self, name="Library Mod"):
        root = self.root / name; root.mkdir(); (root / "descriptor.mod").write_text(f'name="{name}"\nremote_file_id="123"\n', encoding="utf-8"); english = root / "localization" / "english"; english.mkdir(parents=True); (english / "a_english.yml").write_text('l_english:\n a:0 "A"\n', encoding="utf-8"); (root / "common").mkdir(); (root / "common" / "a.txt").write_text("x={}", encoding="utf-8"); return root

    def test_loadout_create_save_export_import(self):
        manager = LoadoutManager(self.config); loadout = manager.create("Korea Campaign"); manager.save(loadout["id"], [{"mod_id":"123","enabled":True,"position":2}]); self.assertEqual(manager.state_for("123"), (True, 2))
        output = self.root / "loadout.json"; manager.export_file(output); payload = json.loads(output.read_text(encoding="utf-8")); self.assertEqual(payload["format"], "v3mm_loadout")
        imported = manager.import_file(output); self.assertNotEqual(imported["id"], loadout["id"]); self.assertEqual(imported["mods"][0]["position"], 2)

    def test_library_project_link_translation_state_and_file_index(self):
        root = self._mod(); korean = root / "localization" / "korean"; korean.mkdir(); (korean / "a_korean.yml").write_text('l_korean:\n a:0 "가"\n', encoding="utf-8")
        imports = ModImportManager(self.config); entry = mod_entry_from_folder(root, ModSource.MANUAL); imports.merge([entry]); projects = ProjectManager(self.config); project = projects.save_project({"name":"Translation", "source_path":str(root), "localization_path":str(root / "localization" / "english"), "install_path":str(root), "target_language":"korean"})
        service = ModLibraryService(imports, projects); state = service.state(entry); self.assertEqual(state.project["id"], project["id"]); self.assertTrue(state.translation_exists)
        linked = service.link_project(entry, project["id"]); self.assertEqual(linked.project_id, project["id"]); paths = [item.relative_path for item in ModFileIndexer().build(linked)]; self.assertIn("common/a.txt", paths); self.assertIn("localization/english/a_english.yml", paths)

    def test_v21_replaces_library_navigation_with_api_and_conflicts(self):
        window = MainWindow(self.config); window.show(); QApplication.processEvents()
        self.assertFalse(hasattr(window, "mod_library_page")); self.assertTrue(hasattr(window, "ai_translation_page")); self.assertTrue(hasattr(window, "conflict_page")); self.assertEqual(window.stack.count(), 13); window.close()


if __name__ == "__main__": unittest.main()
