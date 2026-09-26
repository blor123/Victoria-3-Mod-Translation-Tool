from pathlib import Path

from PySide6.QtWidgets import QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout

from app import DEFAULT_PROMPT_VERSION
from app.gui.dialogs import friendly_error
from app.i18n import t
from app.i18n.language_definition import target_language
from app.snapshots import SnapshotManager, capture_localization, compare_snapshot
from app.translation.incremental_builder import build_incremental_package
from app.projects import resolve_localization_path


class LocalizationChangesDialog(QDialog):
    def __init__(self, config, project, activities, parent=None) -> None:
        super().__init__(parent); self.config = config; self.project = project; self.activities = activities; self.manager = SnapshotManager(); self.diff = None; self.setWindowTitle(t("diff.title")); self.resize(780, 600)
        root = QVBoxLayout(self); self.summary = QLabel(); self.summary.setWordWrap(True); root.addWidget(self.summary)
        filters = QHBoxLayout(); self.filter = QComboBox()
        for status in ("ALL", "NEW", "CHANGED", "DELETED", "UNCHANGED"): self.filter.addItem(t(f"diff.{status.lower()}"), status)
        self.filter.currentIndexChanged.connect(self.refresh); filters.addWidget(self.filter); filters.addStretch(); root.addLayout(filters)
        self.list = QListWidget(); root.addWidget(self.list, 1)
        actions = QHBoxLayout(); baseline = QPushButton(t("diff.save_baseline"), objectName="secondaryButton"); baseline.clicked.connect(self.save_baseline); package = QPushButton(t("diff.build_incremental"), objectName="burgundyButton"); package.clicked.connect(self.build_package); actions.addWidget(baseline); actions.addStretch(); actions.addWidget(package); root.addLayout(actions); self.analyze()
    def _root(self): return resolve_localization_path(self.project, target_language(str(self.config.data.get("language", "ko-KR"))))
    def analyze(self):
        previous = self.manager.latest(self.project["id"])
        if not previous: self.summary.setText(t("diff.no_snapshot")); self.list.clear(); return
        try: self.diff = compare_snapshot(previous, capture_localization(self._root()))
        except Exception as error: self.summary.setText(f"⚠ {friendly_error(error)}"); return
        counts = self.diff.counts; self.summary.setText(t("diff.summary", new=counts["NEW"], changed=counts["CHANGED"], deleted=counts["DELETED"], unchanged=counts["UNCHANGED"])); self.refresh()
    def refresh(self):
        self.list.clear()
        if not self.diff: return
        wanted = self.filter.currentData()
        for item in self.diff.items:
            if wanted != "ALL" and item.status != wanted: continue
            detail = f"[{item.status}] {item.key}\n{item.new_value}"
            if item.status == "CHANGED": detail += f"\n{t('diff.previous')}: {item.old_value}"
            self.list.addItem(detail)
    def save_baseline(self):
        try:
            self.manager.save(self.project, target_language(str(self.config.data.get("language", "ko-KR"))), self._root()); self.activities.add("SNAPSHOT_SAVED", self.project.get("name", ""), self.project.get("id")); self.analyze()
        except Exception as error: QMessageBox.warning(self, t("diff.title"), friendly_error(error))
    def build_package(self):
        if not self.diff or not self.diff.translatable: QMessageBox.information(self, t("diff.title"), t("diff.no_changes")); return
        filename, _ = QFileDialog.getSaveFileName(self, t("diff.build_incremental"), f"{self.project.get('name', 'V3MM')}_incremental.zip", "ZIP (*.zip)")
        if not filename: return
        if not filename.lower().endswith(".zip"): filename += ".zip"
        try:
            report = build_incremental_package(self.diff, self._root(), Path(filename), target_language(str(self.config.data.get("language", "ko-KR"))), int(self.config.data.get("prompt_version", DEFAULT_PROMPT_VERSION))); self.activities.add("INCREMENTAL_PACKAGE_CREATED", self.project.get("name", ""), self.project.get("id"), metadata={"files": len(report.files), "path": filename}); QMessageBox.information(self, t("diff.title"), t("diff.package_complete", files=len(report.files), path=filename))
        except Exception as error: QMessageBox.warning(self, t("diff.title"), friendly_error(error))
