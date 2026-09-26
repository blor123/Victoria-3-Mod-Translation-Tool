from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from app.gui.dialogs import show_operation_error
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.mod_sources.models import ModSource


class ModLibraryPage(QScrollArea):
    status_changed = Signal(str, str); project_requested = Signal(dict); translation_requested = Signal(object); update_requested = Signal(dict)
    def __init__(self, config, import_manager, project_manager, loadout_manager, service) -> None:
        super().__init__(); self.config = config; self.imports = import_manager; self.projects = project_manager; self.loadouts = loadout_manager; self.service = service; self.state_cache = {}
        self.setWidgetResizable(True); self.setFrameShape(QFrame.Shape.NoFrame); self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(objectName="pageSurface"); root = QVBoxLayout(content); root.setContentsMargins(22, 16, 22, 16); root.setSpacing(11); root.addWidget(PageHeader(t("library.title"), t("library.description")))
        toolbar = QFrame(objectName="formPanel"); tools = QGridLayout(toolbar); tools.setContentsMargins(14, 10, 14, 10); tools.setSpacing(8)
        self.search = QLineEdit(); self.search.setPlaceholderText(t("library.search")); self.search.textChanged.connect(self.refresh)
        self.filter = QComboBox(); self.filter.addItem(t("library.filter_all"), "all"); self.filter.addItem("Steam", "steam"); self.filter.addItem(t("library.filter_local"), "local"); self.filter.addItem(t("library.filter_translated"), "translated"); self.filter.addItem(t("library.filter_needs"), "needs"); self.filter.addItem(t("library.filter_project"), "project"); self.filter.currentIndexChanged.connect(self.refresh)
        self.sort = QComboBox(); self.sort.addItem(t("library.sort_name"), "name"); self.sort.addItem(t("library.sort_modified"), "modified"); self.sort.addItem("Workshop ID", "workshop"); self.sort.addItem(t("library.sort_order"), "order"); self.sort.currentIndexChanged.connect(self.refresh)
        tools.addWidget(self.search, 0, 0, 1, 2); tools.addWidget(self.filter, 1, 0); tools.addWidget(self.sort, 1, 1); root.addWidget(toolbar)
        self.table = QTableWidget(0, 9); self.table.setHorizontalHeaderLabels([t("library.enabled"), t("library.order"), t("mod_import.name"), t("mod_import.type"), "Workshop ID", "Localization", t("library.project"), t("library.translation"), t("library.actions")]); self.table.verticalHeader().hide(); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.horizontalHeader().setStretchLastSection(True); self.table.setMinimumHeight(300); self.table.setMinimumWidth(0); root.addWidget(self.table, 1)
        self.summary = QLabel(objectName="mutedText"); root.addWidget(self.summary)
        loadout = QFrame(objectName="formPanel"); row = QGridLayout(loadout); row.setContentsMargins(14, 10, 14, 10); row.setSpacing(7); row.addWidget(QLabel(t("library.loadout"), objectName="panelTitle"), 0, 0); self.loadout_combo = QComboBox(); self.loadout_combo.currentIndexChanged.connect(self._select_loadout); row.addWidget(self.loadout_combo, 0, 1, 1, 4)
        for column, (label, slot, style) in enumerate(((t("library.new"), self._new_loadout, "burgundyButton"), (t("common.save"), self._save_loadout, ""), (t("projects.delete"), self._delete_loadout, "secondaryButton"), (t("library.import"), self._import_loadout, "secondaryButton"), (t("library.export"), self._export_loadout, "secondaryButton"))):
            button = QPushButton(label, objectName=style); button.clicked.connect(slot); row.addWidget(button, 1, column)
        root.addWidget(loadout); warning = QLabel(t("library.internal_warning"), objectName="mutedText"); warning.setWordWrap(True); root.addWidget(warning); self.setWidget(content)
        self.imports.changed.connect(self._source_changed); self.projects.changed.connect(self.refresh); self.loadouts.changed.connect(self._loadouts_changed); self._refresh_loadouts(); self._reset_states(); self.refresh()

    def _source_changed(self): self._reset_states(); self.refresh()
    def _loadouts_changed(self): self._refresh_loadouts(); self._reset_states(); self.refresh()
    def _refresh_loadouts(self):
        current = self.loadouts.active_id; self.loadout_combo.blockSignals(True); self.loadout_combo.clear(); self.loadout_combo.addItem(t("library.no_loadout"), "")
        for item in self.loadouts.loadouts: self.loadout_combo.addItem(str(item.get("name", "Loadout")), str(item.get("id", "")))
        index = self.loadout_combo.findData(current); self.loadout_combo.setCurrentIndex(max(0, index)); self.loadout_combo.blockSignals(False)
    def _reset_states(self):
        self.state_cache = {entry.id: list(self.loadouts.state_for(entry.id, entry.enabled, entry.load_order_position)) for entry in self.imports.entries}

    def _entries(self):
        query = self.search.text().strip().casefold(); mode = self.filter.currentData(); values = []
        for entry in self.imports.entries:
            state = self.service.state(entry)
            if query and query not in f"{entry.name} {entry.workshop_id} {entry.path or ''}".casefold(): continue
            if mode == "steam" and entry.source is not ModSource.STEAM_WORKSHOP: continue
            if mode == "local" and entry.source is ModSource.STEAM_WORKSHOP: continue
            if mode == "translated" and not state.translation_exists: continue
            if mode == "needs" and not state.update_needed: continue
            if mode == "project" and not state.project: continue
            values.append((entry, state))
        sort = self.sort.currentData()
        key = {"modified": lambda pair: -(pair[0].modified_time or 0), "workshop": lambda pair: pair[0].workshop_id, "order": lambda pair: self.state_cache.get(pair[0].id, [True, 0])[1], "name": lambda pair: pair[0].name.casefold()}[sort]
        return sorted(values, key=key)

    def refresh(self):
        values = self._entries(); self.table.setRowCount(len(values)); source_names = {ModSource.STEAM_WORKSHOP: "Steam", ModSource.PARADOX_LAUNCHER: "Paradox", ModSource.JSON_IMPORT: "JSON", ModSource.MANUAL: t("mod_import.source_manual")}
        active = bool(self.loadouts.active())
        for row, (entry, state) in enumerate(values):
            enabled, order = self.state_cache.setdefault(entry.id, list(self.loadouts.state_for(entry.id, entry.enabled, entry.load_order_position)))
            check = QCheckBox(); check.setChecked(bool(enabled)); check.setEnabled(active); check.toggled.connect(lambda value, key=entry.id: self._set_enabled(key, value)); self.table.setCellWidget(row, 0, check)
            spin = QSpinBox(); spin.setRange(0, 9999); spin.setValue(int(order)); spin.setEnabled(active); spin.valueChanged.connect(lambda value, key=entry.id: self._set_order(key, value)); self.table.setCellWidget(row, 1, spin)
            target_names = ", ".join(path.name for path in entry.localization_paths) or "—"; project_name = str(state.project.get("name")) if state.project else t("library.not_linked"); translation = t("library.update_needed") if state.update_needed else (t("library.translated") if state.translation_exists else t("library.translation_needed"))
            for column, text in enumerate((entry.name, source_names.get(entry.source, entry.source.value), entry.workshop_id or "—", target_names, project_name, translation), start=2): self.table.setItem(row, column, QTableWidgetItem(text))
            actions = QWidget(); action_row = QHBoxLayout(actions); action_row.setContentsMargins(2, 2, 2, 2); action_row.setSpacing(3)
            for label, slot in ((t("library.project_action"), lambda checked=False, e=entry, s=state: self._project(e, s.project)), (t("library.translate_action"), lambda checked=False, e=entry: self.translation_requested.emit(e)), (t("library.update_action"), lambda checked=False, p=state.project: self.update_requested.emit(p) if p else None), (t("library.folder_action"), lambda checked=False, e=entry: self._open_folder(e))):
                button = QPushButton(label, objectName="linkButton"); button.clicked.connect(slot); action_row.addWidget(button)
            self.table.setCellWidget(row, 8, actions); self.table.setRowHeight(row, 42)
        self.summary.setText(t("library.summary", shown=len(values), total=len(self.imports.entries)))

    def _set_enabled(self, key, value): self.state_cache.setdefault(key, [True, 0])[0] = value
    def _set_order(self, key, value): self.state_cache.setdefault(key, [True, 0])[1] = value
    def _select_loadout(self):
        identifier = str(self.loadout_combo.currentData() or "")
        if identifier: self.loadouts.select(identifier)
        else: self.config.update(active_loadout_id=""); self._reset_states(); self.refresh()
    def _new_loadout(self):
        name, ok = QInputDialog.getText(self, t("library.new"), t("library.loadout_name"));
        if ok and name.strip(): self.loadouts.create(name)
    def _save_loadout(self):
        active = self.loadouts.active()
        if not active: QMessageBox.information(self, t("library.loadout"), t("library.create_first")); return
        states = [{"mod_id": entry.id, "enabled": bool(self.state_cache.get(entry.id, [True, 0])[0]), "position": int(self.state_cache.get(entry.id, [True, 0])[1])} for entry in self.imports.entries]
        self.loadouts.save(str(active["id"]), states); self.status_changed.emit(t("common.saved"), "ready")
    def _delete_loadout(self):
        active = self.loadouts.active()
        if active and QMessageBox.question(self, t("projects.delete"), t("library.delete_question")) == QMessageBox.StandardButton.Yes: self.loadouts.remove(str(active["id"]))
    def _export_loadout(self):
        if not self.loadouts.active(): QMessageBox.information(self, t("library.loadout"), t("library.create_first")); return
        value, _ = QFileDialog.getSaveFileName(self, t("library.export"), str(self.config.data.get("last_loadout_path", "")) or "V3MM_Loadout.json", "JSON (*.json)")
        if value:
            try:
                path = Path(value if value.lower().endswith(".json") else value + ".json"); self.loadouts.export_file(path); self.config.update(last_loadout_path=str(path)); self.status_changed.emit(t("library.exported"), "ready")
            except Exception as error: show_operation_error(self, t("library.export"), error)
    def _import_loadout(self):
        value, _ = QFileDialog.getOpenFileName(self, t("library.import"), str(self.config.data.get("last_loadout_path", "")), "JSON (*.json)")
        if value:
            try: self.loadouts.import_file(Path(value)); self.status_changed.emit(t("library.imported"), "ready")
            except Exception as error: show_operation_error(self, t("library.import"), error)
    def _project(self, entry, project):
        if project: self.project_requested.emit(project); return
        projects = self.projects.projects
        if not projects: QMessageBox.information(self, t("library.project"), t("projects.empty")); return
        names = [str(item.get("name", "Project")) for item in projects]; name, ok = QInputDialog.getItem(self, t("library.project"), t("library.select_project"), names, 0, False)
        if ok: self.service.link_project(entry, str(projects[names.index(name)].get("id", "")))
    def _open_folder(self, entry):
        if entry.path and entry.path.exists(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(entry.path)))
