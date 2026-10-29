from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QLabel,
    QTextEdit, QTextBrowser, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.utils import APP_VERSION

PRIVACY_TEXT = """
<h3>Политика конфиденциальности AssistPiip</h3>
<p><b>Дата последнего обновления:</b> 2026 г.</p>

<p>AssistPiip — это локальный десктопный ассистент для Windows. Мы уважаем вашу приватность и спроектировали приложение так, чтобы ваши данные оставались только на вашем компьютере.</p>

<h4>1. Буфер обмена</h4>
<p>Приложение автоматически сохраняет историю скопированного текста и изображений (до 50 элементов). Эти данные хранятся <b>исключительно локально</b> в папке <code>data/clipboard/</code> рядом с исполняемым файлом. Изображения сохраняются в формате PNG. Мы не передаём содержимое буфера обмена на серверы и не анализируем его.</p>

<h4>2. Файлы и приложения</h4>
<p>Приложение может открывать файлы, папки и приложения по команде пользователя. Оно не сканирует вашу файловую систему и не собирает информацию о ваших документах. Пути к файлам сохраняются только в ваших пользовательских командах в файле <code>data/commands.json</code>.</p>

<h4>3. Настройки и автозапуск</h4>
<p>Ваши настройки (тема, прозрачность, путь к браузеру) сохраняются локально с помощью системного реестра Windows (QSettings). Для автозапуска приложение использует ветку реестра <code>HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run</code>. Эти данные не покидают ваш компьютер.</p>

<h4>4. Сетевые подключения</h4>
<p>Приложение <b>не имеет встроенной аналитики, телеметрии или рекламы</b>. Оно не отправляет отчёты о падениях. В интернет AssistPiip обращается только по вашей инициативе: команды «айпи» и «пинг», перевод текста, а также проверка обновлений (сравнивается номер версии с сайтом проекта, проверку можно отключить в настройках). В фоновом режиме приложение в сеть не ходит.</p>

<h4>5. Удаление данных</h4>
<p>Вы можете в любой момент очистить историю буфера обмена, заметки и команды через интерфейс приложения. Полное удаление папки <code>data/</code> и удаление приложения приведёт к безвозвратному удалению всех локальных данных.</p>

<h4>6. Контакты</h4>
<p>По вопросам конфиденциальности вы можете связаться с разработчиком через сайт проекта (указан во вкладке «Контакты»).</p>
"""

TERMS_TEXT = """
<h3>Условия использования AssistPiip</h3>
<p><b>1. Предоставление «как есть»</b><br>
Приложение предоставляется бесплатно «как есть» (as is). Разработчик не несёт ответственности за возможные сбои в работе системы, потерю данных или иные последствия использования программы.</p>

<p><b>2. Использование по назначению</b><br>
Вы обязуетесь использовать AssistPiip только для законных целей и не применять его для автоматизации вредоносных действий, несанкционированного доступа или нарушения работы других программ.</p>

<p><b>3. Ответственность за данные</b><br>
Поскольку приложение сохраняет историю буфера обмена (которая может содержать пароли и личные данные), вы самостоятельно несёте ответственность за безопасность вашего компьютера и учётной записи Windows.</p>

<p><b>4. Изменения</b><br>
Разработчик оставляет за собой право обновлять приложение и данные условия без предварительного уведомления.</p>
"""

CONTACTS_TEXT = """
<h3>Контакты и обратная связь</h3>
<p>AssistPiip — независимый проект. Если вы нашли ошибку, у вас есть предложение по улучшению или вопрос по работе приложения, вы можете связаться с нами:</p>

<ul>
<li><b>Сайт проекта:</b> <a href="https://maxsosiv.github.io/AssistPiip/">maxsosiv.github.io/AssistPiip</a></li>
<li><b>GitHub:</b> <a href="https://github.com/MaxsoSiv/AssistPiip/">github.com/MaxsoSiv/AssistPiip</a></li>
<li><b>Электронная почта:</b> <a href="mailto:assistpiip@gmail.com">assistpiip@gmail.com</a></li>
</ul>

<p>Мы всегда рады обратной связи и стараемся отвечать на все конструктивные сообщения.</p>
"""


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О AssistPiip")
        self.resize(600, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()

        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_title = QLabel("AssistPiip")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: bold;")

        lbl_ver = QLabel(f"Версия: {APP_VERSION} (Beta)")
        lbl_ver.setStyleSheet("font-size: 14px; color: #888;")

        lbl_desc = QLabel(
            "Текстовый ассистент для Windows.\n\n"
            "Работает локально, не требует подключения к интернету и не собирает ваши данные."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; margin-top: 10px;")

        about_layout.addWidget(lbl_title)
        about_layout.addWidget(lbl_ver)
        about_layout.addWidget(lbl_desc)
        about_layout.addStretch()

        privacy_widget = QWidget()
        privacy_layout = QVBoxLayout(privacy_widget)
        privacy_layout.setContentsMargins(0, 0, 0, 0)
        privacy_edit = QTextEdit()
        privacy_edit.setReadOnly(True)
        privacy_edit.setHtml(PRIVACY_TEXT)
        privacy_edit.setStyleSheet("border: none; background: transparent;")
        privacy_layout.addWidget(privacy_edit)

        terms_widget = QWidget()
        terms_layout = QVBoxLayout(terms_widget)
        terms_layout.setContentsMargins(0, 0, 0, 0)
        terms_edit = QTextEdit()
        terms_edit.setReadOnly(True)
        terms_edit.setHtml(TERMS_TEXT)
        terms_edit.setStyleSheet("border: none; background: transparent;")
        terms_layout.addWidget(terms_edit)

        contacts_widget = QWidget()
        contacts_layout = QVBoxLayout(contacts_widget)
        contacts_layout.setContentsMargins(0, 0, 0, 0)
        contacts_edit = QTextBrowser()
        contacts_edit.setOpenExternalLinks(True)
        contacts_edit.setHtml(CONTACTS_TEXT)
        contacts_edit.setStyleSheet("border: none; background: transparent;")
        contacts_layout.addWidget(contacts_edit)

        self.tabs.addTab(about_widget, "О программе")
        self.tabs.addTab(privacy_widget, "Конфиденциальность")
        self.tabs.addTab(terms_widget, "Условия")
        self.tabs.addTab(contacts_widget, "Контакты")

        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
