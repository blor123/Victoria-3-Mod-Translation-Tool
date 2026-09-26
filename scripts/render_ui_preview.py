"""Render a deterministic UI screenshot for visual QA without touching user settings."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.gui.theme import apply_theme
from app.i18n import SUPPORTED_LANGUAGES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--page", type=int, default=0, choices=range(13))
    parser.add_argument("--language", default="ko-KR", choices=SUPPORTED_LANGUAGES)
    parser.add_argument("--width", type=int, default=1180)
    parser.add_argument("--height", type=int, default=760)
    parser.add_argument("--wizard", action="store_true")
    args = parser.parse_args()
    application = QApplication([])
    apply_theme(application)
    with tempfile.TemporaryDirectory() as temp:
        config = ConfigManager(Path(temp) / "config.json")
        config.update(language=args.language)
        for name, action, status in reversed(
            [
                ("Economic and Financial Mod", "apply", "applied"),
                ("More Buildings+", "package", "package_ready"),
                ("Historical Flavor Expanded", "apply", "applied"),
            ]
        ):
            config.add_recent_activity(name, action, status)
        if args.wizard:
            from app.gui.project_wizard import ProjectWizard
            window = ProjectWizard(config)
        else:
            window = MainWindow(config)
            window.navigate(args.page)
        window.resize(args.width, args.height)
        window.show()
        application.processEvents()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(args.output))
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
