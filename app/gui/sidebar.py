from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.i18n import t
from app.utils.paths import resource_path


class Sidebar(QFrame):
    page_selected = Signal(int)

    def __init__(self) -> None:
        super().__init__(); self.setObjectName("sidebar"); self.setFixedWidth(238); self.buttons: list[QPushButton] = []; self.group = QButtonGroup(self); self.group.setExclusive(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 6, 0, 6)
        scroll = QScrollArea(); scroll.setObjectName("sidebarScroll"); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); outer.addWidget(scroll)
        content = QWidget(); self.layout = QVBoxLayout(content); self.layout.setContentsMargins(0, 4, 0, 4); self.layout.setSpacing(1); scroll.setWidget(content)
        self._add_page(0, "sidebar.home", "home.svg")
        self._add_page(1, "sidebar.quick", "package.svg")
        self._add_page(4, "sidebar.translation_update", "apply.svg")
        line = QFrame(objectName="sidebarSeparator"); line.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(line)
        self.parent_button = QPushButton(t("sidebar.translation")); self.parent_button.setObjectName("navParent"); self.parent_button.setCheckable(True); self.parent_button.setChecked(True); self.parent_button.setIconSize(QSize(16, 16)); self.parent_button.clicked.connect(self.set_translation_expanded); self.layout.addWidget(self.parent_button)
        self.children = QFrame(); children_layout = QVBoxLayout(self.children); children_layout.setContentsMargins(12, 0, 0, 0); children_layout.setSpacing(1)
        self._add_page(2, "sidebar.package", "package.svg", children_layout, "navChild")
        self._add_page(3, "sidebar.apply", "apply.svg", children_layout, "navChild")
        self.layout.addWidget(self.children)
        line = QFrame(objectName="sidebarSeparator"); line.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(line)
        self.api_parent = QPushButton(t("sidebar.api")); self.api_parent.setObjectName("navParent"); self.api_parent.setCheckable(True); self.api_parent.setChecked(True); self.api_parent.setIconSize(QSize(16, 16)); self.api_parent.clicked.connect(self.set_api_expanded); self.layout.addWidget(self.api_parent)
        self.api_children = QFrame(); api_layout = QVBoxLayout(self.api_children); api_layout.setContentsMargins(12, 0, 0, 0); api_layout.setSpacing(1)
        self._add_page(5, "sidebar.ai_translation", "package.svg", api_layout, "navChild")
        self._add_page(6, "sidebar.ai_update", "apply.svg", api_layout, "navChild")
        self._add_page(7, "sidebar.ai_settings", "settings.svg", api_layout, "navChild")
        self.layout.addWidget(self.api_children)
        line = QFrame(objectName="sidebarSeparator"); line.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(line)
        self._add_page(8, "sidebar.projects", "project.svg")
        self._add_page(9, "sidebar.conflicts", "tools.svg")
        line = QFrame(objectName="sidebarSeparator"); line.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(line)
        self._add_page(10, "sidebar.tools", "tools.svg")
        self.layout.addWidget(QLabel(t("sidebar.program"), objectName="sidebarSection"))
        self._add_page(11, "sidebar.settings", "settings.svg")
        self._add_page(12, "sidebar.about", "info.svg")
        self.layout.addStretch(); self.buttons[0].setChecked(True); self.set_translation_expanded(True); self.set_api_expanded(True)

    def _add_page(self, index, label_key, icon_name, layout=None, object_name="navButton"):
        button = QPushButton(t(label_key)); button.setObjectName(object_name); button.setCheckable(True); button.setIcon(QIcon(str(resource_path(f"resources/icons/{icon_name}")))); button.setIconSize(QSize(20, 20)); button.clicked.connect(lambda checked=False, page=index: self.select(page)); self.group.addButton(button, index)
        while len(self.buttons) <= index: self.buttons.append(None)
        self.buttons[index] = button; (layout or self.layout).addWidget(button)

    def set_translation_expanded(self, expanded: bool) -> None:
        self.children.setVisible(expanded)
        icon = "triangle_expanded.svg" if expanded else "triangle_collapsed.svg"
        self.parent_button.setIcon(QIcon(str(resource_path(f"resources/icons/{icon}"))))

    def set_api_expanded(self, expanded: bool) -> None:
        self.api_children.setVisible(expanded)
        icon = "triangle_expanded.svg" if expanded else "triangle_collapsed.svg"
        self.api_parent.setIcon(QIcon(str(resource_path(f"resources/icons/{icon}"))))

    def select(self, index: int) -> None:
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            if index in (2, 3):
                if not self.children.isVisible(): self.parent_button.setChecked(True); self.set_translation_expanded(True)
                self.parent_button.setProperty("active", True)
            else: self.parent_button.setProperty("active", False)
            if index in (5, 6, 7):
                if not self.api_children.isVisible(): self.api_parent.setChecked(True); self.set_api_expanded(True)
                self.api_parent.setProperty("active", True)
            else: self.api_parent.setProperty("active", False)
            self.parent_button.style().unpolish(self.parent_button); self.parent_button.style().polish(self.parent_button); self.api_parent.style().unpolish(self.api_parent); self.api_parent.style().polish(self.api_parent); self.page_selected.emit(index)
