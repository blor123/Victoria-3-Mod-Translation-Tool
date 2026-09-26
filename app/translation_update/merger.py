import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.archive.zip_extractor import validate_archive
from app.errors import ArchiveValidationError, InputValidationError
from app.translation.package_importer import inspect_translation_zip
from app.utils.file_scanner import scan_yml_files

_KEY = re.compile(r'^\s*([A-Za-z0-9_.-]+):\d*\s+"')


@dataclass(frozen=True)
class MergeReport:
    destination: Path
    files: int
    replaced: int
    added: int
    preserved: int


def _read_update(zip_path: Path, target_suffix: str) -> tuple[dict[str, str], dict[str, str]]:
    planned = inspect_translation_zip(zip_path, target_suffix)
    lines: dict[str, str] = {}; file_for_key: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        infos = {item.filename: item for item in validate_archive(archive)}
        for item in planned:
            text = archive.read(infos[item.archive_name]).decode("utf-8-sig")
            for line in text.splitlines():
                match = _KEY.match(line)
                if match:
                    key = match.group(1)
                    if key in lines: raise ArchiveValidationError(f"Duplicate localization key in update ZIP: {key}")
                    lines[key] = line
                    parts = item.install_relative_path.parts
                    file_for_key[key] = PurePosixPath(*parts[2:]).as_posix() if len(parts) > 2 else item.install_relative_path.name
    if not lines: raise InputValidationError("The update ZIP contains no localization entries.")
    return lines, file_for_key


def _existing_files(root: Path, target_suffix: str) -> list[Path]:
    files = scan_yml_files([root])
    preferred = [p for p in files if target_suffix.casefold() in [x.casefold() for x in p.parts]]
    return preferred or files


def _output_relative(source: Path, root: Path, target_suffix: str) -> str:
    parts = source.parts; folded = [part.casefold() for part in parts]
    for index in range(len(parts) - 1):
        if folded[index] == "localization" and folded[index + 1] == target_suffix.casefold():
            return PurePosixPath(*parts[index + 2:]).as_posix()
    try: return source.relative_to(root).as_posix()
    except ValueError: return source.name


def build_merged_translation_zip(existing_root: Path, update_zip: Path, destination: Path, target_suffix: str, header: str) -> MergeReport:
    """Create a preview ZIP. Existing files are never changed; installation performs backup."""
    existing_root = Path(existing_root); destination = Path(destination)
    if not existing_root.exists(): raise InputValidationError("Existing translation path does not exist.")
    updates, update_files = _read_update(Path(update_zip), target_suffix)
    outputs: dict[str, list[str]] = {}; replaced = 0; preserved = 0
    for source in _existing_files(existing_root, target_suffix):
        text = source.read_text(encoding="utf-8-sig", errors="replace"); result = []
        for line in text.splitlines():
            match = _KEY.match(line)
            if match and match.group(1) in updates:
                result.append(updates.pop(match.group(1))); replaced += 1
            else:
                result.append(line)
                if match: preserved += 1
        outputs[_output_relative(source, existing_root, target_suffix)] = result
    added = len(updates)
    for key, line in updates.items():
        name = update_files[key]
        outputs.setdefault(name, [header]).append(line)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="v3mm_merge_", suffix=".zip", dir=destination.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, lines in sorted(outputs.items()):
                relative = PurePosixPath(name)
                if relative.is_absolute() or ".." in relative.parts: raise ArchiveValidationError("Unsafe merge output path.")
                archive.writestr(f"localization/{target_suffix}/{relative.as_posix()}", ("\ufeff" + "\n".join(lines) + "\n").encode("utf-8"))
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return MergeReport(destination, len(outputs), replaced, added, preserved)
