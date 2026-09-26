import os
import sys
from pathlib import Path

from app import APP_NAME


def resource_path(relative: str | Path) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / APP_NAME.replace(" ", "")
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_temp_root() -> Path:
    import tempfile

    path = Path(tempfile.gettempdir()) / APP_NAME.replace(" ", "")
    path.mkdir(parents=True, exist_ok=True)
    return path
