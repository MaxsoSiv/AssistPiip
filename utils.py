import os
import sys
import shutil
import subprocess
import webbrowser
import logging
import win32gui
import win32con

APP_VERSION = "1.1.0"


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_path(path: str) -> bool:
    if not path:
        return False

    try:
        if os.path.exists(path):
            os.startfile(path)
            return True
    except OSError as e:
        logging.error(f"Ошибка ОС при открытии {path}: {e}")
        return False

    resolved = shutil.which(path)
    if resolved:
        try:
            subprocess.Popen([resolved])
            return True
        except OSError as e:
            logging.error(f"Ошибка ОС при запуске {resolved}: {e}")
            return False

    try:
        subprocess.Popen(path, shell=True)
        return True
    except FileNotFoundError:
        logging.error(f"Файл или приложение не найдено: {path}")
        return False
    except PermissionError:
        logging.error(f"Отказано в доступе при запуске: {path}")
        return False
    except OSError as e:
        logging.error(f"Ошибка ОС при запуске {path}: {e}")
        return False


def open_url(url: str, browser_path: str = "") -> bool:
    if not url:
        return False
        
    if browser_path and os.path.exists(browser_path):
        try:
            subprocess.Popen([browser_path, url])
            return True
        except FileNotFoundError:
            logging.error(f"Браузер не найден по пути: {browser_path}")
        except OSError as e:
            logging.error(f"Ошибка ОС при запуске браузера {browser_path}: {e}")
            
    try:
        success = webbrowser.open(url)
        if not success:
            logging.warning(f"Система не смогла открыть URL: {url}")
        return success
    except webbrowser.Error as e:
        logging.error(f"Ошибка модуля webbrowser: {e}")
        return False


def set_always_on_top(window, enabled: bool):
    hwnd = int(window.winId())
    flag = win32con.HWND_TOPMOST if enabled else win32con.HWND_NOTOPMOST
    try:
        win32gui.SetWindowPos(
            hwnd, flag, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
    except Exception as e:
        logging.error(f"Не удалось изменить Z-порядок окна: {e}")
