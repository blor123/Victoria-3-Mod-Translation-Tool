import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.gui.main_window import MainWindow
from app.gui.theme import apply_theme
from app.utils.logging import configure_logging
from app.utils.paths import resource_path
from app.utils.temp_cleanup import cleanup_stale_temp
from app.i18n import set_language


def main() -> int:
    configure_logging()
    cleanup_stale_temp()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    application = QApplication(sys.argv)
    application.setApplicationName("Victoria 3 Mod Manager")
    application.setOrganizationName("V3MM")
    application.setWindowIcon(QIcon(str(resource_path("resources/icons/app.ico"))))
    apply_theme(application)
    config = ConfigManager()
    set_language(str(config.data.get("language", "ko-KR")))
    window = MainWindow(config)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
