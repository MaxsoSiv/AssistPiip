import ctypes
import time
from ctypes import wintypes

import win32clipboard

user32 = ctypes.windll.user32

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_C = 0x43
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

MODIFIER_KEYS = (VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD


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


def _modifiers_held() -> bool:
    for vk in MODIFIER_KEYS:
        if user32.GetAsyncKeyState(vk) & 0x8000:
            return True
    return False


def _wait_modifiers_released(timeout_s: float = 0.6) -> bool:
    deadline = time.monotonic() + timeout_s
    while _modifiers_held():
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)
    time.sleep(0.03)
    return True


def _send_ctrl_c() -> None:
    seq = [_KEYBDINPUT(VK_CONTROL, 0, 0, 0, None), _KEYBDINPUT(VK_C, 0, 0, 0, None),
           (_KEYBDINPUT(VK_C, 0, KEYEVENTF_KEYUP, 0, None)),
           (_KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, None))]
    arr = (_INPUT * len(seq))()
    for i, ki in enumerate(seq):
        arr[i].type = INPUT_KEYBOARD
        arr[i].ki = ki
    user32.SendInput(len(arr), arr, ctypes.sizeof(_INPUT))


def _copy_and_read(poll_s: float) -> str | None:
    before_seq = user32.GetClipboardSequenceNumber()
    _send_ctrl_c()
    deadline = time.monotonic() + poll_s
    while time.monotonic() < deadline:
        if user32.GetClipboardSequenceNumber() != before_seq:
            read_deadline = time.monotonic() + 0.4
            while time.monotonic() < read_deadline:
                text = _get_clipboard_text()
                if text is not None:
                    return text
                time.sleep(0.05)
            return None
        time.sleep(0.03)
    return None


def capture_selection(release_timeout_s: float = 0.6, poll_s: float = 0.8) -> str | None:
    previous = _get_clipboard_text()

    captured = None
    for attempt in range(2):
        _wait_modifiers_released(release_timeout_s if attempt == 0 else 0.3)
        captured = _copy_and_read(poll_s)
        if captured and captured.strip():
            break
        time.sleep(0.15)

    if not captured or not captured.strip():
        return None

    if previous is not None and previous != captured:
        _set_clipboard_text(previous)
    return captured
