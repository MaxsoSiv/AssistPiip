import math
from PySide6.QtWidgets import QWidget, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush


class JarvisBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_anim)

        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1

        self._accent = QColor(43, 108, 176)
        self._base = QColor(15, 17, 21)

        self._blur_effect = QGraphicsBlurEffect(self)
        self._blur_effect.setBlurRadius(0)
        self._blur_effect.setEnabled(False)
        self.setGraphicsEffect(self._blur_effect)

        self._timer.start(33)

    def set_theme(self, theme_name):
        if theme_name == "dark":
            self._accent = QColor(43, 108, 176)
            self._base = QColor(15, 17, 21)
        elif theme_name == "light":
            self._accent = QColor(43, 108, 176)
            self._base = QColor(232, 234, 237)
        elif theme_name == "ocean":
            self._accent = QColor(0, 180, 216)
            self._base = QColor(10, 25, 47)
        elif theme_name == "sunset":
            self._accent = QColor(252, 163, 17)
            self._base = QColor(43, 13, 13)
        self.update()

    def set_blurred(self, blurred):
        if blurred:
            self._blur_effect.setBlurRadius(40)
            self._blur_effect.setEnabled(True)
        else:
            self._blur_effect.setEnabled(False)
        self.update()

    def start(self):
        if not self._timer.isActive():
            self._timer.start(33)

    def stop(self):
        self._timer.stop()

    def _update_anim(self):
        self._angle = (self._angle + 1) % 360
        self._pulse += 0.015 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        cx, cy = w / 2.0, h / 2.0
        max_r = min(w, h) * 0.8

        base_c = QColor(self._base)
        base_c.setAlpha(165)
        grad = QRadialGradient(cx, cy, max_r)
        grad.setColorAt(0, base_c)
        base_c.setAlpha(0)
        grad.setColorAt(1, base_c)
        painter.fillRect(self.rect(), grad)

        accent = QColor(self._accent)

        c1 = QColor(accent)
        c1.setAlpha(70)
        painter.setPen(QPen(c1, 2))
        painter.drawEllipse(QPointF(cx, cy), max_r * 0.4, max_r * 0.4)

        c2 = QColor(accent)
        c2.setAlpha(int(90 + 155 * self._pulse))
        painter.setPen(QPen(c2, 1.5))
        r2 = max_r * 0.6 + self._pulse * 25
        painter.drawEllipse(QPointF(cx, cy), r2, r2)

        painter.translate(cx, cy)

        painter.save()
        painter.rotate(self._angle)
        c3 = QColor(accent)
        c3.setAlpha(135)
        pen1 = QPen(c3, 8)
        pen1.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen1)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect1 = QRectF(-max_r * 0.7, -max_r * 0.7, max_r * 1.4, max_r * 1.4)
        painter.drawArc(rect1, 0, 50 * 16)
        painter.restore()

        painter.save()
        painter.rotate(-self._angle * 1.5)
        c4 = QColor(accent.lighter(130))
        c4.setAlpha(105)
        pen2 = QPen(c4, 4)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        rect2 = QRectF(-max_r * 0.5, -max_r * 0.5, max_r * 1.0, max_r * 1.0)
        painter.drawArc(rect2, 180 * 16, 30 * 16)
        painter.restore()

        painter.end()
