from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiffItem:
    status: str
    key: str
    old_value: str = ""
    new_value: str = ""
    relative_path: str = ""
    raw_line: str = ""


@dataclass
class DiffResult:
    items: list[DiffItem] = field(default_factory=list)
    @property
    def counts(self) -> dict[str, int]:
        return {name: sum(item.status == name for item in self.items) for name in ("NEW", "CHANGED", "DELETED", "UNCHANGED")}
    @property
    def translatable(self) -> list[DiffItem]: return [item for item in self.items if item.status in {"NEW", "CHANGED"}]


def compare_snapshot(previous: dict, current: dict) -> DiffResult:
    old = {item["key"]: item for item in previous.get("entries", [])}; new = {item["key"]: item for item in current.get("entries", [])}; result = DiffResult()
    for key in sorted(old.keys() | new.keys(), key=str.casefold):
        before, after = old.get(key), new.get(key)
        if before is None: status = "NEW"
        elif after is None: status = "DELETED"
        elif before.get("value") != after.get("value"): status = "CHANGED"
        else: status = "UNCHANGED"
        source = after or before or {}; result.items.append(DiffItem(status, key, str((before or {}).get("value", "")), str((after or {}).get("value", "")), str(source.get("relative_path", "")), str((after or {}).get("raw_line", ""))))
    return result
