import os
import sys
import json
import hashlib
import logging
import zipfile
import tempfile
import threading
import subprocess
import requests

from PySide6.QtCore import QObject, Signal

RELEASES_URL = "https://maxsosiv.github.io/AssistPiip/releases.json"
SITE_URL = "https://maxsosiv.github.io/AssistPiip/"


def parse_version(version) -> tuple:
    parts = []
    for piece in str(version).split("."):
        num = ""
        for ch in piece:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote, local) -> bool:
    return parse_version(remote) > parse_version(local)


def fetch_latest() -> dict | None:
    resp = requests.get(RELEASES_URL, timeout=6)
    resp.raise_for_status()
    releases = resp.json()
    if not isinstance(releases, list) or not releases:
        return None
    return max(releases, key=lambda r: parse_version(r.get("version", "0")))


def download(url: str, dest_path: str) -> str:
    digest = hashlib.sha256()
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            f.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def _write_update_script(path, staging, app_dir, pid):
    exe_path = os.path.join(app_dir, "AssistPiip.exe")
    script = (
        "@echo off\r\n"
        ":wait\r\n"
        f'tasklist /FI "PID eq {pid}" | find /I "{pid}" >nul\r\n'
        "if not errorlevel 1 (\r\n"
        "    timeout /t 1 /nobreak >nul\r\n"
        "    goto wait\r\n"
        ")\r\n"
        f'xcopy "{staging}" "{app_dir}" /E /Y /I /Q >nul\r\n'
        f'start "" "{exe_path}"\r\n'
        "del \"%~f0\"\r\n"
    )
    for encoding in ("cp866", "mbcs"):
        try:
            with open(path, "w", encoding=encoding) as f:
                f.write(script)
            return
        except UnicodeEncodeError:
            continue
    raise UnicodeEncodeError("cp866/mbcs", script, 0, 1, "path is not representable in OEM/ANSI codepage")


def _safe_extractall(zf, dest: str):
    dest_real = os.path.realpath(dest)
    for member in zf.infolist():
        name = member.filename.replace("\\", "/")
        if os.path.isabs(name) or ".." in name.split("/"):
            raise zipfile.BadZipFile(f"Небезопасный путь в архиве: {member.filename}")
        target = os.path.realpath(os.path.join(dest, member.filename))
        if target != dest_real and not target.startswith(dest_real + os.sep):
            raise zipfile.BadZipFile(f"Путь вне папки распаковки: {member.filename}")
    zf.extractall(dest)


def apply_update(zip_path: str, app_dir: str, pid: int) -> bool:
    staging = tempfile.mkdtemp(prefix="assistpiip_update_")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            _safe_extractall(zf, staging)
    except (zipfile.BadZipFile, OSError) as e:
        logging.error(f"Не удалось распаковать архив обновления: {e}")
        return False

    nested = os.path.join(staging, "AssistPiip")
    if os.path.isdir(nested):
        staging = nested

    if not os.path.exists(os.path.join(staging, "AssistPiip.exe")):
        logging.error("В архиве обновления не найден AssistPiip.exe")
        return False

    bat_path = os.path.join(tempfile.gettempdir(), f"assistpiip_update_{pid}.bat")
    try:
        _write_update_script(bat_path, staging, app_dir, pid)
    except UnicodeEncodeError:
        logging.error("Путь установки не представим в системной кодировке, автообновление невозможно")
        return False

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    return True


class UpdateChecker(QObject):
    finished = Signal(object)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            result = fetch_latest()
        except Exception as e:
            result = {"error": str(e)}
        self.finished.emit(result)


class UpdateDownloader(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, expected_sha256: str = "", parent=None):
        super().__init__(parent)
        self._expected = (expected_sha256 or "").strip().lower()

    def start(self, url: str):
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    def _run(self, url):
        path = os.path.join(tempfile.gettempdir(), "assistpiip_update.zip")
        try:
            digest = download(url, path)
        except Exception as e:
            self.failed.emit(str(e))
            return
        if self._expected and digest.lower() != self._expected:
            try:
                os.remove(path)
            except OSError:
                pass
            logging.error(f"SHA-256 архива обновления не совпал: {digest}")
            self.failed.emit("Контрольная сумма архива не совпала. Скачайте обновление вручную с сайта.")
            return
        self.finished.emit(path)
