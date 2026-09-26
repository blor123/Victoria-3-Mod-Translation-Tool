import unittest

from app.translation.filename_converter import convert_localization_filename


class FilenameConverterTests(unittest.TestCase):
    def test_standard_names(self) -> None:
        self.assertEqual(convert_localization_filename("economy_english.yml"), "economy_korean.yml")
        self.assertEqual(
            convert_localization_filename("financial_system_l_english.yml"),
            "financial_system_l_korean.yml",
        )

    def test_case_insensitive_suffix_and_preserves_extension(self) -> None:
        self.assertEqual(convert_localization_filename("Name_ENGLISH.YML"), "Name_korean.YML")

    def test_suffixless_unicode_names_receive_target_suffix(self) -> None:
        self.assertEqual(convert_localization_filename("한글 파일.yml"), "한글 파일_korean.yml")
        self.assertEqual(convert_localization_filename("notes.txt"), "notes.txt")


if __name__ == "__main__":
    unittest.main()
