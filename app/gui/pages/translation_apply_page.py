from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config.config_manager import ConfigManager
from app.errors import OperationCancelled
from app.gui.dialogs import confirm_install, friendly_error, show_operation_error
from app.gui.widgets.page_header import PageHeader
from app.gui.widgets.result_panel import ResultPanel
from app.translation.package_importer import inspect_translation_zip, install_translation_zip
from app.i18n import t
from app.i18n.language_definition import target_language
from app.validation.localization_validator import validate_translation_zip
from app.gui.validation_dialog import ValidationDialog
from app.snapshots import SnapshotManager
from app.projects import resolve_localization_path


class TranslationApplyPage(QScrollArea):
    status_changed = Signal(str, str)
    activity_completed = Signal(str, str, str)

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.current_project: dict | None = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("pageSurface")
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(18)
        root.addWidget(
            PageHeader(
                t("apply.title"), t("apply.description"),
            )
        )
        panel = QFrame()
        panel.setObjectName("formPanel")
        form = QGridLayout(panel)
        form.setContentsMargins(24, 24, 24, 24)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(15)
        self.import_edit = QLineEdit()
        self.import_edit.setPlaceholderText(t("apply.zip"))
        import_button = QPushButton(t("apply.browse"))
        import_button.clicked.connect(self._choose_import_zip)
        clear_import = QPushButton(t("common.reset"), objectName="secondaryButton"); clear_import.clicked.connect(self._clear_import)
        self.install_edit = QLineEdit()
        self.install_edit.setPlaceholderText(t("apply.install"))
        install_button = QPushButton(t("apply.browse"))
        install_button.clicked.connect(self._choose_install_folder)
        clear_install = QPushButton(t("common.reset"), objectName="secondaryButton"); clear_install.clicked.connect(self._clear_install)
        form.addWidget(QLabel(t("apply.zip")), 0, 0, 1, 3)
        form.addWidget(self.import_edit, 1, 0)
        form.addWidget(import_button, 1, 1)
        form.addWidget(clear_import, 1, 2)
        form.addWidget(QLabel(t("apply.install")), 2, 0, 1, 3)
        form.addWidget(self.install_edit, 3, 0)
        form.addWidget(install_button, 3, 1)
        form.addWidget(clear_install, 3, 2)
        note = QLabel(t("apply.note"))
        note.setObjectName("mutedText")
        note.setWordWrap(True)
        form.addWidget(note, 4, 0, 1, 3)
        actions = QHBoxLayout()
        reset_all = QPushButton(t("common.reset_all"), objectName="secondaryButton"); reset_all.clicked.connect(self.reset_all); actions.addWidget(reset_all); actions.addStretch()
        apply_button = QPushButton(t("apply.button"))
        apply_button.setObjectName("blueButton")
        apply_button.clicked.connect(self._apply_translation)
        actions.addWidget(apply_button)
        form.addLayout(actions, 5, 0, 1, 3)
        root.addWidget(panel)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        root.addWidget(self.progress)
        self.result = ResultPanel()
        root.addWidget(self.result)
        root.addStretch()
        self.setWidget(content)
        self.restore_paths()

    def restore_paths(self) -> None:
        if not self.config.data.get("remember_recent_paths", True):
            return
        self.install_edit.setText(str(self.config.data.get("last_install_path", "")))
        self.import_edit.setText(str(self.config.data.get("last_import_zip_path", "")))

    def set_project(self, project: dict) -> None:
        self.current_project = dict(project)
        if project.get("install_path"): self.install_edit.setText(str(project["install_path"]))

    def reset_all(self) -> None:
        self.current_project = None; self.import_edit.clear(); self.install_edit.clear(); self.progress.hide(); self.result.hide(); self.config.update(last_import_zip_path="", last_install_path="")

    def _clear_import(self) -> None:
        self.import_edit.clear(); self.result.hide(); self.config.update(last_import_zip_path="")

    def _clear_install(self) -> None:
        self.install_edit.clear(); self.result.hide(); self.config.update(last_install_path="")

    def _dialog_start(self, value: str) -> str:
        path = Path(value) if value else Path.home()
        return str(path if path.is_dir() else path.parent)

    def _choose_import_zip(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, t("apply.zip"), self._dialog_start(self.import_edit.text()), "ZIP (*.zip)"
        )
        if filename:
            self.import_edit.setText(filename)

    def _choose_install_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, t("apply.install"), self._dialog_start(self.install_edit.text())
        )
        if folder:
            self.install_edit.setText(folder)

    def _apply_translation(self) -> None:
        zip_text = self.import_edit.text().strip()
        install_text = self.install_edit.text().strip()
        if not zip_text or not install_text:
            QMessageBox.warning(self, t("common.input"), t("apply.input_required"))
            return
        zip_path = Path(zip_text)
        install_root = Path(install_text)
        try:
            language = target_language(str(self.config.data.get("language", "ko-KR")))
            files = inspect_translation_zip(zip_path, language.filename_suffix)
            validation = validate_translation_zip(zip_path)
            if validation is not None and (validation.issues or validation.errors):
                if ValidationDialog(validation, self).exec() != ValidationDialog.DialogCode.Accepted: return
            elif validation is None:
                self.status_changed.emit(t("validation.no_manifest"), "busy")
            policy = confirm_install(
                self,
                files,
                install_root,
                bool(self.config.data.get("create_backup", True)),
            )
            if policy is None:
                return
            self.progress.show()
            self.result.hide()
            self.status_changed.emit(t("apply.busy"), "busy")
            QApplication.processEvents()
            result = install_translation_zip(zip_path, install_root, policy, language.filename_suffix)
            if self.current_project and self.current_project.get("id"):
                source_root = resolve_localization_path(self.current_project, language)
                snapshots = SnapshotManager()
                if source_root.exists() and snapshots.latest(self.current_project["id"]) is None:
                    snapshots.save(self.current_project, language, source_root)
            if self.config.data.get("remember_recent_paths", True):
                self.config.update(
                    last_import_zip_path=str(zip_path), last_install_path=str(install_root)
                )
            self.result.show_success(
                t("apply.complete"),
                t("apply.summary", installed=len(result.installed), skipped=len(result.skipped), backed_up=len(result.backed_up)),
                install_root,
            )
            self.activity_completed.emit(install_root.name, "apply", "applied")
            self.status_changed.emit(t("apply.complete"), "ready")
        except OperationCancelled:
            self.status_changed.emit(t("apply.cancelled"), "ready")
        except Exception as error:
            self.result.show_error(t("apply.failed"), friendly_error(error))
            self.status_changed.emit(t("apply.error"), "error")
            show_operation_error(self, t("apply.error"), error)
        finally:
            self.progress.hide()
