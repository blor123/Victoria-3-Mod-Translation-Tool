import hashlib
import tempfile
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QGridLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget)

from app.config.config_manager import ConfigManager
from app.gui.dialogs import confirm_install, show_operation_error
from app.gui.widgets.page_header import PageHeader
from app.gui.validation_dialog import ValidationDialog
from app.i18n import t
from app.i18n.language_definition import target_language
from app.models import OverwritePolicy
from app.snapshots import SnapshotManager, capture_localization
from app.translation.incremental_builder import build_incremental_package
from app.translation.package_importer import inspect_translation_zip, install_translation_zip
from app.translation_update import analyze_legacy, analyze_with_snapshot, build_merged_translation_zip
from app.utils.paths import app_temp_root
from app.validation.localization_validator import validate_translation_zip


class TranslationUpdatePage(QScrollArea):
    status_changed = Signal(str, str); activity_completed = Signal(str, str, str)

    def __init__(self, config: ConfigManager, project_manager) -> None:
        super().__init__(); self.config = config; self.project_manager = project_manager; self.diff = None; self.project = None
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(26, 20, 26, 20); root.setSpacing(14)
        root.addWidget(PageHeader(t("update_translation.title"), t("update_translation.description")))
        panel = QFrame(objectName="formPanel"); form = QGridLayout(panel); form.setContentsMargins(20, 18, 20, 18); form.setVerticalSpacing(10)
        self.projects = QComboBox(); self.projects.addItem(t("update_translation.manual"), None)
        for project in project_manager.projects: self.projects.addItem(str(project.get("name", "Project")), project)
        self.projects.currentIndexChanged.connect(self._project_selected); form.addWidget(QLabel(t("projects.title")), 0, 0); form.addWidget(self.projects, 0, 1, 1, 2)
        self.previous = self._path_row(form, 1, t("update_translation.previous"), "last_update_previous_path")
        self.existing = self._path_row(form, 2, t("update_translation.existing"), "last_update_translation_path")
        self.updated = self._path_row(form, 3, t("update_translation.updated"), "last_update_source_path")
        analyze = QPushButton(t("update_translation.analyze"), objectName="secondaryButton"); analyze.clicked.connect(self._analyze); form.addWidget(analyze, 4, 2)
        self.summary = QTextEdit(); self.summary.setReadOnly(True); self.summary.setMinimumHeight(110); form.addWidget(self.summary, 5, 0, 1, 3)
        self.output = QLineEdit(); self.output.setPlaceholderText("V3MM_Translation_Update.zip"); browse = QPushButton(t("common.browse")); browse.clicked.connect(self._output); build = QPushButton(t("update_translation.build"), objectName="burgundyButton"); build.clicked.connect(self._build); form.addWidget(self.output, 6, 0); form.addWidget(browse, 6, 1); form.addWidget(build, 6, 2)
        self.returned = QLineEdit(); self.returned.setPlaceholderText(t("update_translation.returned")); returned_browse = QPushButton(t("common.browse")); returned_browse.clicked.connect(self._returned); merge = QPushButton(t("update_translation.merge"), objectName="blueButton"); merge.clicked.connect(self._merge_apply); form.addWidget(self.returned, 7, 0); form.addWidget(returned_browse, 7, 1); form.addWidget(merge, 7, 2)
        root.addWidget(panel); root.addStretch(); self.setWidget(content)

    def _path_row(self, form, row, label, key):
        edit = QLineEdit(str(self.config.data.get(key, ""))); button = QPushButton(t("common.browse")); button.clicked.connect(lambda checked=False, field=edit: self._folder(field)); form.addWidget(QLabel(label), row, 0); form.addWidget(edit, row, 1); form.addWidget(button, row, 2); return edit
    def _folder(self, edit):
        value = QFileDialog.getExistingDirectory(self, t("common.browse"), edit.text());
        if value: edit.setText(value)
    def _output(self):
        value, _ = QFileDialog.getSaveFileName(self, t("update_translation.build"), self.output.text() or "V3MM_Translation_Update.zip", "ZIP (*.zip)");
        if value: self.output.setText(value if value.lower().endswith(".zip") else value + ".zip")
    def _returned(self):
        value, _ = QFileDialog.getOpenFileName(self, t("update_translation.returned"), "", "ZIP (*.zip)");
        if value: self.returned.setText(value)
    def _project_selected(self):
        self.project = self.projects.currentData()
        if not self.project: return
        source = str(self.project.get("localization_path") or self.project.get("source_path", "")); install = str(self.project.get("install_path", "")); self.updated.setText(source); self.existing.setText(install)
    def set_project(self, project):
        for index in range(self.projects.count()):
            value = self.projects.itemData(index)
            if value and value.get("id") == project.get("id"): self.projects.setCurrentIndex(index); return
        self.project = dict(project); self.updated.setText(str(project.get("localization_path") or project.get("source_path", ""))); self.existing.setText(str(project.get("install_path", "")))
    def _language(self):
        return target_language(str((self.project or {}).get("target_language") or self.config.data.get("language", "ko-KR")))
    def _snapshot_project(self):
        if self.project: return self.project
        source = Path(self.updated.text()).resolve(); digest = hashlib.sha256(str(source).casefold().encode("utf-8")).hexdigest()[:16]
        return {"id": f"manual_{digest}", "name": source.name, "source_path": str(source), "localization_path": str(source)}
    def _analyze(self):
        if not self.updated.text() or not self.existing.text(): QMessageBox.warning(self, t("common.input"), t("update_translation.required")); return
        try:
            if self.previous.text().strip():
                self.diff = analyze_with_snapshot(capture_localization(Path(self.previous.text())), Path(self.updated.text())); mode = t("update_translation.snapshot_mode")
            elif (snapshot := SnapshotManager().latest(str(self._snapshot_project().get("id", "")))):
                self.diff = analyze_with_snapshot(snapshot, Path(self.updated.text())); mode = t("update_translation.snapshot_mode")
            else:
                self.diff = analyze_legacy(Path(self.existing.text()), Path(self.updated.text())); mode = t("update_translation.legacy_mode")
            counts = {}
            for item in self.diff.items: counts[item.status] = counts.get(item.status, 0) + 1
            self.summary.setPlainText(mode + "\n" + " · ".join(f"{key}: {value}" for key, value in counts.items())); self.status_changed.emit(t("update_translation.analyzed"), "ready")
            self.config.update(last_update_previous_path=self.previous.text(), last_update_translation_path=self.existing.text(), last_update_source_path=self.updated.text())
        except Exception as error: show_operation_error(self, t("update_translation.failed"), error)
    def _build(self):
        if self.diff is None: self._analyze()
        if self.diff is None or not self.output.text().strip(): return
        try:
            report = build_incremental_package(self.diff, Path(self.updated.text()), Path(self.output.text()), self._language(), int(self.config.data.get("prompt_version", 4))); self.status_changed.emit(t("update_translation.package_complete"), "ready"); self.activity_completed.emit(Path(self.updated.text()).name, "package", "package_ready"); QMessageBox.information(self, t("update_translation.package_complete"), t("package.total", count=len(report.files)))
        except Exception as error: show_operation_error(self, t("update_translation.failed"), error)
    def _merge_apply(self):
        if not self.returned.text().strip() or not self.existing.text().strip() or not self.updated.text().strip(): QMessageBox.warning(self, t("common.input"), t("update_translation.required")); return
        try:
            language = self._language(); app_temp_root().mkdir(parents=True, exist_ok=True)
            validation = validate_translation_zip(Path(self.returned.text()))
            if validation is not None and (validation.issues or validation.errors):
                if ValidationDialog(validation, self).exec() != ValidationDialog.DialogCode.Accepted: return
            with tempfile.TemporaryDirectory(prefix="update_", dir=app_temp_root()) as temp:
                merged = Path(temp) / "merged_translation.zip"; report = build_merged_translation_zip(Path(self.existing.text()), Path(self.returned.text()), merged, language.filename_suffix, language.localization_header)
                files = inspect_translation_zip(merged, language.filename_suffix); policy = confirm_install(self, files, Path(self.existing.text()), True)
                if policy is None: return
                # Updates always retain a recoverable copy even if the global setting is off.
                if policy is OverwritePolicy.OVERWRITE: policy = OverwritePolicy.BACKUP_AND_OVERWRITE
                if policy is OverwritePolicy.SKIP:
                    self.status_changed.emit(t("apply.cancelled"), "ready"); return
                result = install_translation_zip(merged, Path(self.existing.text()), policy, language.filename_suffix)
            SnapshotManager().save(self._snapshot_project(), language, Path(self.updated.text()))
            self.status_changed.emit(t("update_translation.complete"), "ready"); self.activity_completed.emit(Path(self.existing.text()).name, "apply", "applied"); QMessageBox.information(self, t("update_translation.complete"), t("update_translation.merge_summary", replaced=report.replaced, added=report.added, preserved=report.preserved, installed=len(result.installed)))
        except Exception as error: show_operation_error(self, t("update_translation.failed"), error)
