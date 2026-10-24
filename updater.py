import os
import sys
import json
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


def download(url: str, dest_path: str):
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            f.write(chunk)


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
    with open(path, "w", encoding="cp866") as f:
        f.write(script)


def apply_update(zip_path: str, app_dir: str, pid: int) -> bool:
    staging = tempfile.mkdtemp(prefix="assistpiip_update_")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(staging)

    nested = os.path.join(staging, "AssistPiip")
    if os.path.isdir(nested):
        staging = nested

    if not os.path.exists(os.path.join(staging, "AssistPiip.exe")):
        logging.error("В архиве обновления не найден AssistPiip.exe")
        return False

    bat_path = os.path.join(tempfile.gettempdir(), f"assistpiip_update_{pid}.bat")
    _write_update_script(bat_path, staging, app_dir, pid)

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

    def start(self, url: str):
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    def _run(self, url):
        path = os.path.join(tempfile.gettempdir(), "assistpiip_update.zip")
        try:
            download(url, path)
        except Exception as e:
            self.failed.emit(str(e))
            return
        self.finished.emit(path)
