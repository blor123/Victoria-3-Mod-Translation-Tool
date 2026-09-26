import json
from pathlib import Path

from app.ai.request_builder import conflict_payload
from app.ai.response_parser import validate_conflict_result
from app.version import CONFLICT_PROMPT_VERSION
from app.ai.rate_limit_manager import RateLimitManager


class ConflictAIService:
    def __init__(self,provider,cache_path:Path,max_retries=3): self.provider=provider; self.cache_path=Path(cache_path); self.cache=self._load(); self.limiter=RateLimitManager(max_retries)
    def _load(self):
        try:return json.loads(self.cache_path.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError):return {}
    def _save(self):
        self.cache_path.parent.mkdir(parents=True,exist_ok=True); temp=self.cache_path.with_suffix('.tmp'); temp.write_text(json.dumps(self.cache,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(self.cache_path)
    def preview(self,conflict):
        payload=conflict_payload(conflict)
        return {"type":payload["type"],"subject":payload["subject"],"mod_a":payload["mod_a"],"mod_b":payload["mod_b"],"characters_a":len(payload["snippet_a"]),"characters_b":len(payload["snippet_b"])}
    def analyze(self,conflict,force=False):
        fingerprint=conflict.fingerprint(self.provider.model,CONFLICT_PROMPT_VERSION)
        if not force and fingerprint in self.cache:return self.cache[fingerprint]
        result=validate_conflict_result(self.limiter.run(lambda:self.provider.analyze_conflict(conflict_payload(conflict)))); self.cache[fingerprint]=result; self._save(); return result
