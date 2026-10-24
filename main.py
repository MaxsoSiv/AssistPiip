import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation

from logger_manager import setup_logging
from settings_manager import SettingsManager
from ui_main import MainWindow
from splash_screen import SplashScreen
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

    splash = SplashScreen()
    state = {"window": None, "splash_done": False}

    def reveal():
        window = state["window"]
        if window is None or not state["splash_done"] or window.isVisible():
            return
        window.setWindowOpacity(0.0)
        window.show()
        fade = QPropertyAnimation(window, b"windowOpacity", window)
        fade.setDuration(340)
        fade.setStartValue(0.0)
        fade.setEndValue(settings.window_opacity)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def build():
        window = MainWindow(settings, log_signal)

        tray = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        tray.setToolTip("AssistPiip")
        menu = QMenu()

        show_action = QAction("Показать")
        show_action.triggered.connect(window._restore_from_circle)
        menu.addAction(show_action)

        quit_action = QAction("Выход")
        quit_action.triggered.connect(window._full_exit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: window._restore_from_circle() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        tray.show()

        window._tray = tray
        state["window"] = window
        reveal()

    def on_splash_finished():
        state["splash_done"] = True
        reveal()

    splash.finished.connect(on_splash_finished)
    splash.show()
    splash.start()
    QTimer.singleShot(90, build)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
