from PySide6.QtCore import QObject,QThread,Signal
from PySide6.QtWidgets import QComboBox,QFrame,QHBoxLayout,QLabel,QMessageBox,QProgressBar,QPushButton,QVBoxLayout,QWidget

from app.ai import AITranslationService,CredentialStore
from app.ai.providers import GeminiProvider
from app.ai.update_service import AIUpdateService
from app.gui.widgets.page_header import PageHeader
from app.i18n import t


class UpdateWorker(QObject):
    progress=Signal(int,int,int,int);finished=Signal(object,int,object);failed=Signal(str)
    def __init__(self,service,project):super().__init__();self.service=service;self.project=project
    def run(self):
        try:self.finished.emit(*self.service.update(self.project,lambda *v:self.progress.emit(*v)))
        except Exception as error:self.failed.emit(str(error))


class AIUpdatePage(QWidget):
    status_changed=Signal(str,str);activity_completed=Signal(str,str,str)
    def __init__(self,config,projects):
        super().__init__();self.config=config;self.projects=projects;self.store=CredentialStore();self.service=None;self.setObjectName('pageSurface');root=QVBoxLayout(self);root.setContentsMargins(28,22,28,22);root.addWidget(PageHeader(t('ai.update.title'),t('ai.update.description')));panel=QFrame(objectName='panel');layout=QVBoxLayout(panel);layout.addWidget(QLabel(t('projects.title')));self.project=QComboBox();layout.addWidget(self.project);self.analysis=QLabel('',objectName='mutedText');self.analysis.setWordWrap(True);layout.addWidget(self.analysis);self.progress=QProgressBar();self.progress.hide();layout.addWidget(self.progress);row=QHBoxLayout();self.check=QPushButton(t('diff.check_changes'));self.start=QPushButton(t('ai.update.start'),objectName='burgundyButton');self.cancel=QPushButton(t('ai.cancel'),objectName='secondaryButton');self.cancel.setEnabled(False);row.addWidget(self.check);row.addWidget(self.start);row.addWidget(self.cancel);layout.addLayout(row);root.addWidget(panel);root.addStretch();self.check.clicked.connect(self._check);self.start.clicked.connect(self._start);self.cancel.clicked.connect(self._cancel);projects.changed.connect(self.refresh);self.refresh()
    def refresh(self):
        selected=self.project.currentData();self.project.clear()
        for item in self.projects.projects:self.project.addItem(str(item.get('name','')),item.get('id'))
        index=self.project.findData(selected)
        if index>=0:self.project.setCurrentIndex(index)
    def set_project(self,project):
        index=self.project.findData(project.get('id'))
        if index>=0:self.project.setCurrentIndex(index)
    def _selected(self):return next((p for p in self.projects.projects if p.get('id')==self.project.currentData()),None)
    def _check(self):
        project=self._selected()
        if not project:return
        dummy=AIUpdateService(None);diff,legacy=dummy.analyze(project)
        if legacy:self.analysis.setText(t('ai.update.legacy'))
        else:
            counts=diff.counts;self.analysis.setText(t('ai.update.counts',new=counts['NEW'],changed=counts['CHANGED'],deleted=counts['DELETED'],unchanged=counts['UNCHANGED']))
    def _start(self):
        project=self._selected();key=self.store.get()
        if not project:return
        if not key:QMessageBox.information(self,t('ai.update.title'),t('ai.status.missing'));return
        provider=GeminiProvider(key,str(self.config.data.get('ai_model','gemini-3.8-flash')));retries=self.config.data.get('ai_max_retries',3) if self.config.data.get('ai_retry_enabled',True) else 0;translation=AITranslationService(provider,self.config.data.get('ai_batch_size',40),retries);self.service=AIUpdateService(translation);self.start.setEnabled(False);self.cancel.setEnabled(True);self.progress.show();thread=QThread(self);worker=UpdateWorker(self.service,project);worker.moveToThread(thread);thread.started.connect(worker.run);worker.progress.connect(self._progress);worker.finished.connect(self._done);worker.failed.connect(self._failed);worker.finished.connect(thread.quit);worker.failed.connect(thread.quit);thread.finished.connect(worker.deleteLater);thread.finished.connect(thread.deleteLater);self.thread=thread;self.worker=worker;thread.start()
    def _progress(self,done,total,batch,batches):self.progress.setMaximum(max(1,total));self.progress.setValue(done);self.analysis.setText(t('ai.progress',done=done,total=total,batch=batch,batches=batches))
    def _done(self,session,count,backup):self.start.setEnabled(True);self.cancel.setEnabled(False);self.analysis.setText(t('ai.update.completed',count=count));self.activity_completed.emit(str(self.project.currentText()),'api_update','completed')
    def _failed(self,error):self.start.setEnabled(True);self.cancel.setEnabled(False);self.analysis.setText(error);self.status_changed.emit(t('common.error'),'error')
    def _cancel(self):
        if self.service:self.service.translation.cancel();self.cancel.setEnabled(False)
