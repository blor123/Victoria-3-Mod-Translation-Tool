import re
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.validation.manifest import load_best_manifest

_KEY = re.compile(r"(?m)^[ \t]*([A-Za-z0-9_.-]+):\d*[ \t]+")
_TOKEN = re.compile(r"\$[^$\r\n]+\$|£[^£\r\n]+£|@[A-Za-z0-9_]+!|#[A-Za-z0-9_]+|\\n|\[(?:Concept|GetPlayer|SCOPE)\([^\]\r\n]+\)\]")


def extract_keys(text: str) -> set[str]: return set(_KEY.findall(text))
def extract_tokens(text: str) -> set[str]: return set(_TOKEN.findall(text))


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    filename: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)
    expected_files: int = 0
    actual_files: int = 0
    matched_keys: int = 0

    @property
    def errors(self): return [i for i in self.issues if i.severity == "ERROR"]
    @property
    def warnings(self): return [i for i in self.issues if i.severity == "WARNING"]


def validate_translation_zip(zip_path) -> ValidationReport | None:
    with zipfile.ZipFile(zip_path) as archive:
        yml = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith(".yml")]
        result = {PurePosixPath(i.filename).name.casefold(): (i, archive.read(i).decode("utf-8-sig", errors="replace")) for i in yml}
    manifest = load_best_manifest(set(result))
    if not manifest: return None
    report = ValidationReport(expected_files=len(manifest["files"]), actual_files=len(result))
    expected_names = {item["filename"].casefold() for item in manifest["files"]}
    for missing in sorted(expected_names - set(result)):
        report.issues.append(ValidationIssue("ERROR", missing, "Missing localization file"))
    for extra in sorted(set(result) - expected_names):
        report.issues.append(ValidationIssue("WARNING", extra, "Unexpected localization file"))
    for source in manifest["files"]:
        name = source["filename"].casefold()
        if name not in result: continue
        text = result[name][1]; expected_keys = set(source["keys"]); actual_keys = extract_keys(text)
        report.matched_keys += len(expected_keys & actual_keys)
        for key in sorted(expected_keys - actual_keys): report.issues.append(ValidationIssue("ERROR", source["filename"], f"Missing key: {key}"))
        for key in sorted(actual_keys - expected_keys): report.issues.append(ValidationIssue("WARNING", source["filename"], f"Unexpected key: {key}"))
        expected_tokens = set(source["tokens"]); actual_tokens = extract_tokens(text)
        for token in sorted(expected_tokens - actual_tokens): report.issues.append(ValidationIssue("WARNING", source["filename"], f"Token changed or missing: {token}"))
    return report
