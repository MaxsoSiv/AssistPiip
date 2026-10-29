from PySide6.QtCore import QSettings, QObject, Signal


class SettingsManager(QObject):
    theme_changed = Signal(str)
    opacity_changed = Signal(float)
    circle_opacity_changed = Signal(float)
    circle_theme_changed = Signal(str)
    always_on_top_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._settings = QSettings("AssistPiip", "AssistPiip")

    def get(self, key: str, default=None, type=None):
        if type is not None:
            return self._settings.value(key, default, type=type)
        return self._settings.value(key, default)

    def set(self, key: str, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    @property
    def theme(self) -> str:
        return self.get("theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self.set("theme", value)
        self.theme_changed.emit(value)

    @property
    def window_opacity(self) -> float:
        return float(self.get("window_opacity", 1.0))

    @window_opacity.setter
    def window_opacity(self, value: float):
        self.set("window_opacity", value)
        self.opacity_changed.emit(value)

    @property
    def circle_opacity(self) -> float:
        return float(self.get("circle_opacity", 0.85))

    @circle_opacity.setter
    def circle_opacity(self, value: float):
        self.set("circle_opacity", value)
        self.circle_opacity_changed.emit(value)

    @property
    def circle_theme(self) -> str:
        return self.get("circle_theme", "blue")

    @circle_theme.setter
    def circle_theme(self, value: str):
        self.set("circle_theme", value)
        self.circle_theme_changed.emit(value)

    @property
    def browser_path(self) -> str:
        return self.get("browser_path", "")

    @browser_path.setter
    def browser_path(self, value: str):
        self.set("browser_path", value)

    @property
    def autostart(self) -> bool:
        return self.get("autostart", False, type=bool)

    @autostart.setter
    def autostart(self, value: bool):
        self.set("autostart", value)

    @property
    def developer_mode(self) -> bool:
        return self.get("developer_mode", False, type=bool)

    @developer_mode.setter
    def developer_mode(self, value: bool):
        self.set("developer_mode", value)

    @property
    def always_on_top(self) -> bool:
        return self.get("always_on_top", False, type=bool)

    @always_on_top.setter
    def always_on_top(self, value: bool):
        self.set("always_on_top", value)

    @property
    def hotkey(self) -> str:
        return self.get("hotkey", "Ctrl+Alt+P")

    @hotkey.setter
    def hotkey(self, value: str):
        self.set("hotkey", value)

    @property
    def check_updates(self) -> bool:
        return self.get("check_updates", True, type=bool)

    @check_updates.setter
    def check_updates(self, value: bool):
        self.set("check_updates", value)

    @property
    def accent_color(self) -> str:
        return self.get("accent_color", "")

    @accent_color.setter
    def accent_color(self, value: str):
        self.set("accent_color", value)

    @property
    def spotlight_hotkey(self) -> str:
        return self.get("spotlight_hotkey", "Ctrl+Alt+K")

    @spotlight_hotkey.setter
    def spotlight_hotkey(self, value: str):
        self.set("spotlight_hotkey", value)

    @property
    def quick_commands(self) -> list[str]:
        val = self.get("quick_commands", None)
        if val is None:
            return ["браузер", "проводник", "айпи", "пинг", "__minimize__", "__exit__", "__help__"]
        if isinstance(val, str):
            return [val] if val else []
        return list(val)

    @quick_commands.setter
    def quick_commands(self, value: list[str]):
        self.set("quick_commands", value)

    @property
    def ai_enabled(self) -> bool:
        return self.get("ai_enabled", False, type=bool)

    @ai_enabled.setter
    def ai_enabled(self, value: bool):
        self.set("ai_enabled", value)

    @property
    def ai_base_url(self) -> str:
        return self.get("ai_base_url", "https://api.openai.com/v1")

    @ai_base_url.setter
    def ai_base_url(self, value: str):
        self.set("ai_base_url", value)

    @property
    def ai_model(self) -> str:
        return self.get("ai_model", "")

    @ai_model.setter
    def ai_model(self, value: str):
        self.set("ai_model", value)

    @property
    def selection_hotkey(self) -> str:
        return self.get("selection_hotkey", "Ctrl+Alt+T")

    @selection_hotkey.setter
    def selection_hotkey(self, value: str):
        self.set("selection_hotkey", value)

    @property
    def voice_hotkey(self) -> str:
        return self.get("voice_hotkey", "Ctrl+Alt+V")

    @voice_hotkey.setter
    def voice_hotkey(self, value: str):
        self.set("voice_hotkey", value)

    @property
    def voice_language(self) -> str:
        return self.get("voice_language", "ru-RU")

    @voice_language.setter
    def voice_language(self, value: str):
        self.set("voice_language", value)
