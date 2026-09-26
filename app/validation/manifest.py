import json
import uuid
from datetime import datetime
from pathlib import Path

from app.utils.paths import user_data_dir


def manifests_dir() -> Path:
    path = user_data_dir() / "manifests"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_manifest(files, target, prompt_version: int) -> str:
    from app.validation.localization_validator import extract_keys, extract_tokens

    manifest_id = uuid.uuid4().hex
    payload = {
        "id": manifest_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "target_language": target.filename_suffix,
        "target_ui_locale": target.ui_code,
        "target_header": target.localization_header,
        "prompt_version": prompt_version,
        "files": [],
    }
    for item in files:
        text = item.content.decode("utf-8-sig", errors="replace")
        payload["files"].append({
            "archive_path": item.archive_path.as_posix(),
            "filename": item.archive_path.name,
            "keys": sorted(extract_keys(text)),
            "tokens": sorted(extract_tokens(text)),
        })
    (manifests_dir() / f"{manifest_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_id


def load_best_manifest(result_filenames: set[str]) -> dict | None:
    best, best_score = None, 0
    for path in sorted(manifests_dir().glob("*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            names = {str(item["filename"]).casefold() for item in data.get("files", [])}
            score = len(names & {name.casefold() for name in result_filenames})
            if score > best_score:
                best, best_score = data, score
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            continue
    return best
