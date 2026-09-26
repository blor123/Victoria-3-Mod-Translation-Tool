import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class ProjectManager(QObject):
    changed = Signal()

    def __init__(self, config) -> None: super().__init__(); self.config = config
    @property
    def projects(self): return list(self.config.data.get("projects", []))

    def save_project(self, project: dict) -> dict:
        data = dict(project); data.setdefault("id", uuid.uuid4().hex); data["updated_at"] = datetime.now().isoformat(timespec="minutes"); data.setdefault("created_at", data["updated_at"])
        source = Path(str(data.get("source_path", "")))
        if not data.get("localization_path") and source.exists():
            candidate = source / "localization"
            if candidate.exists(): data["localization_path"] = str(candidate)
        projects = self.projects; projects = [data if p.get("id") == data["id"] else p for p in projects]
        if not any(p.get("id") == data["id"] for p in projects): projects.append(data)
        self.config.data["projects"] = projects; self.config.save(); self.changed.emit(); return data

    def remove(self, project_id: str) -> None:
        self.config.data["projects"] = [p for p in self.projects if p.get("id") != project_id]; self.config.save(); self.changed.emit()
