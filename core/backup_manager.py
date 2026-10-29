import logging
import os
import shutil
from datetime import datetime, timedelta

BACKUP_FILES = ("commands.json", "notes.json", "reminders.json", "chat_history.json", "clipboard.json")
KEEP_DAYS = 7


def run_backup(data_dir: str) -> str | None:
    backup_root = os.path.join(data_dir, "backups")
    today = datetime.now().strftime("%Y-%m-%d")
    dest = os.path.join(backup_root, today)
    if os.path.isdir(dest):
        return None

    present = [f for f in BACKUP_FILES if os.path.isfile(os.path.join(data_dir, f))]
    if not present:
        return None

    try:
        os.makedirs(dest, exist_ok=True)
        for name in present:
            shutil.copy2(os.path.join(data_dir, name), os.path.join(dest, name))
    except OSError as e:
        logging.error(f"Не удалось создать резервную копию: {e}")
        return None

    _rotate(backup_root, KEEP_DAYS)
    return dest


def _rotate(backup_root: str, keep_days: int):
    cutoff = datetime.now() - timedelta(days=keep_days)
    try:
        entries = os.listdir(backup_root)
    except OSError:
        return
    for name in entries:
        try:
            day = datetime.strptime(name, "%Y-%m-%d")
        except ValueError:
            continue
        if day < cutoff:
            path = os.path.join(backup_root, name)
            try:
                shutil.rmtree(path)
            except OSError as e:
                logging.warning(f"Не удалось удалить старый бэкап {name}: {e}")
