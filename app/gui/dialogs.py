import logging
import traceback
from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QWidget

from app.errors import V3MMError
from app.models import OverwritePolicy
from app.i18n import t


def friendly_error(error: Exception) -> str:
    if isinstance(error, V3MMError):
        return str(error)
    if isinstance(error, PermissionError):
        return t("common.permission")
    return t("common.unexpected")


def show_operation_error(parent: QWidget, title: str, error: Exception) -> None:
    summary = friendly_error(error)
    logging.getLogger("v3mm").exception(title)
    message = QMessageBox(parent)
    message.setIcon(QMessageBox.Icon.Critical)
    message.setWindowTitle(t("common.error"))
    message.setText(f"{title}\n\n{summary}")
    message.setDetailedText("".join(traceback.format_exception(error)))
    message.exec()


def confirm_install(
    parent: QWidget, files: list, install_root: Path, prefer_backup: bool
) -> OverwritePolicy | None:
    existing = [item for item in files if (install_root / item.install_relative_path).exists()]
    preview = "\n".join(f"• {item.install_relative_path.as_posix()}" for item in files[:12])
    if len(files) > 12:
        preview += f"\n• {t('install.more', count=len(files) - 12)}"
    message = QMessageBox(parent)
    message.setIcon(QMessageBox.Icon.Question)
    message.setWindowTitle(t("install.title"))
    message.setText(t("install.text", count=len(files), path=install_root))
    message.setInformativeText(
        t("install.info", existing=len(existing), preview=preview)
    )
    backup_button = message.addButton(t("install.backup"), QMessageBox.ButtonRole.AcceptRole)
    overwrite_button = message.addButton(t("install.overwrite"), QMessageBox.ButtonRole.DestructiveRole)
    skip_button = message.addButton(t("install.skip"), QMessageBox.ButtonRole.ActionRole)
    message.addButton(t("common.cancel"), QMessageBox.ButtonRole.RejectRole)
    message.setDefaultButton(backup_button if prefer_backup else overwrite_button)
    message.exec()
    clicked = message.clickedButton()
    if clicked is backup_button:
        return OverwritePolicy.BACKUP_AND_OVERWRITE
    if clicked is overwrite_button:
        return OverwritePolicy.OVERWRITE
    if clicked is skip_button:
        return OverwritePolicy.SKIP
    return None
