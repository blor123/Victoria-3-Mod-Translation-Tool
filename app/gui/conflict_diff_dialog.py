import difflib
from PySide6.QtWidgets import QDialog,QHBoxLayout,QLabel,QPlainTextEdit,QVBoxLayout

from app.i18n import t


class ConflictDiffDialog(QDialog):
    def __init__(self,conflict,parent=None):
        super().__init__(parent);self.setWindowTitle(t('conflict.diff'));self.resize(1050,700);root=QVBoxLayout(self);root.addWidget(QLabel(f"{conflict.category}: {conflict.subject}",objectName='panelTitle'));views=QHBoxLayout();left=QVBoxLayout();right=QVBoxLayout();left.addWidget(QLabel(f"{conflict.mod_a}\n{conflict.file_a}"));right.addWidget(QLabel(f"{conflict.mod_b}\n{conflict.file_b}"));a=QPlainTextEdit();b=QPlainTextEdit();a.setReadOnly(True);b.setReadOnly(True)
        a_lines=conflict.snippet_a.splitlines();b_lines=conflict.snippet_b.splitlines();matcher=difflib.SequenceMatcher(None,a_lines,b_lines);out_a=[];out_b=[]
        for tag,i1,i2,j1,j2 in matcher.get_opcodes():
            marker='  ' if tag=='equal' else ('~ ' if tag=='replace' else '- ' if tag=='delete' else '+ ')
            out_a.extend(marker+line for line in a_lines[i1:i2]);out_b.extend(marker+line for line in b_lines[j1:j2])
        a.setPlainText('\n'.join(out_a));b.setPlainText('\n'.join(out_b));left.addWidget(a);right.addWidget(b);views.addLayout(left);views.addLayout(right);root.addLayout(views)
