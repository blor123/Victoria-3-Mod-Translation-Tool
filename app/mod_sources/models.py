from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ModSource(str, Enum):
    MANUAL = "manual"
    STEAM_WORKSHOP = "steam_workshop"
    PARADOX_LAUNCHER = "paradox_launcher"
    JSON_IMPORT = "json_import"
    STEAM = "steam_workshop"       # v1.6 compatibility alias
    PARADOX = "paradox_launcher"
    JSON = "json_import"


@dataclass(frozen=True)
class ModEntry:
    name: str
    path: Path | None = None
    source: ModSource = ModSource.MANUAL
    mod_id: str = ""
    workshop_id: str = ""
    descriptor_path: Path | None = None
    version: str = ""
    supported_game_version: str = ""
    enabled: bool | None = None
    load_order_position: int | None = None
    localization_paths: tuple[Path, ...] = ()
    project_id: str = ""
    playset: str = ""
    modified_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.mod_id or self.workshop_id or (str(self.path) if self.path else self.name)

    def to_dict(self) -> dict:
        data = asdict(self); data["source"] = self.source.value
        for key in ("path", "descriptor_path"):
            data[key] = str(data[key]) if data[key] else ""
        data["localization_paths"] = [str(item) for item in self.localization_paths]
        return data

    @classmethod
    def from_dict(cls, data: dict, source_override: ModSource | None = None) -> "ModEntry":
        source_text = str(data.get("source") or data.get("source_type") or ModSource.JSON_IMPORT.value)
        try: source = source_override or ModSource(source_text)
        except ValueError: source = source_override or ModSource.JSON_IMPORT
        path = Path(str(data["path"])) if data.get("path") else None
        descriptor = Path(str(data["descriptor_path"])) if data.get("descriptor_path") else None
        localizations = tuple(Path(str(item)) for item in data.get("localization_paths", []) if item)
        position = data.get("load_order_position", data.get("position"))
        try: position = int(position) if position is not None else None
        except (TypeError, ValueError): position = None
        return cls(
            name=str(data.get("name") or data.get("display_name") or "Unknown Mod"), path=path,
            source=source, mod_id=str(data.get("mod_id") or data.get("id") or ""),
            workshop_id=str(data.get("workshop_id") or data.get("steam_id") or ""),
            descriptor_path=descriptor, version=str(data.get("version") or ""),
            supported_game_version=str(data.get("supported_game_version") or ""),
            enabled=data.get("enabled") if isinstance(data.get("enabled"), bool) else None,
            load_order_position=position, localization_paths=localizations,
            project_id=str(data.get("project_id") or ""), playset=str(data.get("playset") or ""),
            modified_time=float(data["modified_time"]) if data.get("modified_time") is not None else None,
            metadata=dict(data.get("metadata") or {}),
        )
