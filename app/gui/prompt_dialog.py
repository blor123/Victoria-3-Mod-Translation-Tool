from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.config.config_manager import ConfigManager
from app.i18n import t
from app.translation.prompt_manager import prompt_body, restore_default_prompt, save_custom_prompt


class PromptDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None, language: str | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.language = language or str(config.data.get("prompt_language", config.data.get("language", "ko-KR")))
        self.setWindowTitle(t("prompt.title"))
        self.resize(720, 560)
        layout = QVBoxLayout(self)
        note = QLabel(t("prompt.description"))
        note.setObjectName("mutedText")
        self.editor = QTextEdit(prompt_body(config, self.language))
        controls = QHBoxLayout()
        restore = QPushButton(t("common.restore"))
        copy = QPushButton(t("common.copy"))
        save = QPushButton(t("common.save"))
        save.setObjectName("burgundyButton")
        restore.clicked.connect(self._restore)
        copy.clicked.connect(self._copy)
        save.clicked.connect(self._save)
        controls.addWidget(restore)
        controls.addWidget(copy)
        controls.addStretch()
        controls.addWidget(save)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.button(QDialogButtonBox.StandardButton.Close).setText(t("common.close"))
        close.rejected.connect(self.reject)
        layout.addWidget(note)
        layout.addWidget(self.editor, 1)
        layout.addLayout(controls)
        layout.addWidget(close)

    def _restore(self) -> None:
        self.editor.setPlainText(restore_default_prompt(self.config, self.language))
        QMessageBox.information(self, t("prompt.title"), t("prompt.restored"))

    def _copy(self) -> None:
        QApplication.clipboard().setText(self.editor.toPlainText())
        QMessageBox.information(self, t("common.copied"), t("prompt.copied", version=2))

    def _save(self) -> None:
        save_custom_prompt(self.config, self.editor.toPlainText(), self.language)
        QMessageBox.information(self, t("prompt.title"), t("prompt.saved"))
