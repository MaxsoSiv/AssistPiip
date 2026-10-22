import json
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class ChatMessage:
    def __init__(self, role: str, text: str, timestamp: str = None):
        self.role = role
        self.text = text
        self.timestamp = timestamp or datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return {"role": self.role, "text": self.text, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        return cls(data["role"], data["text"], data.get("timestamp"))


class ChatManager(QObject):
    messages_changed = Signal()

    def __init__(self, data_dir: str, limit: int = 80):
        super().__init__()
        self._file = os.path.join(data_dir, "chat_history.json")
        self._limit = limit
        self._messages: list[ChatMessage] = []
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._messages = [ChatMessage.from_dict(item) for item in raw]
            except Exception:
                self._messages = []

    def _save(self):
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        trimmed = self._messages[-self._limit:]
        self._messages = trimmed
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in trimmed], f, ensure_ascii=False, indent=2)
        self.messages_changed.emit()

    def add_message(self, role: str, text: str):
        self._messages.append(ChatMessage(role, text))
        if len(self._messages) > self._limit:
            self._messages = self._messages[-self._limit:]
        self._save()

    def all_messages(self) -> list[ChatMessage]:
        return list(self._messages)
