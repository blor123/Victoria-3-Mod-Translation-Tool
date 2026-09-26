import re
import os
from dataclasses import dataclass
from pathlib import Path
from app.i18n.language_definition import KNOWN_SUFFIXES

ENTRY = re.compile(r'^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):(?P<version>\d*)\s+"(?P<value>(?:\\.|[^"\\])*)"(?P<tail>\s*(?:#.*)?)$')
HEADER = re.compile(r'^\s*l_([A-Za-z0-9_-]+):\s*$')


@dataclass
class LocalizationEntry:
    entry_id: str; key: str; version: str; value: str; line_index: int; relative_path: str


@dataclass
class LocalizationDocument:
    path: Path; relative_path: str; lines: list[str]; entries: list[LocalizationEntry]; language: str
    def render(self, translations: dict[str,str], target_header: str | None=None) -> str:
        lines=list(self.lines)
        if target_header:
            for index,line in enumerate(lines):
                if HEADER.match(line): lines[index]=f"l_{target_header}:"; break
        for entry in self.entries:
            if entry.entry_id not in translations: continue
            original=ENTRY.match(lines[entry.line_index])
            escaped=translations[entry.entry_id].replace('\\','\\\\').replace('"','\\"')
            lines[entry.line_index]=f'{original.group("indent")}{entry.key}:{entry.version} "{escaped}"{original.group("tail")}'
        return "\ufeff"+"\n".join(lines)+("\n" if lines else "")


def _decode_value(value: str) -> str: return value.replace('\\"','"').replace('\\n','\\n').replace('\\\\','\\')


def parse_file(path: Path, root: Path | None=None) -> LocalizationDocument:
    path=Path(path); text=path.read_text(encoding="utf-8-sig",errors="strict"); lines=text.splitlines(); language="unknown"; entries=[]
    for line in lines:
        match=HEADER.match(line)
        if match: language=match.group(1); break
    relative=path.relative_to(root).as_posix() if root else path.name
    for index,line in enumerate(lines):
        match=ENTRY.match(line)
        if match: entries.append(LocalizationEntry(f"{relative}::{match.group('key')}",match.group("key"),match.group("version"),_decode_value(match.group("value")),index,relative))
    return LocalizationDocument(path,relative,lines,entries,language)


def parse_sources(sources: list[Path]) -> list[LocalizationDocument]:
    source_paths=list(map(Path,sources)); files=[]
    for source in source_paths: files.extend([source] if source.is_file() and source.suffix.lower()==".yml" else sorted(source.rglob("*.yml")) if source.is_dir() else [])
    unique=sorted({p.resolve() for p in files},key=lambda p:str(p).casefold())
    root=Path(os.path.commonpath([str(p.parent) for p in unique])) if unique else None
    if root and root.name.casefold() in KNOWN_SUFFIXES and root.parent.name.casefold()=="localization": root=root.parent.parent
    elif len(source_paths)==1 and source_paths[0].is_dir() and source_paths[0].name.casefold()=="localization": root=source_paths[0].parent.resolve()
    return [parse_file(path,root) for path in unique]
