from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.gui.localization_changes_dialog import LocalizationChangesDialog
from app.gui.project_wizard import ProjectWizard
from app.gui.widgets.page_header import PageHeader
from app.i18n import t


class ProjectsPage(QScrollArea):
    package_requested = Signal(dict); apply_requested = Signal(dict); ai_translation_requested = Signal(dict); ai_update_requested = Signal(dict)
    def __init__(self, manager, activities, config=None) -> None:
        super().__init__(); self.manager = manager; self.activities = activities; self.config = config or manager.config; self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(28, 22, 28, 22); root.setSpacing(14); root.addWidget(PageHeader(t("projects.title"), t("projects.description")))
        create = QPushButton(t("projects.new"), objectName="burgundyButton"); create.clicked.connect(self._edit); root.addWidget(create)
        self.list_layout = QVBoxLayout(); self.list_layout.setSpacing(12); root.addLayout(self.list_layout); root.addStretch(); self.setWidget(content); manager.changed.connect(self.refresh); self.refresh()

    def refresh(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self.manager.projects: self.list_layout.addWidget(QLabel(t("projects.empty"), objectName="mutedText")); return
        for project in self.manager.projects:
            card = QFrame(objectName="panel"); layout = QVBoxLayout(card); title = QHBoxLayout(); title.addWidget(QLabel(str(project.get("name", "")), objectName="panelTitle")); title.addStretch(); title.addWidget(QLabel(str(project.get("target_language", "")), objectName="mutedText")); layout.addLayout(title)
            path = QLabel(str(project.get("localization_path") or project.get("source_path", "")), objectName="mutedText"); path.setWordWrap(True); layout.addWidget(path)
            primary = QHBoxLayout()
            for label, slot, style in ((t("projects.full_package"), lambda checked=False, p=project: self.package_requested.emit(p), ""), (t("diff.check_changes"), lambda checked=False, p=project: self._changes(p), "burgundyButton"), (t("home.apply_title"), lambda checked=False, p=project: self.apply_requested.emit(p), "")):
                button = QPushButton(label, objectName=style); button.clicked.connect(slot); primary.addWidget(button)
            layout.addLayout(primary)
            api_row = QHBoxLayout()
            for label, slot in ((t("ai.translation.title"), lambda checked=False, p=project: self.ai_translation_requested.emit(p)), (t("ai.update.title"), lambda checked=False, p=project: self.ai_update_requested.emit(p))):
                button=QPushButton(label,objectName="secondaryButton"); button.clicked.connect(slot); api_row.addWidget(button)
            layout.addLayout(api_row)
            secondary = QHBoxLayout(); secondary.addStretch()
            for label, slot in ((t("projects.edit"), lambda checked=False, p=project: self._edit(p)), (t("projects.delete"), lambda checked=False, p=project: self._remove(p))):
                button = QPushButton(label, objectName="secondaryButton"); button.clicked.connect(slot); secondary.addWidget(button)
            layout.addLayout(secondary); self.list_layout.addWidget(card)

    def _edit(self, project=None) -> None:
        wizard = ProjectWizard(self.config, project, self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            saved = self.manager.save_project(wizard.data()); self.activities.add("PROJECT_CREATED" if not project else "PROJECT_UPDATED", saved["name"], saved["id"])
    def _changes(self, project): LocalizationChangesDialog(self.config, project, self.activities, self).exec()
    def _remove(self, project) -> None:
        if QMessageBox.question(self, t("projects.delete"), t("projects.delete_confirm")) == QMessageBox.StandardButton.Yes: self.manager.remove(project["id"])
