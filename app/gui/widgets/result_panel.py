from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
from app.i18n import t


class ResultPanel(QFrame):
    dismissed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("resultPanel")
        self._folder: Path | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        self.title = QLabel()
        self.details = QLabel()
        self.details.setObjectName("mutedText")
        self.details.setWordWrap(True)
        self.open_button = QPushButton(t("common.open_folder"))
        self.open_button.setObjectName("secondaryButton")
        self.open_button.clicked.connect(self._open_folder)
        layout.addWidget(self.title)
        layout.addWidget(self.details)
        layout.addWidget(self.open_button, 0)
        self.hide()

    def show_success(self, title: str, details: str, folder: Path | None = None) -> None:
        self.title.setObjectName("successTitle")
        self.title.style().unpolish(self.title)
        self.title.style().polish(self.title)
        self.title.setText(f"✓ {title}")
        self.details.setText(details)
        self._folder = folder
        self.open_button.setVisible(folder is not None)
        self.show()

    def show_error(self, title: str, details: str) -> None:
        self.title.setObjectName("errorTitle")
        self.title.style().unpolish(self.title)
        self.title.style().polish(self.title)
        self.title.setText(f"⚠ {title}")
        self.details.setText(details)
        self._folder = None
        self.open_button.hide()
        self.show()

    def _open_folder(self) -> None:
        if self._folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._folder)))
