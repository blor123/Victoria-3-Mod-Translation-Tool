from app.snapshots import DiffItem, DiffResult, capture_localization, compare_snapshot


def analyze_with_snapshot(previous: dict, updated_source) -> DiffResult:
    current = capture_localization(updated_source)
    return compare_snapshot(previous, current)


def analyze_legacy(existing_translation, updated_source) -> DiffResult:
    """Key-only fallback. It intentionally never guesses whether text changed."""
    translated = capture_localization(existing_translation)
    current = capture_localization(updated_source)
    old = {entry["key"]: entry for entry in translated.get("entries", [])}
    new = {entry["key"]: entry for entry in current.get("entries", [])}
    result = DiffResult()
    for key in sorted(old.keys() | new.keys(), key=str.casefold):
        before, after = old.get(key), new.get(key)
        if before is None:
            status = "NEW"
        elif after is None:
            status = "DELETION_CANDIDATE"
        else:
            status = "EXISTING_UNKNOWN"
        source = after or before or {}
        result.items.append(DiffItem(status, key, str((before or {}).get("value", "")), str((after or {}).get("value", "")), str(source.get("relative_path", "")), str((after or {}).get("raw_line", ""))))
    return result
