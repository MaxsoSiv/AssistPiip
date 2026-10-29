import threading

import psutil
import shiboken6
import webbrowser
from urllib.parse import quote
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QLabel
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QColor

PROTECTED_PROCESSES = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "explorer.exe", "svchost.exe"
}

HELP_TEXT = """
<b>Расшифровка цветов в мониторе процессов:</b><br><br>

🟢 <b>Безопасно (Зелёный):</b> Процесс находится в системных папках (например, <code>C:\\Program Files\\</code>) или является известным системным компонентом Windows.<br><br>

🟡 <b>Неизвестно (Оранжевый):</b> Процесс имеет доступный путь к файлу, но расположен в нестандартном месте (например, на другом диске <code>D:\\Games\\...</code> или в папке <code>C:\\Python312\\</code>). Как правило, это безопасно, но рекомендуется проверить.<br><br>

🔴 <b>Подозрительно (Красный):</b> Процесс скрывает свой путь (нет прав доступа) или запущен из временных/пользовательских папок (<code>AppData</code>, <code>Temp</code>).<br><br>

<i>⚠️ Важное примечание:</i><br>
Многие легитимные программы устанавливаются в папки пользователя (AppData). Например, <b>Discord</b>, <b>Zed</b>, <b>python.exe</b> и <b>ruff.exe</b> могут быть помечены красным цветом. Это <u>не означает</u>, что они являются вирусами. Если вы знаете, что это за программа — не закрывайте её.<br><br>
Если вы не уверены в процессе, нажмите кнопку «Поиск», чтобы узнать о нём в интернете.
"""

class _ScanWorker(QObject):
    finished = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            result = scan_processes()
        except Exception:
            result = []
        if shiboken6.isValid(self):
            self.finished.emit(result)


def scan_processes() -> list:
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            mem_info = proc.info['memory_info']
            if not name or mem_info is None:
                continue
            if pid <= 4 or name.lower() in PROTECTED_PROCESSES:
                continue

            try:
                exe_path = proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                exe_path = ""

            processes.append({
                'pid': pid,
                'name': name,
                'mem': mem_info.rss / (1024 * 1024),
                'path': exe_path
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x['mem'], reverse=True)
    return processes


class MonitorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Монитор процессов")
        title.setStyleSheet("font-size:22px; font-weight:600;")
        top.addWidget(title)
        top.addStretch()

        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)

        lbl_green = QLabel("● Безопасно")
        lbl_green.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 13px;")

        lbl_orange = QLabel("● Неизвестно")
        lbl_orange.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 13px;")

        lbl_red = QLabel("● Подозрительно")
        lbl_red.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px;")

        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setObjectName("monitorHelpBtn")
        btn_help.setToolTip("Что означают цвета?")
        btn_help.clicked.connect(self._show_help)

        legend_layout.addWidget(lbl_green)
        legend_layout.addWidget(lbl_orange)
        legend_layout.addWidget(lbl_red)
        legend_layout.addWidget(btn_help)

        top.addLayout(legend_layout)
        top.addSpacing(20)

        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.setObjectName("primaryButton")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.clicked.connect(self.refresh_processes)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Имя", "PID", "ОЗУ (МБ)", "Статус", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table, 1)
        self.refresh_processes()

    def _show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Справка по цветам")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(HELP_TEXT)
        msg.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_processes()

    def refresh_processes(self):
        if self._scan_worker is not None:
            return
        self.btn_refresh.setEnabled(False)
        self.table.setRowCount(0)

        self._scan_worker = _ScanWorker(self)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.start()

    def _on_scan_done(self, processes):
        if not shiboken6.isValid(self):
            return
        self._scan_worker = None
        self.btn_refresh.setEnabled(True)
        for p in processes[:50]:
            self._add_process_row(p)

    def _add_process_row(self, p):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(p['name']))
        self.table.setItem(row, 1, QTableWidgetItem(str(p['pid'])))

        mem_item = QTableWidgetItem(f"{p['mem']:.1f}")
        mem_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, mem_item)

        status_text = "Безопасно"
        status_color = QColor("#2ecc71")

        path_lower = p['path'].lower()
        if not p['path'] or "temp" in path_lower or "appdata" in path_lower:
            status_text = "Подозрительно"
            status_color = QColor("#e74c3c")
        elif len(p['name']) <= 8 and any(c.isdigit() for c in p['name']):
            status_text = "Подозрительно"
            status_color = QColor("#e74c3c")
        elif "program files" not in path_lower and p['path']:
            status_text = "Неизвестно"
            status_color = QColor("#f39c12")

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(status_color)
        self.table.setItem(row, 3, status_item)

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 4, 4, 4)
        action_layout.setSpacing(4)

        btn_search = QPushButton("Поиск")
        btn_search.setFixedSize(60, 24)
        btn_search.setObjectName("monitorSearchBtn")
        btn_search.clicked.connect(lambda checked, n=p['name']: self._search_process(n))

        btn_kill = QPushButton("Завершить")
        btn_kill.setFixedSize(70, 24)
        btn_kill.setObjectName("monitorKillBtn")
        btn_kill.clicked.connect(lambda checked, pid=p['pid'], n=p['name']: self._kill_process(pid, n))

        action_layout.addWidget(btn_search)
        action_layout.addWidget(btn_kill)

        self.table.setCellWidget(row, 4, action_widget)

    def _search_process(self, name):
        url = "https://www.google.com/search?q=" + quote(f"что за процесс {name}")
        webbrowser.open(url)

    def _kill_process(self, pid, name):
        reply = QMessageBox.question(
            self, "Завершение процесса",
            f"Вы уверены, что хотите завершить процесс «{name}» (PID: {pid})?\n"
            "Это может привести к потере несохранённых данных или сбою программы.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=3)
                self.refresh_processes()
            except psutil.AccessDenied:
                QMessageBox.warning(
                    self, "Отказано в доступе",
                    "У вас нет прав для завершения этого процесса.\n"
                    "Возможно, он запущен от имени администратора или системы."
                )
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    self.refresh_processes()
                except psutil.AccessDenied:
                    QMessageBox.warning(self, "Ошибка", "Не удалось завершить процесс принудительно.")
            except psutil.NoSuchProcess:
                self.refresh_processes()
