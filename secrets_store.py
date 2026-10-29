import logging

import pywintypes
import win32cred

PREFIX = "AssistPiip."


def save_secret(name: str, secret: str) -> bool:
    if not name or not secret:
        return False
    try:
        credential = {
            "Type": win32cred.CRED_TYPE_GENERIC,
            "TargetName": PREFIX + name,
            "UserName": "AssistPiip",
            "CredentialBlob": secret,
            "Comment": "AssistPiip secret",
            "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        }
        win32cred.CredWrite(credential, 0)
        return True
    except (pywintypes.error, OSError, TypeError) as e:
        logging.error(f"Не удалось сохранить секрет в Credential Manager: {e}")
        return False


def load_secret(name: str) -> str | None:
    if not name:
        return None
    try:
        cred = win32cred.CredRead(PREFIX + name, win32cred.CRED_TYPE_GENERIC)
        blob = cred.get("CredentialBlob")
        if not blob:
            return None
        if isinstance(blob, bytes):
            try:
                return blob.decode("utf-16-le")
            except UnicodeDecodeError:
                return blob.decode("utf-8", errors="replace")
        return blob
    except (pywintypes.error, OSError):
        return None


def delete_secret(name: str) -> bool:
    try:
        win32cred.CredDelete(PREFIX + name, win32cred.CRED_TYPE_GENERIC, 0)
        return True
    except (pywintypes.error, OSError):
        return False


def has_secret(name: str) -> bool:
    return load_secret(name) is not None
