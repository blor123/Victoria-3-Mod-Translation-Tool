import hashlib
import json
import uuid
from dataclasses import asdict,dataclass,field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ConflictMod:
    id:str; display_name:str; root_path:Path; descriptor_path:Path|None=None; project_id:str=""
    @classmethod
    def from_folder(cls,path,project_id=""):
        root=Path(path).resolve(); descriptor=next((p for p in (root/"descriptor.mod",root.with_suffix(".mod")) if p.exists()),None)
        return cls(hashlib.sha256(str(root).casefold().encode()).hexdigest()[:16],root.name,root,descriptor,project_id)


@dataclass
class ConflictRecord:
    category:str; severity:str; subject:str; reason:str; mod_a:str=""; mod_b:str=""; file_a:str=""; file_b:str=""; snippet_a:str=""; snippet_b:str=""; replace_paths:tuple[str,...]=(); ai_result:dict|None=None; id:str=field(default_factory=lambda:uuid.uuid4().hex)
    def fingerprint(self,model="",prompt_version=1):
        payload=[self.category,self.subject,self.snippet_a,self.snippet_b,model,str(prompt_version)]
        return hashlib.sha256("\0".join(payload).encode("utf-8")).hexdigest()
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,data):
        values=dict(data); values["replace_paths"]=tuple(values.get("replace_paths",())); return cls(**values)


@dataclass
class ConflictReport:
    mods:list[ConflictMod]; conflicts:list[ConflictRecord]; warnings:list[str]=field(default_factory=list); created_at:str=field(default_factory=lambda:datetime.now().isoformat(timespec="seconds")); version:int=1
    def summary(self):
        result={"mods":len(self.mods),"total":len(self.conflicts)}
        for item in self.conflicts: result[item.category]=result.get(item.category,0)+1
        return result
    def to_dict(self):
        return {"format":"v3mm_conflict_report","version":self.version,"created_at":self.created_at,
                "mods":[{**asdict(mod),"root_path":str(mod.root_path),"descriptor_path":str(mod.descriptor_path) if mod.descriptor_path else ""} for mod in self.mods],
                "summary":self.summary(),"conflicts":[item.to_dict() for item in self.conflicts],"warnings":self.warnings}
    @classmethod
    def from_dict(cls,data):
        mods=[ConflictMod(item["id"],item["display_name"],Path(item["root_path"]),Path(item["descriptor_path"]) if item.get("descriptor_path") else None,item.get("project_id","")) for item in data.get("mods",[])]
        return cls(mods,[ConflictRecord.from_dict(item) for item in data.get("conflicts",[])],list(data.get("warnings",[])),str(data.get("created_at","")),int(data.get("version",1)))
