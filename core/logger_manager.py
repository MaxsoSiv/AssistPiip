import logging
from PySide6.QtCore import QObject, Signal


class LogSignal(QObject):
    new_log = Signal(str)


class QtLogHandler(logging.Handler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter

    def emit(self, record):
        msg = self.format(record)
        self.signal_emitter.new_log.emit(msg)


def setup_logging(level=logging.INFO):
    log_signal = LogSignal()
    handler = QtLogHandler(log_signal)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    return log_signal, root_logger
