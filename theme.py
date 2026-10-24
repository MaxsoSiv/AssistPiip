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
QPushButton#navButton:checked { font-weight: 600; background: #2b6cb0; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #ccc; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(47, 50, 55, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #ccc; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #ccc; border: none; padding: 0; }
QPushButton#titleButton:hover { background: rgba(58, 61, 66, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #ccc; border: none; padding: 0; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(43, 45, 49, 0.9); border: 1px solid #3a3d42; border-radius: 6px; padding: 4px 8px; color: #eee; }
QLineEdit#commandInput { background: rgba(43, 45, 49, 0.9); border: 1px solid #3a3d42; border-radius: 10px; padding: 0 14px; color: #eee; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #2b6cb0; }
QPushButton#primaryButton { background: #2b6cb0; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #3182ce; }
QPushButton#secondaryButton { background: rgba(58, 61, 66, 0.9); color: #ddd; border: none; border-radius: 8px; padding: 6px 14px; }
QPushButton#secondaryButton:hover { background: rgba(74, 77, 82, 0.9); }
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
QWidget#statusRow { background: #202225; }
QLabel#statusLabel { background: transparent; color: #aaa; padding-left: 4px; font-size: 11px; }
QLabel#versionLabel { color: #666b73; font-size: 10px; padding-left: 14px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QSizeGrip { background: transparent; width: 14px; height: 14px; }
QScrollBar::handle:vertical { background: rgba(58, 61, 66, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(30, 31, 34, 0.9); border: 1px solid #2b2d31; border-radius: 12px; color: #fff; padding: 10px; }
QPushButton#calcButton { background: rgba(43, 45, 49, 0.9); color: #fff; border: none; border-radius: 24px; font-weight: 500; padding: 0; }
QPushButton#calcButton:hover { background: rgba(58, 61, 66, 0.9); }
QPushButton#calcOperator { background: #2b6cb0; color: #fff; border: none; border-radius: 24px; font-weight: bold; padding: 0; }
QPushButton#calcOperator:hover { background: #3182ce; }
QPushButton#calcMemory { background: rgba(58, 61, 66, 0.9); color: #ddd; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcMemory:hover { background: rgba(74, 77, 82, 0.9); }
QPushButton#calcLogic { background: rgba(45, 55, 72, 0.9); color: #cbd5e0; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcLogic:hover { background: rgba(74, 85, 104, 0.9); }
QLabel#calcHistoryLabel { color: #aaa; font-size: 12px; }
QTableWidget { background: rgba(30, 31, 34, 0.85); border: 1px solid rgba(43, 45, 49, 0.8); border-radius: 10px; color: #ddd; gridline-color: transparent; }
QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(43, 45, 49, 0.5); }
QTableWidget::item:selected { background: #2b6cb0; color: #fff; }
QHeaderView::section { background: #2b2d31; color: #aaa; border: none; padding: 4px; }
QPushButton#monitorSearchBtn { background: #2b6cb0; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorSearchBtn:hover { background: #3182ce; }
QPushButton#monitorKillBtn { background: #5a1f1f; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorKillBtn:hover { background: #7a2a2a; }
QPushButton#monitorHelpBtn { background: #3a3d42; color: #ddd; border: none; border-radius: 12px; font-weight: bold; padding: 0; }
QPushButton#monitorHelpBtn:hover { background: #4a4d52; }

QPushButton { background: #2b2d31; color: #ddd; border: 1px solid #3a3d42; border-radius: 8px; padding: 6px 16px; font-weight: 500; }
QPushButton:hover { background: #3a3d42; }
QPushButton:pressed { background: #232529; }
QPushButton:disabled { color: #777; background: #2b2d31; }
QPushButton#primaryButton:pressed { background: #245a97; }
QPushButton#dangerButton:pressed { background: #471818; }
QPushButton#quickButton:pressed { background: #232529; }
QPushButton#navButton:pressed { background: #232529; }
QMenu { background: #2b2d31; color: #ddd; border: 1px solid #3a3d42; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 24px 7px 14px; border-radius: 6px; }
QMenu::item:selected { background: #2b6cb0; color: #fff; }
QMenu::item:disabled { color: #777; }
QMenu::separator { height: 1px; background: #3a3d42; margin: 5px 8px; }
QToolTip { background: #2b2d31; color: #ddd; border: 1px solid #2b6cb0; border-radius: 6px; padding: 5px 9px; font-size: 12px; }
QTabWidget::pane { border: 1px solid #3a3d42; border-radius: 8px; }
QTabBar::tab { padding: 7px 16px; color: #777; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { color: #2b6cb0; border-bottom: 2px solid #2b6cb0; }
QProgressBar { background: #2b2d31; border: 1px solid #3a3d42; border-radius: 6px; text-align: center; color: #ddd; }
QProgressBar::chunk { background: #2b6cb0; border-radius: 6px; }
QWidget#translateResult { background: rgba(30, 31, 34, 0.85); border: 1px solid #3a3d42; border-radius: 10px; }
QKeySequenceEdit { background: #2b2d31; color: #ddd; border: 1px solid #3a3d42; border-radius: 6px; padding: 4px 8px; }
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
QPushButton#navButton:checked { font-weight: 600; background: #2b6cb0; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #1a1b1e; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(208, 211, 216, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #1a1b1e; background: transparent; }
QPushButton#sidebarExit:hover { background: #e0b0b0; }
QPushButton#titleButton { background: transparent; color: #1a1b1e; border: none; padding: 0; }
QPushButton#titleButton:hover { background: rgba(208, 211, 216, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #1a1b1e; border: none; padding: 0; }
QPushButton#titleClose:hover { background: #c42b1c; color: #fff; border-radius: 6px; }
QLineEdit { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 6px; padding: 4px 8px; color: #1a1b1e; }
QLineEdit#commandInput { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 10px; padding: 0 14px; color: #1a1b1e; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #2b6cb0; }
QPushButton#primaryButton { background: #2b6cb0; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #3182ce; }
QPushButton#secondaryButton { background: rgba(208, 211, 216, 0.9); color: #1a1b1e; border: none; border-radius: 8px; padding: 6px 14px; }
QPushButton#secondaryButton:hover { background: rgba(192, 195, 200, 0.9); }
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
QWidget#statusRow { background: #d0d3d8; }
QLabel#statusLabel { background: transparent; color: #333; padding-left: 4px; font-size: 11px; }
QLabel#versionLabel { color: #8a8d92; font-size: 10px; padding-left: 14px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QSizeGrip { background: transparent; width: 14px; height: 14px; }
QScrollBar::handle:vertical { background: rgba(192, 195, 200, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 12px; color: #1a1b1e; padding: 10px; }
QPushButton#calcButton { background: rgba(232, 234, 237, 0.9); color: #1a1b1e; border: none; border-radius: 24px; font-weight: 500; padding: 0; }
QPushButton#calcButton:hover { background: rgba(208, 211, 216, 0.9); }
QPushButton#calcOperator { background: #2b6cb0; color: #fff; border: none; border-radius: 24px; font-weight: bold; padding: 0; }
QPushButton#calcOperator:hover { background: #3182ce; }
QPushButton#calcMemory { background: rgba(208, 211, 216, 0.9); color: #1a1b1e; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcMemory:hover { background: rgba(192, 195, 200, 0.9); }
QPushButton#calcLogic { background: rgba(192, 195, 200, 0.9); color: #1a1b1e; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcLogic:hover { background: rgba(160, 163, 168, 0.9); }
QLabel#calcHistoryLabel { color: #666; font-size: 12px; }
QTableWidget { background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(192, 195, 200, 0.8); border-radius: 10px; color: #1a1b1e; gridline-color: transparent; }
QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(224, 227, 232, 0.5); }
QTableWidget::item:selected { background: #2b6cb0; color: #fff; }
QHeaderView::section { background: #d0d3d8; color: #333; border: none; padding: 4px; }
QPushButton#monitorSearchBtn { background: #2b6cb0; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorSearchBtn:hover { background: #3182ce; }
QPushButton#monitorKillBtn { background: #5a1f1f; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorKillBtn:hover { background: #7a2a2a; }
QPushButton#monitorHelpBtn { background: #c0c3c8; color: #1a1b1e; border: none; border-radius: 12px; font-weight: bold; padding: 0; }
QPushButton#monitorHelpBtn:hover { background: #b0b3b8; }

QPushButton { background: #ffffff; color: #1a1b1e; border: 1px solid #c0c3c8; border-radius: 8px; padding: 6px 16px; font-weight: 500; }
QPushButton:hover { background: #eceef1; }
QPushButton:pressed { background: #dfe2e6; }
QPushButton:disabled { color: #888; background: #ffffff; }
QPushButton#primaryButton:pressed { background: #245a97; }
QPushButton#dangerButton:pressed { background: #471818; }
QPushButton#quickButton:pressed { background: #dfe2e6; }
QPushButton#navButton:pressed { background: #dfe2e6; }
QMenu { background: #ffffff; color: #1a1b1e; border: 1px solid #c0c3c8; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 24px 7px 14px; border-radius: 6px; }
QMenu::item:selected { background: #2b6cb0; color: #fff; }
QMenu::item:disabled { color: #888; }
QMenu::separator { height: 1px; background: #c0c3c8; margin: 5px 8px; }
QToolTip { background: #ffffff; color: #1a1b1e; border: 1px solid #2b6cb0; border-radius: 6px; padding: 5px 9px; font-size: 12px; }
QTabWidget::pane { border: 1px solid #c0c3c8; border-radius: 8px; }
QTabBar::tab { padding: 7px 16px; color: #888; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { color: #2b6cb0; border-bottom: 2px solid #2b6cb0; }
QProgressBar { background: #ffffff; border: 1px solid #c0c3c8; border-radius: 6px; text-align: center; color: #1a1b1e; }
QProgressBar::chunk { background: #2b6cb0; border-radius: 6px; }
QWidget#translateResult { background: rgba(255, 255, 255, 0.9); border: 1px solid #c0c3c8; border-radius: 10px; }
QKeySequenceEdit { background: #ffffff; color: #1a1b1e; border: 1px solid #c0c3c8; border-radius: 6px; padding: 4px 8px; }
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
QPushButton#navButton:checked { font-weight: 600; background: #00b4d8; color: #fff; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #c9d6e8; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(17, 34, 64, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #c9d6e8; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #c9d6e8; border: none; padding: 0; }
QPushButton#titleButton:hover { background: rgba(17, 34, 64, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #c9d6e8; border: none; padding: 0; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(17, 34, 64, 0.9); border: 1px solid #1d3557; border-radius: 6px; padding: 4px 8px; color: #e0e0e0; }
QLineEdit#commandInput { background: rgba(17, 34, 64, 0.9); border: 1px solid #1d3557; border-radius: 10px; padding: 0 14px; color: #e0e0e0; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #00b4d8; }
QPushButton#primaryButton { background: #00b4d8; color: #fff; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #48cae4; }
QPushButton#secondaryButton { background: rgba(29, 53, 87, 0.9); color: #c9d6e8; border: none; border-radius: 8px; padding: 6px 14px; }
QPushButton#secondaryButton:hover { background: rgba(42, 74, 115, 0.9); }
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
QWidget#statusRow { background: #112240; }
QLabel#statusLabel { background: transparent; color: #8ca3c7; padding-left: 4px; font-size: 11px; }
QLabel#versionLabel { color: #45607f; font-size: 10px; padding-left: 14px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QSizeGrip { background: transparent; width: 14px; height: 14px; }
QScrollBar::handle:vertical { background: rgba(29, 53, 87, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(13, 31, 59, 0.9); border: 1px solid #1d3557; border-radius: 12px; color: #e0e0e0; padding: 10px; }
QPushButton#calcButton { background: rgba(17, 34, 64, 0.9); color: #c9d6e8; border: none; border-radius: 24px; font-weight: 500; padding: 0; }
QPushButton#calcButton:hover { background: rgba(29, 53, 87, 0.9); }
QPushButton#calcOperator { background: #00b4d8; color: #fff; border: none; border-radius: 24px; font-weight: bold; padding: 0; }
QPushButton#calcOperator:hover { background: #48cae4; }
QPushButton#calcMemory { background: rgba(29, 53, 87, 0.9); color: #c9d6e8; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcMemory:hover { background: rgba(42, 74, 115, 0.9); }
QPushButton#calcLogic { background: rgba(23, 58, 94, 0.9); color: #c9d6e8; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcLogic:hover { background: rgba(29, 53, 87, 0.9); }
QLabel#calcHistoryLabel { color: #8ca3c7; font-size: 12px; }
QTableWidget { background: rgba(13, 31, 59, 0.85); border: 1px solid rgba(17, 34, 64, 0.8); border-radius: 10px; color: #c9d6e8; gridline-color: transparent; }
QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(17, 34, 64, 0.5); }
QTableWidget::item:selected { background: #00b4d8; color: #fff; }
QHeaderView::section { background: #112240; color: #8ca3c7; border: none; padding: 4px; }
QPushButton#monitorSearchBtn { background: #00b4d8; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorSearchBtn:hover { background: #48cae4; }
QPushButton#monitorKillBtn { background: #5a1f1f; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorKillBtn:hover { background: #7a2a2a; }
QPushButton#monitorHelpBtn { background: #1d3557; color: #c9d6e8; border: none; border-radius: 12px; font-weight: bold; padding: 0; }
QPushButton#monitorHelpBtn:hover { background: #2a4a73; }

QPushButton { background: #112240; color: #c9d6e8; border: 1px solid #1d3557; border-radius: 8px; padding: 6px 16px; font-weight: 500; }
QPushButton:hover { background: #1d3557; }
QPushButton:pressed { background: #0d1b33; }
QPushButton:disabled { color: #5f7799; background: #112240; }
QPushButton#primaryButton:pressed { background: #0094b5; }
QPushButton#dangerButton:pressed { background: #471818; }
QPushButton#quickButton:pressed { background: #0d1b33; }
QPushButton#navButton:pressed { background: #0d1b33; }
QMenu { background: #112240; color: #c9d6e8; border: 1px solid #1d3557; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 24px 7px 14px; border-radius: 6px; }
QMenu::item:selected { background: #00b4d8; color: #fff; }
QMenu::item:disabled { color: #5f7799; }
QMenu::separator { height: 1px; background: #1d3557; margin: 5px 8px; }
QToolTip { background: #112240; color: #c9d6e8; border: 1px solid #00b4d8; border-radius: 6px; padding: 5px 9px; font-size: 12px; }
QTabWidget::pane { border: 1px solid #1d3557; border-radius: 8px; }
QTabBar::tab { padding: 7px 16px; color: #5f7799; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { color: #00b4d8; border-bottom: 2px solid #00b4d8; }
QProgressBar { background: #112240; border: 1px solid #1d3557; border-radius: 6px; text-align: center; color: #c9d6e8; }
QProgressBar::chunk { background: #00b4d8; border-radius: 6px; }
QWidget#translateResult { background: rgba(13, 31, 59, 0.85); border: 1px solid #1d3557; border-radius: 10px; }
QKeySequenceEdit { background: #112240; color: #c9d6e8; border: 1px solid #1d3557; border-radius: 6px; padding: 4px 8px; }
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
QPushButton#navButton:checked { font-weight: 600; background: #fca311; color: #000; }
QPushButton#sidebarBottom { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #fdf0d5; background: transparent; }
QPushButton#sidebarBottom:hover { background: rgba(94, 40, 18, 0.7); }
QPushButton#sidebarExit { text-align: left; padding-left: 14px; border: none; border-radius: 8px; color: #fdf0d5; background: transparent; }
QPushButton#sidebarExit:hover { background: #5a1f1f; }
QPushButton#titleButton { background: transparent; color: #fdf0d5; border: none; padding: 0; }
QPushButton#titleButton:hover { background: rgba(94, 40, 18, 0.8); border-radius: 6px; }
QPushButton#titleClose { background: transparent; color: #fdf0d5; border: none; padding: 0; }
QPushButton#titleClose:hover { background: #c42b1c; border-radius: 6px; }
QLineEdit { background: rgba(61, 20, 20, 0.9); border: 1px solid #5e2812; border-radius: 6px; padding: 4px 8px; color: #fdf0d5; }
QLineEdit#commandInput { background: rgba(61, 20, 20, 0.9); border: 1px solid #5e2812; border-radius: 10px; padding: 0 14px; color: #fdf0d5; font-size: 14px; }
QLineEdit#commandInput:focus { border-color: #fca311; }
QPushButton#primaryButton { background: #fca311; color: #000; border: none; border-radius: 10px; padding: 0 24px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #ffb703; }
QPushButton#secondaryButton { background: rgba(94, 40, 18, 0.9); color: #fdf0d5; border: none; border-radius: 8px; padding: 6px 14px; }
QPushButton#secondaryButton:hover { background: rgba(122, 54, 24, 0.9); }
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
QWidget#statusRow { background: #3d1414; }
QLabel#statusLabel { background: transparent; color: #fca311; padding-left: 4px; font-size: 11px; }
QLabel#versionLabel { color: #8a4a3a; font-size: 10px; padding-left: 14px; }
QScrollBar:vertical { border: none; background: transparent; width: 10px; }
QSizeGrip { background: transparent; width: 14px; height: 14px; }
QScrollBar::handle:vertical { background: rgba(94, 40, 18, 0.8); min-height: 20px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QLineEdit#calcDisplay { background: rgba(31, 8, 8, 0.9); border: 1px solid #5e2812; border-radius: 12px; color: #fdf0d5; padding: 10px; }
QPushButton#calcButton { background: rgba(61, 20, 20, 0.9); color: #fdf0d5; border: none; border-radius: 24px; font-weight: 500; padding: 0; }
QPushButton#calcButton:hover { background: rgba(94, 40, 18, 0.9); }
QPushButton#calcOperator { background: #fca311; color: #000; border: none; border-radius: 24px; font-weight: bold; padding: 0; }
QPushButton#calcOperator:hover { background: #ffb703; }
QPushButton#calcMemory { background: rgba(94, 40, 18, 0.9); color: #fdf0d5; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcMemory:hover { background: rgba(122, 54, 24, 0.9); }
QPushButton#calcLogic { background: rgba(74, 28, 21, 0.9); color: #fdf0d5; border: none; border-radius: 24px; padding: 0; }
QPushButton#calcLogic:hover { background: rgba(94, 40, 18, 0.9); }
QLabel#calcHistoryLabel { color: #fca311; font-size: 12px; }
QTableWidget { background: rgba(31, 8, 8, 0.85); border: 1px solid rgba(61, 20, 20, 0.8); border-radius: 10px; color: #fdf0d5; gridline-color: transparent; }
QTableWidget::item { padding: 4px; border-bottom: 1px solid rgba(61, 20, 20, 0.5); }
QTableWidget::item:selected { background: #fca311; color: #000; }
QHeaderView::section { background: #3d1414; color: #fca311; border: none; padding: 4px; }
QPushButton#monitorSearchBtn { background: #fca311; color: #000; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorSearchBtn:hover { background: #ffb703; }
QPushButton#monitorKillBtn { background: #5a1f1f; color: #fff; border: none; border-radius: 4px; font-size: 11px; padding: 0; }
QPushButton#monitorKillBtn:hover { background: #7a2a2a; }
QPushButton#monitorHelpBtn { background: #5e2812; color: #fdf0d5; border: none; border-radius: 12px; font-weight: bold; padding: 0; }
QPushButton#monitorHelpBtn:hover { background: #7a3a1e; }

QPushButton { background: #3d1414; color: #fdf0d5; border: 1px solid #5e2812; border-radius: 8px; padding: 6px 16px; font-weight: 500; }
QPushButton:hover { background: #4d1a17; }
QPushButton:pressed { background: #331010; }
QPushButton:disabled { color: #8a5a4a; background: #3d1414; }
QPushButton#primaryButton:pressed { background: #d98c0a; }
QPushButton#dangerButton:pressed { background: #471818; }
QPushButton#quickButton:pressed { background: #331010; }
QPushButton#navButton:pressed { background: #331010; }
QMenu { background: #3d1414; color: #fdf0d5; border: 1px solid #5e2812; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 24px 7px 14px; border-radius: 6px; }
QMenu::item:selected { background: #fca311; color: #000; }
QMenu::item:disabled { color: #8a5a4a; }
QMenu::separator { height: 1px; background: #5e2812; margin: 5px 8px; }
QToolTip { background: #3d1414; color: #fdf0d5; border: 1px solid #fca311; border-radius: 6px; padding: 5px 9px; font-size: 12px; }
QTabWidget::pane { border: 1px solid #5e2812; border-radius: 8px; }
QTabBar::tab { padding: 7px 16px; color: #8a5a4a; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { color: #fca311; border-bottom: 2px solid #fca311; }
QProgressBar { background: #3d1414; border: 1px solid #5e2812; border-radius: 6px; text-align: center; color: #fdf0d5; }
QProgressBar::chunk { background: #fca311; border-radius: 6px; }
QWidget#translateResult { background: rgba(31, 8, 8, 0.85); border: 1px solid #5e2812; border-radius: 10px; }
QKeySequenceEdit { background: #3d1414; color: #fdf0d5; border: 1px solid #5e2812; border-radius: 6px; padding: 4px 8px; }
"""

THEMES = {
    "dark": DARK_QSS,
    "light": LIGHT_QSS,
    "ocean": OCEAN_QSS,
    "sunset": SUNSET_QSS,
}
