import os
import re
from pathlib import Path

from app.mod_sources.base_provider import ModSourceProvider
from app.mod_sources.descriptor import mod_entry_from_folder
from app.mod_sources.models import ModEntry, ModSource

VICTORIA3_APP_ID = "529340"
_VDF_PAIR = re.compile(r'^\s*"([^"]+)"\s+"([^"]+)"')


def _registry_steam_path() -> Path | None:
    try:
        import winreg
        for hive, key_name in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"), (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
            try:
                with winreg.OpenKey(hive, key_name) as key:
                    value, _ = winreg.QueryValueEx(key, "SteamPath" if hive == winreg.HKEY_CURRENT_USER else "InstallPath")
                    if value: return Path(value)
            except OSError: continue
    except (ImportError, OSError): pass
    return None


def default_steam_roots() -> list[Path]:
    candidates = [_registry_steam_path()]
    for variable in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        if os.environ.get(variable): candidates.append(Path(os.environ[variable]) / "Steam")
    return [item for item in candidates if item and item.exists()]


def read_library_paths(steam_root: Path) -> list[Path]:
    roots = [Path(steam_root)]
    vdf = Path(steam_root) / "steamapps" / "libraryfolders.vdf"
    try:
        for line in vdf.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            match = _VDF_PAIR.match(line)
            if not match: continue
            key, value = match.groups()
            if key.casefold() == "path" or key.isdigit():
                candidate = Path(value.replace("\\\\", "\\"))
                if (candidate / "steamapps").is_dir(): roots.append(candidate)
    except OSError: pass
    unique = {str(path.resolve()).casefold(): path.resolve() for path in roots if path.exists()}
    return list(unique.values())


class SteamModSourceProvider(ModSourceProvider):
    def __init__(self, steam_roots: list[Path] | None = None) -> None:
        self.steam_roots = steam_roots
        self.warnings: list[str] = []

    @property
    def provider_id(self) -> str: return ModSource.STEAM_WORKSHOP.value

    def discover(self) -> list[ModEntry]:
        self.warnings = []; roots = self.steam_roots if self.steam_roots is not None else default_steam_roots()
        libraries: list[Path] = []
        for root in roots: libraries.extend(read_library_paths(root))
        found: list[ModEntry] = []
        for library in {str(path).casefold(): path for path in libraries}.values():
            workshop = library / "steamapps" / "workshop" / "content" / VICTORIA3_APP_ID
            if not workshop.is_dir(): continue
            try: children = list(workshop.iterdir())
            except OSError as error: self.warnings.append(str(error)); continue
            for folder in children:
                if not folder.is_dir(): continue
                try: found.append(mod_entry_from_folder(folder, ModSource.STEAM_WORKSHOP, workshop_id=folder.name, metadata={"steam_library": str(library)}))
                except OSError as error: self.warnings.append(f"{folder}: {error}")
        unique = {entry.id.casefold(): entry for entry in found}
        return sorted(unique.values(), key=lambda item: item.name.casefold())
