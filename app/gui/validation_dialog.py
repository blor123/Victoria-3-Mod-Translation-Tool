from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextEdit, QVBoxLayout

from app.i18n import t


class ValidationDialog(QDialog):
    def __init__(self, report, parent=None) -> None:
        super().__init__(parent); self.setWindowTitle(t("validation.title")); self.resize(680, 460)
        root = QVBoxLayout(self)
        root.addWidget(QLabel(t("validation.summary", expected=report.expected_files, actual=report.actual_files, errors=len(report.errors), warnings=len(report.warnings))))
        details = QTextEdit(); details.setReadOnly(True)
        details.setPlainText("\n".join(f"[{item.severity}] {item.filename}: {item.message}" for item in report.issues) or t("validation.success")); root.addWidget(details)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("validation.proceed")); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
