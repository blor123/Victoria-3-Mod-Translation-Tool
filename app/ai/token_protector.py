import re

TOKEN_PATTERN = re.compile(r"""\$[^$\r\n]+\$|£[^£\r\n]+£|@[A-Za-z0-9_]+!|#[A-Za-z0-9_]+|\\n|\[(?:Concept|GetPlayer|SCOPE|GetLawType|GetBuildingType)\([^\]\r\n]+\)\]|§[A-Za-z0-9!]|\[[A-Za-z0-9_.:|()'" ,+\-]+\]""")


class TokenProtector:
    def protect(self, text: str) -> tuple[str, dict[str,str]]:
        mapping={}
        def replace(match):
            placeholder=f"__V3MM_TOKEN_{len(mapping)+1:04d}__"; mapping[placeholder]=match.group(0); return placeholder
        return TOKEN_PATTERN.sub(replace,text),mapping
    def restore(self, text: str, mapping: dict[str,str]) -> str:
        result=text
        for placeholder,value in mapping.items(): result=result.replace(placeholder,value)
        missing=[key for key in mapping if key in result]
        if missing: raise ValueError("Protected token restoration failed.")
        return result
    def validate(self, text: str, mapping: dict[str,str]) -> bool: return all(text.count(key)==1 for key in mapping)
