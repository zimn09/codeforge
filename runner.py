"""Build and run programs for every runnable language in the registry."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

from .languages import Language, language_for_key

C_FLAGS = (
    "-std=c17",
    "-Wall",
    "-Wextra",
    "-g",
    "-O0",
    "-fdiagnostics-color=always",
)
CPP_FLAGS = (
    "-std=c++20",
    "-Wall",
    "-Wextra",
    "-g",
    "-O0",
    "-fdiagnostics-color=always",
)

JAVA_PUBLIC_CLASS = re.compile(
    r"\bpublic\s+(?:final\s+|abstract\s+|sealed\s+|non-sealed\s+)?"
    r"(?:class|interface|enum|record)\s+(\w+)"
)
JAVA_ANY_CLASS = re.compile(r"\b(?:class|interface|enum|record)\s+(\w+)")
JAVA_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)


@dataclass
class Command:
    program: str
    args: list[str] = field(default_factory=list)
    stage: str = "run"  # compile | run
    native: bool = False
    env: dict[str, str] = field(default_factory=dict)


def _which(candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return None


def _missing(language: Language) -> str:
    tools = ", ".join(language.tools) or "the required tool"
    return (
        f"Could not find {tools} to run {language.name}.\n"
        "Install the toolchain and try again."
    )


class Runner(QObject):
    """Runs one job at a time, possibly with a compile step first."""

    output = Signal(str, str)       # text, kind
    finished = Signal(int, str)     # exit code, message
    state_changed = Signal(bool)    # running?

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._process: QProcess | None = None
        self._commands: list[Command] = []
        self._stage = ""
        self._source: Path | None = None
        self._compile_only = False
        self._stopping = False
        self._started_at = 0.0
        self.last_elapsed = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_running(self) -> bool:
        return self._process is not None

    def run(
        self,
        language: Language | str,
        source: Path,
        compile_only: bool = False,
    ) -> bool:
        if self.is_running():
            self.output.emit("A program is already running — stop it first.\n", "error")
            return False

        if isinstance(language, str):
            language = language_for_key(language)

        source = Path(source).expanduser().resolve()
        if not source.is_file():
            self.output.emit(f"File not found: {source}\n", "error")
            self.finished.emit(1, "File not found")
            return False

        commands, error = self._build_plan(language, source, compile_only)
        if error:
            self.output.emit(error + "\n", "error")
            self.finished.emit(1, error.splitlines()[0])
            return False

        self._source = source
        self._commands = commands
        self._compile_only = compile_only
        self._stopping = False
        self._started_at = time.monotonic()
        self.last_elapsed = 0.0
        self.state_changed.emit(True)
        self._start_next()
        return True

    def send_input(self, text: str) -> None:
        if (
            self._process is not None
            and self._stage == "run"
            and self._process.state() == QProcess.ProcessState.Running
        ):
            self._process.write(text.encode("utf-8"))

    def stop(self) -> None:
        process = self._process
        if process is None:
            return
        self._stopping = True
        self._commands.clear()
        self.output.emit("\n[stopping…]\n", "system")
        process.terminate()
        QTimer.singleShot(1500, lambda p=process: self._force_kill(p))

    # ------------------------------------------------------------------
    # Plan building
    # ------------------------------------------------------------------
    def _build_plan(
        self,
        language: Language,
        source: Path,
        compile_only: bool,
    ) -> tuple[list[Command], str | None]:
        if language.runner is None:
            return [], f"{language.name} files cannot be run by CodeForge."

        build_dir = source.parent / "build"
        try:
            build_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return [], f"Cannot create build directory: {exc}"

        binary = build_dir / source.stem
        if os.name == "nt":
            binary = binary.with_suffix(".exe")

        kind = language.runner
        commands: list[Command] = []

        if kind == "python":
            commands = [
                Command(
                    sys.executable,
                    ["-u", str(source)],
                    "run",
                    env={"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
                )
            ]

        elif kind in ("c", "cpp"):
            compiler = _which(
                ("gcc", "cc", "clang")
                if kind == "c"
                else ("g++", "clang++", "c++")
            )
            if compiler is None:
                return [], _missing(language)
            flags = C_FLAGS if kind == "c" else CPP_FLAGS
            commands = [
                Command(
                    compiler,
                    [*flags, "-o", str(binary), str(source), "-lm"],
                    "compile",
                ),
                Command(str(binary), [], "run", native=True),
            ]

        elif kind == "rust":
            compiler = _which(("rustc",))
            if compiler is None:
                return [], _missing(language)
            commands = [
                Command(
                    compiler,
                    ["--edition", "2021", "-O", "-o", str(binary), str(source)],
                    "compile",
                ),
                Command(str(binary), [], "run", native=True),
            ]

        elif kind == "go":
            compiler = _which(("go",))
            if compiler is None:
                return [], _missing(language)
            commands = [
                Command(compiler, ["build", "-o", str(binary), str(source)], "compile"),
                Command(str(binary), [], "run", native=True),
            ]

        elif kind == "java":
            compiler = _which(("javac",))
            runtime = _which(("java",))
            if compiler is None or runtime is None:
                return [], _missing(language)
            class_name, package = self._java_names(source)
            classes_dir = build_dir / "classes"
            try:
                classes_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return [], f"Cannot create build directory: {exc}"
            qualified = f"{package}.{class_name}" if package else class_name
            commands = [
                Command(
                    compiler,
                    ["-g", "-d", str(classes_dir), str(source)],
                    "compile",
                ),
                Command(
                    runtime,
                    ["-cp", str(classes_dir), qualified],
                    "run",
                ),
            ]

        elif kind in ("node", "bash", "perl", "lua", "ruby", "php"):
            tool = _which(language.tools)
            if tool is None:
                return [], _missing(language)
            commands = [Command(tool, [str(source)], "run")]

        else:
            return [], f"Unsupported runner: {kind}"

        if compile_only:
            commands = [command for command in commands if command.stage == "compile"]
            if not commands:
                return [], (
                    f"{language.name} is interpreted — there is nothing to build.\n"
                    "Press Run instead."
                )

        return commands, None

    def _java_names(self, source: Path) -> tuple[str, str]:
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return source.stem, ""
        package_match = JAVA_PACKAGE.search(text)
        package = package_match.group(1) if package_match else ""
        public_match = JAVA_PUBLIC_CLASS.search(text)
        any_match = JAVA_ANY_CLASS.search(text)
        class_name = (
            public_match.group(1)
            if public_match
            else (any_match.group(1) if any_match else source.stem)
        )
        return class_name, package

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _start_next(self) -> None:
        if not self._commands:
            elapsed = time.monotonic() - self._started_at
            if self._compile_only:
                self._finish(0, "Build finished", elapsed)
            else:
                self._finish(0, "Process finished", elapsed)
            return

        command = self._commands.pop(0)
        self._stage = command.stage
        self._start_process(command)

    def _start_process(self, command: Command) -> None:
        assert self._source is not None

        process = QProcess(self)
        process.setWorkingDirectory(str(self._source.parent))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        env = QProcessEnvironment.systemEnvironment()
        for key, value in command.env.items():
            env.insert(key, value)
        process.setProcessEnvironment(env)

        process.readyReadStandardOutput.connect(lambda p=process: self._read_stdout(p))
        process.readyReadStandardError.connect(lambda p=process: self._read_stderr(p))
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(lambda error, p=process: self._on_error(error, p))

        program, args = command.program, list(command.args)
        self.output.emit(f"$ {shlex.join([program, *args])}\n", "cmd")

        if command.native and shutil.which("stdbuf"):
            program = shutil.which("stdbuf") or program
            args = ["-o0", "-e0", command.program, *command.args]

        self._process = process
        process.start(program, args)

    # ------------------------------------------------------------------
    # QProcess callbacks
    # ------------------------------------------------------------------
    def _read_stdout(self, process: QProcess) -> None:
        data = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        if data:
            kind = "build" if self._stage == "compile" else "stdout"
            self.output.emit(data, kind)

    def _read_stderr(self, process: QProcess) -> None:
        data = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        if data:
            self.output.emit(data, "stderr")

    def _on_finished(self, code: int, _status: QProcess.ExitStatus) -> None:
        process = self._process
        if process is not None:
            self._read_stdout(process)
            self._read_stderr(process)
            process.deleteLater()
            self._process = None

        if self._stopping:
            self._stopping = False
            self._commands.clear()
            elapsed = time.monotonic() - self._started_at if self._started_at else 0.0
            self._finish(130, "Stopped", elapsed)
            return

        stage = self._stage
        if code != 0:
            message = (
                "Build failed" if stage == "compile" else f"Process exited with code {code}"
            )
            self._commands.clear()
            self._finish(code, message, self._elapsed())
            return

        if stage == "compile":
            self.output.emit("  ✓ compiled\n", "success")

        if self._commands:
            self._start_next()
            return

        elapsed = time.monotonic() - self._started_at
        if self._compile_only:
            self._finish(0, "Build finished", elapsed)
        else:
            self._finish(0, "Process finished", elapsed)

    def _on_error(self, error: QProcess.ProcessError, process: QProcess) -> None:
        if error != QProcess.ProcessError.FailedToStart:
            return
        message = process.errorString()
        self.output.emit(f"Failed to start process: {message}\n", "error")
        process.deleteLater()
        self._process = None
        self._commands.clear()
        elapsed = time.monotonic() - self._started_at if self._started_at else 0.0
        self._finish(127, "Failed to start process", elapsed)

    def _force_kill(self, process: QProcess) -> None:
        if process.state() != QProcess.ProcessState.NotRunning:
            process.kill()

    def _elapsed(self) -> float:
        return time.monotonic() - self._started_at if self._started_at else 0.0

    def _finish(self, code: int, message: str, elapsed: float) -> None:
        self.last_elapsed = max(0.0, elapsed)
        self._stage = ""
        self._source = None
        self._commands.clear()
        self.state_changed.emit(False)
        self.finished.emit(code, message)
