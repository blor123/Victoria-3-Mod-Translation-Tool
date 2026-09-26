from dataclasses import dataclass
from pathlib import Path

from app.i18n.language_definition import target_language
from app.mod_sources.models import ModEntry
from app.snapshots import SnapshotManager, capture_localization


@dataclass(frozen=True)
class LibraryState:
    project: dict | None
    translation_exists: bool
    update_needed: bool
    source_changed: bool


class ModLibraryService:
    def __init__(self, import_manager, project_manager, snapshot_manager=None) -> None:
        self.imports = import_manager; self.projects = project_manager; self.snapshots = snapshot_manager or SnapshotManager()
    def project_for(self, entry: ModEntry) -> dict | None:
        if entry.project_id:
            linked = next((item for item in self.projects.projects if item.get("id") == entry.project_id), None)
            if linked: return linked
        if not entry.path: return None
        root = entry.path.resolve()
        for project in self.projects.projects:
            for key in ("source_path", "localization_path"):
                value = Path(str(project.get(key, "")))
                if not value.exists(): continue
                resolved = value.resolve()
                if resolved == root or root in resolved.parents or resolved in root.parents: return project
        return None
    def link_project(self, entry: ModEntry, project_id: str) -> ModEntry:
        updated = ModEntry(**{**entry.__dict__, "project_id": project_id}); self.imports.update_entry(updated); return updated
    def state(self, entry: ModEntry) -> LibraryState:
        project = self.project_for(entry); translation = any(path.name.casefold() != "english" for path in entry.localization_paths); changed = False
        if project:
            language = target_language(str(project.get("target_language") or "ko-KR")); install = Path(str(project.get("install_path", ""))) / "localization" / language.filename_suffix
            translation = translation or (install.is_dir() and any(install.rglob("*.yml")))
            snapshot = self.snapshots.latest(str(project.get("id", "")))
            source = Path(str(project.get("localization_path") or project.get("source_path", "")))
            if snapshot and source.exists():
                try: changed = capture_localization(source).get("hash") != snapshot.get("hash")
                except Exception: changed = False
        return LibraryState(project, translation, bool(project and translation and changed), changed)
