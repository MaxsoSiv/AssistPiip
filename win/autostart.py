import winreg
import sys
import os
import logging

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AssistPiip"


def _get_executable() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    return f'"{python}" "{script}"'


def set_autostart(enabled: bool) -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_executable())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except PermissionError:
        logging.error("Нет прав на запись в реестр для автозапуска.")
        return False
    except OSError as e:
        logging.error(f"Ошибка реестра при настройке автозапуска: {e}")
        return False


def is_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError as e:
        logging.error(f"Ошибка чтения реестра для проверки автозапуска: {e}")
        return False
