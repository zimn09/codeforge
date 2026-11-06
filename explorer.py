"""Project file explorer with a small file-management context menu."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QDir, QFileInfo, QModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileIconProvider,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from . import icons, theme
from .languages import language_for_path


class LanguageIconProvider(QFileIconProvider):
    """Small painted badges for known source files."""

    def __init__(self):
        super().__init__()
        self._cache: dict[str, QIcon] = {}

    def icon(self, info):  # noqa: N802 (Qt API)
        if isinstance(info, QFileInfo) and info.isFile():
            language = language_for_path(Path(info.filePath()))
            if language.key != "text":
                if language.key not in self._cache:
                    self._cache[language.key] = icons.file_badge(language.color)
                return self._cache[language.key]
        return super().icon(info)


class Explorer(QWidget):
    file_activated = Signal(object)       # Path
    file_renamed = Signal(object, object)  # old Path, new Path
    file_deleted = Signal(object)          # Path

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._root: Path | None = None

        header = QHBoxLayout()
        header.setContentsMargins(14, 12, 10, 2)
        header.setSpacing(4)

        title = QLabel("EXPLORER")
        title.setObjectName("panelHeader")
        self.folder_label = QLabel("no folder")
        self.folder_label.setObjectName("folderName")

        self.new_button = QPushButton()
        self.new_button.setObjectName("iconButton")
        self.new_button.setFixedSize(24, 24)
        self.new_button.setIconSize(QSize(15, 15))
        self.new_button.setToolTip("New file")
        self.new_button.clicked.connect(lambda: self._new_file(self._root))

        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("iconButton")
        self.refresh_button.setFixedSize(24, 24)
        self.refresh_button.setIconSize(QSize(15, 15))
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.clicked.connect(self.refresh)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.new_button)
        header.addWidget(self.refresh_button)

        self.model = QFileSystemModel(self)
        self.model.setFilter(
            QDir.Filter.AllEntries
            | QDir.Filter.NoDotAndDotDot
            | QDir.Filter.AllDirs
        )
        self.model.setReadOnly(False)
        self._icon_provider = LanguageIconProvider()
        self.model.setIconProvider(self._icon_provider)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setSortingEnabled(False)
        self.tree.setIconSize(QSize(16, 16))
        for column in (1, 2, 3):
            self.tree.hideColumn(column)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(self.folder_label)
        layout.addSpacing(6)
        layout.addWidget(self.tree, 1)

        self.folder_label.setContentsMargins(14, 0, 12, 0)

        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.customContextMenuRequested.connect(self._show_menu)

        self.refresh_theme()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def refresh_theme(self) -> None:
        self.new_button.setIcon(icons.icon("plus", theme.FG_MUTED, 15))
        self.refresh_button.setIcon(icons.icon("refresh", theme.FG_MUTED, 15))
        self._icon_provider = LanguageIconProvider()
        self.model.setIconProvider(self._icon_provider)

    def refresh(self) -> None:
        if self._root is None:
            return
        index = self.model.setRootPath(str(self._root))
        self.tree.setRootIndex(index)
        self.tree.expand(index)

    # ------------------------------------------------------------------
    # Folder handling
    # ------------------------------------------------------------------
    def set_root(self, folder: Path) -> None:
        folder = Path(folder).expanduser().resolve()
        if not folder.is_dir():
            return
        self._root = folder
        self.folder_label.setText(folder.name or str(folder))
        self.folder_label.setToolTip(str(folder))
        index = self.model.setRootPath(str(folder))
        self.tree.setRootIndex(index)
        self.tree.expand(index)

    def root(self) -> Path | None:
        return self._root

    def _path_for(self, index: QModelIndex) -> Path | None:
        if not index.isValid():
            return self._root
        return Path(self.model.filePath(index))

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------
    def _on_double_click(self, index: QModelIndex) -> None:
        path = self._path_for(index)
        if path is not None and path.is_file():
            self.file_activated.emit(path)

    def _base_directory(self) -> Path:
        index = self.tree.currentIndex()
        path = self._path_for(index)
        if path is None:
            return self._root or Path.home()
        return path if path.is_dir() else path.parent

    def _show_menu(self, position) -> None:
        index = self.tree.indexAt(position)
        path = self._path_for(index)
        menu = QMenu(self)

        if path is not None and path.is_file():
            open_action = menu.addAction("Open")
            open_action.triggered.connect(lambda: self.file_activated.emit(path))
            menu.addSeparator()

        base = path if path is not None and path.is_dir() else None
        if base is None and path is not None:
            base = path.parent
        if base is None:
            base = self._root

        new_file = menu.addAction("New File…")
        new_file.triggered.connect(lambda: self._new_file(base))
        new_folder = menu.addAction("New Folder…")
        new_folder.triggered.connect(lambda: self._new_folder(base))

        if path is not None and self._root is not None and path != self._root:
            menu.addSeparator()
            rename = menu.addAction("Rename…")
            rename.triggered.connect(lambda: self._rename(path))
            delete = menu.addAction("Delete")
            delete.triggered.connect(lambda: self._delete(path))

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _new_file(self, base: Path | None = None) -> None:
        base = base or self._base_directory()
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if not ok or not name.strip():
            return
        target = self._safe_target(base, name.strip())
        if target is None:
            return
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch(exist_ok=False)
        except FileExistsError:
            QMessageBox.warning(self, "New File", f"{target.name} already exists.")
            return
        except OSError as exc:
            QMessageBox.warning(self, "New File", str(exc))
            return
        self.file_activated.emit(target)

    def _new_folder(self, base: Path | None = None) -> None:
        base = base or self._base_directory()
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        target = self._safe_target(base, name.strip())
        if target is None:
            return
        try:
            target.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            QMessageBox.warning(self, "New Folder", f"{target.name} already exists.")
            return
        except OSError as exc:
            QMessageBox.warning(self, "New Folder", str(exc))

    def _rename(self, path: Path) -> None:
        name, ok = QInputDialog.getText(
            self, "Rename", "New name:", text=path.name
        )
        if not ok or not name.strip() or name.strip() == path.name:
            return
        target = self._safe_target(path.parent, name.strip())
        if target is None:
            return
        try:
            path.rename(target)
        except OSError as exc:
            QMessageBox.warning(self, "Rename", str(exc))
            return
        self.file_renamed.emit(path, target)

    def _delete(self, path: Path) -> None:
        answer = QMessageBox.question(
            self,
            "Delete",
            f"Delete “{path.name}”?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            QMessageBox.warning(self, "Delete", str(exc))
            return
        self.file_deleted.emit(path)

    def _safe_target(self, base: Path, name: str) -> Path | None:
        root = self._root or base
        target = (base / name).expanduser()
        try:
            resolved = target.resolve()
        except OSError:
            resolved = target.absolute()
        if not resolved.is_relative_to(root.resolve()):
            QMessageBox.warning(
                self,
                "Invalid path",
                "The new path must stay inside the opened folder.",
            )
            return None
        return resolved
