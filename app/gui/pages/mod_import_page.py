from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from app.gui.dialogs import show_operation_error
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.mod_sources import JsonModSourceProvider, ParadoxLauncherProvider, SteamModSourceProvider, export_mod_list
from app.mod_sources.manual_provider import ManualModSourceProvider
from app.mod_sources.models import ModSource


class ModImportPage(QScrollArea):
    status_changed = Signal(str, str)

    def __init__(self, config, manager) -> None:
        super().__init__(); self.config = config; self.manager = manager; self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame); self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(24, 18, 24, 18); root.setSpacing(14)
        root.addWidget(PageHeader(t("mod_import.title"), t("mod_import.description")))
        source = QFrame(objectName="formPanel"); row = QGridLayout(source); row.setContentsMargins(18, 15, 18, 15); row.setSpacing(8); row.addWidget(QLabel(t("mod_import.source"), objectName="panelTitle"), 0, 0, 1, 2)
        steam = QPushButton(t("mod_import.steam")); steam.clicked.connect(self._steam); paradox = QPushButton(t("mod_import.paradox")); paradox.clicked.connect(self._paradox)
        folder = QPushButton(t("mod_import.folder")); folder.clicked.connect(self._folder); json_button = QPushButton(t("mod_import.json_import")); json_button.clicked.connect(self._json_import)
        row.addWidget(steam, 1, 0); row.addWidget(paradox, 1, 1); row.addWidget(folder, 2, 0); row.addWidget(json_button, 2, 1)
        root.addWidget(source)
        self.notice = QLabel(t("mod_import.read_only"), objectName="mutedText"); self.notice.setWordWrap(True); root.addWidget(self.notice)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels([t("mod_import.name"), t("mod_import.type"), t("mod_import.workshop"), t("mod_import.path"), t("mod_import.localization"), t("mod_import.enabled"), t("mod_import.order")]); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.verticalHeader().hide(); self.table.horizontalHeader().setStretchLastSection(False); self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().ResizeMode.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(3, self.table.horizontalHeader().ResizeMode.Stretch); self.table.setMinimumHeight(290); root.addWidget(self.table)
        actions = QHBoxLayout(); self.count = QLabel(objectName="mutedText"); actions.addWidget(self.count); actions.addStretch(); export = QPushButton(t("mod_import.export"), objectName="secondaryButton"); export.clicked.connect(self._export); clear = QPushButton(t("activity.clear_all"), objectName="secondaryButton"); clear.clicked.connect(self._clear); actions.addWidget(export); actions.addWidget(clear); root.addLayout(actions); root.addStretch(); self.setWidget(content)
        manager.changed.connect(self.refresh); self.refresh()

    def refresh(self) -> None:
        entries = self.manager.entries; self.table.setRowCount(len(entries))
        source_names = {ModSource.MANUAL: t("mod_import.source_manual"), ModSource.STEAM_WORKSHOP: "Steam Workshop", ModSource.PARADOX_LAUNCHER: "Paradox Launcher", ModSource.JSON_IMPORT: "JSON"}
        for row, entry in enumerate(entries):
            values = [entry.name, source_names.get(entry.source, entry.source.value), entry.workshop_id, str(entry.path or ""), ", ".join(path.name for path in entry.localization_paths), "✓" if entry.enabled is True else ("—" if entry.enabled is None else "✕"), "" if entry.load_order_position is None else str(entry.load_order_position)]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value); item.setToolTip(value); self.table.setItem(row, column, item)
        self.count.setText(t("mod_import.count", count=len(entries)))

    def _consume(self, provider, failure_key="mod_import.failed") -> None:
        try:
            entries = provider.discover(); self.manager.merge(entries); warnings = getattr(provider, "warnings", [])
            if entries: message = t("mod_import.found", count=len(entries)); state = "ready"
            elif warnings and failure_key != "mod_import.failed": message = t(failure_key); state = "error"
            else: message = t("mod_import.none"); state = "error"
            if warnings: message += "\n" + t("mod_import.warning", detail=warnings[0])
            self.notice.setText(message); self.status_changed.emit(message.splitlines()[0], state)
        except Exception as error:
            self.notice.setText(t(failure_key)); self.status_changed.emit(t(failure_key), "error"); show_operation_error(self, t(failure_key), error)

    def _steam(self): self._consume(SteamModSourceProvider(), "mod_import.steam_failed")
    def _paradox(self): self._consume(ParadoxLauncherProvider(), "mod_import.paradox_failed")
    def _folder(self):
        value = QFileDialog.getExistingDirectory(self, t("mod_import.folder"), str(self.config.data.get("last_mod_import_path", "")))
        if value: self.config.update(last_mod_import_path=value); self._consume(ManualModSourceProvider([Path(value)]))
    def _json_import(self):
        value, _ = QFileDialog.getOpenFileName(self, t("mod_import.json_import"), str(self.config.data.get("last_mod_import_path", "")), "JSON (*.json)")
        if value: self.config.update(last_mod_import_path=value); self._consume(JsonModSourceProvider(Path(value)))
    def _export(self):
        if not self.manager.entries: QMessageBox.information(self, t("mod_import.title"), t("mod_import.none")); return
        value, _ = QFileDialog.getSaveFileName(self, t("mod_import.export"), str(self.config.data.get("last_mod_export_path", "")) or "V3MM_Mod_List.json", "JSON (*.json)")
        if not value: return
        destination = Path(value if value.lower().endswith(".json") else value + ".json")
        try: export_mod_list(self.manager.entries, destination); self.config.update(last_mod_export_path=str(destination)); self.status_changed.emit(t("mod_import.exported"), "ready"); QMessageBox.information(self, t("mod_import.export"), str(destination))
        except Exception as error: show_operation_error(self, t("mod_import.failed"), error)
    def _clear(self):
        if QMessageBox.question(self, t("activity.clear_all"), t("mod_import.clear_question"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes: self.manager.clear()
