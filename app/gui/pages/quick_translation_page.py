from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from app.config.config_manager import ConfigManager
from app.gui.dialogs import confirm_install, show_operation_error
from app.gui.widgets.drop_area import DropArea
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.i18n.language_definition import LANGUAGES, target_language
from app.translation.package_builder import build_translation_package_report
from app.translation.package_importer import inspect_translation_zip, install_translation_zip
from app.translation.prompt_manager import active_prompt


class QuickTranslationPage(QScrollArea):
    status_changed = Signal(str, str); activity_completed = Signal(str, str, str)

    def __init__(self, config: ConfigManager) -> None:
        super().__init__(); self.config = config; self.sources: list[Path] = []
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(24, 18, 24, 18); root.setSpacing(12)
        root.addWidget(PageHeader(t("quick.title"), t("quick.description")))
        root.addWidget(self._package_panel()); root.addWidget(self._prompt_panel()); root.addWidget(self._apply_panel()); root.addStretch(); self.setWidget(content)

    def _package_panel(self):
        panel = QFrame(objectName="formPanel"); form = QGridLayout(panel); form.setContentsMargins(18, 15, 18, 15)
        form.addWidget(QLabel(t("quick.step1"), objectName="panelTitle"), 0, 0, 1, 4)
        self.drop = DropArea(); self.drop.paths_dropped.connect(self.add_sources); form.addWidget(self.drop, 1, 0, 1, 4)
        self.source_edit = QLineEdit(); self.source_edit.setReadOnly(True); form.addWidget(self.source_edit, 2, 0, 1, 2)
        files = QPushButton(t("package.files")); files.clicked.connect(self._files); folder = QPushButton(t("package.folder")); folder.clicked.connect(self._folder); form.addWidget(files, 2, 2); form.addWidget(folder, 2, 3)
        lang = target_language(str(self.config.data.get("language", "ko-KR"))); self.target_label = QLabel(t("quick.target", language=lang.display_name), objectName="mutedText"); form.addWidget(self.target_label, 3, 0, 1, 4)
        self.export_edit = QLineEdit(str(self.config.data.get("last_quick_export_path", ""))); self.export_edit.setPlaceholderText("V3MM_Translation_Package.zip"); browse = QPushButton(t("common.browse")); browse.clicked.connect(self._export); build = QPushButton(t("package.create"), objectName="burgundyButton"); build.clicked.connect(self._build)
        form.addWidget(self.export_edit, 4, 0, 1, 2); form.addWidget(browse, 4, 2); form.addWidget(build, 4, 3); return panel

    def _prompt_panel(self):
        panel = QFrame(objectName="formPanel"); layout = QVBoxLayout(panel); layout.setContentsMargins(18, 15, 18, 15); layout.addWidget(QLabel(t("quick.step2"), objectName="panelTitle"))
        row = QHBoxLayout(); self.prompt_group = QButtonGroup(self); self.prompt_group.setExclusive(True)
        selected = str(self.config.data.get("prompt_language") or self.config.data.get("language", "ko-KR"))
        for code, definition in LANGUAGES.items():
            button = QPushButton(definition.display_name, objectName="languageChip"); button.setCheckable(True); button.setChecked(code == selected); button.clicked.connect(lambda checked=False, value=code: self._select_prompt_language(value)); self.prompt_group.addButton(button); row.addWidget(button)
        row.addStretch(); show = QPushButton(t("package.edit_prompt"), objectName="secondaryButton"); show.clicked.connect(self._show_prompt); copy = QPushButton(t("package.copy_prompt"), objectName="secondaryButton"); copy.clicked.connect(self._copy_prompt); row.addWidget(show); row.addWidget(copy); layout.addLayout(row); return panel

    def _apply_panel(self):
        panel = QFrame(objectName="formPanel"); form = QGridLayout(panel); form.setContentsMargins(18, 15, 18, 15); form.addWidget(QLabel(t("quick.step3"), objectName="panelTitle"), 0, 0, 1, 4)
        self.translation_zip = QLineEdit(); self.translation_zip.setPlaceholderText(t("apply.zip")); z = QPushButton(t("common.browse")); z.clicked.connect(self._translation_zip)
        self.install_edit = QLineEdit(str(self.config.data.get("last_install_path", ""))); self.install_edit.setPlaceholderText(t("apply.install")); d = QPushButton(t("common.browse")); d.clicked.connect(self._install_folder); apply = QPushButton(t("apply.button"), objectName="blueButton"); apply.clicked.connect(self._apply)
        form.addWidget(self.translation_zip, 1, 0, 1, 3); form.addWidget(z, 1, 3); form.addWidget(self.install_edit, 2, 0, 1, 3); form.addWidget(d, 2, 3); form.addWidget(apply, 3, 3); return panel

    def add_sources(self, paths):
        self.sources = [Path(path).resolve() for path in paths if Path(path).exists()]; self.source_edit.setText(" | ".join(map(str, self.sources)))
    def _files(self):
        values, _ = QFileDialog.getOpenFileNames(self, t("package.files"), "", "YML (*.yml)");
        if values: self.add_sources(values)
    def _folder(self):
        value = QFileDialog.getExistingDirectory(self, t("package.folder"));
        if value: self.add_sources([value])
    def _export(self):
        value, _ = QFileDialog.getSaveFileName(self, t("package.export"), self.export_edit.text() or "V3MM_Translation_Package.zip", "ZIP (*.zip)");
        if value: self.export_edit.setText(value if value.lower().endswith(".zip") else value + ".zip")
    def _translation_zip(self):
        value, _ = QFileDialog.getOpenFileName(self, t("apply.zip"), "", "ZIP (*.zip)");
        if value: self.translation_zip.setText(value)
    def _install_folder(self):
        value = QFileDialog.getExistingDirectory(self, t("apply.install"));
        if value: self.install_edit.setText(value)
    def _select_prompt_language(self, code): self.config.update(prompt_language=code)
    def _show_prompt(self):
        from app.gui.prompt_dialog import PromptDialog
        PromptDialog(self.config, self, str(self.config.data.get("prompt_language", "ko-KR"))).exec()
    def _copy_prompt(self):
        QApplication.clipboard().setText(active_prompt(self.config, target_language(str(self.config.data.get("language", "ko-KR"))), str(self.config.data.get("prompt_language", "ko-KR")))); self.status_changed.emit(t("common.copied"), "ready")
    def _build(self):
        if not self.sources or not self.export_edit.text().strip(): QMessageBox.warning(self, t("common.input"), t("package.input_required")); return
        try:
            destination = Path(self.export_edit.text().strip()); report = build_translation_package_report(self.sources, destination, target_language(str(self.config.data.get("language", "ko-KR"))), int(self.config.data.get("prompt_version", 4)))
            self.config.update(last_quick_export_path=str(destination)); self.status_changed.emit(t("package.complete"), "ready"); self.activity_completed.emit(self.sources[0].stem, "package", "package_ready"); QMessageBox.information(self, t("package.complete"), t("package.total", count=len(report.files)))
        except Exception as error: show_operation_error(self, t("package.error"), error)
    def _apply(self):
        if not self.translation_zip.text().strip() or not self.install_edit.text().strip(): QMessageBox.warning(self, t("common.input"), t("apply.input_required")); return
        try:
            language = target_language(str(self.config.data.get("language", "ko-KR"))); archive = Path(self.translation_zip.text()); root = Path(self.install_edit.text()); files = inspect_translation_zip(archive, language.filename_suffix); policy = confirm_install(self, files, root, bool(self.config.data.get("create_backup", True)))
            if policy is None: return
            result = install_translation_zip(archive, root, policy, language.filename_suffix); self.config.update(last_install_path=str(root), last_import_zip_path=str(archive)); self.status_changed.emit(t("apply.complete"), "ready"); self.activity_completed.emit(root.name, "apply", "applied"); QMessageBox.information(self, t("apply.complete"), t("apply.summary", installed=len(result.installed), skipped=len(result.skipped), backed_up=len(result.backed_up)))
        except Exception as error: show_operation_error(self, t("apply.error"), error)
