import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from app.archive.zip_extractor import safely_extract_members, validate_archive
from app.backup.backup_manager import backup_file, create_backup_root
from app.errors import (
    ArchiveValidationError,
    DuplicateTargetError,
    OperationCancelled,
)
from app.models import ImportFile, InstallResult, OverwritePolicy
from app.utils.paths import app_temp_root


def _zip_path(name: str) -> PurePosixPath:
    return PurePosixPath(name.replace("\\", "/"))


def _localization_index(parts: tuple[str, ...], target_language: str) -> int | None:
    folded = [part.casefold() for part in parts]
    for index in range(len(folded) - 1):
        if folded[index] == "localization" and folded[index + 1] == target_language.casefold():
            return index
    return None


def _plan_from_infos(infos: list[zipfile.ZipInfo], target_language: str = "korean") -> list[ImportFile]:
    yml_infos = [
        info
        for info in infos
        if not info.is_dir() and _zip_path(info.filename).suffix.lower() == ".yml"
    ]
    preferred = [
        info
        for info in yml_infos
        if _localization_index(_zip_path(info.filename).parts, target_language) is not None
    ]
    selected = preferred or yml_infos
    if not selected:
        raise ArchiveValidationError("ZIP 안에서 YML 파일을 찾지 못했습니다.")

    planned: list[ImportFile] = []
    targets: dict[str, str] = {}
    for info in selected:
        archive_path = _zip_path(info.filename)
        index = _localization_index(archive_path.parts, target_language)
        if index is None:
            relative = Path("localization", target_language, archive_path.name)
        else:
            relative = Path(*archive_path.parts[index:])
        key = relative.as_posix().casefold()
        if key in targets:
            raise DuplicateTargetError(
                f"ZIP 안의 두 파일이 같은 위치에 설치됩니다: {targets[key]} / {info.filename}"
            )
        targets[key] = info.filename
        planned.append(ImportFile(info.filename, relative, info.file_size))
    return sorted(planned, key=lambda item: item.install_relative_path.as_posix().casefold())


def inspect_translation_zip(zip_path: Path, target_language: str = "korean") -> list[ImportFile]:
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            infos = validate_archive(archive)
            return _plan_from_infos(infos, target_language)
    except (zipfile.BadZipFile, OSError) as error:
        raise ArchiveValidationError(
            "번역 ZIP을 읽을 수 없습니다. 파일이 손상되었거나 올바른 ZIP이 아닐 수 있습니다."
        ) from error


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".v3mm_", dir=destination.parent)
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def install_translation_zip(
    zip_path: Path, install_root: Path, policy: OverwritePolicy, target_language: str = "korean"
) -> InstallResult:
    if policy is OverwritePolicy.CANCEL:
        raise OperationCancelled("사용자가 설치를 취소했습니다.")

    planned = inspect_translation_zip(zip_path, target_language)
    install_root = Path(install_root)
    install_root.mkdir(parents=True, exist_ok=True)
    result = InstallResult()
    backup_root: Path | None = None
    logger = logging.getLogger("v3mm")
    logger.info("Translation installation started (%d files)", len(planned))

    with tempfile.TemporaryDirectory(prefix="job_", dir=app_temp_root()) as temp_name:
        temp_dir = Path(temp_name)
        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                infos = validate_archive(archive)
                by_name = {info.filename: info for info in infos}
                selected_infos = [by_name[item.archive_name] for item in planned]
                extracted = safely_extract_members(archive, selected_infos, temp_dir)
        except (zipfile.BadZipFile, OSError) as error:
            raise ArchiveValidationError("번역 ZIP 압축 해제에 실패했습니다.") from error

        root_resolved = install_root.resolve()
        for item in planned:
            destination = install_root / item.install_relative_path
            parent_resolved = destination.parent.resolve()
            if root_resolved != parent_resolved and root_resolved not in parent_resolved.parents:
                raise ArchiveValidationError("설치 대상 경로가 지정 폴더를 벗어납니다.")
            if destination.exists():
                if policy is OverwritePolicy.SKIP:
                    result.skipped.append(destination)
                    continue
                if policy is OverwritePolicy.BACKUP_AND_OVERWRITE:
                    if backup_root is None:
                        backup_root = create_backup_root(install_root)
                    result.backed_up.append(
                        backup_file(destination, item.install_relative_path, backup_root)
                    )
            _atomic_copy(extracted[item.archive_name], destination)
            result.installed.append(destination)

    logger.info(
        "Translation installation completed (installed=%d, skipped=%d, backups=%d)",
        len(result.installed),
        len(result.skipped),
        len(result.backed_up),
    )
    return result
