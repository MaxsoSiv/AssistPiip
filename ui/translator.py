import threading
from urllib.parse import quote

import requests
import shiboken6
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTextEdit, QPushButton, QFrame
)

API_URL = "https://translate.googleapis.com/translate_a/single"

LANGS = [
    ("Русский", "ru"),
    ("English", "en"),
    ("Українська", "uk"),
    ("Deutsch", "de"),
    ("Français", "fr"),
    ("Español", "es"),
    ("Italiano", "it"),
    ("Português", "pt"),
    ("Polski", "pl"),
    ("Türkçe", "tr"),
    ("中文", "zh"),
    ("日本語", "ja"),
]


def translate_request(text: str, source: str, target: str) -> dict:
    url = f"{API_URL}?client=gtx&sl={source}&tl={target}&dt=t&q={quote(text)}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    parts = data[0]
    translated = "".join(part[0] for part in parts if part and part[0])
    detected = data[2] if len(data) > 2 and isinstance(data[2], str) else source
    return {"text": translated, "lang": detected}


class TranslationWorker(QObject):
    finished = Signal(object)

    def start(self, text, source, target):
        threading.Thread(target=self._run, args=(text, source, target), daemon=True).start()

    def _run(self, text, source, target):
        try:
            result = translate_request(text, source, target)
        except Exception as e:
            result = {"error": str(e)}
        if shiboken6.isValid(self):
            self.finished.emit(result)


class TranslatorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._last_detected = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Переводчик")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        layout.addWidget(title)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)

        self._source_combo = QComboBox()
        self._source_combo.addItem("Определить автоматически", "auto")
        for name, code in LANGS:
            self._source_combo.addItem(name, code)
        self._source_combo.setCurrentIndex(0)
        lang_row.addWidget(self._source_combo, 1)

        self._swap_btn = QPushButton("⇄")
        self._swap_btn.setObjectName("secondaryButton")
        self._swap_btn.setFixedSize(40, 32)
        self._swap_btn.setToolTip("Поменять языки местами")
        self._swap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._swap_btn.clicked.connect(self._swap_languages)
        lang_row.addWidget(self._swap_btn)

        self._target_combo = QComboBox()
        for name, code in LANGS:
            self._target_combo.addItem(name, code)
        self._target_combo.setCurrentIndex(1)
        lang_row.addWidget(self._target_combo, 1)
        layout.addLayout(lang_row)

        self._source_edit = QTextEdit()
        self._source_edit.setPlaceholderText("Введите текст...")
        self._source_edit.setFixedHeight(110)
        self._source_edit.setAcceptRichText(False)
        layout.addWidget(self._source_edit)

        btn_row = QHBoxLayout()
        self._translate_btn = QPushButton("Перевести")
        self._translate_btn.setObjectName("primaryButton")
        self._translate_btn.setFixedHeight(38)
        self._translate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._translate_btn.clicked.connect(self._translate)
        btn_row.addWidget(self._translate_btn)

        self._copy_btn = QPushButton("Копировать")
        self._copy_btn.setObjectName("secondaryButton")
        self._copy_btn.setFixedHeight(38)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._copy_result)
        btn_row.addWidget(self._copy_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        result_frame = QFrame()
        result_frame.setObjectName("translateResult")
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(12, 10, 12, 10)

        self._lang_label = QLabel("Перевод")
        self._lang_label.setStyleSheet("font-size: 11px; color: #888;")
        result_layout.addWidget(self._lang_label)

        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setFixedHeight(120)
        result_layout.addWidget(self._result_edit)
        layout.addWidget(result_frame)

        layout.addStretch()

    def _swap_languages(self):
        source_idx = self._source_combo.currentIndex()
        if source_idx == 0:
            tgt_code = self._target_combo.currentData()
            tgt_as_src = self._find_source_index(tgt_code) if tgt_code else 0
            detected_idx = self._find_lang_index(self._last_detected) if self._last_detected else -1
            if tgt_as_src and detected_idx > 0:
                self._source_combo.setCurrentIndex(tgt_as_src)
                self._target_combo.setCurrentIndex(detected_idx)
                self._last_detected = ""
        else:
            src_code = self._source_combo.itemData(source_idx)
            tgt_code = self._target_combo.currentData()
            tgt_as_src = self._find_source_index(tgt_code) if tgt_code else 0
            src_as_tgt = self._find_lang_index(src_code) if src_code else -1
            if tgt_as_src and src_as_tgt > 0:
                self._source_combo.setCurrentIndex(tgt_as_src)
                self._target_combo.setCurrentIndex(src_as_tgt)
        text = self._source_edit.toPlainText()
        result = self._result_edit.toPlainText()
        if result:
            self._source_edit.setPlainText(result)
            self._result_edit.clear()

    def _find_lang_index(self, code: str) -> int:
        for i in range(self._target_combo.count()):
            if self._target_combo.itemData(i) == code:
                return i
        return -1

    def _find_source_index(self, code: str) -> int:
        for i in range(1, self._source_combo.count()):
            if self._source_combo.itemData(i) == code:
                return i
        return 0

    def _translate(self):
        text = self._source_edit.toPlainText().strip()
        if not text:
            return
        if self._worker is not None:
            return

        source = self._source_combo.currentData()
        target = self._target_combo.currentData()
        self._translate_btn.setEnabled(False)
        self._lang_label.setText("Перевожу...")

        self._worker = TranslationWorker(self)
        self._worker.finished.connect(self._on_done)
        self._worker.start(text, source, target)

    def _on_done(self, result):
        self._worker.deleteLater()
        self._worker = None
        self._translate_btn.setEnabled(True)

        if "error" in result:
            self._lang_label.setText("Ошибка перевода. Проверьте подключение к интернету.")
            return

        self._result_edit.setPlainText(result["text"])
        lang_code = result.get("lang", "")
        if lang_code and lang_code != "auto":
            self._last_detected = lang_code
        lang_name = self._lang_name(lang_code)
        self._lang_label.setText(f"Перевод{f' · {lang_name}' if lang_name else ''}")

    def _lang_name(self, code: str) -> str:
        for i in range(self._source_combo.count()):
            if self._source_combo.itemData(i) == code:
                return self._source_combo.itemText(i)
        return code

    def _copy_result(self):
        text = self._result_edit.toPlainText().strip()
        if text:
            QGuiApplication.clipboard().setText(text)
            self._copy_btn.setText("Скопировано")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("Копировать"))
