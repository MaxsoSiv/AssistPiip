import json
import os
import logging
from PySide6.QtCore import QObject, Signal, QTimer


class Command:
    def __init__(self, trigger: str, aliases: list[str], actions: list[dict], case_sensitive: bool = False):
        self.trigger = trigger
        self.aliases = aliases
        self.actions = actions
        self.case_sensitive = case_sensitive

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger,
            "aliases": self.aliases,
            "actions": self.actions,
            "case_sensitive": self.case_sensitive,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Command":
        return cls(
            data["trigger"],
            data.get("aliases", []),
            data.get("actions", []),
            data.get("case_sensitive", False),
        )


class CommandManager(QObject):
    commands_changed = Signal()

    def __init__(self, settings, data_dir: str):
        super().__init__()
        self._settings = settings
        self._data_dir = data_dir
        self._file = os.path.join(data_dir, "commands.json")
        self._commands: list[Command] = []
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self._file):
            return
            
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._commands = [Command.from_dict(item) for item in raw]
        except json.JSONDecodeError:
            logging.error("Файл commands.json поврежден. Список команд будет пуст.")
            self._commands = []
        except OSError as e:
            logging.error(f"Ошибка чтения файла команд: {e}")
            self._commands = []

    def _save(self):
        try:
            os.makedirs(self._data_dir, exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self._commands], f, ensure_ascii=False, indent=2)
            self.commands_changed.emit()
        except OSError as e:
            logging.error(f"Ошибка сохранения файла команд: {e}")

    def all_commands(self) -> list[Command]:
        return list(self._commands)

    def add_command(self, command: Command):
        self._commands.append(command)
        self._save()

    def remove_command(self, trigger: str):
        self._commands = [c for c in self._commands if c.trigger != trigger]
        self._save()

    def find_by_trigger(self, text: str) -> Command | None:
        for cmd in self._commands:
            candidates = [cmd.trigger] + cmd.aliases
            for candidate in candidates:
                if cmd.case_sensitive:
                    if text.strip() == candidate.strip():
                        return cmd
                else:
                    if text.strip().lower() == candidate.strip().lower():
                        return cmd
        return None

    def execute_actions(self, command: Command):
        for i, action in enumerate(command.actions):
            QTimer.singleShot(i * 1500, lambda a=action: self._run_action(a))

    def _run_action(self, action: dict):
        from utils import open_path, open_url

        kind = action.get("type")
        value = action.get("value", "")
        if kind == "url":
            open_url(value, self._settings.browser_path)
        elif kind in ("app", "file"):
            open_path(value)
