from collections.abc import Iterable
from pathlib import Path

from app.errors import InputValidationError


def scan_yml_files(inputs: Iterable[Path]) -> list[Path]:
    """Return unique YML files without following directory symlinks."""
    found: dict[str, Path] = {}
    for raw_path in inputs:
        path = Path(raw_path)
        if not path.exists():
            raise InputValidationError(f"입력 경로가 존재하지 않습니다: {path}")
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if candidate.suffix.lower() == ".yml":
                found[str(candidate.resolve()).casefold()] = candidate.resolve()
    if not found:
        raise InputValidationError("선택한 경로에서 YML 파일을 찾지 못했습니다.")
    return sorted(found.values(), key=lambda item: str(item).casefold())
