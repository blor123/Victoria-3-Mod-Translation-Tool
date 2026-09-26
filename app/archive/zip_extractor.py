import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from app.errors import ArchiveValidationError

MAX_ARCHIVE_FILES = 5_000
MAX_UNCOMPRESSED_BYTES = 1_073_741_824


def _safe_member_path(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or path.is_absolute()
        or ".." in path.parts
        or (path.parts and ":" in path.parts[0])
    ):
        raise ArchiveValidationError(f"안전하지 않은 ZIP 내부 경로입니다: {name}")
    return path


def validate_archive(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_FILES:
        raise ArchiveValidationError("ZIP에 파일이 너무 많습니다.")
    if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
        raise ArchiveValidationError("ZIP 압축 해제 크기가 안전 제한을 초과합니다.")
    for info in infos:
        _safe_member_path(info.filename)
        unix_mode = info.external_attr >> 16
        if unix_mode and stat.S_ISLNK(unix_mode):
            raise ArchiveValidationError("ZIP 안의 심볼릭 링크는 허용되지 않습니다.")
        if info.flag_bits & 0x1:
            raise ArchiveValidationError("암호화된 ZIP은 지원하지 않습니다.")
    return infos


def safely_extract_members(
    archive: zipfile.ZipFile, members: list[zipfile.ZipInfo], destination: Path
) -> dict[str, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    root = destination.resolve()
    for info in members:
        relative = _safe_member_path(info.filename)
        if info.is_dir():
            continue
        target = destination.joinpath(*relative.parts)
        resolved_parent = target.parent.resolve()
        if root != resolved_parent and root not in resolved_parent.parents:
            raise ArchiveValidationError("ZIP이 임시 폴더 밖에 파일을 만들려고 했습니다.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info, "r") as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
        extracted[info.filename] = target
    return extracted
