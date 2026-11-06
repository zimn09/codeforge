"""Output console with simple ANSI colour support."""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import theme

ANSI_RE = re.compile(r"\x1b\[([0-9;]*)([A-Za-z])")
PARTIAL_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*$")

ANSI_BASIC = {
    30: "#5a5a6e",
    31: "#ff6b6b",
    32: "#7bd88f",
    33: "#ffd479",
    34: "#6cb6ff",
    35: "#d19bff",
    36: "#63e6e2",
    37: "#e6e6f0",
    90: "#8b8ba7",
    91: "#ff9b9b",
    92: "#a8f0b8",
    93: "#ffe6a3",
    94: "#9ccfff",
    95: "#e3b8ff",
    96: "#9bf4f0",
    97: "#ffffff",
}

KIND_COLORS = {
    "stdout": "fg",
    "stderr": "red",
    "build": "yellow",
    "system": "fg_muted",
    "success": "green",
    "error": "red",
    "cmd": "accent",
    "input": "cyan",
}


def kind_color(kind: str) -> str:
    token = KIND_COLORS.get(kind, "fg")
    return getattr(theme, token.upper(), theme.FG)


class OutputConsole(QPlainTextEdit):
    """Read-only log that understands a useful subset of ANSI escapes."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("outputConsole")
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setMaximumBlockCount(20000)
        self.setFont(theme.monospace_font(11))
        self.setPlaceholderText("Run a file with F5 — output appears here.")
        self._pending = ""

    def set_font_size(self, size: int) -> None:
        self.setFont(theme.monospace_font(size))

    def feed(self, text: str, kind: str = "stdout") -> None:
        if not text:
            return

        data = self._pending + text
        self._pending = ""

        limit = len(data)
        partial = PARTIAL_ESCAPE_RE.search(data)
        if partial:
            # Hold back a partial escape sequence until the next chunk.
            self._pending = data[partial.start() :]
            limit = partial.start()

        base = QTextCharFormat()
        base.setForeground(_color(kind_color(kind)))
        current = QTextCharFormat(base)

        position = 0
        for match in ANSI_RE.finditer(data, 0, limit):
            if match.start() > position:
                self._write(data[position : match.start()], current)
            if match.group(2) == "m":
                current = self._apply_sgr(match.group(1), base)
            position = match.end()
        if position < limit:
            self._write(data[position:limit], current)

    def _write(self, text: str, fmt: QTextCharFormat) -> None:
        if not text:
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _apply_sgr(self, params: str, base: QTextCharFormat) -> QTextCharFormat:
        fmt = QTextCharFormat(base)
        codes = [int(part) if part else 0 for part in params.split(";")]

        index = 0
        while index < len(codes):
            code = codes[index]
            if code == 0:
                fmt = QTextCharFormat(base)
            elif code == 1:
                fmt.setFontWeight(QFont.Weight.Bold)
            elif code == 2:
                fmt.setForeground(_color(theme.FG_DIM))
            elif code == 3:
                fmt.setFontItalic(True)
            elif code == 4:
                fmt.setFontUnderline(True)
            elif code == 22:
                fmt.setFontWeight(QFont.Weight.Normal)
            elif code == 23:
                fmt.setFontItalic(False)
            elif code == 24:
                fmt.setFontUnderline(False)
            elif code == 39:
                fmt.setForeground(base.foreground())
            elif code in ANSI_BASIC:
                fmt.setForeground(_color(ANSI_BASIC[code]))
            elif code == 38 and index + 1 < len(codes):
                if codes[index + 1] == 5 and index + 2 < len(codes):
                    fmt.setForeground(_color(_xterm256(codes[index + 2])))
                    index += 2
                elif codes[index + 1] == 2 and index + 4 < len(codes):
                    fmt.setForeground(
                        _color(
                            f"#{codes[index + 2]:02x}{codes[index + 3]:02x}{codes[index + 4]:02x}"
                        )
                    )
                    index += 4
            index += 1

        return fmt


def _color(value: str):
    from PySide6.QtGui import QColor

    return QColor(value)


def _xterm256(index: int) -> str:
    if index < 16:
        table = [
            "#000000", "#800000", "#008000", "#808000", "#000080", "#800080",
            "#008080", "#c0c0c0", "#808080", "#ff0000", "#00ff00", "#ffff00",
            "#0000ff", "#ff00ff", "#00ffff", "#ffffff",
        ]
        return table[index]
    if index < 232:
        index -= 16
        r, g, b = index // 36, (index % 36) // 6, index % 6
        levels = [0, 95, 135, 175, 215, 255]
        return f"#{levels[r]:02x}{levels[g]:02x}{levels[b]:02x}"
    grey = 8 + (index - 232) * 10
    return f"#{grey:02x}{grey:02x}{grey:02x}"


class OutputPanel(QWidget):
    send_input = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("outputPanel")
        self._running = False
        self._status_kind = "ready"

        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 2)
        header.setSpacing(8)

        title = QLabel("OUTPUT")
        title.setObjectName("panelHeader")

        self.status = QLabel("READY")
        self.status.setObjectName("runStatus")

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("chip")
        self.clear_button.setToolTip("Clear the output")

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("chip")
        self.stop_button.setToolTip("Stop the running program (Shift+F5)")

        header.addWidget(title)
        header.addWidget(self.status)
        header.addStretch(1)
        header.addWidget(self.clear_button)
        header.addWidget(self.stop_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        self.console = OutputConsole()

        input_row = QHBoxLayout()
        input_row.setContentsMargins(14, 0, 14, 12)
        input_row.setSpacing(8)

        prompt = QLabel("›")
        prompt.setStyleSheet(
            f"color: {theme.ACCENT}; font-size: 16px; font-weight: 800;"
        )
        self._prompt = prompt

        self.input = QLineEdit()
        self.input.setPlaceholderText("Send input to the running program…")
        self.input.setClearButtonEnabled(True)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("chip")

        input_row.addWidget(prompt)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.progress)
        layout.addWidget(self.console, 1)
        layout.addLayout(input_row)

        self.clear_button.clicked.connect(self.console.clear)
        self.stop_button.clicked.connect(self.stop_requested)
        self.send_button.clicked.connect(self._emit_input)
        self.input.returnPressed.connect(self._emit_input)

        self.set_running(False)

    def _emit_input(self) -> None:
        text = self.input.text()
        if not text:
            return
        self.input.clear()
        self.feed(f"> {text}\n", "input")
        self.send_input.emit(text)

    def feed(self, text: str, kind: str = "stdout") -> None:
        self.console.feed(text, kind)

    def clear(self) -> None:
        self.console.clear()
        self.console._pending = ""

    def set_running(self, running: bool) -> None:
        self._running = running
        self.input.setEnabled(running)
        self.send_button.setEnabled(running)
        self.stop_button.setEnabled(running)
        self.progress.setVisible(running)
        if running:
            self.set_status("RUNNING", "running")
        else:
            self.set_status("READY", "ready")

    def set_status(self, text: str, kind: str = "ready") -> None:
        self._status_kind = kind
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {kind_color(kind)};")

    def refresh_theme(self) -> None:
        self.set_status(self.status.text(), self._status_kind)
        self._prompt.setStyleSheet(
            f"color: {theme.ACCENT}; font-size: 16px; font-weight: 800;"
        )

    def set_font_size(self, size: int) -> None:
        self.console.set_font_size(size)
