import json
import os
import logging
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QGuiApplication

ACTION_TYPES = ("url", "app", "file", "script")


class Command:
    def __init__(self, trigger: str, aliases: list[str], actions: list[dict], case_sensitive: bool = False, source: str = "user"):
        self.trigger = trigger
        self.aliases = aliases
        self.actions = actions
        self.case_sensitive = case_sensitive
        self.source = source

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger,
            "aliases": self.aliases,
            "actions": self.actions,
            "case_sensitive": self.case_sensitive,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict, source: str = "user") -> "Command | None":
        try:
            trigger = data["trigger"]
            if not isinstance(trigger, str) or not trigger.strip():
                return None
            actions = data.get("actions", [])
            if not isinstance(actions, list):
                return None
            clean_actions = []
            for action in actions:
                if not isinstance(action, dict):
                    return None
                kind = action.get("type")
                value = action.get("value")
                if kind not in ACTION_TYPES or not isinstance(value, str) or not value.strip():
                    return None
                clean_actions.append({"type": kind, "value": value})
            if not clean_actions:
                return None
            aliases = data.get("aliases", [])
            if not isinstance(aliases, list):
                aliases = []
            aliases = [a for a in aliases if isinstance(a, str) and a.strip()]
            return cls(trigger, aliases, clean_actions, bool(data.get("case_sensitive", False)), source)
        except (KeyError, TypeError):
            return None


class CommandManager(QObject):
    commands_changed = Signal()

    def __init__(self, settings, data_dir: str):
        super().__init__()
        self._settings = settings
        self._data_dir = data_dir
        self._file = os.path.join(data_dir, "commands.json")
        self._plugins_dir = os.path.join(data_dir, "plugins")
        self._commands: list[Command] = []
        self._plugin_commands: list[Command] = []
        self._selection_provider = None
        os.makedirs(data_dir, exist_ok=True)
        self._load()
        self._load_plugins()

    def set_selection_provider(self, provider):
        self._selection_provider = provider

    def _load(self):
        if not os.path.exists(self._file):
            return

        try:
            with open(self._file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._commands = [c for c in (Command.from_dict(item) for item in raw) if c]
        except json.JSONDecodeError:
            logging.error("Файл commands.json поврежден. Список команд будет пуст.")
            self._commands = []
        except OSError as e:
            logging.error(f"Ошибка чтения файла команд: {e}")
            self._commands = []

    def _load_plugins(self):
        self._plugin_commands = []
        if not os.path.isdir(self._plugins_dir):
            return
        try:
            names = [n for n in os.listdir(self._plugins_dir) if n.lower().endswith(".json")]
        except OSError as e:
            logging.error(f"Не удалось прочитать папку плагинов: {e}")
            return
        for name in names:
            path = os.path.join(self._plugins_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"Плагин {name} поврежден и пропущен: {e}")
                continue
            if not isinstance(raw, dict):
                logging.warning(f"Плагин {name}: ожидается объект с полем commands")
                continue
            commands_raw = raw.get("commands", [])
            if not isinstance(commands_raw, list):
                logging.warning(f"Плагин {name}: commands должен быть списком")
                continue
            loaded = [c for c in (Command.from_dict(item, source="plugin") for item in commands_raw) if c]
            skipped = len(commands_raw) - len(loaded)
            if skipped:
                logging.warning(f"Плагин {name}: {skipped} команд пропущено из-за некорректной схемы")
            self._plugin_commands.extend(loaded)
            logging.info(f"Плагин {name}: загружено команд: {len(loaded)}")

    def _save(self):
        try:
            os.makedirs(self._data_dir, exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self._commands], f, ensure_ascii=False, indent=2)
            self.commands_changed.emit()
        except OSError as e:
            logging.error(f"Ошибка сохранения файла команд: {e}")

    def all_commands(self) -> list[Command]:
        return list(self._commands) + list(self._plugin_commands)

    def add_command(self, command: Command):
        self._commands = [c for c in self._commands if c.trigger != command.trigger]
        self._commands.append(command)
        self._save()

    def import_commands(self, commands: list):
        clean = [c for c in commands if c]
        known = {c.trigger for c in self._plugin_commands}
        self._commands = [c for c in clean if c.trigger not in known]
        self._save()

    def remove_command(self, trigger: str):
        if any(c.trigger == trigger for c in self._plugin_commands):
            logging.warning(f"Команда «{trigger}» из плагина не удаляется через интерфейс")
            return
        self._commands = [c for c in self._commands if c.trigger != trigger]
        self._save()

    def is_plugin(self, trigger: str) -> bool:
        return any(c.trigger == trigger for c in self._plugin_commands)

    def find_by_trigger(self, text: str) -> Command | None:
        for cmd in self.all_commands():
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

    def _substitute(self, value: str) -> str:
        if "{clipboard}" in value:
            value = value.replace("{clipboard}", QGuiApplication.clipboard().text())
        if "{selection}" in value and self._selection_provider:
            try:
                text = self._selection_provider() or ""
            except Exception as e:
                logging.error(f"Не удалось получить выделенный текст: {e}")
                text = ""
            value = value.replace("{selection}", text)
        return value

    def _run_action(self, action: dict):
        import subprocess
        from core.utils import open_path, open_url

        kind = action.get("type")
        value = self._substitute(action.get("value", ""))
        if not value:
            return
        if kind == "url":
            open_url(value, self._settings.browser_path)
        elif kind == "script":
            try:
                subprocess.Popen(
                    ["cmd", "/c", value],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    close_fds=True,
                )
            except OSError as e:
                logging.error(f"Не удалось запустить скрипт {value}: {e}")
        elif kind in ("app", "file"):
            open_path(value)
