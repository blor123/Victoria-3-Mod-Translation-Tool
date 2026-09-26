import shutil
import threading
from pathlib import Path

from app.ai.api_errors import AICancelled
from app.ai.batch_manager import BatchManager
from app.ai.localization_parser import parse_sources
from app.ai.rate_limit_manager import RateLimitManager
from app.ai.token_protector import TokenProtector
from app.ai.translation_session import TranslationSession
from app.i18n.language_definition import KNOWN_SUFFIXES
from app.translation.filename_converter import convert_localization_filename


class AITranslationService:
    def __init__(self, provider, batch_size=40, max_retries=3):
        self.provider=provider; self.batches=BatchManager(batch_size); self.limiter=RateLimitManager(max_retries); self.protector=TokenProtector(); self._cancel=threading.Event()
    def cancel(self): self._cancel.set(); self.provider.cancel()
    def translate_items(self, items: list[dict], target_language: str, progress=None, wait=None) -> TranslationSession:
        protected={}; payload=[]
        for item in items:
            text,mapping=self.protector.protect(str(item["text"])); protected[str(item["id"])]=mapping; payload.append({"id":str(item["id"]),"text":text})
        session=TranslationSession(len(payload)); batches=self.batches.split(payload)
        for batch_index,batch in enumerate(batches,1):
            if self._cancel.is_set(): session.cancelled=True; raise AICancelled("Translation cancelled.")
            try:
                results=self.limiter.run(lambda b=batch:self.provider.translate_batch(b,target_language),on_wait=wait)
                expected={item["id"] for item in batch}; found=set()
                for item in results:
                    identifier=str(item.get("id","")); text=str(item.get("text",""))
                    if identifier not in expected or not self.protector.validate(text,protected[identifier]): continue
                    session.translations[identifier]=self.protector.restore(text,protected[identifier]); found.add(identifier)
                if found != expected: session.failed_batches.append([item for item in batch if item["id"] not in found])
            except AICancelled: raise
            except Exception: session.failed_batches.append(batch)
            session.completed+=len(batch)
            if progress: progress(session.completed,session.total,batch_index,len(batches))
        return session
    def translate(self, sources, target_language, output_dir: Path, progress=None, wait=None) -> TranslationSession:
        self._cancel.clear()
        if hasattr(self.provider,"reset_cancel"): self.provider.reset_cancel()
        documents=parse_sources([Path(p) for p in sources]); payload=[]
        for document in documents:
            for entry in document.entries:
                payload.append({"id":entry.entry_id,"text":entry.value})
        prompt_name=getattr(target_language,"prompt_name",str(target_language)); suffix=getattr(target_language,"filename_suffix",str(target_language).casefold())
        session=self.translate_items(payload,prompt_name,progress,wait)
        output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
        for document in documents:
            parts=[suffix if part.casefold() in KNOWN_SUFFIXES else part for part in Path(document.relative_path).parts]
            if parts: parts[-1]=convert_localization_filename(parts[-1],suffix)
            relative=Path(*parts); target=output_dir/relative; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(document.render(session.translations,suffix),encoding="utf-8")
        return session
    @staticmethod
    def apply_preview(preview_dir: Path, destination: Path, backup_root: Path | None=None) -> int:
        preview_dir=Path(preview_dir); destination=Path(destination); files=list(preview_dir.rglob("*.yml")); copied=0
        for source in files:
            target=destination/source.relative_to(preview_dir)
            if target.exists() and backup_root:
                backup=Path(backup_root)/target.relative_to(destination); backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,backup)
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target); copied+=1
        return copied
