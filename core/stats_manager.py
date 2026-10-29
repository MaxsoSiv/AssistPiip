import json
import os
import logging
from datetime import datetime

from PySide6.QtCore import QObject


class StatsManager(QObject):
    def __init__(self, data_dir: str):
        super().__init__()
        self._file = os.path.join(data_dir, "stats.json")
        self._stats: dict = {}
        self._load()

    def _load(self):
        if not os.path.exists(self._file):
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                self._stats = raw
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Файл stats.json поврежден, статистика будет пуста: {e}")
            self._stats = {}

    def _save(self):
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logging.error(f"Ошибка сохранения статистики: {e}")

    def increment(self, trigger: str):
        if not trigger:
            return
        entry = self._stats.get(trigger)
        if entry is None:
            entry = {"count": 0, "last": ""}
        entry["count"] += 1
        entry["last"] = datetime.now().isoformat(timespec="seconds")
        self._stats[trigger] = entry
        self._save()

    def count(self, trigger: str) -> int:
        entry = self._stats.get(trigger)
        return entry["count"] if entry else 0

    def top(self, n: int = 5) -> list[tuple[str, int]]:
        items = [(k, v["count"]) for k, v in self._stats.items()]
        items.sort(key=lambda kv: kv[1], reverse=True)
        return items[:n]
