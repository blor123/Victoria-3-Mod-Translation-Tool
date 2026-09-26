import json
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.errors import InputValidationError

FORMAT = "v3mm_loadout"


class LoadoutManager(QObject):
    changed = Signal()
    def __init__(self, config) -> None: super().__init__(); self.config = config
    @property
    def loadouts(self) -> list[dict]: return [dict(item) for item in self.config.data.get("loadouts", []) if isinstance(item, dict)]
    @property
    def active_id(self) -> str: return str(self.config.data.get("active_loadout_id", ""))
    def active(self) -> dict | None: return next((item for item in self.loadouts if item.get("id") == self.active_id), None)
    def create(self, name: str) -> dict:
        data = {"id": uuid.uuid4().hex, "name": name.strip() or "Loadout", "mods": [], "created_at": datetime.now().isoformat(timespec="minutes"), "updated_at": datetime.now().isoformat(timespec="minutes")}
        values = self.loadouts + [data]; self.config.update(loadouts=values, active_loadout_id=data["id"]); self.changed.emit(); return data
    def select(self, loadout_id: str) -> None: self.config.update(active_loadout_id=loadout_id); self.changed.emit()
    def save(self, loadout_id: str, states: list[dict]) -> None:
        values = self.loadouts; found = False
        for item in values:
            if item.get("id") == loadout_id: item["mods"] = sorted(states, key=lambda value: int(value.get("position", 0))); item["updated_at"] = datetime.now().isoformat(timespec="minutes"); found = True
        if not found: raise InputValidationError("선택한 V3MM Loadout을 찾지 못했습니다.")
        self.config.update(loadouts=values); self.changed.emit()
    def remove(self, loadout_id: str) -> None:
        values = [item for item in self.loadouts if item.get("id") != loadout_id]; active = values[0]["id"] if values else ""; self.config.update(loadouts=values, active_loadout_id=active); self.changed.emit()
    def state_for(self, mod_id: str, default_enabled=None, default_position=None) -> tuple[bool, int]:
        active = self.active(); state = next((item for item in active.get("mods", []) if item.get("mod_id") == mod_id), None) if active else None
        return (bool(state.get("enabled", True)), int(state.get("position", 0))) if state else (default_enabled is not False, int(default_position or 0))
    def export_file(self, path: Path, loadout_id: str | None = None) -> Path:
        loadout = next((item for item in self.loadouts if item.get("id") == (loadout_id or self.active_id)), None)
        if not loadout: raise InputValidationError("내보낼 Loadout이 없습니다.")
        payload = {"format": FORMAT, "version": 1, "game": "victoria3", "loadout": loadout}; path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); temp = path.with_name(path.name + ".tmp"); temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"); temp.replace(path); return path
    def import_file(self, path: Path) -> dict:
        try: payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error: raise InputValidationError("Loadout JSON을 읽을 수 없습니다.") from error
        if not isinstance(payload, dict) or payload.get("format") != FORMAT or not isinstance(payload.get("loadout"), dict): raise InputValidationError("지원하지 않는 V3MM Loadout 형식입니다.")
        incoming = dict(payload["loadout"]); incoming["id"] = uuid.uuid4().hex; incoming.setdefault("name", Path(path).stem); incoming["mods"] = [item for item in incoming.get("mods", []) if isinstance(item, dict) and item.get("mod_id")]; incoming["updated_at"] = datetime.now().isoformat(timespec="minutes")
        self.config.update(loadouts=self.loadouts + [incoming], active_loadout_id=incoming["id"], last_loadout_path=str(path)); self.changed.emit(); return incoming
