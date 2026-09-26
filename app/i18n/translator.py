import json
import logging
from pathlib import Path

from app.utils.paths import resource_path

SUPPORTED_LANGUAGES = {
    "ko-KR": "한국어",
    "en-US": "English",
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "ja-JP": "日本語",
}

_language = "ko-KR"
_strings: dict[str, str] = {}
_fallback: dict[str, str] = {}


def _load(code: str) -> dict[str, str]:
    path = resource_path(f"resources/translations/{code}.json")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        strings = {str(key): str(value) for key, value in data.items()}
        extra = resource_path(f"resources/translations/v14/{code}.json")
        if Path(extra).exists():
            extra_data = json.loads(Path(extra).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in extra_data.items()})
        v15 = resource_path(f"resources/translations/v15/{code}.json")
        if Path(v15).exists():
            v15_data = json.loads(Path(v15).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in v15_data.items()})
        v16 = resource_path(f"resources/translations/v16/{code}.json")
        if Path(v16).exists():
            v16_data = json.loads(Path(v16).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in v16_data.items()})
        v17 = resource_path(f"resources/translations/v17/{code}.json")
        if Path(v17).exists():
            v17_data = json.loads(Path(v17).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in v17_data.items()})
        v18 = resource_path(f"resources/translations/v18/{code}.json")
        if Path(v18).exists():
            v18_data = json.loads(Path(v18).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in v18_data.items()})
        v21 = resource_path(f"resources/translations/v21/{code}.json")
        if Path(v21).exists():
            v21_data = json.loads(Path(v21).read_text(encoding="utf-8"))
            strings.update({str(key): str(value) for key, value in v21_data.items()})
        return strings
    except (OSError, json.JSONDecodeError, TypeError):
        logging.getLogger("v3mm").exception("Could not load UI translation: %s", code)
        return {}


def set_language(code: str) -> str:
    global _language, _strings, _fallback
    _language = code if code in SUPPORTED_LANGUAGES else "ko-KR"
    _fallback = _load("en-US")
    _strings = _load(_language)
    if not _strings and _language != "en-US":
        _language = "en-US"
        _strings = _fallback
    return _language


def current_language() -> str:
    return _language


def t(key: str, **values: object) -> str:
    template = _strings.get(key, _fallback.get(key, key))
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template


set_language("ko-KR")
