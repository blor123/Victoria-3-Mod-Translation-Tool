import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

from app import DEFAULT_PROMPT_VERSION
from app.utils.paths import user_data_dir

DEFAULT_CONFIG = {
    "language": "ko-KR",
    "last_source_path": "",
    "last_export_path": "",
    "last_install_path": "",
    "last_import_zip_path": "",
    "create_backup": True,
    "open_export_folder_after_creation": True,
    "remember_recent_paths": True,
    "recent_activities": [],
    "activities": [],
    "activity_migration_complete": False,
    "dismissed_activity_keys": [],
    "projects": [],
    "check_updates_on_startup": True,
    "last_update_check": "",
    "prompt_version": DEFAULT_PROMPT_VERSION,
    "custom_prompt": "",
    "prompt_language": "ko-KR",
    "custom_prompts": {},
    "last_quick_export_path": "",
    "last_update_source_path": "",
    "last_update_previous_path": "",
    "last_update_translation_path": "",
    "imported_mods": [],
    "last_mod_import_path": "",
    "last_mod_export_path": "",
    "loadouts": [],
    "active_loadout_id": "",
    "last_loadout_path": "",
    "ai_provider": "gemini",
    "ai_model": "gemini-3.8-flash",
    "ai_retry_enabled": True,
    "ai_max_retries": 3,
    "ai_batch_size": 40,
    "ai_conflict_notice_dismissed": False,
    "last_ai_source_path": "",
    "last_ai_output_path": "",
    "last_ai_install_path": "",
    "conflict_reports": [],
    "last_conflict_path": "",
}


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_data_dir() / "config.json"
        self.data = self.load()

    def load(self) -> dict:
        data = deepcopy(DEFAULT_CONFIG)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update({key: value for key, value in loaded.items() if key in data})
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass
        # v1.5 used one shared prompt. Preserve it under the selected prompt language.
        if data.get("custom_prompt") and not data.get("custom_prompts"):
            code = str(data.get("prompt_language") or data.get("language") or "ko-KR")
            data["custom_prompts"] = {code: str(data["custom_prompt"])}
        if not data.get("prompt_language"):
            data["prompt_language"] = str(data.get("language", "ko-KR"))
        # v2.1.0 used the legacy GenerateContent default. Authorization keys use
        # the current Interactions API and its current default model.
        if data.get("ai_model") == "gemini-2.5-flash":
            data["ai_model"] = DEFAULT_CONFIG["ai_model"]
        return data

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp_name = tempfile.mkstemp(prefix="config_", dir=self.path.parent)
        os.close(handle)
        temp_path = Path(temp_name)
        try:
            temp_path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(temp_path, self.path)
        finally:
            temp_path.unlink(missing_ok=True)

    def update(self, **values: object) -> None:
        for key, value in values.items():
            if key in DEFAULT_CONFIG:
                self.data[key] = value
        self.save()

    def add_recent_activity(self, name: str, action: str, status: str) -> None:
        from datetime import datetime

        current = self.data.get("recent_activities", [])
        activities = list(current) if isinstance(current, list) else []
        activities.insert(
            0,
            {
                "name": name or "Untitled",
                "timestamp": datetime.now().isoformat(timespec="minutes"),
                "action": action,
                "status": status,
            },
        )
        self.data["recent_activities"] = activities[:5]
        self.save()
