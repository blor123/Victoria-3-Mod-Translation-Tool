from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TranslationSession:
    total: int; completed: int=0; failed_batches: list[list[dict]]=field(default_factory=list); translations: dict[str,str]=field(default_factory=dict); cancelled: bool=False
    started_at: str=field(default_factory=lambda:datetime.now().isoformat(timespec="seconds"))
    @property
    def succeeded(self): return len(self.translations)
