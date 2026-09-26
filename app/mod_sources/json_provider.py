import json
from pathlib import Path

from app.errors import InputValidationError
from app.mod_sources.base_provider import ModSourceProvider
from app.mod_sources.descriptor import mod_entry_from_folder, parse_descriptor
from app.mod_sources.models import ModEntry, ModSource

FORMAT = "v3mm_mod_list"
FORMAT_VERSION = 1


def _resolve_path(value, base: Path) -> Path | None:
    if not value: return None
    path = Path(str(value).replace("file://", ""))
    return path if path.is_absolute() else (base / path).resolve()


class JsonModSourceProvider(ModSourceProvider):
    def __init__(self, path: Path) -> None: self.path = Path(path); self.warnings: list[str] = []
    @property
    def provider_id(self) -> str: return ModSource.JSON_IMPORT.value

    def discover(self) -> list[ModEntry]:
        self.warnings = []
        try: data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error: raise InputValidationError("Mod List JSON을 읽을 수 없습니다.") from error
        values = self._extract_values(data)
        entries: list[ModEntry] = []
        for position, item in enumerate(values):
            try:
                entry = self._entry(item, position)
                if entry: entries.append(entry)
            except (OSError, TypeError, ValueError) as error: self.warnings.append(f"item {position + 1}: {error}")
        if not entries: raise InputValidationError("JSON에서 가져올 Mod 항목을 찾지 못했습니다. V3MM Mod List, mods 배열 또는 enabled_mods 목록을 지원합니다.")
        unique = {entry.id.casefold(): entry for entry in entries}
        return sorted(unique.values(), key=lambda item: ((item.load_order_position is None), item.load_order_position or 0, item.name.casefold()))

    def _extract_values(self, data) -> list:
        if isinstance(data, list): return data
        if not isinstance(data, dict): raise InputValidationError("JSON 최상위 값은 객체 또는 배열이어야 합니다.")
        for key in ("mods", "mod_list", "items", "entries"):
            values = data.get(key)
            if isinstance(values, list): return values
            if isinstance(values, dict): return [dict(value, id=value.get("id", item_key)) if isinstance(value, dict) else value for item_key, value in values.items()]
        if isinstance(data.get("enabled_mods"), list):
            enabled = [{"path": value, "enabled": True, "position": index} for index, value in enumerate(data["enabled_mods"])]
            disabled = [{"path": value, "enabled": False} for value in data.get("disabled_mods", [])]
            return enabled + disabled
        # mods_registry.json sometimes stores entries directly by registry id.
        object_values = [dict(value, id=value.get("id", key)) for key, value in data.items() if isinstance(value, dict)]
        if object_values: return object_values
        raise InputValidationError("지원하는 Mod 목록 필드를 찾지 못했습니다.")

    def _entry(self, item, position: int) -> ModEntry | None:
        base = self.path.parent
        if isinstance(item, str): item = {"path": item, "enabled": True, "position": position}
        if not isinstance(item, dict): return None
        raw_path = item.get("path") or item.get("dirPath") or item.get("descriptor_path") or item.get("archivePath")
        path = _resolve_path(raw_path, base); descriptor = path if path and path.is_file() and path.suffix.casefold() == ".mod" else None
        if descriptor:
            values = parse_descriptor(descriptor); declared = _resolve_path(values.get("path"), descriptor.parent)
            if declared and declared.is_dir():
                entry = mod_entry_from_folder(declared, ModSource.JSON_IMPORT, workshop_id=str(item.get("workshop_id") or item.get("steamId") or values.get("remote_file_id", "")), enabled=item.get("enabled"), position=item.get("position", position), playset=str(item.get("playset") or ""), metadata={"json_source": str(self.path), "descriptor": str(descriptor)})
                return ModEntry(**{**entry.__dict__, "name": str(item.get("name") or item.get("displayName") or values.get("name") or entry.name), "mod_id": str(item.get("mod_id") or item.get("id") or entry.mod_id)})
        if path and path.is_dir():
            entry = mod_entry_from_folder(path, ModSource.JSON_IMPORT, workshop_id=str(item.get("workshop_id") or item.get("steamId") or ""), enabled=item.get("enabled"), position=item.get("position", position), playset=str(item.get("playset") or ""), metadata={"json_source": str(self.path)})
            return ModEntry(**{**entry.__dict__, "name": str(item.get("name") or item.get("displayName") or entry.name), "mod_id": str(item.get("mod_id") or item.get("id") or entry.mod_id), "project_id": str(item.get("project_id") or "")})
        normalized = dict(item); normalized["path"] = str(path) if path else ""; normalized.setdefault("position", position); normalized["metadata"] = {**dict(item.get("metadata") or {}), "json_source": str(self.path)}
        return ModEntry.from_dict(normalized, ModSource.JSON_IMPORT)


def export_mod_list(entries: list[ModEntry], path: Path) -> Path:
    payload = {"format": FORMAT, "version": FORMAT_VERSION, "game": "victoria3", "mods": [entry.to_dict() for entry in entries]}
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"); temporary.replace(path)
    return path
