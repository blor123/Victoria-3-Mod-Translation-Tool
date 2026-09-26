from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.config.config_manager import ConfigManager
from app.gui.prompt_dialog import PromptDialog
from app.gui.widgets.page_header import PageHeader
from app.i18n import SUPPORTED_LANGUAGES, t
from app.translation.prompt_manager import restore_default_prompt


class SettingsPage(QScrollArea):
    settings_saved = Signal()
    language_changed = Signal(str)
    update_check_requested = Signal()

    def __init__(self, config: ConfigManager) -> None:
        super().__init__(); self.config = config; self.setObjectName("pageSurface"); self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(28, 22, 28, 22); root.setSpacing(18)
        root.addWidget(PageHeader(t("settings.title"), t("settings.description")))
        panel = QFrame(objectName="formPanel"); layout = QVBoxLayout(panel); layout.setContentsMargins(24, 22, 24, 22); layout.setSpacing(13)
        layout.addWidget(QLabel(t("settings.general"), objectName="panelTitle"))
        language_row = QHBoxLayout(); language_row.addWidget(QLabel(t("settings.language")))
        self.language = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items(): self.language.addItem(name, code)
        index = self.language.findData(str(config.data.get("language", "ko-KR"))); self.language.setCurrentIndex(max(index, 0))
        self.language.currentIndexChanged.connect(self._change_language)
        self.language.setMaximumWidth(240)
        language_row.addWidget(self.language); language_row.addStretch(); layout.addLayout(language_row)
        helper = QLabel(t("settings.target_help"), objectName="mutedText"); helper.setWordWrap(True); layout.addWidget(helper)
        layout.addWidget(QLabel(t("settings.translation"), objectName="panelTitle"))
        self.backup = QCheckBox(t("settings.backup")); self.open_folder = QCheckBox(t("settings.open_folder")); self.remember_paths = QCheckBox(t("settings.remember"))
        self.backup.setChecked(bool(config.data.get("create_backup", True))); self.open_folder.setChecked(bool(config.data.get("open_export_folder_after_creation", True))); self.remember_paths.setChecked(bool(config.data.get("remember_recent_paths", True)))
        layout.addWidget(self.backup); layout.addWidget(self.open_folder); layout.addWidget(self.remember_paths)
        layout.addWidget(QLabel(t("update.section"), objectName="panelTitle"))
        self.check_updates = QCheckBox(t("update.check_startup")); self.check_updates.setChecked(bool(config.data.get("check_updates_on_startup", True))); layout.addWidget(self.check_updates)
        update_row = QHBoxLayout(); check = QPushButton(t("update.check_now"), objectName="secondaryButton"); check.clicked.connect(self.update_check_requested); update_row.addWidget(check); update_row.addWidget(QLabel(t("update.current", version=__import__('app').APP_VERSION), objectName="mutedText")); update_row.addStretch(); layout.addLayout(update_row)
        layout.addWidget(QLabel(t("settings.prompt"), objectName="panelTitle"))
        prompt_row = QHBoxLayout(); edit = QPushButton(t("settings.prompt_edit")); restore = QPushButton(t("settings.prompt_restore"), objectName="secondaryButton")
        edit.clicked.connect(lambda: PromptDialog(self.config, self).exec()); restore.clicked.connect(self._restore_prompt)
        prompt_row.addWidget(edit); prompt_row.addWidget(restore); prompt_row.addStretch(); layout.addLayout(prompt_row)
        note = QLabel(t("settings.note"), objectName="mutedText"); note.setWordWrap(True); layout.addWidget(note)
        save = QPushButton(t("settings.save")); save.clicked.connect(self.save); layout.addWidget(save)
        root.addWidget(panel); root.addStretch(); self.setWidget(content)

    def _change_language(self) -> None:
        code = str(self.language.currentData())
        old = str(self.config.data.get("language", "ko-KR"))
        if code != old:
            values = {"language": code}
            if str(self.config.data.get("prompt_language", old)) == old: values["prompt_language"] = code
            self.config.update(**values); self.language_changed.emit(code)

    def _restore_prompt(self) -> None:
        restore_default_prompt(self.config); self.settings_saved.emit()

    def save(self) -> None:
        self.config.update(create_backup=self.backup.isChecked(), open_export_folder_after_creation=self.open_folder.isChecked(), remember_recent_paths=self.remember_paths.isChecked(), language=str(self.language.currentData()), check_updates_on_startup=self.check_updates.isChecked())
        self.settings_saved.emit()
