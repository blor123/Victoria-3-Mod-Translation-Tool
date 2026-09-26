from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.utils.paths import resource_path


def apply_theme(application: QApplication) -> None:
    font = QFont("Malgun Gothic")
    font.setFamilies(["Malgun Gothic", "Segoe UI", "Arial"])
    font.setPointSize(10)
    application.setFont(font)
    stylesheet = resource_path("resources/styles/dark_victorian.qss")
    application.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
