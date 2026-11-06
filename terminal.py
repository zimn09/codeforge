"""A compact, line-based shell terminal for the bottom panel."""

from __future__ import annotations

import codecs
import os
import re
import shlex
import shutil
import uuid
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .console import OutputConsole, kind_color

DONE_RE = re.compile(
    r"__CODEFORGE_DONE_([0-9a-f]+)__(\d+)\|([^\r\n]*)\r?\n"
)
PARTIAL_MARKER = "__CODEFORGE_DONE_"


class CommandLineEdit(QLineEdit):
    """Command input with familiar up/down history and Ctrl+L."""

    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._history: list[str] = []
        self._history_index = 0
        self._draft = ""

    def remember(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        if not self._history or self._history[-1] != command:
            self._history.append(command)
        self._history_index = len(self._history)
        self._draft = ""

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.key() == Qt.Key.Key_Up:
            if self._history:
                if self._history_index == len(self._history):
                    self._draft = self.text()
                if self._history_index > 0:
                    self._history_index -= 1
                    self.setText(self._history[self._history_index])
                    self.setCursorPosition(len(self.text()))
            event.accept()
            return
        if event.key() == Qt.Key.Key_Down:
            if self._history and self._history_index < len(self._history):
                self._history_index += 1
                if self._history_index == len(self._history):
                    self.setText(self._draft)
                else:
                    self.setText(self._history[self._history_index])
                self.setCursorPosition(len(self.text()))
            event.accept()
            return
        if (
            event.key() == Qt.Key.Key_L
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.clear_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class TerminalPanel(QWidget):
    """Persistent shell process with a command line and ANSI output view."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self._cwd: Path | None = None
        self._pending_output = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._status_kind = "ready"
        self._status_text = "READY"
        self._shell_program, self._shell_args = self._detect_shell()

        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 2)
        header.setSpacing(8)

        title = QLabel("TERMINAL")
        title.setObjectName("panelHeader")

        self.cwd_label = QLabel("no folder")
        self.cwd_label.setObjectName("terminalCwd")

        self.status = QLabel("READY")
        self.status.setObjectName("runStatus")

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("chip")
        self.clear_button.setToolTip("Clear the terminal")

        self.restart_button = QPushButton("Restart")
        self.restart_button.setObjectName("chip")
        self.restart_button.setToolTip("Restart the shell")

        header.addWidget(title)
        header.addWidget(self.cwd_label)
        header.addWidget(self.status)
        header.addStretch(1)
        header.addWidget(self.clear_button)
        header.addWidget(self.restart_button)

        self.console = OutputConsole()
        self.console.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.console.setPlaceholderText("Type a command below and press Enter…")

        input_row = QHBoxLayout()
        input_row.setContentsMargins(14, 0, 14, 12)
        input_row.setSpacing(8)

        self._prompt = QLabel("❯")
        self._prompt.setStyleSheet(
            f"color: {theme.ACCENT}; font-size: 16px; font-weight: 800;"
        )

        self.input = CommandLineEdit()
        self.input.setFont(theme.monospace_font(11))
        self.input.setPlaceholderText("Type a command and press Enter…")
        self.input.setClearButtonEnabled(True)

        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("chip")
        self.run_button.setToolTip("Run the command")

        input_row.addWidget(self._prompt)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.run_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.console, 1)
        layout.addLayout(input_row)

        self._process = QProcess(self)
        self._process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        self.clear_button.clicked.connect(self.clear_console)
        self.restart_button.clicked.connect(self.restart)
        self.run_button.clicked.connect(self.execute)
        self.input.returnPressed.connect(self.execute)
        self.input.clear_requested.connect(self.clear_console)

        self.set_status("READY", "ready")
        self.input.setEnabled(False)
        self.run_button.setEnabled(False)

    # ------------------------------------------------------------------
    # Shell lifecycle
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_shell() -> tuple[str, list[str]]:
        if os.name == "nt":
            return os.environ.get("COMSPEC", "cmd.exe"), []
        bash = shutil.which("bash")
        if bash:
            return bash, ["--noprofile", "--norc"]
        shell = shutil.which("sh") or os.environ.get("SHELL") or "/bin/sh"
        return shell, []

    @staticmethod
    def _quote(path: Path) -> str:
        if os.name == "nt":
            escaped = str(path).replace('"', '\\"')
            return f'"{escaped}"'
        return shlex.quote(str(path))

    @property
    def running(self) -> bool:
        return (
            self._process.state() != QProcess.ProcessState.NotRunning
        )

    def _start_shell(self) -> None:
        self.stop()
        self.clear_console()
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._pending_output = ""

        cwd = self._cwd or Path.home()
        self._process.setWorkingDirectory(str(cwd))
        env = QProcessEnvironment.systemEnvironment()
        env.insert("TERM", "xterm-256color")
        if not env.contains("PAGER"):
            env.insert("PAGER", "cat")
        if not env.contains("GIT_PAGER"):
            env.insert("GIT_PAGER", "cat")
        self._process.setProcessEnvironment(env)
        self._process.start(self._shell_program, self._shell_args)
        self.set_status("STARTING", "success")

    def ensure_started(self) -> bool:
        if self.running:
            return True
        self._start_shell()
        return self._process.waitForStarted(1500)

    def restart(self) -> None:
        self._start_shell()
        self._process.waitForStarted(1500)
        self.focus_input()

    def stop(self) -> None:
        if self._process.state() == QProcess.ProcessState.NotRunning:
            return
        self._process.terminate()
        if not self._process.waitForFinished(900):
            self._process.kill()
            self._process.waitForFinished(500)

    def set_working_directory(self, path: Path) -> None:
        try:
            path = Path(path).expanduser().resolve()
        except OSError:
            path = Path(path).expanduser()
        self._cwd = path
        self._update_cwd_label()
        if self.running:
            token = uuid.uuid4().hex[:12]
            script = (
                f"cd -- {self._quote(path)}\n"
                f"printf '__CODEFORGE_DONE_{token}__%s|%s\\n' \"$?\" \"$PWD\"\n"
            )
            self._process.write(script.encode("utf-8"))

    def _update_cwd_label(self) -> None:
        if self._cwd is None:
            self.cwd_label.setText("no folder")
            self.cwd_label.setToolTip("")
            return
        name = self._cwd.name or str(self._cwd)
        self.cwd_label.setText(name)
        self.cwd_label.setToolTip(str(self._cwd))

    # ------------------------------------------------------------------
    # Command execution / output
    # ------------------------------------------------------------------
    def execute(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.input.remember(command)
        self.input.clear()

        if command in {"clear", "cls"}:
            self.clear_console()
            return

        if not self.ensure_started():
            self.console.feed("Could not start the shell.\n", "error")
            self.set_status("ERROR", "error")
            return

        self.console.feed(f"❯ {command}\n", "cmd")
        self.set_status("RUNNING", "success")
        token = uuid.uuid4().hex[:12]
        script = (
            f"{command}\n"
            f"printf '__CODEFORGE_DONE_{token}__%s|%s\\n' \"$?\" \"$PWD\"\n"
        )
        self._process.write(script.encode("utf-8"))

    def _read_output(self) -> None:
        chunk = bytes(self._process.readAllStandardOutput())
        if not chunk:
            return
        text = self._decoder.decode(chunk)
        text = text.replace("\r\n", "\n").replace("\r", "")
        self._consume(text)

    def _consume(self, text: str) -> None:
        if not text:
            return
        data = self._pending_output + text
        while True:
            match = DONE_RE.search(data)
            if match is None:
                break
            prefix = data[: match.start()]
            if prefix:
                self._feed_output(prefix)
            self._on_command_done(match.group(2), match.group(3))
            data = data[match.end() :]

        partial = data.rfind(PARTIAL_MARKER)
        if partial >= 0:
            if partial:
                self._feed_output(data[:partial])
            self._pending_output = data[partial:]
            return
        self._pending_output = ""
        if data:
            self._feed_output(data)

    def _feed_output(self, text: str) -> None:
        if not text:
            return
        if not text.endswith("\n"):
            text += "\n"
        self.console.feed(text, "stdout")

    def _on_command_done(self, code: str, cwd: str) -> None:
        if cwd:
            try:
                path = Path(cwd)
                if path.is_dir():
                    self._cwd = path
                    self._update_cwd_label()
            except OSError:
                pass
        if code == "0":
            self.set_status("READY", "ready")
        else:
            self.set_status(f"EXIT {code}", "error")

    # ------------------------------------------------------------------
    # Qt process callbacks
    # ------------------------------------------------------------------
    def _on_started(self) -> None:
        self.input.setEnabled(True)
        self.run_button.setEnabled(True)
        self.set_status("READY", "ready")
        location = self._cwd or Path.home()
        self.console.feed(f"── Terminal · {location} ──\n", "system")
        self._update_cwd_label()

    def _on_finished(self, code: int, _status) -> None:
        self._read_output()
        if code == 0:
            self.console.feed("\n[Shell exited]\n", "system")
        else:
            self.console.feed(f"\n[Shell exited with code {code}]\n", "error")
        self.set_status("CLOSED", "error")
        self.input.setEnabled(False)
        self.run_button.setEnabled(False)

    def _on_error(self, _error) -> None:
        message = self._process.errorString()
        self.console.feed(f"Failed to start shell: {message}\n", "error")
        self.set_status("ERROR", "error")
        self.input.setEnabled(False)
        self.run_button.setEnabled(False)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().showEvent(event)
        self.ensure_started()

    def focus_input(self) -> None:
        self.ensure_started()
        self.input.setFocus()

    def clear_console(self) -> None:
        self.console.clear()
        self.console._pending = ""
        self._pending_output = ""

    def set_status(self, text: str, kind: str = "ready") -> None:
        self._status_text = text
        self._status_kind = kind
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {kind_color(kind)};")

    def refresh_theme(self) -> None:
        self.set_status(self._status_text, self._status_kind)
        self._prompt.setStyleSheet(
            f"color: {theme.ACCENT}; font-size: 16px; font-weight: 800;"
        )

    def set_font_size(self, size: int) -> None:
        self.console.set_font_size(size)
        self.input.setFont(theme.monospace_font(size))
