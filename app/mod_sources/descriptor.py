import re
from pathlib import Path

from app.mod_sources.models import ModEntry, ModSource

_PAIR = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*"([^"]*)"')


def parse_descriptor(path: Path | None) -> dict[str, str]:
    if not path or not Path(path).is_file(): return {}
    result: dict[str, str] = {}
    try:
        for line in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
            match = _PAIR.match(line)
            if match: result[match.group(1)] = match.group(2)
    except OSError: return {}
    return result


def find_localizations(root: Path | None) -> tuple[Path, ...]:
    if not root or not Path(root).is_dir(): return ()
    localization = Path(root) / "localization"
    if not localization.is_dir(): return ()
    found = [path for path in localization.iterdir() if path.is_dir() and any(path.rglob("*.yml"))]
    if not found and any(localization.rglob("*.yml")): found = [localization]
    return tuple(sorted(found, key=lambda item: str(item).casefold()))


def mod_entry_from_folder(folder: Path, source: ModSource, *, workshop_id: str = "", enabled=None, position=None, playset="", metadata=None) -> ModEntry:
    folder = Path(folder).resolve(); descriptor = folder / "descriptor.mod"
    if not descriptor.exists():
        candidates = list(folder.glob("*.mod")); descriptor = candidates[0] if candidates else None
    values = parse_descriptor(descriptor)
    actual_path = folder
    declared = values.get("path")
    if declared and Path(declared).is_dir(): actual_path = Path(declared).resolve()
    workshop = workshop_id or values.get("remote_file_id", "")
    try: modified = actual_path.stat().st_mtime
    except OSError: modified = None
    return ModEntry(
        name=values.get("name") or folder.name, path=actual_path, source=source,
        mod_id=workshop or str(actual_path), workshop_id=workshop, descriptor_path=descriptor,
        version=values.get("version", ""), supported_game_version=values.get("supported_version", ""),
        enabled=enabled, load_order_position=position, localization_paths=find_localizations(actual_path),
        playset=playset, modified_time=modified, metadata=metadata or {},
    )
