from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, Signal, QDateTime, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QFont


class FloatingCircle(QWidget):
    clicked = Signal()

    def __init__(self, parent=None, theme: str = "blue", opacity: float = 0.85):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(64, 64)
        self._theme = theme
        self._opacity = opacity
        self._drag_pos = QPoint()
        self._press_pos = QPoint()
        self._press_time = 0

        self._pulse_val = 0.0
        self._pulse_dir = 1
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.start(50)

    def set_opacity(self, value: float):
        self._opacity = value
        self.update()

    def set_theme(self, theme: str):
        self._theme = theme
        self.update()

    def _update_pulse(self):
        self._pulse_val += 0.05 * self._pulse_dir
        if self._pulse_val >= 1.0:
            self._pulse_val = 1.0
            self._pulse_dir = -1
        elif self._pulse_val <= 0.0:
            self._pulse_val = 0.0
            self._pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)

        color1 = QColor(60, 160, 240)
        color2 = QColor(60, 220, 200)

        if self._theme == "green":
            color1, color2 = QColor(40, 200, 80), QColor(150, 240, 60)
        elif self._theme == "red":
            color1, color2 = QColor(220, 40, 40), QColor(240, 100, 40)
        elif self._theme == "purple":
            color1, color2 = QColor(150, 40, 220), QColor(200, 60, 240)
        elif self._theme == "orange":
            color1, color2 = QColor(240, 120, 20), QColor(240, 200, 20)

        pulse_color = QColor(color2)
        pulse_color.setAlphaF((1.0 - self._pulse_val) * 0.6)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(pulse_color, 2 + self._pulse_val * 2))
        r = 28 + self._pulse_val * 6
        painter.drawEllipse(32 - r, 32 - r, int(r * 2), int(r * 2))

        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(6, 6, 52, 52)

        painter.setPen(QPen(Qt.GlobalColor.white))
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "P")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._press_time = QDateTime.currentMSecsSinceEpoch()
            self._drag_pos = self._press_pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            elapsed = QDateTime.currentMSecsSinceEpoch() - self._press_time
            moved = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if elapsed < 250 and moved < 5:
                self.clicked.emit()
            event.accept()
