from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ToastNotification(QFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent); self.setObjectName("toastNotification"); self.setFixedSize(440, 96)
        root = QHBoxLayout(self); text = QVBoxLayout(); self.title = QLabel(objectName="successTitle"); self.message = QLabel(objectName="mutedText"); text.addWidget(self.title); text.addWidget(self.message); root.addLayout(text, 1)
        close = QPushButton("×", objectName="linkButton"); close.clicked.connect(self.hide); root.addWidget(close); self.hide()

    def display(self, title: str, message: str) -> None:
        self.title.setText(title); self.message.setText(message)
        parent = self.parentWidget(); self.move((parent.width() - self.width()) // 2, int(parent.height() * .66) - self.height() // 2)
        self.show(); self.raise_(); QTimer.singleShot(5000, self.hide)
