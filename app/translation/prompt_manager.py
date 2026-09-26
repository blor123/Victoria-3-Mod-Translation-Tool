from pathlib import Path

from app import DEFAULT_PROMPT_VERSION
from app.config.config_manager import ConfigManager
from app.utils.paths import resource_path


PROMPT_FILES = {
    "ko-KR": "ko", "en-US": "en", "zh-CN": "zh_cn",
    "zh-TW": "zh_tw", "ja-JP": "ja",
}


def normalize_prompt_language(code: str | None) -> str:
    return code if code in PROMPT_FILES else "ko-KR"


def default_prompt(language: str = "ko-KR") -> str:
    token = PROMPT_FILES[normalize_prompt_language(language)]
    path = resource_path(
        f"resources/prompts/victoria3_translation_{token}_v{DEFAULT_PROMPT_VERSION}.txt"
    )
    return Path(path).read_text(encoding="utf-8")


def prompt_body(config: ConfigManager, language: str | None = None) -> str:
    code = normalize_prompt_language(language or str(config.data.get("prompt_language") or config.data.get("language", "ko-KR")))
    values = config.data.get("custom_prompts", {})
    custom = str(values.get(code, "") if isinstance(values, dict) else "").strip()
    return custom or default_prompt(code)


def active_prompt(config: ConfigManager, target=None, instruction_language: str | None = None) -> str:
    language = normalize_prompt_language(instruction_language or str(config.data.get("prompt_language") or config.data.get("language", "ko-KR")))
    prompt = prompt_body(config, language)
    if target is None:
        from app.i18n.language_definition import target_language
        target = target_language(str(config.data.get("language", "ko-KR")))
    return f"Target translation language: {target.prompt_name}\nRequired localization header: {target.localization_header}\nThese target settings take precedence over any conflicting wording in a custom instruction.\n\n{prompt}"


def save_custom_prompt(config: ConfigManager, text: str, language: str | None = None) -> None:
    code = normalize_prompt_language(language or str(config.data.get("prompt_language", "ko-KR")))
    values = dict(config.data.get("custom_prompts", {})); values[code] = text
    config.update(custom_prompts=values, prompt_language=code, prompt_version=DEFAULT_PROMPT_VERSION)


def restore_default_prompt(config: ConfigManager, language: str | None = None) -> str:
    code = normalize_prompt_language(language or str(config.data.get("prompt_language", "ko-KR")))
    text = default_prompt(code); values = dict(config.data.get("custom_prompts", {})); values.pop(code, None)
    config.update(custom_prompts=values, prompt_language=code, prompt_version=DEFAULT_PROMPT_VERSION)
    return text
