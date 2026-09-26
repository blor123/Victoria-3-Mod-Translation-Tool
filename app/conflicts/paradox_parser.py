import re
from dataclasses import dataclass

ASSIGNMENT=re.compile(r'(?m)^\s*([A-Za-z0-9_.:@-]+)\s*=\s*\{')


@dataclass(frozen=True)
class Definition:
    name:str; start_line:int; end_line:int; snippet:str


def _mask_comments(text:str)->str:
    result=[]; quoted=False; escaped=False; comment=False
    for char in text:
        if comment:
            if char=='\n': comment=False; result.append(char)
            else: result.append(' ')
        elif quoted:
            result.append(char)
            if escaped: escaped=False
            elif char=='\\': escaped=True
            elif char=='"': quoted=False
        elif char=='#': comment=True; result.append(' ')
        else:
            result.append(char)
            if char=='"': quoted=True
    return ''.join(result)


def parse_definitions(text:str)->tuple[list[Definition],list[str]]:
    masked=_mask_comments(text); depth=0; quoted=False; escaped=False; top_starts={}; close_for={}; warnings=[]
    for index,char in enumerate(masked):
        if quoted:
            if escaped: escaped=False
            elif char=='\\': escaped=True
            elif char=='"': quoted=False
            continue
        if char=='"': quoted=True; continue
        if char=='{':
            if depth==0: top_starts[index]=True
            depth+=1
        elif char=='}':
            depth-=1
            if depth<0: warnings.append("Unexpected closing brace"); depth=0
            elif depth==0:
                start=max((value for value in top_starts if value<=index and value not in close_for),default=None)
                if start is not None: close_for[start]=index
    if depth: warnings.append("Unclosed brace")
    definitions=[]
    for match in ASSIGNMENT.finditer(masked):
        brace=masked.find('{',match.start(),match.end()+1)
        # Only assignments beginning at top level are registered in top_starts.
        if brace not in top_starts: continue
        end=close_for.get(brace)
        if end is None: continue
        start_line=text.count('\n',0,match.start())+1; end_line=text.count('\n',0,end)+1
        snippet=text[match.start():end+1]
        definitions.append(Definition(match.group(1),start_line,end_line,snippet))
    return definitions,warnings
