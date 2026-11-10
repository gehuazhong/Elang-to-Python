"""设计窗口的外框示意；内容坐标保持不变，系统装饰绘制在内容区外。"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QMainWindow, QStyleOptionGraphicsItem, QWidget


class WindowFrame(QGraphicsRectItem):
    def __init__(self) -> None:
        super().__init__()
        self.title = "窗口"
        self.icon = QIcon()
        self.frameless = False
        self.buttons: tuple[str, ...] = ()
        self.setZValue(-1)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setToolTip("单击标题栏或外框，编辑窗口属性。")

    def configure(self, window: QMainWindow) -> None:
        flags = window.windowFlags()
        self.frameless = bool(flags & Qt.WindowType.FramelessWindowHint)
        self.title = window.windowTitle()
        self.icon = window.windowIcon()
        self.buttons = tuple(name for name, flag in (
            ("minimize", Qt.WindowType.WindowMinimizeButtonHint),
            ("maximize", Qt.WindowType.WindowMaximizeButtonHint),
            ("close", Qt.WindowType.WindowCloseButtonHint),
        ) if flags & flag)
        self.preview_size(window.width(), window.height())

    def preview_size(self, width: int, height: int) -> None:
        self.setRect(QRectF(0, 0, width, height) if self.frameless else
                     QRectF(-5, -39, width + 10, height + 44))
        self.update()

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-1, -1, 10, 12)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        rect = self.rect()
        painter.save()
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(43, 49, 41, 24))
            painter.drawRoundedRect(rect.translated(2, 3), 2, 2)
            if self.frameless:
                return
            painter.setClipRect(rect)
            painter.setPen(QPen(QColor("#a3aaa0"), 1))
            painter.setBrush(QColor("#f5f6f2"))
            painter.drawRoundedRect(rect, 2, 2)
            if self.icon.isNull():
                painter.setPen(QPen(QColor("#56674f"), 1.4))
                painter.drawRoundedRect(QRectF(10, -27, 15, 14), 2, 2)
                painter.drawLine(QPointF(10, -23), QPointF(25, -23))
            else:
                self.icon.paint(painter, QRect(10, -28, 16, 16))
            painter.setPen(QColor("#30352e"))
            space = max(0, int(rect.width() - 55 - len(self.buttons) * 38))
            title = painter.fontMetrics().elidedText(self.title, Qt.TextElideMode.ElideRight, space)
            painter.drawText(QRectF(35, -38, space, 37), Qt.AlignmentFlag.AlignVCenter, title)
            right = rect.right() - 18
            painter.setPen(QPen(QColor("#5b6456"), 1.1))
            for name in reversed(self.buttons):
                if name == "close":
                    painter.drawLine(QPointF(right - 5, -24), QPointF(right + 5, -14))
                    painter.drawLine(QPointF(right + 5, -24), QPointF(right - 5, -14))
                elif name == "maximize":
                    painter.drawRect(QRectF(right - 5, -24, 10, 10))
                else:
                    painter.drawLine(QPointF(right - 5, -19), QPointF(right + 5, -19))
                right -= 38
        finally:
            painter.restore()
