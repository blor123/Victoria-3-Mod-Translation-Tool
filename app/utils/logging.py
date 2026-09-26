import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import user_data_dir


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("v3mm")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = user_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "v3mm.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    return logger
