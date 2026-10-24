import ast
import math
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLineEdit, QComboBox, QLabel, QListWidget, QListWidgetItem, QStackedWidget,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class SafeEvaluator:
    ALLOWED_FUNCS = {
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
        'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
        'ln': math.log, 'log10': math.log10, 'log2': math.log2,
        'sqrt': math.sqrt, 'cbrt': lambda x: math.copysign(abs(x) ** (1 / 3), x),
        'factorial': lambda x: math.factorial(int(x)),
        'cot': lambda x: 1 / math.tan(x),
        'acot': lambda x: math.atan(1 / x) if x != 0 else math.pi / 2
    }

    ALLOWED_NAMES = {
        'pi': math.pi,
        'e': math.e
    }

    @classmethod
    def evaluate(cls, expr: str) -> float | int:
        expr = expr.replace("XOR", "\x00")
        expr = expr.replace("AND", "&").replace("OR", "|").replace("NOT", "~")
        expr = expr.replace("^", "**").replace("\x00", "^")
        expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
        expr = expr.replace("mod", "%")

        tree = ast.parse(expr, mode='eval')
        return cls._eval_node(tree.body)

    @classmethod
    def _eval_node(cls, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.FloorDiv): return left // right
            if isinstance(node.op, ast.Mod): return left % right
            if isinstance(node.op, ast.Pow): return left ** right
            if isinstance(node.op, ast.BitAnd): return int(left) & int(right)
            if isinstance(node.op, ast.BitOr): return int(left) | int(right)
            if isinstance(node.op, ast.BitXor): return int(left) ^ int(right)
            if isinstance(node.op, ast.LShift): return int(left) << int(right)
            if isinstance(node.op, ast.RShift): return int(left) >> int(right)
        if isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand)
            if isinstance(node.op, ast.USub): return -operand
            if isinstance(node.op, ast.UAdd): return +operand
            if isinstance(node.op, ast.Invert): return ~int(operand)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in cls.ALLOWED_FUNCS:
                args = [cls._eval_node(arg) for arg in node.args]
                return cls.ALLOWED_FUNCS[node.func.id](*args)
            if isinstance(node.func, ast.Name) and node.func.id == 'factorial':
                args = [cls._eval_node(arg) for arg in node.args]
                return math.factorial(int(args[0]))
        if isinstance(node, ast.Name) and node.id in cls.ALLOWED_NAMES:
            return cls.ALLOWED_NAMES[node.id]
        raise ValueError("Недопустимое выражение")


class CalculatorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory = 0.0
        self._history = []
        self._current_base = 10
        self._buttons = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        top_row = QHBoxLayout()
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Обычный", "Инженерный", "Программистский"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        top_row.addWidget(self._mode_combo)

        self._base_combo = QComboBox()
        self._base_combo.addItems(["DEC", "HEX", "OCT", "BIN"])
        self._base_combo.setVisible(False)
        self._base_combo.currentTextChanged.connect(self._on_base_changed)
        top_row.addWidget(self._base_combo)

        top_row.addStretch()
        main_layout.addLayout(top_row)

        self._display = QLineEdit()
        self._display.setObjectName("calcDisplay")
        self._display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._display.setFixedHeight(80)
        self._display.returnPressed.connect(self._calculate)

        display_center = QHBoxLayout()
        display_center.addStretch()
        display_center.addWidget(self._display, 3)
        display_center.addStretch()
        main_layout.addLayout(display_center)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_standard_ui())
        self._stack.addWidget(self._create_engineering_ui())
        self._stack.addWidget(self._create_programmer_ui())
        self._stack.setMaximumWidth(500)

        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self._stack, 3)
        center_layout.addStretch()
        main_layout.addLayout(center_layout, 1)

        history_widget = QWidget()
        history_widget.setMaximumWidth(500)
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)

        history_label = QLabel("История")
        history_label.setObjectName("calcHistoryLabel")
        history_layout.addWidget(history_label)

        self._history_list = QListWidget()
        self._history_list.setFixedHeight(100)
        self._history_list.itemClicked.connect(self._on_history_clicked)
        history_layout.addWidget(self._history_list)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(history_widget, 3)
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)

    def _create_standard_ui(self):
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("MC", 0, 0), ("MR", 0, 1), ("M+", 0, 2), ("M-", 0, 3),
            ("AC", 1, 0), ("(", 1, 1), (")", 1, 2), ("/", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("*", 2, 3),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("-", 3, 3),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("+", 4, 3),
            ("0", 5, 0), (".", 5, 1), ("%", 5, 2), ("=", 5, 3),
        ]

        for text, r, c in buttons:
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setObjectName("calcButton")
            if text in ("/", "*", "-", "+", "=", "AC"):
                btn.setObjectName("calcOperator")
            elif text in ("MC", "MR", "M+", "M-"):
                btn.setObjectName("calcMemory")
            btn.clicked.connect(lambda checked, t=text: self._on_button_clicked(t))
            grid.addWidget(btn, r, c)
            self._buttons.append(btn)

        for i in range(6):
            grid.setRowStretch(i, 1)
        for i in range(4):
            grid.setColumnStretch(i, 1)

        return widget

    def _create_engineering_ui(self):
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("MC", 0, 0), ("MR", 0, 1), ("M+", 0, 2), ("M-", 0, 3), ("AC", 0, 4),
            ("sin", 1, 0), ("cos", 1, 1), ("tan", 1, 2), ("cot", 1, 3), ("/", 1, 4),
            ("asin", 2, 0), ("acos", 2, 1), ("atan", 2, 2), ("acot", 2, 3), ("*", 2, 4),
            ("sinh", 3, 0), ("cosh", 3, 1), ("tanh", 3, 2), ("ln", 3, 3), ("-", 3, 4),
            ("log10", 4, 0), ("log2", 4, 1), ("sqrt", 4, 2), ("cbrt", 4, 3), ("+", 4, 4),
            ("pi", 5, 0), ("e", 5, 1), ("x^y", 5, 2), ("n!", 5, 3), ("=", 5, 4),
            ("7", 6, 0), ("8", 6, 1), ("9", 6, 2), ("(", 6, 3), (")", 6, 4),
            ("4", 7, 0), ("5", 7, 1), ("6", 7, 2), ("0", 7, 3), (".", 7, 4),
            ("1", 8, 0), ("2", 8, 1), ("3", 8, 2), ("%", 8, 3), (" ", 8, 4),
        ]

        for text, r, c in buttons:
            if text == " ":
                continue
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setObjectName("calcButton")
            if text in ("/", "*", "-", "+", "=", "AC"):
                btn.setObjectName("calcOperator")
            elif text in ("MC", "MR", "M+", "M-"):
                btn.setObjectName("calcMemory")
            btn.clicked.connect(lambda checked, t=text: self._on_button_clicked(t))
            grid.addWidget(btn, r, c)
            self._buttons.append(btn)

        for i in range(9):
            grid.setRowStretch(i, 1)
        for i in range(5):
            grid.setColumnStretch(i, 1)

        return widget

    def _create_programmer_ui(self):
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("MC", 0, 0), ("MR", 0, 1), ("M+", 0, 2), ("M-", 0, 3), ("AC", 0, 4),
            ("AND", 1, 0), ("OR", 1, 1), ("XOR", 1, 2), ("NOT", 1, 3), ("/", 1, 4),
            ("<<", 2, 0), (">>", 2, 1), ("(", 2, 2), (")", 2, 3), ("*", 2, 4),
            ("7", 3, 0), ("8", 3, 1), ("9", 3, 2), ("A", 3, 3), ("-", 3, 4),
            ("4", 4, 0), ("5", 4, 1), ("6", 4, 2), ("B", 4, 3), ("+", 4, 4),
            ("1", 5, 0), ("2", 5, 1), ("3", 5, 2), ("C", 5, 3), ("=", 5, 4),
            ("0", 6, 0), ("D", 6, 1), ("E", 6, 2), ("F", 6, 3), ("", 6, 4),
        ]

        self._hex_buttons = []
        for text, r, c in buttons:
            if text == "":
                continue
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setObjectName("calcButton")
            if text in ("/", "*", "-", "+", "="):
                btn.setObjectName("calcOperator")
            elif text in ("MC", "MR", "M+", "M-"):
                btn.setObjectName("calcMemory")
            elif text in ("AND", "OR", "XOR", "NOT", "<<", ">>"):
                btn.setObjectName("calcLogic")
            btn.clicked.connect(lambda checked, t=text: self._on_button_clicked(t))
            grid.addWidget(btn, r, c)
            self._buttons.append(btn)
            if text in ("A", "B", "C", "D", "E", "F"):
                self._hex_buttons.append(btn)
                btn.setVisible(False)

        for i in range(7):
            grid.setRowStretch(i, 1)
        for i in range(5):
            grid.setColumnStretch(i, 1)

        return widget

    def _on_button_clicked(self, text):
        if text in ("AC", "C"):
            self._display.clear()
            self._display.setToolTip("")
            return
        if text == "=":
            self._calculate()
            return
        if text == "MC":
            self._memory = 0.0
            return
        if text == "MR":
            self._display.setText(str(self._memory))
            return
        if text == "M+":
            try:
                val = float(self._display.text())
                self._memory += val
            except ValueError:
                pass
            return
        if text == "M-":
            try:
                val = float(self._display.text())
                self._memory -= val
            except ValueError:
                pass
            return

        if text == "x^y":
            text = "**"
        elif text == "n!":
            text = "!"
        elif text == "pi":
            text = str(math.pi)
        elif text == "e":
            text = str(math.e)
        elif text in ("sin", "cos", "tan", "cot", "asin", "acos", "atan", "acot", "sinh", "cosh", "tanh", "ln", "log10", "log2", "sqrt", "cbrt"):
            text += "("

        current = self._display.text()
        if text in ("+", "-", "*", "/", "%", "**", "&", "|", "^", "<<", ">>", "AND", "OR", "XOR"):
            current = current.rstrip("+-*/%&|^<>")
        self._display.setText(current + text)

    def _convert_to_decimal(self, expr, base):
        if base == 10:
            return expr

        expr = expr.replace("XOR", "\x00").replace("AND", "&").replace("OR", "|").replace("NOT", "~")

        if base == 16:
            expr = re.sub(r'\b[0-9A-F]+\b', lambda m: str(int(m.group(0), 16)), expr)
        elif base == 8:
            expr = re.sub(r'\b[0-7]+\b', lambda m: str(int(m.group(0), 8)), expr)
        elif base == 2:
            expr = re.sub(r'\b[01]+\b', lambda m: str(int(m.group(0), 2)), expr)
        return expr

    def _convert_from_decimal(self, val, base):
        if base == 10:
            return str(val)
        if base == 16:
            return hex(int(val))[2:].upper()
        if base == 8:
            return oct(int(val))[2:]
        if base == 2:
            return bin(int(val))[2:]
        return str(val)

    def _calculate(self):
        expr = self._display.text().strip()
        if not expr:
            return

        try:
            if self._stack.currentIndex() == 2:
                base_name = self._base_combo.currentText()
                base = {"DEC": 10, "HEX": 16, "OCT": 8, "BIN": 2}[base_name]
                dec_expr = self._convert_to_decimal(expr, base)
                result = SafeEvaluator.evaluate(dec_expr)
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                display_result = self._convert_from_decimal(result, base)
                self._display.setText(display_result)
                self._add_to_history(f"{expr} = {display_result}")
            else:
                result = SafeEvaluator.evaluate(expr)
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 10)
                self._display.setText(str(result))
                self._add_to_history(f"{expr} = {result}")
            self._display.setToolTip("")
        except ZeroDivisionError:
            self._display.setText("Ошибка")
            self._display.setToolTip("Деление на ноль")
        except ValueError as e:
            self._display.setText("Ошибка")
            self._display.setToolTip(str(e))
        except Exception as e:
            self._display.setText("Ошибка")
            self._display.setToolTip(f"Некорректное выражение: {e}")

    def _add_to_history(self, text: str):
        self._history.append(text)
        if len(self._history) > 10:
            self._history.pop(0)
        self._history_list.clear()
        for item in reversed(self._history):
            self._history_list.addItem(item)

    def _on_history_clicked(self, item):
        text = item.text().split(" = ")[-1]
        self._display.setText(text)

    def _on_mode_changed(self, index):
        self._stack.setCurrentIndex(index)
        self._base_combo.setVisible(index == 2)
        for btn in self._hex_buttons:
            btn.setVisible(self._base_combo.currentText() == "HEX")

        if index == 2:
            self._on_base_changed(self._base_combo.currentText())

        QTimer.singleShot(0, self._update_fonts)

    def _on_base_changed(self, base_name):
        for btn in self._hex_buttons:
            btn.setVisible(base_name == "HEX")

        bases = {"DEC": 10, "HEX": 16, "OCT": 8, "BIN": 2}
        new_base = bases.get(base_name, 10)

        text = self._display.text().strip()
        if not text:
            self._current_base = new_base
            return

        try:
            dec_expr = self._convert_to_decimal(text, self._current_base)
            val = SafeEvaluator.evaluate(dec_expr)
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            new_text = self._convert_from_decimal(val, new_base)
            self._display.setText(new_text)
        except Exception:
            self._display.clear()
            self._display.setToolTip("Невозможно сконвертировать текущее значение")

        self._current_base = new_base
        QTimer.singleShot(0, self._update_fonts)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._update_fonts)

    def _update_fonts(self):
        for btn in self._buttons:
            if btn.isVisible():
                w = btn.width()
                h = btn.height()
                if w > 0 and h > 0:
                    size = max(10, min(24, int(min(w, h) * 0.4)))
                    f = btn.font()
                    f.setPointSize(size)
                    btn.setFont(f)

        h = self._display.height()
        if h > 0:
            size = max(20, min(36, int(h * 0.5)))
            f = self._display.font()
            f.setPointSize(size)
            f.setBold(True)
            self._display.setFont(f)
