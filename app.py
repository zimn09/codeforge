"""Application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from . import APP_NAME, icons
from . import theme
from .main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    app = QApplication([argv[0]] if argv else [APP_NAME])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("CodeForge")
    app.setStyle("Fusion")
    app.setFont(theme.ui_font(10))

    settings = QSettings("CodeForge", "CodeForge")
    theme.activate(str(settings.value("theme", "midnight")))
    app.setStyleSheet(theme.build_qss())
    app.setWindowIcon(icons.icon("spark", theme.ACCENT, 64))

    start_path: Path | None = None
    for argument in argv[1:]:
        if argument.startswith("-"):
            continue
        candidate = Path(argument).expanduser()
        if candidate.exists():
            start_path = candidate
            break

    window = MainWindow(start_path)
    window.show()
    return app.exec()
