import logging
import win32con
import win32gui

HOTKEY_ID_MAIN = 0xB00C
HOTKEY_ID_SPOTLIGHT = 0xB00D

MOD_MAP = {
    "ctrl": win32con.MOD_CONTROL,
    "shift": win32con.MOD_SHIFT,
    "alt": win32con.MOD_ALT,
    "win": win32con.MOD_WIN,
    "meta": win32con.MOD_WIN,
}


def parse_combo(text: str):
    parts = [p.strip().lower() for p in text.split("+") if p.strip()]
    if len(parts) < 2:
        return None

    mods = 0
    for p in parts[:-1]:
        if p not in MOD_MAP:
            return None
        mods |= MOD_MAP[p]

    key = parts[-1]
    if len(key) == 1 and key.isalpha():
        vk = ord(key.upper())
    elif len(key) == 1 and key.isdigit():
        vk = ord(key)
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    else:
        return None

    return mods, vk


class HotkeyManager:
    def __init__(self, window):
        self._window = window
        self._registered = {}

    def register(self, hotkey_id: int, combo_text: str):
        self.unregister(hotkey_id)

        parsed = parse_combo(combo_text)
        if parsed is None:
            return False, "Неподдерживаемая комбинация"

        mods, vk = parsed
        try:
            hwnd = int(self._window.winId())
            win32gui.RegisterHotKey(hwnd, hotkey_id, mods, vk)
        except Exception as e:
            logging.error(f"Горячая клавиша не зарегистрирована: {e}")
            return False, "Комбинация уже занята другой программой"

        self._registered[hotkey_id] = combo_text
        return True, ""

    def unregister(self, hotkey_id: int):
        if hotkey_id in self._registered:
            try:
                win32gui.UnregisterHotKey(int(self._window.winId()), hotkey_id)
            except Exception:
                pass
            del self._registered[hotkey_id]

    def unregister_all(self):
        for hotkey_id in list(self._registered):
            self.unregister(hotkey_id)
