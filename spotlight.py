from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLineEdit, QLabel


class Spotlight(QWidget):
    submitted = Signal(str)

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(640, 90)

        card = QFrame()
        card.setObjectName("spotlightCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 12, 18, 10)
        inner.setSpacing(4)

        self._input = QLineEdit()
        self._input.setObjectName("spotlightInput")
        self._input.setPlaceholderText("Команда для AssistPiip...")
        self._input.returnPressed.connect(self._submit)
        inner.addWidget(self._input)

        hint = QLabel("Enter — выполнить   ·   Esc — закрыть")
        hint.setObjectName("spotlightHint")
        inner.addWidget(hint)

    def _submit(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.hide()
        self.submitted.emit(text)

    def open_at_cursor(self):
        geo = QGuiApplication.primaryScreen().availableGeometry()
        pos = QCursor.pos()
        x = min(max(pos.x() - self.width() // 2, geo.left() + 8), geo.right() - self.width() - 8)
        y = pos.y() + 28
        if y + self.height() > geo.bottom():
            y = pos.y() - self.height() - 10
        y = max(y, geo.top() + 8)
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowDeactivate and self.isVisible():
            self.hide()
        super().changeEvent(event)
