import ctypes
import time
from ctypes import wintypes

import win32clipboard

user32 = ctypes.windll.user32

VK_CONTROL = 0x11
VK_C = 0x43
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _get_clipboard_text() -> str | None:
    try:
        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return None
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            return data if isinstance(data, str) else None
        finally:
            win32clipboard.CloseClipboard()
    except OSError:
        return None


def _set_clipboard_text(text: str) -> None:
    try:
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()
    except OSError:
        pass


def _send_ctrl_c() -> None:
    seq = [(_KEYBDINPUT(VK_CONTROL, 0, 0, 0, None)), (_KEYBDINPUT(VK_C, 0, 0, 0, None)),
           (_KEYBDINPUT(VK_C, 0, KEYEVENTF_KEYUP, 0, None)), (_KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, None))]
    arr = (_INPUT * len(seq))()
    for i, ki in enumerate(seq):
        arr[i].type = INPUT_KEYBOARD
        arr[i].ki = ki
    user32.SendInput(len(arr), arr, ctypes.sizeof(_INPUT))


def capture_selection(timeout_ms: int = 600) -> str | None:
    previous = _get_clipboard_text()
    before_seq = user32.GetClipboardSequenceNumber()
    try:
        _send_ctrl_c()
    except OSError as e:
        raise RuntimeError(f"Не удалось отправить Ctrl+C: {e}") from e

    deadline = time.monotonic() + timeout_ms / 1000.0
    captured = None
    while time.monotonic() < deadline:
        if user32.GetClipboardSequenceNumber() != before_seq:
            time.sleep(0.08)
            captured = _get_clipboard_text()
            break
        time.sleep(0.03)

    if not captured or not captured.strip():
        return None
    if captured == previous and before_seq == user32.GetClipboardSequenceNumber():
        return None

    if previous is not None and previous != captured:
        _set_clipboard_text(previous)
    return captured
