"""Main application window."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QTime, QTimer, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QCloseEvent,
    QDesktopServices,
    QGuiApplication,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__, git, icons, theme
from .console import OutputPanel
from .editor import CodeEditor
from .explorer import Explorer
from .findbar import FindBar
from .highlighter import create_highlighter
from .languages import (
    language_for_key,
    language_for_path,
    display_languages,
)
from .liveserver import LiveServer
from .palette import CommandPalette
from .plugins import (
    PLUGINS,
    PLUGIN_BY_KEY,
    PluginManagerPage,
    default_plugin_states,
)
from .runner import Runner
from .settings_dialog import SettingsDialog
from .terminal import TerminalPanel
from .welcome import WelcomePage

WEB_PREVIEW_LANGUAGES = {"html", "css"}


def detect_language(path: Path | None) -> str:
    return language_for_path(path).key


def _as_int_list(value) -> list[int] | None:
    if not value:
        return None
    try:
        return [int(item) for item in value]
    except (TypeError, ValueError):
        return None


def _as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _rgba(color: str, alpha: float) -> str:
    value = QColor(color)
    return (
        f"rgba({value.red()}, {value.green()}, {value.blue()}, "
        f"{alpha:.2f})"
    )


class MainWindow(QMainWindow):
    def __init__(self, start_path: Path | None = None):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(980, 640)
        self.resize(1320, 840)
        self.setAcceptDrops(True)

        self._settings = QSettings("CodeForge", "CodeForge")
        self._font_size = 12
        self._console_font_size = 11
        self._transparency_enabled = False
        self._transparency_opacity = 90
        self._recent: list[str] = []
        self._untitled_count = 0
        self._folder: Path | None = None
        self._closing = False
        self._icon_actions: dict[QAction, tuple[str, str]] = {}
        self._theme_actions: dict[str, QAction] = {}
        self._run_text = "READY"
        self._run_kind = "ready"
        self._plugin_states = default_plugin_states()
        self._plugins_page: PluginManagerPage | None = None
        self._zen_previous: tuple[bool, bool] | None = None
        self._git_status: git.GitStatus | None = None
        self._active_tabs: QTabWidget | None = None
        self._split_orientation = Qt.Orientation.Horizontal

        self._live_server = LiveServer()
        self._runner = Runner(self)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setInterval(30_000)
        self._auto_save_timer.timeout.connect(self._auto_save_modified)
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1_000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._git_timer = QTimer(self)
        self._git_timer.setInterval(5_000)
        self._git_timer.timeout.connect(self._refresh_git_status)

        self._create_actions()
        self._create_theme_actions()
        self._build_ui()
        self._build_menus()
        self._connect_signals()
        self._restore_settings()
        self._open_initial(start_path)
        self._apply_plugin_states()
        self._rebuild_recent_menu()
        self._welcome.set_recent(self._recent)
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _make_action(
        self,
        text: str,
        shortcut: str | QKeySequence.StandardKey | None = None,
        slot=None,
        icon_name: str | None = None,
        icon_role: str = "muted",
        checkable: bool = False,
        checked: bool = False,
        shortcuts: list[str] | None = None,
        palette_text: str | None = None,
    ) -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut))
        if shortcuts:
            action.setShortcuts([QKeySequence(item) for item in shortcuts])
        if icon_name is not None:
            self._icon_actions[action] = (icon_name, icon_role)
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
        if palette_text:
            action.setProperty("paletteText", palette_text)
        if slot is not None:
            action.triggered.connect(slot)
        self.addAction(action)
        return action

    def _create_actions(self) -> None:
        std = QKeySequence.StandardKey

        self._new_action = self._make_action(
            "&New File", "Ctrl+N", lambda: self.new_file("python"),
            icon_name="new",
        )
        self._new_any_action = self._make_action(
            "New File &As…", "Ctrl+Shift+N", self.new_file_dialog,
            icon_name="plus",
        )
        self._open_action = self._make_action(
            "&Open File…", "Ctrl+O", self.open_file_dialog,
            icon_name="open",
        )
        self._open_folder_action = self._make_action(
            "Open F&older…", "Ctrl+Shift+O", self.open_folder_dialog,
            icon_name="folder",
        )
        self._save_action = self._make_action(
            "&Save", "Ctrl+S", self.save_current,
            icon_name="save",
        )
        self._save_as_action = self._make_action(
            "Save &As…", "Ctrl+Shift+S", self.save_current_as
        )
        self._save_all_action = self._make_action(
            "Save A&ll", "Ctrl+Alt+S", self.save_all
        )
        self._close_tab_action = self._make_action(
            "&Close Tab", "Ctrl+W", self.close_current_tab,
            icon_name="close",
        )
        self._split_right_action = self._make_action(
            "Split Editor &Right",
            "Ctrl+\\",
            lambda: self.split_editor(Qt.Orientation.Horizontal),
            icon_name="split",
            palette_text="Editor: Split Right",
        )
        self._split_down_action = self._make_action(
            "Split Editor &Down",
            "Ctrl+Shift+\\",
            lambda: self.split_editor(Qt.Orientation.Vertical),
            icon_name="split",
            palette_text="Editor: Split Down",
        )
        self._close_split_action = self._make_action(
            "Close Spl&it",
            None,
            self.close_split,
            icon_name="close",
            palette_text="Editor: Close Split",
        )
        self._exit_action = self._make_action("E&xit", "Ctrl+Q", self.close)

        self._undo_action = self._make_action(
            "&Undo", std.Undo, lambda: self._editor_call("undo")
        )
        self._redo_action = self._make_action(
            "&Redo", std.Redo, lambda: self._editor_call("redo")
        )
        self._cut_action = self._make_action(
            "Cu&t", std.Cut, lambda: self._editor_call("cut")
        )
        self._copy_action = self._make_action(
            "&Copy", std.Copy, lambda: self._editor_call("copy")
        )
        self._paste_action = self._make_action(
            "&Paste", std.Paste, lambda: self._editor_call("paste")
        )
        self._select_all_action = self._make_action(
            "Select &All", std.SelectAll, lambda: self._editor_call("selectAll")
        )
        self._find_action = self._make_action(
            "&Find…", "Ctrl+F", self.show_find, icon_name="search"
        )
        self._replace_action = self._make_action(
            "&Replace…", "Ctrl+H", self.show_replace
        )
        self._find_next_action = self._make_action(
            "Find &Next", "F3", self.find_next
        )
        self._find_previous_action = self._make_action(
            "Find &Previous", "Shift+F3", self.find_previous
        )
        self._comment_action = self._make_action(
            "Toggle &Comment", "Ctrl+/", lambda: self._editor_call("toggle_comment")
        )

        self._run_action = self._make_action(
            "&Run", "F5", self.run_current, icon_name="run", icon_role="accent"
        )
        self._stop_action = self._make_action(
            "&Stop", "Shift+F5", self.stop_current,
            icon_name="stop", icon_role="red",
        )
        self._build_action = self._make_action(
            "&Build", "Ctrl+Shift+B", self.build_current,
            icon_name="build", icon_role="yellow",
        )
        self._live_start_action = self._make_action(
            "Start &Live Server",
            "Ctrl+Alt+L",
            self.start_live_server,
            icon_name="globe",
            icon_role="green",
            palette_text="Live Server: Start",
        )
        self._live_preview_action = self._make_action(
            "Open Live &Preview",
            None,
            self.open_live_preview,
            icon_name="globe",
            palette_text="Live Server: Open Preview",
        )
        self._live_stop_action = self._make_action(
            "Stop Live Server",
            None,
            self.stop_live_server,
            icon_name="stop",
            icon_role="red",
            palette_text="Live Server: Stop",
        )
        self._clear_output_action = self._make_action(
            "Clear &Output", "Ctrl+L", self._output_clear
        )

        self._git_refresh_action = self._make_action(
            "Re&fresh Git Status",
            "Ctrl+Shift+G",
            self.refresh_git_status,
            icon_name="git",
            icon_role="green",
            palette_text="Git: Refresh Status",
        )
        self._git_changes_action = self._make_action(
            "Show &Changes",
            None,
            self.show_git_changes,
            icon_name="file",
            palette_text="Git: Show Changes",
        )
        self._git_diff_action = self._make_action(
            "Show &Diff",
            None,
            self.show_git_diff,
            icon_name="file",
            palette_text="Git: Show Diff",
        )
        self._git_log_action = self._make_action(
            "Show &Log",
            None,
            self.show_git_log,
            icon_name="git",
            palette_text="Git: Show Log",
        )
        self._git_stage_action = self._make_action(
            "&Stage All Changes",
            None,
            self.stage_all_changes,
            icon_name="plus",
            icon_role="green",
            palette_text="Git: Stage All Changes",
        )
        self._git_commit_action = self._make_action(
            "&Commit…",
            None,
            self.commit_changes,
            icon_name="save",
            icon_role="accent",
            palette_text="Git: Commit",
        )

        self._palette_action = self._make_action(
            "Command &Palette…",
            "Ctrl+K",
            self.show_command_palette,
            icon_name="command",
            icon_role="accent",
            shortcuts=["Ctrl+K", "Ctrl+Shift+P"],
        )
        self._plugins_action = self._make_action(
            "&Plugins",
            "Ctrl+Shift+X",
            self.show_plugins_tab,
            icon_name="plugins",
            icon_role="accent",
            palette_text="Plugins: Open Plugin Manager",
        )
        self._settings_action = self._make_action(
            "&Settings…",
            "Ctrl+,",
            self.show_settings,
            icon_name="settings",
        )

        self._zoom_in_action = self._make_action(
            "Zoom &In", "Ctrl+=", lambda: self.set_font_size(self._font_size + 1)
        )
        self._zoom_out_action = self._make_action(
            "Zoom &Out", "Ctrl+-", lambda: self.set_font_size(self._font_size - 1)
        )
        self._zoom_reset_action = self._make_action(
            "&Reset Zoom", "Ctrl+0", lambda: self.set_font_size(12)
        )
        self._toggle_sidebar_action = self._make_action(
            "Show &Explorer", "Ctrl+B", self._set_sidebar_visible,
            icon_name="panel", checkable=True, checked=True,
        )
        self._toggle_output_action = self._make_action(
            "Show &Output", "Ctrl+J", None,
            icon_name="terminal", checkable=True, checked=True,
        )
        self._focus_terminal_action = self._make_action(
            "Show &Terminal",
            "Ctrl+`",
            self.show_terminal,
            icon_name="terminal",
            palette_text="Terminal: Focus",
        )

        self._about_action = self._make_action(
            "&About CodeForge", None, self.show_about
        )
        self._about_qt_action = self._make_action(
            "About &Qt", None, lambda: QMessageBox.aboutQt(self, "About Qt")
        )

        self._new_action.setToolTip("New Python file (Ctrl+N)")
        self._new_any_action.setToolTip("Create a file in any language (Ctrl+Shift+N)")
        self._open_action.setToolTip("Open a file (Ctrl+O)")
        self._save_action.setToolTip("Save (Ctrl+S)")
        self._run_action.setToolTip("Run the current file (F5)")
        self._stop_action.setToolTip("Stop the running program (Shift+F5)")
        self._build_action.setToolTip("Compile the current file (Ctrl+Shift+B)")
        self._split_right_action.setToolTip(
            "Show a second editor pane side by side (Ctrl+\\)"
        )
        self._split_down_action.setToolTip(
            "Show a second editor pane below (Ctrl+Shift+\\)"
        )
        self._close_split_action.setToolTip("Close the secondary editor pane")
        self._live_start_action.setToolTip(
            "Serve the workspace and open it in your browser (Ctrl+Alt+L)"
        )
        self._live_preview_action.setToolTip(
            "Open the current page in the live preview"
        )
        self._live_stop_action.setToolTip("Stop the live preview server")
        self._palette_action.setToolTip("Search every command (Ctrl+K)")
        self._plugins_action.setToolTip("Manage built-in plugins (Ctrl+Shift+X)")
        self._settings_action.setToolTip("Appearance and window preferences (Ctrl+,)")
        self._toggle_sidebar_action.setToolTip("Show or hide the explorer (Ctrl+B)")
        self._toggle_output_action.setToolTip("Show or hide the bottom panel (Ctrl+J)")
        self._focus_terminal_action.setToolTip(
            "Open the interactive terminal (Ctrl+`)"
        )
        self._git_refresh_action.setToolTip(
            "Refresh repository branch and working-tree status (Ctrl+Shift+G)"
        )
        self._git_changes_action.setToolTip("Show Git status and diff statistics")
        self._git_diff_action.setToolTip("Show the current working-tree diff")
        self._git_log_action.setToolTip("Show recent commits")
        self._git_stage_action.setToolTip("Stage every change in the repository")
        self._git_commit_action.setToolTip("Commit staged changes")

    def _create_theme_actions(self) -> None:
        group = QActionGroup(self)
        group.setExclusive(True)
        for key in theme.THEME_ORDER:
            label = theme.theme_label(key)
            action = self._make_action(
                label,
                None,
                lambda _checked=False, name=key: self.apply_theme(name),
                checkable=True,
                checked=key == theme.CURRENT_THEME,
                palette_text=f"Theme: {label}",
            )
            group.addAction(action)
            self._theme_actions[key] = action

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._tabs = self._create_editor_tabs()
        self._tabs_secondary = self._create_editor_tabs()
        self._tabs_secondary.setVisible(False)
        self._active_tabs = self._tabs

        self._editor_split = QSplitter(Qt.Orientation.Horizontal)
        self._editor_split.setObjectName("editorSplit")
        self._editor_split.addWidget(self._tabs)
        self._editor_split.addWidget(self._tabs_secondary)
        self._editor_split.setStretchFactor(0, 1)
        self._editor_split.setStretchFactor(1, 1)
        self._editor_split.setCollapsible(0, False)
        self._editor_split.setCollapsible(1, False)

        self._welcome = WelcomePage()
        self._stack = QStackedWidget()
        self._stack.addWidget(self._welcome)
        self._stack.addWidget(self._editor_split)

        self._find_bar = FindBar()
        self._find_bar.setVisible(False)

        self._path_label = QLabel("No file open")
        self._path_label.setObjectName("pathLabel")
        self._path_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self._language_dot = QLabel()
        self._language_dot.setFixedSize(8, 8)
        self._language_pill = QLabel()
        self._language_pill.setObjectName("languagePill")

        editor_header = QWidget()
        editor_header.setObjectName("editorHeader")
        header_layout = QHBoxLayout(editor_header)
        header_layout.setContentsMargins(14, 6, 14, 6)
        header_layout.setSpacing(8)
        header_layout.addWidget(self._path_label, 1)
        header_layout.addWidget(self._language_dot)
        header_layout.addWidget(self._language_pill)

        self._editor_card = QFrame()
        self._editor_card.setObjectName("editorCard")
        editor_layout = QVBoxLayout(self._editor_card)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(editor_header)
        editor_layout.addWidget(self._find_bar)
        editor_layout.addWidget(self._stack, 1)

        self._explorer = Explorer()
        sidebar_card = QFrame()
        sidebar_card.setObjectName("sidebarCard")
        sidebar_layout = QVBoxLayout(sidebar_card)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(self._explorer)
        self._sidebar_card = sidebar_card

        self._output = OutputPanel()
        self._terminal = TerminalPanel()
        self._bottom_tabs = QTabWidget()
        self._bottom_tabs.setObjectName("bottomTabs")
        self._bottom_tabs.setDocumentMode(True)
        self._bottom_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._bottom_tabs.tabBar().setObjectName("bottomTabBar")
        self._bottom_tabs.addTab(self._output, "Output")
        self._bottom_tabs.addTab(self._terminal, "Terminal")
        self._bottom_tabs.setCurrentWidget(self._output)

        output_card = QFrame()
        output_card.setObjectName("outputCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(self._bottom_tabs)
        self._output_card = output_card

        self._right_split = QSplitter(Qt.Orientation.Vertical)
        self._right_split.addWidget(self._editor_card)
        self._right_split.addWidget(output_card)
        self._right_split.setStretchFactor(0, 1)
        self._right_split.setStretchFactor(1, 0)
        self._right_split.setSizes([600, 280])
        self._right_split.setCollapsible(0, False)

        self._main_split = QSplitter(Qt.Orientation.Horizontal)
        self._main_split.addWidget(sidebar_card)
        self._main_split.addWidget(self._right_split)
        self._main_split.setStretchFactor(0, 0)
        self._main_split.setStretchFactor(1, 1)
        self._main_split.setSizes([280, 1020])
        self._main_split.setCollapsible(0, True)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._main_split)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self._build_command_bar())
        central_layout.addWidget(body, 1)
        self.setCentralWidget(central)

        self._build_status_bar()

    def _build_command_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("commandBar")
        bar.setFixedHeight(56)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        logo = QLabel("</>")
        logo.setObjectName("logoBadge")
        logo.setTextFormat(Qt.TextFormat.PlainText)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(34, 34)

        name = QLabel("CodeForge")
        name.setObjectName("appName")

        version = QLabel(f"v{__version__}")
        version.setObjectName("versionBadge")

        self._sidebar_button = QPushButton()
        self._sidebar_button.setObjectName("iconButton")
        self._sidebar_button.setFixedSize(32, 32)
        self._sidebar_button.setIconSize(QSize(17, 17))
        self._sidebar_button.setCheckable(True)
        self._sidebar_button.setChecked(True)
        self._sidebar_button.setToolTip("Toggle explorer (Ctrl+B)")
        self._sidebar_button.clicked.connect(self._set_sidebar_visible)

        self._search_button = QPushButton("Search commands…   Ctrl+K")
        self._search_button.setObjectName("searchPill")
        self._search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_button.setToolTip("Command palette (Ctrl+K)")
        self._search_button.clicked.connect(self.show_command_palette)

        self._run_button = QPushButton("Run")
        self._run_button.setObjectName("runButton")
        self._run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_button.setToolTip("Run current file (F5)")
        self._run_button.clicked.connect(self.run_current)

        self._stop_button = QPushButton()
        self._stop_button.setObjectName("iconButton")
        self._stop_button.setFixedSize(32, 32)
        self._stop_button.setIconSize(QSize(16, 16))
        self._stop_button.setToolTip("Stop (Shift+F5)")
        self._stop_button.clicked.connect(self.stop_current)

        self._build_button = QPushButton()
        self._build_button.setObjectName("iconButton")
        self._build_button.setFixedSize(32, 32)
        self._build_button.setIconSize(QSize(16, 16))
        self._build_button.setToolTip("Build (Ctrl+Shift+B)")
        self._build_button.clicked.connect(self.build_current)

        self._plugins_button = QPushButton()
        self._plugins_button.setObjectName("iconButton")
        self._plugins_button.setFixedSize(32, 32)
        self._plugins_button.setIconSize(QSize(17, 17))
        self._plugins_button.setToolTip("Plugins (Ctrl+Shift+X)")
        self._plugins_button.clicked.connect(self.show_plugins_tab)

        self._settings_button = QPushButton()
        self._settings_button.setObjectName("iconButton")
        self._settings_button.setFixedSize(32, 32)
        self._settings_button.setIconSize(QSize(17, 17))
        self._settings_button.setToolTip("Settings (Ctrl+,)")
        self._settings_button.clicked.connect(self.show_settings)

        layout.addWidget(logo)
        layout.addWidget(name)
        layout.addWidget(version)
        layout.addSpacing(8)
        layout.addStretch(1)
        layout.addWidget(self._sidebar_button)
        layout.addWidget(self._search_button)
        layout.addSpacing(4)
        layout.addWidget(self._run_button)
        layout.addWidget(self._stop_button)
        layout.addWidget(self._build_button)
        layout.addSpacing(2)
        layout.addWidget(self._plugins_button)
        layout.addWidget(self._settings_button)

        self._refresh_command_icons()
        return bar

    def _build_status_bar(self) -> None:
        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_language = QLabel("Plain Text")
        self._status_position = QLabel("Ln 1, Col 1")
        self._status_spaces = QLabel("Spaces: 4")
        self._status_words = QLabel("0 words")
        self._status_words.setObjectName("statusWords")
        self._status_words.setVisible(False)
        self._status_clock = QLabel("")
        self._status_clock.setObjectName("statusClock")
        self._status_clock.setVisible(False)
        self._status_git = QLabel("")
        self._status_git.setObjectName("statusGit")
        self._status_git.setVisible(False)
        self._status_live = QLabel("")
        self._status_live.setObjectName("statusLive")
        self._status_live.setVisible(False)
        self._status_encoding = QLabel("UTF-8")
        self._status_run = QLabel("READY")
        self._status_run.setObjectName("runStatus")

        status.addWidget(self._status_dot)
        status.addWidget(self._status_language)
        status.addWidget(self._status_position)
        status.addWidget(self._status_spaces)
        status.addPermanentWidget(self._status_words)
        status.addPermanentWidget(self._status_clock)
        status.addPermanentWidget(self._status_live)
        status.addPermanentWidget(self._status_git)
        status.addPermanentWidget(self._status_encoding)
        status.addPermanentWidget(self._status_run)

    def _build_menus(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")
        file_menu.addAction(self._new_action)
        file_menu.addAction(self._new_any_action)
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._open_folder_action)
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu("Recent Files")
        file_menu.addSeparator()
        file_menu.addAction(self._save_action)
        file_menu.addAction(self._save_as_action)
        file_menu.addAction(self._save_all_action)
        file_menu.addSeparator()
        file_menu.addAction(self._close_tab_action)
        file_menu.addAction(self._exit_action)

        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._cut_action)
        edit_menu.addAction(self._copy_action)
        edit_menu.addAction(self._paste_action)
        edit_menu.addAction(self._select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._find_action)
        edit_menu.addAction(self._replace_action)
        edit_menu.addAction(self._find_next_action)
        edit_menu.addAction(self._find_previous_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._comment_action)

        run_menu = bar.addMenu("&Run")
        run_menu.addAction(self._run_action)
        run_menu.addAction(self._stop_action)
        run_menu.addAction(self._build_action)
        run_menu.addSeparator()
        run_menu.addAction(self._live_start_action)
        run_menu.addAction(self._live_preview_action)
        run_menu.addAction(self._live_stop_action)
        run_menu.addSeparator()
        run_menu.addAction(self._clear_output_action)

        self._git_menu = bar.addMenu("&Git")
        self._git_menu.addAction(self._git_refresh_action)
        self._git_menu.addSeparator()
        self._git_menu.addAction(self._git_changes_action)
        self._git_menu.addAction(self._git_diff_action)
        self._git_menu.addAction(self._git_log_action)
        self._git_menu.addSeparator()
        self._git_menu.addAction(self._git_stage_action)
        self._git_menu.addAction(self._git_commit_action)
        self._git_menu.menuAction().setVisible(False)

        view_menu = bar.addMenu("&View")
        view_menu.addAction(self._palette_action)
        view_menu.addAction(self._plugins_action)
        view_menu.addSeparator()
        view_menu.addAction(self._toggle_sidebar_action)
        view_menu.addAction(self._toggle_output_action)
        view_menu.addAction(self._focus_terminal_action)
        view_menu.addSeparator()
        view_menu.addAction(self._split_right_action)
        view_menu.addAction(self._split_down_action)
        view_menu.addAction(self._close_split_action)
        view_menu.addSeparator()
        view_menu.addAction(self._zoom_in_action)
        view_menu.addAction(self._zoom_out_action)
        view_menu.addAction(self._zoom_reset_action)
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("&Theme")
        for action in self._theme_actions.values():
            theme_menu.addAction(action)
        view_menu.addSeparator()
        view_menu.addAction(self._settings_action)

        help_menu = bar.addMenu("&Help")
        help_menu.addAction(self._about_action)
        help_menu.addAction(self._about_qt_action)

    def _connect_signals(self) -> None:
        self._bottom_tabs.currentChanged.connect(self._on_bottom_tab_changed)

        self._explorer.file_activated.connect(self.open_file)
        self._explorer.file_renamed.connect(self._on_file_renamed)
        self._explorer.file_deleted.connect(self._on_file_deleted)

        self._welcome.new_file.connect(lambda: self.new_file("python"))
        self._welcome.open_file.connect(self.open_file_dialog)
        self._welcome.open_folder.connect(self.open_folder_dialog)
        self._welcome.command_palette.connect(self.show_command_palette)
        self._welcome.recent_selected.connect(self._open_recent)
        self._welcome.language_selected.connect(self.new_file)

        self._runner.output.connect(self._output.feed)
        self._runner.state_changed.connect(self._on_runner_state)
        self._runner.finished.connect(self._on_runner_finished)

        self._output.send_input.connect(self._send_input)
        self._output.stop_requested.connect(self._runner.stop)
        self._output.clear_button.clicked.connect(self._output_clear)

        self._find_bar.search_changed.connect(self._on_search_changed)
        self._find_bar.find_next.connect(self.find_next)
        self._find_bar.find_previous.connect(self.find_previous)
        self._find_bar.replace_one.connect(self._replace_one)
        self._find_bar.replace_all.connect(self._replace_all_matches)
        self._find_bar.closed.connect(self._close_find)

        self._toggle_sidebar_action.toggled.connect(self._set_sidebar_visible)
        self._toggle_output_action.toggled.connect(self._set_output_visible)

        self._escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._escape_shortcut.activated.connect(self._close_find)

    # ------------------------------------------------------------------
    # Theme / icons
    # ------------------------------------------------------------------
    def apply_theme(self, name: str, save: bool = True) -> None:
        theme.activate(name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_qss())

        for editor in self._iter_editors():
            editor.refresh_theme()

        self._refresh_icons()
        self._output.refresh_theme()
        self._terminal.refresh_theme()
        self._explorer.refresh_theme()
        self._welcome.refresh_theme()
        if self._plugins_page is not None:
            self._plugins_page.refresh_theme()
        self._update_editor_header()
        self._update_cursor_status()
        self._set_run_status(self._run_text, self._run_kind)
        self._refresh_git_status()

        action = self._theme_actions.get(theme.CURRENT_THEME)
        if action is not None and not action.isChecked():
            action.setChecked(True)
        if save:
            self._settings.setValue("theme", theme.CURRENT_THEME)

    def _icon_color(self, role: str) -> str:
        return {
            "muted": theme.FG_MUTED,
            "fg": theme.FG,
            "accent": theme.ACCENT,
            "red": theme.RED,
            "yellow": theme.YELLOW,
            "green": theme.GREEN,
            "white": "#ffffff",
        }.get(role, theme.FG_MUTED)

    def _refresh_icons(self) -> None:
        for action, (name, role) in self._icon_actions.items():
            action.setIcon(icons.icon(name, self._icon_color(role), 18))
        self._refresh_command_icons()
        self._refresh_tab_close_icons()

    def _refresh_tab_close_icons(self) -> None:
        if not hasattr(self, "_tabs"):
            return
        for tabs in self._all_editor_tabs():
            for index in range(tabs.count()):
                button = tabs.tabBar().tabButton(
                    index, QTabBar.ButtonPosition.RightSide
                )
                if isinstance(button, QPushButton):
                    button.setIcon(icons.icon("close", theme.FG_DIM, 12))

    def _refresh_command_icons(self) -> None:
        if not hasattr(self, "_run_button"):
            return
        self._search_button.setIcon(icons.icon("search", theme.FG_MUTED, 15))
        self._run_button.setIcon(icons.icon("run", "#ffffff", 15))
        self._stop_button.setIcon(icons.icon("stop", theme.FG_MUTED, 16))
        self._build_button.setIcon(icons.icon("build", theme.FG_MUTED, 16))
        if hasattr(self, "_plugins_button"):
            self._plugins_button.setIcon(icons.icon("plugins", theme.ACCENT, 17))
        if hasattr(self, "_settings_button"):
            self._settings_button.setIcon(icons.icon("settings", theme.FG_MUTED, 17))
        self._update_sidebar_button()

    def _update_sidebar_button(self) -> None:
        if not hasattr(self, "_sidebar_button"):
            return
        color = theme.ACCENT if self._sidebar_button.isChecked() else theme.FG_MUTED
        self._sidebar_button.setIcon(icons.icon("panel", color, 17))

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def _apply_transparency(
        self, enabled: bool, opacity: int, save: bool = False
    ) -> None:
        opacity = max(50, min(100, int(opacity)))
        self._transparency_enabled = bool(enabled)
        self._transparency_opacity = opacity
        value = opacity / 100.0 if enabled else 1.0
        self.setWindowOpacity(value)
        if self._is_hyprland():
            self._apply_hyprland_transparency(enabled, value)
        if save:
            self._settings.setValue(
                "transparency_enabled", self._transparency_enabled
            )
            self._settings.setValue("transparency_opacity", opacity)

    def _is_hyprland(self) -> bool:
        app = QGuiApplication.instance()
        platform = app.platformName() if app is not None else ""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
        if platform not in {"wayland", "xcb"}:
            return False
        return "hyprland" in desktop.lower() or bool(signature)

    def _hyprland_window_selector(self) -> str:
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
            clients = json.loads(result.stdout)
            pid = os.getpid()
            matches: list[dict] = []
            for client in clients:
                try:
                    client_pid = int(client.get("pid", -1))
                except (TypeError, ValueError):
                    continue
                if client_pid == pid:
                    matches.append(client)
            for client in matches:
                if "CodeForge" in str(client.get("title", "")):
                    address = client.get("address")
                    if address:
                        return f"address:{address}"
            if matches:
                address = matches[0].get("address")
                if address:
                    return f"address:{address}"
        except (OSError, subprocess.SubprocessError, ValueError, TypeError):
            pass
        return "title:CodeForge"

    def _apply_hyprland_transparency(self, enabled: bool, value: float) -> None:
        window = self._hyprland_window_selector()
        if enabled:
            props = (
                ("opacity_override", "1"),
                ("opacity", f"{value:.2f}"),
                ("opacity_inactive_override", "1"),
                ("opacity_inactive", f"{value:.2f}"),
            )
        else:
            props = (
                ("opacity", "1"),
                ("opacity_override", "0"),
                ("opacity_inactive", "1"),
                ("opacity_inactive_override", "0"),
            )
        try:
            for prop, prop_value in props:
                subprocess.run(
                    [
                        "hyprctl",
                        "dispatch",
                        f'hl.dsp.window.set_prop({{ prop = "{prop}", value = "{prop_value}", window = "{window}" }})',
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
        except (OSError, subprocess.SubprocessError):
            pass

    def show_settings(self) -> None:
        previous = (self._transparency_enabled, self._transparency_opacity)
        dialog = SettingsDialog(*previous, self)
        dialog.preview_changed.connect(self._apply_transparency)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply_transparency(*dialog.values(), save=True)
        else:
            self._apply_transparency(*previous)
        dialog.deleteLater()

    def _restore_settings(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self._settings.value("window_state")
        if state:
            self.restoreState(state)

        try:
            self._font_size = max(8, min(36, int(self._settings.value("font_size", 12))))
        except (TypeError, ValueError):
            self._font_size = 12
        try:
            self._console_font_size = max(
                8, min(36, int(self._settings.value("console_font_size", 11)))
            )
        except (TypeError, ValueError):
            self._console_font_size = 11

        self._output.set_font_size(self._console_font_size)
        self._terminal.set_font_size(self._console_font_size)

        if self._settings.contains("plugins_enabled"):
            stored_plugins = self._settings.value("plugins_enabled", [])
            if isinstance(stored_plugins, str):
                stored_plugins = [
                    item for item in stored_plugins.split(",") if item
                ]
            enabled_plugins = {str(item) for item in (stored_plugins or [])}
            self._plugin_states = {
                spec.key: spec.key in enabled_plugins for spec in PLUGINS
            }
        else:
            self._plugin_states = default_plugin_states()

        try:
            saved_opacity = int(self._settings.value("transparency_opacity", 90))
        except (TypeError, ValueError):
            saved_opacity = 90
        self._apply_transparency(
            _as_bool(self._settings.value("transparency_enabled", False)),
            saved_opacity,
        )

        sizes = _as_int_list(self._settings.value("split_sizes"))
        if sizes and len(sizes) == 2:
            self._main_split.setSizes(sizes)
        sizes = _as_int_list(self._settings.value("v_split_sizes"))
        if sizes and len(sizes) == 2:
            self._right_split.setSizes(sizes)

        stored_recent = self._settings.value("recent_files", [])
        if isinstance(stored_recent, str):
            stored_recent = [stored_recent]
        self._recent = [str(item) for item in (stored_recent or [])][:10]

        stored_theme = str(self._settings.value("theme", theme.CURRENT_THEME))
        self.apply_theme(stored_theme, save=False)

        last_folder = self._settings.value("last_folder", "")
        folder = Path(str(last_folder)).expanduser() if last_folder else None
        if folder is None or not folder.is_dir():
            folder = Path.home() / "projects" / "python"
            if not folder.is_dir():
                folder = Path.home()
        self.set_folder(folder)

    def _open_initial(self, start_path: Path | None) -> None:
        if start_path is None:
            return
        path = Path(start_path).expanduser()
        if path.is_dir():
            self.set_folder(path)
        elif path.is_file():
            self.set_folder(path.parent)
            self.open_file(path)

    def _save_settings(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("window_state", self.saveState())
        self._settings.setValue("split_sizes", self._main_split.sizes())
        self._settings.setValue("v_split_sizes", self._right_split.sizes())
        self._settings.setValue("font_size", self._font_size)
        self._settings.setValue("console_font_size", self._console_font_size)
        self._settings.setValue(
            "transparency_enabled", self._transparency_enabled
        )
        self._settings.setValue("transparency_opacity", self._transparency_opacity)
        self._settings.setValue(
            "plugins_enabled",
            [key for key, enabled in self._plugin_states.items() if enabled],
        )
        self._settings.setValue("recent_files", self._recent)
        self._settings.setValue("last_folder", str(self._folder) if self._folder else "")
        self._settings.setValue("theme", theme.CURRENT_THEME)

    # ------------------------------------------------------------------
    # Plugins
    # ------------------------------------------------------------------
    def _plugin_enabled(self, key: str) -> bool:
        spec = PLUGIN_BY_KEY.get(key)
        default = spec.default if spec is not None else False
        return bool(self._plugin_states.get(key, default))

    def _apply_plugin_states(self) -> None:
        for plugin in PLUGINS:
            self._apply_plugin(plugin.key, self._plugin_enabled(plugin.key))
        if self._plugins_page is not None:
            self._plugins_page.set_states(self._plugin_states)

    def _apply_plugin(self, key: str, enabled: bool) -> None:
        if key == "auto_save":
            if enabled:
                self._auto_save_timer.start()
            else:
                self._auto_save_timer.stop()
            return
        if key == "word_count":
            self._status_words.setVisible(enabled)
            self._update_word_count()
            return
        if key == "status_clock":
            self._status_clock.setVisible(enabled)
            if enabled:
                self._update_clock()
                self._clock_timer.start()
            else:
                self._clock_timer.stop()
            return
        if key == "zen_mode":
            self._set_zen_mode(enabled)
            return
        if key == "git_integration":
            self._apply_git_plugin(enabled)
            return
        if key == "trim_trailing_whitespace" or key == "final_newline":
            return

        for editor in self._iter_editors():
            if key == "word_wrap":
                editor.set_word_wrap(enabled)
            elif key == "indent_guides":
                editor.set_indent_guides_enabled(enabled)
            elif key == "current_line":
                editor.set_current_line_highlight(enabled)
            elif key == "auto_close_brackets":
                editor.set_auto_close_brackets(enabled)

    def _apply_git_plugin(self, enabled: bool) -> None:
        self._git_menu.menuAction().setVisible(enabled)
        if enabled:
            self._git_timer.start()
            self._refresh_git_status()
            return
        self._git_timer.stop()
        self._git_status = None
        self._status_git.setVisible(False)
        self._update_git_actions()

    def _git_path(self) -> Path | None:
        editor = self.current_editor()
        if editor is not None and editor.path is not None:
            return editor.path
        return self._folder

    def _refresh_git_status(self) -> None:
        if not self._plugin_enabled("git_integration"):
            self._status_git.setVisible(False)
            self._update_git_actions()
            return

        status = git.read_status(self._git_path())
        self._git_status = status
        if status is None:
            self._status_git.setVisible(False)
        elif status.error:
            self._status_git.setText("git unavailable")
            self._status_git.setStyleSheet(f"color: {theme.RED};")
            self._status_git.setToolTip(status.error)
            self._status_git.setVisible(True)
        else:
            self._status_git.setText(git.status_label(status))
            color = theme.YELLOW if status.dirty else theme.GREEN
            self._status_git.setStyleSheet(f"color: {color};")
            self._status_git.setToolTip(git.status_tooltip(status))
            self._status_git.setVisible(True)
        self._update_git_actions()

    def _update_git_actions(self) -> None:
        enabled = self._plugin_enabled("git_integration")
        self._git_menu.menuAction().setVisible(enabled)
        status = self._git_status
        available = bool(enabled and status is not None and not status.error)
        dirty = bool(available and status is not None and status.dirty)
        staged = bool(available and status is not None and status.staged)

        for action in (
            self._git_refresh_action,
            self._git_changes_action,
            self._git_log_action,
        ):
            action.setEnabled(available)
        self._git_diff_action.setEnabled(dirty)
        self._git_stage_action.setEnabled(dirty)
        self._git_commit_action.setEnabled(staged or dirty)

    def refresh_git_status(self) -> None:
        if not self._plugin_enabled("git_integration"):
            return
        self._refresh_git_status()
        status = self._git_status
        if status is None:
            self.statusBar().showMessage("No Git repository found.", 3000)
        elif status.error:
            self.statusBar().showMessage(status.error, 3500)
        else:
            self.statusBar().showMessage("Git status refreshed", 1800)

    def _git_root_or_message(self) -> Path | None:
        if not self._plugin_enabled("git_integration"):
            return None
        root = git.find_repository(self._git_path())
        if root is None:
            self.statusBar().showMessage(
                "No Git repository found for this workspace.", 3000
            )
        return root

    def _show_git_result(
        self,
        title: str,
        root: Path,
        args: tuple[str, ...],
        result: subprocess.CompletedProcess[str] | None,
        empty_text: str,
    ) -> None:
        self._show_output()
        self._output.clear()
        self._output.feed(f"── {title} · {root} ──\n", "system")
        self._output.feed(f"\n$ git {' '.join(args)}\n", "cmd")
        if result is None:
            self._output.feed("Git is not installed.\n", "error")
            return
        text = ((result.stdout or "") + (result.stderr or "")).rstrip()
        if text:
            self._output.feed(
                text + "\n",
                "stdout" if result.returncode == 0 else "stderr",
            )
        else:
            self._output.feed(empty_text + "\n", "system")
        if result.returncode != 0:
            self._output.feed(
                f"[Git exited with code {result.returncode}]\n", "error"
            )

    def _show_git_command(
        self,
        title: str,
        root: Path,
        args: tuple[str, ...],
        empty_text: str,
    ) -> subprocess.CompletedProcess[str] | None:
        result = git.run_git(root, *args)
        self._show_git_result(title, root, args, result, empty_text)
        return result

    def _show_git_commands(
        self,
        title: str,
        root: Path,
        commands: tuple[tuple[tuple[str, ...], str], ...],
    ) -> None:
        self._show_output()
        self._output.clear()
        self._output.feed(f"── {title} · {root} ──\n", "system")
        for args, empty_text in commands:
            result = git.run_git(root, *args)
            self._output.feed(f"\n$ git {' '.join(args)}\n", "cmd")
            if result is None:
                self._output.feed("Git is not installed.\n", "error")
                return
            text = ((result.stdout or "") + (result.stderr or "")).rstrip()
            if text:
                self._output.feed(
                    text + "\n",
                    "stdout" if result.returncode == 0 else "stderr",
                )
            else:
                self._output.feed(empty_text + "\n", "system")
            if result.returncode != 0:
                self._output.feed(
                    f"[Git exited with code {result.returncode}]\n", "error"
                )

    def show_git_changes(self) -> None:
        root = self._git_root_or_message()
        if root is None:
            return
        self._show_git_commands(
            "Git Changes",
            root,
            (
                (("status", "--short", "--branch"), "Working tree clean."),
                (("diff", "--stat"), "No unstaged changes."),
                (("diff", "--cached", "--stat"), "No staged changes."),
            ),
        )

    def show_git_diff(self) -> None:
        root = self._git_root_or_message()
        if root is None:
            return
        self._show_git_commands(
            "Git Diff",
            root,
            (
                (("diff", "--no-color"), "No unstaged changes."),
                (("diff", "--cached", "--no-color"), "No staged changes."),
            ),
        )

    def show_git_log(self) -> None:
        root = self._git_root_or_message()
        if root is None:
            return
        self._show_git_command(
            "Git Log",
            root,
            ("log", "--oneline", "--decorate", "--graph", "-20"),
            "No commits yet.",
        )

    def stage_all_changes(self) -> None:
        root = self._git_root_or_message()
        if root is None:
            return
        result = self._show_git_command(
            "Stage All Changes",
            root,
            ("add", "-A"),
            "Changes staged.",
        )
        if result is not None and result.returncode == 0:
            self.statusBar().showMessage("Staged all changes", 2200)
        self._refresh_git_status()

    def commit_changes(self) -> None:
        root = self._git_root_or_message()
        if root is None:
            return

        message, accepted = QInputDialog.getMultiLineText(
            self, "Git Commit", "Commit message:", ""
        )
        if not accepted or not message.strip():
            return

        status = git.read_status(root)
        if status is not None and status.dirty and not status.staged:
            answer = QMessageBox.question(
                self,
                "Git Commit",
                "No changes are staged. Stage all changes and commit?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            add_result = git.run_git(root, "add", "-A")
            if add_result is None or add_result.returncode != 0:
                self._show_git_result(
                    "Git Stage",
                    root,
                    ("add", "-A"),
                    add_result,
                    "No changes to stage.",
                )
                self._refresh_git_status()
                return

        result = self._show_git_command(
            "Git Commit",
            root,
            ("commit", "-m", message.strip()),
            "Nothing to commit.",
        )
        if result is not None and result.returncode == 0:
            self.statusBar().showMessage("Commit created", 2500)
        self._refresh_git_status()

    def _on_plugin_toggled(self, key: str, enabled: bool) -> None:
        self._plugin_states[key] = bool(enabled)
        self._apply_plugin(key, bool(enabled))
        self._settings.setValue(
            "plugins_enabled",
            [name for name, active in self._plugin_states.items() if active],
        )
        spec = PLUGIN_BY_KEY.get(key)
        name = spec.name if spec is not None else key
        self.statusBar().showMessage(
            f"{name} {'enabled' if enabled else 'disabled'}", 2200
        )

    def show_plugins_tab(self) -> None:
        if self._plugins_page is None:
            self._plugins_page = PluginManagerPage(self._plugin_states, self)
            self._plugins_page.plugin_toggled.connect(self._on_plugin_toggled)
            index = self._tabs.addTab(
                self._plugins_page,
                icons.icon("plugins", theme.ACCENT, 14),
                "Plugins",
            )
            self._tabs.setTabToolTip(index, "Manage built-in plugins")
            self._tabs.tabBar().setTabButton(
                index, QTabBar.ButtonPosition.RightSide, None
            )
        self._active_tabs = self._tabs
        self._stack.setCurrentWidget(self._editor_split)
        self._tabs.setCurrentWidget(self._plugins_page)
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()

    def _auto_save_modified(self) -> None:
        for editor in self._iter_editors():
            if (
                editor.path is not None
                and editor.document().isModified()
            ):
                self.save_editor(editor)

    def _update_clock(self) -> None:
        self._status_clock.setText(QTime.currentTime().toString("HH:mm"))

    def _update_word_count(self) -> None:
        if not self._plugin_enabled("word_count"):
            return
        editor = self.current_editor()
        if editor is None:
            self._status_words.setText("0 words")
            return
        text = editor.toPlainText()
        words = len(text.split())
        self._status_words.setText(f"{words} words · {len(text)} chars")

    def _set_zen_mode(self, enabled: bool) -> None:
        if enabled:
            if self._zen_previous is None:
                self._zen_previous = (
                    not self._sidebar_card.isHidden(),
                    not self._output_card.isHidden(),
                )
            self._set_sidebar_visible(False)
            self._set_output_visible(False)
            return
        sidebar, output = self._zen_previous or (True, True)
        self._zen_previous = None
        self._set_sidebar_visible(sidebar)
        self._set_output_visible(output)

    def _format_text_for_save(self, text: str) -> str:
        if self._plugin_enabled("trim_trailing_whitespace"):
            text = "\n".join(line.rstrip() for line in text.split("\n"))
        if self._plugin_enabled("final_newline") and text and not text.endswith("\n"):
            text += "\n"
        return text

    # ------------------------------------------------------------------
    # Editor / tab management
    # ------------------------------------------------------------------
    def _create_editor_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabsClosable(True)
        tabs.setMovable(True)
        tabs.setDocumentMode(True)
        tabs.setElideMode(Qt.TextElideMode.ElideRight)
        tabs.setUsesScrollButtons(True)
        tabs.setIconSize(QSize(10, 10))
        tabs.tabCloseRequested.connect(
            lambda index, target=tabs: self.close_tab_at(index, target)
        )
        tabs.currentChanged.connect(
            lambda _index, target=tabs: self._on_tabs_changed(target)
        )
        return tabs

    def _all_editor_tabs(self) -> list[QTabWidget]:
        if not hasattr(self, "_tabs"):
            return []
        tabs = [self._tabs]
        if hasattr(self, "_tabs_secondary"):
            tabs.append(self._tabs_secondary)
        return tabs

    def _split_active(self) -> bool:
        return (
            hasattr(self, "_tabs_secondary")
            and not self._tabs_secondary.isHidden()
        )

    def _iter_editors(self):
        for tabs in self._all_editor_tabs():
            for index in range(tabs.count()):
                editor = tabs.widget(index)
                if isinstance(editor, CodeEditor):
                    yield editor

    def _tabs_for_editor(self, editor: CodeEditor) -> QTabWidget | None:
        for tabs in self._all_editor_tabs():
            if tabs.indexOf(editor) >= 0:
                return tabs
        return None

    def _active_editor_tabs(self) -> QTabWidget:
        if self._active_tabs is None:
            self._active_tabs = self._tabs
        return self._active_tabs

    def _on_tabs_changed(self, tabs: QTabWidget) -> None:
        self._active_tabs = tabs
        self._on_tab_changed(tabs.currentIndex())

    def _on_editor_focused(self, editor: CodeEditor) -> None:
        tabs = self._tabs_for_editor(editor)
        if tabs is None or tabs is self._active_editor_tabs():
            return
        self._active_tabs = tabs
        self._on_tab_changed(tabs.currentIndex())

    def _set_split_visible(self, visible: bool) -> None:
        if visible:
            if not self._split_active():
                self._tabs_secondary.setVisible(True)
                self._size_split_evenly()
            return
        self._tabs_secondary.setVisible(False)
        if self._active_tabs is self._tabs_secondary:
            self._active_tabs = self._tabs
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()

    def _size_split_evenly(self) -> None:
        if not self._split_active():
            return
        if self._editor_split.orientation() == Qt.Orientation.Horizontal:
            total = max(400, self._editor_split.width() or self.width())
        else:
            total = max(300, self._editor_split.height() or self.height())
        first = total // 2
        self._editor_split.setSizes([first, max(1, total - first)])

    def split_editor(self, orientation: Qt.Orientation) -> None:
        editor = self.current_editor()
        if editor is None:
            return

        if self._split_active():
            if self._editor_split.orientation() != orientation:
                self._editor_split.setOrientation(orientation)
                self._split_orientation = orientation
                self._size_split_evenly()
            self._active_tabs = (
                self._tabs
                if self._active_tabs is self._tabs_secondary
                else self._tabs_secondary
            )
            self._active_tabs.setFocus()
            self._on_tab_changed(self._active_tabs.currentIndex())
            return

        self._split_orientation = orientation
        self._editor_split.setOrientation(orientation)
        self._editor_split.setSizes([1, 1])
        self._tabs_secondary.setVisible(True)
        self._size_split_evenly()
        self._active_tabs = self._tabs_secondary

        copy = self._create_editor(
            editor.language,
            editor.path,
            editor.toPlainText(),
        )
        copy.title = editor.title
        self._add_editor(copy)
        if editor.document().isModified():
            copy.document().setModified(True)
        self.statusBar().showMessage("Editor split created", 1800)

    def close_split(self) -> bool:
        if not self._split_active():
            return True
        for index in range(self._tabs_secondary.count() - 1, -1, -1):
            if not self.close_tab_at(index, self._tabs_secondary):
                return False
        self._tabs_secondary.setVisible(False)
        self._active_tabs = self._tabs
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()
        return True

    def current_editor(self) -> CodeEditor | None:
        widget = self._active_editor_tabs().currentWidget()
        return widget if isinstance(widget, CodeEditor) else None

    def _editor_call(self, method: str) -> None:
        editor = self.current_editor()
        if editor is not None:
            getattr(editor, method)()

    def _create_editor(
        self,
        language: str,
        path: Path | None,
        text: str = "",
    ) -> CodeEditor:
        editor = CodeEditor(language)
        editor.path = path
        editor.set_font_size(self._font_size)
        editor.set_word_wrap(self._plugin_enabled("word_wrap"))
        editor.set_indent_guides_enabled(
            self._plugin_enabled("indent_guides")
        )
        editor.set_current_line_highlight(
            self._plugin_enabled("current_line")
        )
        editor.set_auto_close_brackets(
            self._plugin_enabled("auto_close_brackets")
        )
        if text:
            editor.setPlainText(text)
        editor.highlighter = create_highlighter(language, editor.document())
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(
            lambda modified, ed=editor: self._on_modified(ed, modified)
        )
        editor.cursorPositionChanged.connect(self._update_cursor_status)
        editor.font_size_changed.connect(self._on_editor_zoom)
        editor.focused.connect(lambda ed=editor: self._on_editor_focused(ed))
        return editor

    def _add_editor(self, editor: CodeEditor) -> None:
        tabs = self._active_editor_tabs()
        index = tabs.addTab(editor, editor.title)
        tabs.setTabToolTip(
            index, str(editor.path) if editor.path else "Unsaved file"
        )
        self._install_tab_close(index, editor, tabs)
        tabs.setCurrentIndex(index)
        if tabs is self._tabs_secondary and tabs.isHidden():
            tabs.setVisible(True)
            self._size_split_evenly()
        self._stack.setCurrentWidget(self._editor_split)
        self._update_tab_for(editor)
        editor.setFocus()
        self._update_editor_header()
        self._update_ui_state()

    def _install_tab_close(
        self,
        index: int,
        editor: CodeEditor,
        tabs: QTabWidget | None = None,
    ) -> None:
        target = tabs or self._active_editor_tabs()
        button = QPushButton()
        button.setObjectName("tabCloseButton")
        button.setFixedSize(18, 18)
        button.setIcon(icons.icon("close", theme.FG_DIM, 12))
        button.setIconSize(QSize(12, 12))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip("Close")
        button.clicked.connect(
            lambda _checked=False, target_editor=editor: self._close_editor(
                target_editor
            )
        )
        target.tabBar().setTabButton(
            index, QTabBar.ButtonPosition.RightSide, button
        )

    def _close_editor(self, editor: CodeEditor) -> None:
        tabs = self._tabs_for_editor(editor)
        if tabs is None:
            return
        index = tabs.indexOf(editor)
        if index >= 0:
            self.close_tab_at(index, tabs)

    def new_file(self, language: str = "python") -> None:
        lang = language_for_key(language)
        self._untitled_count += 1
        suffix = lang.extensions[0] if lang.extensions else ".txt"
        editor = self._create_editor(lang.key, None)
        editor.title = f"untitled-{self._untitled_count}{suffix}"
        self._add_editor(editor)

    def new_file_dialog(self) -> None:
        languages = display_languages() + [language_for_key("text")]
        names = [language.name for language in languages]
        name, accepted = QInputDialog.getItem(
            self, "New File", "Language:", names, 0, False
        )
        if not accepted:
            return
        try:
            language = languages[names.index(name)]
        except ValueError:
            return
        self.new_file(language.key)

    def open_file_dialog(self) -> None:
        start = str(self._default_directory())
        patterns: list[str] = []
        for language in display_languages():
            patterns.extend("*" + extension for extension in language.extensions)
        patterns.append("*.txt")
        filters = (
            f"Supported files ({' '.join(patterns)});;All files (*)"
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", start, filters
        )
        if path:
            self.open_file(Path(path))

    def open_file(self, path: Path) -> None:
        path = Path(path).expanduser().resolve()
        for tabs in self._all_editor_tabs():
            for index in range(tabs.count()):
                editor = tabs.widget(index)
                if isinstance(editor, CodeEditor) and editor.path == path:
                    tabs.setCurrentIndex(index)
                    self._active_tabs = tabs
                    self._stack.setCurrentWidget(self._editor_split)
                    self._on_tab_changed(index)
                    editor.setFocus()
                    return

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            QMessageBox.warning(
                self, "Open File", f"{path.name} is not a UTF-8 text file."
            )
            return
        except OSError as exc:
            QMessageBox.warning(self, "Open File", str(exc))
            return

        language = detect_language(path)
        editor = self._create_editor(language, path, text)
        editor.title = path.name
        self._add_editor(editor)
        self._add_recent(path)

    def _add_recent(self, path: Path) -> None:
        entry = str(path)
        if entry in self._recent:
            self._recent.remove(entry)
        self._recent.insert(0, entry)
        del self._recent[10:]
        self._settings.setValue("recent_files", self._recent)
        self._rebuild_recent_menu()
        self._welcome.set_recent(self._recent)

    def _rebuild_recent_menu(self) -> None:
        if not hasattr(self, "_recent_menu"):
            return
        self._recent_menu.clear()
        if not self._recent:
            empty = self._recent_menu.addAction("No recent files")
            empty.setEnabled(False)
            return
        for entry in self._recent:
            action = self._recent_menu.addAction(Path(entry).name)
            action.setToolTip(entry)
            action.triggered.connect(lambda _checked=False, p=entry: self._open_recent(p))
        self._recent_menu.addSeparator()
        clear = self._recent_menu.addAction("Clear Recent Files")
        clear.triggered.connect(self._clear_recent)

    def _open_recent(self, entry: str) -> None:
        path = Path(entry)
        if not path.is_file():
            QMessageBox.warning(
                self, "Recent Files", f"{path} no longer exists."
            )
            self._recent = [item for item in self._recent if item != entry]
            self._settings.setValue("recent_files", self._recent)
            self._rebuild_recent_menu()
            self._welcome.set_recent(self._recent)
            return
        self.open_file(path)

    def _clear_recent(self) -> None:
        self._recent = []
        self._settings.setValue("recent_files", self._recent)
        self._rebuild_recent_menu()
        self._welcome.set_recent(self._recent)

    def _on_modified(self, editor: CodeEditor, _modified: bool) -> None:
        self._update_tab_for(editor)
        if editor is self.current_editor():
            self._update_window_title()

    def _update_tab_for(self, editor: CodeEditor) -> None:
        tabs = self._tabs_for_editor(editor)
        if tabs is None:
            return
        index = tabs.indexOf(editor)
        if index < 0:
            return
        name = editor.path.name if editor.path else editor.title
        prefix = "* " if editor.document().isModified() else ""
        language = language_for_key(editor.language)
        tabs.setTabText(index, prefix + name)
        tabs.setTabIcon(index, icons.dot_icon(language.color, 9))
        tabs.setTabToolTip(
            index, str(editor.path) if editor.path else "Unsaved file"
        )

    def _update_window_title(self) -> None:
        editor = self.current_editor()
        if editor is None:
            self.setWindowTitle(APP_NAME)
            return
        name = editor.path.name if editor.path else editor.title
        prefix = "*" if editor.document().isModified() else ""
        self.setWindowTitle(f"{prefix}{name} — {APP_NAME}")

    def _update_editor_header(self) -> None:
        editor = self.current_editor()
        if editor is None:
            self._path_label.setText("No file open")
            self._path_label.setToolTip("")
            self._language_dot.setVisible(False)
            self._language_pill.setVisible(False)
            return

        language = language_for_key(editor.language)
        if editor.path is None:
            path_text = editor.title
            tooltip = "Unsaved file"
        else:
            tooltip = str(editor.path)
            if self._folder is not None:
                try:
                    relative = editor.path.relative_to(self._folder)
                except ValueError:
                    path_text = str(editor.path)
                else:
                    path_text = "  ›  ".join([self._folder.name, *relative.parts])
            else:
                path_text = str(editor.path)

        self._path_label.setText(path_text)
        self._path_label.setToolTip(tooltip)

        self._language_dot.setVisible(True)
        self._language_dot.setStyleSheet(
            f"background: {language.color}; border-radius: 4px;"
        )
        self._language_pill.setVisible(True)
        self._language_pill.setText(language.name)
        self._language_pill.setStyleSheet(
            f"color: {language.color};"
            f" background: {_rgba(language.color, 0.13)};"
            f" border: 1px solid {_rgba(language.color, 0.35)};"
            " border-radius: 8px; padding: 2px 9px;"
            " font-size: 10px; font-weight: 700;"
        )

    def _on_tab_changed(self, _index: int) -> None:
        self._update_window_title()
        self._update_editor_header()
        self._update_cursor_status()
        self._update_ui_state()
        self._refresh_git_status()
        if self._find_bar.isVisible():
            self._on_search_changed(
                self._find_bar.text(), self._find_bar.case_sensitive()
            )

    def close_tab_at(
        self,
        index: int,
        tabs: QTabWidget | None = None,
    ) -> bool:
        target = tabs or self._active_editor_tabs()
        editor = target.widget(index)
        if not isinstance(editor, CodeEditor):
            return False
        if not self._maybe_save(editor):
            return False
        target.removeTab(index)
        editor.deleteLater()
        if target is self._tabs_secondary and target.count() == 0:
            target.setVisible(False)
            self._active_tabs = self._tabs
        elif (
            target is self._tabs
            and target.count() == 0
            and self._split_active()
            and self._tabs_secondary.count() > 0
        ):
            self._active_tabs = self._tabs_secondary
        if self._tabs.count() == 0 and self._tabs_secondary.count() == 0:
            self._stack.setCurrentWidget(self._welcome)
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()
        return True

    def close_current_tab(self) -> None:
        tabs = self._active_editor_tabs()
        if tabs.count():
            self.close_tab_at(tabs.currentIndex(), tabs)

    def _on_file_renamed(self, old: Path, new: Path) -> None:
        for editor in self._iter_editors():
            if editor.path is None:
                continue
            if editor.path == old:
                editor.path = new
            elif old in editor.path.parents:
                editor.path = new / editor.path.relative_to(old)
            else:
                continue
            language = detect_language(editor.path)
            if language != editor.language:
                editor.set_language(language)
            self._update_tab_for(editor)
        self._update_editor_header()
        self._update_window_title()
        self._refresh_git_status()

    def _on_file_deleted(self, path: Path) -> None:
        for tabs in self._all_editor_tabs():
            for index in reversed(range(tabs.count())):
                editor = tabs.widget(index)
                if not isinstance(editor, CodeEditor) or editor.path is None:
                    continue
                if editor.path == path or path in editor.path.parents:
                    editor.document().setModified(False)
                    tabs.removeTab(index)
                    editor.deleteLater()
            if tabs is self._tabs_secondary and tabs.count() == 0:
                tabs.setVisible(False)
        if self._tabs.count() == 0 and self._tabs_secondary.count() == 0:
            self._stack.setCurrentWidget(self._welcome)
        if self._active_tabs is self._tabs_secondary and not self._split_active():
            self._active_tabs = self._tabs
        elif (
            self._active_tabs is self._tabs
            and self._tabs.count() == 0
            and self._split_active()
            and self._tabs_secondary.count() > 0
        ):
            self._active_tabs = self._tabs_secondary
        self._update_editor_header()
        self._update_ui_state()
        self._update_window_title()
        self._refresh_git_status()

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def _default_directory(self) -> Path:
        editor = self.current_editor()
        if editor is not None and editor.path is not None:
            return editor.path.parent
        if self._folder is not None:
            return self._folder
        return Path.home()

    def save_current(self) -> bool:
        editor = self.current_editor()
        if editor is None:
            return False
        return self.save_editor(editor)

    def save_current_as(self) -> bool:
        editor = self.current_editor()
        if editor is None:
            return False
        return self.save_editor_as(editor)

    def save_editor(self, editor: CodeEditor) -> bool:
        if editor.path is None:
            return self.save_editor_as(editor)
        return self._write_file(editor, editor.path)

    def save_editor_as(self, editor: CodeEditor) -> bool:
        if editor.path is not None:
            suggested = editor.path
        else:
            suggested = self._default_directory() / (editor.title or "untitled.py")
        language = language_for_key(editor.language)
        patterns = " ".join(f"*{extension}" for extension in language.extensions) or "*"
        filters = f"{language.name} files ({patterns});;All files (*)"
        path_string, _ = QFileDialog.getSaveFileName(
            self, "Save As", str(suggested), filters
        )
        if not path_string:
            return False
        return self._write_file(editor, Path(path_string))

    def _write_file(self, editor: CodeEditor, path: Path) -> bool:
        text = self._format_text_for_save(editor.toPlainText())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Save File", str(exc))
            return False

        if text != editor.toPlainText():
            position = editor.textCursor().position()
            scroll = editor.verticalScrollBar().value()
            editor.setPlainText(text)
            cursor = editor.textCursor()
            cursor.setPosition(min(position, len(text)))
            editor.setTextCursor(cursor)
            editor.verticalScrollBar().setValue(scroll)

        editor.path = path
        language = detect_language(path)
        if language != editor.language:
            editor.set_language(language)
        editor.document().setModified(False)
        self._update_tab_for(editor)
        self._update_editor_header()
        self._update_window_title()
        self._update_cursor_status()
        self._update_ui_state()
        self.statusBar().showMessage(f"Saved {path.name}", 2500)
        self._add_recent(path)
        self._refresh_git_status()

        if self._folder is not None and not path.is_relative_to(self._folder):
            self.set_folder(path.parent)
        return True

    def save_all(self) -> bool:
        for editor in self._iter_editors():
            if not self.save_editor(editor):
                return False
        return True

    def _maybe_save(self, editor: CodeEditor) -> bool:
        if not editor.document().isModified():
            return True
        name = editor.path.name if editor.path else editor.title
        answer = QMessageBox.question(
            self,
            "Unsaved Changes",
            f"Save changes to “{name}” before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.save_editor(editor)
        return True

    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().showEvent(event)
        if self._transparency_enabled:
            QTimer.singleShot(0, self._sync_transparency_after_show)
            QTimer.singleShot(250, self._sync_transparency_after_show)

    def _sync_transparency_after_show(self) -> None:
        if not self.isVisible():
            return
        self._apply_transparency(
            self._transparency_enabled, self._transparency_opacity
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt API)
        if self._closing:
            event.accept()
            return
        if not self.save_all():
            event.ignore()
            return

        self._closing = True
        self._runner.stop()
        self._terminal.stop()
        self._live_server.stop()
        self._save_settings()
        event.accept()

    # ------------------------------------------------------------------
    # Folder handling
    # ------------------------------------------------------------------
    def set_folder(self, folder: Path) -> None:
        folder = Path(folder).expanduser().resolve()
        if not folder.is_dir():
            return
        if self._live_server.running and self._live_server.root != folder:
            self._live_server.stop()
            self._update_live_status()
            self.statusBar().showMessage(
                "Live Server stopped because the workspace changed", 3000
            )
        self._folder = folder
        self._explorer.set_root(folder)
        self._terminal.set_working_directory(folder)
        self._settings.setValue("last_folder", str(folder))
        if hasattr(self, "_path_label"):
            self._update_editor_header()
        self._refresh_git_status()

    def open_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Open Folder", str(self._default_directory())
        )
        if folder:
            self.set_folder(Path(folder))

    # ------------------------------------------------------------------
    # Running / building
    # ------------------------------------------------------------------
    def _prepare_for_run(self, editor: CodeEditor) -> bool:
        if editor.path is None or editor.document().isModified():
            return self.save_editor(editor)
        return True

    def _show_output(self) -> None:
        self._set_output_visible(True)
        self._bottom_tabs.setCurrentWidget(self._output)

    def _live_root(self) -> Path:
        if self._folder is not None:
            return self._folder
        editor = self.current_editor()
        if editor is not None and editor.path is not None:
            return editor.path.parent
        return Path.cwd()

    def _live_target(self) -> str:
        if not self._live_server.running:
            return ""
        root = self._live_server.root or self._live_root()
        editor = self.current_editor()
        if (
            editor is not None
            and editor.path is not None
            and editor.language == "html"
        ):
            try:
                editor.path.relative_to(root)
            except ValueError:
                pass
            else:
                return self._live_server.url_for(editor.path)
        if editor is not None and editor.path is not None:
            for name in ("index.html", "index.htm"):
                sibling = editor.path.parent / name
                if sibling.is_file():
                    return self._live_server.url_for(sibling)
        for name in ("index.html", "index.htm"):
            candidate = root / name
            if candidate.is_file():
                return self._live_server.url_for(candidate)
        return self._live_server.url_for()

    def _update_live_status(self) -> None:
        running = self._live_server.running
        self._status_live.setVisible(running)
        if running:
            self._status_live.setText(f"LIVE :{self._live_server.port}")
            self._status_live.setStyleSheet(
                f"color: {theme.GREEN}; font-weight: 700;"
            )
            self._status_live.setToolTip(self._live_server.url)
        self._live_start_action.setEnabled(not running)
        self._live_preview_action.setEnabled(running)
        self._live_stop_action.setEnabled(running)

    def start_live_server(self) -> None:
        if self._live_server.running:
            self.open_live_preview()
            return
        root = self._live_root()
        try:
            url = self._live_server.start(root)
        except OSError as exc:
            QMessageBox.warning(self, "Live Server", str(exc))
            return

        self._show_output()
        self._output.feed(f"── Live Server · {root} ──\n", "system")
        self._output.feed(f"Local: {url}\n", "success")
        self._output.feed(
            "Auto-reload is enabled. Save a file to refresh the browser.\n",
            "system",
        )
        self._update_live_status()
        target = self._live_target()
        QDesktopServices.openUrl(QUrl(target or url))
        self.statusBar().showMessage(f"Live Server running at {url}", 3500)

    def open_live_preview(self) -> None:
        if not self._live_server.running:
            self.start_live_server()
            return
        target = self._live_target() or self._live_server.url
        QDesktopServices.openUrl(QUrl(target))
        self.statusBar().showMessage(f"Opened {target}", 2500)

    def stop_live_server(self) -> None:
        if not self._live_server.running:
            return
        self._live_server.stop()
        self._update_live_status()
        if hasattr(self, "_output"):
            self._show_output()
            self._output.feed("Live Server stopped.\n", "system")
        self.statusBar().showMessage("Live Server stopped", 2500)

    def show_terminal(self) -> None:
        self._set_output_visible(True)
        self._bottom_tabs.setCurrentWidget(self._terminal)
        self._terminal.focus_input()

    def _on_bottom_tab_changed(self, _index: int) -> None:
        if self._bottom_tabs.currentWidget() is self._terminal:
            self._terminal.ensure_started()
            self._terminal.focus_input()

    def run_current(self) -> None:
        editor = self.current_editor()
        if editor is None:
            return
        language = language_for_key(editor.language)
        if editor.language in WEB_PREVIEW_LANGUAGES:
            if not self._prepare_for_run(editor):
                return
            self.start_live_server()
            return
        if language.runner is None:
            QMessageBox.information(
                self,
                "Run",
                f"{language.name} files are highlighted but cannot be run "
                "by CodeForge.",
            )
            return
        if not self._prepare_for_run(editor):
            return

        self._show_output()
        self._output.clear()
        self._output.feed(
            f"── Run {editor.path.name} · {language.name} ──\n", "system"
        )
        self._runner.run(language, editor.path)

    def build_current(self) -> None:
        editor = self.current_editor()
        if editor is None:
            return
        language = language_for_key(editor.language)
        if not language.compiled:
            QMessageBox.information(
                self, "Build", f"{language.name} is interpreted — press Run instead."
            )
            return
        if not self._prepare_for_run(editor):
            return

        self._show_output()
        self._output.clear()
        self._output.feed(
            f"── Build {editor.path.name} · {language.name} ──\n", "system"
        )
        self._runner.run(language, editor.path, compile_only=True)

    def stop_current(self) -> None:
        self._runner.stop()

    def _send_input(self, text: str) -> None:
        self._runner.send_input(text + "\n")

    def _set_run_status(self, text: str, kind: str) -> None:
        self._run_text = text
        self._run_kind = kind
        colors = {
            "ready": theme.FG_MUTED,
            "running": theme.GREEN,
            "done": theme.GREEN,
            "error": theme.RED,
            "build": theme.YELLOW,
        }
        color = colors.get(kind, theme.FG_MUTED)
        self._status_run.setText(text)
        self._status_run.setStyleSheet(f"color: {color};")
        if hasattr(self, "_output"):
            self._output.set_status(text, kind)

    def _on_runner_state(self, running: bool) -> None:
        self._output.set_running(running)
        self._set_run_status(
            "RUNNING" if running else "READY",
            "running" if running else "ready",
        )
        self._update_ui_state()

    def _on_runner_finished(self, code: int, message: str) -> None:
        elapsed = self._runner.last_elapsed
        kind = "success" if code == 0 else "error"
        if elapsed >= 1.0:
            timing = f"{elapsed:.2f} s"
        else:
            timing = f"{elapsed * 1000:.0f} ms"
        self._output.feed(f"\n[{message} · {timing}]\n", kind)
        if code == 0:
            label = f"DONE · {timing}"
            status_kind = "done"
        elif code == 130:
            label = "STOPPED"
            status_kind = "error"
        else:
            label = f"EXIT {code}"
            status_kind = "error"
        self._set_run_status(label, status_kind)
        self._update_ui_state()

    def _output_clear(self) -> None:
        self._output.clear()

    # ------------------------------------------------------------------
    # Command palette
    # ------------------------------------------------------------------
    def show_command_palette(self) -> None:
        actions = self.findChildren(QAction)
        palette = CommandPalette(actions, self)
        if palette.exec() == QDialog.DialogCode.Accepted:
            action = palette.selected_action()
            if action is not None:
                QTimer.singleShot(0, action.trigger)
        palette.deleteLater()

    # ------------------------------------------------------------------
    # Find / replace
    # ------------------------------------------------------------------
    def show_find(self) -> None:
        self._find_bar.set_replace_visible(False)
        self._find_bar.setVisible(True)
        self._find_bar.focus_find()
        self._on_search_changed(
            self._find_bar.text(), self._find_bar.case_sensitive()
        )

    def show_replace(self) -> None:
        self._find_bar.set_replace_visible(True)
        self._find_bar.setVisible(True)
        self._find_bar.focus_find()
        self._on_search_changed(
            self._find_bar.text(), self._find_bar.case_sensitive()
        )

    def _close_find(self) -> None:
        if not self._find_bar.isVisible():
            return
        self._find_bar.setVisible(False)
        for editor in self._iter_editors():
            editor.clear_search()
        editor = self.current_editor()
        if editor is not None:
            editor.setFocus()

    def _on_search_changed(self, text: str, case_sensitive: bool) -> None:
        editor = self.current_editor()
        if editor is None:
            return
        editor.highlight_matches(text, case_sensitive)

    def find_next(self) -> None:
        editor = self.current_editor()
        if editor is None:
            return
        text = self._find_bar.text()
        if not text:
            return
        editor.highlight_matches(text, self._find_bar.case_sensitive())
        if not editor.find_text(text, self._find_bar.case_sensitive()):
            self.statusBar().showMessage("No matches", 2000)

    def find_previous(self) -> None:
        editor = self.current_editor()
        if editor is None:
            return
        text = self._find_bar.text()
        if not text:
            return
        editor.highlight_matches(text, self._find_bar.case_sensitive())
        if not editor.find_text(
            text, self._find_bar.case_sensitive(), backwards=True
        ):
            self.statusBar().showMessage("No matches", 2000)

    def _replace_one(self, find: str, replace: str, case_sensitive: bool) -> None:
        editor = self.current_editor()
        if editor is None or not find:
            return
        editor.replace_next(find, replace, case_sensitive)
        editor.highlight_matches(find, case_sensitive)

    def _replace_all_matches(
        self, find: str, replace: str, case_sensitive: bool
    ) -> None:
        editor = self.current_editor()
        if editor is None or not find:
            return
        count = editor.replace_all(find, replace, case_sensitive)
        editor.highlight_matches(find, case_sensitive)
        self.statusBar().showMessage(f"Replaced {count} occurrence(s)", 3000)

    # ------------------------------------------------------------------
    # Zoom, sidebar, status
    # ------------------------------------------------------------------
    def set_font_size(self, size: int) -> None:
        size = max(8, min(36, int(size)))
        self._font_size = size
        for editor in self._iter_editors():
            editor.set_font_size(size)

    def _on_editor_zoom(self, size: int) -> None:
        self._font_size = size
        for editor in self._iter_editors():
            if editor.font_size != size:
                editor.set_font_size(size)

    def _set_sidebar_visible(self, visible: bool) -> None:
        visible = bool(visible)
        self._sidebar_card.setVisible(visible)
        if self._toggle_sidebar_action.isChecked() != visible:
            self._toggle_sidebar_action.blockSignals(True)
            self._toggle_sidebar_action.setChecked(visible)
            self._toggle_sidebar_action.blockSignals(False)
        if self._sidebar_button.isChecked() != visible:
            self._sidebar_button.blockSignals(True)
            self._sidebar_button.setChecked(visible)
            self._sidebar_button.blockSignals(False)
        self._update_sidebar_button()

    def _set_output_visible(self, visible: bool) -> None:
        visible = bool(visible)
        self._output_card.setVisible(visible)
        if self._toggle_output_action.isChecked() != visible:
            self._toggle_output_action.blockSignals(True)
            self._toggle_output_action.setChecked(visible)
            self._toggle_output_action.blockSignals(False)

    def _update_cursor_status(self) -> None:
        editor = self.current_editor()
        if editor is None:
            self._status_position.setText("Ln 1, Col 1")
            self._status_language.setText("Plain Text")
            self._status_dot.setStyleSheet(
                f"background: {theme.FG_DIM}; border-radius: 4px;"
            )
            return
        language = language_for_key(editor.language)
        cursor = editor.textCursor()
        self._status_position.setText(
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.positionInBlock() + 1}"
        )
        self._status_language.setText(language.name)
        self._status_dot.setStyleSheet(
            f"background: {language.color}; border-radius: 4px;"
        )
        self._update_word_count()

    def _update_ui_state(self) -> None:
        editor = self.current_editor()
        has_editor = editor is not None
        running = self._runner.is_running()
        language = language_for_key(editor.language) if editor is not None else None

        for action in (
            self._save_action,
            self._save_as_action,
            self._close_tab_action,
            self._undo_action,
            self._redo_action,
            self._cut_action,
            self._copy_action,
            self._paste_action,
            self._select_all_action,
            self._find_action,
            self._replace_action,
            self._find_next_action,
            self._find_previous_action,
        ):
            action.setEnabled(has_editor)
        self._comment_action.setEnabled(
            has_editor and bool(language.comment) if language else False
        )

        self._save_all_action.setEnabled(any(True for _ in self._iter_editors()))
        can_preview = bool(
            language is not None
            and language.key in WEB_PREVIEW_LANGUAGES
        )
        self._run_action.setEnabled(
            has_editor and language is not None
            and (language.runner is not None or can_preview)
            and not running
        )
        self._stop_action.setEnabled(running)
        self._build_action.setEnabled(
            has_editor and language is not None
            and language.compiled and not running
        )
        self._run_button.setEnabled(self._run_action.isEnabled())
        self._stop_button.setEnabled(running)
        self._build_button.setEnabled(self._build_action.isEnabled())
        self._split_right_action.setEnabled(has_editor)
        self._split_down_action.setEnabled(has_editor)
        self._close_split_action.setEnabled(self._split_active())
        self._update_live_status()
        if language is not None:
            self._build_button.setToolTip(f"Build {language.name} (Ctrl+Shift+B)")
        if can_preview:
            self._run_action.setToolTip("Preview in Live Server (F5)")
            self._run_button.setToolTip("Preview in Live Server (F5)")
            self._run_button.setText("Preview")
        else:
            self._run_action.setToolTip("Run the current file (F5)")
            self._run_button.setToolTip("Run current file (F5)")
            self._run_button.setText("Run")
        self._sidebar_button.setChecked(not self._sidebar_card.isHidden())
        self._update_sidebar_button()
        self._update_cursor_status()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME} {__version__}</h3>"
            "<p>A refined multi-language IDE built with PySide6.</p>"
            "<p>Compiled languages are built into a local "
            "<code>build/</code> folder. Interpreted languages run with "
            "their native toolchain.</p>",
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt API)
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_dir():
                self.set_folder(path)
            elif path.is_file():
                self.set_folder(path.parent)
                self.open_file(path)
        event.acceptProposedAction()
