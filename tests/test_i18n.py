import json
import unittest
from pathlib import Path

from app.i18n import SUPPORTED_LANGUAGES


class I18nTests(unittest.TestCase):
    def test_all_locales_have_the_same_keys(self) -> None:
        root = Path(__file__).parents[1] / "resources" / "translations"
        translations = {code: json.loads((root / f"{code}.json").read_text(encoding="utf-8")) for code in SUPPORTED_LANGUAGES}
        expected = set(translations["ko-KR"])
        for code, strings in translations.items():
            self.assertEqual(set(strings), expected, code)
            self.assertTrue(all(strings.values()), code)
        for version in ("v14", "v15"):
            overlays = {code: json.loads((root / version / f"{code}.json").read_text(encoding="utf-8")) for code in SUPPORTED_LANGUAGES}
            overlay_keys = set(overlays["ko-KR"])
            for code, strings in overlays.items(): self.assertEqual(set(strings), overlay_keys, f"{version}/{code}")
