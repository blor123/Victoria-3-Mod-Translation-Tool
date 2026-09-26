import re
from pathlib import Path

from app.i18n.language_definition import KNOWN_SUFFIXES

_SUFFIX = re.compile(
    rf"_(?P<language>{'|'.join(map(re.escape, KNOWN_SUFFIXES))})$", re.IGNORECASE
)


def detect_filename_language(filename: str) -> str:
    match = _SUFFIX.search(Path(filename).stem)
    return match.group("language").casefold() if match else "unknown"


def convert_localization_filename(filename: str, target_language: str = "korean") -> str:
    path = Path(filename)
    if path.suffix.casefold() not in {".yml", ".yaml"}:
        return filename
    match = _SUFFIX.search(path.stem)
    stem = _SUFFIX.sub(f"_{target_language}", path.stem) if match else f"{path.stem}_{target_language}"
    return stem + path.suffix
