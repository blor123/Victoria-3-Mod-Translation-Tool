from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app import APP_VERSION
from app.i18n import t


class AppStatusBar(QFrame):
    update_clicked = Signal()
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statusBar")
        self.setFixedHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 8, 22, 8)
        self.status_label = QLabel(f"✓ {t('common.ready')}")
        self.status_label.setObjectName("statusReady")
        self.update_button = QPushButton(objectName="linkButton")
        self.update_button.hide(); self.update_button.clicked.connect(self.update_clicked)
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("versionLabel")
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.update_button)
        layout.addWidget(version)

    def set_update(self, version: str | None) -> None:
        self.update_button.setText(t("update.available", version=version))
        self.update_button.setVisible(bool(version))

    def set_status(self, message: str, kind: str = "ready") -> None:
        symbols = {"ready": "✓", "busy": "●", "error": "⚠"}
        names = {"ready": "statusReady", "busy": "statusBusy", "error": "statusError"}
        self.status_label.setText(f"{symbols.get(kind, '●')} {message}")
        self.status_label.setObjectName(names.get(kind, "statusReady"))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
