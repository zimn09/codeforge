"""Themes, palette tokens and the application stylesheet."""

from __future__ import annotations

from string import Template

from PySide6.QtGui import QFont, QFontDatabase

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

MIDNIGHT = {
    "bg": "#0e0e18",
    "bg_alt": "#161627",
    "bg_panel": "#131322",
    "bg_editor": "#111120",
    "bg_output": "#0c0c16",
    "bg_gutter": "#0d0d17",
    "border": "#26263e",
    "border_soft": "#1d1d31",
    "hover": "#1f1f34",
    "scroll": "#2f2f4a",
    "scroll_hover": "#3d3d60",
    "fg": "#e9e7f5",
    "fg_muted": "#9492b3",
    "fg_dim": "#605e7e",
    "accent": "#a78bfa",
    "accent_strong": "#7c5cff",
    "accent_soft": "#241f3d",
    "gradient_from": "#7c5cff",
    "gradient_to": "#c084fc",
    "pink": "#ff8ac2",
    "green": "#7bd88f",
    "red": "#ff7a7a",
    "yellow": "#ffd479",
    "cyan": "#63e6e2",
    "orange": "#ffb86b",
    "current_line": "#1a1a2e",
    "selection": "#3b3363",
    "search_match": "#4a3f7a",
    "search_current": "#6f5bd6",
    "gutter_fg": "#4b4a68",
    "gutter_fg_current": "#b6b3d6",
    "indent_guide": "#1f1f35",
    "syn_keyword": "#c8a6ff",
    "syn_builtin": "#63e6e2",
    "syn_constant": "#ffb86b",
    "syn_string": "#a6e3a1",
    "syn_comment": "#6c6a8a",
    "syn_number": "#ffb86b",
    "syn_decorator": "#ffd479",
    "syn_function": "#8fd3ff",
    "syn_type": "#ffc98b",
    "syn_preproc": "#ff8ac2",
    "syn_variable": "#f0a6ff",
    "syn_key": "#ff9ecb",
    "syn_tag": "#ff8a65",
    "syn_attribute": "#ffd479",
    "syn_heading": "#c8a6ff",
    "syn_link": "#6cb6ff",
}

AURORA = {
    "bg": "#091114",
    "bg_alt": "#101c1f",
    "bg_panel": "#0e191c",
    "bg_editor": "#0c171a",
    "bg_output": "#081012",
    "bg_gutter": "#091114",
    "border": "#1e3338",
    "border_soft": "#172a2e",
    "hover": "#14292c",
    "scroll": "#1f3a3d",
    "scroll_hover": "#2b5054",
    "fg": "#e4f2f0",
    "fg_muted": "#8aa9a8",
    "fg_dim": "#567171",
    "accent": "#5eead4",
    "accent_strong": "#14b8a6",
    "accent_soft": "#12312f",
    "gradient_from": "#14b8a6",
    "gradient_to": "#67e8f9",
    "pink": "#fda4af",
    "green": "#6ee7b7",
    "red": "#fb7185",
    "yellow": "#fde68a",
    "cyan": "#67e8f9",
    "orange": "#fdba74",
    "current_line": "#112428",
    "selection": "#164e4a",
    "search_match": "#1d5c57",
    "search_current": "#2dd4bf",
    "gutter_fg": "#3e5c5c",
    "gutter_fg_current": "#a7d8d3",
    "indent_guide": "#143034",
    "syn_keyword": "#7dd3fc",
    "syn_builtin": "#5eead4",
    "syn_constant": "#fcd34d",
    "syn_string": "#86efac",
    "syn_comment": "#5b7a78",
    "syn_number": "#fdba74",
    "syn_decorator": "#fde68a",
    "syn_function": "#67e8f9",
    "syn_type": "#fcd34d",
    "syn_preproc": "#fda4af",
    "syn_variable": "#a7f3d0",
    "syn_key": "#5eead4",
    "syn_tag": "#fda4af",
    "syn_attribute": "#fde68a",
    "syn_heading": "#7dd3fc",
    "syn_link": "#38bdf8",
}

EMBER = {
    "bg": "#12100f",
    "bg_alt": "#1c1917",
    "bg_panel": "#171412",
    "bg_editor": "#141110",
    "bg_output": "#0e0c0b",
    "bg_gutter": "#100e0d",
    "border": "#332b26",
    "border_soft": "#27211d",
    "hover": "#261f1a",
    "scroll": "#3a3029",
    "scroll_hover": "#4a3d33",
    "fg": "#f5ede6",
    "fg_muted": "#b3a094",
    "fg_dim": "#75655b",
    "accent": "#fbbf24",
    "accent_strong": "#f59e0b",
    "accent_soft": "#332713",
    "gradient_from": "#f59e0b",
    "gradient_to": "#fb7185",
    "pink": "#fb7185",
    "green": "#a3e635",
    "red": "#f87171",
    "yellow": "#fbbf24",
    "cyan": "#67e8f9",
    "orange": "#fb923c",
    "current_line": "#221c17",
    "selection": "#45301a",
    "search_match": "#5a3f18",
    "search_current": "#b45309",
    "gutter_fg": "#5a4b40",
    "gutter_fg_current": "#c7b3a3",
    "indent_guide": "#2a221c",
    "syn_keyword": "#fdba74",
    "syn_builtin": "#67e8f9",
    "syn_constant": "#fbbf24",
    "syn_string": "#a3e635",
    "syn_comment": "#7a6a5e",
    "syn_number": "#fb923c",
    "syn_decorator": "#fde68a",
    "syn_function": "#fca5a5",
    "syn_type": "#fcd34d",
    "syn_preproc": "#fb7185",
    "syn_variable": "#f9a8d4",
    "syn_key": "#fbbf24",
    "syn_tag": "#fb7185",
    "syn_attribute": "#fde68a",
    "syn_heading": "#fdba74",
    "syn_link": "#60a5fa",
}

PORCELAIN = {
    "bg": "#f3f3f8",
    "bg_alt": "#ffffff",
    "bg_panel": "#f8f8fc",
    "bg_editor": "#ffffff",
    "bg_output": "#f7f7fb",
    "bg_gutter": "#f0f0f7",
    "border": "#dedeea",
    "border_soft": "#e9e9f2",
    "hover": "#eeeef7",
    "scroll": "#d7d7e4",
    "scroll_hover": "#c3c3d6",
    "fg": "#23233a",
    "fg_muted": "#6b6b86",
    "fg_dim": "#9b9bb2",
    "accent": "#6d4aff",
    "accent_strong": "#5b36f0",
    "accent_soft": "#ece8ff",
    "gradient_from": "#6d4aff",
    "gradient_to": "#a855f7",
    "pink": "#db2777",
    "green": "#15803d",
    "red": "#dc2626",
    "yellow": "#b45309",
    "cyan": "#0e7490",
    "orange": "#c2410c",
    "current_line": "#f4f2ff",
    "selection": "#ddd5ff",
    "search_match": "#ffe9a8",
    "search_current": "#fbbf24",
    "gutter_fg": "#b0b0c4",
    "gutter_fg_current": "#5b36f0",
    "indent_guide": "#ececf5",
    "syn_keyword": "#7c3aed",
    "syn_builtin": "#0e7490",
    "syn_constant": "#b45309",
    "syn_string": "#15803d",
    "syn_comment": "#8b8ba7",
    "syn_number": "#c2410c",
    "syn_decorator": "#a16207",
    "syn_function": "#1d4ed8",
    "syn_type": "#a16207",
    "syn_preproc": "#be185d",
    "syn_variable": "#be185d",
    "syn_key": "#b91c1c",
    "syn_tag": "#c2410c",
    "syn_attribute": "#a16207",
    "syn_heading": "#6d28d9",
    "syn_link": "#1d4ed8",
}

THEMES = {
    "midnight": ("Midnight", MIDNIGHT),
    "aurora": ("Aurora", AURORA),
    "ember": ("Ember", EMBER),
    "porcelain": ("Porcelain", PORCELAIN),
}
THEME_ORDER = ("midnight", "aurora", "ember", "porcelain")

CURRENT_THEME = "midnight"


def activate(name: str) -> str:
    """Load a palette into the module namespace and return its key."""
    global CURRENT_THEME
    if name not in THEMES:
        name = "midnight"
    CURRENT_THEME = name
    for token, value in THEMES[name][1].items():
        globals()[token.upper()] = value
    return name


def theme_label(name: str) -> str:
    return THEMES.get(name, THEMES["midnight"])[0]


def is_light(name: str | None = None) -> bool:
    return (name or CURRENT_THEME) == "porcelain"


def next_theme(name: str | None = None) -> str:
    current = name or CURRENT_THEME
    index = THEME_ORDER.index(current)
    return THEME_ORDER[(index + 1) % len(THEME_ORDER)]


# Populate tokens for the default theme.
activate(CURRENT_THEME)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

MONO_FONTS = (
    "JetBrains Mono",
    "Fira Code",
    "Cascadia Code",
    "Consolas",
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Courier New",
)

UI_FONTS = (
    "Inter",
    "Noto Sans",
    "Segoe UI",
    "Helvetica Neue",
    "DejaVu Sans",
)

_MONO_FAMILY: str | None = None
_UI_FAMILY: str | None = None


def _pick(families: tuple[str, ...], cache_value: str | None) -> str:
    if cache_value is not None:
        return cache_value
    available = set(QFontDatabase.families())
    return next((name for name in families if name in available), "")


def monospace_font(size: int = 12) -> QFont:
    global _MONO_FAMILY
    _MONO_FAMILY = _pick(MONO_FONTS, _MONO_FAMILY)
    font = QFont(_MONO_FAMILY or "monospace")
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    font.setPointSize(size)
    return font


def ui_font(size: int = 10) -> QFont:
    global _UI_FAMILY
    _UI_FAMILY = _pick(UI_FONTS, _UI_FAMILY)
    font = QFont(_UI_FAMILY or "sans-serif")
    font.setPointSize(size)
    return font


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

_QSS = Template(
    """
QMainWindow, QDialog {
    background: $bg;
}

QWidget {
    color: $fg;
}

QLabel, QCheckBox {
    background: transparent;
}

QMenuBar {
    background: $bg_panel;
    border-bottom: 1px solid $border_soft;
    padding: 3px 8px;
}

QMenuBar::item {
    background: transparent;
    color: $fg_muted;
    padding: 5px 10px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background: $hover;
    color: $fg;
}

QMenu {
    background: $bg_alt;
    border: 1px solid $border;
    padding: 6px;
}

QMenu::item {
    padding: 6px 30px 6px 24px;
    border-radius: 6px;
    color: $fg_muted;
}

QMenu::item:selected {
    background: $accent_soft;
    color: $fg;
}

QMenu::item:disabled {
    color: $fg_dim;
}

QMenu::separator {
    height: 1px;
    background: $border_soft;
    margin: 5px 12px;
}

QWidget#commandBar {
    background: $bg_panel;
    border-bottom: 1px solid $border_soft;
}

QLabel#logoBadge {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 $gradient_from, stop:1 $gradient_to);
    color: #ffffff;
    border-radius: 9px;
    font-size: 14px;
    font-weight: 800;
}

QLabel#appName {
    color: $fg;
    font-size: 14px;
    font-weight: 800;
}

QLabel#versionBadge {
    color: $fg_dim;
    background: $bg_alt;
    border: 1px solid $border_soft;
    border-radius: 7px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QPushButton#searchPill {
    background: $bg_alt;
    border: 1px solid $border;
    border-radius: 9px;
    color: $fg_dim;
    padding: 6px 12px;
    text-align: left;
}

QPushButton#searchPill:hover {
    border-color: $accent;
    color: $fg_muted;
}

QPushButton#runButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent_strong, stop:1 $gradient_to);
    border: none;
    border-radius: 9px;
    color: #ffffff;
    padding: 7px 16px;
    font-weight: 700;
}

QPushButton#runButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent, stop:1 $gradient_to);
}

QPushButton#runButton:pressed {
    padding-top: 8px;
    padding-bottom: 6px;
}

QPushButton#runButton:disabled {
    background: $bg_alt;
    border: 1px solid $border_soft;
    color: $fg_dim;
}

QPushButton#iconButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 6px;
}

QPushButton#iconButton:hover {
    background: $hover;
    border-color: $border_soft;
}

QPushButton#iconButton:pressed {
    background: $accent_soft;
}

QPushButton#iconButton:checked {
    background: $accent_soft;
    border-color: $accent;
}

QPushButton#iconButton:disabled {
    background: transparent;
}

QFrame#sidebarCard {
    background: $bg_panel;
    border: 1px solid $border;
    border-radius: 12px;
}

QFrame#editorCard {
    background: $bg_editor;
    border: 1px solid $border;
    border-radius: 12px;
}

QFrame#outputCard {
    background: $bg_output;
    border: 1px solid $border;
    border-radius: 12px;
}

QTabWidget#bottomTabs::pane {
    border: none;
    background: transparent;
}

QTabBar#bottomTabBar::tab {
    padding: 6px 10px;
    font-size: 10px;
    font-weight: 700;
}

QWidget#terminalPanel {
    background: transparent;
}

QLabel#terminalCwd {
    color: $fg_muted;
    font-size: 10px;
    padding: 0 4px;
}

QWidget#editorHeader {
    background: transparent;
    border-bottom: 1px solid $border_soft;
}

QLabel#pathLabel {
    color: $fg_muted;
    font-size: 11px;
}

QLabel#languagePill {
    border-radius: 8px;
    padding: 2px 9px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#panelHeader {
    color: $fg_dim;
    font-size: 10px;
    font-weight: 800;
}

QLabel#folderName {
    color: $fg;
    font-size: 12px;
    font-weight: 700;
}

QLabel#runStatus, QLabel#statusPill {
    border-radius: 8px;
    padding: 2px 9px;
    font-size: 10px;
    font-weight: 800;
}

QLabel#hint {
    color: $fg_dim;
    font-size: 11px;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar {
    background: transparent;
}

QTabBar::tab {
    background: transparent;
    color: $fg_dim;
    padding: 8px 14px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}

QTabBar::tab:selected {
    color: $fg;
    border-bottom: 2px solid $accent;
}

QTabBar::tab:hover:!selected {
    color: $fg_muted;
}

QPushButton#tabCloseButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 0;
}

QPushButton#tabCloseButton:hover {
    background: $hover;
}

QTreeView {
    background: transparent;
    border: none;
    outline: 0;
    padding: 4px 6px;
}

QTreeView::item {
    padding: 5px 4px;
    border-radius: 6px;
    color: $fg_muted;
}

QTreeView::item:hover {
    background: $hover;
    color: $fg;
}

QTreeView::item:selected {
    background: $accent_soft;
    color: $fg;
}

QHeaderView::section {
    background: transparent;
    border: none;
}

QSplitter::handle {
    background: $bg;
}

QSplitter::handle:horizontal {
    width: 10px;
}

QSplitter::handle:vertical {
    height: 10px;
}

QLineEdit {
    background: $bg_alt;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px 9px;
    color: $fg;
    selection-background-color: $accent_strong;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border-color: $accent;
}

QLineEdit:disabled {
    color: $fg_dim;
}

QPlainTextEdit#codeEditor {
    background: $bg_editor;
    color: $fg;
    border: none;
    selection-background-color: $selection;
    selection-color: $fg;
    font-family: "DejaVu Sans Mono", "Consolas", "Courier New", monospace;
}

QPlainTextEdit#outputConsole {
    background: $bg_output;
    color: $fg;
    border: none;
    selection-background-color: $selection;
    selection-color: $fg;
    font-family: "DejaVu Sans Mono", "Consolas", "Courier New", monospace;
}

QPushButton {
    background: $bg_alt;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px 14px;
    color: $fg;
}

QPushButton:hover {
    background: $hover;
    border-color: $accent_soft;
}

QPushButton:pressed {
    background: $accent_soft;
}

QPushButton:disabled {
    color: $fg_dim;
    background: $bg_alt;
    border-color: $border_soft;
}

QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent_strong, stop:1 $gradient_to);
    border: none;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent, stop:1 $gradient_to);
}

QPushButton#chip {
    padding: 3px 10px;
    font-size: 11px;
    border-radius: 6px;
    color: $fg_muted;
}

QPushButton#chip:hover {
    color: $fg;
}

QCheckBox {
    color: $fg_muted;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid $border;
    border-radius: 4px;
    background: $bg_alt;
}

QCheckBox::indicator:checked {
    background: $accent;
    border-color: $accent;
}

QDialog#settingsDialog {
    background: $bg;
}

QLabel#settingsBadge {
    background: $accent_soft;
    border: 1px solid $border;
    border-radius: 10px;
}

QLabel#settingsTitle {
    color: $fg;
    font-size: 20px;
    font-weight: 800;
}

QLabel#settingsSubtitle {
    color: $fg_muted;
    font-size: 11px;
}

QFrame#settingsCard {
    background: $bg_panel;
    border: 1px solid $border;
    border-radius: 14px;
}

QCheckBox#settingsCheck {
    color: $fg;
    font-size: 12px;
    font-weight: 600;
    spacing: 8px;
}

QLabel#settingsName {
    color: $fg_muted;
    font-size: 11px;
    font-weight: 600;
}

QLabel#settingsDescription, QLabel#settingsHint {
    color: $fg_dim;
    font-size: 10px;
}

QLabel#settingsValue {
    color: $fg;
    font-size: 11px;
    font-weight: 700;
}

QLabel#settingsValue:disabled {
    color: $fg_dim;
}

QSlider {
    min-height: 22px;
}

QSlider::groove:horizontal {
    height: 4px;
    background: $border_soft;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent_strong, stop:1 $gradient_to);
    border-radius: 2px;
}

QSlider::add-page:horizontal {
    background: $border_soft;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -6px 0;
    background: #ffffff;
    border: 2px solid $accent;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: $accent;
    border-color: $accent_strong;
}

QSlider::handle:horizontal:disabled {
    background: $border;
    border-color: $border_soft;
}

QSlider::sub-page:horizontal:disabled {
    background: $border_soft;
}

QWidget#findBar {
    background: $bg_alt;
    border-bottom: 1px solid $border_soft;
}

QProgressBar {
    border: none;
    background: $border_soft;
    min-height: 3px;
    max-height: 3px;
    border-radius: 1px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $accent_strong, stop:1 $gradient_to);
    border-radius: 1px;
}

QStatusBar {
    background: $bg_panel;
    border-top: 1px solid $border_soft;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: $fg_muted;
    padding: 0 6px;
    font-size: 11px;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: $scroll;
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: $scroll_hover;
}

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: $scroll;
    min-width: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: $scroll_hover;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

QWidget#welcomePage {
    background: transparent;
}

QScrollArea#welcomeScroll {
    background: transparent;
    border: none;
}

QScrollArea#welcomeScroll > QWidget > QWidget {
    background: transparent;
}

QWidget#welcomeCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 $bg_alt, stop:1 $bg_panel);
    border: 1px solid $border;
    border-radius: 20px;
}

QLabel#welcomeBadge {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 $gradient_from, stop:1 $gradient_to);
    color: #ffffff;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 800;
}

QLabel#welcomeTitle {
    color: $fg;
    font-size: 34px;
    font-weight: 800;
}

QLabel#welcomeSubtitle {
    color: $fg_muted;
    font-size: 14px;
}

QLabel#sectionLabel {
    color: $fg_dim;
    font-size: 10px;
    font-weight: 800;
}

QLabel#langChip {
    background: $bg_alt;
    border: 1px solid $border_soft;
    border-radius: 9px;
    padding: 3px 8px;
    color: $fg_muted;
    font-size: 10px;
}

QPushButton#langChip {
    background: transparent;
    border: 1px solid $border_soft;
    border-radius: 7px;
    padding: 3px 10px;
    color: $fg_muted;
    font-size: 11px;
    text-align: left;
}

QPushButton#langChip:hover {
    background: $accent_soft;
    border-color: $accent;
    color: $fg;
}

QPushButton#langChip:pressed {
    background: $selection;
}

QLabel#statusWords {
    color: $fg_muted;
    font-size: 10px;
    padding: 0 6px;
}

QLabel#statusClock {
    color: $accent;
    background: $accent_soft;
    border: 1px solid $border_soft;
    border-radius: 7px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#statusGit {
    color: $green;
    background: $bg_alt;
    border: 1px solid $border_soft;
    border-radius: 7px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#statusLive {
    color: $green;
    background: $bg_alt;
    border: 1px solid $border_soft;
    border-radius: 7px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

QSplitter#editorSplit::handle:horizontal {
    width: 6px;
}

QSplitter#editorSplit::handle:vertical {
    height: 6px;
}

QWidget#pluginsPage, QWidget#pluginsList, QScrollArea#pluginsScroll {
    background: transparent;
    border: none;
}

QLabel#pluginsTitle {
    color: $fg;
    font-size: 28px;
    font-weight: 800;
}

QLabel#pluginsSubtitle {
    color: $fg_muted;
    font-size: 11px;
}

QLabel#pluginsCount {
    color: $accent;
    background: $accent_soft;
    border: 1px solid $border;
    border-radius: 9px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 800;
}

QFrame#pluginCard {
    background: $bg_panel;
    border: 1px solid $border;
    border-radius: 12px;
}

QFrame#pluginCard:hover {
    border-color: $accent;
    background: $bg_alt;
}

QLabel#pluginIcon {
    background: $accent_soft;
    border: 1px solid $border;
    border-radius: 10px;
}

QLabel#pluginName {
    color: $fg;
    font-size: 13px;
    font-weight: 700;
}

QLabel#pluginCategory {
    color: $accent;
    background: $accent_soft;
    border-radius: 6px;
    padding: 1px 7px;
    font-size: 8px;
    font-weight: 800;
}

QLabel#pluginDescription {
    color: $fg_muted;
    font-size: 10px;
}

QCheckBox#pluginToggle {
    color: $fg_muted;
    font-size: 10px;
    font-weight: 600;
    spacing: 7px;
}

QCheckBox#pluginToggle::indicator {
    width: 26px;
    height: 14px;
    border-radius: 7px;
    background: $bg_output;
    border: 1px solid $border;
}

QCheckBox#pluginToggle::indicator:checked {
    background: $accent;
    border-color: $accent;
}

QFrame#keywordSuggestionsFrame {
    background: $bg_alt;
    border: 1px solid $border;
    border-radius: 8px;
}

QListWidget#keywordSuggestions {
    background: transparent;
    border: none;
    outline: 0;
    padding: 4px;
    color: $fg;
}

QListWidget#keywordSuggestions::item {
    padding: 4px 10px;
    border-radius: 5px;
}

QListWidget#keywordSuggestions::item:selected {
    background: $accent_soft;
    color: $fg;
}

QListWidget#recentList {
    background: transparent;
    border: none;
    outline: 0;
}

QListWidget#recentList::item {
    border-radius: 8px;
    padding: 2px;
}

QListWidget#recentList::item:hover {
    background: $hover;
}

QListWidget#recentList::item:selected {
    background: $accent_soft;
}

QLabel#recentName {
    color: $fg;
    font-size: 12px;
    font-weight: 600;
}

QLabel#recentPath {
    color: $fg_dim;
    font-size: 10px;
}

QFrame#paletteCard {
    background: $bg_alt;
    border: 1px solid $border;
    border-radius: 14px;
}

QLineEdit#paletteSearch {
    background: transparent;
    border: none;
    border-bottom: 1px solid $border_soft;
    border-radius: 0;
    padding: 14px 18px;
    font-size: 15px;
}

QLineEdit#paletteSearch:focus {
    border: none;
    border-bottom: 1px solid $accent;
}

QListWidget#paletteList {
    background: transparent;
    border: none;
    outline: 0;
    padding: 8px;
}

QListWidget#paletteList::item {
    border-radius: 8px;
    padding: 2px 6px;
}

QListWidget#paletteList::item:selected {
    background: $accent_soft;
}

QLabel#paletteName {
    color: $fg;
    font-size: 13px;
}

QLabel#shortcutChip {
    color: $fg_dim;
    font-size: 10px;
    background: $bg_editor;
    border: 1px solid $border_soft;
    border-radius: 6px;
    padding: 2px 7px;
}

QLabel#paletteHint {
    color: $fg_dim;
    font-size: 10px;
    padding: 8px;
}

QToolTip {
    background: $bg_alt;
    color: $fg;
    border: 1px solid $border;
    padding: 4px 6px;
}
"""
)


def build_qss() -> str:
    tokens = {
        token: globals()[token.upper()]
        for token in THEMES[CURRENT_THEME][1]
    }
    return _QSS.substitute(tokens)


QSS = build_qss()
