from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class FeatureCard(QFrame):
    activated = Signal()

    def __init__(
        self, icon_text: str, title: str, description: str, button_text: str, accent: str,
        minimum_height: int = 240,
    ) -> None:
        super().__init__()
        self.setObjectName("featureCard")
        self.setMinimumWidth(0)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(minimum_height)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 22)
        layout.setSpacing(14)

        icon = QLabel(icon_text)
        icon.setObjectName("cardIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label = QLabel(title)
        title_label.setMinimumWidth(0)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label = QLabel(description)
        description_label.setMinimumWidth(0)
        description_label.setObjectName("cardDescription")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName(accent)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.clicked.connect(self.activated)
        layout.addWidget(icon)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
        layout.addWidget(button)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit()
        super().mouseReleaseEvent(event)
