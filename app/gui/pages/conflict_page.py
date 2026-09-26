from pathlib import Path
from PySide6.QtCore import QObject,QThread,Qt,Signal
from PySide6.QtWidgets import QAbstractItemView,QComboBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QLineEdit,QListWidget,QMessageBox,QProgressBar,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget

from app.ai import ConflictAIService,CredentialStore
from app.ai.providers import GeminiProvider
from app.conflicts import ConflictAnalyzer,ConflictMod,ConflictReportManager
from app.gui.conflict_diff_dialog import ConflictDiffDialog
from app.gui.widgets.page_header import PageHeader
from app.i18n import t
from app.utils.paths import user_data_dir


class ConflictWorker(QObject):
    progress=Signal(str,int,int);finished=Signal(object);failed=Signal(str)
    def __init__(self,mods):super().__init__();self.mods=mods;self.cancelled=False
    def run(self):
        try:self.finished.emit(ConflictAnalyzer().analyze(self.mods,lambda *v:self.progress.emit(*v),lambda:self.cancelled))
        except Exception as error:self.failed.emit(str(error))


class ConflictAIWorker(QObject):
    progress=Signal(int,int);finished=Signal(object);failed=Signal(str)
    def __init__(self,service,conflicts):super().__init__();self.service=service;self.conflicts=conflicts
    def run(self):
        try:
            results=[]
            for index,conflict in enumerate(self.conflicts,1):result=self.service.analyze(conflict);conflict.ai_result=result;results.append(result);self.progress.emit(index,len(self.conflicts))
            self.finished.emit(results)
        except Exception as error:self.failed.emit(str(error))


class ConflictPage(QWidget):
    status_changed=Signal(str,str);activity_completed=Signal(str,str,str)
    def __init__(self,config,projects):
        super().__init__();self.config=config;self.projects=projects;self.mods=[];self.report=None;self.filtered=[];self.store=CredentialStore();self.setObjectName('pageSurface');root=QVBoxLayout(self);root.setContentsMargins(28,18,28,18);root.setSpacing(9);root.addWidget(PageHeader(t('conflict.title'),t('conflict.description')))
        controls=QHBoxLayout();add=QPushButton(t('conflict.add_folder'));add.clicked.connect(self._add);project=QPushButton(t('conflict.add_project'));project.clicked.connect(self._project);clear=QPushButton(t('common.clear'),objectName='secondaryButton');clear.clicked.connect(self._clear);controls.addWidget(add);controls.addWidget(project);controls.addWidget(clear);controls.addStretch();root.addLayout(controls);self.mod_list=QListWidget();self.mod_list.setMaximumHeight(90);root.addWidget(self.mod_list)
        runrow=QHBoxLayout();self.analyze=QPushButton(t('conflict.analyze'),objectName='burgundyButton');self.analyze.clicked.connect(self._analyze);self.cancel=QPushButton(t('ai.cancel'),objectName='secondaryButton');self.cancel.setEnabled(False);self.cancel.clicked.connect(self._cancel);self.progress=QProgressBar();runrow.addWidget(self.analyze);runrow.addWidget(self.cancel);runrow.addWidget(self.progress,1);root.addLayout(runrow);self.summary=QLabel(t('conflict.minimum'),objectName='mutedText');root.addWidget(self.summary)
        filters=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText(t('conflict.search'));self.filter=QComboBox();[(self.filter.addItem(t(f'conflict.filter.{key}'),key)) for key in ('all','file','definition','localization','replace_path','parser','ai')];filters.addWidget(self.search,1);filters.addWidget(self.filter);root.addLayout(filters);self.search.textChanged.connect(self._refresh);self.filter.currentIndexChanged.connect(self._refresh)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels([t('conflict.severity'),t('conflict.category'),t('conflict.subject'),t('conflict.mods'),t('conflict.reason')]);self.table.horizontalHeader().setStretchLastSection(True);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.table.itemDoubleClicked.connect(lambda:self._diff());root.addWidget(self.table,1)
        actions=QHBoxLayout();self.diff=QPushButton(t('conflict.diff'));self.ai=QPushButton(t('conflict.ai'));self.export=QPushButton(t('conflict.report.save'));self.diff.clicked.connect(self._diff);self.ai.clicked.connect(self._ai);self.export.clicked.connect(self._export);actions.addWidget(self.diff);actions.addWidget(self.ai);actions.addWidget(self.export);actions.addStretch();root.addLayout(actions)
    def _add(self):
        path=QFileDialog.getExistingDirectory(self,t('conflict.add_folder'),str(self.config.data.get('last_conflict_path','')))
        if path:self._append(ConflictMod.from_folder(path));self.config.update(last_conflict_path=path)
    def _project(self):
        if not self.projects.projects:return
        names=[p.get('name','') for p in self.projects.projects];name,_=__import__('PySide6.QtWidgets',fromlist=['QInputDialog']).QInputDialog.getItem(self,t('projects.title'),t('projects.title'),names,0,False)
        project=next((p for p in self.projects.projects if p.get('name')==name),None)
        if project:self._append(ConflictMod.from_folder(project.get('source_path',''),project.get('id','')))
    def _append(self,mod):
        if mod.root_path.exists() and all(existing.root_path!=mod.root_path for existing in self.mods):self.mods.append(mod);self.mod_list.addItem(f"{mod.display_name} — {mod.root_path}")
    def _clear(self):self.mods=[];self.mod_list.clear();self.report=None;self.table.setRowCount(0)
    def _analyze(self):
        if len(self.mods)<2:QMessageBox.information(self,t('conflict.title'),t('conflict.minimum'));return
        self.analyze.setEnabled(False);self.cancel.setEnabled(True);thread=QThread(self);worker=ConflictWorker(list(self.mods));worker.moveToThread(thread);thread.started.connect(worker.run);worker.progress.connect(self._progress);worker.finished.connect(self._done);worker.failed.connect(self._failed);worker.finished.connect(thread.quit);worker.failed.connect(thread.quit);thread.finished.connect(worker.deleteLater);thread.finished.connect(thread.deleteLater);self.thread=thread;self.worker=worker;thread.start()
    def _progress(self,stage,done,total):self.progress.setMaximum(max(1,total));self.progress.setValue(done);self.summary.setText(t('conflict.progress',stage=stage,done=done,total=total))
    def _done(self,report):self.report=report;self.analyze.setEnabled(True);self.cancel.setEnabled(False);s=report.summary();self.summary.setText(t('conflict.summary',mods=s['mods'],total=s['total']));self._refresh();self.activity_completed.emit(t('conflict.title'),'conflict_analysis','completed')
    def _failed(self,error):self.analyze.setEnabled(True);self.cancel.setEnabled(False);self.summary.setText(error)
    def _cancel(self):
        if hasattr(self,'worker'):self.worker.cancelled=True;self.cancel.setEnabled(False)
    def _refresh(self):
        if not self.report:return
        query=self.search.text().casefold();category=self.filter.currentData();self.filtered=[c for c in self.report.conflicts if (category=='all' or category=='ai' and c.ai_result or c.category==category) and query in f'{c.subject} {c.file_a} {c.file_b} {c.mod_a} {c.mod_b}'.casefold()];self.table.setRowCount(len(self.filtered))
        for row,c in enumerate(self.filtered):
            for col,value in enumerate((c.severity,c.category,c.subject,f'{c.mod_a} ↔ {c.mod_b}',c.reason)):self.table.setItem(row,col,QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
    def _selected(self):
        rows=sorted({index.row() for index in self.table.selectionModel().selectedRows()});return [self.filtered[row] for row in rows if row<len(self.filtered)]
    def _diff(self):
        selected=self._selected()
        if selected:ConflictDiffDialog(selected[0],self).exec()
    def _ai(self):
        selected=self._selected()
        if not selected:return
        key=self.store.get()
        if not key:QMessageBox.information(self,t('conflict.ai'),t('ai.status.missing'));return
        conflict=selected[0];preview=f"{len(selected)} conflict(s)\n{conflict.category}: {conflict.subject}\n{conflict.mod_a}: {len(conflict.snippet_a)} chars\n{conflict.mod_b}: {len(conflict.snippet_b)} chars\n\n{t('conflict.external_notice')}"
        if QMessageBox.question(self,t('conflict.ai.preview'),preview)!=QMessageBox.StandardButton.Yes:return
        try:
            provider=GeminiProvider(key,str(self.config.data.get('ai_model','gemini-3.8-flash')));retries=self.config.data.get('ai_max_retries',3) if self.config.data.get('ai_retry_enabled',True) else 0;service=ConflictAIService(provider,user_data_dir()/'ai_conflict_cache.json',retries);self.ai.setEnabled(False);thread=QThread(self);worker=ConflictAIWorker(service,selected);worker.moveToThread(thread);thread.started.connect(worker.run);worker.progress.connect(lambda done,total:self.summary.setText(t('ai.progress',done=done,total=total,batch=done,batches=total)));worker.finished.connect(self._ai_done);worker.failed.connect(self._ai_failed);worker.finished.connect(thread.quit);worker.failed.connect(thread.quit);thread.finished.connect(worker.deleteLater);thread.finished.connect(thread.deleteLater);self.ai_thread=thread;self.ai_worker=worker;thread.start()
        except Exception as error:QMessageBox.warning(self,t('common.error'),str(error))
    def _ai_done(self,results):self.ai.setEnabled(True);self._refresh();QMessageBox.information(self,t('conflict.ai'),results[0].get('summary','') if len(results)==1 else f'{len(results)} analysis complete')
    def _ai_failed(self,error):self.ai.setEnabled(True);QMessageBox.warning(self,t('common.error'),error)
    def _export(self):
        if not self.report:return
        path,_=QFileDialog.getSaveFileName(self,t('conflict.report.save'),'V3MM_Conflict_Report.json','JSON (*.json)')
        if path:ConflictReportManager().save(self.report,Path(path))
