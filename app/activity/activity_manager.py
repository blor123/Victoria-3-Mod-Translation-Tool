import uuid
from datetime import datetime

from PySide6.QtCore import QObject, Signal


class ActivityManager(QObject):
    changed = Signal()
    added = Signal(dict)

    def __init__(self, config) -> None:
        super().__init__(); self.config = config
        if not isinstance(config.data.get("activities"), list): config.data["activities"] = []
        if not config.data.get("activity_migration_complete", False):
            if not config.data["activities"]:
                for old in config.data["recent_activities"]:
                    old_type = {"package": "PACKAGE_CREATED", "apply": "TRANSLATION_APPLIED"}.get(str(old.get("action", "")).lower(), "INFO")
                    config.data["activities"].append({"id": uuid.uuid4().hex, "type": old_type, "message": old.get("name", ""), "timestamp": old.get("timestamp", ""), "project_id": None, "severity": "info", "read": True, "metadata": {"status": old.get("status", "")}})
            config.data["recent_activities"] = []
            config.data["activity_migration_complete"] = True
            config.save()

    @property
    def records(self) -> list[dict]: return list(self.config.data.get("activities", []))

    def add(self, activity_type: str, message: str, project_id=None, severity="info", metadata=None, dedupe_key=None) -> dict:
        records = self.records
        if dedupe_key:
            if dedupe_key in self.config.data.get("dismissed_activity_keys", []): return {}
            for record in records:
                if record.get("metadata", {}).get("dedupe_key") == dedupe_key: return record
        meta = dict(metadata or {})
        if dedupe_key: meta["dedupe_key"] = dedupe_key
        record = {"id": uuid.uuid4().hex, "type": activity_type, "message": message, "timestamp": datetime.now().isoformat(timespec="minutes"), "project_id": project_id, "severity": severity, "read": False, "metadata": meta}
        records.insert(0, record); self.config.data["activities"] = records[:200]; self.config.save(); self.added.emit(record); self.changed.emit(); return record

    def remove(self, activity_id: str) -> None:
        removed = next((r for r in self.records if r.get("id") == activity_id), None)
        if removed and removed.get("metadata", {}).get("dedupe_key"):
            keys = set(self.config.data.get("dismissed_activity_keys", [])); keys.add(removed["metadata"]["dedupe_key"]); self.config.data["dismissed_activity_keys"] = sorted(keys)[-500:]
        self.config.data["activities"] = [r for r in self.records if r.get("id") != activity_id]; self.config.save(); self.changed.emit()

    def clear(self) -> None:
        keys = set(self.config.data.get("dismissed_activity_keys", [])); keys.update(r.get("metadata", {}).get("dedupe_key") for r in self.records if r.get("metadata", {}).get("dedupe_key")); self.config.data["dismissed_activity_keys"] = sorted(keys)[-500:]; self.config.data["activities"] = []; self.config.save(); self.changed.emit()

    def mark_all_read(self) -> None:
        records = self.records
        for record in records: record["read"] = True
        self.config.data["activities"] = records; self.config.save(); self.changed.emit()

    def unread_count(self) -> int: return sum(not r.get("read", False) for r in self.records)
