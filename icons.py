"""Hand-drawn, theme-aware line icons (no external assets)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

from . import theme


def _pixmap(size: int) -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(2.0)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(size / 24.0, size / 24.0)
    return pixmap, painter


def _pen(painter: QPainter, color: str, width: float = 1.7) -> None:
    painter.setPen(
        QPen(
            QColor(color),
            width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _fill(painter: QPainter, color: str, points: list[tuple[float, float]]) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))


def icon(name: str, color: str | None = None, size: int = 20) -> QIcon:
    color = color or theme.FG_MUTED
    pixmap, painter = _pixmap(size)
    _pen(painter, color)

    if name == "new":
        painter.drawRoundedRect(QRectF(6, 2.5, 12, 19), 2, 2)
        painter.drawLine(QPointF(9, 8), QPointF(15, 8))
        painter.drawLine(QPointF(9, 12), QPointF(15, 12))
        painter.drawLine(QPointF(9, 16), QPointF(11.5, 16))
        _pen(painter, theme.ACCENT, 1.9)
        painter.drawLine(QPointF(17, 15), QPointF(22, 15))
        painter.drawLine(QPointF(19.5, 12.5), QPointF(19.5, 17.5))

    elif name in ("open", "folder"):
        path = QPainterPath()
        path.moveTo(2.5, 19.5)
        path.lineTo(2.5, 6.5)
        path.lineTo(8.5, 6.5)
        path.lineTo(10.5, 8.5)
        path.lineTo(21.5, 8.5)
        path.lineTo(21.5, 19.5)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(2.5, 11), QPointF(21.5, 11))

    elif name == "save":
        painter.drawLine(QPointF(12, 3.5), QPointF(12, 14.5))
        painter.drawLine(QPointF(8, 10.5), QPointF(12, 14.5))
        painter.drawLine(QPointF(16, 10.5), QPointF(12, 14.5))
        painter.drawPolyline(
            QPolygonF(
                [QPointF(5, 16.5), QPointF(5, 20.5), QPointF(19, 20.5), QPointF(19, 16.5)]
            )
        )

    elif name == "run":
        _fill(painter, color, [(8, 4.5), (20, 12), (8, 19.5)])

    elif name == "stop":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(6.5, 6.5, 11, 11), 2.5, 2.5)

    elif name in ("build", "package"):
        hexagon = [
            (12, 2.5),
            (20, 7),
            (20, 17),
            (12, 21.5),
            (4, 17),
            (4, 7),
        ]
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in hexagon]))
        painter.drawLine(QPointF(4, 7), QPointF(12, 11.5))
        painter.drawLine(QPointF(20, 7), QPointF(12, 11.5))
        painter.drawLine(QPointF(12, 11.5), QPointF(12, 21.5))

    elif name == "panel":
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 2.5, 2.5)
        painter.drawLine(QPointF(9, 4), QPointF(9, 20))
        _pen(painter, theme.ACCENT, 1.6)
        painter.drawLine(QPointF(5.5, 8), QPointF(7, 8))
        painter.drawLine(QPointF(5.5, 11), QPointF(7, 11))

    elif name == "terminal":
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 2.5, 2.5)
        painter.drawPolyline(
            QPolygonF([QPointF(6.5, 9), QPointF(9.5, 11.5), QPointF(6.5, 14)])
        )
        painter.drawLine(QPointF(11.5, 15), QPointF(16, 15))

    elif name == "search":
        painter.drawEllipse(QRectF(4, 4, 11, 11))
        painter.drawLine(QPointF(14, 14), QPointF(20.5, 20.5))

    elif name in ("command", "spark"):
        _fill(
            painter,
            color,
            [(12, 2), (14.6, 9.4), (22, 12), (14.6, 14.6), (12, 22), (9.4, 14.6), (2, 12), (9.4, 9.4)],
        )

    elif name == "settings":
        for y, knob in ((7.5, 9.0), (12.0, 15.0), (16.5, 7.0)):
            painter.drawLine(QPointF(3.5, y), QPointF(20.5, y))
            painter.setBrush(QColor(color))
            painter.drawEllipse(QRectF(knob - 2.2, y - 2.2, 4.4, 4.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "plugins":
        painter.drawRoundedRect(QRectF(4, 4, 7, 7), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(13, 4, 7, 7), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(4, 13, 7, 7), 1.5, 1.5)
        painter.drawLine(QPointF(13, 16.5), QPointF(20, 16.5))
        painter.drawLine(QPointF(16.5, 13), QPointF(16.5, 20))

    elif name == "git":
        painter.drawLine(QPointF(7, 6), QPointF(7, 18))
        branch = QPainterPath()
        branch.moveTo(7, 11)
        branch.cubicTo(12, 11, 17, 12, 17, 7)
        painter.drawPath(branch)
        for x, y in ((7, 4), (7, 20), (17, 4)):
            painter.drawEllipse(QRectF(x - 2.2, y - 2.2, 4.4, 4.4))

    elif name == "close":
        painter.drawLine(QPointF(6.5, 6.5), QPointF(17.5, 17.5))
        painter.drawLine(QPointF(17.5, 6.5), QPointF(6.5, 17.5))

    elif name == "plus":
        painter.drawLine(QPointF(12, 5), QPointF(12, 19))
        painter.drawLine(QPointF(5, 12), QPointF(19, 12))

    elif name == "refresh":
        painter.drawArc(QRectF(4, 4, 16, 16), 35 * 16, 290 * 16)
        painter.drawPolyline(
            QPolygonF([QPointF(18.5, 2.5), QPointF(19.5, 7), QPointF(15, 7.5)])
        )

    elif name == "chevron-right":
        painter.drawPolyline(
            QPolygonF([QPointF(9, 5.5), QPointF(15.5, 12), QPointF(9, 18.5)])
        )

    elif name == "chevron-down":
        painter.drawPolyline(
            QPolygonF([QPointF(5.5, 9), QPointF(12, 15.5), QPointF(18.5, 9)])
        )

    elif name == "file":
        path = QPainterPath()
        path.moveTo(6, 2.5)
        path.lineTo(14, 2.5)
        path.lineTo(18.5, 7)
        path.lineTo(18.5, 21.5)
        path.lineTo(6, 21.5)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawPolyline(
            QPolygonF([QPointF(14, 2.5), QPointF(14, 7), QPointF(18.5, 7)])
        )

    elif name == "moon":
        path = QPainterPath()
        path.addEllipse(QRectF(4, 3, 16, 18))
        painter.drawPath(path)
        _fill(painter, theme.BG_PANEL, [(10, 4), (20, 4), (20, 22), (14, 18)])

    elif name == "globe":
        painter.drawEllipse(QRectF(3, 3, 18, 18))
        painter.drawEllipse(QRectF(8, 3, 8, 18))
        painter.drawLine(QPointF(3, 12), QPointF(21, 12))
        painter.drawArc(QRectF(3, 7, 18, 10), 0, 180 * 16)
        painter.drawArc(QRectF(3, 7, 18, 10), 0, -180 * 16)

    elif name == "split":
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 2.5, 2.5)
        painter.drawLine(QPointF(12, 4), QPointF(12, 20))
        painter.drawLine(QPointF(6, 8), QPointF(9, 8))
        painter.drawLine(QPointF(15, 8), QPointF(18, 8))
        painter.drawLine(QPointF(6, 11), QPointF(9, 11))
        painter.drawLine(QPointF(15, 11), QPointF(18, 11))

    painter.end()
    return QIcon(pixmap)


def dot_icon(color: str, size: int = 10) -> QIcon:
    pixmap, painter = _pixmap(size)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(QRectF(4, 4, 16, 16))
    painter.end()
    return QIcon(pixmap)


def file_badge(color: str, size: int = 16) -> QIcon:
    pixmap, painter = _pixmap(size)
    _pen(painter, theme.FG_DIM, 1.5)
    path = QPainterPath()
    path.moveTo(5, 2.5)
    path.lineTo(13, 2.5)
    path.lineTo(18, 7.5)
    path.lineTo(18, 21.5)
    path.lineTo(5, 21.5)
    path.closeSubpath()
    painter.drawPath(path)
    painter.drawPolyline(
        QPolygonF([QPointF(13, 2.5), QPointF(13, 7.5), QPointF(18, 7.5)])
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(QRectF(13.5, 13.5, 9, 9))
    painter.end()
    return QIcon(pixmap)
