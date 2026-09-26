from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWizard, QWizardPage

from app.i18n import t
from app.i18n.language_definition import target_language
from app.projects import detect_project_paths


class ProjectWizard(QWizard):
    def __init__(self, config, project=None, parent=None) -> None:
        super().__init__(parent); self.config = config; self.project = dict(project or {}); self.target = target_language(str(config.data.get("language", "ko-KR")))
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
        self.setWindowTitle(t("wizard.edit_title") if project else t("wizard.title")); self.resize(780, 590); self.setMinimumSize(680, 520)
        self.setButtonText(QWizard.WizardButton.NextButton, t("wizard.next")); self.setButtonText(QWizard.WizardButton.BackButton, t("wizard.back")); self.setButtonText(QWizard.WizardButton.FinishButton, t("wizard.create")); self.setButtonText(QWizard.WizardButton.CancelButton, t("common.cancel"))
        self.name_edit = QLineEdit(str(self.project.get("name", ""))); self.root_edit = QLineEdit(str(self.project.get("source_path", ""))); self.localization_edit = QLineEdit(str(self.project.get("localization_path", ""))); self.install_edit = QLineEdit(str(self.project.get("install_path", ""))); self.status = QLabel(); self.status.setWordWrap(True); self.review = QLabel(); self.review.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); self.review.setWordWrap(True)
        self.addPage(self._name_page()); self.addPage(self._root_page()); self.addPage(self._paths_page()); self.addPage(self._review_page()); self.currentIdChanged.connect(self._page_changed)
        if self.root_edit.text(): self._detect()

    def _page(self, title, description):
        page = QWizardPage(); page.setTitle(title); page.setSubTitle(description); page.setLayout(QVBoxLayout()); return page
    def _name_page(self):
        page = self._page(t("wizard.name_step"), t("wizard.name_help")); form = QFormLayout(); form.addRow(t("wizard.name_required"), self.name_edit); page.layout().addLayout(form); page.registerField("projectName*", self.name_edit); page.layout().addStretch(); return page
    def _path_row(self, edit, browse_slot):
        row = QHBoxLayout(); row.addWidget(edit, 1); browse = QPushButton(t("common.browse")); browse.clicked.connect(browse_slot); clear = QPushButton(t("common.reset"), objectName="secondaryButton"); clear.clicked.connect(edit.clear); clear.setToolTip(t("common.reset_path_tooltip")); row.addWidget(browse); row.addWidget(clear); return row
    def _root_page(self):
        page = self._page(t("wizard.mod_step"), t("wizard.mod_help")); page.layout().addWidget(QLabel(t("wizard.mod_required"))); page.layout().addLayout(self._path_row(self.root_edit, self._browse_root)); page.layout().addWidget(self.status); page.registerField("modRoot*", self.root_edit); page.layout().addStretch(); return page
    def _paths_page(self):
        page = self._page(t("wizard.paths_step"), t("wizard.paths_help")); page.layout().addWidget(QLabel(t("projects.localization"))); page.layout().addLayout(self._path_row(self.localization_edit, lambda: self._browse(self.localization_edit))); page.layout().addWidget(QLabel(t("wizard.localization_help"), objectName="mutedText")); page.layout().addWidget(QLabel(t("projects.install"))); page.layout().addLayout(self._path_row(self.install_edit, lambda: self._browse(self.install_edit))); page.layout().addWidget(QLabel(t("wizard.install_help"), objectName="mutedText")); redetect = QPushButton(t("wizard.redetect"), objectName="secondaryButton"); redetect.clicked.connect(self._detect); page.layout().addWidget(redetect); page.layout().addStretch(); return page
    def _review_page(self):
        page = self._page(t("wizard.review_step"), t("wizard.review_help")); page.layout().addWidget(self.review); page.layout().addStretch(); return page
    def _browse_root(self):
        folder = QFileDialog.getExistingDirectory(self, t("wizard.mod_step"), self.root_edit.text())
        if folder: self.root_edit.setText(folder); self._detect()
    def _browse(self, edit):
        folder = QFileDialog.getExistingDirectory(self, t("common.browse"), edit.text() or self.root_edit.text())
        if folder: edit.setText(folder)
    def _detect(self):
        root = Path(self.root_edit.text().strip())
        if not root.is_dir(): self.status.setText(t("wizard.invalid_mod")); return
        result = detect_project_paths(root, self.target)
        if result.localization_path:
            self.localization_edit.setText(str(result.localization_path)); self.install_edit.setText(str(result.install_root)); self.status.setText(t("wizard.found", count=result.yml_count, path=result.localization_path))
        else: self.status.setText(t("wizard.not_found"))
    def _page_changed(self, page_id):
        if page_id == 3:
            target_path = Path(self.install_edit.text()) / "localization" / self.target.filename_suffix
            self.review.setText(t("wizard.review", name=self.name_edit.text(), mod=self.root_edit.text(), localization=self.localization_edit.text(), install=target_path, language=f"{self.target.display_name} ({self.target.filename_suffix})"))
    def accept(self):
        if not Path(self.root_edit.text()).is_dir() or not Path(self.localization_edit.text()).is_dir(): self.status.setText(t("wizard.not_found")); self.restart(); return
        super().accept()
    def data(self) -> dict:
        value = dict(self.project); value.update(name=self.name_edit.text().strip(), source_path=self.root_edit.text().strip(), localization_path=self.localization_edit.text().strip(), install_path=self.install_edit.text().strip(), target_language=self.target.filename_suffix); return value
