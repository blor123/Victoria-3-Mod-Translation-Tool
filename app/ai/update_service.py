import shutil
from datetime import datetime
from pathlib import Path

from app.ai.localization_parser import parse_sources
from app.i18n.language_definition import target_language
from app.snapshots import SnapshotManager,capture_localization,compare_snapshot
from app.utils.paths import user_data_dir


class AIUpdateService:
    def __init__(self,translation_service,snapshots=None): self.translation=translation_service; self.snapshots=snapshots or SnapshotManager()
    def analyze(self,project):
        current=capture_localization(Path(project.get('localization_path') or project.get('source_path',''))); previous=self.snapshots.latest(project['id'])
        return (compare_snapshot(previous,current),False) if previous else (None,True)
    def update(self,project,progress=None,wait=None):
        source=Path(project.get('localization_path') or project.get('source_path','')); install_value=str(project.get('install_path','')).strip()
        if not source.exists(): raise ValueError('Project source localization path does not exist.')
        if not install_value: raise ValueError('Project install path is not configured.')
        install=Path(install_value)
        language=target_language(str(project.get('target_language') or 'ko-KR')); previous=self.snapshots.latest(project['id']); current=capture_localization(source)
        if previous:
            diff=compare_snapshot(previous,current); wanted={item.key for item in diff.translatable}
        else:
            existing_keys={e.key for d in parse_sources([install]) for e in d.entries} if install.exists() else set(); wanted={item['key'] for item in current['entries'] if item['key'] not in existing_keys}
        items=[{'id':item['key'],'text':item['value']} for item in current['entries'] if item['key'] in wanted]
        session=self.translation.translate_items(items,language.prompt_name,progress,wait)
        documents=parse_sources([install]) if install.exists() else []; by_key={e.key:(doc,e) for doc in documents for e in doc.entries}; touched=set(); backup=user_data_dir()/'backups'/str(project['id'])/datetime.now().strftime('%Y%m%d_%H%M%S')
        for key,value in session.translations.items():
            if key in by_key:touched.add(by_key[key][0].path)
        for doc in documents:
            changes={e.entry_id:session.translations[e.key] for e in doc.entries if e.key in session.translations}
            if not changes:continue
            relative=doc.path.relative_to(install); target=install/relative; saved=backup/relative; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,saved); target.write_text(doc.render(changes),encoding='utf-8')
        missing={k:v for k,v in session.translations.items() if k not in by_key}
        if missing:
            target=install/'localization'/language.filename_suffix/f'v3mm_api_update_l_{language.filename_suffix}.yml'; target.parent.mkdir(parents=True,exist_ok=True)
            lines=[language.localization_header]+[f' {key}:0 "{value.replace(chr(34),chr(92)+chr(34))}"' for key,value in missing.items()]; target.write_text('\ufeff'+'\n'.join(lines)+'\n',encoding='utf-8')
        self.snapshots.save(project,language,source); return session,len(wanted),backup
