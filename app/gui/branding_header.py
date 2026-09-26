from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from app.utils.paths import resource_path


class BrandingHeader(QFrame):
    notifications_requested = Signal()
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("topBanner")
        self.setFixedHeight(116)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(35, 16, 35, 16)
        layout.addStretch()
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        mark = QLabel("V3MM")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("VICTORIA 3 MOD MANAGER")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("TRANSLATION  ·  PROJECTS  ·  TOOLS")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.addWidget(mark)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        layout.addLayout(text_layout)
        layout.addStretch()
        self.notification_button = QPushButton()
        self.notification_button.setObjectName("notificationButton")
        self.notification_button.setFixedSize(64, 40)
        self.notification_button.setIcon(QIcon(str(resource_path("resources/icons/notification.svg")))); self.notification_button.setIconSize(QSize(22, 22))
        self.notification_button.clicked.connect(self.notifications_requested)
        layout.addWidget(self.notification_button, 0, Qt.AlignmentFlag.AlignTop)

    def set_badge(self, count: int) -> None:
        self.notification_button.setText(str(count) if count else "")
