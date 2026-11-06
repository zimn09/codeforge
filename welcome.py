"""Branded empty-state page with languages and recent files."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import __version__, icons, theme
from .languages import language_for_path, runnable_languages


def _pretty_path(path: Path) -> str:
    parent = path.parent
    if parent == Path.home():
        return "~"
    return parent.name or str(parent)


class WelcomePage(QWidget):
    new_file = Signal()
    open_file = Signal()
    open_folder = Signal()
    command_palette = Signal()
    recent_selected = Signal(str)
    language_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("welcomePage")

        scroll = QScrollArea()
        scroll.setObjectName("welcomeScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)

        content = QWidget()
        content.setObjectName("welcomePage")
        outer = QVBoxLayout(content)
        outer.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setContentsMargins(30, 16, 30, 16)
        row.addStretch(1)

        column = QWidget()
        column.setMaximumWidth(880)
        column.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(10)

        column_layout.addWidget(self._build_hero())
        column_layout.addWidget(self._build_languages())
        column_layout.addWidget(self._build_recent())
        column_layout.addStretch(1)

        row.addWidget(column, 10)
        row.addStretch(1)
        outer.addLayout(row)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------
    def _build_hero(self) -> QFrame:
        card = QFrame()
        card.setObjectName("welcomeCard")

        badge = QLabel("</>")
        badge.setObjectName("welcomeBadge")
        badge.setTextFormat(Qt.TextFormat.PlainText)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(54, 54)

        title = QLabel("CodeForge")
        title.setObjectName("welcomeTitle")

        subtitle = QLabel(
            "A focused, multi-language workspace for writing and running code."
        )
        subtitle.setObjectName("welcomeSubtitle")

        heading = QVBoxLayout()
        heading.setSpacing(2)
        heading.addWidget(title)
        heading.addWidget(subtitle)

        top = QHBoxLayout()
        top.setSpacing(18)
        top.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        top.addLayout(heading, 1)

        version = QLabel(f"v{__version__}")
        version.setObjectName("versionBadge")
        top.addWidget(version, 0, Qt.AlignmentFlag.AlignTop)

        new_button = QPushButton("New File")
        new_button.setObjectName("primary")
        new_button.clicked.connect(self.new_file)

        open_button = QPushButton("Open File")
        open_button.clicked.connect(self.open_file)

        folder_button = QPushButton("Open Folder")
        folder_button.clicked.connect(self.open_folder)

        palette_button = QPushButton("Command Palette")
        palette_button.setObjectName("chip")
        palette_button.clicked.connect(self.command_palette)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(new_button)
        buttons.addWidget(open_button)
        buttons.addWidget(folder_button)
        buttons.addSpacing(6)
        buttons.addWidget(palette_button)
        buttons.addStretch(1)

        hint = QLabel(
            "F5 Run   ·   Shift+F5 Build   ·   Ctrl+S Save   ·   "
            "Ctrl+F Find   ·   Ctrl+K Commands"
        )
        hint.setObjectName("hint")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 20, 28, 16)
        layout.setSpacing(11)
        layout.addLayout(top)
        layout.addLayout(buttons)
        layout.addWidget(hint)
        return card

    def _build_languages(self) -> QFrame:
        card = QFrame()
        card.setObjectName("welcomeCard")

        title = QLabel("RUNS OUT OF THE BOX")
        title.setObjectName("sectionLabel")

        note = QLabel("plus HTML, CSS, JSON, SQL, YAML, TOML and more")
        note.setObjectName("hint")

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(note)

        grid = QGridLayout()
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)
        for index, language in enumerate(runnable_languages()):
            chip = QPushButton(language.name)
            chip.setObjectName("langChip")
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setIcon(icons.dot_icon(language.color, 7))
            chip.setIconSize(QSize(7, 7))
            chip.setToolTip(f"New {language.name} file")
            chip.clicked.connect(
                lambda _checked=False, key=language.key: self.language_selected.emit(key)
            )
            grid.addWidget(chip, index // 5, index % 5)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(9)
        layout.addLayout(header)
        layout.addLayout(grid)
        return card

    def _build_recent(self) -> QFrame:
        self.recent_card = QFrame()
        self.recent_card.setObjectName("welcomeCard")
        self.recent_card.setVisible(False)

        title = QLabel("RECENT FILES")
        title.setObjectName("sectionLabel")

        self.recent_list = QListWidget()
        self.recent_list.setObjectName("recentList")
        self.recent_list.setIconSize(QSize(16, 16))
        self.recent_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.recent_list.itemClicked.connect(self._recent_clicked)
        self.recent_list.itemActivated.connect(self._recent_clicked)

        self.empty_label = QLabel("No recent files yet — open one to get started.")
        self.empty_label.setObjectName("hint")

        layout = QVBoxLayout(self.recent_card)
        layout.setContentsMargins(22, 12, 22, 12)
        layout.setSpacing(6)
        layout.addWidget(title)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.recent_list)
        return self.recent_card

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def set_recent(self, paths: list[str] | list[Path]) -> None:
        self.recent_list.clear()
        entries = [Path(path) for path in paths][:3]
        self._recent_paths = entries

        for path in entries:
            language = language_for_path(path)
            if language.key == "text":
                file_icon = icons.icon("file", theme.FG_MUTED, 16)
            else:
                file_icon = icons.file_badge(language.color, 16)

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setIcon(file_icon)
            item.setToolTip(str(path))

            widget = QWidget()
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row = QHBoxLayout(widget)
            row.setContentsMargins(8, 2, 8, 2)
            row.setSpacing(10)

            name = QLabel(path.name)
            name.setObjectName("recentName")
            location = QLabel(_pretty_path(path))
            location.setObjectName("recentPath")
            location.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            location.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            location.setToolTip(str(path))

            row.addWidget(name)
            row.addWidget(location, 1)

            item.setSizeHint(QSize(0, 32))
            self.recent_list.addItem(item)
            self.recent_list.setItemWidget(item, widget)

        has_entries = bool(entries)
        self.recent_card.setVisible(has_entries)
        self.empty_label.setVisible(False)
        self.recent_list.setVisible(has_entries)
        if has_entries:
            self.recent_list.setFixedHeight(len(entries) * 34 + 2)

    def refresh_theme(self) -> None:
        if getattr(self, "_recent_paths", None):
            self.set_recent(self._recent_paths)

    def _recent_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_selected.emit(path)
