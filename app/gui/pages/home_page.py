from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.gui.widgets.feature_card import FeatureCard
from app.gui.widgets.page_header import PageHeader
from app.i18n import t


class HomePage(QScrollArea):
    quick_requested = Signal(); package_requested = Signal(); apply_requested = Signal()
    def __init__(self, activity_manager) -> None:
        super().__init__(); self.activity_manager = activity_manager; self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame); self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(objectName="pageSurface"); self.root = QVBoxLayout(content); self.root.setContentsMargins(22, 18, 22, 18); self.root.setSpacing(16)
        self.root.addWidget(PageHeader(t("home.title"), t("home.description")))
        quick = FeatureCard("1 · 2 · 3", t("home.quick_title"), t("home.quick_desc"), t("home.start"), "burgundyButton", 185)
        package = FeatureCard("A  →  가", t("home.package_title"), t("home.package_desc"), t("home.start"), "secondaryButton")
        apply = FeatureCard("ZIP  →  ▰", t("home.apply_title"), t("home.apply_desc"), t("home.start"), "blueButton")
        quick.activated.connect(self.quick_requested); package.activated.connect(self.package_requested); apply.activated.connect(self.apply_requested)
        self.root.addWidget(quick); cards = QHBoxLayout(); cards.setSpacing(16); cards.addWidget(package, 1); cards.addWidget(apply, 1); self.root.addLayout(cards)
        self.panel = QFrame(objectName="panel"); self.activity_layout = QVBoxLayout(self.panel); self.activity_layout.setContentsMargins(18, 14, 18, 14)
        header = QHBoxLayout(); header.addWidget(QLabel(t("home.recent"), objectName="panelTitle")); header.addStretch(); clear = QPushButton(t("activity.clear_all"), objectName="linkButton"); clear.clicked.connect(activity_manager.clear); header.addWidget(clear); self.activity_layout.addLayout(header)
        self.root.addWidget(self.panel); self.root.addStretch(); self.setWidget(content); activity_manager.changed.connect(self.refresh_activities); self.refresh_activities()

    def refresh_activities(self) -> None:
        while self.activity_layout.count() > 1:
            item = self.activity_layout.takeAt(1)
            if item.widget(): item.widget().deleteLater()
        records = [r for r in self.activity_manager.records if r.get("type") != "UPDATE_AVAILABLE"][:5]
        if not records: self.activity_layout.addWidget(QLabel(t("home.empty"), objectName="mutedText")); return
        for record in records:
            row = QFrame(objectName="activityRow"); layout = QHBoxLayout(row); layout.setContentsMargins(4, 8, 4, 8)
            layout.addWidget(QLabel(str(record.get("message", ""))), 1); layout.addWidget(QLabel(str(record.get("timestamp", "")).replace("T", " "), objectName="mutedText"))
            layout.addWidget(QLabel(t(f"activity.{str(record.get('type', 'INFO')).lower()}"), objectName="activityStatus"))
            remove = QPushButton(t("activity.remove"), objectName="linkButton"); remove.clicked.connect(lambda checked=False, rid=record.get("id"): self.activity_manager.remove(rid)); layout.addWidget(remove); self.activity_layout.addWidget(row)
