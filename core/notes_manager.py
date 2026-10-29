import json
import os
import uuid
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class Note:
    MAX_HISTORY = 10

    def __init__(self, title: str, body: str, pinned: bool = False, created: str = None,
                 note_id: str = None, history: list = None):
        self.id = note_id or uuid.uuid4().hex
        self.title = title
        self.body = body
        self.pinned = pinned
        self.created = created or datetime.now().isoformat(timespec="seconds")
        self.history = history or []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "pinned": self.pinned,
            "created": self.created,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        history = data.get("history", [])
        return cls(
            data["title"],
            data["body"],
            data.get("pinned", False),
            data.get("created"),
            data.get("id"),
            history if isinstance(history, list) else [],
        )

    def snapshot(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "saved": datetime.now().isoformat(timespec="seconds"),
        }


class NotesManager(QObject):
    notes_changed = Signal()

    def __init__(self, data_dir: str):
        super().__init__()
        self._file = os.path.join(data_dir, "notes.json")
        self._notes: list[Note] = []
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self._file):
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._notes = [Note.from_dict(item) for item in raw]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Файл notes.json поврежден, список заметок будет пуст: {e}")
            self._notes = []
        except OSError as e:
            logging.error(f"Ошибка чтения файла заметок: {e}")
            self._notes = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump([n.to_dict() for n in self._notes], f, ensure_ascii=False, indent=2)
            self.notes_changed.emit()
        except OSError as e:
            logging.error(f"Ошибка сохранения файла заметок: {e}")

    def _find_index(self, note_id: str) -> int:
        for i, note in enumerate(self._notes):
            if note.id == note_id:
                return i
        return -1

    def all_notes(self) -> list[Note]:
        by_date = sorted(self._notes, key=lambda n: n.created, reverse=True)
        return sorted(by_date, key=lambda n: not n.pinned)

    def add_note(self, note: Note):
        self._notes.append(note)
        self._save()

    def update_note(self, note: Note, updated: Note):
        idx = self._find_index(note.id)
        if idx != -1:
            history = list(updated.history)
            history.insert(0, note.snapshot())
            updated.history = history[: Note.MAX_HISTORY]
            self._notes[idx] = updated
            self._save()
        else:
            logging.warning("Обновление несуществующей заметки пропущено")

    def remove_note(self, note: Note):
        idx = self._find_index(note.id)
        if idx != -1:
            del self._notes[idx]
            self._save()
        else:
            logging.warning("Удаление несуществующей заметки пропущено")

    def toggle_pin(self, note: Note):
        idx = self._find_index(note.id)
        if idx != -1:
            self._notes[idx].pinned = not self._notes[idx].pinned
            self._save()
        else:
            logging.warning("Переключение закрепления несуществующей заметки пропущено")
