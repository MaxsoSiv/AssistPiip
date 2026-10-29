import os
import sys
import json
import html
import logging
import shiboken6
import random
import subprocess
import threading
import re
import requests
from datetime import datetime, timedelta
from ctypes import wintypes
import win32con
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QDialog, QFormLayout, QComboBox, QCheckBox, QSlider,
    QFileDialog, QMessageBox, QMenu, QFrame, QGridLayout, QScrollArea,
    QSizePolicy, QSizeGrip, QKeySequenceEdit, QProgressDialog, QColorDialog,
    QInputDialog
)
from PySide6.QtCore import Qt, QBuffer, QIODevice, QObject, QSize, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmapCache, QPixmap, QPainter, QLinearGradient, QColor, QFont, QCursor, QKeySequence

from settings_manager import SettingsManager
from command_manager import CommandManager, Command
from notes_manager import NotesManager, Note
from chat_manager import ChatManager
from clipboard_manager import ClipboardManager, ClipboardEntry
from reminders import ReminderManager, parse_when
from toast import ToastManager
from fuzzy_matcher import FuzzyMatcher
from floating_widget import FloatingCircle
from utils import open_path, open_url, set_always_on_top, get_app_dir, APP_VERSION
import updater
import backup_manager
from hotkey_manager import HotkeyManager, HOTKEY_ID_MAIN, HOTKEY_ID_SPOTLIGHT, HOTKEY_ID_SELECTION
from calculator import CalculatorPage, SafeEvaluator
from monitor_page import MonitorPage
from translator import TranslatorPage
from jarvis_bg import JarvisBackground
from about_dialog import AboutDialog
from theme import THEMES, apply_accent
from chat_view import ChatView
from spotlight import Spotlight
from secrets_store import save_secret, delete_secret, has_secret, load_secret
from llm_provider import LLMClient, LLMError, strip_html
from selection_capture import capture_selection
from selection_popup import SelectionPopup
import autostart as autostart_mod


PAGE_MAIN = 0
PAGE_SETTINGS = 1
PAGE_COMMANDS = 2
PAGE_NOTES = 3
PAGE_CLIPBOARD = 4
PAGE_CALCULATOR = 5
PAGE_MONITOR = 6
PAGE_TRANSLATE = 7
PAGE_COUNT = 8


class _CommandWorker(QObject):
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
            result = {"ok": False, "error": str(e)}
        if shiboken6.isValid(self):
            self.finished.emit(result)


class _AIWorker(QObject):
    delta = Signal(str)
    finished = Signal(object)
    failed = Signal(object)

    def __init__(self, client: LLMClient, messages, parent=None):
        super().__init__(parent)
        self._client = client
        self._messages = messages
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        buffer = []
        try:
            result = self._client.chat(
                self._messages,
                on_delta=self._on_delta_wrapper(buffer),
                cancel=self._cancel,
            )
        except LLMError as e:
            if shiboken6.isValid(self):
                self.failed.emit({"error": e, "partial": "".join(buffer)})
            return
        except Exception as e:
            if shiboken6.isValid(self):
                self.failed.emit({"error": LLMError("network", str(e)), "partial": "".join(buffer)})
            return
        if shiboken6.isValid(self):
            self.finished.emit({"content": result["content"], "usage": result.get("usage")})

    def _on_delta_wrapper(self, buffer):
        def handle(chunk):
            buffer.append(chunk)
            self.delta.emit(chunk)
        return handle


class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsManager, log_signal):
        super().__init__()
        self.settings = settings
        self.log_signal = log_signal
        self._log_history = []
        self.log_signal.new_log.connect(self._on_new_log)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        base = get_app_dir()
        self._icons = {}
        for name in ["main", "settings", "calculator", "notes", "commands", "clipboard", "monitor", "translate",
                     "collapse", "exit", "pin_on", "pin_off", "minimize", "maximize", "close"]:
            path = os.path.join(base, "icons", f"{name}.png")
            if os.path.exists(path):
                self._icons[name] = QIcon(path)

        icon_path = os.path.join(base, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._drag_pos = None
        self._always_on_top = self.settings.always_on_top
        self._last_page_index = PAGE_MAIN

        data_dir = os.path.join(base, "data")
        self.matcher = FuzzyMatcher(threshold=80)
        self.command_manager = CommandManager(settings, data_dir)
        self.notes_manager = NotesManager(data_dir)
        self.chat_manager = ChatManager(data_dir, limit=80)
        self.clipboard_manager = ClipboardManager(data_dir, limit=50)
        self.reminder_manager = ReminderManager(data_dir)
        self.toast_manager = ToastManager(self.settings.theme)
        self.reminder_manager.triggered.connect(self._on_reminder)
        self._clipboard_search_query = ""

        self._floating = None
        self._tray = None
        self._pages_created = set()
        self._page_widgets = {}
        self._placeholders = {}
        self._heavy_pages = {PAGE_SETTINGS, PAGE_COMMANDS, PAGE_NOTES, PAGE_CLIPBOARD, PAGE_CALCULATOR, PAGE_MONITOR, PAGE_TRANSLATE}

        backup_manager.run_backup(data_dir)

        self._build_ui()
        self._connect_signals()
        self._apply_theme()
        self._ensure_page(PAGE_MAIN)
        self._load_chat_history()
        self._apply_opacity(self.settings.window_opacity)
        self._on_nav(PAGE_MAIN)

        if self._always_on_top:
            set_always_on_top(self, True)
            self._pin_btn.setIcon(self._icons.get("pin_on", QIcon()))

        self._update_checker = None
        self._update_downloader = None
        self._net_worker = None
        self._selection_worker = None
        self._ai_worker = None
        self._ai_buffer = ""
        self._ai_flush_timer = QTimer(self)
        self._ai_flush_timer.setInterval(90)
        self._ai_flush_timer.timeout.connect(self._flush_ai_delta)

        self._hotkey = HotkeyManager(self)
        ok, err = self._hotkey.register(HOTKEY_ID_MAIN, self.settings.hotkey)
        if ok:
            logging.info(f"Горячая клавиша: {self.settings.hotkey}")
        else:
            logging.warning(f"Горячая клавиша {self.settings.hotkey} не назначена: {err}")

        ok, err = self._hotkey.register(HOTKEY_ID_SPOTLIGHT, self.settings.spotlight_hotkey)
        if ok:
            logging.info(f"Быстрая команда: {self.settings.spotlight_hotkey}")
        else:
            logging.warning(f"Быстрая команда {self.settings.spotlight_hotkey} не назначена: {err}")

        ok, err = self._hotkey.register(HOTKEY_ID_SELECTION, self.settings.selection_hotkey)
        if ok:
            logging.info(f"Выделенный текст: {self.settings.selection_hotkey}")
        else:
            logging.warning(f"Выделенный текст {self.settings.selection_hotkey} не назначен: {err}")

        self._spotlight = Spotlight(self.settings, self.command_manager, self.notes_manager, self.clipboard_manager)
        self._spotlight.submitted.connect(self._on_spotlight_submit)
        self._spotlight.activated.connect(self._on_spotlight_activated)

        self._selection_popup = SelectionPopup(self)
        self._selection_popup.set_llm_client(self._make_llm_client())

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_circle_countdown)
        self._clock_timer.start()

    def nativeEvent(self, eventType, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == win32con.WM_HOTKEY:
            if msg.wParam == HOTKEY_ID_MAIN:
                self._toggle_via_hotkey()
                return True, 0
            if msg.wParam == HOTKEY_ID_SPOTLIGHT:
                self._toggle_spotlight()
                return True, 0
            if msg.wParam == HOTKEY_ID_SELECTION:
                self._toggle_selection_popup()
                return True, 0
        return super().nativeEvent(eventType, message)

    def _toggle_spotlight(self):
        if self._spotlight.isVisible():
            self._spotlight.hide()
            return
        self._spotlight.open_at_cursor()

    def _on_spotlight_submit(self, text):
        self.execute_command_text(text)

    def _on_spotlight_activated(self, action):
        kind = action.get("kind")
        if kind == "command":
            self.execute_command_text(action.get("payload", ""))
        elif kind == "note":
            note = action.get("payload")
            if note is not None:
                self._restore_from_circle()
                self._on_nav(PAGE_NOTES)
                dlg = NoteDialog(self, note)
                if dlg.exec():
                    updated = dlg.get_note()
                    if updated:
                        self.notes_manager.update_note(note, updated)
        elif kind == "clipboard":
            entry = action.get("payload")
            if entry is not None:
                self.clipboard_manager.copy_entry(entry)
                self.toast_manager.show_toast("Буфер обмена", "Скопировано из истории")

    def _toggle_selection_popup(self):
        if self._selection_popup.isVisible():
            self._selection_popup.close()
            return
        if self._selection_worker is not None:
            return
        self._selection_worker = _CommandWorker(capture_selection, self)
        self._selection_worker.finished.connect(self._on_selection_captured)
        self._selection_worker.start()

    def _on_selection_captured(self, result):
        self._selection_worker.deleteLater()
        self._selection_worker = None
        if not shiboken6.isValid(self):
            return
        if not result["ok"] or not result["data"]:
            self.toast_manager.show_toast("Выделенный текст", "Не удалось захватить выделенный текст")
            return
        self._selection_popup.set_llm_client(self._make_llm_client())
        self._selection_popup.open_with_text(result["data"])

    def _make_llm_client(self) -> LLMClient | None:
        if not self.settings.ai_enabled:
            return None
        key = load_secret("ai_api_key")
        if not key:
            return None
        base_url = self.settings.ai_base_url.strip()
        model = self.settings.ai_model.strip()
        if not base_url or not model:
            return None
        return LLMClient(base_url, key, model)

    def _ai_system_prompt(self) -> str:
        return ("Ты Пип — локальный ассистент в приложении AssistPiip для Windows. "
                "Отвечай кратко, по делу и на языке пользователя. "
                "Не используй HTML и Markdown-разметку — обычный текст.")

    def _start_ai_chat(self, text: str) -> bool:
        client = self._make_llm_client()
        if client is None:
            return False
        if self._ai_worker is not None:
            self._log_chat("assistant", "Подожди, Пип ещё отвечает. Enter — прервать.")
            return True

        history = []
        for m in self.chat_manager.all_messages()[-12:]:
            content = strip_html(m.text)
            if content and m.role in ("user", "assistant"):
                history.append({"role": m.role, "content": content})
        messages = [{"role": "system", "content": self._ai_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": text})

        self._ai_worker = _AIWorker(client, messages, self)
        self._ai_worker.delta.connect(self._on_ai_delta)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.failed.connect(self._on_ai_failed)
        self._ai_buffer = ""
        self._chat_view.stream_reset()
        self._ai_flush_timer.start(90)
        self._input.setPlaceholderText("Пип отвечает... Enter — прервать")
        self._ai_worker.start()
        logging.info(f"AI-запрос: {text[:80]}")
        return True

    def _flush_ai_delta(self):
        if self._ai_buffer and self._ai_worker is not None:
            self._chat_view.stream_append(self._ai_buffer)

    def _on_ai_delta(self, chunk):
        self._ai_buffer += chunk

    def _on_ai_finished(self, result):
        self._ai_flush_timer.stop()
        self._chat_view.stream_append(self._ai_buffer)
        self._chat_view.stream_end()
        content = result["content"].strip()
        usage = result.get("usage")
        if usage:
            logging.info(f"AI usage: {usage}")
        self.chat_manager.add_message("assistant", html.escape(content))
        self._ai_worker.deleteLater()
        self._ai_worker = None
        self._ai_buffer = ""
        self._input.setPlaceholderText(self._input_placeholder_text())
        self._status.setText("Пип ответил")

    def _on_ai_failed(self, payload):
        self._ai_flush_timer.stop()
        error = payload["error"]
        partial = payload.get("partial", "")
        self._chat_view.stream_end()
        if isinstance(error, LLMError):
            message = error.user_message
        else:
            message = str(error)
        shown = partial.strip()
        if shown:
            shown += "\n\n" + message
        else:
            shown = message
        self._chat_view.add_message("assistant", shown)
        self.chat_manager.add_message("assistant", html.escape(shown))
        logging.warning(f"AI-ошибка: {error}")
        self._ai_worker.deleteLater()
        self._ai_worker = None
        self._ai_buffer = ""
        self._input.setPlaceholderText(self._input_placeholder_text())

    def _input_placeholder_text(self) -> str:
        if self.settings.ai_enabled and has_secret("ai_api_key"):
            return "Команда или вопрос Пипу · = 2+2 · заметка · напомни ..."
        return "Введите команду · = 2+2 · заметка · напомни ..."

    def tray_new_note(self):
        dlg = NoteDialog(self)
        if dlg.exec():
            note = dlg.get_note()
            if note:
                self.notes_manager.add_note(note)
                self.toast_manager.show_toast("Заметка", f"Сохранено: {note.title}")

    def tray_reminder(self):
        text, ok = QInputDialog.getText(
            self, "Напоминание",
            "Что и когда: «через 20 минут перерыв» или «в 19:30 позвонить»",
        )
        if not ok:
            return
        text = text.strip()
        if not text:
            return
        parsed = parse_when(text)
        if parsed is None:
            self.toast_manager.show_toast("Напоминание", "Не понял время. Пример: «через 20 минут перерыв»")
            return
        due, label = parsed
        if not label:
            label = "Напоминание"
        self.reminder_manager.add(due, label, "reminder")
        self.toast_manager.show_toast("Напоминание установлено", f"{label} — {due.strftime('%H:%M %d.%m')}")

    def tray_clipboard_copy(self, entry):
        self.clipboard_manager.copy_entry(entry)
        self.toast_manager.show_toast("Буфер обмена", "Скопировано из истории")

    def _update_circle_countdown(self):
        items = self.reminder_manager.pending()
        if items and self._floating and self._floating.isVisible():
            total = max(int((items[0]["due"] - datetime.now()).total_seconds()), 0)
            if total >= 3600:
                text = f"{total // 3600}:{total % 3600 // 60:02d}:{total % 60:02d}"
            else:
                text = f"{total // 60:02d}:{total % 60:02d}"
            self._floating.set_countdown(text)
        elif self._floating:
            self._floating.set_countdown(None)

    def _toggle_via_hotkey(self):
        if self.isVisible() and not self.isMinimized():
            self._minimize_to_circle()
        else:
            self._restore_from_circle()

    def _on_new_log(self, text):
        self._log_history.append(text)
        if len(self._log_history) > 1000:
            self._log_history.pop(0)
        if hasattr(self, "_log_viewer") and shiboken6.isValid(self._log_viewer):
            self._log_viewer.append(text)
            sb = self._log_viewer.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = self._create_title_bar()
        root.addWidget(self._title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = self._create_sidebar()
        body.addWidget(self._sidebar)

        content_widget = QWidget()
        content_widget.setObjectName("pageContainer")
        content_layout = QGridLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._jarvis_bg = JarvisBackground()
        content_layout.addWidget(self._jarvis_bg, 0, 0)

        self._stack = QStackedWidget()
        self._stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        for i in range(PAGE_COUNT):
            ph = QWidget()
            ph.setObjectName("pageContainer")
            self._placeholders[i] = ph
            self._stack.addWidget(ph)

        content_layout.addWidget(self._stack, 0, 0)
        body.addWidget(content_widget, 1)

        root.addLayout(body, 1)

        status_row = QWidget()
        status_row.setObjectName("statusRow")
        status_row.setFixedHeight(24)
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(8, 0, 0, 0)
        status_layout.setSpacing(0)

        self._status = QLabel(random.choice(["Пип крутой", "Пипарик мощь", "Пип готов к работе"]))
        self._status.setObjectName("statusLabel")
        status_layout.addWidget(self._status)

        status_layout.addStretch()
        status_layout.addWidget(QSizeGrip(self), 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        root.addWidget(status_row)

    def _create_title_bar(self) -> QWidget:
        bar = QFrame()
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar.setFixedHeight(46)
        bar.setObjectName("titleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(8)

        base = get_app_dir()
        app_icon_path = os.path.join(base, "app_icon.png")
        if os.path.exists(app_icon_path):
            icon_label = QLabel()
            pix = QIcon(app_icon_path).pixmap(26, 26)
            icon_label.setPixmap(pix)
            layout.addWidget(icon_label)

        title = QLabel("AssistPiip")
        title.setStyleSheet("font-weight:600; font-size:14px;")
        layout.addWidget(title)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("versionLabel")
        layout.addWidget(version_label)

        self._about_btn = QPushButton("?")
        self._about_btn.setObjectName("titleButton")
        self._about_btn.setFixedSize(26, 26)
        self._about_btn.setToolTip("О программе")
        self._about_btn.clicked.connect(self._show_about)
        layout.addWidget(self._about_btn)

        layout.addStretch()

        self._pin_btn = QPushButton()
        self._pin_btn.setObjectName("titleButton")
        self._pin_btn.setFixedSize(34, 34)
        self._pin_btn.setIcon(self._icons.get("pin_off", QIcon()))
        self._pin_btn.setToolTip("Закрепить поверх окон")
        layout.addWidget(self._pin_btn)

        self._min_btn = QPushButton()
        self._min_btn.setObjectName("titleButton")
        self._min_btn.setFixedSize(34, 34)
        self._min_btn.setIcon(self._icons.get("minimize", QIcon()))
        layout.addWidget(self._min_btn)

        self._max_btn = QPushButton()
        self._max_btn.setObjectName("titleButton")
        self._max_btn.setFixedSize(34, 34)
        self._max_btn.setIcon(self._icons.get("maximize", QIcon()))
        layout.addWidget(self._max_btn)

        self._close_btn = QPushButton()
        self._close_btn.setObjectName("titleClose")
        self._close_btn.setFixedSize(34, 34)
        self._close_btn.setIcon(self._icons.get("close", QIcon()))
        layout.addWidget(self._close_btn)

        bar.mousePressEvent = self._title_press
        bar.mouseMoveEvent = self._title_move
        bar.mouseReleaseEvent = self._title_release
        bar.mouseDoubleClickEvent = self._title_double_click

        return bar

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 16, 10, 12)
        layout.setSpacing(4)

        nav_buttons = [
            ("Главное меню", "main", PAGE_MAIN),
            ("Настройки", "settings", PAGE_SETTINGS),
            ("Калькулятор", "calculator", PAGE_CALCULATOR),
            ("Заметки", "notes", PAGE_NOTES),
            ("Команды", "commands", PAGE_COMMANDS),
            ("Буфер обмена", "clipboard", PAGE_CLIPBOARD),
            ("Переводчик", "translate", PAGE_TRANSLATE),
            ("Монитор", "monitor", PAGE_MONITOR),
        ]

        self._nav_buttons = []
        for text, icon_name, index in nav_buttons:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.setIconSize(QSize(18, 18))
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if icon_name in self._icons:
                btn.setIcon(self._icons[icon_name])
            btn.clicked.connect(lambda checked, idx=index: self._on_nav(idx))
            layout.addWidget(btn)
            self._nav_buttons.append((btn, index))

        layout.addStretch()

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("versionLabel")
        layout.addWidget(version_label)

        self._collapse_btn = QPushButton("Свернуть")
        self._collapse_btn.setObjectName("sidebarBottom")
        self._collapse_btn.setFixedHeight(34)
        self._collapse_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.setIcon(self._icons.get("collapse", QIcon()))
        self._collapse_btn.clicked.connect(self._minimize_to_circle)
        layout.addWidget(self._collapse_btn)

        self._exit_btn = QPushButton("Выход")
        self._exit_btn.setObjectName("sidebarExit")
        self._exit_btn.setFixedHeight(34)
        self._exit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._exit_btn.setIcon(self._icons.get("exit", QIcon()))
        self._exit_btn.clicked.connect(self._full_exit)
        layout.addWidget(self._exit_btn)

        return sidebar

    def _create_main_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Чем могу помочь?")
        header.setStyleSheet("font-size:22px; font-weight:600;")
        layout.addWidget(header)

        self._chat_view = ChatView(self.settings)
        layout.addWidget(self._chat_view, 1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setObjectName("commandInput")
        self._input.setPlaceholderText(self._input_placeholder_text())
        self._input.setFixedHeight(44)
        self._input.returnPressed.connect(self._execute_input)
        self._input.setToolTip("Enter — выполнить, стрелки вверх/вниз — история команд")
        input_row.addWidget(self._input, 1)

        self._input_history = []
        self._hist_index = 0

        def input_key_press(event):
            if event.key() == Qt.Key.Key_Up and self._input_history:
                self._hist_index = max(self._hist_index - 1, -len(self._input_history))
                self._input.setText(self._input_history[self._hist_index])
                return
            if event.key() == Qt.Key.Key_Down:
                if not self._input_history:
                    return
                self._hist_index += 1
                if self._hist_index >= 0:
                    self._hist_index = 0
                    self._input.clear()
                else:
                    self._input.setText(self._input_history[self._hist_index])
                return
            QLineEdit.keyPressEvent(self._input, event)

        self._input.keyPressEvent = input_key_press

        run_btn = QPushButton("Выполнить")
        run_btn.setObjectName("primaryButton")
        run_btn.setFixedHeight(44)
        run_btn.clicked.connect(self._execute_input)
        input_row.addWidget(run_btn)
        layout.addLayout(input_row)

        quick_label = QLabel("Быстрые команды")
        quick_label.setStyleSheet("font-size:12px;")
        layout.addWidget(quick_label)

        self._quick_scroll = QScrollArea()
        self._quick_scroll.setObjectName("quickScroll")
        self._quick_scroll.setWidgetResizable(True)
        self._quick_scroll.setFixedHeight(50)
        self._quick_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._quick_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._quick_container = QWidget()
        self._quick_container.setObjectName("quickContainer")
        self._quick_layout = QHBoxLayout(self._quick_container)
        self._quick_layout.setContentsMargins(0, 0, 0, 0)
        self._quick_layout.setSpacing(8)
        self._quick_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._quick_scroll.setWidget(self._quick_container)
        layout.addWidget(self._quick_scroll)

        self._refresh_quick_commands()
        return page

    def _refresh_quick_commands(self):
        if not hasattr(self, "_quick_layout"):
            return
        while self._quick_layout.count():
            item = self._quick_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for trigger in self.settings.quick_commands:
            cmd_widget = QWidget()
            cmd_widget.setObjectName("quickItem")
            cmd_layout = QHBoxLayout(cmd_widget)
            cmd_layout.setContentsMargins(0, 0, 0, 0)
            cmd_layout.setSpacing(2)

            label_map = {
                "__minimize__": "Свернуть",
                "__exit__": "Выход",
                "__help__": "Помощь",
                "айпи": "Айпи",
                "пинг": "Пинг"
            }
            display_text = label_map.get(trigger, trigger)

            btn = QPushButton(display_text)
            btn.setObjectName("quickButton")
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=trigger: self._quick_command(c))

            del_btn = QPushButton("×")
            del_btn.setObjectName("quickDeleteButton")
            del_btn.setFixedSize(22, 22)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setToolTip("Убрать из быстрых")
            del_btn.clicked.connect(lambda checked, c=trigger: self._confirm_remove_quick(c))

            cmd_layout.addWidget(btn)
            cmd_layout.addWidget(del_btn, 0, Qt.AlignmentFlag.AlignTop)

            self._quick_layout.addWidget(cmd_widget)

        add_btn = QPushButton("+")
        add_btn.setObjectName("quickAddButton")
        add_btn.setFixedSize(38, 38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Добавить быструю команду")
        add_btn.clicked.connect(self._show_add_quick_menu)
        self._quick_layout.addWidget(add_btn)

    def _show_add_quick_menu(self):
        menu = QMenu(self)
        current_quick = self.settings.quick_commands

        builtins = [
            ("Браузер", "браузер"),
            ("Проводник", "проводник"),
            ("Заметки", "заметки"),
            ("Айпи", "айпи"),
            ("Пинг", "пинг"),
            ("Свернуть", "__minimize__"),
            ("Выход", "__exit__"),
            ("Помощь", "__help__"),
        ]

        has_items = False
        for label, trigger in builtins:
            if trigger not in current_quick:
                action = menu.addAction(label)
                action.setData(trigger)
                has_items = True

        custom_cmds = self.command_manager.all_commands()
        for cmd in custom_cmds:
            if cmd.trigger not in current_quick:
                action = menu.addAction(f"[Своя] {cmd.trigger}")
                action.setData(cmd.trigger)
                has_items = True

        if not has_items:
            action = menu.addAction("Все команды уже добавлены")
            action.setEnabled(False)

        action = menu.exec(QCursor.pos())
        if action and action.data():
            trigger = action.data()
            current = self.settings.quick_commands
            if trigger not in current:
                current.append(trigger)
                self.settings.quick_commands = current
                self._refresh_quick_commands()

    def _confirm_remove_quick(self, trigger):
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить команду «{trigger}» из быстрого доступа?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            current = self.settings.quick_commands
            if trigger in current:
                current.remove(trigger)
                self.settings.quick_commands = current
                self._refresh_quick_commands()

    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("settingsInner")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Настройки")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light", "ocean", "sunset", "purple", "pink"])
        self._theme_combo.setCurrentText(self.settings.theme)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form.addRow("Тема окна:", self._theme_combo)

        accent_row = QHBoxLayout()
        self._accent_btn = QPushButton("Как в теме")
        self._accent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._accent_btn.clicked.connect(self._on_accent_pick)
        accent_row.addWidget(self._accent_btn)
        accent_reset_btn = QPushButton("Сбросить")
        accent_reset_btn.setObjectName("secondaryButton")
        accent_reset_btn.clicked.connect(self._on_accent_reset)
        accent_row.addWidget(accent_reset_btn)
        accent_row.addStretch()
        form.addRow("Цвет акцента:", accent_row)

        accent_hint = QLabel("Перекрашивает кнопки, фон, уведомления и кружок под выбранный цвет")
        accent_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", accent_hint)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_slider.setValue(int(self.settings.window_opacity * 100))
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        form.addRow("Прозрачность окна:", self._opacity_slider)

        self._circle_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._circle_opacity_slider.setRange(20, 100)
        self._circle_opacity_slider.setValue(int(self.settings.circle_opacity * 100))
        self._circle_opacity_slider.valueChanged.connect(self._on_circle_opacity_changed)
        form.addRow("Прозрачность кружка:", self._circle_opacity_slider)

        self._circle_theme_combo = QComboBox()
        self._circle_theme_combo.addItems(["blue", "green", "red", "purple", "orange", "pink", "gold", "custom"])
        self._circle_theme_combo.setCurrentText(self.settings.circle_theme)
        self._circle_theme_combo.currentTextChanged.connect(self._on_circle_theme_changed)
        form.addRow("Тема кружка:", self._circle_theme_combo)

        browser_row = QHBoxLayout()
        self._browser_path_edit = QLineEdit(self.settings.browser_path)
        self._browser_path_edit.setPlaceholderText("По умолчанию")
        browser_row.addWidget(self._browser_path_edit, 1)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(36)
        browse_btn.clicked.connect(self._browse_browser)
        browser_row.addWidget(browse_btn)
        form.addRow("Путь к браузеру:", browser_row)

        hotkey_row = QHBoxLayout()
        self._hotkey_edit = QKeySequenceEdit(QKeySequence(self.settings.hotkey))
        self._hotkey_edit.setToolTip("Нажмите комбинацию из 2-4 клавиш, например Ctrl+Alt+P.\nПоказать или скрыть окно из любой программы.")
        self._hotkey_edit.editingFinished.connect(self._on_hotkey_changed)
        hotkey_row.addWidget(self._hotkey_edit)
        hotkey_reset_btn = QPushButton("По умолчанию")
        hotkey_reset_btn.setObjectName("secondaryButton")
        hotkey_reset_btn.clicked.connect(self._reset_hotkey)
        hotkey_row.addWidget(hotkey_reset_btn)
        form.addRow("Горячая клавиша:", hotkey_row)

        hotkey_hint = QLabel("Действие: показывает или скрывает окно AssistPiip из любой программы")
        hotkey_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", hotkey_hint)

        spot_row = QHBoxLayout()
        self._spotlight_edit = QKeySequenceEdit(QKeySequence(self.settings.spotlight_hotkey))
        self._spotlight_edit.setToolTip("Например Ctrl+Alt+K")
        self._spotlight_edit.editingFinished.connect(self._on_spotlight_hotkey_changed)
        spot_row.addWidget(self._spotlight_edit)
        spot_reset_btn = QPushButton("По умолчанию")
        spot_reset_btn.setObjectName("secondaryButton")
        spot_reset_btn.clicked.connect(self._reset_spotlight_hotkey)
        spot_row.addWidget(spot_reset_btn)
        form.addRow("Быстрая команда:", spot_row)

        spot_hint = QLabel("Действие: открывает мини-строку у курсора — команда выполняется без открытия окна")
        spot_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", spot_hint)

        sel_row = QHBoxLayout()
        self._selection_hotkey_edit = QKeySequenceEdit(QKeySequence(self.settings.selection_hotkey))
        self._selection_hotkey_edit.setToolTip("Например Ctrl+Alt+T")
        self._selection_hotkey_edit.editingFinished.connect(self._on_selection_hotkey_changed)
        sel_row.addWidget(self._selection_hotkey_edit)
        sel_reset_btn = QPushButton("По умолчанию")
        sel_reset_btn.setObjectName("secondaryButton")
        sel_reset_btn.clicked.connect(self._reset_selection_hotkey)
        sel_row.addWidget(sel_reset_btn)
        form.addRow("Выделенный текст:", sel_row)

        sel_hint = QLabel("Действие: захватывает выделенный в любой программе текст и предлагает перевод и AI-действия")
        sel_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", sel_hint)

        self._ai_check = QCheckBox("AI-ассистент в чате (OpenAI-совместимый провайдер)")
        self._ai_check.setChecked(self.settings.ai_enabled)
        self._ai_check.toggled.connect(self._on_ai_toggled)
        form.addRow("", self._ai_check)

        self._ai_url_edit = QLineEdit(self.settings.ai_base_url)
        self._ai_url_edit.setPlaceholderText("https://api.openai.com/v1")
        self._ai_url_edit.editingFinished.connect(self._on_ai_url_changed)
        form.addRow("Base URL:", self._ai_url_edit)

        self._ai_model_edit = QLineEdit(self.settings.ai_model)
        self._ai_model_edit.setPlaceholderText("имя модели, например gpt-4o-mini")
        self._ai_model_edit.editingFinished.connect(self._on_ai_model_changed)
        form.addRow("Модель:", self._ai_model_edit)

        key_row = QHBoxLayout()
        self._ai_key_edit = QLineEdit()
        self._ai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._ai_key_edit.setPlaceholderText("Ключ сохранён в Credential Manager" if has_secret("ai_api_key") else "Вставьте API-ключ")
        key_save_btn = QPushButton("Сохранить ключ")
        key_save_btn.setObjectName("primaryButton")
        key_save_btn.clicked.connect(self._on_ai_key_save)
        key_delete_btn = QPushButton("Удалить")
        key_delete_btn.setObjectName("secondaryButton")
        key_delete_btn.clicked.connect(self._on_ai_key_delete)
        key_row.addWidget(self._ai_key_edit, 1)
        key_row.addWidget(key_save_btn)
        key_row.addWidget(key_delete_btn)
        form.addRow("API-ключ:", key_row)

        ai_hint = QLabel("Запросы уходят на указанный сервер только когда вы пишете в чат. "
                         "Ключ хранится в Windows Credential Manager и не попадает в логи и конфиги.")
        ai_hint.setStyleSheet("color: #888; font-size: 11px;")
        ai_hint.setWordWrap(True)
        form.addRow("", ai_hint)

        self._updates_check = QCheckBox("Проверять обновления при запуске")
        self._updates_check.setChecked(self.settings.check_updates)
        self._updates_check.toggled.connect(self._on_updates_toggled)
        form.addRow("", self._updates_check)

        update_row = QHBoxLayout()
        self._check_update_btn = QPushButton("Проверить обновления")
        self._check_update_btn.setObjectName("primaryButton")
        self._check_update_btn.clicked.connect(lambda: self._check_updates(True))
        update_row.addWidget(self._check_update_btn)
        update_row.addStretch()
        form.addRow("Обновления:", update_row)

        backup_row = QHBoxLayout()
        export_btn = QPushButton("Экспорт настроек")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self._export_settings)
        backup_row.addWidget(export_btn)
        import_btn = QPushButton("Импорт из файла")
        import_btn.setObjectName("secondaryButton")
        import_btn.clicked.connect(self._import_settings)
        backup_row.addWidget(import_btn)
        backup_row.addStretch()
        form.addRow("Резервная копия:", backup_row)

        self._autostart_check = QCheckBox("Запускать при старте Windows")
        self._autostart_check.setChecked(autostart_mod.is_autostart_enabled())
        self._autostart_check.toggled.connect(self._on_autostart_toggled)
        form.addRow("", self._autostart_check)

        self._dev_mode_check = QCheckBox("Режим разработчика (логи и отладка)")
        self._dev_mode_check.setChecked(self.settings.developer_mode)
        self._dev_mode_check.toggled.connect(self._on_dev_mode_toggled)
        form.addRow("", self._dev_mode_check)

        layout.addLayout(form)
        layout.addStretch()

        dev_on = self.settings.developer_mode

        self._log_label = QLabel("Логи и отладка")
        self._log_label.setStyleSheet("font-weight:600; margin-top: 10px;")
        self._log_label.setVisible(dev_on)
        layout.addWidget(self._log_label)

        self._log_viewer = QTextEdit()
        self._log_viewer.setReadOnly(True)
        self._log_viewer.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        self._log_viewer.setMinimumHeight(150)
        self._log_viewer.setMaximumHeight(250)
        self._log_viewer.setVisible(dev_on)
        if self._log_history:
            self._log_viewer.setPlainText("\n".join(self._log_history))
            sb = self._log_viewer.verticalScrollBar()
            sb.setValue(sb.maximum())
        layout.addWidget(self._log_viewer)

        self._clear_logs_btn = QPushButton("Очистить логи")
        self._clear_logs_btn.setObjectName("dangerButton")
        self._clear_logs_btn.setFixedHeight(32)
        self._clear_logs_btn.setVisible(dev_on)
        self._clear_logs_btn.clicked.connect(self._clear_logs)
        layout.addWidget(self._clear_logs_btn, 0, Qt.AlignmentFlag.AlignRight)

        layout.addStretch()
        return page

    def _clear_logs(self):
        self._log_history.clear()
        if hasattr(self, "_log_viewer") and shiboken6.isValid(self._log_viewer):
            self._log_viewer.clear()
        logging.info("Логи очищены")

    def _on_dev_mode_toggled(self, checked):
        self.settings.developer_mode = checked
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if checked else logging.INFO)

        if hasattr(self, "_log_label") and shiboken6.isValid(self._log_label):
            self._log_label.setVisible(checked)
        if hasattr(self, "_log_viewer") and shiboken6.isValid(self._log_viewer):
            self._log_viewer.setVisible(checked)
        if hasattr(self, "_clear_logs_btn") and shiboken6.isValid(self._clear_logs_btn):
            self._clear_logs_btn.setVisible(checked)

        if checked:
            logging.info("Режим разработчика включен")
        else:
            logging.info("Режим разработчика выключен")

    def _create_commands_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Команды")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        top.addWidget(title)
        top.addStretch()

        add_btn = QPushButton("Новая команда")
        add_btn.setObjectName("primaryButton")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_command_dialog)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self._commands_list = QListWidget()
        self._commands_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._commands_list.customContextMenuRequested.connect(self._command_context_menu)
        layout.addWidget(self._commands_list, 1)

        self._refresh_commands_list()
        return page

    def _create_notes_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Заметки")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        top.addWidget(title)
        top.addStretch()

        add_btn = QPushButton("Добавить заметку")
        add_btn.setObjectName("primaryButton")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_note_dialog)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self._notes_list = QListWidget()
        self._notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._notes_list.customContextMenuRequested.connect(self._note_context_menu)
        self._notes_list.itemDoubleClicked.connect(self._open_note)
        layout.addWidget(self._notes_list, 1)

        self._refresh_notes_list()
        return page

    def _create_clipboard_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Буфер обмена")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        top.addWidget(title)
        top.addStretch()

        clear_btn = QPushButton("Очистить всё")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setFixedHeight(36)
        clear_btn.clicked.connect(self._clear_clipboard)
        top.addWidget(clear_btn)
        layout.addLayout(top)

        self._clipboard_search = QLineEdit()
        self._clipboard_search.setPlaceholderText("Поиск по содержимому или дате (ГГГГ-ММ-ДД)...")
        self._clipboard_search.textChanged.connect(self._on_clipboard_search_changed)
        layout.addWidget(self._clipboard_search)

        self._clipboard_list = QListWidget()
        self._clipboard_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._clipboard_list.customContextMenuRequested.connect(self._clipboard_context_menu)
        self._clipboard_list.itemDoubleClicked.connect(self._view_clipboard_entry)
        layout.addWidget(self._clipboard_list, 1)

        self._refresh_clipboard_list()
        return page

    def _on_clipboard_search_changed(self, text):
        self._clipboard_search_query = text.strip()
        self._refresh_clipboard_list()

    def _create_calculator_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        calc = CalculatorPage()
        layout.addWidget(calc)
        return page

    def _create_monitor_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        monitor = MonitorPage()
        layout.addWidget(monitor)
        return page

    def _create_translate_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageContainer")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        translator = TranslatorPage()
        layout.addWidget(translator)
        return page

    def _ensure_page(self, index: int) -> QWidget:
        if index in self._pages_created:
            return self._page_widgets[index]
        if index == PAGE_MAIN:
            widget = self._create_main_page()
        elif index == PAGE_SETTINGS:
            widget = self._create_settings_page()
        elif index == PAGE_COMMANDS:
            widget = self._create_commands_page()
        elif index == PAGE_NOTES:
            widget = self._create_notes_page()
        elif index == PAGE_CLIPBOARD:
            widget = self._create_clipboard_page()
        elif index == PAGE_CALCULATOR:
            widget = self._create_calculator_page()
        elif index == PAGE_MONITOR:
            widget = self._create_monitor_page()
        elif index == PAGE_TRANSLATE:
            widget = self._create_translate_page()
        else:
            return None
        ph = self._placeholders[index]
        self._stack.removeWidget(ph)
        self._stack.insertWidget(index, widget)
        self._page_widgets[index] = widget
        self._pages_created.add(index)
        return widget

    def _release_heavy_pages(self):
        for index in list(self._heavy_pages):
            if index in self._pages_created:
                real = self._page_widgets.pop(index)
                self._stack.removeWidget(real)
                real.deleteLater()
                self._stack.insertWidget(index, self._placeholders[index])
                self._pages_created.discard(index)
        QPixmapCache.clear()

    def _connect_signals(self):
        self._pin_btn.clicked.connect(self._toggle_pin)
        self._min_btn.clicked.connect(self.showMinimized)
        self._max_btn.clicked.connect(self._toggle_max)
        self._close_btn.clicked.connect(self._full_exit)

        self.settings.theme_changed.connect(self._apply_theme)
        self.settings.opacity_changed.connect(self._apply_opacity)
        self.settings.circle_opacity_changed.connect(self._apply_circle_opacity)
        self.settings.circle_theme_changed.connect(self._apply_circle_theme)

        self.command_manager.commands_changed.connect(self._refresh_commands_list)
        self.notes_manager.notes_changed.connect(self._refresh_notes_list)
        self.clipboard_manager.clipboard_changed.connect(self._refresh_clipboard_list)

    def _load_chat_history(self):
        if not hasattr(self, "_chat_view") or not shiboken6.isValid(self._chat_view):
            return
        self._chat_view.set_theme(self.settings.theme, self.settings.accent_color)
        self._chat_view.clear()
        messages = self.chat_manager.all_messages()
        for msg in messages:
            self._chat_view.add_message(msg.role, msg.text, msg.timestamp)
        if not messages:
            self._chat_view.add_message(
                "assistant",
                "Привет! Я Пип. Введи команду — браузер, заметка, напомни через 20 минут..., "
                "или посчитай: = 2+2*2",
                datetime.now().isoformat(timespec="seconds"),
            )

    def _on_nav(self, index: int):
        for btn, idx in self._nav_buttons:
            btn.setChecked(idx == index)
        if index >= 0:
            self._ensure_page(index)
            self._stack.setCurrentIndex(index)
            self._last_page_index = index

            is_main = (index == PAGE_MAIN)
            self._jarvis_bg.set_blurred(not is_main)

    def _quick_command(self, command: str):
        if command == "__minimize__":
            self._minimize_to_circle()
        elif command == "__exit__":
            self._full_exit()
        elif command == "__help__":
            self._show_help()
        else:
            self._input.setText(command)
            self._execute_input()

    def _execute_input(self):
        text = self._input.text().strip()
        if self._ai_worker is not None:
            self._input.clear()
            self._ai_worker.cancel()
            self._status.setText("Прерываю ответ Пипа...")
            return
        self._input.clear()
        self.execute_command_text(text)

    def execute_command_text(self, text: str):
        if not text:
            return

        if not self._input_history or self._input_history[-1] != text:
            self._input_history.append(text)
            if len(self._input_history) > 50:
                self._input_history.pop(0)
        self._hist_index = 0
        self._log_chat("user", text)
        logging.info(f"Ввод команды: {text}")

        if text.startswith("="):
            self._run_chat_calculator(text[1:].strip())
            return

        if re.match(r"^(?:через|спустя)\s+\d", text.lower()) or re.match(r"^в\s+\d{1,2}[:.]\d{2}\s+\S", text.lower()):
            self._run_delayed_command(text)
            return

        cmd = self.command_manager.find_by_trigger(text)
        if cmd:
            self._log_chat("assistant", f"Выполняю: {cmd.trigger}")
            logging.info(f"Выполнение кастомной команды: {cmd.trigger}")
            self.command_manager.execute_actions(cmd)
            return

        builtin = self._match_builtin(text)
        if builtin:
            self._run_builtin(builtin, text)
            return

        candidates = self._all_command_strings()
        best = self.matcher.best_match(text, candidates)
        if best:
            found = self.command_manager.find_by_trigger(best)
            if found:
                self._log_chat("assistant", f"Нечёткое совпадение: «{html.escape(text)}» → «{html.escape(best)}»")
                logging.info(f"Нечёткое совпадение: {text} -> {best}")
                self.command_manager.execute_actions(found)
                return

        if self._start_ai_chat(text):
            return

        self._log_chat("assistant", f"Команда не распознана: «{html.escape(text)}»")
        logging.warning(f"Команда не распознана: {text}")

    def _run_chat_calculator(self, expr: str):
        if not expr:
            self._log_chat("assistant", "Введите выражение после «=», например <b>= 2+2*2</b> или <b>= sqrt(144)</b>")
            return
        try:
            result = SafeEvaluator.evaluate(expr)
            if isinstance(result, float):
                result = int(result) if result.is_integer() else round(result, 10)
            self._log_chat("assistant", f"<b>{html.escape(expr)}</b> = <b>{result}</b>")
            logging.info(f"Чат-калькулятор: {expr} = {result}")
        except ZeroDivisionError:
            self._log_chat("assistant", "Деление на ноль.")
        except Exception as e:
            self._log_chat("assistant", f"Не смог вычислить: {e}")

    def _run_delayed_command(self, text: str):
        parsed = parse_when(text)
        if parsed is None:
            self._log_chat("assistant", "Не понял время. Пример: «через 30 минут открой браузер»")
            return
        due, command = parsed
        if not command:
            self._log_chat("assistant", "Укажите, что выполнить. Пример: «через 30 минут открой браузер»")
            return
        self.reminder_manager.add(due, command, "delayed")
        self._log_chat("assistant", f"Выполню «{html.escape(command)}» в {due.strftime('%H:%M %d.%m')}")
        logging.info(f"Отложенная команда: {command} на {due}")

    def _all_command_strings(self) -> list[str]:
        result = []
        for cmd in self.command_manager.all_commands():
            result.append(cmd.trigger)
            result.extend(cmd.aliases)
        result.extend([
            "браузер", "browser", "проводник", "explorer",
            "свернуть", "выход", "помощь", "заметки", "напомни", "таймер",
            "айпи", "ip", "пинг", "ping"
        ])
        return result

    def _match_builtin(self, text: str) -> str | None:
        normalized = text.strip().lower()
        builtins = {
            "браузер": ["браузер", "browser", "хром", "chrome", "файрфокс", "firefox", "edge", "опера", "opera"],
            "проводник": ["проводник", "explorer", "папка", "folder", "файлы"],
            "свернуть": ["свернуть", "minimize", "скрыть"],
            "выход": ["выход", "exit", "quit", "закрыть"],
            "помощь": ["помощь", "help", "справка"],
        }
        for key, aliases in builtins.items():
            if normalized in aliases:
                return key

        if normalized.startswith(("айпи", "ip", "ай пи", "ай-пи")):
            return "ip"
        if normalized.startswith(("пинг", "ping")):
            return "ping"
        if normalized.startswith(("заметка", "заметки", "note")):
            return "notes"
        if normalized.startswith(("напомни", "напомнить", "напоминание", "reminder")):
            return "remind"
        if normalized.startswith(("таймер", "timer")):
            return "timer"

        return None

    def _run_builtin(self, key: str, raw_text: str):
        logging.info(f"Выполнение встроенной команды: {key}")

        if key == "ip":
            if self._net_worker is not None:
                self._log_chat("assistant", "Подожди, выполняется предыдущая сетевая команда.")
                return
            self._log_chat("assistant", "Получаю IP-адрес...")
            self._run_net(lambda: requests.get("https://api.ipify.org", timeout=5).text)
            self._net_worker.finished.connect(self._on_ip_done)

        elif key == "ping":
            if self._net_worker is not None:
                self._log_chat("assistant", "Подожди, выполняется предыдущая сетевая команда.")
                return
            parts = raw_text.split()
            host = parts[1] if len(parts) > 1 else "8.8.8.8"
            self._log_chat("assistant", f"Пингую {html.escape(host)}...")
            self._run_net(lambda: self._ping_host(host))
            self._net_worker.finished.connect(self._on_ping_done)

        elif key == "браузер":
            open_url("https://www.google.com", self.settings.browser_path)
            self._log_chat("assistant", "Открываю браузер")
        elif key == "проводник":
            open_path(os.path.expanduser("~"))
            self._log_chat("assistant", "Открываю проводник")
        elif key == "notes":
            rest = raw_text.strip()
            lowered = rest.lower()
            for prefix in ("заметки", "заметка", "notes", "note"):
                if lowered.startswith(prefix):
                    rest = rest[len(prefix):].lstrip(" :,-")
                    break

            if not rest:
                self._on_nav(PAGE_NOTES)
                self._log_chat("assistant", "Открываю заметки. Чтобы создать: «заметка <текст>» или «заметка <текст> | <описание>»")
                return

            if "|" in rest:
                title, body = rest.split("|", 1)
                title, body = title.strip(), body.strip()
            else:
                title, body = rest, ""

            note = Note(title or "Без названия", body)
            self.notes_manager.add_note(note)
            msg = f"Заметка сохранена: «{html.escape(note.title)}»"
            if body:
                msg += f" ({len(body)} симв.)"
            self._log_chat("assistant", msg)
            logging.info(f"Быстрая заметка создана: {note.title}")
        elif key in ("remind", "timer"):
            self._run_reminder_command(key, raw_text)
        elif key == "свернуть":
            self._minimize_to_circle()
        elif key == "выход":
            self._full_exit()
        elif key == "помощь":
            self._show_help()

    def _run_net(self, fn):
        self._net_worker = _CommandWorker(fn, self)
        self._net_worker.start()

    def _finish_net(self):
        if self._net_worker is not None:
            self._net_worker.deleteLater()
            self._net_worker = None

    def _on_ip_done(self, result):
        self._finish_net()
        if result["ok"]:
            self._log_chat("assistant", f"Ваш внешний IP: <b>{html.escape(str(result['data']))}</b>")
        else:
            self._log_chat("assistant", "Не удалось получить IP. Проверьте подключение к интернету.")

    def _ping_host(self, host):
        result = subprocess.run(
            ["ping", "-n", "4", host],
            capture_output=True, text=True, encoding="cp866", errors="replace", timeout=15
        )
        return host, result.stdout or ""

    def _on_ping_done(self, result):
        self._finish_net()
        if not result["ok"]:
            self._log_chat("assistant", f"Ошибка выполнения пинга: {html.escape(str(result['error']))}")
            return

        host, output = result["data"]

        if "100% потерь" in output or "100% loss" in output or "не найден" in output:
            self._log_chat("assistant", f"Узел {html.escape(host)} недоступен (100% потерь).")
            return

        times = re.findall(r"([0-9]+)(?:ms|мс)", output)
        if times:
            values = [int(t) for t in times]
            avg = sum(values) // len(values)
            self._log_chat(
                "assistant",
                f"Пинг {html.escape(host)}:<br>Мин: {min(values)}ms, Сред: {avg}ms, Макс: {max(values)}ms",
            )
        else:
            self._log_chat(
                "assistant",
                f"Пинг {html.escape(host)} завершен, но не удалось распарсить время.<br><pre>{html.escape(output)}</pre>",
            )

    def _show_help(self):
        ai_on = self._make_llm_client() is not None
        ai_line = (
            "AI-ассистент включен: всё, что не похоже на команду, Пип отвечает как чат (Enter во время ответа — прервать).\n"
            if ai_on else
            "AI-ассистент выключен: включите его в настройках, чтобы задавать вопросы в чат.\n"
        )
        QMessageBox.information(
            self, "Помощь",
            "Введите команду в поле ввода.\n"
            "Доступны: браузер, проводник, заметки, напоминания, таймер, свернуть, выход, помощь, айпи, пинг.\n"
            "Быстрая заметка: «заметка купить хлеб» или «заметка купить хлеб | вечером».\n"
            "Напоминания: «напомни через 20 минут купить хлеб», «напомни в 19:30 позвонить».\n"
            "Таймер: «таймер 5 минут», «таймер 30 секунд».\n"
            "Отмена: «таймер отмена», «напомни отмена», «напомни отмена 2» (по номеру из списка).\n"
            "Спотлайт: мини-строка у курсора — ищет команды, заметки и буфер обмена.\n"
            "Выделенный текст: хоткей захватывает выделенное и предлагает перевод и AI-действия.\n"
            + ai_line +
            "Также можно создавать свои команды во вкладке «Команды»."
        )

    def _run_reminder_command(self, key, raw_text):
        kind = "timer" if key == "timer" else "reminder"
        prefixes = ("напоминание", "напомнить", "напомни", "reminder") if kind == "reminder" else ("таймер", "timer")
        lowered = raw_text.lower()
        rest = raw_text
        for prefix in prefixes:
            if lowered.startswith(prefix):
                rest = raw_text[len(prefix):].lstrip(" :,")
                break

        if not rest or rest.lower().startswith(("список", "list")):
            self._list_reminders()
            return

        if rest.lower().startswith(("отмен", "стоп", "сброс")):
            self._cancel_reminders(kind, rest)
            return

        parsed = parse_when(rest)
        if parsed is None and rest.lstrip()[:1].isdigit():
            parsed = parse_when("через " + rest)
        if parsed is None:
            self._log_chat(
                "assistant",
                "Не понял время. Примеры: «напомни через 20 минут купить хлеб», "
                "«напомни в 19:30 позвонить», «таймер 5 минут», «напомни отмена»"
            )
            return

        due, label = parsed
        if not label:
            label = "Таймер" if kind == "timer" else "Напоминание"
        entry = self.reminder_manager.add(due, label, kind)
        title = "Таймер на" if kind == "timer" else "Напомню"
        self._log_chat("assistant", f"{title} {due.strftime('%H:%M %d.%m')}: {html.escape(entry['label'])}")
        logging.info(f"{'Таймер' if kind == 'timer' else 'Напоминание'} установлено: {label} на {due}")

    def _cancel_reminders(self, kind, rest):
        lowered = rest.lower()
        items = self.reminder_manager.pending()

        m = re.search(r"\b(\d+)\b", lowered)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= len(items):
                entry = items[idx - 1]
                self.reminder_manager.cancel(rid=entry["id"])
                self._log_chat("assistant", f"Отменил: «{html.escape(entry['label'])}» ({entry['due'].strftime('%H:%M %d.%m')})")
                logging.info(f"Напоминание отменено: {entry['label']}")
            else:
                self._log_chat("assistant", f"В списке нет напоминания №{idx}. «напомни список» покажет нумерацию.")
            return

        words = lowered.split()
        if words and words[-1].startswith("вс"):
            removed = self.reminder_manager.cancel()
            self._log_chat(
                "assistant",
                f"Отменил всё ({len(removed)} шт.)" if removed else "Активных напоминаний нет",
            )
            return

        removed = self.reminder_manager.cancel(kind=kind)
        what = ("таймер", "таймера", "таймеров") if kind == "timer" else ("напоминание", "напоминания", "напоминаний")
        if removed:
            word = self._plural_ru(len(removed), *what)
            lines = "<br>".join(f"• «{html.escape(r['label'])}» ({r['due'].strftime('%H:%M %d.%m')})" for r in removed)
            self._log_chat("assistant", f"Отменил {len(removed)} {word}:<br>{lines}")
            logging.info(f"Отменены {what[2]}: {len(removed)} шт.")
        else:
            self._log_chat("assistant", f"Активных {what[2]} нет. «напомни список» — посмотреть все.")

    def _plural_ru(self, n: int, one: str, few: str, many: str) -> str:
        n = abs(n) % 100
        if 11 <= n <= 14:
            return many
        d = n % 10
        if d == 1:
            return one
        if 2 <= d <= 4:
            return few
        return many

    def _list_reminders(self):
        items = self.reminder_manager.pending()
        if not items:
            self._log_chat("assistant", "Активных напоминаний нет. Пример: «напомни через 10 минут сделать перерыв»")
            return
        lines = [f"{i}. {html.escape(r['label'])} — {r['due'].strftime('%H:%M %d.%m')} ({r['kind']})" for i, r in enumerate(items, 1)]
        self._log_chat(
            "assistant",
            "Активные напоминания:<br>" + "<br>".join(lines)
            + "<br>Отмена: «напомни отмена 2» — по номеру, «таймер отмена» — все таймеры, «напомни отмена всё» — все подряд",
        )

    def _on_reminder(self, entry):
        QApplication.beep()
        kind = entry.get("kind", "reminder")

        if kind == "delayed":
            self.toast_manager.show_toast("Отложенная команда", entry["label"])
            self._log_chat("assistant", f"Пора выполнять: {entry['label']}")
            self.execute_command_text(entry["label"])
            return

        title = "Таймер завершён" if kind == "timer" else "Напоминание"

        def snooze():
            self.reminder_manager.add(datetime.now() + timedelta(minutes=5), entry["label"], kind)

        self.toast_manager.show_toast(title, entry["label"], on_snooze=snooze)
        self._log_chat("assistant", f"⏰ {title}: {entry['label']}")

    def _minimize_to_circle(self):
        self._last_page_index = self._stack.currentIndex()
        self._release_heavy_pages()
        self._jarvis_bg.stop()
        self.hide()
        if self._floating is None:
            self._floating = FloatingCircle(theme=self.settings.circle_theme, opacity=self.settings.circle_opacity)
            self._floating.clicked.connect(self._restore_from_circle)
            self._floating.exit_requested.connect(self._full_exit)
        self._floating.set_theme(self.settings.circle_theme)
        self._apply_circle_theme(self.settings.circle_theme)
        self._floating.set_opacity(self.settings.circle_opacity)
        self._floating.show()
        self._floating.move(self.cursor().pos())
        self._floating.clamp_to_screen()
        self._update_circle_countdown()
        logging.debug("Свернуто в кружок")

    def _restore_from_circle(self):
        if self._floating:
            self._floating.hide()
        self._jarvis_bg.set_blurred(self._last_page_index != PAGE_MAIN)
        self._ensure_page(self._last_page_index)
        self._stack.setCurrentIndex(self._last_page_index)
        self.showNormal()
        self.activateWindow()
        for btn, idx in self._nav_buttons:
            btn.setChecked(idx == self._last_page_index)
        logging.debug("Восстановлено из кружка")

    def _apply_circle_opacity(self, value: float):
        if self._floating:
            self._floating.set_opacity(value)

    def _apply_circle_theme(self, theme: str):
        if not self._floating:
            return
        if theme == "custom" and self.settings.accent_color:
            c = QColor(self.settings.accent_color)
            self._floating.set_custom_colors(c, c.lighter(140))
        else:
            self._floating.set_custom_colors(None, None)
            self._floating.set_theme(theme)

    def _apply_opacity(self, value: float):
        self.setWindowOpacity(value)

    def _apply_theme(self):
        qss = THEMES.get(self.settings.theme, THEMES["dark"])
        accent = self.settings.accent_color
        if accent:
            qss = apply_accent(qss, self.settings.theme, accent)
        self.setStyleSheet(qss)

        accent_qcolor = QColor(accent) if accent else None
        self.toast_manager.set_theme(self.settings.theme)
        if accent_qcolor:
            self.toast_manager.set_custom_accent(accent_qcolor)

        if hasattr(self, "_jarvis_bg"):
            self._jarvis_bg.set_theme(self.settings.theme)
            if accent_qcolor:
                self._jarvis_bg.set_custom_accent(accent_qcolor)

        self._update_accent_button()
        self._load_chat_history()

    def _update_accent_button(self):
        if not hasattr(self, "_accent_btn") or not shiboken6.isValid(self._accent_btn):
            return
        color = self.settings.accent_color or "#2b6cb0"
        self._accent_btn.setStyleSheet(
            f"QPushButton {{ background: {color}; color: #fff; border: 1px solid rgba(255, 255, 255, 0.2);"
            f" border-radius: 8px; padding: 6px 14px; font-weight: 600; }}"
        )
        self._accent_btn.setText(self.settings.accent_color.upper() if self.settings.accent_color else "Как в теме")

    def _on_theme_changed(self, value: str):
        self.settings.theme = value
        logging.info(f"Тема изменена на: {value}")

    def _on_opacity_changed(self, value: int):
        self.settings.window_opacity = value / 100.0

    def _on_circle_opacity_changed(self, value: int):
        self.settings.circle_opacity = value / 100.0

    def _on_circle_theme_changed(self, value: str):
        self.settings.circle_theme = value

    def _browse_browser(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите исполняемый файл браузера", "C:\\", "Executable (*.exe)")
        if path:
            self._browser_path_edit.setText(path)
            self.settings.browser_path = path
            logging.info(f"Путь к браузеру изменен: {path}")

    def _on_autostart_toggled(self, checked: bool):
        ok = autostart_mod.set_autostart(checked)
        if not ok:
            self._autostart_check.setChecked(not checked)
            QMessageBox.warning(self, "Ошибка", "Не удалось изменить автозапуск")
            logging.error("Не удалось изменить автозапуск")
        else:
            self.settings.autostart = checked
            logging.info(f"Автозапуск: {'вкл' if checked else 'выкл'}")

    def _on_hotkey_changed(self):
        combo = self._hotkey_edit.keySequence().toString()
        if not combo or combo == self.settings.hotkey:
            return
        ok, err = self._hotkey.register(HOTKEY_ID_MAIN, combo)
        if ok:
            self.settings.hotkey = combo
            self._status.setText(f"Горячая клавиша: {combo}")
            logging.info(f"Горячая клавиша изменена: {combo}")
        else:
            QMessageBox.warning(self, "Горячая клавиша", f"Не удалось назначить «{combo}»:\n{err}")
            self._hotkey_edit.setKeySequence(QKeySequence(self.settings.hotkey))

    def _reset_hotkey(self):
        self._hotkey_edit.setKeySequence(QKeySequence("Ctrl+Alt+P"))
        self._on_hotkey_changed()

    def _on_spotlight_hotkey_changed(self):
        combo = self._spotlight_edit.keySequence().toString()
        if not combo or combo == self.settings.spotlight_hotkey:
            return
        ok, err = self._hotkey.register(HOTKEY_ID_SPOTLIGHT, combo)
        if ok:
            self.settings.spotlight_hotkey = combo
            self._status.setText(f"Быстрая команда: {combo}")
            logging.info(f"Быстрая команда изменена: {combo}")
        else:
            QMessageBox.warning(self, "Быстрая команда", f"Не удалось назначить «{combo}»:\n{err}")
            self._spotlight_edit.setKeySequence(QKeySequence(self.settings.spotlight_hotkey))

    def _reset_spotlight_hotkey(self):
        self._spotlight_edit.setKeySequence(QKeySequence("Ctrl+Alt+K"))
        self._on_spotlight_hotkey_changed()

    def _on_selection_hotkey_changed(self):
        combo = self._selection_hotkey_edit.keySequence().toString()
        if not combo or combo == self.settings.selection_hotkey:
            return
        ok, err = self._hotkey.register(HOTKEY_ID_SELECTION, combo)
        if ok:
            self.settings.selection_hotkey = combo
            self._status.setText(f"Выделенный текст: {combo}")
            logging.info(f"Хоткей выделенного текста изменен: {combo}")
        else:
            QMessageBox.warning(self, "Выделенный текст", f"Не удалось назначить «{combo}»:\n{err}")
            self._selection_hotkey_edit.setKeySequence(QKeySequence(self.settings.selection_hotkey))

    def _reset_selection_hotkey(self):
        self._selection_hotkey_edit.setKeySequence(QKeySequence("Ctrl+Alt+T"))
        self._on_selection_hotkey_changed()

    def _on_ai_toggled(self, checked):
        self.settings.ai_enabled = checked
        self._refresh_ai_dependent_ui()
        logging.info(f"AI-ассистент: {'вкл' if checked else 'выкл'}")

    def _on_ai_url_changed(self):
        url = self._ai_url_edit.text().strip().rstrip("/")
        self.settings.ai_base_url = url or "https://api.openai.com/v1"

    def _on_ai_model_changed(self):
        self.settings.ai_model = self._ai_model_edit.text().strip()

    def _on_ai_key_save(self):
        key = self._ai_key_edit.text().strip()
        if not key:
            QMessageBox.information(self, "API-ключ", "Вставьте ключ в поле перед сохранением.")
            return
        if save_secret("ai_api_key", key):
            self._ai_key_edit.clear()
            self._ai_key_edit.setPlaceholderText("Ключ сохранён в Credential Manager")
            self._status.setText("API-ключ сохранён")
            logging.info("API-ключ сохранён в Credential Manager")
        else:
            QMessageBox.warning(self, "API-ключ", "Не удалось сохранить ключ в Credential Manager.")
        self._refresh_ai_dependent_ui()

    def _on_ai_key_delete(self):
        delete_secret("ai_api_key")
        self._ai_key_edit.setPlaceholderText("Вставьте API-ключ")
        self._status.setText("API-ключ удалён")
        logging.info("API-ключ удалён из Credential Manager")
        self._refresh_ai_dependent_ui()

    def _refresh_ai_dependent_ui(self):
        if hasattr(self, "_input") and shiboken6.isValid(self._input):
            self._input.setPlaceholderText(self._input_placeholder_text())
        if hasattr(self, "_selection_popup") and shiboken6.isValid(self._selection_popup):
            self._selection_popup.set_llm_client(self._make_llm_client())

    def _on_accent_pick(self):
        initial = QColor(self.settings.accent_color) if self.settings.accent_color else QColor("#2b6cb0")
        color = QColorDialog.getColor(initial, self, "Выберите цвет акцента")
        if not color.isValid():
            return
        self.settings.accent_color = color.name()
        self._apply_theme()
        logging.info(f"Цвет акцента: {color.name()}")

    def _on_accent_reset(self):
        self.settings.accent_color = ""
        self._apply_theme()
        logging.info("Цвет акцента сброшен")

    def _on_updates_toggled(self, checked: bool):
        self.settings.check_updates = checked

    def _export_settings(self):
        default_path = os.path.join(os.path.expanduser("~"), "assistpiip-backup.json")
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт настроек", default_path, "JSON (*.json)")
        if not path:
            return

        payload = {
            "app": "AssistPiip",
            "version": APP_VERSION,
            "exported": datetime.now().isoformat(timespec="seconds"),
            "settings": {
                "theme": self.settings.theme,
                "window_opacity": self.settings.window_opacity,
                "circle_opacity": self.settings.circle_opacity,
                "circle_theme": self.settings.circle_theme,
                "browser_path": self.settings.browser_path,
                "autostart": self.settings.autostart,
                "developer_mode": self.settings.developer_mode,
                "always_on_top": self.settings.always_on_top,
                "hotkey": self.settings.hotkey,
                "spotlight_hotkey": self.settings.spotlight_hotkey,
                "accent_color": self.settings.accent_color,
                "check_updates": self.settings.check_updates,
                "quick_commands": self.settings.quick_commands,
            },
            "commands": [c.to_dict() for c in self.command_manager.all_commands()],
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "Экспорт", f"Не удалось сохранить файл: {e}")
            return

        self._status.setText(f"Настройки экспортированы: {os.path.basename(path)}")
        logging.info(f"Экспорт настроек и команд: {path}")

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт настроек", os.path.expanduser("~"), "JSON (*.json)")
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            s = payload["settings"]
            commands = [Command.from_dict(c) for c in payload.get("commands", [])]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
            QMessageBox.warning(self, "Импорт", f"Файл повреждён или не подходит: {e}")
            return

        reply = QMessageBox.question(
            self, "Импорт",
            f"Заменить текущие настройки и команды данными из файла?\n"
            f"Экспортировано: {payload.get('exported', '—')} · команд: {len(commands)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.settings.theme = s.get("theme", self.settings.theme)
        self.settings.window_opacity = float(s.get("window_opacity", self.settings.window_opacity))
        self.settings.circle_opacity = float(s.get("circle_opacity", self.settings.circle_opacity))
        self.settings.circle_theme = s.get("circle_theme", self.settings.circle_theme)
        self.settings.accent_color = s.get("accent_color", "")
        self.settings.browser_path = s.get("browser_path", "")
        self.settings.developer_mode = bool(s.get("developer_mode", False))
        self.settings.always_on_top = bool(s.get("always_on_top", False))
        self.settings.check_updates = bool(s.get("check_updates", True))
        if "quick_commands" in s:
            self.settings.quick_commands = list(s["quick_commands"])

        hotkey = s.get("hotkey")
        if hotkey:
            ok, err = self._hotkey.register(HOTKEY_ID_MAIN, hotkey)
            if ok:
                self.settings.hotkey = hotkey
        spot = s.get("spotlight_hotkey")
        if spot:
            ok, err = self._hotkey.register(HOTKEY_ID_SPOTLIGHT, spot)
            if ok:
                self.settings.spotlight_hotkey = spot

        set_always_on_top(self, self.settings.always_on_top)
        self._pin_btn.setIcon(self._icons.get("pin_on" if self.settings.always_on_top else "pin_off", QIcon()))

        if "autostart" in s:
            if autostart_mod.set_autostart(bool(s["autostart"])):
                self.settings.autostart = bool(s["autostart"])

        self.command_manager.import_commands(commands)
        self._sync_settings_widgets()
        if hasattr(self, "_quick_layout"):
            self._refresh_quick_commands()
        self._apply_theme()
        self._apply_opacity(self.settings.window_opacity)
        self._status.setText("Настройки импортированы")
        logging.info(f"Импорт настроек и команд из {path}")

    def _sync_settings_widgets(self):
        if not hasattr(self, "_theme_combo") or not shiboken6.isValid(self._theme_combo):
            return
        self._theme_combo.setCurrentText(self.settings.theme)
        self._opacity_slider.setValue(int(self.settings.window_opacity * 100))
        self._circle_opacity_slider.setValue(int(self.settings.circle_opacity * 100))
        self._circle_theme_combo.setCurrentText(self.settings.circle_theme)
        self._browser_path_edit.setText(self.settings.browser_path)
        self._hotkey_edit.setKeySequence(QKeySequence(self.settings.hotkey))
        self._spotlight_edit.setKeySequence(QKeySequence(self.settings.spotlight_hotkey))
        self._selection_hotkey_edit.setKeySequence(QKeySequence(self.settings.selection_hotkey))
        self._ai_check.setChecked(self.settings.ai_enabled)
        self._ai_url_edit.setText(self.settings.ai_base_url)
        self._ai_model_edit.setText(self.settings.ai_model)
        self._ai_key_edit.setPlaceholderText("Ключ сохранён в Credential Manager" if has_secret("ai_api_key") else "Вставьте API-ключ")
        self._autostart_check.setChecked(autostart_mod.is_autostart_enabled())
        self._updates_check.setChecked(self.settings.check_updates)
        self._dev_mode_check.setChecked(self.settings.developer_mode)

    def _check_updates(self, manual=False):
        if self._update_checker is not None:
            return
        self._update_checker = updater.UpdateChecker(self)
        self._update_checker.finished.connect(lambda info: self._on_update_info(info, manual))
        self._update_checker.start()
        if manual:
            self._status.setText("Проверяю обновления...")

    def _on_update_info(self, info, manual):
        self._update_checker.deleteLater()
        self._update_checker = None
        if manual:
            self._status.setText(random.choice(["Пип готов к работе", "Пипарик мощь", "Пип крутой"]))

        if not info or "error" in info:
            err = info.get("error") if info else "пустой ответ"
            logging.warning(f"Проверка обновлений не удалась: {err}")
            if manual:
                QMessageBox.warning(self, "Обновления", "Не удалось проверить обновления.\nПроверьте подключение к интернету.")
            return

        remote = str(info.get("version", ""))
        if not updater.is_newer(remote, APP_VERSION):
            if manual:
                QMessageBox.information(self, "Обновления", f"У вас последняя версия ({APP_VERSION}).")
            return

        notes = info.get("notes", "")
        url = info.get("file", "")
        expected_sha = str(info.get("sha256", "") or "")

        box = QMessageBox(self)
        box.setWindowTitle("Доступно обновление")
        box.setText(f"Вышла версия {remote} (у вас {APP_VERSION}).")
        box.setInformativeText(notes)

        auto_btn = None
        if getattr(sys, "frozen", False) and url:
            auto_btn = box.addButton("Обновить автоматически", QMessageBox.ButtonRole.AcceptRole)
        page_btn = box.addButton("Открыть страницу скачивания", QMessageBox.ButtonRole.HelpRole)
        box.addButton("Позже", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is auto_btn:
            self._download_update(url, expected_sha)
        elif clicked is page_btn:
            open_url(updater.SITE_URL, self.settings.browser_path)

    def _download_update(self, url, expected_sha=""):
        progress = QProgressDialog("Скачиваю обновление...", None, 0, 0, self)
        progress.setWindowTitle("Обновление")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        self._update_downloader = updater.UpdateDownloader(expected_sha, self)

        def on_done(path):
            progress.close()
            if expected_sha:
                logging.info("SHA-256 архива обновления совпал")
            else:
                logging.warning("SHA-256 в releases.json отсутствует, целостность архива не проверена")
            if updater.apply_update(path, get_app_dir(), os.getpid()):
                self._full_exit()
            else:
                QMessageBox.warning(self, "Обновление", "Архив обновления повреждён.\nСкачайте новую версию с сайта вручную.")

        def on_fail(err):
            progress.close()
            QMessageBox.warning(self, "Обновление", f"Не удалось скачать обновление:\n{err}")

        self._update_downloader.finished.connect(on_done)
        self._update_downloader.failed.connect(on_fail)
        self._update_downloader.start(url)

    def _toggle_pin(self):
        self._always_on_top = not self._always_on_top
        set_always_on_top(self, self._always_on_top)
        if self._always_on_top:
            self._pin_btn.setIcon(self._icons.get("pin_on", QIcon()))
        else:
            self._pin_btn.setIcon(self._icons.get("pin_off", QIcon()))
        self.settings.always_on_top = self._always_on_top

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _full_exit(self):
        logging.info("Выход из приложения")
        if hasattr(self, "_hotkey") and self._hotkey:
            self._hotkey.unregister_all()
        if hasattr(self, "_spotlight") and self._spotlight:
            self._spotlight.close()
        if self._floating:
            self._floating.close()
        if self._tray:
            self._tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _log_chat(self, role: str, text: str):
        self.chat_manager.add_message(role, text)
        if hasattr(self, "_chat_view") and shiboken6.isValid(self._chat_view):
            self._chat_view.add_message(role, text, datetime.now().isoformat(timespec="seconds"))

    def _title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isMaximized():
                self.showNormal()
                pos = event.globalPosition().toPoint()
                self.move(pos.x() - self.width() // 2, max(pos.y() - int(event.position().y()), 0))
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _title_move(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _title_release(self, event):
        self._drag_pos = None

    def _title_double_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_max()

    def _add_command_dialog(self):
        dlg = CommandDialog(self.settings, self)
        if dlg.exec():
            cmd = dlg.get_command()
            if cmd:
                self.command_manager.add_command(cmd)
                logging.info(f"Добавлена команда: {cmd.trigger}")

    def _refresh_commands_list(self):
        if not hasattr(self, "_commands_list") or not shiboken6.isValid(self._commands_list):
            return
        self._commands_list.clear()
        for cmd in self.command_manager.all_commands():
            item = QListWidgetItem()
            widget = QWidget()
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            widget.setMinimumHeight(70)
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(12, 8, 12, 8)

            left = QVBoxLayout()
            lbl_trigger = QLabel(cmd.trigger)
            lbl_trigger.setStyleSheet("font-weight: bold; font-size: 14px; color: #ddd;")
            lbl_trigger.setWordWrap(True)
            left.addWidget(lbl_trigger)
            if cmd.aliases:
                lbl_aliases = QLabel(", ".join(cmd.aliases))
                lbl_aliases.setStyleSheet("color: #888; font-size: 12px;")
                lbl_aliases.setWordWrap(True)
                left.addWidget(lbl_aliases)
            left.addStretch()
            layout.addLayout(left)

            layout.addStretch()

            right = QVBoxLayout()
            right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            for act in cmd.actions:
                act_type = act.get("type")
                val = str(act.get("value", ""))
                if len(val) > 40:
                    val = val[:37] + "..."
                lbl_act = QLabel(f"[{act_type}] {val}")
                lbl_act.setStyleSheet("color: #aaa; font-size: 12px;")
                lbl_act.setWordWrap(True)
                right.addWidget(lbl_act, 0, Qt.AlignmentFlag.AlignRight)
            layout.addLayout(right)

            item.setSizeHint(widget.sizeHint())
            self._commands_list.addItem(item)
            self._commands_list.setItemWidget(item, widget)

    def _command_context_menu(self, pos):
        if not hasattr(self, "_commands_list") or not shiboken6.isValid(self._commands_list):
            return
        item = self._commands_list.itemAt(pos)
        if not item:
            return

        idx = self._commands_list.row(item)
        cmd = self.command_manager.all_commands()[idx]
        trigger = cmd.trigger

        menu = QMenu(self)
        edit_action = menu.addAction("Изменить")

        if trigger in self.settings.quick_commands:
            quick_action = menu.addAction("Удалить из быстрых")
        else:
            quick_action = menu.addAction("Добавить в быстрые")

        delete_action = menu.addAction("Удалить")

        action = menu.exec(self._commands_list.mapToGlobal(pos))

        if action == edit_action:
            dlg = CommandDialog(self.settings, self, edit_cmd=cmd)
            if dlg.exec():
                new_cmd = dlg.get_command()
                if new_cmd:
                    self.command_manager.remove_command(trigger)
                    self.command_manager.add_command(new_cmd)
                    if trigger in self.settings.quick_commands:
                        self.settings.quick_commands = [new_cmd.trigger if x == trigger else x for x in self.settings.quick_commands]
                        self._refresh_quick_commands()
        elif action == quick_action:
            current = self.settings.quick_commands
            if trigger in current:
                current.remove(trigger)
            else:
                current.append(trigger)
            self.settings.quick_commands = current
            self._refresh_quick_commands()
            logging.info(f"Изменены быстрые команды: {self.settings.quick_commands}")
        elif action == delete_action:
            self.command_manager.remove_command(trigger)
            if trigger in self.settings.quick_commands:
                self.settings.quick_commands = [x for x in self.settings.quick_commands if x != trigger]
                self._refresh_quick_commands()
            logging.info(f"Удалена команда: {trigger}")

    def _add_note_dialog(self):
        dlg = NoteDialog(self)
        if dlg.exec():
            note = dlg.get_note()
            if note:
                self.notes_manager.add_note(note)
                logging.info(f"Добавлена заметка: {note.title}")

    def _refresh_notes_list(self):
        if not hasattr(self, "_notes_list") or not shiboken6.isValid(self._notes_list):
            return
        self._notes_list.clear()
        for note in self.notes_manager.all_notes():
            prefix = "PIN " if note.pinned else ""
            item = QListWidgetItem(f"{prefix}{note.title}\n{note.created}")
            item.setData(Qt.ItemDataRole.UserRole, note)
            self._notes_list.addItem(item)

    def _note_context_menu(self, pos):
        if not hasattr(self, "_notes_list") or not shiboken6.isValid(self._notes_list):
            return
        item = self._notes_list.itemAt(pos)
        if not item:
            return
        note = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        open_action = menu.addAction("Открыть")
        pin_action = menu.addAction("Открепить" if note.pinned else "Закрепить")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self._notes_list.mapToGlobal(pos))
        if action == open_action:
            self._open_note(item)
        elif action == pin_action:
            self.notes_manager.toggle_pin(note)
        elif action == delete_action:
            self.notes_manager.remove_note(note)
            logging.info(f"Удалена заметка: {note.title}")

    def _open_note(self, item):
        note = item.data(Qt.ItemDataRole.UserRole)
        dlg = NoteDialog(self, note)
        if dlg.exec():
            updated = dlg.get_note()
            if updated:
                self.notes_manager.update_note(note, updated)

    def _refresh_clipboard_list(self):
        if not hasattr(self, "_clipboard_list") or not shiboken6.isValid(self._clipboard_list):
            return
        self._clipboard_list.clear()
        for entry in self.clipboard_manager.all_entries():
            if self._clipboard_search_query:
                q = self._clipboard_search_query.lower()
                haystack = entry.content if entry.kind == "text" else os.path.basename(entry.content)
                if q not in entry.created.lower() and q not in haystack.lower():
                    continue

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, entry)

            if entry.kind == "text":
                preview = entry.content[:60].replace("\n", " ")
                item.setText(f"TXT {preview}\n{entry.created}")
                self._clipboard_list.addItem(item)
            else:
                widget = QWidget()
                widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(8, 8, 8, 8)

                lbl_text = QLabel(f"IMG {os.path.basename(entry.content)}\n{entry.created}")
                lbl_text.setStyleSheet("color: #888; font-size: 12px;")
                lbl_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                lbl_img = QLabel()
                pix = QPixmap(entry.content)
                if not pix.isNull():
                    pix = pix.scaled(400, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    lbl_img.setPixmap(pix)
                    lbl_img.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

                layout.addWidget(lbl_text)
                layout.addStretch()
                layout.addWidget(lbl_img)

                item.setSizeHint(widget.sizeHint())
                self._clipboard_list.addItem(item)
                self._clipboard_list.setItemWidget(item, widget)

    def _clipboard_context_menu(self, pos):
        if not hasattr(self, "_clipboard_list") or not shiboken6.isValid(self._clipboard_list):
            return
        item = self._clipboard_list.itemAt(pos)
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        pin_action = menu.addAction("Открепить" if entry.pinned else "📌 Закрепить")
        view_action = menu.addAction("Просмотреть")
        copy_action = menu.addAction("Скопировать обратно")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self._clipboard_list.mapToGlobal(pos))
        if action == pin_action:
            self.clipboard_manager.toggle_pin(entry)
        elif action == view_action:
            self._view_clipboard_entry(item)
        elif action == copy_action:
            self.clipboard_manager.copy_entry(entry)
            logging.debug("Скопировано из истории буфера")
        elif action == delete_action:
            self.clipboard_manager.remove_entry(entry)

    def _view_clipboard_entry(self, item):
        entry = item.data(Qt.ItemDataRole.UserRole)
        dlg = ClipboardViewerDialog(entry, self)
        dlg.exec()

    def _clear_clipboard(self):
        if QMessageBox.question(self, "Очистить", "Удалить всю историю буфера обмена?") == QMessageBox.StandardButton.Yes:
            self.clipboard_manager.clear_all()
            logging.info("История буфера обмена очищена")


class ClipboardViewerDialog(QDialog):
    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр")
        self.resize(600, 500)
        layout = QVBoxLayout(self)

        if entry.kind == "text":
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(entry.content)
            layout.addWidget(text_edit)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            label = QLabel()
            pixmap = QPixmap(entry.content)
            if not pixmap.isNull():
                label.setPixmap(pixmap)
            else:
                label.setText("Не удалось загрузить изображение")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll.setWidget(label)
            layout.addWidget(scroll)

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)


class CommandDialog(QDialog):
    def __init__(self, settings, parent=None, edit_cmd=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Редактировать команду" if edit_cmd else "Новая команда")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._trigger = QLineEdit()
        form.addRow("Триггер:", self._trigger)

        self._aliases = QLineEdit()
        self._aliases.setPlaceholderText("через запятую")
        form.addRow("Алиасы:", self._aliases)

        self._case_check = QCheckBox("Учитывать регистр")
        form.addRow("", self._case_check)

        layout.addLayout(form)

        actions_label = QLabel("Действия (до 10). Тип script запускает .bat/.cmd/.ps1/.py скрыто, без окна консоли")
        actions_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(actions_label)

        self._actions_container = QVBoxLayout()
        layout.addLayout(self._actions_container)

        self._actions = []
        add_action_btn = QPushButton("+ Добавить действие")
        add_action_btn.clicked.connect(self._add_action_row)
        layout.addWidget(add_action_btn)

        buttons = QHBoxLayout()
        ok = QPushButton("Сохранить")
        ok.setObjectName("primaryButton")
        ok.clicked.connect(self._on_ok)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        if edit_cmd:
            self._trigger.setText(edit_cmd.trigger)
            self._aliases.setText(", ".join(edit_cmd.aliases))
            self._case_check.setChecked(edit_cmd.case_sensitive)
            for act in edit_cmd.actions:
                self._add_action_row(act.get("type", "url"), act.get("value", ""))
        else:
            self._add_action_row()

    def _add_action_row(self, act_type=None, act_val=None):
        if len(self._actions) >= 10:
            return
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        type_combo = QComboBox()
        type_combo.addItems(["url", "app", "file", "script"])
        if act_type:
            type_combo.setCurrentText(act_type)

        value_edit = QLineEdit()
        if type_combo.currentText() == "script":
            value_edit.setPlaceholderText("Путь к .bat / .cmd / .ps1 / .py")
        else:
            value_edit.setPlaceholderText("URL или путь")
        if act_val:
            value_edit.setText(act_val)

        def on_type_changed(text):
            value_edit.setPlaceholderText("Путь к .bat / .cmd / .ps1 / .py" if text == "script" else "URL или путь")

        type_combo.currentTextChanged.connect(on_type_changed)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(32)

        def browse():
            if type_combo.currentText() == "script":
                path, _ = QFileDialog.getOpenFileName(self, "Выберите скрипт", "C:\\", "Скрипты (*.bat *.cmd *.ps1 *.py);;Все файлы (*.*)")
            else:
                path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
            if path:
                value_edit.setText(path)

        browse_btn.clicked.connect(browse)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(28)

        row_layout.addWidget(type_combo)
        row_layout.addWidget(value_edit, 1)
        row_layout.addWidget(browse_btn)
        row_layout.addWidget(remove_btn)

        self._actions_container.addWidget(row)
        self._actions.append((row, type_combo, value_edit))

        def remove():
            row.setParent(None)
            self._actions.remove((row, type_combo, value_edit))

        remove_btn.clicked.connect(remove)

    def _on_ok(self):
        if not self._trigger.text().strip():
            QMessageBox.warning(self, "Ошибка", "Триггер не может быть пустым")
            return
        if not any(value_edit.text().strip() for _, _, value_edit in self._actions):
            QMessageBox.warning(self, "Ошибка", "Заполните хотя бы одно действие")
            return
        self.accept()

    def get_command(self) -> Command | None:
        trigger = self._trigger.text().strip()
        aliases = [a.strip() for a in self._aliases.text().split(",") if a.strip()]
        actions = []
        for _, type_combo, value_edit in self._actions:
            value = value_edit.text().strip()
            if value:
                actions.append({"type": type_combo.currentText(), "value": value})
        if not trigger or not actions:
            return None
        return Command(trigger, aliases, actions, self._case_check.isChecked())


class NoteDialog(QDialog):
    def __init__(self, parent=None, note: Note = None):
        super().__init__(parent)
        self.setWindowTitle("Заметка")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)

        self._title = QLineEdit()
        self._title.setPlaceholderText("Заголовок")
        if note:
            self._title.setText(note.title)
        layout.addWidget(self._title)

        self._body = QTextEdit()
        self._body.setPlaceholderText("Текст заметки...")
        if note:
            self._body.setPlainText(note.body)
        layout.addWidget(self._body, 1)

        buttons = QHBoxLayout()
        ok = QPushButton("Сохранить")
        ok.setObjectName("primaryButton")
        ok.clicked.connect(self._on_ok)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        self._note = note

    def _on_ok(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "Ошибка", "Заголовок не может быть пустым")
            return
        self.accept()

    def get_note(self) -> Note | None:
        title = self._title.text().strip()
        body = self._body.toPlainText().strip()
        if not title:
            return None
        if self._note:
            return Note(title, body, self._note.pinned, self._note.created, self._note.id)
        return Note(title, body)
