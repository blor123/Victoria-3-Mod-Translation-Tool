"""Render public, privacy-safe screenshots with the packaged UI code."""

import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.gui.theme import apply_theme


def main() -> int:
    output = Path(__file__).resolve().parents[1] / "docs" / "images"
    output.mkdir(parents=True, exist_ok=True)
    application = QApplication.instance() or QApplication([])
    apply_theme(application)
    with tempfile.TemporaryDirectory() as temp:
        config = ConfigManager(Path(temp) / "config.json")
        config.update(language="ko-KR", check_updates_on_startup=False)
        window = MainWindow(config)
        window.resize(1180, 760)
        window.show()
        application.processEvents()
        if not window.grab().save(str(output / "v2.1.2-home.png"), "PNG"):
            return 1
        window.navigate(4)
        application.processEvents()
        if not window.grab().save(str(output / "v2.1.2-translation-update.png"), "PNG"):
            return 1
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
