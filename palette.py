"""A fast, keyboard-first command palette."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QAction, QColor, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CommandPalette(QDialog):
    """Popup search over the window's QActions."""

    def __init__(self, actions: list[QAction], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(680, 470)
        self._selected: QAction | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("paletteCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        self.search = QLineEdit()
        self.search.setObjectName("paletteSearch")
        self.search.setPlaceholderText("Search commands, files and themes…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._accept_current)
        self.search.installEventFilter(self)

        self.list = QListWidget()
        self.list.setObjectName("paletteList")
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.list.itemClicked.connect(self._accept_item)
        self.list.itemActivated.connect(self._accept_item)

        hint = QLabel("↑↓  Navigate      ↵  Run      Esc  Close")
        hint.setObjectName("paletteHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_label = QLabel("No matching commands")
        self.empty_label.setObjectName("hint")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setContentsMargins(0, 28, 0, 28)
        self.empty_label.setVisible(False)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.search)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.list, 1)
        layout.addWidget(hint)

        self._populate(actions)
        self._filter("")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def selected_action(self) -> QAction | None:
        return self._selected

    # ------------------------------------------------------------------
    # Population / filtering
    # ------------------------------------------------------------------
    def _populate(self, actions: list[QAction]) -> None:
        seen: set[tuple[str, str, str]] = set()
        for action in actions:
            if action.isSeparator() or action.menu() is not None:
                continue
            text = action.property("paletteText") or action.text()
            if not text:
                continue
            if not action.isEnabled():
                continue
            text = str(text).replace("&", "").replace("…", "")
            shortcut = action.shortcut().toString(
                QKeySequence.SequenceFormat.NativeText
            )
            key = (text, shortcut, action.toolTip())
            if key in seen:
                continue
            seen.add(key)

            item = QListWidgetItem()
            item.setText("")
            item.setData(Qt.ItemDataRole.UserRole + 2, text)
            item.setToolTip(action.toolTip() or action.statusTip() or text)
            item.setData(Qt.ItemDataRole.UserRole, action)
            item.setData(Qt.ItemDataRole.UserRole + 1, shortcut)

            widget = QWidget()
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row = QHBoxLayout(widget)
            row.setContentsMargins(8, 3, 8, 3)
            row.setSpacing(10)

            pixmap = action.icon().pixmap(QSize(16, 16))
            if not pixmap.isNull():
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                icon_label.setFixedWidth(18)
                row.addWidget(icon_label)

            label = QLabel(text)
            label.setObjectName("paletteName")
            row.addWidget(label, 1)

            if shortcut:
                chip = QLabel(shortcut)
                chip.setObjectName("shortcutChip")
                row.addWidget(chip)

            item.setSizeHint(QSize(0, 38))
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)

    def _filter(self, _text: str) -> None:
        query = self.search.text().strip().lower()
        parts = query.split()
        first: QListWidgetItem | None = None
        visible = 0

        for row in range(self.list.count()):
            item = self.list.item(row)
            shortcut = item.data(Qt.ItemDataRole.UserRole + 1) or ""
            name = item.data(Qt.ItemDataRole.UserRole + 2) or ""
            haystack = f"{name} {item.toolTip()} {shortcut}".lower()
            hidden = bool(parts) and not all(part in haystack for part in parts)
            item.setHidden(hidden)
            if not hidden:
                visible += 1
                if first is None:
                    first = item

        if first is not None:
            self.list.setCurrentItem(first)
        self.list.setVisible(visible > 0)
        self.empty_label.setVisible(visible == 0)

    def _visible_rows(self) -> list[int]:
        return [
            row
            for row in range(self.list.count())
            if not self.list.item(row).isHidden()
        ]

    def _move(self, delta: int) -> None:
        rows = self._visible_rows()
        if not rows:
            return
        current = self.list.currentRow()
        try:
            index = rows.index(current)
        except ValueError:
            index = 0
        index = max(0, min(len(rows) - 1, index + delta))
        self.list.setCurrentRow(rows[index])
        item = self.list.item(rows[index])
        if item is not None:
            self.list.scrollToItem(item)

    def _accept_current(self) -> None:
        item = self.list.currentItem()
        if item is None or item.isHidden():
            rows = self._visible_rows()
            if not rows:
                return
            item = self.list.item(rows[0])
        self._accept_item(item)

    def _accept_item(self, item: QListWidgetItem) -> None:
        action = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(action, QAction) and action.isEnabled():
            self._selected = action
            self.accept()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def eventFilter(self, watched, event) -> bool:  # noqa: N802 (Qt API)
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                self._move(1)
                return True
            if key == Qt.Key.Key_Up:
                self._move(-1)
                return True
            if key == Qt.Key.Key_PageDown:
                self._move(6)
                return True
            if key == Qt.Key.Key_PageUp:
                self._move(-6)
                return True
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(watched, event)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().showEvent(event)
        parent = self.parentWidget()
        if parent is not None:
            geometry = parent.window().frameGeometry()
            x = geometry.center().x() - self.width() // 2
            y = geometry.center().y() - self.height() // 2
            screen = QGuiApplication.screenAt(geometry.center())
            if screen is not None:
                area = screen.availableGeometry()
                x = max(area.left() + 8, min(x, area.right() - self.width() - 8))
                y = max(area.top() + 8, min(y, area.bottom() - self.height() - 8))
            self.move(x, y)
        self.search.setFocus()
        self.search.selectAll()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
