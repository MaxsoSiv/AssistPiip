import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

from logger_manager import setup_logging
from settings_manager import SettingsManager
from ui_main import MainWindow
from utils import get_app_dir


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    log_signal, logger = setup_logging(logging.INFO)

    def exception_hook(exctype, value, tb):
        logger.critical("Необработанное исключение", exc_info=(exctype, value, tb))
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = exception_hook
    logger.info("Запуск AssistPiip")

    base_dir = get_app_dir()
    icon_path = os.path.join(base_dir, "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    settings = SettingsManager()
    window = MainWindow(settings, log_signal)

    tray = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
    tray.setToolTip("AssistPiip")
    menu = QMenu()

    show_action = QAction("Показать")
    show_action.triggered.connect(window.showNormal)
    menu.addAction(show_action)

    quit_action = QAction("Выход")
    quit_action.triggered.connect(window._full_exit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: window.showNormal() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    window._tray = tray
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
