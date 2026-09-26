import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from app import APP_VERSION, DEFAULT_PROMPT_VERSION
from app.snapshots.snapshot_model import LocalizationEntry
from app.utils.file_scanner import scan_yml_files
from app.utils.paths import user_data_dir

_ENTRY = re.compile(r'^\s*([A-Za-z0-9_.-]+):\d*\s+"(.*)"\s*$')


def capture_localization(root: Path) -> dict:
    root = Path(root).resolve(); entries: list[dict] = []; files = scan_yml_files([root])
    for path in files:
        try: relative = path.relative_to(root).as_posix()
        except ValueError: relative = path.name
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for line in text.splitlines():
            match = _ENTRY.match(line)
            if match:
                entries.append(LocalizationEntry(match.group(1), match.group(2), relative, line).to_dict())
    digest = hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"root": str(root), "files": len(files), "entries": entries, "hash": digest}


class SnapshotManager:
    def __init__(self, base: Path | None = None) -> None:
        self.base = base or user_data_dir() / "projects"

    def _directory(self, project_id: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", project_id); path = self.base / safe / "snapshots"; path.mkdir(parents=True, exist_ok=True); return path

    def save(self, project: dict, target, localization_path: Path | None = None) -> Path:
        root = Path(localization_path or project.get("localization_path") or project.get("source_path", "")); state = capture_localization(root)
        payload = {"project_id": project["id"], "created_at": datetime.now().isoformat(timespec="seconds"), "target_language": target.filename_suffix, "target_ui_locale": target.ui_code, "prompt_version": DEFAULT_PROMPT_VERSION, "app_version": APP_VERSION, **state}
        path = self._directory(project["id"]) / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"; path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"); return path

    def latest(self, project_id: str) -> dict | None:
        files = sorted(self._directory(project_id).glob("*.json"), reverse=True)
        for path in files:
            try: return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError): continue
        return None
