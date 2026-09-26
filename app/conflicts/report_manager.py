import json
from pathlib import Path
from app.conflicts.models import ConflictReport


class ConflictReportManager:
    def save(self,report:ConflictReport,path:Path)->Path:
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(json.dumps(report.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8'); temporary.replace(path); return path
    def load(self,path:Path)->ConflictReport:
        data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if data.get('format')!='v3mm_conflict_report':raise ValueError('Unsupported conflict report format.')
        return ConflictReport.from_dict(data)
    def is_stale(self,report:ConflictReport)->bool:
        try:return any(not mod.root_path.exists() or any(p.stat().st_mtime>Path(mod.root_path).stat().st_mtime for p in mod.root_path.rglob('*') if p.is_file()) for mod in report.mods)
        except OSError:return True
