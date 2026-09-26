from collections import defaultdict
from itertools import combinations

from app.conflicts.models import ConflictRecord,ConflictReport
from app.conflicts.scanner import index_mod


def _short(text,max_chars=12000):
    if not text:return ''
    return text if len(text)<=max_chars else text[:max_chars]+"\n… [snippet truncated]"


class ConflictAnalyzer:
    def analyze(self,mods,progress=None,cancel=None)->ConflictReport:
        all_files=[]; replacements={}; warnings=[]
        for number,mod in enumerate(mods,1):
            if cancel and cancel(): break
            if progress: progress("index",number-1,len(mods))
            records,paths,issues=index_mod(mod,cancel=cancel); all_files.extend(records); replacements[mod.id]=(mod.display_name,paths); warnings.extend(issues)
        conflicts=[]; by_path=defaultdict(list)
        for item in all_files: by_path[item.relative_path.casefold()].append(item)
        for records in by_path.values():
            for a,b in combinations(records,2):
                if a.mod_id==b.mod_id:continue
                same=a.digest==b.digest
                conflicts.append(ConflictRecord("file","DUPLICATE" if same else "POTENTIAL_CONFLICT",a.relative_path,
                    "Same relative path and identical content." if same else "Same relative path but different content.",
                    a.mod_name,b.mod_name,a.relative_path,b.relative_path,_short(a.text),_short(b.text)))
        if progress:progress("localization",0,len(all_files))
        localizations=defaultdict(list)
        for item in all_files:
            for language,key,value in item.localizations:localizations[(language.casefold(),key)].append((item,value))
        for (language,key),values in localizations.items():
            for (a,av),(b,bv) in combinations(values,2):
                if a.mod_id==b.mod_id:continue
                same=av==bv
                conflicts.append(ConflictRecord("localization","DUPLICATE" if same else "POTENTIAL_CONFLICT",f"{language}:{key}",
                    "Same language/key/value." if same else "Same language/key but different values.",a.mod_name,b.mod_name,a.relative_path,b.relative_path,av,bv))
        if progress:progress("definition",0,len(all_files))
        definitions=defaultdict(list)
        for item in all_files:
            for definition in item.definitions:definitions[definition.name].append((item,definition))
        for name,values in definitions.items():
            for (a,ad),(b,bd) in combinations(values,2):
                if a.mod_id==b.mod_id:continue
                same=ad.snippet==bd.snippet
                conflicts.append(ConflictRecord("definition","DUPLICATE" if same else "CONFLICT",name,
                    "Both mods define the same top-level definition with identical content." if same else "Both mods define the same top-level definition.",
                    a.mod_name,b.mod_name,a.relative_path,b.relative_path,_short(ad.snippet),_short(bd.snippet)))
        if progress:progress("replace_path",0,len(replacements))
        for mod_id,(name,paths) in replacements.items():
            for path in paths:
                affected=sorted({item.mod_name for item in all_files if item.mod_id!=mod_id and (item.relative_path.casefold()==path.casefold() or item.relative_path.casefold().startswith(path.casefold().rstrip('/')+'/'))})
                reason="replace_path hides files in this path"
                if affected:reason+=f" and overlaps: {', '.join(affected)}"
                conflicts.append(ConflictRecord("replace_path","REPLACE_PATH_WARNING",path,reason,name,affected[0] if affected else "",replace_paths=(path,)))
        for warning in warnings: conflicts.append(ConflictRecord("parser","PARSER_WARNING",warning,"One file could not be fully parsed; remaining analysis continued."))
        return ConflictReport(list(mods),conflicts,warnings)
