from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QWidget

from app.gui.widgets.page_header import PageHeader
from app.i18n import t


class ToolsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("pageSurface")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(18)
        root.addWidget(PageHeader(t("tools.title"), t("tools.description")))
        cards = QHBoxLayout()
        cards.setSpacing(16)
        for title, version, description in (
            (t("tools.order"), t("tools.order_version"), t("tools.order_desc")),
        ):
            panel = QFrame()
            panel.setObjectName("panel")
            layout = QVBoxLayout(panel)
            layout.setContentsMargins(24, 24, 24, 24)
            heading = QLabel(title)
            heading.setObjectName("panelTitle")
            version_label = QLabel(version)
            version_label.setObjectName("versionLabel")
            body = QLabel(description)
            body.setObjectName("mutedText")
            body.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(version_label)
            layout.addSpacing(8)
            layout.addWidget(body)
            layout.addStretch()
            cards.addWidget(panel)
        root.addLayout(cards)
        root.addStretch()
