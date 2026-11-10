"""固定屏幕尺寸的缩放手柄及中文尺寸提示。"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPen

from resources.colors import ACCENT
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSimpleTextItem

from core.models import Rect


HANDLE_CURSORS = {
    "nw": Qt.CursorShape.SizeFDiagCursor, "se": Qt.CursorShape.SizeFDiagCursor,
    "ne": Qt.CursorShape.SizeBDiagCursor, "sw": Qt.CursorShape.SizeBDiagCursor,
    "n": Qt.CursorShape.SizeVerCursor, "s": Qt.CursorShape.SizeVerCursor,
    "w": Qt.CursorShape.SizeHorCursor, "e": Qt.CursorShape.SizeHorCursor,
}


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, name: str, parent: QGraphicsItem) -> None:
        super().__init__(-3.5, -3.5, 7, 7, parent)
        self.name = name
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setPen(QPen(QColor(ACCENT), 1))
        self.setBrush(QColor("#ffffff"))
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(2)
        self.setToolTip("拖动调整尺寸；按退出键取消；按住上档键可临时关闭网格吸附。")


class SelectionAdornments:
    def __init__(self, outline: QGraphicsRectItem) -> None:
        self.outline = outline
        self.handles = {key: ResizeHandle(key, outline) for key in HANDLE_CURSORS}
        self.badge = QGraphicsRectItem(outline)
        self.badge.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.badge.setPen(QPen(Qt.PenStyle.NoPen))
        self.badge.setBrush(QColor(ACCENT))
        self.badge.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.text = QGraphicsSimpleTextItem(self.badge)
        self.text.setFont(QFont("Microsoft YaHei UI", 9))
        self.text.setBrush(QColor("#ffffff"))
        self.text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.badge.hide()

    def update(self, rect: QRectF, geometry: Rect | None, *, root: bool, editable: bool,
               zoom: int, moving: bool = False) -> None:
        self.outline.setRect(rect)
        center = rect.center()
        positions = {"nw": rect.topLeft(), "n": QPointF(center.x(), rect.top()), "ne": rect.topRight(),
                     "w": QPointF(rect.left(), center.y()), "e": QPointF(rect.right(), center.y()),
                     "sw": rect.bottomLeft(), "s": QPointF(center.x(), rect.bottom()), "se": rect.bottomRight()}
        for key, handle in self.handles.items():
            handle.setPos(positions[key])
            available = not root or key in {"e", "s", "se"}
            # 小控件隐藏拥挤的边中点，保留角点便于重新放大。
            if key in {"n", "s"} and rect.width() * zoom / 100 < 24:
                available = False
            if key in {"e", "w"} and rect.height() * zoom / 100 < 24:
                available = False
            handle.setVisible(editable and available)
        self.badge.setVisible(geometry is not None and moving)
        if geometry and moving:
            self.text.setText(f"宽 {geometry.width}　高 {geometry.height}" if root else
                              f"位置 {geometry.x}, {geometry.y}　·　{geometry.width} × {geometry.height}")
            size = self.text.boundingRect()
            self.badge.setRect(0, 0, size.width() + 16, size.height() + 8)
            self.text.setPos(8, 4)
            self.badge.setPos(rect.left(), rect.bottom() + 12 * 100 / zoom)
