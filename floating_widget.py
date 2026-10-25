import math
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QPoint, QPointF, Signal, QDateTime, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient, QFont, QGuiApplication, QAction


class FloatingCircle(QWidget):
    clicked = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None, theme: str = "blue", opacity: float = 0.85):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(72, 72)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.setMouseTracking(True)
        self._theme = theme
        self._opacity = opacity
        self._hover = False
        self._countdown = None
        self._custom_colors = None
        self._drag_pos = QPoint()
        self._press_pos = QPoint()
        self._press_time = 0

        self._pulse_val = 0.0
        self._pulse_dir = 1
        self._orbit_angle = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.start(33)

    def _show_menu(self, pos):
        menu = QMenu(self)
        show_action = QAction("Показать окно", menu)
        show_action.triggered.connect(self.clicked.emit)
        menu.addAction(show_action)
        exit_action = QAction("Выход", menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)
        menu.exec(self.mapToGlobal(pos))

    def clamp_to_screen(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = min(max(self.x(), screen.left()), screen.right() - self.width())
        y = min(max(self.y(), screen.top()), screen.bottom() - self.height())
        self.move(x, y)

    def set_opacity(self, value: float):
        self._opacity = value
        self.update()

    def set_theme(self, theme: str):
        self._theme = theme
        self.update()

    def set_custom_colors(self, c1, c2):
        self._custom_colors = (c1, c2) if c1 is not None else None
        self.update()

    def set_countdown(self, text):
        if text != self._countdown:
            self._countdown = text
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def _update_pulse(self):
        self._pulse_val += 0.04 * self._pulse_dir
        if self._pulse_val >= 1.0:
            self._pulse_val = 1.0
            self._pulse_dir = -1
        elif self._pulse_val <= 0.0:
            self._pulse_val = 0.0
            self._pulse_dir = 1
        self._orbit_angle = (self._orbit_angle + 3.2) % 360
        self.update()

    def _palette(self):
        if self._custom_colors:
            return self._custom_colors
        if self._theme == "green":
            return QColor(40, 200, 80), QColor(150, 240, 60)
        if self._theme == "red":
            return QColor(220, 40, 40), QColor(240, 100, 40)
        if self._theme == "purple":
            return QColor(150, 40, 220), QColor(200, 60, 240)
        if self._theme == "orange":
            return QColor(240, 120, 20), QColor(240, 200, 20)
        if self._theme == "pink":
            return QColor(236, 72, 153), QColor(255, 130, 190)
        if self._theme == "gold":
            return QColor(212, 175, 55), QColor(245, 210, 100)
        return QColor(60, 160, 240), QColor(60, 220, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(min(self._opacity + (0.15 if self._hover else 0.0), 1.0))

        color1, color2 = self._palette()
        cx, cy = 36.0, 36.0

        pulse_color = QColor(color2)
        pulse_color.setAlphaF((1.0 - self._pulse_val) * 0.6)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(pulse_color, 2 + self._pulse_val * 2))
        r = 30 + self._pulse_val * 6
        painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        glow = QRadialGradient(cx, cy, 34)
        gc = QColor(color1)
        gc.setAlphaF(0.35 if self._hover else 0.22)
        glow.setColorAt(0, gc)
        gc2 = QColor(color1)
        gc2.setAlphaF(0.0)
        glow.setColorAt(1, gc2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(int(cx - 34), int(cy - 34), 68, 68)

        orbit_pen = QColor(color2)
        orbit_pen.setAlphaF(0.45)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(orbit_pen, 1))
        painter.drawEllipse(int(cx - 29), int(cy - 29), 58, 58)

        gradient = QLinearGradient(cx - 20, cy - 20, cx + 20, cy + 20)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(int(cx - 22), int(cy - 22), 44, 44)

        inner_ring = QColor(16, 20, 26)
        inner_ring.setAlphaF(0.35)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(inner_ring, 1))
        painter.drawEllipse(int(cx - 18), int(cy - 18), 36, 36)

        sheen = QLinearGradient(cx, cy - 22, cx, cy)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 70))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(sheen))
        painter.drawEllipse(int(cx - 22), int(cy - 22), 44, 30)

        a = math.radians(self._orbit_angle)
        sx = cx + 29 * math.cos(a)
        sy = cy + 29 * math.sin(a)

        trail = QColor(color2)
        painter.setPen(Qt.PenStyle.NoPen)
        for k in range(1, 6):
            ta = a - math.radians(k * 12)
            trail.setAlphaF(0.4 / k)
            painter.setBrush(trail)
            painter.drawEllipse(
                QPointF(cx + 29 * math.cos(ta), cy + 29 * math.sin(ta)),
                2.4 / k * 1.6, 2.4 / k * 1.6,
            )

        sat_halo = QColor(color2)
        sat_halo.setAlphaF(0.5)
        painter.setBrush(sat_halo)
        painter.drawEllipse(QPointF(sx, sy), 4.4, 4.4)
        sat = QColor(255, 255, 255)
        painter.setBrush(sat)
        painter.drawEllipse(QPointF(sx, sy), 2.2, 2.2)

        if self._countdown:
            text_font = QFont()
            text_font.setPointSize(12 if len(self._countdown) <= 5 else 10)
            text_font.setBold(True)
            painter.setFont(text_font)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._countdown)
        else:
            painter.setPen(QPen(QColor(16, 20, 26)))
            font = QFont()
            font.setPointSize(21)
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
            else:
                self.clamp_to_screen()
            event.accept()
