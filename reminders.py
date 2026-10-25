import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal, QTimer

UNITS = {
    "секунд": 1, "секунды": 1, "секунду": 1, "сек": 1, "с": 1,
    "минут": 60, "минуты": 60, "минуту": 60, "мин": 60, "м": 60,
    "часов": 3600, "часа": 3600, "час": 3600, "ч": 3600,
    "дней": 86400, "дня": 86400, "день": 86400, "д": 86400,
    "неделю": 604800, "недели": 604800, "нед": 604800,
}

DUR_RE = re.compile(
    r"(?:через|спустя)\s+(\d+)\s*(секунд[а-я]*|сек|с\b|минут[а-я]*|мин|м\b|час[а-я]*|ч\b|дн[а-я]*|день|дней|д\b|недел[а-я]*|нед)\s*",
    re.IGNORECASE,
)
AT_RE = re.compile(r"\b(?:в|на)\s+(\d{1,2})[:.](\d{2})\b")


def parse_duration(text: str) -> timedelta | None:
    m = DUR_RE.search(text.lower())
    if not m:
        return None
    amount = int(m.group(1))
    unit = m.group(2).strip()
    if unit[0] == "с":
        seconds = 1
    elif unit[0] == "м":
        seconds = 60
    elif unit[0] == "ч":
        seconds = 3600
    elif unit[0] in ("д",):
        seconds = 86400
    elif unit[0] == "н":
        seconds = 604800
    else:
        return None
    return timedelta(seconds=amount * seconds)


def parse_when(text: str):
    lowered = text.lower()

    dur = parse_duration(lowered)
    if dur:
        due = datetime.now() + dur
        rest = DUR_RE.sub("", text, count=1).strip(" ,:-")
        return due, rest

    m = AT_RE.search(lowered)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        if hour > 23 or minute > 59:
            return None
        now = datetime.now()
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due <= now:
            due += timedelta(days=1)
        rest = AT_RE.sub("", text, count=1).strip(" ,:-")
        return due, rest

    return None


class ReminderManager(QObject):
    triggered = Signal(dict)

    def __init__(self, data_dir: str):
        super().__init__()
        self._file = os.path.join(data_dir, "reminders.json")
        self._reminders = []
        self._timers = {}
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self._file):
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            now = datetime.now()
            for item in raw:
                due = datetime.fromisoformat(item["due"])
                if due <= now:
                    continue
                self._arm(item["id"], due, item["label"], item.get("kind", "reminder"))
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logging.error(f"Файл reminders.json поврежден: {e}")

    def _save(self):
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(
                    [{"id": r["id"], "due": r["due"].isoformat(timespec="seconds"), "label": r["label"], "kind": r["kind"]} for r in self._reminders],
                    f, ensure_ascii=False, indent=2,
                )
        except OSError as e:
            logging.error(f"Ошибка сохранения напоминаний: {e}")

    def _arm(self, rid, due, label, kind):
        entry = {"id": rid, "due": due, "label": label, "kind": kind}
        self._reminders.append(entry)
        delay = max(int((due - datetime.now()).total_seconds() * 1000), 0)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda r=entry: self._fire(r))
        timer.start(min(delay, 2**31 - 1))
        self._timers[rid] = timer

    def add(self, due: datetime, label: str, kind: str = "reminder") -> dict:
        entry = {"id": uuid.uuid4().hex, "due": due, "label": label, "kind": kind}
        self._arm(entry["id"], due, label, kind)
        self._save()
        return entry

    def cancel(self, rid: str = None, kind: str = None) -> list:
        removed = []
        for entry in list(self._reminders):
            if rid is not None and entry["id"] != rid:
                continue
            if kind is not None and entry["kind"] != kind:
                continue
            removed.append(entry)

        for entry in removed:
            self._reminders.remove(entry)
            timer = self._timers.pop(entry["id"], None)
            if timer:
                timer.stop()
                timer.deleteLater()

        if removed:
            self._save()
        return removed

    def _fire(self, entry):
        if entry not in self._reminders:
            return
        self._reminders.remove(entry)
        self._timers.pop(entry["id"], None)
        self._save()
        self.triggered.emit(entry)

    def pending(self) -> list:
        return sorted(self._reminders, key=lambda r: r["due"])
