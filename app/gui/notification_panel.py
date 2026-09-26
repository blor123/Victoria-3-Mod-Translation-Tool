from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.i18n import t


class NotificationPanel(QFrame):
    def __init__(self, manager, parent=None) -> None:
        super().__init__(parent); self.manager = manager; self.setObjectName("notificationPanel"); self.setFixedWidth(360); self.setMinimumHeight(130); self.setMaximumHeight(460)
        root = QVBoxLayout(self); header = QHBoxLayout(); header.addWidget(QLabel(t("notification.title"), objectName="panelTitle")); header.addStretch()
        clear = QPushButton(t("activity.clear_all"), objectName="linkButton"); clear.clicked.connect(manager.clear); header.addWidget(clear); root.addLayout(header)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(); self.items = QVBoxLayout(content); self.items.setAlignment(Qt.AlignmentFlag.AlignTop); scroll.setWidget(content); root.addWidget(scroll)
        manager.changed.connect(self.refresh); self.refresh(); self.hide()

    def refresh(self) -> None:
        while self.items.count():
            item = self.items.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        records = self.manager.records
        if not records:
            self.items.addWidget(QLabel(t("notification.empty"), objectName="mutedText")); self.resize(360, 140); return
        for record in records:
            row = QFrame(objectName="notificationItem"); layout = QVBoxLayout(row); top = QHBoxLayout()
            title = QLabel(t(f"activity.{str(record.get('type', 'INFO')).lower()}")); title.setObjectName("panelTitle"); top.addWidget(title); top.addStretch()
            remove = QPushButton(t("activity.remove"), objectName="linkButton"); remove.clicked.connect(lambda checked=False, rid=record.get("id"): self.manager.remove(rid)); top.addWidget(remove)
            layout.addLayout(top); layout.addWidget(QLabel(str(record.get("message", ""))))
            stamp = QLabel(str(record.get("timestamp", "")).replace("T", " "), objectName="mutedText"); layout.addWidget(stamp); self.items.addWidget(row)
        self.resize(360, min(460, max(160, 74 + len(records) * 88)))

    def show_panel(self) -> None:
        self.refresh(); self.show(); self.raise_(); self.manager.mark_all_read()
