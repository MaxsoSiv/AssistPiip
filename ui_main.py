import os
import logging
import shiboken6
import random
import base64
import subprocess
import re
import requests
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QDialog, QFormLayout, QComboBox, QCheckBox, QSlider,
    QFileDialog, QMessageBox, QMenu, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QBuffer, QIODevice, QSize
from PySide6.QtGui import QIcon, QPixmapCache, QPixmap, QPainter, QLinearGradient, QColor, QFont, QCursor

from settings_manager import SettingsManager
from command_manager import CommandManager, Command
from notes_manager import NotesManager, Note
from chat_manager import ChatManager
from clipboard_manager import ClipboardManager, ClipboardEntry
from fuzzy_matcher import FuzzyMatcher
from floating_widget import FloatingCircle
from utils import open_path, open_url, set_always_on_top, get_app_dir
from calculator import CalculatorPage
from monitor_page import MonitorPage
from jarvis_bg import JarvisBackground
from about_dialog import AboutDialog
from theme import THEMES
import autostart as autostart_mod


PAGE_MAIN = 0
PAGE_SETTINGS = 1
PAGE_COMMANDS = 2
PAGE_NOTES = 3
PAGE_CLIPBOARD = 4
PAGE_CALCULATOR = 5
PAGE_MONITOR = 6
PAGE_COUNT = 7


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
        for name in ["main", "settings", "calculator", "notes", "commands", "clipboard", "monitor",
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
        self._clipboard_search_query = ""

        self._floating = None
        self._tray = None
        self._pages_created = set()
        self._page_widgets = {}
        self._placeholders = {}
        self._heavy_pages = {PAGE_SETTINGS, PAGE_COMMANDS, PAGE_NOTES, PAGE_CLIPBOARD, PAGE_CALCULATOR, PAGE_MONITOR}

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

        self._status = QLabel(random.choice(["Пип крутой", "Пипарик мощь", "Пип готов к работе"]))
        self._status.setObjectName("statusLabel")
        self._status.setFixedHeight(24)
        root.addWidget(self._status)

    def _create_title_bar(self) -> QWidget:
        bar = QFrame()
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar.setFixedHeight(40)
        bar.setObjectName("titleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        base = get_app_dir()
        app_icon_path = os.path.join(base, "app_icon.png")
        if os.path.exists(app_icon_path):
            icon_label = QLabel()
            pix = QIcon(app_icon_path).pixmap(24, 24)
            icon_label.setPixmap(pix)
            layout.addWidget(icon_label)

        title = QLabel("AssistPiip")
        title.setStyleSheet("font-weight:600; font-size:14px;")
        layout.addWidget(title)

        self._about_btn = QPushButton("?")
        self._about_btn.setObjectName("titleButton")
        self._about_btn.setFixedSize(24, 24)
        self._about_btn.setStyleSheet("font-weight: bold; font-size: 16px; color: #aaa;")
        self._about_btn.setToolTip("О программе")
        self._about_btn.clicked.connect(self._show_about)
        layout.addWidget(self._about_btn)

        layout.addStretch()

        self._pin_btn = QPushButton()
        self._pin_btn.setObjectName("titleButton")
        self._pin_btn.setFixedSize(32, 32)
        self._pin_btn.setIcon(self._icons.get("pin_off", QIcon()))
        self._pin_btn.setToolTip("Закрепить поверх окон")
        layout.addWidget(self._pin_btn)

        self._min_btn = QPushButton()
        self._min_btn.setObjectName("titleButton")
        self._min_btn.setFixedSize(32, 32)
        self._min_btn.setIcon(self._icons.get("minimize", QIcon()))
        layout.addWidget(self._min_btn)

        self._max_btn = QPushButton()
        self._max_btn.setObjectName("titleButton")
        self._max_btn.setFixedSize(32, 32)
        self._max_btn.setIcon(self._icons.get("maximize", QIcon()))
        layout.addWidget(self._max_btn)

        self._close_btn = QPushButton()
        self._close_btn.setObjectName("titleClose")
        self._close_btn.setFixedSize(32, 32)
        self._close_btn.setIcon(self._icons.get("close", QIcon()))
        layout.addWidget(self._close_btn)

        bar.mousePressEvent = self._title_press
        bar.mouseMoveEvent = self._title_move
        bar.mouseReleaseEvent = self._title_release

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
            ("Монитор", "monitor", PAGE_MONITOR),
        ]

        self._nav_buttons = []
        for text, icon_name, index in nav_buttons:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            if icon_name in self._icons:
                btn.setIcon(self._icons[icon_name])
            btn.clicked.connect(lambda checked, idx=index: self._on_nav(idx))
            layout.addWidget(btn)
            self._nav_buttons.append((btn, index))

        layout.addStretch()

        self._collapse_btn = QPushButton("Свернуть")
        self._collapse_btn.setObjectName("sidebarBottom")
        self._collapse_btn.setFixedHeight(34)
        self._collapse_btn.setIcon(self._icons.get("collapse", QIcon()))
        self._collapse_btn.clicked.connect(self._minimize_to_circle)
        layout.addWidget(self._collapse_btn)

        self._exit_btn = QPushButton("Выход")
        self._exit_btn.setObjectName("sidebarExit")
        self._exit_btn.setFixedHeight(34)
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

        self._chat_view = QTextEdit()
        self._chat_view.setObjectName("chatView")
        self._chat_view.setReadOnly(True)
        layout.addWidget(self._chat_view, 1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setObjectName("commandInput")
        self._input.setPlaceholderText("Введите команду...")
        self._input.setFixedHeight(44)
        self._input.returnPressed.connect(self._execute_input)
        input_row.addWidget(self._input, 1)

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
        self._quick_scroll.setWidgetResizable(True)
        self._quick_scroll.setFixedHeight(50)
        self._quick_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._quick_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._quick_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._quick_container = QWidget()
        self._quick_container.setStyleSheet("background: transparent;")
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
            cmd_widget.setStyleSheet("background: transparent;")
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
            btn.clicked.connect(lambda checked, c=trigger: self._quick_command(c))

            del_btn = QPushButton("×")
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #aaa;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { color: #ff4d4d; }
            """)
            del_btn.clicked.connect(lambda checked, c=trigger: self._confirm_remove_quick(c))

            cmd_layout.addWidget(btn)
            cmd_layout.addWidget(del_btn, 0, Qt.AlignmentFlag.AlignTop)

            self._quick_layout.addWidget(cmd_widget)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 36)
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(43, 45, 49, 0.5);
                color: #ddd;
                border: 1px dashed #555;
                border-radius: 18px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background: #3a3d42; }
        """)
        add_btn.setToolTip("Добавить быструю команду")
        add_btn.clicked.connect(self._show_add_quick_menu)
        self._quick_layout.addWidget(add_btn)

    def _show_add_quick_menu(self):
        menu = QMenu(self)
        current_quick = self.settings.quick_commands

        builtins = [
            ("Браузер", "браузер"),
            ("Проводник", "проводник"),
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
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Настройки")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light", "ocean", "sunset"])
        self._theme_combo.setCurrentText(self.settings.theme)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form.addRow("Тема окна:", self._theme_combo)

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
        self._circle_theme_combo.addItems(["blue", "green", "red", "purple", "orange"])
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
        self._clipboard_search.setPlaceholderText("Поиск по дате (ГГГГ-ММ-ДД)...")
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

    def _get_avatar_html(self, role):
        is_assistant = (role == "assistant")
        text = "P" if is_assistant else "Вы"

        pix = QPixmap(48, 48)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, 48, 48)
        if self.settings.theme == "dark":
            if is_assistant:
                grad.setColorAt(0.0, QColor(43, 108, 176))
                grad.setColorAt(1.0, QColor(0, 180, 216))
            else:
                grad.setColorAt(0.0, QColor(252, 163, 17))
                grad.setColorAt(1.0, QColor(255, 107, 107))
        elif self.settings.theme == "light":
            if is_assistant:
                grad.setColorAt(0.0, QColor(43, 108, 176))
                grad.setColorAt(1.0, QColor(0, 180, 216))
            else:
                grad.setColorAt(0.0, QColor(252, 163, 17))
                grad.setColorAt(1.0, QColor(255, 107, 107))
        elif self.settings.theme == "ocean":
            if is_assistant:
                grad.setColorAt(0.0, QColor(0, 119, 182))
                grad.setColorAt(1.0, QColor(0, 180, 216))
            else:
                grad.setColorAt(0.0, QColor(255, 183, 3))
                grad.setColorAt(1.0, QColor(251, 133, 0))
        elif self.settings.theme == "sunset":
            if is_assistant:
                grad.setColorAt(0.0, QColor(252, 163, 17))
                grad.setColorAt(1.0, QColor(255, 107, 107))
            else:
                grad.setColorAt(0.0, QColor(255, 107, 107))
                grad.setColorAt(1.0, QColor(252, 163, 17))

        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 48, 48)

        painter.setPen(QColor("white"))
        font = QFont("Arial", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()

        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pix.save(buffer, "PNG")
        b64 = base64.b64encode(buffer.data().data()).decode('utf-8')

        return f'<img src="data:image/png;base64,{b64}" width="32" height="32" style="border-radius: 16px; float: left; margin-right: 8px; margin-bottom: 4px;">'

    def _load_chat_history(self):
        if not hasattr(self, "_chat_view") or not shiboken6.isValid(self._chat_view):
            return
        self._chat_view.clear()
        for msg in self.chat_manager.all_messages():
            prefix = "AssistPiip" if msg.role == "assistant" else "Вы"
            avatar = self._get_avatar_html(msg.role)
            color = "#2b6cb0" if msg.role == "assistant" else "#e67e22"
            html = f"""
            <div style="margin-bottom: 12px;">
                {avatar}
                <div style="margin-left: 40px;">
                    <b style="color: {color};">{prefix}</b> <span style="color: #888; font-size: 11px;">{msg.timestamp}</span><br>
                    <span>{msg.text}</span>
                </div>
            </div>
            """
            self._chat_view.append(html)
        sb = self._chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

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
        if not text:
            return

        self._input.clear()
        self._log_chat("user", text)
        logging.info(f"Ввод команды: {text}")

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
                self._log_chat("assistant", f"Нечёткое совпадение: «{text}» → «{best}»")
                logging.info(f"Нечёткое совпадение: {text} -> {best}")
                self.command_manager.execute_actions(found)
                return

        self._log_chat("assistant", f"Команда не распознана: «{text}»")
        logging.warning(f"Команда не распознана: {text}")

    def _all_command_strings(self) -> list[str]:
        result = []
        for cmd in self.command_manager.all_commands():
            result.append(cmd.trigger)
            result.extend(cmd.aliases)
        result.extend([
            "браузер", "browser", "проводник", "explorer",
            "свернуть", "выход", "помощь",
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

        return None

    def _run_builtin(self, key: str, raw_text: str):
        logging.info(f"Выполнение встроенной команды: {key}")

        if key == "ip":
            self._log_chat("assistant", "Получаю IP-адрес...")
            try:
                ip = requests.get("https://api.ipify.org", timeout=5).text
                self._log_chat("assistant", f"Ваш внешний IP: <b>{ip}</b>")
            except requests.RequestException:
                self._log_chat("assistant", "Не удалось получить IP. Проверьте подключение к интернету.")

        elif key == "ping":
            parts = raw_text.split()
            host = parts[1] if len(parts) > 1 else "8.8.8.8"

            self._log_chat("assistant", f"Пингую {host}...")
            try:
                result = subprocess.run(
                    ["ping", "-n", "4", host],
                    capture_output=True, text=True, encoding="cp866", timeout=5
                )
                output = result.stdout

                if "100% потерь" in output or "100% loss" in output or "не найден" in output:
                    self._log_chat("assistant", f"Узел {host} недоступен (100% потерь).")
                else:
                    times = re.findall(r"([0-9]+)(?:ms|мс)", output)
                    if times:
                        times = [int(t) for t in times]
                        avg = sum(times) // len(times)
                        mn = min(times)
                        mx = max(times)
                        self._log_chat("assistant", f"Пинг {host}:<br>Мин: {mn}ms, Сред: {avg}ms, Макс: {mx}ms")
                    else:
                        self._log_chat("assistant", f"Пинг {host} завершен, но не удалось распарсить время.<br><pre>{output}</pre>")
            except subprocess.TimeoutExpired:
                self._log_chat("assistant", f"Превышено время ожидания ответа от {host}.")
            except Exception as e:
                self._log_chat("assistant", f"Ошибка выполнения пинга: {e}")

        elif key == "браузер":
            open_url("https://www.google.com", self.settings.browser_path)
            self._log_chat("assistant", "Открываю браузер")
        elif key == "проводник":
            open_path(os.path.expanduser("~"))
            self._log_chat("assistant", "Открываю проводник")
        elif key == "свернуть":
            self._minimize_to_circle()
        elif key == "выход":
            self._full_exit()
        elif key == "помощь":
            self._show_help()

    def _show_help(self):
        QMessageBox.information(
            self, "Помощь",
            "Введите команду в поле ввода.\n"
            "Доступны: браузер, проводник, свернуть, выход, помощь, айпи, пинг.\n"
            "Также можно создавать свои команды во вкладке «Команды»."
        )

    def _minimize_to_circle(self):
        self._last_page_index = self._stack.currentIndex()
        self._release_heavy_pages()
        self._jarvis_bg.stop()
        self.hide()
        if self._floating is None:
            self._floating = FloatingCircle(theme=self.settings.circle_theme, opacity=self.settings.circle_opacity)
            self._floating.clicked.connect(self._restore_from_circle)
        self._floating.set_theme(self.settings.circle_theme)
        self._floating.set_opacity(self.settings.circle_opacity)
        self._floating.show()
        self._floating.move(self.cursor().pos())
        logging.debug("Свернуто в кружок")

    def _restore_from_circle(self):
        if self._floating:
            self._floating.hide()
        self._jarvis_bg.start()
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
        if self._floating:
            self._floating.set_theme(theme)

    def _apply_opacity(self, value: float):
        self.setWindowOpacity(value)

    def _apply_theme(self):
        qss = THEMES.get(self.settings.theme, THEMES["dark"])
        self.setStyleSheet(qss)
        if hasattr(self, "_jarvis_bg"):
            self._jarvis_bg.set_theme(self.settings.theme)
        self._load_chat_history()

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
        if self._floating:
            self._floating.close()
        if self._tray:
            self._tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _log_chat(self, role: str, text: str):
        self.chat_manager.add_message(role, text)
        prefix = "AssistPiip" if role == "assistant" else "Вы"
        avatar = self._get_avatar_html(role)
        color = "#2b6cb0" if role == "assistant" else "#e67e22"
        html = f"""
        <div style="margin-bottom: 12px;">
            {avatar}
            <div style="margin-left: 40px;">
                <b style="color: {color};">{prefix}</b> <span style="color: #888; font-size: 11px;">сейчас</span><br>
                <span>{text}</span>
            </div>
        </div>
        """
        self._chat_view.append(html)
        sb = self._chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _title_move(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _title_release(self, event):
        self._drag_pos = None

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
                val = act.get("value")
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
        idx = self.notes_manager.all_notes().index(note)
        if action == open_action:
            self._open_note(item)
        elif action == pin_action:
            self.notes_manager.toggle_pin(idx)
        elif action == delete_action:
            self.notes_manager.remove_note(idx)
            logging.info(f"Удалена заметка: {note.title}")

    def _open_note(self, item):
        note = item.data(Qt.ItemDataRole.UserRole)
        dlg = NoteDialog(self, note)
        if dlg.exec():
            updated = dlg.get_note()
            if updated:
                idx = self.notes_manager.all_notes().index(note)
                self.notes_manager.update_note(idx, updated)

    def _refresh_clipboard_list(self):
        if not hasattr(self, "_clipboard_list") or not shiboken6.isValid(self._clipboard_list):
            return
        self._clipboard_list.clear()
        for entry in self.clipboard_manager.all_entries():
            if self._clipboard_search_query:
                if self._clipboard_search_query.lower() not in entry.created.lower():
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
        view_action = menu.addAction("Просмотреть")
        copy_action = menu.addAction("Скопировать обратно")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self._clipboard_list.mapToGlobal(pos))
        if action == view_action:
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

        actions_label = QLabel("Действия (до 10):")
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
        type_combo.addItems(["url", "app", "file"])
        if act_type:
            type_combo.setCurrentText(act_type)

        value_edit = QLineEdit()
        value_edit.setPlaceholderText("URL или путь")
        if act_val:
            value_edit.setText(act_val)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(32)

        def browse():
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
        if not self._actions:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одно действие")
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
            return Note(title, body, self._note.pinned, self._note.created)
        return Note(title, body)
