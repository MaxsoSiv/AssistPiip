import logging
import threading

import shiboken6
from PySide6.QtCore import QObject, Signal

try:
    import speech_recognition as _sr
except ImportError:
    _sr = None


def available() -> bool:
    return _sr is not None


def install_hint() -> str:
    return "Голосовой ввод недоступен: установите пакеты SpeechRecognition и PyAudio (pip install SpeechRecognition PyAudio)"


class VoiceWorker(QObject):
    listening = Signal()
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ignore = False

    def ignore_result(self):
        self._ignore = True

    def start(self, language: str):
        if _sr is None:
            self.failed.emit(install_hint())
            return
        threading.Thread(target=self._run, args=(language,), daemon=True).start()

    def _run(self, language: str):
        if shiboken6.isValid(self):
            self.listening.emit()
        try:
            recognizer = _sr.Recognizer()
            with _sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=25)
        except OSError as e:
            if shiboken6.isValid(self) and not self._ignore:
                self.failed.emit(f"Микрофон недоступен: {e}")
            return
        except Exception as e:
            if shiboken6.isValid(self) and not self._ignore:
                self.failed.emit(f"Ошибка записи: {e}")
            return

        if self._ignore:
            return

        try:
            text = recognizer.recognize_google(audio, language=language or "ru-RU")
        except _sr.WaitTimeoutError:
            if shiboken6.isValid(self) and not self._ignore:
                self.failed.emit("Речь не распознана — тишина.")
            return
        except _sr.UnknownValueError:
            if shiboken6.isValid(self) and not self._ignore:
                self.failed.emit("Не расслышал. Попробуйте ещё раз.")
            return
        except _sr.RequestError as e:
            logging.warning(f"Голосовой ввод: ошибка распознавания: {e}")
            if shiboken6.isValid(self) and not self._ignore:
                self.failed.emit("Сервис распознавания недоступен. Проверьте интернет.")
            return

        if shiboken6.isValid(self) and not self._ignore:
            self.finished.emit(text.strip())
