from dataclasses import dataclass
from pathlib import Path

from app.mod_sources.models import ModEntry


@dataclass(frozen=True)
class ModFileRecord:
    mod_id: str
    relative_path: str
    size: int
    modified_time: float


class ModFileIndexer:
    """Read-only file inventory consumed by the future conflict analyzer."""
    def build(self, entry: ModEntry) -> list[ModFileRecord]:
        if not entry.path or not entry.path.is_dir(): return []
        records = []
        for path in entry.path.rglob("*"):
            if path.is_symlink() or not path.is_file(): continue
            try:
                stat = path.stat(); records.append(ModFileRecord(entry.id, path.relative_to(entry.path).as_posix(), stat.st_size, stat.st_mtime))
            except OSError: continue
        return sorted(records, key=lambda item: item.relative_path.casefold())
