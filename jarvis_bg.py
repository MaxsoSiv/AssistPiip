import math
from PySide6.QtWidgets import QWidget, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient, QConicalGradient, QBrush


class JarvisBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_anim)

        self._angle = 0
        self._tick_angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1

        self._accent = QColor(43, 108, 176)
        self._base = QColor(15, 17, 21)
        self._accent_override = None

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
        elif theme_name == "purple":
            self._accent = QColor(139, 92, 246)
            self._base = QColor(21, 16, 31)
        elif theme_name == "pink":
            self._accent = QColor(236, 72, 153)
            self._base = QColor(31, 16, 22)
        self.update()

    def set_custom_accent(self, color):
        self._accent_override = QColor(color) if color else None
        self.update()

    def set_blurred(self, blurred):
        if blurred:
            self._blur_effect.setBlurRadius(40)
            self._blur_effect.setEnabled(True)
            self._timer.stop()
        else:
            self._blur_effect.setEnabled(False)
            if not self._timer.isActive():
                self._timer.start(33)
        self.update()

    def start(self):
        if not self._timer.isActive():
            self._timer.start(33)

    def stop(self):
        self._timer.stop()

    def _update_anim(self):
        self._angle = (self._angle + 1) % 360
        self._tick_angle = (self._tick_angle + 0.25) % 360
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

        if self._accent_override:
            self._accent = QColor(self._accent_override)

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        cx, cy = w / 2.0, h / 2.0
        max_r = min(w, h) * 0.8

        self._paint_base(painter, cx, cy, max_r)
        self._paint_sweep(painter, cx, cy, max_r)
        self._paint_rings(painter, cx, cy, max_r)
        self._paint_ticks(painter, cx, cy, max_r)
        self._paint_arcs(painter, cx, cy, max_r)
        self._paint_satellites(painter, cx, cy, max_r)
        painter.end()

    def _paint_base(self, painter, cx, cy, max_r):
        base_c = QColor(self._base)
        base_c.setAlpha(165)
        grad = QRadialGradient(cx, cy, max_r)
        grad.setColorAt(0, base_c)
        base_c.setAlpha(0)
        grad.setColorAt(1, base_c)
        painter.fillRect(self.rect(), QBrush(grad))

    def _paint_sweep(self, painter, cx, cy, max_r):
        accent = QColor(self._accent)
        sweep = QConicalGradient(cx, cy, -self._angle)
        c0 = QColor(accent)
        c0.setAlpha(0)
        sweep.setColorAt(0.0, c0)
        c1 = QColor(accent)
        c1.setAlpha(26)
        sweep.setColorAt(0.88, c1)
        c2 = QColor(accent)
        c2.setAlpha(0)
        sweep.setColorAt(1.0, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sweep))
        painter.drawEllipse(QPointF(cx, cy), max_r * 0.92, max_r * 0.92)

    def _paint_rings(self, painter, cx, cy, max_r):
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

        c3 = QColor(accent)
        c3.setAlpha(40)
        painter.setPen(QPen(c3, 1))
        painter.drawEllipse(QPointF(cx, cy), max_r * 0.78, max_r * 0.78)

    def _paint_ticks(self, painter, cx, cy, max_r):
        accent = QColor(self._accent)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._tick_angle)

        for i in range(48):
            major = (i % 4 == 0)
            t1 = QColor(accent)
            t1.setAlpha(85 if major else 38)
            painter.setPen(QPen(t1, 2 if major else 1))
            r_out = max_r * 0.84
            r_in = r_out - (10 if major else 5)
            a = math.radians(i * 7.5)
            painter.drawLine(
                QPointF(r_in * math.cos(a), r_in * math.sin(a)),
                QPointF(r_out * math.cos(a), r_out * math.sin(a)),
            )
        painter.restore()

    def _paint_arcs(self, painter, cx, cy, max_r):
        accent = QColor(self._accent)
        painter.save()
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

        painter.save()
        painter.rotate(self._angle * 0.7)
        c5 = QColor(accent.lighter(160))
        c5.setAlpha(70)
        pen3 = QPen(c5, 2)
        pen3.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen3)
        rect3 = QRectF(-max_r * 0.9, -max_r * 0.9, max_r * 1.8, max_r * 1.8)
        painter.drawArc(rect3, 100 * 16, 20 * 16)
        painter.restore()
        painter.restore()

    def _paint_satellites(self, painter, cx, cy, max_r):
        accent = QColor(self._accent)
        painter.setPen(Qt.PenStyle.NoPen)

        sats = (
            (0.4, 1.0, 3.2, 150),
            (0.6, -0.62, 2.6, 190),
            (0.78, 0.45, 2.2, 230),
        )
        t = self._angle
        for radius_f, speed, size, offset in sats:
            a = math.radians(offset + t * speed)
            r = max_r * radius_f
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)

            for k in range(1, 5):
                ta = a - math.radians(k * 9 * speed)
                tp = QColor(accent)
                tp.setAlpha(int(50 / k))
                painter.setBrush(tp)
                tr = r
                painter.drawEllipse(
                    QPointF(cx + tr * math.cos(ta), cy + tr * math.sin(ta)),
                    size / k * 0.7, size / k * 0.7,
                )

            halo = QColor(accent)
            halo.setAlpha(60)
            painter.setBrush(halo)
            painter.drawEllipse(QPointF(x, y), size * 2.0, size * 2.0)

            dot = QColor(accent.lighter(130))
            dot.setAlpha(220)
            painter.setBrush(dot)
            painter.drawEllipse(QPointF(x, y), size, size)
