import math
import random

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QGuiApplication, QPainter, QColor, QLinearGradient, QRadialGradient,
    QConicalGradient, QFont, QFontMetricsF, QPen, QBrush
)
from PySide6.QtWidgets import QWidget

from core.utils import APP_VERSION

ACCENT_A = QColor(60, 160, 240)
ACCENT_B = QColor(60, 220, 200)
TITLE = "AssistPiip"
VERSION = "v" + APP_VERSION
HINTS = (
    (700, "Инициализация интерфейса"),
    (1150, "Загрузка команд и заметок"),
    (1600, "Подготовка тем оформления"),
    (2000, "Почти готово"),
)
SKIP_HINT = "клик — пропустить"

STARS = []
_rng = random.Random(20261)
for _i in range(46):
    STARS.append((
        _rng.uniform(0.03, 0.97),
        _rng.uniform(0.05, 0.95),
        _rng.uniform(0.6, 2.2),
        _rng.uniform(0.06, 0.2),
        _rng.uniform(0.0, math.tau),
    ))


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


def _ease_out_elastic(p):
    if p <= 0 or p >= 1:
        return _clamp01(p)
    return 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * (2 * math.pi / 3)) + 1


class SplashScreen(QWidget):
    finished = Signal()

    DURATION = 2700
    FADE_DUR = 420

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 380)
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
        self._title_font.setPixelSize(32)
        self._title_font.setWeight(QFont.Weight.DemiBold)

        self._logo_font = QFont()
        self._logo_font.setFamilies(["Segoe UI Black", "Segoe UI", "Arial"])
        self._logo_font.setPixelSize(56)
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
        cy = 128.0
        bob = 2.5 * math.sin(t / 480.0) if t > 430 else 0.0

        self._paint_backdrop(painter, w, h, t)
        self._paint_stars(painter, w, h, t)
        self._paint_radar(painter, cx, cy + bob, t)
        self._paint_ripples(painter, cx, cy + bob, t)
        self._paint_orbits(painter, cx, cy + bob, t)
        self._paint_satellites(painter, cx, cy + bob, t)
        self._paint_logo(painter, cx, cy + bob, t)
        self._paint_title(painter, cx, t)
        self._paint_tagline(painter, cx, t)
        self._paint_version(painter, cx, t)
        self._paint_progress(painter, w, t)
        self._paint_hint(painter, cx, t)
        self._paint_skip_hint(painter, w, h, t)
        painter.end()

    def _paint_backdrop(self, painter, w, h, t):
        enter = _ease_out_cubic(_phase(t, 0, 300))
        if enter <= 0:
            return

        vignette = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.62)
        c0 = QColor(7, 10, 16)
        c0.setAlphaF(0.86 * enter)
        vignette.setColorAt(0.0, c0)
        c1 = QColor(9, 13, 21)
        c1.setAlphaF(0.7 * enter)
        vignette.setColorAt(0.6, c1)
        c2 = QColor(9, 13, 21)
        c2.setAlphaF(0.28 * enter)
        vignette.setColorAt(1.0, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(vignette))
        painter.drawEllipse(QPointF(w / 2.0, h / 2.0), max(w, h) * 0.62, max(w, h) * 0.62)

        floor = QLinearGradient(0, h - 90, 0, h)
        fc = QColor(ACCENT_A)
        fc.setAlphaF(0.05 * enter)
        floor.setColorAt(0.0, QColor(0, 0, 0, 0))
        floor.setColorAt(1.0, fc)
        painter.setBrush(QBrush(floor))
        painter.drawRect(QRectF(0, h - 90, w, 90))

    def _paint_stars(self, painter, w, h, t):
        enter = _phase(t, 100, 900)
        if enter <= 0:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        for fx, fy, size, speed, seed in STARS:
            twinkle = 0.55 + 0.45 * math.sin(t / 620.0 + seed)
            x = (fx * w + math.sin(t / 2400.0 + seed * 7.0) * 9.0) % w
            y = (fy * h - t * speed * 0.012) % h
            c = QColor(200, 220, 240)
            c.setAlphaF(0.5 * enter * twinkle * min(size / 2.0, 1.0))
            painter.setBrush(c)
            r = size * (0.7 + 0.3 * twinkle)
            painter.drawEllipse(QPointF(x, y), r, r)

    def _paint_radar(self, painter, cx, cy, t):
        enter = _ease_out_cubic(_phase(t, 250, 700))
        if enter <= 0:
            return
        sweep = QConicalGradient(cx, cy, -t / 14.0)
        a0 = QColor(ACCENT_B)
        a0.setAlphaF(0.0)
        sweep.setColorAt(0.0, a0)
        a1 = QColor(ACCENT_B)
        a1.setAlphaF(0.16 * enter)
        sweep.setColorAt(0.86, a1)
        a2 = QColor(ACCENT_B)
        a2.setAlphaF(0.0)
        sweep.setColorAt(1.0, a2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sweep))
        painter.drawEllipse(QPointF(cx, cy), 118, 118)

        ring = QColor(ACCENT_A)
        ring.setAlphaF(0.18 * enter)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(ring, 1))
        painter.drawEllipse(QPointF(cx, cy), 118, 118)

    def _paint_ripples(self, painter, cx, cy, t):
        for ripple_start in (330, 470):
            p = _phase(t, ripple_start, 620)
            if p <= 0 or p >= 1:
                continue
            eased = _ease_out_cubic(p)
            r = 44 + eased * 88
            c = QColor(ACCENT_B)
            c.setAlphaF(0.4 * (1.0 - p))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(c, 2 * (1.0 - p) + 0.5))
            painter.drawEllipse(QPointF(cx, cy), r, r)

    def _paint_orbits(self, painter, cx, cy, t):
        logo_alpha = _ease_out_cubic(_phase(t, 0, 420))
        if logo_alpha <= 0:
            return
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for radius, base_alpha, dash in ((74, 30, True), (86, 18, False)):
            ring = QColor(ACCENT_A)
            ring.setAlphaF(base_alpha / 255.0 * logo_alpha)
            pen = QPen(ring, 1)
            if dash:
                pen.setStyle(Qt.PenStyle.DashLine)
                pen.setDashOffset(t / 60.0)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        arcs = (
            (62, 4.0, 115.0, 150.0, 0.0, ACCENT_B, 0.8),
            (72, 3.0, 70.0, -105.0, 120.0, ACCENT_A, 0.65),
            (86, 2.0, 34.0, 65.0, 250.0, QColor(140, 200, 235), 0.45),
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
            (72, -105.0, 120.0, QColor(170, 220, 245), 2.6, 0.8),
            (86, 65.0, 250.0, QColor(140, 200, 235), 2.0, 0.6),
        )
        for radius, speed, offset, color, size, alpha_f in satellites:
            a = math.radians(offset + speed * (t / 1000.0))
            sx = cx + radius * math.cos(a)
            sy = cy + radius * math.sin(a)

            for k in range(1, 5):
                ta = a - math.radians(k * 8 * speed / 10.0)
                trail = QColor(color)
                trail.setAlphaF(0.4 * logo_alpha * alpha_f / k)
                painter.setBrush(trail)
                painter.drawEllipse(
                    QPointF(cx + radius * math.cos(ta), cy + radius * math.sin(ta)),
                    size * 1.5 / k, size * 1.5 / k,
                )

            halo = QColor(color)
            halo.setAlphaF(0.35 * logo_alpha * alpha_f)
            painter.setBrush(halo)
            painter.drawEllipse(QPointF(sx, sy), size * 1.9, size * 1.9)
            dot = QColor(color)
            dot.setAlphaF(logo_alpha * alpha_f)
            painter.setBrush(dot)
            painter.drawEllipse(QPointF(sx, sy), size, size)

    def _paint_logo(self, painter, cx, cy, t):
        pop = _phase(t, 60, 520)
        if pop <= 0:
            return
        overshoot = _ease_out_back(pop)
        settle = _phase(t, 380, 420)
        settle_alpha = _clamp01(_ease_out_elastic(settle))
        scale = (0.55 + 0.45 * overshoot) * (1.0 + 0.04 * (1.0 - _ease_out_elastic(settle)))
        alpha = _ease_out_cubic(pop)

        side = 98.0 * scale
        rect = QRectF(cx - side / 2, cy - side / 2, side, side)

        shadow = QRadialGradient(cx, cy + side * 0.62, side * 0.7)
        sc = QColor(ACCENT_A)
        sc.setAlphaF(0.22 * alpha * (1.0 - settle_alpha))
        shadow.setColorAt(0, sc)
        sc.setAlphaF(0.0)
        shadow.setColorAt(1, sc)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow))
        painter.drawEllipse(QPointF(cx, cy + side * 0.62), side * 0.7, side * 0.28)

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

        sheen = QLinearGradient(cx, cy - side / 2, cx, cy)
        sh = QColor(255, 255, 255)
        sh.setAlphaF(70 * alpha / 255.0)
        sheen.setColorAt(0.0, sh)
        sh.setAlphaF(0.0)
        sheen.setColorAt(1.0, sh)
        painter.setBrush(QBrush(sheen))
        painter.drawRoundedRect(rect.adjusted(0, 0, 0, -side * 0.35), 26 * scale, 26 * scale)

        painter.setFont(self._logo_font)
        glyph = QColor(16, 20, 26)
        glyph.setAlphaF(alpha)
        painter.setPen(QPen(glyph, 1))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "P")

    def _paint_title(self, painter, cx, t):
        glow_p = _phase(t, 900, 500)
        painter.setFont(self._title_font)
        fm = QFontMetricsF(self._title_font)
        spacing = 1.5
        advances = [fm.horizontalAdvance(ch) for ch in TITLE]
        total = sum(advances) + spacing * (len(TITLE) - 1)
        x = cx - total / 2.0
        baseline = 240.0

        for i, ch in enumerate(TITLE):
            p = _ease_out_cubic(_phase(t, 280 + i * 50, 260))
            if p > 0:
                glow = (0.6 + 0.4 * math.sin(t / 300.0 + i * 0.7)) * _ease_out_cubic(glow_p)
                if glow > 0:
                    gc = QColor(ACCENT_B)
                    gc.setAlphaF(0.35 * glow * p)
                    painter.setPen(QPen(gc, 1))
                    painter.drawText(QPointF(x, baseline), ch)
                c = QColor(233, 239, 246)
                c.setAlphaF(p)
                painter.setPen(QPen(c, 1))
                y = baseline + (1.0 - p) * 8.0
                painter.drawText(QPointF(x, y), ch)
            x += advances[i] + spacing

    def _paint_tagline(self, painter, cx, t):
        p = _ease_out_cubic(_phase(t, 900, 400))
        if p <= 0:
            return
        painter.setFont(self._small_font)
        fm = QFontMetricsF(self._small_font)
        text = "Текстовый ассистент для Windows"
        c = QColor(150, 164, 184)
        c.setAlphaF(0.85 * p)
        painter.setPen(QPen(c, 1))
        painter.drawText(QPointF(cx - fm.horizontalAdvance(text) / 2, 264), text)

    def _paint_version(self, painter, cx, t):
        p = _phase(t, 560, 320)
        if p <= 0:
            return
        painter.setFont(self._small_font)
        fm = QFontMetricsF(self._small_font)
        c = QColor(122, 134, 154)
        c.setAlphaF(_ease_out_cubic(p))
        painter.setPen(QPen(c, 1))
        painter.drawText(QPointF(cx - fm.horizontalAdvance(VERSION) / 2, 288), VERSION)

    def _paint_progress(self, painter, w, t):
        track_w = 240.0
        track = QRectF((w - track_w) / 2.0, 306, track_w, 4)
        painter.setPen(Qt.PenStyle.NoPen)
        bgc = QColor(255, 255, 255)
        bgc.setAlphaF(0.10)
        painter.setBrush(bgc)
        painter.drawRoundedRect(track, 2, 2)

        p = _ease_in_out_cubic(_phase(t, 660, 1500))
        if p <= 0:
            return
        fill_w = track_w * p
        grad = QLinearGradient(track.left() + (t / 6.0) % track_w - track_w, 0,
                               track.left() + (t / 6.0) % track_w, 0)
        grad.setColorAt(0.0, QColor(ACCENT_A))
        grad.setColorAt(0.5, QColor(ACCENT_B))
        grad.setColorAt(1.0, QColor(ACCENT_A))
        painter.setBrush(QBrush(grad))
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
        painter.drawText(QPointF(cx - fm.horizontalAdvance(text) / 2, 336), text)

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
