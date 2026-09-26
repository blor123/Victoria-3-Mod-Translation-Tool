from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app import APP_NAME, APP_VERSION
from app.constants import STEAM_PROFILE_URL
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.utils.paths import resource_path


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("pageSurface")
        root = QVBoxLayout(self); root.setContentsMargins(28, 22, 28, 22); root.addWidget(PageHeader(t("about.title")))
        panel = QFrame(objectName="panel"); layout = QVBoxLayout(panel); layout.setContentsMargins(30, 24, 30, 24); layout.setSpacing(8)
        icon = QLabel(); icon.setPixmap(QPixmap(str(resource_path("resources/icons/app.png"))).scaled(116, 116, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(APP_NAME, objectName="pageTitle"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version = QLabel(f"V3MM  ·  Version {APP_VERSION}", objectName="versionLabel"); version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creator = QLabel(t("about.creator")); creator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        steam = QLabel(f'<a href="{STEAM_PROFILE_URL}">{STEAM_PROFILE_URL}</a>'); steam.setOpenExternalLinks(True); steam.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction); steam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description = QLabel(t("about.description"), objectName="mutedText"); description.setWordWrap(True); description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for widget in (icon, title, version, creator, steam, description): layout.addWidget(widget)
        root.addWidget(panel); root.addStretch()
