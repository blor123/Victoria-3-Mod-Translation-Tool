from PySide6.QtCore import QObject,QThread,Signal
from PySide6.QtWidgets import QCheckBox,QComboBox,QFrame,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QPushButton,QSpinBox,QVBoxLayout,QWidget

from app.ai.credential_store import CredentialStore
from app.ai.providers.gemini_provider import GeminiProvider
from app.gui.widgets.page_header import PageHeader
from app.i18n import t


class ConnectionWorker(QObject):
    finished=Signal(bool,object); failed=Signal(str)
    def __init__(self,key,model):super().__init__();self.key=key;self.model=model
    def run(self):
        try:
            provider=GeminiProvider(self.key,self.model); models=provider.get_available_models()
            legacy_model=provider.model.startswith('gemini-2.')
            if models and (provider.model not in models or legacy_model):
                preferred=('gemini-3.8-flash','gemini-3.5-flash','gemini-3.1-flash-lite')
                provider.model=next((name for name in preferred if name in models),models[0]);models=[provider.model]+[name for name in models if name!=provider.model]
            ok=provider.test_connection(); self.finished.emit(ok,models)
        except Exception as error:self.failed.emit(str(error))


class AISettingsPage(QWidget):
    status_changed=Signal(str,str)
    def __init__(self,config,store=None):
        super().__init__();self.config=config;self.store=store or CredentialStore();self.thread=None;self.setObjectName('pageSurface')
        root=QVBoxLayout(self);root.setContentsMargins(28,22,28,22);root.addWidget(PageHeader(t('ai.settings.title'),t('ai.settings.description')))
        panel=QFrame(objectName='panel');form=QVBoxLayout(panel);form.addWidget(QLabel(t('ai.provider')));form.addWidget(QLabel('Google Gemini',objectName='panelTitle'));form.addWidget(QLabel(t('ai.key')))
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);self.key.setPlaceholderText('••••••••••••••••');form.addWidget(self.key)
        row=QHBoxLayout();self.save=QPushButton(t('ai.key.save'),objectName='burgundyButton');self.test=QPushButton(t('ai.test'));self.delete=QPushButton(t('ai.key.delete'),objectName='secondaryButton');row.addWidget(self.save);row.addWidget(self.test);row.addWidget(self.delete);form.addLayout(row)
        form.addWidget(QLabel(t('ai.model')));self.model=QComboBox();self.model.setEditable(True);self.model.addItem(str(config.data.get('ai_model','gemini-3.8-flash')));form.addWidget(self.model)
        advanced=QHBoxLayout();self.retry=QCheckBox(t('ai.retry'));self.retry.setChecked(bool(config.data.get('ai_retry_enabled',True)));self.batch=QSpinBox();self.batch.setRange(1,200);self.batch.setValue(int(config.data.get('ai_batch_size',40)));advanced.addWidget(self.retry);advanced.addWidget(QLabel(t('ai.batch')));advanced.addWidget(self.batch);form.addLayout(advanced)
        self.state=QLabel(t('ai.status.saved') if self.store.exists() else t('ai.status.missing'),objectName='mutedText');form.addWidget(self.state);root.addWidget(panel);root.addStretch()
        self.save.clicked.connect(self._save);self.delete.clicked.connect(self._delete);self.test.clicked.connect(self._test);self.model.currentTextChanged.connect(lambda value:self.config.update(ai_model=value));self.retry.toggled.connect(lambda value:self.config.update(ai_retry_enabled=value));self.batch.valueChanged.connect(lambda value:self.config.update(ai_batch_size=value))
    def _save(self):
        try:self.store.set(self.key.text().strip());self.key.clear();self.state.setText(t('ai.status.saved'));self.status_changed.emit(t('common.saved'),'ready')
        except Exception as error:QMessageBox.warning(self,t('common.error'),str(error))
    def _delete(self):
        try:self.store.delete();self.key.clear();self.state.setText(t('ai.status.missing'))
        except Exception as error:QMessageBox.warning(self,t('common.error'),str(error))
    def _test(self):
        key=self.key.text().strip() or self.store.get()
        if not key:QMessageBox.information(self,t('ai.settings.title'),t('ai.status.missing'));return
        self.test.setEnabled(False);self.state.setText(t('ai.testing'));thread=QThread(self);worker=ConnectionWorker(key,self.model.currentText());worker.moveToThread(thread);thread.started.connect(worker.run);worker.finished.connect(self._tested);worker.failed.connect(self._failed);worker.finished.connect(thread.quit);worker.failed.connect(thread.quit);thread.finished.connect(worker.deleteLater);thread.finished.connect(thread.deleteLater);self.thread=thread;self.worker=worker;thread.start()
    def _tested(self,ok,models):
        self.test.setEnabled(True);self.state.setText(t('ai.status.available') if ok else t('ai.status.failed'));current=self.model.currentText();self.model.clear();self.model.addItems(models or [current]);self.model.setCurrentText(current if current in models else (models[0] if models else current))
    def _failed(self,error):self.test.setEnabled(True);self.state.setText(t('ai.status.failed'));QMessageBox.warning(self,t('common.error'),error)
