import json
import os
import uuid
import hashlib
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer, QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QImage


class ClipboardEntry:
    def __init__(self, kind: str, content: str, created: str = None, pinned: bool = False):
        self.kind = kind
        self.content = content
        self.created = created or datetime.now().isoformat(timespec="seconds")
        self.pinned = pinned

    def to_dict(self) -> dict:
        return {"kind": self.kind, "content": self.content, "created": self.created, "pinned": self.pinned}

    @classmethod
    def from_dict(cls, data: dict) -> "ClipboardEntry":
        return cls(data["kind"], data["content"], data.get("created"), data.get("pinned", False))


class ClipboardManager(QObject):
    clipboard_changed = Signal()

    def __init__(self, data_dir: str, limit: int = 50):
        super().__init__()
        self._dir = os.path.join(data_dir, "clipboard")
        self._file = os.path.join(data_dir, "clipboard.json")
        self._limit = limit
        self._entries: list[ClipboardEntry] = []
        self._self_copy = False
        self._last_hash = None
        os.makedirs(self._dir, exist_ok=True)
        self._load()

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(200)
        self._debounce_timer.timeout.connect(self._process_clipboard)

        self._clipboard = QGuiApplication.clipboard()
        self._clipboard.dataChanged.connect(self._on_clipboard_changed)

    def _load(self):
        if not os.path.exists(self._file):
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._entries = [ClipboardEntry.from_dict(item) for item in raw]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Файл clipboard.json поврежден, история буфера будет пуста: {e}")
            self._entries = []
        except OSError as e:
            logging.error(f"Ошибка чтения истории буфера обмена: {e}")
            self._entries = []

    def _save(self):
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self._entries], f, ensure_ascii=False, indent=2)
        except OSError as e:
            logging.error(f"Ошибка сохранения истории буфера обмена: {e}")
            return
        self.clipboard_changed.emit()

    def _trim(self):
        while len(self._entries) > self._limit:
            idx = next((i for i, e in enumerate(self._entries) if not e.pinned), None)
            if idx is None:
                break
            old = self._entries.pop(idx)
            if old.kind == "image" and os.path.exists(old.content):
                try:
                    os.remove(old.content)
                except OSError:
                    pass

    def _on_clipboard_changed(self):
        if self._self_copy:
            return
        self._debounce_timer.start()

    def _process_clipboard(self):
        if self._self_copy:
            return

        mime = self._clipboard.mimeData()
        if mime is None:
            return

        if mime.hasImage():
            image = self._clipboard.image()
            if image.isNull():
                return

            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            raw_bytes = buffer.data()
            buffer.close()

            current_hash = hashlib.md5(raw_bytes).hexdigest()
            if current_hash == self._last_hash:
                return
            self._last_hash = current_hash

            name = f"{uuid.uuid4().hex}.png"
            path = os.path.join(self._dir, name)
            if not image.save(path, "PNG"):
                logging.error("Не удалось сохранить изображение из буфера обмена")
                return
            self._entries.append(ClipboardEntry("image", path))

        elif mime.hasText():
            text = self._clipboard.text()
            if text is None or text == "":
                return

            current_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if current_hash == self._last_hash:
                return
            self._last_hash = current_hash

            self._entries.append(ClipboardEntry("text", text))
        else:
            return

        self._trim()
        self._save()

    def copy_entry(self, entry: ClipboardEntry):
        self._self_copy = True
        try:
            if entry.kind == "text":
                self._clipboard.setText(entry.content)
            elif entry.kind == "image":
                image = QImage(entry.content)
                if not image.isNull():
                    self._clipboard.setImage(image)
        finally:
            QTimer.singleShot(300, self._reset_self_copy)

    def _reset_self_copy(self):
        self._self_copy = False

    def all_entries(self) -> list[ClipboardEntry]:
        pinned = [e for e in self._entries if e.pinned]
        rest = [e for e in self._entries if not e.pinned]
        return list(reversed(pinned)) + list(reversed(rest))

    def toggle_pin(self, entry: ClipboardEntry):
        try:
            idx = self._entries.index(entry)
        except ValueError:
            return
        self._entries[idx].pinned = not self._entries[idx].pinned
        self._save()

    def remove_entry(self, entry: ClipboardEntry):
        if entry in self._entries:
            self._entries.remove(entry)
            if entry.kind == "image" and os.path.exists(entry.content):
                try:
                    os.remove(entry.content)
                except OSError:
                    pass
            self._save()

    def clear_all(self):
        removed = [e for e in self._entries if not e.pinned]
        self._entries = [e for e in self._entries if e.pinned]
        for entry in removed:
            if entry.kind == "image" and os.path.exists(entry.content):
                try:
                    os.remove(entry.content)
                except OSError:
                    pass
        self._last_hash = None
        self._save()
