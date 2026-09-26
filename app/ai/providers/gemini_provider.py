import json
import threading
import urllib.error
import urllib.request

from app.ai.api_errors import AICancelled, AIAuthenticationError, AIError, AIRateLimitError, AIResponseError
from app.ai.providers.base_provider import AIProvider
from app.utils.paths import resource_path

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.8-flash", timeout: int = 90):
        self.api_key = api_key; self.model = model; self.timeout = timeout; self._cancelled = threading.Event()
    def get_provider_name(self) -> str: return "Google Gemini"
    def cancel(self) -> None: self._cancelled.set()
    def reset_cancel(self) -> None: self._cancelled.clear()
    def _request(self, path: str, payload: dict | None = None) -> dict:
        if self._cancelled.is_set(): raise AICancelled("The operation was cancelled.")
        url = f"{BASE_URL}/{path.lstrip('/')}"; headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8") if payload is not None else None, headers=headers, method="POST" if payload is not None else "GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response: return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8", errors="replace")[:1000]
            try:
                api_message = str(json.loads(message).get("error", {}).get("message", ""))
            except (json.JSONDecodeError, AttributeError, TypeError):
                api_message = ""
            if error.code == 401:
                raise AIAuthenticationError(
                    "Gemini 인증에 실패했습니다. Google AI Studio에서 새 Authorization Key를 발급하고 다시 저장해 주세요."
                ) from error
            if error.code == 403:
                if "denied access" in api_message.casefold():
                    raise AIAuthenticationError(
                        "이 Google Cloud 프로젝트는 Gemini API 사용 권한이 없습니다. "
                        "AI Studio에서 프로젝트/API 상태와 결제·지역 제한을 확인해 주세요."
                    ) from error
                raise AIAuthenticationError(
                    "Gemini API 접근이 거부되었습니다. 키의 프로젝트, API 활성화 및 사용 권한을 확인해 주세요."
                ) from error
            if error.code == 429:
                try: retry = float(error.headers.get("Retry-After", "1") or 1)
                except ValueError: retry = 1.0
                raise AIRateLimitError("Gemini API rate limit reached.", retry) from error
            raise AIError(f"Gemini API HTTP {error.code}: {message}") from error
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error: raise AIError(f"Gemini API request failed: {error}") from error
    def _generate(self, prompt: str, schema: dict) -> object:
        data = self._request("interactions", {
            "model": self.model,
            "input": prompt,
            "store": False,
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        })
        try:
            text = next(
                block["text"]
                for step in reversed(data["steps"])
                if step.get("type") == "model_output"
                for block in step.get("content", [])
                if block.get("type") == "text"
            )
            return json.loads(text)
        except (KeyError, StopIteration, TypeError, json.JSONDecodeError) as error:
            raise AIResponseError("Gemini response could not be parsed.") from error
    def test_connection(self) -> bool:
        result = self._generate('Return {"ok": true}.', {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]})
        return bool(isinstance(result, dict) and result.get("ok"))
    def get_available_models(self) -> list[str]:
        data = self._request("models?pageSize=100"); models = []
        for item in data.get("models", []):
            if "generateContent" in item.get("supportedGenerationMethods", []): models.append(str(item.get("name", "")).removeprefix("models/"))
        return sorted(filter(None, models))
    def translate_batch(self, entries: list[dict], target_language: str) -> list[dict]:
        template = resource_path("resources/prompts/api_translation_v1.txt").read_text(encoding="utf-8")
        prompt = template.replace("{target_language}", target_language).replace("{entries}", json.dumps(entries, ensure_ascii=False))
        schema = {"type": "object", "properties": {"translations": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}}, "required": ["id", "text"]}}}, "required": ["translations"]}
        result = self._generate(prompt, schema)
        if not isinstance(result, dict) or not isinstance(result.get("translations"), list): raise AIResponseError("Translation response is invalid.")
        return result["translations"]
    def analyze_conflict(self, payload: dict) -> dict:
        template = resource_path("resources/prompts/conflict_analysis_en_v1.txt").read_text(encoding="utf-8")
        prompt = template + "\n\nINPUT:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
        arrays = {"important_differences", "possible_effects", "uncertainties", "recommended_checks"}
        fields = ("summary", "interaction_type", "overwrite_risk", "important_differences", "possible_effects", "compatibility_patch_needed", "uncertainties", "recommended_checks")
        schema = {"type": "object", "properties": {name: ({"type": "array", "items": {"type": "string"}} if name in arrays else {"type": "string"}) for name in fields}, "required": list(fields)}
        result = self._generate(prompt, schema)
        if not isinstance(result, dict): raise AIResponseError("Conflict analysis response is invalid.")
        return result
