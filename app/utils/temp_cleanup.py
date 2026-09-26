import logging
import shutil
import time

from app.utils.paths import app_temp_root


def cleanup_stale_temp(max_age_days: int = 7) -> None:
    cutoff = time.time() - max_age_days * 86_400
    root = app_temp_root()
    for child in root.iterdir():
        try:
            if child.is_dir() and child.name.startswith("job_") and child.stat().st_mtime < cutoff:
                shutil.rmtree(child)
        except OSError:
            logging.getLogger("v3mm").warning("Could not remove stale temp directory")
