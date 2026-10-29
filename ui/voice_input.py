import shiboken6
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsOpacityEffect
)

from core.voice_recognition import VoiceWorker


class VoicePopup(QWidget):
    insert_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)
        self._worker = None
        self._language = "ru-RU"

        card = QFrame()
        card.setObjectName("spotlightCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(8)

        head = QHBoxLayout()
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #4cc38a; font-size: 18px;")
        self._pulse = QGraphicsOpacityEffect(self._dot)
        self._pulse.setOpacity(1.0)
        self._dot.setGraphicsEffect(self._pulse)
        head.addWidget(self._dot)
        self._title = QLabel("Говорите...")
        self._title.setObjectName("spotlightInput")
        head.addWidget(self._title, 1)
        inner.addLayout(head)

        self._body = QLabel("")
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.PlainText)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._body.hide()
        inner.addWidget(self._body)

        self._status = QLabel("Esc — отмена")
        self._status.setStyleSheet("font-size: 11px; color: #8a90a0;")
        inner.addWidget(self._status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self._insert_btn = QPushButton("В поле ввода")
        self._insert_btn.setObjectName("primaryButton")
        self._insert_btn.setFixedHeight(28)
        self._insert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._insert_btn.clicked.connect(self._insert)
        self._insert_btn.hide()
        btn_row.addWidget(self._insert_btn)

        self._copy_btn = QPushButton("Копировать")
        self._copy_btn.setObjectName("secondaryButton")
        self._copy_btn.setFixedHeight(28)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._copy)
        self._copy_btn.hide()
        btn_row.addWidget(self._copy_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondaryButton")
        close_btn.setFixedHeight(28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        inner.addLayout(btn_row)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(120)
        self._pulse_timer.timeout.connect(self._animate)
        self._pulse_dir = -1

    def _animate(self):
        if not shiboken6.isValid(self._pulse):
            return
        value = self._pulse.opacity() + 0.08 * self._pulse_dir
        if value <= 0.25:
            value = 0.25
            self._pulse_dir = 1
        elif value >= 1.0:
            value = 1.0
            self._pulse_dir = -1
        self._pulse.setOpacity(value)

    def start(self, language: str):
        self._language = language
        self._body.hide()
        self._insert_btn.hide()
        self._copy_btn.hide()
        self._title.setText("Говорите...")
        self._status.setText("Esc — отмена · автоостановка после фразы")
        self._dot.show()
        self._pulse_timer.start()
        self.adjustSize()
        self._place()
        self.show()
        self.raise_()
        self.activateWindow()

        self._worker = VoiceWorker(self)
        self._worker.listening.connect(lambda: None)
        self._worker.finished.connect(self._on_result)
        self._worker.failed.connect(self._on_failed)
        self._worker.start(language)

    def _place(self):
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = min(max(pos.x() - self.width() // 2, geo.left() + 8), geo.right() - self.width() - 8)
        y = pos.y() + 20
        if y + self.height() > geo.bottom():
            y = pos.y() - 80
        self.move(max(x, geo.left() + 8), max(y, geo.top() + 8))

    def _on_result(self, text):
        self._pulse_timer.stop()
        self._dot.setStyleSheet("color: #4cc38a; font-size: 18px;")
        self._pulse.setOpacity(1.0)
        self._title.setText("Распознано")
        self._body.setText(text)
        self._body.show()
        self._insert_btn.show()
        self._copy_btn.show()
        self._status.setText("")
        self.adjustSize()
        self._place()
        self._worker = None

    def _on_failed(self, message):
        self._pulse_timer.stop()
        self._dot.setStyleSheet("color: #e05252; font-size: 18px;")
        self._title.setText("Ошибка")
        self._body.setText(message)
        self._body.show()
        self._status.setText("")
        self.adjustSize()
        self._place()
        self._worker = None

    def _insert(self):
        text = self._body.text().strip()
        if text:
            self.insert_requested.emit(text)
        self.close()

    def _copy(self):
        text = self._body.text().strip()
        if text:
            QGuiApplication.clipboard().setText(text)
            self._status.setText("Скопировано в буфер обмена")

    def cancel(self):
        if self._worker is not None:
            self._worker.ignore_result()
            self._worker = None
        self.close()

    def is_listening(self) -> bool:
        return self._worker is not None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowDeactivate and self.isVisible():
            self.cancel()
        super().changeEvent(event)
