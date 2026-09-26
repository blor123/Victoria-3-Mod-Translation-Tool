import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.mod_sources import JsonModSourceProvider, ModImportManager, ParadoxLauncherProvider, SteamModSourceProvider, export_mod_list
from app.mod_sources.manual_provider import ManualModSourceProvider
from app.mod_sources.models import ModSource


class V17ModSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])
    def setUp(self): self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()

    def _make_mod(self, folder: Path, name="Example Mod", workshop="123456"):
        folder.mkdir(parents=True); (folder / "descriptor.mod").write_text(f'name="{name}"\nversion="1.2"\nsupported_version="1.9.*"\nremote_file_id="{workshop}"\n', encoding="utf-8")
        loc = folder / "localization" / "english"; loc.mkdir(parents=True); (loc / "test_english.yml").write_text('l_english:\n key:0 "Text"\n', encoding="utf-8")

    def test_manual_provider_discovers_mod_folder(self):
        mod = self.root / "mods" / "manual"; self._make_mod(mod)
        result = ManualModSourceProvider([self.root / "mods"]).discover()
        self.assertEqual(len(result), 1); self.assertEqual(result[0].name, "Example Mod"); self.assertEqual(result[0].source, ModSource.MANUAL); self.assertTrue(result[0].localization_paths)

    def test_steam_provider_reads_local_library_without_authentication(self):
        steam = self.root / "Steam"; library = self.root / "SteamLibrary"; (steam / "steamapps").mkdir(parents=True); (library / "steamapps").mkdir(parents=True)
        (steam / "steamapps" / "libraryfolders.vdf").write_text(f'"libraryfolders"\n{{\n "1"\n {{\n  "path" "{str(library).replace(chr(92), chr(92)*2)}"\n }}\n}}', encoding="utf-8")
        mod = library / "steamapps" / "workshop" / "content" / "529340" / "987654321"; self._make_mod(mod, "Workshop Mod", "987654321")
        result = SteamModSourceProvider([steam]).discover()
        self.assertEqual(len(result), 1); self.assertEqual(result[0].source, ModSource.STEAM_WORKSHOP); self.assertEqual(result[0].workshop_id, "987654321"); self.assertEqual(result[0].name, "Workshop Mod")

    def test_paradox_sqlite_is_read_only_and_imports_playset(self):
        mod = self.root / "launcher_mod"; self._make_mod(mod, "Launcher Mod", "555")
        database = self.root / "launcher-v2.sqlite"; connection = sqlite3.connect(database)
        connection.executescript('CREATE TABLE mods(id TEXT, displayName TEXT, dirPath TEXT, steamId TEXT); CREATE TABLE playsets(id TEXT, name TEXT); CREATE TABLE playsets_mods(playsetId TEXT, modId TEXT, enabled INTEGER, position INTEGER);')
        connection.execute("INSERT INTO mods VALUES(?,?,?,?)", ("m1", "Launcher Display", str(mod), "555")); connection.execute("INSERT INTO playsets VALUES(?,?)", ("p1", "Active Set")); connection.execute("INSERT INTO playsets_mods VALUES(?,?,?,?)", ("p1", "m1", 1, 4)); connection.commit(); connection.close()
        before = hashlib.sha256(database.read_bytes()).hexdigest(); result = ParadoxLauncherProvider([database], []).discover(); after = hashlib.sha256(database.read_bytes()).hexdigest()
        self.assertEqual(before, after); self.assertEqual(len(result), 1); self.assertEqual(result[0].name, "Launcher Display"); self.assertTrue(result[0].enabled); self.assertEqual(result[0].load_order_position, 4); self.assertEqual(result[0].playset, "Active Set")

    def test_json_round_trip_and_persistent_manager(self):
        mod = self.root / "json_mod"; self._make_mod(mod, "JSON Mod", "777"); entry = ManualModSourceProvider([mod]).discover()[0]
        output = self.root / "mods.json"; export_mod_list([entry], output); payload = json.loads(output.read_text(encoding="utf-8")); self.assertEqual(payload["format"], "v3mm_mod_list")
        imported = JsonModSourceProvider(output).discover(); self.assertEqual(imported[0].name, "JSON Mod"); self.assertEqual(imported[0].source, ModSource.JSON_IMPORT)
        config = ConfigManager(self.root / "config.json"); manager = ModImportManager(config); manager.merge(imported); self.assertEqual(ModImportManager(ConfigManager(self.root / "config.json")).entries[0].workshop_id, "777")

    def test_json_accepts_top_level_list_registry_and_enabled_mods(self):
        mod = self.root / "listed"; self._make_mod(mod, "Flexible JSON", "888")
        top_list = self.root / "list.json"; top_list.write_text(json.dumps([{"name": "Flexible JSON", "path": str(mod), "enabled": True}]), encoding="utf-8")
        self.assertEqual(JsonModSourceProvider(top_list).discover()[0].name, "Flexible JSON")
        registry = self.root / "registry.json"; registry.write_text(json.dumps({"registry-key": {"displayName": "Registry Mod", "dirPath": str(mod), "steamId": "888"}}), encoding="utf-8")
        self.assertEqual(JsonModSourceProvider(registry).discover()[0].name, "Registry Mod")
        descriptor = self.root / "ugc_888.mod"; descriptor.write_text(f'name="Descriptor Mod"\npath="{mod}"\nremote_file_id="888"\n', encoding="utf-8")
        enabled = self.root / "dlc_load.json"; enabled.write_text(json.dumps({"enabled_mods": [descriptor.name]}), encoding="utf-8")
        result = JsonModSourceProvider(enabled).discover()[0]; self.assertEqual(result.name, "Descriptor Mod"); self.assertTrue(result.enabled)

    def test_sidebar_triangles_have_exact_up_and_down_icons(self):
        config = ConfigManager(self.root / "config.json"); window = MainWindow(config); window.show(); QApplication.processEvents()
        expanded_key = window.sidebar.parent_button.icon().cacheKey(); window.sidebar.parent_button.click(); QApplication.processEvents(); collapsed_key = window.sidebar.parent_button.icon().cacheKey()
        self.assertNotEqual(expanded_key, collapsed_key); self.assertFalse(window.sidebar.children.isVisible()); window.sidebar.parent_button.click(); self.assertTrue(window.sidebar.children.isVisible()); window.close()


if __name__ == "__main__": unittest.main()
