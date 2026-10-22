import os
import sys
import subprocess
import webbrowser
import win32gui
import win32con


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_path(path: str) -> bool:
    if not path:
        return False
    if os.path.exists(path):
        os.startfile(path)
        return True
    try:
        subprocess.Popen(path, shell=True)
        return True
    except Exception:
        return False


def open_url(url: str, browser_path: str = "") -> bool:
    if not url:
        return False
    if browser_path and os.path.exists(browser_path):
        try:
            subprocess.Popen([browser_path, url])
            return True
        except Exception:
            pass
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def set_always_on_top(window, enabled: bool):
    hwnd = int(window.winId())
    flag = win32con.HWND_TOPMOST if enabled else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(
        hwnd, flag, 0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )