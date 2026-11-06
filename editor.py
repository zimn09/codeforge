"""Code editor widget with line numbers, auto-indent and find support."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QPlainTextEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .highlighter import create_highlighter
from .languages import language_for_key
from .libraries import (
    context_token,
    library_context_candidates,
    library_imported_symbols,
)

BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
CLOSING_BRACKETS = set(BRACKET_PAIRS.values())
QUOTE_PAIRS = {"'": "'", '"': '"'}
HTML_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
STRING_PREFIXES = {
    "r",
    "u",
    "b",
    "f",
    "br",
    "rb",
    "fr",
    "rf",
    "ur",
    "ru",
    "l",
    "u8",
}
TAB_WIDTH = 4


class LineNumberArea(QWidget):
    """Gutter widget owned by :class:`CodeEditor`."""

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt API)
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._editor.paint_line_numbers(event)


class KeywordSuggestionList(QListWidget):
    """Hint list that keeps wheel events at its own top and bottom edges."""

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt API)
        scrollbar = self.verticalScrollBar()
        delta = event.angleDelta().y()
        if not delta:
            delta = event.pixelDelta().y()
        at_top = scrollbar.value() <= scrollbar.minimum()
        at_bottom = scrollbar.value() >= scrollbar.maximum()
        if (delta > 0 and at_top) or (delta < 0 and at_bottom):
            event.accept()
            return
        super().wheelEvent(event)


class CodeEditor(QPlainTextEdit):
    font_size_changed = Signal(int)
    focused = Signal()

    def __init__(self, language: str = "python", parent: QWidget | None = None):
        super().__init__(parent)
        self.language = language
        self.path: Path | None = None
        self.title = "untitled"
        self.highlighter = None

        self._font_size = 12
        self._search_selections: list[QTextEdit.ExtraSelection] = []
        self._gutter = LineNumberArea(self)
        self._keyword_suggestions: list[str] = []
        self._keyword_suggestion_index: int = -1
        self._keyword_suggestion_popup: QFrame | None = None
        self._keyword_suggestion_list: QListWidget | None = None
        self._keyword_suggestion_visible: bool = False
        self._keyword_suggestion_token: str = ""
        self._indent_guides_enabled = True
        self._current_line_highlight = True
        self._auto_close_brackets = True

        self.setObjectName("codeEditor")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCenterOnScroll(True)
        self.setCursorWidth(2)
        self.set_font_size(self._font_size)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._update_extra_selections)
        self._update_line_number_area_width(0)
        self._update_extra_selections()

    # ------------------------------------------------------------------
    # Fonts, gutter geometry
    # ------------------------------------------------------------------
    @property
    def font_size(self) -> int:
        return self._font_size

    def set_font_size(self, size: int) -> None:
        self._font_size = max(8, min(36, int(size)))
        font = theme.monospace_font(self._font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * TAB_WIDTH)
        self._update_line_number_area_width(0)

    def set_word_wrap(self, enabled: bool) -> None:
        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if enabled
            else QPlainTextEdit.LineWrapMode.NoWrap
        )

    def set_indent_guides_enabled(self, enabled: bool) -> None:
        self._indent_guides_enabled = bool(enabled)
        self.viewport().update()

    def set_current_line_highlight(self, enabled: bool) -> None:
        self._current_line_highlight = bool(enabled)
        self._update_extra_selections()

    def set_auto_close_brackets(self, enabled: bool) -> None:
        self._auto_close_brackets = bool(enabled)

    def line_number_area_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _count: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(
                0, rect.y(), self._gutter.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        area = self.contentsRect()
        self._gutter.setGeometry(
            QRect(area.left(), area.top(), self.line_number_area_width(), area.height())
        )

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().paintEvent(event)
        self._paint_indent_guides(event)

    def _paint_indent_guides(self, event) -> None:
        if not self._indent_guides_enabled:
            return
        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor(theme.INDENT_GUIDE), 1))
        space = self.fontMetrics().horizontalAdvance(" ")
        offset = self.contentOffset()
        rect = event.rect()
        block = self.firstVisibleBlock()

        while block.isValid():
            geometry = self.blockBoundingGeometry(block).translated(offset)
            if geometry.top() > rect.bottom():
                break
            if block.isVisible() and geometry.bottom() >= rect.top():
                text = block.text()
                stripped = text.lstrip(" ")
                indent = len(text) - len(stripped)
                if stripped:
                    for column in range(TAB_WIDTH, indent, TAB_WIDTH):
                        x = offset.x() + column * space
                        painter.drawLine(
                            QPointF(x, geometry.top() + 2),
                            QPointF(x, geometry.bottom() - 1),
                        )
            block = block.next()
        painter.end()

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(theme.BG_GUTTER))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        number = block.blockNumber()
        offset = self.contentOffset()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = (
                    theme.GUTTER_FG_CURRENT
                    if number == current_line
                    else theme.GUTTER_FG
                )
                painter.setPen(QColor(color))
                painter.drawText(
                    0,
                    top,
                    self._gutter.width() - 7,
                    height,
                    Qt.AlignmentFlag.AlignRight,
                    str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    # ------------------------------------------------------------------
    # Current line and search highlighting
    # ------------------------------------------------------------------
    def _update_extra_selections(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        if self._current_line_highlight and not self.isReadOnly():
            current = QTextEdit.ExtraSelection()
            current.format.setBackground(QColor(theme.CURRENT_LINE))
            current.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            current.cursor = self.textCursor()
            current.cursor.clearSelection()
            selections.append(current)
        selections.extend(self._search_selections)
        self.setExtraSelections(selections)

    def highlight_matches(self, text: str, case_sensitive: bool = False) -> int:
        self._search_selections = []
        count = 0
        if text:
            flags = QTextDocument.FindFlags()
            if case_sensitive:
                flags |= QTextDocument.FindFlag.FindCaseSensitively
            cursor = QTextCursor(self.document())
            while True:
                cursor = self.document().find(text, cursor, flags)
                if cursor.isNull():
                    break
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor(theme.SEARCH_MATCH))
                self._search_selections.append(selection)
                count += 1
        self._update_extra_selections()
        return count

    def clear_search(self) -> None:
        if self._search_selections:
            self._search_selections = []
            self._update_extra_selections()

    def find_text(
        self,
        text: str,
        case_sensitive: bool = False,
        backwards: bool = False,
        wrap: bool = True,
    ) -> bool:
        if not text:
            return False
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backwards:
            flags |= QTextDocument.FindFlag.FindBackward

        if self.find(text, flags):
            return True
        if not wrap:
            return False

        cursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.End
            if backwards
            else QTextCursor.MoveOperation.Start
        )
        self.setTextCursor(cursor)
        return self.find(text, flags)

    def replace_next(self, old: str, new: str, case_sensitive: bool = False) -> bool:
        if not old:
            return False
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            matches = (
                selected == old
                if case_sensitive
                else selected.lower() == old.lower()
            )
            if matches:
                cursor.insertText(new)
                self.setTextCursor(cursor)
        return self.find_text(old, case_sensitive)

    def replace_all(self, old: str, new: str, case_sensitive: bool = False) -> int:
        if not old:
            return 0
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        count = 0
        match = self.document().find(old, cursor, flags)
        while not match.isNull():
            match.insertText(new)
            count += 1
            match = self.document().find(old, match, flags)
        cursor.endEditBlock()
        return count

    # ------------------------------------------------------------------
    # Editing helpers
    # ------------------------------------------------------------------
    @property
    def comment_prefix(self) -> str:
        return language_for_key(self.language).comment

    def set_language(self, language: str) -> None:
        if language == self.language:
            return
        self.language = language
        if self.highlighter is not None:
            self.highlighter.setDocument(None)
        self.highlighter = create_highlighter(language, self.document())

    def refresh_theme(self) -> None:
        """Rebuild theme-dependent colours after a theme switch."""
        if self.highlighter is not None:
            self.highlighter.setDocument(None)
        self.highlighter = create_highlighter(self.language, self.document())
        if self.highlighter is not None:
            self.highlighter.rehighlight()
        self._update_extra_selections()
        self._gutter.update()
        self.viewport().update()

    def _char_at_cursor(self) -> str:
        cursor = self.textCursor()
        if cursor.atBlockEnd():
            return ""
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
        )
        return cursor.selectedText()

    def _char_before_cursor(self) -> str:
        cursor = self.textCursor()
        if cursor.atBlockStart():
            return ""
        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.KeepAnchor,
        )
        return cursor.selectedText()

    def _word_before_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        text = cursor.selectedText()
        index = len(text)
        while index > 0 and (text[index - 1].isalnum() or text[index - 1] == "_"):
            index -= 1
        return text[index:]

    @staticmethod
    def _is_word_char(char: str) -> bool:
        return bool(char) and (char.isalnum() or char == "_")

    def _language_source_tokens(self, field_name: str) -> list[str]:
        language = language_for_key(self.language)
        raw = getattr(language, field_name, ())
        tokens: list[str] = []
        seen: set[str] = set()
        if not raw:
            return tokens
        if isinstance(raw, str):
            values = [item.strip() for item in raw.split("|") if item.strip()]
        else:
            values = []
            for item in raw:
                values.extend(
                    part.strip()
                    for part in str(item).split("|")
                    if part.strip()
                )
        for value in values:
            normalized = value.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            tokens.append(value)
        return tokens

    def _token_extra_chars(self) -> str:
        if self.language in {"html", "xml", "css"}:
            return "-"
        return ""

    def _keyword_token(self, typed: str = "") -> tuple[str, int, int] | None:
        if typed and not (
            typed.isalnum() or typed in {"_"} or typed in self._token_extra_chars()
        ):
            return None
        cursor = self.textCursor()
        block = cursor.block()
        column = cursor.positionInBlock()
        before = block.text()[:column]

        text = self.toPlainText() if self.language == "go" else ""
        special = context_token(
            self.language,
            before,
            text,
            block.blockNumber(),
        )
        if special is not None:
            return (
                special + typed,
                column - len(special),
                column + len(typed),
            )

        extra_chars = self._token_extra_chars()
        start = column
        while start > 0 and (
            before[start - 1].isalnum()
            or before[start - 1] == "_"
            or before[start - 1] in extra_chars
        ):
            start -= 1

        token = before[start:column] + typed
        end = column + len(typed)
        if not token:
            return None
        return token, start, end

    def _keyword_candidates(self, token: str) -> list[str]:
        cursor = self.textCursor()
        block = cursor.block()
        line = block.text()
        column = cursor.positionInBlock()
        text = self.toPlainText()

        context = library_context_candidates(
            self.language,
            text,
            line,
            token,
            column,
            block.blockNumber(),
        )
        if context is not None:
            return context[:10]
        if not token:
            return []

        lowered = token.lower()
        source_fields = (
            "types",
            "keywords",
            "builtins",
            "constants",
        )
        candidates: list[str] = []
        seen: set[str] = set()
        allow_hyphen = self.language in {"html", "xml", "css"}
        for field_name in source_fields:
            for item in self._language_source_tokens(field_name):
                item_lower = item.lower()
                if not item_lower.startswith(lowered) or item_lower == lowered:
                    continue
                valid = item_lower.isidentifier() or (
                    allow_hyphen
                    and all(
                        char.isalnum() or char in {"_", "-"}
                        for char in item_lower
                    )
                    and not item_lower.startswith("-")
                )
                if item_lower in seen or not valid:
                    continue
                seen.add(item_lower)
                candidates.append(item)
        candidates.sort(
            key=lambda item: (
                "_" in item or any(char.isdigit() for char in item),
                len(item),
                item.lower(),
            )
        )
        for item in library_imported_symbols(self.language, text, token):
            if not item.isidentifier():
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(item)
        return candidates[:10]

    def _show_keyword_suggestions(self, candidates: list[str]) -> None:
        if self._keyword_suggestion_popup is None or self._keyword_suggestion_list is None:
            popup = QFrame(self.viewport())
            popup.setObjectName("keywordSuggestionsFrame")
            popup.setFrameShape(QFrame.Shape.NoFrame)
            popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
            popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            layout = QVBoxLayout(popup)
            layout.setContentsMargins(1, 1, 1, 1)
            layout.setSpacing(0)

            list_widget = KeywordSuggestionList(popup)
            list_widget.setObjectName("keywordSuggestions")
            list_widget.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )
            list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            list_widget.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            list_widget.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            list_widget.verticalScrollBar().setFocusPolicy(
                Qt.FocusPolicy.NoFocus
            )
            list_widget.itemClicked.connect(
                self._accept_keyword_suggestion_from_item
            )
            layout.addWidget(list_widget)

            self._keyword_suggestion_popup = popup
            self._keyword_suggestion_list = list_widget

        list_widget = self._keyword_suggestion_list
        assert list_widget is not None
        list_widget.clear()
        for candidate in candidates:
            list_widget.addItem(QListWidgetItem(candidate))
        self._keyword_suggestion_index = 0
        current_item = list_widget.item(self._keyword_suggestion_index)
        if current_item is not None:
            list_widget.setCurrentItem(current_item)

        popup = self._keyword_suggestion_popup
        assert popup is not None
        popup.adjustSize()
        size = popup.sizeHint()
        cursor = self.cursorRect()
        viewport = self.viewport().rect()

        width = min(size.width(), viewport.width())
        x = cursor.left()
        if x + width > viewport.right():
            x = max(0, viewport.right() - width)

        # Fit the popup into the space above or below the cursor. If the
        # candidates are taller than that, the list scrolls instead.
        below = max(0, viewport.bottom() - cursor.bottom() - 3)
        above = max(0, cursor.top() - 3)
        if below >= size.height() or below >= above:
            height = min(size.height(), below)
            y = cursor.bottom() + 3
        else:
            height = min(size.height(), above)
            y = max(0, cursor.top() - height - 3)

        popup.setGeometry(x, y, width, height)
        popup.show()
        popup.raise_()
        self._keyword_suggestion_visible = True

    def _hide_keyword_suggestions(self) -> None:
        popup = self._keyword_suggestion_popup
        if popup is not None:
            popup.hide()
        self._keyword_suggestion_visible = False
        self._keyword_suggestions = []
        self._keyword_suggestion_index = -1
        self._keyword_suggestion_token = ""

    def _update_keyword_suggestions(self, typed: str = "") -> bool:
        token_info = self._keyword_token(typed)
        if token_info is None:
            self._hide_keyword_suggestions()
            return False

        token, _start, _end = token_info
        candidates = self._keyword_candidates(token)
        self._keyword_suggestions = candidates
        self._keyword_suggestion_token = token

        if not candidates:
            self._hide_keyword_suggestions()
            return False

        self._keyword_suggestion_index = 0
        self._show_keyword_suggestions(candidates)
        return True

    def _accept_keyword_suggestion_from_item(
        self, item: QListWidgetItem
    ) -> None:
        if not self._keyword_suggestion_visible:
            return
        list_widget = self._keyword_suggestion_list
        if list_widget is None:
            return
        row = list_widget.row(item)
        if 0 <= row < len(self._keyword_suggestions):
            self._keyword_suggestion_index = row
            self._accept_keyword_suggestion()

    def _move_keyword_suggestion(self, delta: int) -> None:
        if not self._keyword_suggestion_visible or not self._keyword_suggestions:
            return
        count = len(self._keyword_suggestions)
        current = self._keyword_suggestion_index
        if not 0 <= current < count:
            current = 0
        self._keyword_suggestion_index = max(0, min(count - 1, current + delta))
        list_widget = self._keyword_suggestion_list
        if list_widget is None:
            return
        item = list_widget.item(self._keyword_suggestion_index)
        if item is not None:
            list_widget.setCurrentItem(item)
            list_widget.scrollToItem(
                item, QAbstractItemView.ScrollHint.EnsureVisible
            )

    def _accept_keyword_suggestion(self) -> bool:
        if not self._keyword_suggestion_visible or not self._keyword_suggestions:
            self._hide_keyword_suggestions()
            return False

        completion = (
            self._keyword_suggestions[self._keyword_suggestion_index]
            if 0 <= self._keyword_suggestion_index < len(self._keyword_suggestions)
            else self._keyword_suggestions[0]
        )
        token_info = self._keyword_token()
        if token_info is None:
            self._hide_keyword_suggestions()
            return False

        token, start, end = token_info
        cursor = self.textCursor()
        block = cursor.block()
        cursor.beginEditBlock()
        cursor.setPosition(block.position() + start)
        cursor.setPosition(block.position() + end, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(completion)
        cursor.setPosition(block.position() + start + len(completion))
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self._hide_keyword_suggestions()
        return True

    def _should_autoclose_quote(self) -> bool:
        before = self._char_before_cursor()
        after = self._char_at_cursor()
        if before == "\\":
            return False
        if self._is_word_char(before):
            token = self._word_before_cursor().lower()
            if token not in STRING_PREFIXES:
                return False
        if self._is_word_char(after):
            return False
        return True

    def _handle_autoclose(self, text: str) -> bool:
        if not self._auto_close_brackets or len(text) != 1:
            return False
        cursor = self.textCursor()

        if text in CLOSING_BRACKETS or text in QUOTE_PAIRS:
            if not cursor.hasSelection() and self._char_at_cursor() == text:
                cursor.movePosition(QTextCursor.MoveOperation.Right)
                self.setTextCursor(cursor)
                return True

        if text not in BRACKET_PAIRS and text not in QUOTE_PAIRS:
            return False

        closing = BRACKET_PAIRS.get(text, text)
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            selected = cursor.selectedText()
            cursor.beginEditBlock()
            cursor.insertText(f"{text}{selected}{closing}")
            cursor.setPosition(start + 1)
            cursor.setPosition(end + 1, QTextCursor.MoveMode.KeepAnchor)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            return True

        if text in QUOTE_PAIRS and not self._should_autoclose_quote():
            return False

        cursor.insertText(text + closing)
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        self.setTextCursor(cursor)
        return True

    def _handle_html_tag_close(self) -> bool:
        """Insert a matching closing tag after a typed ``>`` in HTML/XML."""
        if (
            not self._auto_close_brackets
            or self.language not in {"html", "xml"}
        ):
            return False
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        before = cursor.block().text()[: cursor.positionInBlock()]
        start = before.rfind("<")
        if start < 0 or ">" in before[start:]:
            return False
        fragment = before[start + 1 :]
        if not fragment or fragment[0] in {"/", "!", "?"}:
            return False
        if fragment.rstrip().endswith("/"):
            return False
        if fragment.count('"') % 2 or fragment.count("'") % 2:
            return False
        match = re.match(r"([A-Za-z][\w:.-]*)(?:\s[^<>]*)?$", fragment)
        if match is None:
            return False
        tag = match.group(1)
        if tag.lower() in HTML_VOID_TAGS:
            return False
        cursor.insertText(f"></{tag}>")
        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.MoveAnchor,
            len(tag) + 3,
        )
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        return True

    def _insert_newline_with_indent(self) -> None:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        indent = block_text[: len(block_text) - len(block_text.lstrip())]
        trimmed = block_text.rstrip()
        extra = " " * TAB_WIDTH if trimmed.endswith((":", "{", "(", "[")) else ""
        cursor.insertText("\n" + indent + extra)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _delete_bracket_pair(self) -> bool:
        if not self._auto_close_brackets:
            return False
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        before = self._char_before_cursor()
        after = self._char_at_cursor()
        if not before or not after:
            return False
        if BRACKET_PAIRS.get(before) != after and not (
            before == after and before in QUOTE_PAIRS
        ):
            return False
        cursor.beginEditBlock()
        cursor.deletePreviousChar()
        cursor.deleteChar()
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        return True

    def _smart_backspace(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        column = cursor.positionInBlock()
        if column == 0:
            return False
        before = cursor.block().text()[:column]
        if before and not before.strip():
            remove = column % TAB_WIDTH or TAB_WIDTH
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.KeepAnchor,
                min(remove, column),
            )
            cursor.removeSelectedText()
            return True
        return False

    def _indent_selection(self, unindent: bool = False) -> None:
        cursor = self.textCursor()
        document = self.document()

        if not cursor.hasSelection():
            if unindent:
                self._smart_backspace()
            else:
                column = cursor.positionInBlock()
                cursor.insertText(" " * (TAB_WIDTH - column % TAB_WIDTH))
            return

        start_block = document.findBlock(cursor.selectionStart())
        end_block = document.findBlock(cursor.selectionEnd())

        cursor.beginEditBlock()
        block = start_block
        while block.isValid():
            block_cursor = QTextCursor(block)
            if unindent:
                text = block.text()
                remove = 0
                if text.startswith("\t"):
                    remove = 1
                else:
                    while remove < TAB_WIDTH and remove < len(text) and text[remove] == " ":
                        remove += 1
                if remove:
                    block_cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        remove,
                    )
                    block_cursor.removeSelectedText()
            else:
                block_cursor.insertText(" " * TAB_WIDTH)
            if block == end_block:
                break
            block = block.next()
        cursor.endEditBlock()

    def toggle_comment(self) -> None:
        prefix = self.comment_prefix
        if not prefix:
            return
        cursor = self.textCursor()
        document = self.document()
        start_block = document.findBlock(cursor.selectionStart())
        end_block = document.findBlock(cursor.selectionEnd())

        blocks = []
        block = start_block
        while block.isValid():
            blocks.append(block)
            if block == end_block:
                break
            block = block.next()

        candidates = [b for b in blocks if b.text().strip()]
        if not candidates:
            return

        all_commented = all(
            b.text().lstrip().startswith(prefix) for b in candidates
        )

        cursor.beginEditBlock()
        for block in blocks:
            text = block.text()
            indent = len(text) - len(text.lstrip())
            block_cursor = QTextCursor(block)
            if all_commented:
                index = text.find(prefix, indent)
                if index == -1:
                    continue
                remove = len(prefix)
                if text[index + remove : index + remove + 1] == " ":
                    remove += 1
                block_cursor.setPosition(block.position() + index)
                block_cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    remove,
                )
                block_cursor.removeSelectedText()
            else:
                block_cursor.setPosition(block.position() + indent)
                block_cursor.insertText(prefix + " ")
        cursor.endEditBlock()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Tab and modifiers == Qt.KeyboardModifier.NoModifier:
            if self._keyword_suggestion_visible and self._keyword_suggestions:
                self._accept_keyword_suggestion()
                return
            self._indent_selection()
            return
        if key == Qt.Key.Key_Backtab or (
            key == Qt.Key.Key_Tab
            and modifiers == Qt.KeyboardModifier.ShiftModifier
        ):
            self._hide_keyword_suggestions()
            self._indent_selection(unindent=True)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and modifiers == Qt.KeyboardModifier.NoModifier:
            self._hide_keyword_suggestions()
            self._insert_newline_with_indent()
            return
        if key == Qt.Key.Key_Escape and self._keyword_suggestion_visible:
            self._hide_keyword_suggestions()
            return
        if (
            key in (Qt.Key.Key_Up, Qt.Key.Key_Down)
            and modifiers == Qt.KeyboardModifier.NoModifier
            and self._keyword_suggestion_visible
            and self._keyword_suggestions
        ):
            self._move_keyword_suggestion(
                -1 if key == Qt.Key.Key_Up else 1
            )
            event.accept()
            return
        if key in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
            Qt.Key.Key_PageUp,
            Qt.Key.Key_PageDown,
        ):
            self._hide_keyword_suggestions()
        if key == Qt.Key.Key_Backspace and modifiers == Qt.KeyboardModifier.NoModifier:
            self._hide_keyword_suggestions()
            if self._delete_bracket_pair() or self._smart_backspace():
                return
        if not (
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.AltModifier
                | Qt.KeyboardModifier.MetaModifier
            )
        ) and event.text():
            text = event.text()
            if text.isprintable():
                if text == ">" and self._handle_html_tag_close():
                    self._update_keyword_suggestions()
                    return
                if self._handle_autoclose(text):
                    self._update_keyword_suggestions()
                    return
                super().keyPressEvent(event)
                self._update_keyword_suggestions()
                return

        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._hide_keyword_suggestions()
        self.focused.emit()
        super().mousePressEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().focusInEvent(event)
        self.focused.emit()

    def focusOutEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._hide_keyword_suggestions()
        super().focusOutEvent(event)

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._hide_keyword_suggestions()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta:
                self.set_font_size(self._font_size + (1 if delta > 0 else -1))
                self.font_size_changed.emit(self._font_size)
            event.accept()
            return
        super().wheelEvent(event)
