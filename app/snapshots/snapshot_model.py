from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LocalizationEntry:
    key: str
    value: str
    relative_path: str
    raw_line: str

    def to_dict(self) -> dict:
        return asdict(self)
