import tempfile
import unittest
import zipfile
from pathlib import Path

from app.errors import DuplicateTargetError, InputValidationError
from app.translation.package_builder import build_translation_package, plan_package


class PackageBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "한글 모드 폴더"
        self.english = self.root / "localization" / "english"
        self.english.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, relative: str, content: bytes = b"l_english:\n key:0 \"Value\"\n") -> Path:
        path = self.english / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_mod_folder_preserves_structure_and_only_changes_header(self) -> None:
        original = b"\xef\xbb\xbfl_english:\r\n key:0 \"Text $VALUE$\"\r\n"
        self._write("economy_english.yml", original)
        self._write("sub 폴더/bank_l_english.yml")
        french = self.root / "localization" / "french" / "ignore_french.yml"
        french.parent.mkdir(parents=True)
        french.write_text("ignore", encoding="utf-8")
        output = Path(self.temp.name) / "결과 파일.zip"

        planned = build_translation_package([self.root], output)

        self.assertEqual(len(planned), 3)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(
                sorted(archive.namelist()),
                [
                    "localization/korean/economy_korean.yml",
                    "localization/korean/ignore_korean.yml",
                    "localization/korean/sub 폴더/bank_l_korean.yml",
                ],
            )
            expected = original.replace(b"l_english:", b"l_korean:", 1)
            self.assertEqual(archive.read("localization/korean/economy_korean.yml"), expected)
            self.assertEqual((self.english / "economy_english.yml").read_bytes(), original)

    def test_header_warning_and_existing_korean_are_preserved(self) -> None:
        french = self._write("french_english.yml", b"\xef\xbb\xbfl_french:\r\n key:0 \"Text\"\r\n")
        korean = self._write("ready_english.yml", b"l_korean:\n key:0 \"Text\"\n")
        planned = plan_package([french, korean])
        statuses = {item.source.name: (item.declaration_status, item.content) for item in planned}
        self.assertEqual(statuses["french_english.yml"][0], "changed")
        self.assertIn(b"l_korean:", statuses["french_english.yml"][1])
        self.assertEqual(statuses["ready_english.yml"][0], "already_target")

    def test_single_unstructured_file_is_normalized(self) -> None:
        source = Path(self.temp.name) / "standalone_english.yml"
        source.write_text("unchanged", encoding="utf-8")
        planned = plan_package([source])
        self.assertEqual(planned[0].archive_path.as_posix(), "localization/korean/standalone_korean.yml")

    def test_english_and_localization_folders_are_supported(self) -> None:
        source = self._write("공백 있는 폴더/한글 이름_english.yml")
        from_english = plan_package([self.english])
        from_localization = plan_package([self.root / "localization"])
        expected = "localization/korean/공백 있는 폴더/한글 이름_korean.yml"
        self.assertIn(expected, [item.archive_path.as_posix() for item in from_english])
        self.assertIn(expected, [item.archive_path.as_posix() for item in from_localization])
        self.assertIn(source, [item.source for item in from_english])

    def test_nonexistent_and_empty_inputs_are_rejected(self) -> None:
        with self.assertRaises(InputValidationError):
            plan_package([self.root / "존재하지 않음"])
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(InputValidationError):
            plan_package([empty])

    def test_duplicate_archive_target_is_rejected(self) -> None:
        first = Path(self.temp.name) / "one" / "same_english.yml"
        second = Path(self.temp.name) / "two" / "same_english.yml"
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_text("1", encoding="utf-8")
        second.write_text("2", encoding="utf-8")
        with self.assertRaises(DuplicateTargetError):
            plan_package([first, second])


if __name__ == "__main__":
    unittest.main()
