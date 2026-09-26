import tempfile
import unittest
import zipfile
from pathlib import Path

from app.errors import ArchiveValidationError, DuplicateTargetError
from app.models import OverwritePolicy
from app.translation.package_importer import inspect_translation_zip, install_translation_zip


class PackageImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _zip(self, name: str, entries: dict[str, bytes]) -> Path:
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            for entry_name, content in entries.items():
                archive.writestr(entry_name, content)
        return path

    def test_finds_nested_localization_korean(self) -> None:
        package = self._zip(
            "아무 이름.zip",
            {
                "translated_files/localization/korean/economy_korean.yml": b"translated",
                "notes.txt": b"ignore",
            },
        )
        files = inspect_translation_zip(package)
        self.assertEqual(files[0].install_relative_path.as_posix(), "localization/korean/economy_korean.yml")

    def test_fallback_yml_is_normalized(self) -> None:
        package = self._zip("flat.zip", {"result.yml": b"translated"})
        files = inspect_translation_zip(package)
        self.assertEqual(files[0].install_relative_path.as_posix(), "localization/korean/result.yml")

    def test_bad_empty_and_unsafe_archives_are_rejected(self) -> None:
        broken = self.root / "broken.zip"
        broken.write_bytes(b"not a zip")
        with self.assertRaises(ArchiveValidationError):
            inspect_translation_zip(broken)
        empty = self._zip("empty.zip", {"readme.txt": b"none"})
        with self.assertRaises(ArchiveValidationError):
            inspect_translation_zip(empty)
        unsafe = self._zip("unsafe.zip", {"../escape.yml": b"bad"})
        with self.assertRaises(ArchiveValidationError):
            inspect_translation_zip(unsafe)

    def test_duplicate_install_target_is_rejected(self) -> None:
        package = self._zip(
            "duplicate.zip",
            {
                "one/localization/korean/same.yml": b"1",
                "two/localization/korean/same.yml": b"2",
            },
        )
        with self.assertRaises(DuplicateTargetError):
            inspect_translation_zip(package)

    def test_install_skip_and_backup_overwrite(self) -> None:
        package = self._zip(
            "translated.zip", {"localization/korean/test_korean.yml": b"new"}
        )
        install_root = self.root / "설치 경로"
        target = install_root / "localization" / "korean" / "test_korean.yml"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"old")

        skipped = install_translation_zip(package, install_root, OverwritePolicy.SKIP)
        self.assertEqual(target.read_bytes(), b"old")
        self.assertEqual(len(skipped.skipped), 1)

        installed = install_translation_zip(
            package, install_root, OverwritePolicy.BACKUP_AND_OVERWRITE
        )
        self.assertEqual(target.read_bytes(), b"new")
        self.assertEqual(len(installed.backed_up), 1)
        self.assertEqual(installed.backed_up[0].read_bytes(), b"old")

    def test_install_new_file_and_plain_overwrite(self) -> None:
        package = self._zip(
            "translated normal.zip", {"localization/korean/new file.yml": b"first"}
        )
        install_root = self.root / "new destination"
        result = install_translation_zip(package, install_root, OverwritePolicy.OVERWRITE)
        target = install_root / "localization" / "korean" / "new file.yml"
        self.assertEqual(target.read_bytes(), b"first")
        self.assertEqual(result.installed, [target])
        self.assertEqual(result.backed_up, [])

        replacement = self._zip(
            "replacement.zip", {"localization/korean/new file.yml": b"second"}
        )
        result = install_translation_zip(replacement, install_root, OverwritePolicy.OVERWRITE)
        self.assertEqual(target.read_bytes(), b"second")
        self.assertEqual(result.backed_up, [])


if __name__ == "__main__":
    unittest.main()
