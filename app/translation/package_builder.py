import logging
from pathlib import Path, PurePosixPath

from app.archive.zip_creator import create_zip
from app.errors import DuplicateTargetError, InputValidationError
from app.i18n.language_definition import KNOWN_SUFFIXES, LanguageDefinition, target_language
from app.models import PackageFile, PackageReport
from app.translation.filename_converter import convert_localization_filename, detect_filename_language
from app.translation.language_header import convert_language_declaration
from app.utils.file_scanner import scan_yml_files
from app.validation.manifest import save_manifest


def _archive_path(source: Path, target: LanguageDefinition) -> PurePosixPath:
    parts = list(source.parts); folded = [part.casefold() for part in parts]
    localization = [i for i, part in enumerate(folded) if part == "localization"]
    filename = convert_localization_filename(source.name, target.filename_suffix)
    if localization:
        tail = parts[localization[-1] + 1:]
        if tail and tail[0].casefold() in KNOWN_SUFFIXES: tail = tail[1:]
        if tail: tail[-1] = filename
        else: tail = [filename]
        return PurePosixPath("localization", target.filename_suffix, *tail)
    language_dirs = [i for i, part in enumerate(folded[:-1]) if part in KNOWN_SUFFIXES]
    if language_dirs:
        tail = parts[language_dirs[-1] + 1:]; tail[-1] = filename
        return PurePosixPath("localization", target.filename_suffix, *tail)
    return PurePosixPath("localization", target.filename_suffix, filename)


def plan_package(inputs: list[Path], target: LanguageDefinition | str = "korean") -> list[PackageFile]:
    if isinstance(target, str):
        target = next((item for item in map(target_language, ("ko-KR", "en-US", "zh-CN", "ja-JP")) if item.filename_suffix == target), target_language("ko-KR"))
    planned: list[PackageFile] = []; targets: dict[str, Path] = {}
    for source in scan_yml_files(inputs):
        archive_path = _archive_path(source, target); key = archive_path.as_posix().casefold()
        if key in targets: raise DuplicateTargetError(f"Output filename collision: {targets[key]} / {source} -> {archive_path}")
        targets[key] = source
        original = source.read_bytes(); header = convert_language_declaration(original, target.filename_suffix)
        filename_language = detect_filename_language(source.name)
        warnings = []
        if header.warning: warnings.append(header.warning)
        if filename_language != "unknown" and header.source_language != "unknown" and filename_language != header.source_language:
            warnings.append("filename_header_mismatch")
        output_name = archive_path.name
        planned.append(PackageFile(source, archive_path, header.content, header.status, ",".join(warnings), filename_language if filename_language != "unknown" else header.source_language, target.filename_suffix, source.name != output_name, header.status == "changed", "already_target_language" if source.name == output_name and header.status == "already_target" else ""))
    if not planned: raise InputValidationError("Localization YML files were not found.")
    return planned


def build_translation_package(inputs: list[Path], destination: Path, target: LanguageDefinition | str = "korean") -> list[PackageFile]:
    files = plan_package(inputs, target); create_zip(files, destination); return files


def build_translation_package_report(inputs: list[Path], destination: Path, target: LanguageDefinition | str = "korean", prompt_version: int = 2) -> PackageReport:
    if isinstance(target, str):
        target = next((item for item in map(target_language, ("ko-KR", "en-US", "zh-CN", "ja-JP")) if item.filename_suffix == target), target_language("ko-KR"))
    logger = logging.getLogger("v3mm"); logger.info("Translation package creation started")
    files = plan_package(inputs, target); create_zip(files, destination)
    manifest_id = save_manifest(files, target, prompt_version)
    logger.info("ZIP created successfully (%d files, target=%s)", len(files), target.filename_suffix)
    return PackageReport(files, sum(len(item.content or b"") for item in files), sum(item.filename_changed for item in files), sum(item.header_changed for item in files), target.filename_suffix, manifest_id)
