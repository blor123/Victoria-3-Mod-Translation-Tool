from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget)

from app.config.config_manager import ConfigManager
from app.gui.dialogs import friendly_error, show_operation_error
from app.gui.prompt_dialog import PromptDialog
from app.gui.widgets.drop_area import DropArea
from app.gui.widgets.page_header import PageHeader
from app.gui.widgets.result_panel import ResultPanel
from app.i18n import t
from app.i18n.language_definition import target_language
from app.translation.package_builder import build_translation_package_report, plan_package
from app.translation.prompt_manager import active_prompt
from app.snapshots import SnapshotManager
from app.projects import resolve_localization_path


def _size_text(size: int) -> str:
    if size < 1024: return f"{size} B"
    if size < 1024 * 1024: return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


class TranslationPackagePage(QScrollArea):
    status_changed = Signal(str, str)
    activity_completed = Signal(str, str, str)

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.source_paths: list[Path] = []
        self.planned = []
        self.current_project: dict | None = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(objectName="pageSurface")
        root = QVBoxLayout(content); root.setContentsMargins(28, 22, 28, 22); root.setSpacing(14)
        root.addWidget(PageHeader(t("package.title"), t("package.description")))
        self.drop_area = DropArea(); self.drop_area.paths_dropped.connect(self.add_sources); root.addWidget(self.drop_area)
        panel = QFrame(objectName="formPanel")
        form = QGridLayout(panel); form.setContentsMargins(22, 20, 22, 20); form.setSpacing(11)
        self.source_edit = QLineEdit(); self.source_edit.setReadOnly(True)
        file_button = QPushButton(t("package.files")); folder_button = QPushButton(t("package.folder")); clear_sources = QPushButton(t("common.reset"), objectName="secondaryButton")
        file_button.clicked.connect(self._choose_source_files); folder_button.clicked.connect(self._choose_source_folder)
        clear_sources.clicked.connect(self.clear_sources); clear_sources.setToolTip(t("common.reset_path_tooltip"))
        form.addWidget(self.source_edit, 0, 0); form.addWidget(file_button, 0, 1); form.addWidget(folder_button, 0, 2); form.addWidget(clear_sources, 0, 3)
        form.addWidget(QLabel(t("package.target"), objectName="panelTitle"), 1, 0, 1, 4)
        self.target_list = QListWidget(); self.target_list.setMinimumHeight(105)
        self.target_count = QLabel(t("package.empty"), objectName="mutedText")
        form.addWidget(self.target_list, 2, 0, 1, 4); form.addWidget(self.target_count, 3, 0, 1, 4)
        selection = QHBoxLayout(); select_all = QPushButton(t("package.select_all"), objectName="secondaryButton"); select_none = QPushButton(t("package.select_none"), objectName="secondaryButton"); select_all.clicked.connect(lambda: self._set_checks(True)); select_none.clicked.connect(lambda: self._set_checks(False)); selection.addWidget(select_all); selection.addWidget(select_none); selection.addStretch(); form.addLayout(selection, 4, 0, 1, 4)
        self.export_edit = QLineEdit(); self.export_edit.setPlaceholderText("V3MM_Translation_Package.zip")
        export_button = QPushButton(t("package.browse")); export_button.clicked.connect(self._choose_export_zip); clear_export = QPushButton(t("common.reset"), objectName="secondaryButton"); clear_export.clicked.connect(self._clear_export)
        form.addWidget(QLabel(t("package.export")), 5, 0, 1, 4); form.addWidget(self.export_edit, 6, 0, 1, 2); form.addWidget(export_button, 6, 2); form.addWidget(clear_export, 6, 3)
        actions = QHBoxLayout()
        copy_button = QPushButton(t("package.copy_prompt"), objectName="secondaryButton")
        edit_button = QPushButton(t("package.edit_prompt"), objectName="secondaryButton")
        create_button = QPushButton(t("package.create"), objectName="burgundyButton")
        copy_button.clicked.connect(self._copy_prompt); edit_button.clicked.connect(lambda: PromptDialog(self.config, self).exec()); create_button.clicked.connect(self._create_package)
        reset_all = QPushButton(t("common.reset_all"), objectName="secondaryButton"); reset_all.clicked.connect(self.reset_all)
        actions.addWidget(copy_button); actions.addWidget(edit_button); actions.addWidget(reset_all); actions.addStretch(); actions.addWidget(create_button)
        form.addLayout(actions, 7, 0, 1, 4); root.addWidget(panel)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); root.addWidget(self.progress)
        self.result = ResultPanel(); root.addWidget(self.result); root.addStretch(); self.setWidget(content)
        self.restore_paths()

    def restore_paths(self) -> None:
        if self.config.data.get("remember_recent_paths", True):
            source = str(self.config.data.get("last_source_path", ""))
            if source and Path(source).exists(): self.add_sources([Path(source)])
            self.export_edit.setText(str(self.config.data.get("last_export_path", "")))

    def add_sources(self, paths: list[Path]) -> None:
        unique = {str(p.resolve()).casefold(): p.resolve() for p in self.source_paths if p.exists()}
        unique.update({str(Path(p).resolve()).casefold(): Path(p).resolve() for p in paths if Path(p).exists()})
        self.source_paths = list(unique.values()); self.source_edit.setText(" | ".join(map(str, self.source_paths))); self._refresh_targets()

    def clear_sources(self) -> None:
        self.current_project = None; self.source_paths = []; self.planned = []; self.source_edit.clear(); self.target_list.clear(); self.target_count.setText(t("package.empty")); self.result.hide(); self.config.update(last_source_path="")

    def reset_all(self) -> None:
        self.clear_sources(); self.export_edit.clear(); self.progress.hide(); self.result.hide(); self.config.update(last_export_path="")

    def _clear_export(self) -> None:
        self.export_edit.clear(); self.result.hide(); self.config.update(last_export_path="")

    def _refresh_targets(self) -> None:
        self.target_list.clear()
        if not self.source_paths: self.target_count.setText(t("package.empty")); return
        try:
            language = target_language(str(self.config.data.get("language", "ko-KR"))); self.planned = plan_package(self.source_paths, language)
            for planned in self.planned:
                item = QListWidgetItem(f"{'⚠' if planned.warning else '✓'}  {planned.source.name}"); item.setData(Qt.ItemDataRole.UserRole, str(planned.source)); item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked); self.target_list.addItem(item)
            self.target_count.setText(t("package.total", count=len(self.planned))); self.status_changed.emit(t("package.found", count=len(self.planned)), "busy")
        except Exception as error: self.target_count.setText(f"⚠ {friendly_error(error)}")

    def _set_checks(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.target_list.count()): self.target_list.item(index).setCheckState(state)

    def set_project(self, project: dict) -> None:
        value = resolve_localization_path(project, target_language(str(self.config.data.get("language", "ko-KR"))))
        if value and Path(value).exists(): self.source_paths = []; self.add_sources([Path(value)]); self.current_project = dict(project)

    def _dialog_start(self, value: str) -> str:
        path = Path(value) if value and " | " not in value else Path.home()
        return str(path if path.is_dir() else path.parent)

    def _choose_source_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, t("package.files"), self._dialog_start(self.source_edit.text()), "YML (*.yml)")
        if files: self.add_sources([Path(item) for item in files])

    def _choose_source_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("package.folder"), self._dialog_start(self.source_edit.text()))
        if folder: self.add_sources([Path(folder)])

    def _choose_export_zip(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, t("package.export"), self.export_edit.text() or "V3MM_Translation_Package.zip", "ZIP (*.zip)")
        if filename: self.export_edit.setText(filename if filename.lower().endswith(".zip") else filename + ".zip")

    def _copy_prompt(self) -> None:
        try:
            QApplication.clipboard().setText(active_prompt(self.config, target_language(str(self.config.data.get("language", "ko-KR"))))); version = int(self.config.data.get("prompt_version", 2))
            self.status_changed.emit(t("prompt.copied", version=version), "ready")
            QMessageBox.information(self, t("common.copied"), t("prompt.copied", version=version))
        except OSError as error: show_operation_error(self, t("prompt.read_error"), error)

    def _create_package(self) -> None:
        destination_text = self.export_edit.text().strip()
        selected = [Path(self.target_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.target_list.count()) if self.target_list.item(i).checkState() == Qt.CheckState.Checked]
        if not self.target_list.count():
            selected = list(self.source_paths)
        if not selected or not destination_text:
            QMessageBox.warning(self, t("common.input"), t("package.input_required")); return
        destination = Path(destination_text)
        if destination.exists() and QMessageBox.question(self, t("package.overwrite_title"), t("package.overwrite_question"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        self.progress.show(); self.result.hide(); self.status_changed.emit(t("package.busy"), "busy"); QApplication.processEvents()
        try:
            language = target_language(str(self.config.data.get("language", "ko-KR")))
            report = build_translation_package_report(selected, destination, language, int(self.config.data.get("prompt_version", 2)))
            if self.current_project and self.current_project.get("id"):
                root = resolve_localization_path(self.current_project, language)
                if root.exists(): SnapshotManager().save(self.current_project, language, root)
            if self.config.data.get("remember_recent_paths", True): self.config.update(last_source_path=str(self.source_paths[0]), last_export_path=str(destination))
            details = t("package.summary", files=len(report.files), size=_size_text(report.total_size), renamed=report.renamed_count, headers=report.declaration_changed_count, warnings=len(report.warnings), path=destination)
            if report.warnings:
                lines = "\n".join(f"• {item.source.name}: {item.warning}" for item in report.warnings); details += "\n\n" + t("package.warning_detail", warnings=lines)
            self.result.show_success(t("package.complete"), details, destination.parent)
            first = self.source_paths[0]; name = first.parent.name if first.is_file() else first.name
            self.activity_completed.emit(name, "package", "package_ready"); self.status_changed.emit(t("package.complete"), "ready")
            if self.config.data.get("open_export_folder_after_creation", True): QDesktopServices.openUrl(QUrl.fromLocalFile(str(destination.parent)))
        except Exception as error:
            self.result.show_error(t("package.failed"), friendly_error(error)); self.status_changed.emit(t("package.error"), "error"); show_operation_error(self, t("package.error"), error)
        finally: self.progress.hide()
