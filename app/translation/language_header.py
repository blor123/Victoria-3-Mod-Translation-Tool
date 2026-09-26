import re
from dataclasses import dataclass

_HEADER = re.compile(rb"(?m)^(\xef\xbb\xbf)?([ \t]*)l_([A-Za-z_]+)([ \t]*:)")


@dataclass(frozen=True)
class HeaderResult:
    content: bytes
    status: str
    declaration: str = ""
    warning: str = ""
    source_language: str = "unknown"


def detect_language_declaration(content: bytes) -> str:
    match = _HEADER.search(content)
    return match.group(3).decode("ascii", errors="replace").casefold() if match else "unknown"


def convert_language_declaration(content: bytes, target_language: str = "korean") -> HeaderResult:
    match = _HEADER.search(content)
    if not match:
        return HeaderResult(content, "missing", "", "missing_declaration")
    source = match.group(3).decode("ascii", errors="replace").casefold()
    if source == target_language.casefold():
        return HeaderResult(content, "already_target", f"l_{source}", "", source)
    replacement = match.group(1) or b""
    replacement += match.group(2) + f"l_{target_language}".encode("ascii") + match.group(4)
    changed = content[:match.start()] + replacement + content[match.end():]
    return HeaderResult(changed, "changed", f"l_{source}", "", source)
