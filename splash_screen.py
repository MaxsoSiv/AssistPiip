import math

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QGuiApplication, QPainter, QColor, QLinearGradient, QRadialGradient,
    QFont, QFontMetricsF, QPen
)
from PySide6.QtWidgets import QWidget

from utils import APP_VERSION

ACCENT_A = QColor(60, 160, 240)
ACCENT_B = QColor(60, 220, 200)
TITLE = "AssistPiip"
VERSION = APP_VERSION
HINTS = (
    (620, "Инициализация интерфейса"),
    (1050, "Загрузка команд и заметок"),
    (1450, "Подготовка тем оформления"),
    (1800, "Почти готово"),
)
SKIP_HINT = "клик — пропустить"


def _clamp01(value):
    return max(0.0, min(1.0, value))


def _phase(t, start, duration):
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return _clamp01((t - start) / duration)


def _ease_out_cubic(p):
    return 1.0 - (1.0 - p) ** 3


def _ease_in_out_cubic(p):
    if p < 0.5:
        return 4.0 * p * p * p
    return 1.0 - ((-2.0 * p + 2.0) ** 3) / 2.0


def _ease_out_back(p):
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (p - 1.0) ** 3 + c1 * (p - 1.0) ** 2


class SplashScreen(QWidget):
    finished = Signal()

    DURATION = 2450
    FADE_DUR = 400

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 326)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        geo = QGuiApplication.primaryScreen().availableGeometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

        self._elapsed = QElapsedTimer()
        self._t = 0
        self._fade_start = self.DURATION - self.FADE_DUR
        self._done = False

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

        self._title_font = QFont()
        self._title_font.setFamilies(["Segoe UI", "Arial"])
        self._title_font.setPixelSize(30)
        self._title_font.setWeight(QFont.Weight.DemiBold)

        self._logo_font = QFont()
        self._logo_font.setFamilies(["Segoe UI Black", "Segoe UI", "Arial"])
        self._logo_font.setPixelSize(52)
        self._logo_font.setWeight(QFont.Weight.Black)

        self._small_font = QFont()
        self._small_font.setFamilies(["Segoe UI", "Arial"])
        self._small_font.setPixelSize(12)

    def start(self):
        self._elapsed.start()
        self.show()
        self.raise_()
        self._timer.start()

    def skip(self):
        if not self._done:
            self._fade_start = min(self._fade_start, self._elapsed.elapsed())

    def mousePressEvent(self, event):
        self.skip()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Space, Qt.Key.Key_Return):
            self.skip()
        else:
            super().keyPressEvent(event)

    def _tick(self):
        t = self._elapsed.elapsed()
        self._t = t
        if t >= self._fade_start:
            fade = _phase(t, self._fade_start, self.FADE_DUR)
            self.setWindowOpacity(1.0 - _ease_in_out_cubic(fade))
            if fade >= 1.0 and not self._done:
                self._done = True
                self._timer.stop()
                self.hide()
                self.finished.emit()
                self.close()
                return
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        t = self._t
        w, h = self.width(), self.height()
        cx = w / 2.0
        cy = 112.0
        bob = 2.5 * math.sin(t / 480.0) if t > 430 else 0.0

        self._paint_background(painter, w, h, t)
        self._paint_glow(painter, cx, cy + bob, t)
        self._paint_orbits(painter, cx, cy + bob, t)
        self._paint_satellites(painter, cx, cy + bob, t)
        self._paint_logo(painter, cx, cy + bob, t)
        self._paint_title(painter, cx, t)
        self._paint_version(painter, cx, t)
        self._paint_progress(painter, w, t)
        self._paint_hint(painter, cx, t)
        self._paint_skip_hint(painter, w, h, t)
        painter.end()

    def _paint_background(self, painter, w, h, t):
        enter = _ease_out_cubic(_phase(t, 0, 200))
        bg = QColor(7, 10, 16)
        bg.setAlphaF(0.94 * enter)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(0, 0, w, h), 18, 18)

        if enter > 0:
            border = QColor(ACCENT_A)
            border.setAlphaF(0.16 * enter)
            painter.setPen(QPen(border, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 18, 18)

    def _paint_glow(self, painter, cx, cy, t):
        logo_alpha = _ease_out_cubic(_phase(t, 0, 420))
        if logo_alpha <= 0:
            return
        pulse = 0.5 + 0.5 * math.sin(t / 380.0)
        glow = QRadialGradient(cx, cy, 130)
        c = QColor(ACCENT_B)
        c.setAlphaF(0.13 * logo_alpha * (0.75 + 0.25 * pulse))
        glow.setColorAt(0, c)
        c.setAlphaF(0.0)
        glow.setColorAt(1, c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy), 130, 130)

    def _paint_orbits(self, painter, cx, cy, t):
        logo_alpha = _ease_out_cubic(_phase(t, 0, 420))
        if logo_alpha <= 0:
            return
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for radius, base_alpha in ((74, 34), (84, 22)):
            ring = QColor(ACCENT_A)
            ring.setAlphaF(base_alpha / 255.0 * logo_alpha)
            painter.setPen(QPen(ring, 1))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        arcs = (
            (62, 4.0, 115.0, 150.0, 0.0, ACCENT_B, 0.75),
            (72, 3.0, 70.0, -105.0, 120.0, ACCENT_A, 0.6),
            (84, 2.0, 34.0, 65.0, 250.0, QColor(140, 200, 235), 0.42),
        )
        for radius, width, span, speed, offset, color, alpha_f in arcs:
            angle = offset + speed * (t / 1000.0)
            c = QColor(color)
            c.setAlphaF(alpha_f * logo_alpha)
            pen = QPen(c, width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            painter.drawArc(rect, int(angle * 16), int(span * 16))

    def _paint_satellites(self, painter, cx, cy, t):
        logo_alpha = _ease_out_cubic(_phase(t, 0, 420))
        if logo_alpha <= 0:
            return
        painter.setPen(Qt.PenStyle.NoPen)

        satellites = (
            (62, 150.0, 0.0, ACCENT_B, 3.4, 0.95),
            (74, -105.0, 120.0, QColor(170, 220, 245), 2.6, 0.8),
            (84, 65.0, 250.0, QColor(140, 200, 235), 2.0, 0.6),
        )
        for radius, speed, offset, color, size, alpha_f in satellites:
            a = math.radians(offset + speed * (t / 1000.0))
            sx = cx + radius * math.cos(a)
            sy = cy + radius * math.sin(a)
            halo = QColor(color)
            halo.setAlphaF(0.35 * logo_alpha * alpha_f)
            painter.setBrush(halo)
            painter.drawEllipse(QPointF(sx, sy), size * 1.9, size * 1.9)
            dot = QColor(color)
            dot.setAlphaF(logo_alpha * alpha_f)
            painter.setBrush(dot)
            painter.drawEllipse(QPointF(sx, sy), size, size)

    def _paint_logo(self, painter, cx, cy, t):
        pop = _phase(t, 30, 470)
        if pop <= 0:
            return
        scale = 0.55 + 0.45 * _ease_out_back(pop)
        alpha = _ease_out_cubic(pop)

        side = 96.0 * scale
        rect = QRectF(cx - side / 2, cy - side / 2, side, side)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        a = QColor(ACCENT_A)
        a.setAlphaF(alpha)
        b = QColor(ACCENT_B)
        b.setAlphaF(alpha)
        grad.setColorAt(0, a)
        grad.setColorAt(1, b)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(rect, 26 * scale, 26 * scale)

        painter.setFont(self._logo_font)
        glyph = QColor(16, 20, 26)
        glyph.setAlphaF(alpha)
        painter.setPen(QPen(glyph, 1))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "P")

    def _paint_title(self, painter, cx, t):
        painter.setFont(self._title_font)
        fm = QFontMetricsF(self._title_font)
        spacing = 1.5
        advances = [fm.horizontalAdvance(ch) for ch in TITLE]
        total = sum(advances) + spacing * (len(TITLE) - 1)
        x = cx - total / 2.0
        baseline = 226.0

        for i, ch in enumerate(TITLE):
            p = _ease_out_cubic(_phase(t, 260 + i * 55, 260))
            if p > 0:
                c = QColor(233, 239, 246)
                c.setAlphaF(p)
                painter.setPen(QPen(c, 1))
                y = baseline + (1.0 - p) * 8.0
                painter.drawText(QPointF(x, y), ch)
            x += advances[i] + spacing

    def _paint_version(self, painter, cx, t):
        p = _phase(t, 520, 320)
        if p <= 0:
            return
        painter.setFont(self._small_font)
        fm = QFontMetricsF(self._small_font)
        c = QColor(122, 134, 154)
        c.setAlphaF(_ease_out_cubic(p))
        painter.setPen(QPen(c, 1))
        painter.drawText(QPointF(cx - fm.horizontalAdvance(VERSION) / 2, 250), VERSION)

    def _paint_progress(self, painter, w, t):
        track_w = 220.0
        track = QRectF((w - track_w) / 2.0, 270, track_w, 4)
        painter.setPen(Qt.PenStyle.NoPen)
        bgc = QColor(255, 255, 255)
        bgc.setAlphaF(0.10)
        painter.setBrush(bgc)
        painter.drawRoundedRect(track, 2, 2)

        p = _ease_in_out_cubic(_phase(t, 620, 1360))
        if p <= 0:
            return
        fill_w = track_w * p
        grad = QLinearGradient(track.left(), 0, track.right(), 0)
        grad.setColorAt(0, QColor(ACCENT_A))
        grad.setColorAt(1, QColor(ACCENT_B))
        painter.setBrush(grad)
        fill = QRectF(track.left(), track.top(), fill_w, track.height())
        painter.drawRoundedRect(fill, 2, 2)

        head = QColor(ACCENT_B)
        head.setAlphaF(0.9)
        painter.setBrush(head)
        painter.drawEllipse(QPointF(fill.right(), track.center().y()), 3.2, 3.2)

    def _paint_hint(self, painter, cx, t):
        current = None
        started = None
        for start, text in HINTS:
            if t >= start:
                current = text
                started = start
        if current is None:
            return

        p = _ease_out_cubic(_phase(t, started, 240))
        fade_at_end = _phase(t, self._fade_start - 150, 300)
        alpha = p * (1.0 - _ease_in_out_cubic(_clamp01(fade_at_end)))
        if alpha <= 0:
            return

        painter.setFont(self._small_font)
        fm = QFontMetricsF(self._small_font)
        text = current + "..."
        c = QColor(122, 134, 154)
        c.setAlphaF(alpha)
        painter.setPen(QPen(c, 1))
        painter.drawText(QPointF(cx - fm.horizontalAdvance(text) / 2, 300), text)

    def _paint_skip_hint(self, painter, w, h, t):
        p = _phase(t, 1100, 400)
        if p <= 0:
            return
        painter.setFont(self._small_font)
        fm = QFontMetricsF(self._small_font)
        c = QColor(90, 100, 118)
        c.setAlphaF(0.8 * _ease_out_cubic(p))
        painter.setPen(QPen(c, 1))
        painter.drawText(QPointF(w - fm.horizontalAdvance(SKIP_HINT) - 14, h - 10), SKIP_HINT)
