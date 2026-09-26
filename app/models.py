from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath


class OverwritePolicy(str, Enum):
    BACKUP_AND_OVERWRITE = "backup_and_overwrite"
    OVERWRITE = "overwrite"
    SKIP = "skip"
    CANCEL = "cancel"


@dataclass(frozen=True)
class PackageFile:
    source: Path
    archive_path: PurePosixPath
    content: bytes | None = None
    declaration_status: str = "unchanged"
    warning: str = ""
    source_language: str = "unknown"
    target_language: str = "korean"
    filename_changed: bool = False
    header_changed: bool = False
    reason: str = ""


@dataclass(frozen=True)
class PackageReport:
    files: list[PackageFile]
    total_size: int
    renamed_count: int
    declaration_changed_count: int
    target_language: str = "korean"
    manifest_id: str = ""

    @property
    def warnings(self) -> list[PackageFile]:
        return [item for item in self.files if item.warning]


@dataclass(frozen=True)
class ImportFile:
    archive_name: str
    install_relative_path: Path
    size: int


@dataclass
class InstallResult:
    installed: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    backed_up: list[Path] = field(default_factory=list)
