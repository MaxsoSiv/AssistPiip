import json
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class Note:
    def __init__(self, title: str, body: str, pinned: bool = False, created: str = None):
        self.title = title
        self.body = body
        self.pinned = pinned
        self.created = created or datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "pinned": self.pinned,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            data["title"],
            data["body"],
            data.get("pinned", False),
            data.get("created"),
        )


class NotesManager(QObject):
    notes_changed = Signal()

    def __init__(self, data_dir: str):
        super().__init__()
        self._file = os.path.join(data_dir, "notes.json")
        self._notes: list[Note] = []
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._notes = [Note.from_dict(item) for item in raw]
            except Exception:
                self._notes = []

    def _save(self):
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump([n.to_dict() for n in self._notes], f, ensure_ascii=False, indent=2)
        self.notes_changed.emit()

    def all_notes(self) -> list[Note]:
        return sorted(self._notes, key=lambda n: (not n.pinned, n.created), reverse=True)

    def add_note(self, note: Note):
        self._notes.append(note)
        self._save()

    def update_note(self, index: int, note: Note):
        if 0 <= index < len(self._notes):
            self._notes[index] = note
            self._save()

    def remove_note(self, index: int):
        if 0 <= index < len(self._notes):
            del self._notes[index]
            self._save()

    def toggle_pin(self, index: int):
        if 0 <= index < len(self._notes):
            self._notes[index].pinned = not self._notes[index].pinned
            self._save()
