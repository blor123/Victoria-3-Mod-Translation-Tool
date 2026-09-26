from pathlib import Path
from PySide6.QtCore import QObject,QThread,Signal
from PySide6.QtWidgets import QComboBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QProgressBar,QPushButton,QVBoxLayout,QWidget

from app.ai import AITranslationService,CredentialStore
from app.ai.providers import GeminiProvider
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.i18n.language_definition import LANGUAGES
from app.utils.paths import user_data_dir
from datetime import datetime


class TranslationWorker(QObject):
    progress=Signal(int,int,int,int);finished=Signal(object);failed=Signal(str)
    def __init__(self,service,source,target,output):super().__init__();self.service=service;self.source=source;self.target=target;self.output=output
    def run(self):
        try:self.finished.emit(self.service.translate([self.source],self.target,self.output,lambda *v:self.progress.emit(*v)))
        except Exception as error:self.failed.emit(str(error))


class AITranslationPage(QWidget):
    status_changed=Signal(str,str);activity_completed=Signal(str,str,str)
    def __init__(self,config):
        super().__init__();self.config=config;self.store=CredentialStore();self.thread=None;self.service=None;self.setObjectName('pageSurface');root=QVBoxLayout(self);root.setContentsMargins(28,22,28,22);root.addWidget(PageHeader(t('ai.translation.title'),t('ai.translation.description')))
        panel=QFrame(objectName='panel');layout=QVBoxLayout(panel);self.source=QLineEdit(str(config.data.get('last_ai_source_path','')));self.output=QLineEdit(str(config.data.get('last_ai_output_path','')));self.install=QLineEdit(str(config.data.get('last_ai_install_path','')));layout.addWidget(QLabel(t('ai.source')));layout.addLayout(self._path_row(self.source,self._source));layout.addWidget(QLabel(t('ai.output')));layout.addLayout(self._path_row(self.output,self._output));layout.addWidget(QLabel(t('ai.install')));layout.addLayout(self._path_row(self.install,self._install));layout.addWidget(QLabel(t('ai.target')));self.target=QComboBox()
        for code,definition in LANGUAGES.items():self.target.addItem(definition.display_name,code)
        layout.addWidget(self.target);self.summary=QLabel('',objectName='mutedText');layout.addWidget(self.summary);self.progress=QProgressBar();self.progress.hide();layout.addWidget(self.progress);buttons=QHBoxLayout();self.start=QPushButton(t('ai.translation.start'),objectName='burgundyButton');self.apply=QPushButton(t('ai.apply'));self.apply.setEnabled(False);self.cancel=QPushButton(t('ai.cancel'),objectName='secondaryButton');self.cancel.setEnabled(False);buttons.addWidget(self.start);buttons.addWidget(self.apply);buttons.addWidget(self.cancel);layout.addLayout(buttons);root.addWidget(panel);root.addStretch();self.start.clicked.connect(self._start);self.apply.clicked.connect(self._apply);self.cancel.clicked.connect(self._cancel)
    def _path_row(self,line,slot):
        row=QHBoxLayout();row.addWidget(line,1);button=QPushButton(t('common.browse'));button.clicked.connect(slot);row.addWidget(button);return row
    def _source(self):
        path=QFileDialog.getExistingDirectory(self,t('ai.source'),self.source.text())
        if path:self.source.setText(path)
    def _output(self):
        path=QFileDialog.getExistingDirectory(self,t('ai.output'),self.output.text())
        if path:self.output.setText(path)
    def _install(self):
        path=QFileDialog.getExistingDirectory(self,t('ai.install'),self.install.text())
        if path:self.install.setText(path);self.config.update(last_ai_install_path=path)
    def set_source(self,path):self.source.setText(str(path))
    def _start(self):
        source=Path(self.source.text());output=Path(self.output.text());key=self.store.get()
        if not key:QMessageBox.information(self,t('ai.translation.title'),t('ai.status.missing'));return
        if not source.exists() or not self.output.text():QMessageBox.warning(self,t('common.error'),t('ai.paths.required'));return
        definition=LANGUAGES[self.target.currentData()];provider=GeminiProvider(key,str(self.config.data.get('ai_model','gemini-3.8-flash')));retries=self.config.data.get('ai_max_retries',3) if self.config.data.get('ai_retry_enabled',True) else 0;self.service=AITranslationService(provider,self.config.data.get('ai_batch_size',40),retries);self.config.update(last_ai_source_path=str(source),last_ai_output_path=str(output));self.start.setEnabled(False);self.cancel.setEnabled(True);self.progress.show();self.progress.setValue(0)
        thread=QThread(self);worker=TranslationWorker(self.service,source,definition,output);worker.moveToThread(thread);thread.started.connect(worker.run);worker.progress.connect(self._progress);worker.finished.connect(self._done);worker.failed.connect(self._failed);worker.finished.connect(thread.quit);worker.failed.connect(thread.quit);thread.finished.connect(worker.deleteLater);thread.finished.connect(thread.deleteLater);self.thread=thread;self.worker=worker;thread.start()
    def _progress(self,done,total,batch,total_batches):self.progress.setMaximum(max(1,total));self.progress.setValue(done);self.summary.setText(t('ai.progress',done=done,total=total,batch=batch,batches=total_batches))
    def _done(self,session):self.start.setEnabled(True);self.cancel.setEnabled(False);self.apply.setEnabled(bool(session.succeeded and self.install.text()));self.summary.setText(t('ai.completed',success=session.succeeded,failed=len(session.failed_batches)));self.activity_completed.emit(self.output.text(),'api_translation','completed')
    def _failed(self,error):self.start.setEnabled(True);self.cancel.setEnabled(False);self.summary.setText(error);self.status_changed.emit(t('common.error'),'error')
    def _cancel(self):
        if self.service:self.service.cancel();self.cancel.setEnabled(False)
    def _apply(self):
        if not self.install.text().strip(): return
        destination=Path(self.install.text())
        try:
            backup=user_data_dir()/'backups'/'api_translation'/datetime.now().strftime('%Y%m%d_%H%M%S');count=AITranslationService.apply_preview(Path(self.output.text()),destination,backup);self.config.update(last_ai_install_path=str(destination));self.summary.setText(t('ai.applied',count=count));self.apply.setEnabled(False)
        except Exception as error:QMessageBox.warning(self,t('common.error'),str(error))
