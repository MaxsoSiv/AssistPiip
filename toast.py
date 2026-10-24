from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QColor, QPainter, QPen, QGuiApplication
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame

ACCENTS = {
    "dark": QColor(43, 108, 176),
    "light": QColor(43, 108, 176),
    "ocean": QColor(0, 180, 216),
    "sunset": QColor(252, 163, 17),
}

CARD_BG = QColor(24, 26, 32)


class ToastCard(QFrame):
    closed = Signal(object)

    def __init__(self, title, message, accent, on_snooze=None, parent=None):
        super().__init__(parent)
        self._accent = accent
        self._on_snooze = on_snooze

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(360)
        self.setMouseTracking(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 8, 10)
        root.setSpacing(4)

        head = QHBoxLayout()
        head.setSpacing(8)
        icon = QLabel("⏰" if on_snooze else "✓")
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        head.addWidget(icon)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #e8ebf0; background: transparent;")
        head.addWidget(title_label, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Закрыть")
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #8c94a2; font-size: 13px; }"
            "QPushButton:hover { color: #ff5d5d; }"
        )
        close_btn.clicked.connect(self.dismiss)
        head.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        body = QLabel(message)
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 13px; color: #c3c9d4; background: transparent;")
        root.addWidget(body)

        foot = QHBoxLayout()
        time_label = QLabel(datetime.now().strftime("%d.%m.%Y %H:%M"))
        time_label.setStyleSheet("font-size: 11px; color: #8c94a2; background: transparent;")
        foot.addWidget(time_label)
        foot.addStretch()

        if on_snooze is not None:
            snooze_btn = QPushButton("Отложить на 5 мин")
            snooze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            snooze_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.07);
                    color: {accent.name()};
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 10px;
                    padding: 4px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background: rgba(255, 255, 255, 0.14); }}
            """)
            snooze_btn.clicked.connect(self._snooze)
            foot.addWidget(snooze_btn)
        root.addLayout(foot)

        self.adjustSize()

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self.dismiss)

    def _snooze(self):
        if self._on_snooze:
            self._on_snooze()
        self.dismiss()

    def start_auto_close(self):
        self._auto_timer.start(8000)

    def enterEvent(self, event):
        self._auto_timer.stop()

    def leaveEvent(self, event):
        self._auto_timer.start(2500)

    def show_at(self, x, y):
        self.move(x, y)
        self.setWindowOpacity(0.0)
        self.show()
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(180)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def dismiss(self):
        self._auto_timer.stop()
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(160)
        fade.setStartValue(self.windowOpacity())
        fade.setEndValue(0.0)
        fade.finished.connect(self._finish)
        fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _finish(self):
        self.closed.emit(self)
        self.hide()
        self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        card = QColor(CARD_BG)
        card.setAlpha(246)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(card)
        painter.drawRoundedRect(rect, 12, 12)

        painter.setPen(QPen(self._accent, 3))
        painter.drawLine(1, 8, 1, self.height() - 8)

        border = QColor(255, 255, 255, 26)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 12, 12)
        painter.end()


class ToastManager(QWidget):
    def __init__(self, theme="dark"):
        super().__init__(None)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self._theme = theme
        self._cards = []

    def set_theme(self, theme):
        self._theme = theme

    def show_toast(self, title, message, on_snooze=None):
        accent = ACCENTS.get(self._theme, ACCENTS["dark"])
        card = ToastCard(title, message, accent, on_snooze)
        card.closed.connect(self._on_closed)
        self._cards.append(card)
        self._relayout()
        card.show_at(card.x(), card.y())
        card.start_auto_close()
        return card

    def _on_closed(self, card):
        if card in self._cards:
            self._cards.remove(card)
        self._relayout()

    def _relayout(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        y = screen.top() + 12
        for card in reversed(self._cards):
            x = screen.right() - card.width() - 12
            card.move(x, y)
            y += card.height() + 8
