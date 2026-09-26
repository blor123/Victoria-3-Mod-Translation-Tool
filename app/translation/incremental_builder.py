from pathlib import Path

from app.archive.zip_creator import create_zip
from app.errors import DuplicateTargetError, InputValidationError
from app.i18n.language_definition import LanguageDefinition
from app.models import PackageFile, PackageReport
from app.translation.package_builder import plan_package
from app.validation.manifest import save_manifest


def build_incremental_package(diff, localization_root: Path, destination: Path, target: LanguageDefinition, prompt_version: int) -> PackageReport:
    selected = diff.translatable
    if not selected: raise InputValidationError("No new or changed localization entries were found.")
    grouped: dict[str, list] = {}
    for item in selected: grouped.setdefault(item.relative_path, []).append(item)
    files: list[PackageFile] = []; targets: set[str] = set(); root = Path(localization_root)
    for relative, items in sorted(grouped.items()):
        source = root / Path(relative); template = plan_package([source], target)[0]
        key = template.archive_path.as_posix().casefold()
        if key in targets: raise DuplicateTargetError(f"Incremental output collision: {template.archive_path}")
        targets.add(key)
        lines = [target.localization_header] + [item.raw_line for item in items]
        content = ("\ufeff" + "\n".join(lines) + "\n").encode("utf-8")
        files.append(PackageFile(source, template.archive_path, content, "incremental", "", template.source_language, target.filename_suffix, template.filename_changed, True, "incremental"))
    create_zip(files, destination); manifest_id = save_manifest(files, target, prompt_version)
    return PackageReport(files, sum(len(item.content or b"") for item in files), sum(item.filename_changed for item in files), len(files), target.filename_suffix, manifest_id)
