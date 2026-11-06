"""Syntax highlighters driven by the language registry."""

from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from . import theme
from .languages import Language, language_for_key

NUMBER_RE = (
    r"\b(0[xX][0-9a-fA-F_]+[uUlL]*|0[bB][01_]+[uUlL]*|0[oO][0-7_]+[uUlL]*|"
    r"(\d[\d_]*\.?[\d_]*|\.\d[\d_]*)([eE][+-]?\d+)?[fFdDlLuU]*)\b"
)

STYLE_MAP = {
    "keyword": ("SYN_KEYWORD", True, False, False),
    "type": ("SYN_TYPE", False, False, False),
    "builtin": ("SYN_BUILTIN", False, False, False),
    "constant": ("SYN_CONSTANT", False, False, False),
    "string": ("SYN_STRING", False, False, False),
    "comment": ("SYN_COMMENT", False, True, False),
    "number": ("SYN_NUMBER", False, False, False),
    "function": ("SYN_FUNCTION", False, False, False),
    "decorator": ("SYN_DECORATOR", False, False, False),
    "preproc": ("SYN_PREPROC", False, False, False),
    "variable": ("SYN_VARIABLE", False, False, False),
    "key": ("SYN_KEY", False, False, False),
    "tag": ("SYN_TAG", False, False, False),
    "attribute": ("SYN_ATTRIBUTE", False, False, False),
    "heading": ("SYN_HEADING", True, False, False),
    "link": ("SYN_LINK", False, False, True),
    "special": ("ACCENT", False, True, False),
    "bold": ("FG", True, False, False),
    "italic": ("FG_MUTED", False, True, False),
    "code": ("SYN_STRING", False, False, False),
    "selector": ("SYN_TAG", False, False, False),
    "property": ("SYN_BUILTIN", False, False, False),
    "atrule": ("SYN_DECORATOR", False, False, False),
    "value": ("SYN_NUMBER", False, False, False),
}


def _style_format(name: str) -> QTextCharFormat:
    token, bold, italic, underline = STYLE_MAP.get(
        name, ("FG", False, False, False)
    )
    color = getattr(theme, token, theme.FG)
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    if underline:
        fmt.setFontUnderline(True)
    return fmt


def _single_quote_end(text: str, start: int, quote: str) -> int | None:
    i = start + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return None


def _alternation(value) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return "|".join(value)


class BaseHighlighter(QSyntaxHighlighter):
    """Shared rule/format plumbing."""

    def __init__(self, document: QTextDocument, language_key: str):
        super().__init__(document)
        self.language_key = language_key
        self.language: Language = language_for_key(language_key)
        self.formats: dict[str, QTextCharFormat] = {}
        self._rules: list[tuple[QRegularExpression, QTextCharFormat, int]] = []
        self._post_rules: list[tuple[QRegularExpression, QTextCharFormat, int]] = []

    def fmt(self, name: str) -> QTextCharFormat:
        if name not in self.formats:
            self.formats[name] = _style_format(name)
        return self.formats[name]

    def add_rule(
        self,
        pattern: str,
        style: str,
        group: int = 0,
        case_insensitive: bool = False,
    ) -> None:
        options = QRegularExpression.PatternOption.NoPatternOption
        if case_insensitive:
            options |= QRegularExpression.PatternOption.CaseInsensitiveOption
        self._rules.append(
            (QRegularExpression(pattern, options), self.fmt(style), group)
        )

    def add_post_rule(self, pattern: str, style: str, group: int = 0) -> None:
        self._post_rules.append(
            (
                QRegularExpression(
                    pattern, QRegularExpression.PatternOption.NoPatternOption
                ),
                self.fmt(style),
                group,
            )
        )

    def apply_rules(self, text: str, masked: list[tuple[int, int]]) -> None:
        for regex, fmt, group in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart(group)
                length = match.capturedLength(group)
                if start < 0 or length <= 0:
                    continue
                end = start + length
                if any(
                    start < span_end and end > span_start
                    for span_start, span_end in masked
                ):
                    continue
                self.setFormat(start, length, fmt)

    def apply_post_rules(self, text: str) -> None:
        for regex, fmt, group in self._post_rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart(group)
                length = match.capturedLength(group)
                if start >= 0 and length > 0:
                    self.setFormat(start, length, fmt)

    def scan_structures(
        self,
        text: str,
        *,
        block: tuple[str, str] | None,
        line_comments: tuple[str, ...],
        quotes: tuple[str, ...],
        preprocessor: bool = False,
    ) -> list[tuple[int, int]] | None:
        """Colour comments/strings and return masked spans.

        Returns ``None`` when the whole block is a comment continuation.
        """
        self.setCurrentBlockState(0)
        masked: list[tuple[int, int]] = []
        length = len(text)
        comment_fmt = self.fmt("comment")
        string_fmt = self.fmt("string")

        if preprocessor:
            stripped = text.lstrip()
            if stripped.startswith("#"):
                start = length - len(stripped)
                self.setFormat(start, length - start, self.fmt("preproc"))

        i = 0
        if block is not None:
            block_start, block_end = block
            if self.previousBlockState() == 1:
                end = text.find(block_end)
                if end == -1:
                    self.setFormat(0, length, comment_fmt)
                    self.setCurrentBlockState(1)
                    return None
                end += len(block_end)
                self.setFormat(0, end, comment_fmt)
                masked.append((0, end))
                i = end

        while i < length:
            if block is not None and text.startswith(block[0], i):
                end = text.find(block[1], i + len(block[0]))
                if end == -1:
                    self.setFormat(i, length - i, comment_fmt)
                    masked.append((i, length))
                    self.setCurrentBlockState(1)
                    break
                end += len(block[1])
                self.setFormat(i, end - i, comment_fmt)
                masked.append((i, end))
                i = end
                continue

            line_token = next(
                (token for token in line_comments if text.startswith(token, i)),
                None,
            )
            if line_token is not None:
                self.setFormat(i, length - i, comment_fmt)
                masked.append((i, length))
                break

            char = text[i]
            if char in quotes:
                end = _single_quote_end(text, i, char)
                if end is None:
                    self.setFormat(i, length - i, string_fmt)
                    masked.append((i, length))
                    break
                self.setFormat(i, end - i, string_fmt)
                masked.append((i, end))
                i = end
                continue

            i += 1

        return masked


class PythonHighlighter(BaseHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document, "python")
        language = self.language

        self.add_rule(r"@[A-Za-z_][\w.]*", "decorator")
        self.add_rule(r"\b([A-Za-z_]\w*)(?=\s*\()", "function", 1)
        self.add_rule(r"\b(?:def|class)\s+([A-Za-z_]\w*)", "function", 1)
        self.add_rule(rf"\b({_alternation(language.builtins)})\b", "builtin", 1)
        self.add_rule(rf"\b({_alternation(language.keywords)})\b", "keyword", 1)
        self.add_rule(r"\b(True|False|None)\b", "constant")
        self.add_rule(NUMBER_RE, "number")
        self.add_rule(r"\b(self|cls)\b", "special")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        self.setCurrentBlockState(0)
        masked: list[tuple[int, int]] = []
        i = 0
        length = len(text)
        string_fmt = self.fmt("string")

        state = self.previousBlockState()
        if state in (1, 2):
            delimiter = '"""' if state == 1 else "'''"
            end = text.find(delimiter)
            if end == -1:
                self.setFormat(0, length, string_fmt)
                self.setCurrentBlockState(state)
                return
            self.setFormat(0, end + 3, string_fmt)
            masked.append((0, end + 3))
            i = end + 3

        while i < length:
            char = text[i]

            if char == "#":
                self.setFormat(i, length - i, self.fmt("comment"))
                masked.append((i, length))
                break

            if text.startswith('"""', i) or text.startswith("'''", i):
                delimiter = text[i : i + 3]
                end = text.find(delimiter, i + 3)
                if end == -1:
                    self.setFormat(i, length - i, string_fmt)
                    masked.append((i, length))
                    self.setCurrentBlockState(1 if delimiter == '"""' else 2)
                    break
                self.setFormat(i, end + 3 - i, string_fmt)
                masked.append((i, end + 3))
                i = end + 3
                continue

            if char in ('"', "'"):
                end = _single_quote_end(text, i, char)
                if end is None:
                    self.setFormat(i, length - i, string_fmt)
                    masked.append((i, length))
                    break
                self.setFormat(i, end - i, string_fmt)
                masked.append((i, end))
                i = end
                continue

            i += 1

        self.apply_rules(text, masked)


class GenericHighlighter(BaseHighlighter):
    def __init__(self, document: QTextDocument, language_key: str):
        super().__init__(document, language_key)
        language = self.language
        insensitive = language.case_insensitive

        self.add_rule(r"\b([A-Za-z_]\w*)(?=\s*\()", "function", 1, insensitive)
        for rule in language.extra_rules:
            pattern, style = rule[0], rule[1]
            group = rule[2] if len(rule) > 2 else 0
            self.add_rule(pattern, style, group, insensitive)
        if language.keywords:
            self.add_rule(
                rf"\b({_alternation(language.keywords)})\b",
                "keyword",
                1,
                insensitive,
            )
        if language.types:
            self.add_rule(
                rf"\b({_alternation(language.types)})\b", "type", 1, insensitive
            )
        if language.builtins:
            self.add_rule(
                rf"\b({_alternation(language.builtins)})\b",
                "builtin",
                1,
                insensitive,
            )
        if language.constants:
            self.add_rule(
                rf"\b({_alternation(language.constants)})\b",
                "constant",
                1,
                insensitive,
            )
        self.add_rule(NUMBER_RE, "number")
        for pattern, style in language.post_rules:
            self.add_post_rule(pattern, style)

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        masked = self.scan_structures(
            text,
            block=self.language.block_comment,
            line_comments=self.language.line_comments,
            quotes=self.language.string_quotes,
            preprocessor=self.language.preprocessor,
        )
        if masked is None:
            return
        self.apply_rules(text, masked)
        self.apply_post_rules(text)


class MarkupHighlighter(BaseHighlighter):
    def __init__(self, document: QTextDocument, language_key: str):
        super().__init__(document, language_key)
        self.add_rule(r"<!DOCTYPE[^>]*>", "preproc", 0, True)
        self.add_rule(r"</?([A-Za-z][\w:.-]*)", "tag", 1)
        self.add_rule(r"\b([A-Za-z_:][\w:.-]*)(?=\s*=)", "attribute", 1)
        self.add_rule(r"&[A-Za-z#\d]+;", "constant")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        masked = self.scan_structures(
            text,
            block=self.language.block_comment,
            line_comments=(),
            quotes=('"', "'"),
        )
        if masked is None:
            return
        self.apply_rules(text, masked)


class CssHighlighter(BaseHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document, "css")
        self.add_rule(r"@[-\w]+", "atrule")
        self.add_rule(r"!important\b", "keyword", 0, True)
        self.add_rule(r"#[0-9a-fA-F]{3,8}\b", "value")
        self.add_rule(
            r"^\s*([a-zA-Z-]+)(?=\s*:)", "property", 1
        )
        self.add_rule(r"::?[A-Za-z-]+", "builtin")
        self.add_rule(r"^[^{}\n;]+(?=\s*\{)", "selector")
        self.add_rule(NUMBER_RE, "value")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        masked = self.scan_structures(
            text,
            block=self.language.block_comment,
            line_comments=(),
            quotes=('"', "'"),
        )
        if masked is None:
            return
        self.apply_rules(text, masked)


class MarkdownHighlighter(BaseHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document, "markdown")
        self.add_rule(r"^#{1,6}\s.*$", "heading")
        self.add_rule(r"^\s*>\s?.*$", "italic")
        self.add_rule(r"^\s*(?:[-*+]|\d+\.)\s", "decorator")
        self.add_rule(r"`[^`\n]+`", "code")
        self.add_rule(r"\*\*[^*\n]+\*\*|__[^_\n]+__", "heading")
        self.add_rule(r"(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)", "italic")
        self.add_rule(r"\[[^\]]*\]\([^)]*\)", "link")
        self.add_rule(r"^\s*(?:---+|\*\*\*+|___+)\s*$", "comment")
        self.add_rule(r"<[^>]+>", "tag")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        stripped = text.strip()
        fence = stripped.startswith("```") or stripped.startswith("~~~")

        if self.previousBlockState() == 1:
            if fence:
                self.setCurrentBlockState(0)
                self.setFormat(0, len(text), self.fmt("decorator"))
            else:
                self.setFormat(0, len(text), self.fmt("code"))
                self.setCurrentBlockState(1)
            return

        self.setCurrentBlockState(0)
        if fence:
            self.setFormat(0, len(text), self.fmt("decorator"))
            self.setCurrentBlockState(1)
            return

        self.apply_rules(text, [])


def create_highlighter(
    language_key: str,
    document: QTextDocument,
) -> QSyntaxHighlighter | None:
    language = language_for_key(language_key)
    kind = language.highlighter
    if kind == "python":
        return PythonHighlighter(document)
    if kind == "generic":
        return GenericHighlighter(document, language_key)
    if kind == "markup":
        return MarkupHighlighter(document, language_key)
    if kind == "css":
        return CssHighlighter(document)
    if kind == "markdown":
        return MarkdownHighlighter(document)
    return None
