import os
import tempfile
import zipfile
from pathlib import Path

from app.models import PackageFile


def create_zip(files: list[PackageFile], destination: Path) -> None:
    """Create an archive atomically so a failed operation leaves no partial ZIP."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix="v3mm_", suffix=".zip.tmp", dir=destination.parent
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                if item.content is None:
                    archive.write(item.source, item.archive_path.as_posix())
                else:
                    archive.writestr(item.archive_path.as_posix(), item.content)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)
