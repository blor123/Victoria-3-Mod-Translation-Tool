from pathlib import Path

from app.mod_sources.base_provider import ModSourceProvider
from app.mod_sources.descriptor import mod_entry_from_folder, parse_descriptor
from app.mod_sources.models import ModEntry, ModSource


class ManualModSourceProvider(ModSourceProvider):
    def __init__(self, paths: list[Path] | None = None) -> None:
        self.paths = paths or []

    @property
    def provider_id(self) -> str:
        return ModSource.MANUAL.value

    def discover(self) -> list[ModEntry]:
        found: list[ModEntry] = []
        for raw in self.paths:
            path = Path(raw)
            if not path.exists(): continue
            if path.is_file() and path.suffix.casefold() == ".mod":
                values = parse_descriptor(path); target = Path(values.get("path", path.parent))
                if not target.is_absolute(): target = path.parent / target
                if target.exists(): found.append(mod_entry_from_folder(target, ModSource.MANUAL, metadata={"registry_descriptor": str(path)}))
                continue
            if (path / "descriptor.mod").exists() or (path / "localization").exists():
                found.append(mod_entry_from_folder(path, ModSource.MANUAL)); continue
            for child in path.iterdir():
                if child.is_dir() and ((child / "descriptor.mod").exists() or (child / "localization").exists()): found.append(mod_entry_from_folder(child, ModSource.MANUAL))
        unique = {entry.id.casefold(): entry for entry in found}
        return sorted(unique.values(), key=lambda item: item.name.casefold())
