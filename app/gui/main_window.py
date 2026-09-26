from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QPoint, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app import APP_NAME, APP_VERSION
from app.activity import ActivityManager
from app.config.config_manager import ConfigManager
from app.gui.branding_header import BrandingHeader
from app.gui.notification_panel import NotificationPanel
from app.gui.toast_notification import ToastNotification
from app.gui.pages.about_page import AboutPage
from app.gui.pages.home_page import HomePage
from app.gui.pages.projects_page import ProjectsPage
from app.gui.pages.settings_page import SettingsPage
from app.gui.pages.tools_page import ToolsPage
from app.gui.pages.translation_apply_page import TranslationApplyPage
from app.gui.pages.translation_package_page import TranslationPackagePage
from app.gui.pages.quick_translation_page import QuickTranslationPage
from app.gui.pages.translation_update_page import TranslationUpdatePage
from app.gui.pages.ai_translation_page import AITranslationPage
from app.gui.pages.ai_update_page import AIUpdatePage
from app.gui.pages.ai_settings_page import AISettingsPage
from app.gui.pages.conflict_page import ConflictPage
from app.gui.sidebar import Sidebar
from app.gui.status_bar import AppStatusBar
from app.i18n import set_language, t
from app.projects import ProjectManager
from app.update.update_checker import check_for_update
from app.utils.paths import resource_path


class UpdateWorker(QObject):
    finished = Signal(object); failed = Signal(str)
    def run(self) -> None:
        try: self.finished.emit(check_for_update(APP_VERSION))
        except Exception as error: self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager) -> None:
        super().__init__(); self.config = config; self.activity_manager = ActivityManager(config); self.project_manager = ProjectManager(config); self.update_info = None; self._update_thread = None; self._closing = False
        requested = str(config.data.get("language", "ko-KR")); actual = set_language(requested)
        if actual != requested: config.update(language=actual)
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}"); self.setWindowIcon(QIcon(str(resource_path("resources/icons/app.ico"))))
        self.resize(1180, 760); self.setMinimumSize(1000, 650); self._build_ui(0); QTimer.singleShot(800, self._maybe_check_updates)

    def _build_ui(self, page_index: int) -> None:
        old = self.centralWidget(); root_widget = QWidget(objectName="appRoot"); root = QVBoxLayout(root_widget); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        self.header = BrandingHeader(); root.addWidget(self.header); body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0); self.sidebar = Sidebar(); self.stack = QStackedWidget()
        self.home_page = HomePage(self.activity_manager); self.quick_page = QuickTranslationPage(self.config); self.package_page = TranslationPackagePage(self.config); self.apply_page = TranslationApplyPage(self.config); self.translation_update_page = TranslationUpdatePage(self.config, self.project_manager); self.ai_translation_page = AITranslationPage(self.config); self.ai_update_page = AIUpdatePage(self.config, self.project_manager); self.ai_settings_page = AISettingsPage(self.config); self.projects_page = ProjectsPage(self.project_manager, self.activity_manager, self.config); self.conflict_page = ConflictPage(self.config, self.project_manager); self.tools_page = ToolsPage(); self.settings_page = SettingsPage(self.config); self.about_page = AboutPage()
        for page in (self.home_page, self.quick_page, self.package_page, self.apply_page, self.translation_update_page, self.ai_translation_page, self.ai_update_page, self.ai_settings_page, self.projects_page, self.conflict_page, self.tools_page, self.settings_page, self.about_page): self.stack.addWidget(page)
        body.addWidget(self.sidebar); body.addWidget(self.stack, 1); root.addLayout(body, 1); self.status_bar = AppStatusBar(); root.addWidget(self.status_bar); self.setCentralWidget(root_widget)
        if old: old.deleteLater()
        self.notifications = NotificationPanel(self.activity_manager, root_widget); self.toast = ToastNotification(root_widget); self._connect_signals(); self._refresh_badge(); self.navigate(page_index)
        if self.update_info: self.status_bar.set_update(self.update_info.version)

    def _connect_signals(self) -> None:
        self.sidebar.page_selected.connect(self.navigate); self.home_page.quick_requested.connect(lambda: self.navigate(1)); self.home_page.package_requested.connect(lambda: self.navigate(2)); self.home_page.apply_requested.connect(lambda: self.navigate(3))
        for page in (self.quick_page, self.package_page, self.apply_page, self.translation_update_page, self.ai_translation_page, self.ai_update_page, self.conflict_page): page.status_changed.connect(self.status_bar.set_status); page.activity_completed.connect(self._record_activity)
        self.ai_settings_page.status_changed.connect(self.status_bar.set_status)
        self.projects_page.package_requested.connect(self._project_package); self.projects_page.apply_requested.connect(self._project_apply)
        self.projects_page.ai_translation_requested.connect(self._project_ai_translation); self.projects_page.ai_update_requested.connect(self._project_ai_update)
        self.settings_page.settings_saved.connect(lambda: self.status_bar.set_status(t("common.saved"), "ready")); self.settings_page.language_changed.connect(self._change_language); self.settings_page.update_check_requested.connect(lambda: self._check_updates(True))
        self.header.notifications_requested.connect(self._toggle_notifications); self.activity_manager.changed.connect(self._refresh_badge); self.status_bar.update_clicked.connect(self._open_update)

    def _change_language(self, code: str) -> None: set_language(code); QTimer.singleShot(0, lambda: self._build_ui(11))
    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if self.sidebar.group.checkedId() != index: self.sidebar.buttons[index].setChecked(True)
        if index == 0: self.home_page.refresh_activities()
    def _record_activity(self, name: str, action: str, status: str) -> None:
        kinds = {"package":"PACKAGE_CREATED","api_translation":"API_TRANSLATION_COMPLETED","api_update":"API_UPDATE_COMPLETED","conflict_analysis":"CONFLICT_ANALYSIS_COMPLETED"}; kind=kinds.get(action,"TRANSLATION_APPLIED"); self.activity_manager.add(kind, name, metadata={"status": status}); self.toast.display(t(f"activity.{kind.lower()}"), name)
    def _project_package(self, project: dict) -> None: self.navigate(2); self.package_page.set_project(project)
    def _project_apply(self, project: dict) -> None: self.navigate(3); self.apply_page.set_project(project)
    def _project_ai_translation(self, project) -> None:
        self.navigate(5); self.ai_translation_page.set_source(project.get("localization_path") or project.get("source_path", ""))
    def _project_ai_update(self, project) -> None: self.navigate(6); self.ai_update_page.set_project(project)
    def _refresh_badge(self) -> None: self.header.set_badge(self.activity_manager.unread_count())
    def _toggle_notifications(self) -> None:
        if self.notifications.isVisible(): self.notifications.hide(); return
        self.notifications.show_panel(); self._position_notifications()
    def _position_notifications(self) -> None:
        anchor = self.header.notification_button.mapTo(self.centralWidget(), QPoint(0, self.header.notification_button.height()))
        gap = 7; x = anchor.x() + self.header.notification_button.width() - self.notifications.width(); y = anchor.y() + gap
        x = max(6, min(x, self.centralWidget().width() - self.notifications.width() - 6)); y = max(6, min(y, self.centralWidget().height() - self.notifications.height() - 6)); self.notifications.move(x, y); self.notifications.raise_()
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "notifications") and self.notifications.isVisible(): self._position_notifications()

    def closeEvent(self, event) -> None:
        self._closing = True
        super().closeEvent(event)

    def _maybe_check_updates(self) -> None:
        if not self.config.data.get("check_updates_on_startup", True): return
        try:
            if datetime.fromisoformat(str(self.config.data.get("last_update_check", ""))) > datetime.now() - timedelta(hours=24): return
        except ValueError: pass
        self._check_updates(False)
    def _check_updates(self, manual=False) -> None:
        if self._update_thread and self._update_thread.isRunning(): return
        self.status_bar.set_status(t("update.checking"), "busy"); thread = QThread(self); worker = UpdateWorker(); worker.moveToThread(thread); thread.started.connect(worker.run)
        worker.finished.connect(lambda info: self._update_finished(info, manual)); worker.failed.connect(lambda error: self._update_failed(error, manual)); worker.finished.connect(thread.quit); worker.failed.connect(thread.quit); thread.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater); self._update_thread = thread; self._update_worker = worker; thread.start()
    def _update_finished(self, info, manual) -> None:
        if self._closing: return
        self.config.update(last_update_check=datetime.now().isoformat(timespec="minutes")); self.update_info = info
        if info:
            self.status_bar.set_update(info.version); self.status_bar.set_status(t("update.available", version=info.version), "ready"); self.activity_manager.add("UPDATE_AVAILABLE", t("update.available", version=info.version), severity="info", metadata={"url": info.url}, dedupe_key=f"update-{info.version}")
        else: self.status_bar.set_status(t("update.none") if manual else t("common.ready"), "ready")
    def _update_failed(self, error: str, manual: bool) -> None:
        if self._closing: return
        self.status_bar.set_status(t("update.failed") if manual else t("common.ready"), "error" if manual else "ready")
    def _open_update(self) -> None:
        if self.update_info: QDesktopServices.openUrl(QUrl(self.update_info.url))
