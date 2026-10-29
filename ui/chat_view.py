import shiboken6
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont, QTextDocument
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

AVATAR_SIZE = 30
BODY_MAX_WIDTH = 440
ROW_MARGIN = 6
BUBBLE_V_MARGINS = 15
BUBBLE_H_MARGINS = 24
HEADER_HEIGHT = 18
SPACING = 2
BORDERS = 4
SAFETY = 4
MIN_ROW_HEIGHT = 58


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
        self._theme = settings.theme if settings else "dark"
        self._accent_hex = ""
        self._rows = []
        self._stream_item = None
        self._stream_body = None

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
        self._rows = []
        self._stream_item = None
        self._stream_body = None

    def add_message(self, role: str, text: str, timestamp: str = ""):
        is_assistant = (role == "assistant")
        row = QWidget()
        head = QHBoxLayout(row)
        head.setContentsMargins(ROW_MARGIN // 2, ROW_MARGIN // 2, ROW_MARGIN // 2, ROW_MARGIN // 2)
        head.setSpacing(8)

        if is_assistant:
            c1, c2 = AVATAR_COLORS.get(self._settings.theme, AVATAR_COLORS["dark"])
            if self._accent_hex:
                c1, c2 = self._accent_hex, None
        else:
            c1, c2 = USER_COLORS

        avatar = QLabel()
        avatar.setPixmap(self._make_avatar("P" if is_assistant else "Я", c1, c2))
        avatar.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
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
        body.setMaximumWidth(BODY_MAX_WIDTH)
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
        self._rows.append((item, body))
        self._relayout_rows()
        self._scroll_if_at_bottom(force=True)

    def stream_reset(self, text: str = ""):
        self._stream_item = None
        self._stream_body = None
        self.add_message("assistant", text)
        if self._rows:
            self._stream_item, self._stream_body = self._rows[-1]

    def stream_append(self, text: str):
        if self._stream_body is None or not shiboken6.isValid(self._stream_body):
            return
        self._stream_body.setText(text)
        self._relayout_single(self._stream_item, self._stream_body)
        self._scroll_if_at_bottom(force=True)

    def stream_end(self):
        self._stream_item = None
        self._stream_body = None

    def render_last_as_html(self, html_text: str):
        if not self._rows:
            return
        item, body = self._rows[-1]
        if not shiboken6.isValid(body):
            return
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setText(html_text)
        self._relayout_single(item, body)

    def _scroll_if_at_bottom(self, force=False):
        sb = self._list.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 24
        if force or at_bottom:
            QTimer.singleShot(0, self._list.scrollToBottom)

    def _relayout_single(self, item, body):
        row = self._list.itemWidget(item)
        if row is None:
            return
        width = self._list.viewport().width() - 4
        if width <= 80:
            return
        body_width = min(BODY_MAX_WIDTH, width - AVATAR_SIZE - 16 - BUBBLE_H_MARGINS - BORDERS) - 2
        if body_width < 60:
            return
        row.setFixedWidth(width)
        doc = QTextDocument()
        doc.setDefaultFont(body.font())
        if body.textFormat() == Qt.TextFormat.PlainText:
            doc.setPlainText(body.text())
        else:
            doc.setHtml(body.text())
        doc.setTextWidth(body_width)
        total = ROW_MARGIN + BUBBLE_V_MARGINS + BORDERS + HEADER_HEIGHT + SPACING + int(doc.size().height()) + SAFETY
        item.setSizeHint(QSize(width, max(total, MIN_ROW_HEIGHT)))

    def _relayout_rows(self):
        width = self._list.viewport().width() - 4
        if width <= 80:
            return
        body_width = min(BODY_MAX_WIDTH, width - AVATAR_SIZE - 16 - BUBBLE_H_MARGINS - BORDERS) - 2
        if body_width < 60:
            return
        for item, body in self._rows:
            row = self._list.itemWidget(item)
            if row is None:
                continue
            row.setFixedWidth(width)

            doc = QTextDocument()
            doc.setDefaultFont(body.font())
            if body.textFormat() == Qt.TextFormat.PlainText:
                doc.setPlainText(body.text())
            else:
                doc.setHtml(body.text())
            doc.setTextWidth(body_width)
            body_h = doc.size().height()

            total = ROW_MARGIN + BUBBLE_V_MARGINS + BORDERS + HEADER_HEIGHT + SPACING + int(body_h) + SAFETY
            item.setSizeHint(QSize(width, max(total, MIN_ROW_HEIGHT)))

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
