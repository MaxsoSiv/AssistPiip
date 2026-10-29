import threading

import shiboken6
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

from core.llm_provider import LLMClient, LLMError
from ui.translator import translate_request


class _PopupWorker(QObject):
    finished = Signal(object)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            result = {"ok": True, "data": self._fn()}
        except Exception as e:
            result = {"ok": False, "error": e}
        if shiboken6.isValid(self):
            self.finished.emit(result)


def _needs_translation_target(text: str) -> str:
    cyrillic = sum(1 for ch in text if "\u0400" <= ch <= "\u04FF")
    return "en" if cyrillic * 3 > len(text) else "ru"


class SelectionPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._llm = None
        self._worker = None
        self._result_text = ""

        self.setFixedWidth(420)

        card = QFrame()
        card.setObjectName("spotlightCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(8)

        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.PlainText)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(self._body)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self._buttons = {}
        for key, label in (
            ("translate", "Перевести"),
            ("summarize", "Кратко"),
            ("fix", "Исправить"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("secondaryButton")
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._run_action(k))
            btn_row.addWidget(btn)
            self._buttons[key] = btn
        btn_row.addStretch()

        copy_btn = QPushButton("Копировать")
        copy_btn.setObjectName("primaryButton")
        copy_btn.setFixedHeight(28)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        btn_row.addWidget(copy_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("secondaryButton")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        inner.addLayout(btn_row)

        self._status = QLabel("")
        self._status.setStyleSheet("font-size: 11px; color: #8a90a0;")
        inner.addWidget(self._status)

    def set_llm_client(self, client: LLMClient | None):
        self._llm = client
        for key in ("summarize", "fix"):
            self._buttons[key].setEnabled(client is not None)
            if client is None:
                self._buttons[key].setToolTip("Настройте AI-ассистента в настройках")
            else:
                self._buttons[key].setToolTip("")

    def open_with_text(self, text: str):
        preview = text if len(text) <= 600 else text[:600] + "…"
        self._body.setText(preview)
        self._result_text = text
        self._status.setText("")
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = min(max(pos.x() - self.width() // 2, geo.left() + 8), geo.right() - self.width() - 8)
        y = pos.y() + 20
        if y + self.height() > geo.bottom():
            y = pos.y() - 60
        y = max(y, geo.top() + 8)
        self.adjustSize()
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def _run_action(self, key: str):
        if self._worker is not None:
            return
        text = self._result_text.strip()
        if not text:
            return
        self._status.setText("Обрабатываю...")

        if key == "translate":
            target = _needs_translation_target(text)
            self._spawn(lambda: translate_request(text, "auto", target))
        elif key == "summarize":
            self._spawn(lambda: self._llm.chat([
                {"role": "system", "content": "Ты кратко резюмируешь текст. Отвечай на языке текста, 2-4 предложения."},
                {"role": "user", "content": text},
            ])["content"])
        elif key == "fix":
            self._spawn(lambda: self._llm.chat([
                {"role": "system", "content": "Исправь орфографию, пунктуацию и грамматику. Верни только исправленный текст без пояснений, на языке исходного текста."},
                {"role": "user", "content": text},
            ])["content"])

    def _spawn(self, fn):
        self._worker = _PopupWorker(fn, self)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _on_done(self, result):
        self._worker.deleteLater()
        self._worker = None
        if not shiboken6.isValid(self):
            return
        if not result["ok"]:
            error = result["error"]
            if isinstance(error, LLMError):
                self._status.setText(error.user_message)
            else:
                self._status.setText(f"Ошибка: {error}")
            return
        text = str(result["data"]).strip()
        if not text:
            self._status.setText("Пустой результат")
            return
        self._result_text = text
        self._body.setText(text if len(text) <= 600 else text[:600] + "…")
        self._status.setText("")
        self.adjustSize()

    def _copy_result(self):
        if self._result_text:
            QGuiApplication.clipboard().setText(self._result_text)
            self._status.setText("Скопировано в буфер обмена")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowDeactivate and self.isVisible():
            self.close()
        super().changeEvent(event)
