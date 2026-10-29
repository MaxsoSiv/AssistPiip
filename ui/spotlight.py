from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLineEdit, QLabel, QListWidget, QListWidgetItem

MAX_RESULTS = 7

BUILTIN_ITEMS = [
    ("браузер", "команда"),
    ("проводник", "команда"),
    ("заметки", "команда"),
    ("айпи", "команда"),
    ("пинг", "команда"),
    ("свернуть", "команда"),
    ("помощь", "команда"),
]


class Spotlight(QWidget):
    submitted = Signal(str)
    activated = Signal(dict)

    def __init__(self, settings=None, command_manager=None, notes_manager=None, clipboard_manager=None):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._settings = settings
        self._command_manager = command_manager
        self._notes_manager = notes_manager
        self._clipboard_manager = clipboard_manager
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(640, 90)

        card = QFrame()
        card.setObjectName("spotlightCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 12, 18, 10)
        inner.setSpacing(4)

        self._input = QLineEdit()
        self._input.setObjectName("spotlightInput")
        self._input.setPlaceholderText("Команда для AssistPiip...")
        self._input.setFixedHeight(32)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._on_return)
        self._input.installEventFilter(self)
        inner.addWidget(self._input)

        self._results = QListWidget()
        self._results.setObjectName("spotlightResults")
        self._results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._results.setUniformItemSizes(True)
        self._results.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._results.itemActivated.connect(lambda item: self._activate(item))
        self._results.itemClicked.connect(lambda item: self._activate(item))
        self._results.hide()
        inner.addWidget(self._results)

        self._hint = QLabel("Enter — выполнить   ·   ↑↓ — выбор   ·   Esc — закрыть")
        self._hint.setObjectName("spotlightHint")
        inner.addWidget(self._hint)

    def _style_results(self):
        dark = (self._settings.theme if self._settings else "dark") != "light"
        text = "#e8ebf0" if dark else "#26292f"
        dim = "#9aa2b0" if dark else "#6b7280"
        self._results.setStyleSheet(
            f"QListWidget#spotlightResults {{ background: transparent; border: none; color: {text}; font-size: 13px; }}"
            f"QListWidget#spotlightResults::item {{ padding: 4px 6px; border-radius: 6px; }}"
            f"QListWidget#spotlightResults::item:selected {{ background: rgba(128, 138, 160, 0.25); color: {text}; }}"
            f"QListWidget#spotlightResults::item:hover {{ background: rgba(128, 138, 160, 0.15); }}"
        )
        self._results.setProperty("dimColor", dim)

    def _on_text_changed(self, text):
        query = text.strip().lower()
        items = self._collect(query)
        self._fill(items)

    def _collect(self, query: str) -> list[dict]:
        if not query:
            return []
        items = []
        seen = set()

        if self._command_manager is not None:
            for cmd in self._command_manager.all_commands():
                names = [cmd.trigger] + list(cmd.aliases)
                if cmd.trigger.lower() not in seen and any(query in n.lower() for n in names):
                    seen.add(cmd.trigger.lower())
                    items.append({"kind": "command", "title": cmd.trigger, "subtitle": "своя команда", "payload": cmd.trigger})

        for trigger, kind in BUILTIN_ITEMS:
            if trigger not in seen and query in trigger:
                seen.add(trigger)
                items.append({"kind": "command", "title": trigger, "subtitle": kind, "payload": trigger})

        if self._notes_manager is not None:
            for note in self._notes_manager.all_notes():
                if query in note.title.lower() or query in note.body.lower():
                    items.append({"kind": "note", "title": note.title or "Без названия", "subtitle": note.created[:10], "payload": note})
                if len(items) >= MAX_RESULTS:
                    break

        if self._clipboard_manager is not None and len(items) < MAX_RESULTS:
            for entry in self._clipboard_manager.all_entries():
                if entry.kind == "text" and query in entry.content.lower():
                    preview = entry.content[:60].replace("\n", " ")
                    items.append({"kind": "clipboard", "title": preview, "subtitle": "буфер", "payload": entry})
                if len(items) >= MAX_RESULTS:
                    break

        return items[:MAX_RESULTS]

    def _fill(self, items: list[dict]):
        self._results.clear()
        if not items:
            self._results.hide()
            self.setFixedSize(640, 90)
            return
        for it in items:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, it)
            self._results.addItem(item)
        self._results.setCurrentRow(0)
        self._results.setFixedHeight(min(len(items), MAX_RESULTS) * 28)
        self.setFixedSize(640, 90 + min(len(items), MAX_RESULTS) * 28)
        self._results.show()

    def _on_return(self):
        if self._results.isVisible() and self._results.count() > 0:
            item = self._results.currentItem() or self._results.item(0)
            self._activate(item)
            return
        self._submit()

    def _submit(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.hide()
        self.submitted.emit(text)

    def _activate(self, item):
        if item is None:
            return
        action = item.data(Qt.ItemDataRole.UserRole)
        self._input.clear()
        self.hide()
        if action:
            self.activated.emit(action)

    def open_at_cursor(self):
        self._style_results()
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = min(max(pos.x() - self.width() // 2, geo.left() + 8), geo.right() - self.width() - 8)
        y = pos.y() + 28
        if y + self.height() > geo.bottom():
            y = pos.y() - self.height() - 10
        y = max(y, geo.top() + 8)
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() == event.Type.KeyPress:
            if self._results.isVisible() and self._results.count() > 0:
                if event.key() == Qt.Key.Key_Down:
                    row = (self._results.currentRow() + 1) % self._results.count()
                    self._results.setCurrentRow(row)
                    return True
                if event.key() == Qt.Key.Key_Up:
                    row = (self._results.currentRow() - 1) % self._results.count()
                    self._results.setCurrentRow(row)
                    return True
            if event.key() == Qt.Key.Key_Escape:
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowDeactivate and self.isVisible():
            self.hide()
        super().changeEvent(event)
