import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.ai.localization_parser import parse_file
from app.conflicts.paradox_parser import Definition,parse_definitions

TEXT_SUFFIXES={".txt",".mod",".yml",".yaml",".gui",".asset",".gfx"}
REPLACE=re.compile(r'(?m)^\s*replace_path\s*=\s*"([^"]+)"')


@dataclass
class IndexedFile:
    mod_id:str; mod_name:str; path:Path; relative_path:str; size:int; digest:str; text:str|None; definitions:list[Definition]; localizations:list[tuple[str,str,str]]


def read_text(path:Path)->str|None:
    if path.suffix.lower() not in TEXT_SUFFIXES: return None
    raw=path.read_bytes()
    for encoding in ("utf-8-sig","utf-8","cp1252"):
        try:return raw.decode(encoding)
        except UnicodeDecodeError: pass
    return None


def index_mod(mod,progress=None,cancel=None):
    records=[]; warnings=[]; paths=[p for p in mod.root_path.rglob('*') if p.is_file() and '.git' not in p.parts]
    for index,path in enumerate(paths,1):
        if cancel and cancel(): break
        try:
            raw=path.read_bytes(); relative=path.relative_to(mod.root_path).as_posix(); text=read_text(path); definitions=[]; localizations=[]
            if text is not None and path.suffix.lower()=='.txt' and relative.casefold().startswith('common/'):
                definitions,issues=parse_definitions(text); warnings.extend(f"{mod.display_name}: {relative}: {issue}" for issue in issues)
            if path.suffix.lower()=='.yml' and text is not None:
                document=parse_file(path,mod.root_path); localizations=[(document.language,entry.key,entry.value) for entry in document.entries]
            records.append(IndexedFile(mod.id,mod.display_name,path,relative,len(raw),hashlib.sha256(raw).hexdigest(),text,definitions,localizations))
        except Exception as error: warnings.append(f"{mod.display_name}: {path.name}: {error}")
        if progress: progress(index,len(paths))
    descriptors=[p for p in (mod.descriptor_path,mod.root_path/'descriptor.mod') if p and p.exists()]
    replace_paths=[]
    for path in dict.fromkeys(descriptors):
        try: replace_paths.extend(REPLACE.findall(read_text(path) or ''))
        except OSError as error: warnings.append(f"{mod.display_name}: descriptor: {error}")
    return records,replace_paths,warnings
