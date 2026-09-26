from PySide6.QtCore import QObject, Signal

from app.mod_sources.models import ModEntry


class ModImportManager(QObject):
    changed = Signal()

    def __init__(self, config) -> None: super().__init__(); self.config = config
    @property
    def entries(self) -> list[ModEntry]:
        return [ModEntry.from_dict(item) for item in self.config.data.get("imported_mods", []) if isinstance(item, dict)]
    def replace(self, entries: list[ModEntry]) -> None:
        self.config.update(imported_mods=[entry.to_dict() for entry in self._deduplicate(entries)]); self.changed.emit()
    def merge(self, entries: list[ModEntry]) -> list[ModEntry]:
        merged = self._deduplicate(self.entries + entries); self.config.update(imported_mods=[entry.to_dict() for entry in merged]); self.changed.emit(); return merged
    def clear(self) -> None: self.config.update(imported_mods=[]); self.changed.emit()
    def update_entry(self, updated: ModEntry) -> None:
        entries = [updated if entry.id == updated.id else entry for entry in self.entries]; self.replace(entries)
    @staticmethod
    def _deduplicate(entries: list[ModEntry]) -> list[ModEntry]:
        values = {}
        for entry in entries:
            key = (entry.workshop_id or (str(entry.path.resolve()) if entry.path and entry.path.exists() else entry.id)).casefold()
            values[key] = entry
        return sorted(values.values(), key=lambda item: item.name.casefold())
