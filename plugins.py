"""Built-in plugin catalog and plugin manager page."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import icons, theme


@dataclass(frozen=True)
class PluginSpec:
    key: str
    name: str
    category: str
    description: str
    default: bool = False


PLUGINS: tuple[PluginSpec, ...] = (
    PluginSpec(
        "auto_save",
        "Auto Save",
        "WORKFLOW",
        "Save modified files automatically every 30 seconds.",
    ),
    PluginSpec(
        "word_wrap",
        "Word Wrap",
        "EDITOR",
        "Wrap long lines at the editor width instead of scrolling.",
    ),
    PluginSpec(
        "indent_guides",
        "Indent Guides",
        "EDITOR",
        "Draw subtle vertical guides for indentation levels.",
        default=True,
    ),
    PluginSpec(
        "current_line",
        "Current Line Highlight",
        "EDITOR",
        "Highlight the line containing the text cursor.",
        default=True,
    ),
    PluginSpec(
        "auto_close_brackets",
        "Auto Close Brackets",
        "EDITOR",
        "Insert matching closing brackets and quotes as you type.",
        default=True,
    ),
    PluginSpec(
        "trim_trailing_whitespace",
        "Trim Trailing Whitespace",
        "SAVING",
        "Remove trailing spaces from every line when saving.",
    ),
    PluginSpec(
        "final_newline",
        "Ensure Final Newline",
        "SAVING",
        "Add a newline at the end of saved files when missing.",
    ),
    PluginSpec(
        "word_count",
        "Word Count",
        "STATUS",
        "Show words and characters for the current file in the status bar.",
    ),
    PluginSpec(
        "status_clock",
        "Status Clock",
        "STATUS",
        "Show a live clock in the status bar.",
    ),
    PluginSpec(
        "zen_mode",
        "Zen Mode",
        "WORKFLOW",
        "Hide the explorer and terminal panels for a focused workspace.",
    ),
    PluginSpec(
        "git_integration",
        "Git & Version Control",
        "VERSION CONTROL",
        "Show the repository branch and changes in the status bar, with "
        "Git status, diff, log, stage, and commit actions in the menu bar.",
    ),
)

PLUGIN_BY_KEY = {plugin.key: plugin for plugin in PLUGINS}

CATEGORY_COLORS = {
    "EDITOR": "ACCENT",
    "WORKFLOW": "GREEN",
    "SAVING": "YELLOW",
    "STATUS": "CYAN",
    "VERSION CONTROL": "ORANGE",
}


def category_color(category: str) -> str:
    return getattr(theme, CATEGORY_COLORS.get(category, "ACCENT"), theme.ACCENT)


def default_plugin_states() -> dict[str, bool]:
    return {plugin.key: plugin.default for plugin in PLUGINS}


class PluginCard(QFrame):
    toggled = Signal(str, bool)

    def __init__(
        self,
        plugin: PluginSpec,
        enabled: bool,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.plugin = plugin
        self.setObjectName("pluginCard")

        icon_label = QLabel()
        icon_label.setObjectName("pluginIcon")
        icon_label.setFixedSize(38, 38)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label = icon_label

        name = QLabel(plugin.name)
        name.setObjectName("pluginName")

        category = QLabel(plugin.category)
        category.setObjectName("pluginCategory")

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(name)
        title_row.addWidget(category)
        title_row.addStretch(1)

        description = QLabel(plugin.description)
        description.setObjectName("pluginDescription")
        description.setWordWrap(True)

        text_column = QVBoxLayout()
        text_column.setSpacing(3)
        text_column.addLayout(title_row)
        text_column.addWidget(description)

        self.toggle = QCheckBox("Enabled")
        self.toggle.setObjectName("pluginToggle")
        self.toggle.setChecked(enabled)
        self.toggle.toggled.connect(
            lambda checked: self.toggled.emit(self.plugin.key, checked)
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)
        layout.addWidget(icon_label)
        layout.addLayout(text_column, 1)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        color = category_color(self.plugin.category)
        self._icon_label.setPixmap(
            icons.icon("plugins", color, 18).pixmap(18, 18)
        )

    def set_enabled(self, enabled: bool) -> None:
        self.toggle.blockSignals(True)
        self.toggle.setChecked(bool(enabled))
        self.toggle.blockSignals(False)


class PluginManagerPage(QWidget):
    """A tab page listing the built-in plugins and their toggles."""

    plugin_toggled = Signal(str, bool)

    def __init__(
        self,
        states: dict[str, bool] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("pluginsPage")
        self._states = default_plugin_states()
        if states:
            self._states.update(states)
        self._cards: dict[str, PluginCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        title = QLabel("Plugins")
        title.setObjectName("pluginsTitle")

        subtitle = QLabel(
            "Built-in extensions for editing, saving, and your workspace."
        )
        subtitle.setObjectName("pluginsSubtitle")
        subtitle.setWordWrap(True)

        self._count_label = QLabel()
        self._count_label.setObjectName("pluginsCount")

        title_column = QVBoxLayout()
        title_column.setSpacing(2)
        title_column.addWidget(title)
        title_column.addWidget(subtitle)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addLayout(title_column, 1)
        header.addWidget(self._count_label, 0, Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setObjectName("pluginsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("pluginsList")
        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(0, 6, 8, 6)
        card_layout.setSpacing(10)

        for plugin in PLUGINS:
            card = PluginCard(
                plugin,
                self._states.get(plugin.key, plugin.default),
                container,
            )
            card.toggled.connect(self._on_card_toggled)
            card_layout.addWidget(card)
            self._cards[plugin.key] = card

        card_layout.addStretch(1)
        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 18, 18)
        layout.setSpacing(16)
        layout.addLayout(header)
        layout.addWidget(scroll, 1)

        self._update_summary()

    def _on_card_toggled(self, key: str, enabled: bool) -> None:
        self._states[key] = bool(enabled)
        self._update_summary()
        self.plugin_toggled.emit(key, bool(enabled))

    def _update_summary(self) -> None:
        enabled = sum(
            1
            for plugin in PLUGINS
            if self._states.get(plugin.key, plugin.default)
        )
        self._count_label.setText(f"{enabled} of {len(PLUGINS)} enabled")

    def states(self) -> dict[str, bool]:
        return dict(self._states)

    def set_states(self, states: dict[str, bool]) -> None:
        self._states = default_plugin_states()
        self._states.update(states)
        for key, card in self._cards.items():
            card.set_enabled(self._states.get(key, False))
        self._update_summary()

    def refresh_theme(self) -> None:
        for card in self._cards.values():
            card.refresh_theme()
