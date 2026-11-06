"""Inline find / replace bar."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

class FindBar(QWidget):
    search_changed = Signal(str, bool)      # text, case sensitive
    find_next = Signal()
    find_previous = Signal()
    replace_one = Signal(str, str, bool)    # find, replace, case
    replace_all = Signal(str, str, bool)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("findBar")

        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Find")
        self.find_edit.setClearButtonEnabled(True)

        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replace with")

        self.case_box = QCheckBox("Aa")
        self.case_box.setToolTip("Match case")

        self.previous_button = QPushButton("↑")
        self.previous_button.setObjectName("chip")
        self.previous_button.setToolTip("Previous match (Shift+F3)")

        self.next_button = QPushButton("↓")
        self.next_button.setObjectName("chip")
        self.next_button.setToolTip("Next match (F3)")

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("chip")
        self.close_button.setToolTip("Close (Esc)")

        self.replace_button = QPushButton("Replace")
        self.replace_button.setObjectName("chip")

        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.setObjectName("chip")

        layout = QGridLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)

        layout.addWidget(self.find_edit, 0, 0, 1, 2)
        layout.addWidget(self.case_box, 0, 2)
        layout.addWidget(self.previous_button, 0, 3)
        layout.addWidget(self.next_button, 0, 4)
        layout.addWidget(self.close_button, 0, 5)

        layout.addWidget(self.replace_edit, 1, 0, 1, 2)
        layout.addWidget(self.replace_button, 1, 2)
        layout.addWidget(self.replace_all_button, 1, 3, 1, 3)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self._replace_row: list[QWidget] = [
            self.replace_edit,
            self.replace_button,
            self.replace_all_button,
        ]

        self.find_edit.textChanged.connect(self._emit_search)
        self.case_box.toggled.connect(self._emit_search)
        self.find_edit.returnPressed.connect(lambda: self.find_next.emit())
        self.next_button.clicked.connect(lambda: self.find_next.emit())
        self.previous_button.clicked.connect(lambda: self.find_previous.emit())
        self.close_button.clicked.connect(lambda: self.closed.emit())
        self.replace_button.clicked.connect(self._emit_replace_one)
        self.replace_all_button.clicked.connect(self._emit_replace_all)

        self.set_replace_visible(False)

    # ------------------------------------------------------------------
    def text(self) -> str:
        return self.find_edit.text()

    def replacement(self) -> str:
        return self.replace_edit.text()

    def case_sensitive(self) -> bool:
        return self.case_box.isChecked()

    def set_replace_visible(self, visible: bool) -> None:
        for widget in self._replace_row:
            widget.setVisible(visible)

    def _emit_search(self, *_args) -> None:
        self.search_changed.emit(self.text(), self.case_sensitive())

    def _emit_replace_one(self) -> None:
        self.replace_one.emit(self.text(), self.replacement(), self.case_sensitive())

    def _emit_replace_all(self) -> None:
        self.replace_all.emit(self.text(), self.replacement(), self.case_sensitive())

    def focus_find(self) -> None:
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def focus_replace(self) -> None:
        self.replace_edit.setFocus()
        self.replace_edit.selectAll()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            event.accept()
            return
        super().keyPressEvent(event)
