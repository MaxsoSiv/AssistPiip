from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem
)

AVATAR_COLORS = {
    "dark": ((43, 108, 176), (0, 180, 216)),
    "light": ((43, 108, 176), (0, 180, 216)),
    "ocean": ((0, 119, 182), (0, 180, 216)),
    "sunset": ((252, 163, 17), (255, 107, 107)),
    "purple": ((139, 92, 246), (196, 140, 255)),
    "pink": ((236, 72, 153), (244, 114, 182)),
}

USER_COLORS = ((252, 163, 17), (255, 107, 107))


def _bubble_avatar(letter, c1, c2):
    pix = QPixmap(36, 36)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QLinearGradient(0, 0, 36, 36)
    grad.setColorAt(0.0, QColor(*c1))
    grad.setColorAt(1.0, QColor(*c2))
    painter.setBrush(grad)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, 36, 36)

    painter.setPen(QColor(255, 255, 255))
    font = QFont()
    font.setPixelSize(15)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    painter.end()
    return pix


class ChatView(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._accent_hex = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._list = QListWidget()
        self._list.setObjectName("chatList")
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._list)

    def set_theme(self, theme: str, accent_hex: str = ""):
        self._theme = theme
        self._accent_hex = accent_hex

    def clear(self):
        self._list.clear()

    def add_message(self, role: str, text: str, timestamp: str = ""):
        is_assistant = (role == "assistant")
        row = QWidget()
        head = QHBoxLayout(row)
        head.setContentsMargins(6, 3, 6, 3)
        head.setSpacing(8)

        if is_assistant:
            c1, c2 = AVATAR_COLORS.get(self._settings.theme, AVATAR_COLORS["dark"])
            if self._accent_hex:
                c1, c2 = self._accent_hex, None
        else:
            c1, c2 = USER_COLORS

        avatar = QLabel()
        avatar.setPixmap(self._make_avatar("P" if is_assistant else "Я", c1, c2))
        avatar.setFixedSize(30, 30)
        avatar.setScaledContents(True)

        bubble = QFrame()
        bubble.setObjectName("chatBubbleAssistant" if is_assistant else "chatBubbleUser")
        bubble.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(12, 7, 12, 8)
        inner.setSpacing(2)

        head_row = QHBoxLayout()
        head_row.setSpacing(8)
        name = QLabel("AssistPiip" if is_assistant else "Вы")
        name.setObjectName("chatName" if is_assistant else "chatNameUser")
        head_row.addWidget(name)

        if timestamp:
            shown = timestamp[11:16] if len(timestamp) >= 16 else timestamp
            time_lbl = QLabel(shown)
            time_lbl.setObjectName("chatTime")
            head_row.addWidget(time_lbl)
        head_row.addStretch()
        inner.addLayout(head_row)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setMaximumWidth(440)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setTextFormat(Qt.TextFormat.PlainText if not is_assistant else Qt.TextFormat.AutoText)
        inner.addWidget(body)

        if is_assistant:
            head.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(bubble, 0, Qt.AlignmentFlag.AlignTop)
            head.addStretch()
        else:
            head.addStretch()
            head.addWidget(bubble, 0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        item = QListWidgetItem()
        self._list.addItem(item)
        self._list.setItemWidget(item, row)
        self._relayout_rows()
        QTimer.singleShot(0, self._list.scrollToBottom)

    def _relayout_rows(self):
        width = self._list.viewport().width() - 4
        if width <= 50:
            return
        for i in range(self._list.count()):
            item = self._list.item(i)
            widget = self._list.itemWidget(item)
            if widget is None:
                continue
            widget.setFixedWidth(width)
            height = widget.layout().heightForWidth(width)
            if height < 0:
                height = widget.sizeHint().height()
            item.setSizeHint(QSize(width, max(int(height) + 1, 44)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_rows()

    def _make_avatar(self, letter, c1, c2):
        if isinstance(c1, str):
            base = QColor(c1)
            lighter = base.lighter(140)
        else:
            base = QColor(*c1)
            lighter = QColor(*c2) if c2 else base.lighter(140)
        return _bubble_avatar(letter, (base.red(), base.green(), base.blue()),
                              (lighter.red(), lighter.green(), lighter.blue()))
