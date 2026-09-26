from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageDefinition:
    ui_code: str
    display_name: str
    filename_suffix: str
    localization_header: str
    prompt_name: str


LANGUAGES = {
    "ko-KR": LanguageDefinition("ko-KR", "한국어", "korean", "l_korean:", "Korean"),
    "en-US": LanguageDefinition("en-US", "English", "english", "l_english:", "English"),
    "zh-CN": LanguageDefinition("zh-CN", "简体中文", "simp_chinese", "l_simp_chinese:", "Simplified Chinese"),
    # Victoria 3 has no separate Traditional Chinese localization directory.
    "zh-TW": LanguageDefinition("zh-TW", "繁體中文", "simp_chinese", "l_simp_chinese:", "Traditional Chinese"),
    "ja-JP": LanguageDefinition("ja-JP", "日本語", "japanese", "l_japanese:", "Japanese"),
}

KNOWN_SUFFIXES = (
    "simp_chinese", "braz_por", "english", "japanese", "korean", "french",
    "german", "spanish", "russian", "polish", "turkish",
)


def target_language(ui_code: str) -> LanguageDefinition:
    if ui_code in LANGUAGES: return LANGUAGES[ui_code]
    return next((item for item in LANGUAGES.values() if item.filename_suffix == ui_code), LANGUAGES["ko-KR"])
