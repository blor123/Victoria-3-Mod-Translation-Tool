import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import quote

from app.mod_sources.base_provider import ModSourceProvider
from app.mod_sources.descriptor import find_localizations, mod_entry_from_folder
from app.mod_sources.models import ModEntry, ModSource


def default_launcher_candidates() -> tuple[list[Path], list[Path]]:
    databases: list[Path] = []; registries: list[Path] = []
    appdata = os.environ.get("APPDATA")
    document_roots = [Path.home() / "Documents"]
    if os.environ.get("OneDrive"):
        document_roots.extend([Path(os.environ["OneDrive"]) / "Documents", Path(os.environ["OneDrive"]) / "문서"])
    if appdata:
        base = Path(appdata) / "Paradox Interactive"
        databases.extend([base / "launcher-v2.sqlite", base / "launcher-v2" / "launcher-v2.sqlite"])
        registries.extend([base / "launcher-v2" / "mods_registry.json", base / "mods_registry.json"])
    for documents_root in document_roots:
        documents = documents_root / "Paradox Interactive" / "Victoria 3"
        databases.extend([documents / "launcher-v2.sqlite", documents / "launcher-v2" / "launcher-v2.sqlite"])
        registries.extend([documents / "launcher-v2" / "mods_registry.json", documents / "mods_registry.json"])
    db_unique = {str(item).casefold(): item for item in databases}; registry_unique = {str(item).casefold(): item for item in registries}
    return list(db_unique.values()), list(registry_unique.values())


def _value(row: sqlite3.Row, *names, default=None):
    lookup = {key.casefold(): row[key] for key in row.keys()}
    for name in names:
        if name.casefold() in lookup and lookup[name.casefold()] is not None: return lookup[name.casefold()]
    return default


class ParadoxLauncherProvider(ModSourceProvider):
    def __init__(self, database_paths: list[Path] | None = None, registry_paths: list[Path] | None = None) -> None:
        defaults = default_launcher_candidates(); self.database_paths = database_paths if database_paths is not None else defaults[0]; self.registry_paths = registry_paths if registry_paths is not None else defaults[1]; self.warnings: list[str] = []
    @property
    def provider_id(self) -> str: return ModSource.PARADOX_LAUNCHER.value

    def discover(self) -> list[ModEntry]:
        self.warnings = []; found: list[ModEntry] = []
        for database in self.database_paths:
            if not Path(database).is_file(): continue
            try: found.extend(self._read_database(Path(database)))
            except (sqlite3.Error, OSError, ValueError) as error: self.warnings.append(f"{database}: {error}")
        if not found:
            for registry in self.registry_paths:
                if not Path(registry).is_file(): continue
                try: found.extend(self._read_registry(Path(registry)))
                except (OSError, json.JSONDecodeError, TypeError) as error: self.warnings.append(f"{registry}: {error}")
        unique = {entry.id.casefold(): entry for entry in found}
        return sorted(unique.values(), key=lambda item: ((item.load_order_position is None), item.load_order_position or 0, item.name.casefold()))

    def _read_database(self, path: Path) -> list[ModEntry]:
        uri = f"file:{quote(path.resolve().as_posix(), safe='/:')}?mode=ro"
        connection = sqlite3.connect(uri, uri=True); connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA query_only=ON")
            tables = {row[0].casefold(): row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            mods_table = tables.get("mods")
            if not mods_table: raise ValueError("mods table not found")
            playset_map = self._playset_map(connection, tables)
            rows = connection.execute(f'SELECT * FROM "{mods_table}"').fetchall()
            result: list[ModEntry] = []
            for row in rows:
                mod_id = str(_value(row, "id", "modId", "gameRegistryId", default=""))
                steam_id = str(_value(row, "steamId", "remoteSteamId", "workshopId", default=""))
                path_text = str(_value(row, "dirPath", "path", "archivePath", default="") or "")
                mod_path = Path(path_text) if path_text else None
                mapping = playset_map.get(mod_id, {})
                if mod_path and mod_path.is_dir():
                    entry = mod_entry_from_folder(mod_path, ModSource.PARADOX_LAUNCHER, workshop_id=steam_id, enabled=mapping.get("enabled"), position=mapping.get("position"), playset=str(mapping.get("playset", "")), metadata={"launcher_database": str(path)})
                    entry = ModEntry(**{**entry.__dict__, "mod_id": mod_id or entry.mod_id, "name": str(_value(row, "displayName", "name", default=entry.name))})
                else:
                    entry = ModEntry(name=str(_value(row, "displayName", "name", default=mod_id or steam_id or "Unknown Mod")), path=mod_path, source=ModSource.PARADOX_LAUNCHER, mod_id=mod_id, workshop_id=steam_id, enabled=mapping.get("enabled"), load_order_position=mapping.get("position"), playset=str(mapping.get("playset", "")), metadata={"launcher_database": str(path)})
                result.append(entry)
            return result
        finally: connection.close()

    def _playset_map(self, connection, tables) -> dict[str, dict]:
        relation = next((tables[name] for name in ("playsets_mods", "playsetsmods", "playset_mods") if name in tables), None)
        if not relation: return {}
        playset_names = {}
        if tables.get("playsets"):
            for row in connection.execute(f'SELECT * FROM "{tables["playsets"]}"'):
                playset_names[str(_value(row, "id", default=""))] = str(_value(row, "name", default=""))
        result = {}
        for row in connection.execute(f'SELECT * FROM "{relation}"'):
            mod_id = str(_value(row, "modId", "mod_id", "mod", default="")); playset_id = str(_value(row, "playsetId", "playset_id", "playset", default=""))
            if not mod_id: continue
            enabled_value = _value(row, "enabled", "isEnabled", default=None)
            enabled = bool(enabled_value) if enabled_value is not None else None
            position = _value(row, "position", "loadOrder", "order", default=None)
            try: position = int(position) if position is not None else None
            except (TypeError, ValueError): position = None
            result.setdefault(mod_id, {"enabled": enabled, "position": position, "playset": playset_names.get(playset_id, playset_id)})
        return result

    def _read_registry(self, path: Path) -> list[ModEntry]:
        data = json.loads(path.read_text(encoding="utf-8-sig")); values = data.get("mods", data) if isinstance(data, dict) else data
        if isinstance(values, dict): values = list(values.values())
        result = []
        for item in values if isinstance(values, list) else []:
            if not isinstance(item, dict): continue
            path_text = item.get("dirPath") or item.get("path") or item.get("archivePath"); mod_path = Path(str(path_text)) if path_text else None
            if mod_path and mod_path.is_dir():
                result.append(mod_entry_from_folder(mod_path, ModSource.PARADOX_LAUNCHER, workshop_id=str(item.get("steamId") or item.get("workshop_id") or ""), enabled=item.get("enabled"), position=item.get("position"), playset=str(item.get("playset") or ""), metadata={"launcher_registry": str(path)}))
            else:
                result.append(ModEntry(name=str(item.get("displayName") or item.get("name") or "Unknown Mod"), path=mod_path, source=ModSource.PARADOX_LAUNCHER, mod_id=str(item.get("id") or ""), workshop_id=str(item.get("steamId") or ""), enabled=item.get("enabled"), load_order_position=item.get("position"), metadata={"launcher_registry": str(path)}))
        return result
