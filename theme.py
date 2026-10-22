DARK_QSS = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f1115, stop:1 #1a1b1e);
}
QDialog { background: #1a1b1e; color: #e0e0e0; }
QFrame#sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f1115, stop:1 #1a1b1e); border-right: 1px solid #2b2d31; }
QFrame#titleBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f1115, stop:1 #1a1b1e); border-bottom: 1px solid #2b2d31; }
QLabel { color: #e0e0e0; }
QCheckBox { color: #e0e0e0; }
QStackedWidget { background: transparent; }
QWidget#pageContainer { background: transparent; }
QPushButton#navButton { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #ddd; background: transparent; }
QPushButton#navButton:hover { background: rgba(47, 50, 55, 0.7); }
QPushButton#navButton:checked { background: #2b6cb0; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #ccc; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(47, 50, 55, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #ccc; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #ccc; border: none; }
QPushButton#titleButton:hover { background: rgba(58, 61, 66, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #ccc; border: none; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(43, 45, 49, 0.9); border: 1px solid #3a3d42; border-radius: 6px; padding: 4px 8px; color: #eee; }
QLineEdit#commandInput { background: rgba(43, 45, 49, 0.9); border: 1px solid #3a3d42; border-radius: 10px; padding: 0 14px; color: #eee; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #2b6cb0; }
QPushButton#primaryButton { background: #2b6cb0; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #3182ce; }
QPushButton#dangerButton { background: #5a1f1f; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#dangerButton:hover { background: #7a2a2a; }
QPushButton#quickButton { background: rgba(43, 45, 49, 0.9); color: #ddd; border: 1px solid #3a3d42; border-radius: 8px; padding: 0 16px; }
QPushButton#quickButton:hover { background: rgba(58, 61, 66, 0.9); }
QTextEdit#chatView { background: rgba(30, 31, 34, 0.85); border: 1px solid rgba(43, 45, 49, 0.8); border-radius: 10px; color: #ddd; padding: 12px; font-size: 13px; }
QTextEdit { background: rgba(30, 31, 34, 0.85); border: 1px solid rgba(43, 45, 49, 0.8); border-radius: 6px; color: #ddd; }
QListWidget { background: rgba(30, 31, 34, 0.85); border: 1px solid rgba(43, 45, 49, 0.8); border-radius: 10px; color: #ddd; padding: 6px; }
QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(43, 45, 49, 0.5); }
QListWidget::item:selected { background: #2b6cb0; color: #fff; }
QComboBox { background: rgba(43, 45, 49, 0.9); color: #ddd; border: 1px solid #3a3d42; border-radius: 6px; padding: 4px 8px; }
QComboBox QAbstractItemView { background: #2b2d31; color: #ddd; selection-background-color: #2b6cb0; }
QLabel#statusLabel { background: #202225; color: #aaa; padding-left: 8px; font-size: 11px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(58, 61, 66, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(30, 31, 34, 0.9); border: 1px solid #2b2d31; border-radius: 12px; color: #fff; padding: 10px; }
QPushButton#calcButton { background: rgba(43, 45, 49, 0.9); color: #fff; border: none; border-radius: 24px; font-weight: 500; }
QPushButton#calcButton:hover { background: rgba(58, 61, 66, 0.9); }
QPushButton#calcOperator { background: #2b6cb0; color: #fff; border: none; border-radius: 24px; font-weight: bold; }
QPushButton#calcOperator:hover { background: #3182ce; }
QPushButton#calcMemory { background: rgba(58, 61, 66, 0.9); color: #ddd; border: none; border-radius: 24px; }
QPushButton#calcMemory:hover { background: rgba(74, 77, 82, 0.9); }
QPushButton#calcLogic { background: rgba(45, 55, 72, 0.9); color: #cbd5e0; border: none; border-radius: 24px; }
QPushButton#calcLogic:hover { background: rgba(74, 85, 104, 0.9); }
QLabel#calcHistoryLabel { color: #aaa; font-size: 12px; }
"""

LIGHT_QSS = """
QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e8eaed, stop:1 #f5f6f8); }
QDialog { background: #f5f6f8; color: #1a1b1e; }
QFrame#sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8eaed, stop:1 #d0d3d8); border-right: 1px solid #c0c3c8; }
QFrame#titleBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8eaed, stop:1 #d0d3d8); border-bottom: 1px solid #c0c3c8; }
QLabel { color: #1a1b1e; }
QCheckBox { color: #1a1b1e; }
QStackedWidget { background: transparent; }
QWidget#pageContainer { background: transparent; }
QPushButton#navButton { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #1a1b1e; background: transparent; }
QPushButton#navButton:hover { background: rgba(208, 211, 216, 0.7); }
QPushButton#navButton:checked { background: #2b6cb0; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #1a1b1e; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(208, 211, 216, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #1a1b1e; background: transparent; }
QPushButton#sidebarExit:hover { background: #e0b0b0; }
QPushButton#titleButton { background: transparent; color: #1a1b1e; border: none; }
QPushButton#titleButton:hover { background: rgba(208, 211, 216, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #1a1b1e; border: none; }
QPushButton#titleClose:hover { background: #c42b1c; color: #fff; border-radius: 6px; }
QLineEdit { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 6px; padding: 4px 8px; color: #1a1b1e; }
QLineEdit#commandInput { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 10px; padding: 0 14px; color: #1a1b1e; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #2b6cb0; }
QPushButton#primaryButton { background: #2b6cb0; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #3182ce; }
QPushButton#dangerButton { background: #5a1f1f; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#dangerButton:hover { background: #7a2a2a; }
QPushButton#quickButton { background: rgba(255, 255, 255, 0.9); color: #1a1b1e; border: 1px solid #c0c3c8; border-radius: 8px; padding: 0 16px; }
QPushButton#quickButton:hover { background: rgba(232, 234, 237, 0.9); }
QTextEdit#chatView { background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(192, 195, 200, 0.8); border-radius: 10px; color: #1a1b1e; padding: 12px; font-size: 13px; }
QTextEdit { background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(192, 195, 200, 0.8); border-radius: 6px; color: #1a1b1e; }
QListWidget { background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(192, 195, 200, 0.8); border-radius: 10px; color: #1a1b1e; padding: 6px; }
QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(224, 227, 232, 0.5); }
QListWidget::item:selected { background: #2b6cb0; color: #fff; }
QComboBox { background: rgba(255, 255, 255, 0.9); color: #1a1b1e; border: 1px solid #c0c3c8; border-radius: 6px; padding: 4px 8px; }
QComboBox QAbstractItemView { background: #fff; color: #1a1b1e; selection-background-color: #2b6cb0; }
QLabel#statusLabel { background: #d0d3d8; color: #333; padding-left: 8px; font-size: 11px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(192, 195, 200, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 12px; color: #1a1b1e; padding: 10px; }
QPushButton#calcButton { background: rgba(232, 234, 237, 0.9); color: #1a1b1e; border: none; border-radius: 24px; font-weight: 500; }
QPushButton#calcButton:hover { background: rgba(208, 211, 216, 0.9); }
QPushButton#calcOperator { background: #2b6cb0; color: #fff; border: none; border-radius: 24px; font-weight: bold; }
QPushButton#calcOperator:hover { background: #3182ce; }
QPushButton#calcMemory { background: rgba(208, 211, 216, 0.9); color: #1a1b1e; border: none; border-radius: 24px; }
QPushButton#calcMemory:hover { background: rgba(192, 195, 200, 0.9); }
QPushButton#calcLogic { background: rgba(192, 195, 200, 0.9); color: #1a1b1e; border: none; border-radius: 24px; }
QPushButton#calcLogic:hover { background: rgba(160, 163, 168, 0.9); }
QLabel#calcHistoryLabel { color: #666; font-size: 12px; }
"""

OCEAN_QSS = """
QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a192f, stop:1 #173a5e); }
QDialog { background: #0a192f; color: #e0e0e0; }
QFrame#sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a192f, stop:1 #173a5e); border-right: 1px solid #112240; }
QFrame#titleBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a192f, stop:1 #173a5e); border-bottom: 1px solid #112240; }
QLabel { color: #e0e0e0; }
QCheckBox { color: #e0e0e0; }
QStackedWidget { background: transparent; }
QWidget#pageContainer { background: transparent; }
QPushButton#navButton { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #c9d6e8; background: transparent; }
QPushButton#navButton:hover { background: rgba(17, 34, 64, 0.7); }
QPushButton#navButton:checked { background: #00b4d8; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #c9d6e8; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(17, 34, 64, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #c9d6e8; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #c9d6e8; border: none; }
QPushButton#titleButton:hover { background: rgba(17, 34, 64, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #c9d6e8; border: none; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(17, 34, 64, 0.9); border: 1px solid #1d3557; border-radius: 6px; padding: 4px 8px; color: #e0e0e0; }
QLineEdit#commandInput { background: rgba(17, 34, 64, 0.9); border: 1px solid #1d3557; border-radius: 10px; padding: 0 14px; color: #e0e0e0; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #00b4d8; }
QPushButton#primaryButton { background: #00b4d8; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #48cae4; }
QPushButton#dangerButton { background: #5a1f1f; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#dangerButton:hover { background: #7a2a2a; }
QPushButton#quickButton { background: rgba(17, 34, 64, 0.9); color: #c9d6e8; border: 1px solid #1d3557; border-radius: 8px; padding: 0 16px; }
QPushButton#quickButton:hover { background: rgba(29, 53, 87, 0.9); }
QTextEdit#chatView { background: rgba(13, 31, 59, 0.85); border: 1px solid rgba(17, 34, 64, 0.8); border-radius: 10px; color: #c9d6e8; padding: 12px; font-size: 13px; }
QTextEdit { background: rgba(13, 31, 59, 0.85); border: 1px solid rgba(17, 34, 64, 0.8); border-radius: 6px; color: #c9d6e8; }
QListWidget { background: rgba(13, 31, 59, 0.85); border: 1px solid rgba(17, 34, 64, 0.8); border-radius: 10px; color: #c9d6e8; padding: 6px; }
QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(17, 34, 64, 0.5); }
QListWidget::item:selected { background: #00b4d8; color: #fff; }
QComboBox { background: rgba(17, 34, 64, 0.9); color: #c9d6e8; border: 1px solid #1d3557; border-radius: 6px; padding: 4px 8px; }
QComboBox QAbstractItemView { background: #112240; color: #c9d6e8; selection-background-color: #00b4d8; }
QLabel#statusLabel { background: #112240; color: #8ca3c7; padding-left: 8px; font-size: 11px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(29, 53, 87, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(13, 31, 59, 0.9); border: 1px solid #1d3557; border-radius: 12px; color: #e0e0e0; padding: 10px; }
QPushButton#calcButton { background: rgba(17, 34, 64, 0.9); color: #c9d6e8; border: none; border-radius: 24px; font-weight: 500; }
QPushButton#calcButton:hover { background: rgba(29, 53, 87, 0.9); }
QPushButton#calcOperator { background: #00b4d8; color: #fff; border: none; border-radius: 24px; font-weight: bold; }
QPushButton#calcOperator:hover { background: #48cae4; }
QPushButton#calcMemory { background: rgba(29, 53, 87, 0.9); color: #c9d6e8; border: none; border-radius: 24px; }
QPushButton#calcMemory:hover { background: rgba(42, 74, 115, 0.9); }
QPushButton#calcLogic { background: rgba(23, 58, 94, 0.9); color: #c9d6e8; border: none; border-radius: 24px; }
QPushButton#calcLogic:hover { background: rgba(29, 53, 87, 0.9); }
QLabel#calcHistoryLabel { color: #8ca3c7; font-size: 12px; }
"""

SUNSET_QSS = """
QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b0d0d, stop:1 #4a1c15); }
QDialog { background: #2b0d0d; color: #fdf0d5; }
QFrame#sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f0808, stop:1 #3d1414); border-right: 1px solid #4a1c15; }
QFrame#titleBar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f0808, stop:1 #3d1414); border-bottom: 1px solid #4a1c15; }
QLabel { color: #fdf0d5; }
QCheckBox { color: #fdf0d5; }
QStackedWidget { background: transparent; }
QWidget#pageContainer { background: transparent; }
QPushButton#navButton { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #fdf0d5; background: transparent; }
QPushButton#navButton:hover { background: rgba(94, 40, 18, 0.7); }
QPushButton#navButton:checked { background: #fca311; color: #000; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #fdf0d5; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(94, 40, 18, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #fdf0d5; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #fdf0d5; border: none; }
QPushButton#titleButton:hover { background: rgba(94, 40, 18, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #fdf0d5; border: none; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(61, 20, 20, 0.9); border: 1px solid #5e2812; border-radius: 6px; padding: 4px 8px; color: #fdf0d5; }
QLineEdit#commandInput { background: rgba(61, 20, 20, 0.9); border: 1px solid #5e2812; border-radius: 10px; padding: 0 14px; color: #fdf0d5; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #fca311; }
QPushButton#primaryButton { background: #fca311; color: #000; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #ffb703; }
QPushButton#dangerButton { background: #5a1f1f; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#dangerButton:hover { background: #7a2a2a; }
QPushButton#quickButton { background: rgba(61, 20, 20, 0.9); color: #fdf0d5; border: 1px solid #5e2812; border-radius: 8px; padding: 0 16px; }
QPushButton#quickButton:hover { background: rgba(94, 40, 18, 0.9); }
QTextEdit#chatView { background: rgba(31, 8, 8, 0.85); border: 1px solid rgba(61, 20, 20, 0.8); border-radius: 10px; color: #fdf0d5; padding: 12px; font-size: 13px; }
QTextEdit { background: rgba(31, 8, 8, 0.85); border: 1px solid rgba(61, 20, 20, 0.8); border-radius: 6px; color: #fdf0d5; }
QListWidget { background: rgba(31, 8, 8, 0.85); border: 1px solid rgba(61, 20, 20, 0.8); border-radius: 10px; color: #fdf0d5; padding: 6px; }
QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(61, 20, 20, 0.5); }
QListWidget::item:selected { background: #fca311; color: #000; }
QComboBox { background: rgba(61, 20, 20, 0.9); color: #fdf0d5; border: 1px solid #5e2812; border-radius: 6px; padding: 4px 8px; }
QComboBox QAbstractItemView { background: #3d1414; color: #fdf0d5; selection-background-color: #fca311; }
QLabel#statusLabel { background: #3d1414; color: #fca311; padding-left: 8px; font-size: 11px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(94, 40, 18, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(31, 8, 8, 0.9); border: 1px solid #5e2812; border-radius: 12px; color: #fdf0d5; padding: 10px; }
QPushButton#calcButton { background: rgba(61, 20, 20, 0.9); color: #fdf0d5; border: none; border-radius: 24px; font-weight: 500; }
QPushButton#calcButton:hover { background: rgba(94, 40, 18, 0.9); }
QPushButton#calcOperator { background: #fca311; color: #000; border: none; border-radius: 24px; font-weight: bold; }
QPushButton#calcOperator:hover { background: #ffb703; }
QPushButton#calcMemory { background: rgba(94, 40, 18, 0.9); color: #fdf0d5; border: none; border-radius: 24px; }
QPushButton#calcMemory:hover { background: rgba(122, 54, 24, 0.9); }
QPushButton#calcLogic { background: rgba(74, 28, 21, 0.9); color: #fdf0d5; border: none; border-radius: 24px; }
QPushButton#calcLogic:hover { background: rgba(94, 40, 18, 0.9); }
QLabel#calcHistoryLabel { color: #fca311; font-size: 12px; }
"""

THEMES = {
    "dark": DARK_QSS,
    "light": LIGHT_QSS,
    "ocean": OCEAN_QSS,
    "sunset": SUNSET_QSS,
}
