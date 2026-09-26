from dataclasses import dataclass
from pathlib import Path

from app.i18n.language_definition import KNOWN_SUFFIXES, LanguageDefinition


@dataclass(frozen=True)
class ProjectPaths:
    mod_root: Path
    localization_path: Path | None
    install_root: Path
    proposed_target_path: Path
    yml_count: int


def detect_project_paths(mod_root: Path, target: LanguageDefinition) -> ProjectPaths:
    root = Path(mod_root).resolve(); localization = root / "localization"; detected = None
    if localization.is_dir():
        preferred = localization / "english"
        candidates = [preferred] + [localization / name for name in KNOWN_SUFFIXES if name != "english"] + [localization]
        for candidate in candidates:
            if candidate.is_dir() and any(path.is_file() for path in candidate.rglob("*.yml")):
                detected = candidate; break
    count = sum(1 for path in detected.rglob("*.yml") if path.is_file()) if detected else 0
    return ProjectPaths(root, detected, root, localization / target.filename_suffix, count)


def resolve_localization_path(project: dict, target: LanguageDefinition) -> Path:
    configured = Path(str(project.get("localization_path", "")))
    if configured.is_dir() and configured.name.casefold() in KNOWN_SUFFIXES:
        return configured
    source = Path(str(project.get("source_path", "")))
    detected = detect_project_paths(source, target) if source.is_dir() else None
    if detected and detected.localization_path: return detected.localization_path
    return configured if configured.is_dir() else source
