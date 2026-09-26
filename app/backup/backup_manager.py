import shutil
from datetime import datetime
from pathlib import Path


def create_backup_root(install_root: Path) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    root = install_root / "backups" / stamp
    root.mkdir(parents=True, exist_ok=False)
    return root


def backup_file(source: Path, relative: Path, backup_root: Path) -> Path:
    destination = backup_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination
