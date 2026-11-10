"""原生控件负责外观，独立图元负责移动；文档不依赖具体绘制实现。"""

from __future__ import annotations

from collections.abc import Iterator

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPalette, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QStyleOptionGraphicsItem, QWidget,
)

from core.build_plan import BuildPlan
from core.models import FrozenMap
from core.registry import WidgetRegistry
from resources.colors import MUTED
from runtime.builder import RuntimeTree
from runtime.advanced_widgets import content_rect
from .window_frame import WindowFrame


class CanvasSurface(QGraphicsRectItem):
    def __init__(self) -> None:
        super().__init__()
        self.grid_size = 8
        self.show_grid = True
        self._grid_key: tuple[int, int] | None = None
        self._grid_brush = QBrush()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QColor("#ffffff"))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)
        if self.show_grid:
            area = option.exposedRect.intersected(self.rect())
            step = self.grid_size
            scale = abs(painter.worldTransform().m11()) * painter.device().devicePixelRatioF()
            # 缩小时只显示较稀的主网格点，实际吸附步长仍由文档设置决定。
            while step * scale < 6 and scale > 0:
                step *= 2
            size = max(2, round(step * scale))
            if self._grid_key != (step, size):
                tile = QPixmap(size, size)
                tile.fill(Qt.GlobalColor.transparent)
                tile_painter = QPainter(tile)
                try:
                    tile_painter.setPen(QColor("#e0e3de"))
                    tile_painter.drawPoint(0, 0)
                finally:
                    tile_painter.end()
                self._grid_brush = QBrush(tile)
                self._grid_brush.setTransform(QTransform.fromScale(step / size, step / size))
                self._grid_key = (step, size)
            # 固定小纹理重复填充，避免每帧分配成千上万个网格点。
            painter.fillRect(area, self._grid_brush)


class NodeItem(QGraphicsPixmapItem):
    def __init__(self, node_id: str, parent: QGraphicsItem) -> None:
        super().__init__(parent)
        self.node_id = node_id
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        # 小比例查看时平滑采样原生缓存，避免中文笔画被最近邻缩放截断。
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.content_layer = QGraphicsRectItem(self)
        self.content_layer.setPen(QPen(Qt.PenStyle.NoPen))
        self.content_layer.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.content_layer.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.content_layer.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)


class CanvasRenderer:
    def __init__(self, scene: QGraphicsScene, registry: WidgetRegistry) -> None:
        self.scene = scene
        self.tree = RuntimeTree(registry)
        self.frame = WindowFrame()
        scene.addItem(self.frame)
        self.surface = CanvasSurface()
        scene.addItem(self.surface)
        self.central_clip = QGraphicsRectItem(self.surface)
        self.central_clip.setPen(QPen(Qt.PenStyle.NoPen))
        self.central_clip.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.central_clip.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.central_clip.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.empty_hint = QGraphicsRectItem(self.surface)
        self.empty_hint.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.empty_hint.setPen(QPen(Qt.PenStyle.NoPen))
        self.empty_hint.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        hint_title = QGraphicsSimpleTextItem("从组件箱拖入控件", self.empty_hint)
        hint_title.setFont(QFont("Microsoft YaHei UI", 10))
        hint_title.setBrush(QColor("#788174"))
        hint_title.setPos(-hint_title.boundingRect().width() / 2, -hint_title.boundingRect().height() / 2)
        self.items: dict[str, NodeItem] = {}
        self.plan: BuildPlan | None = None
        self.ratio = 0.0
        self._pending_images: set[str] = set()
        self.tray_label = QGraphicsSimpleTextItem("非可视组件（仅运行时生效）")
        self.tray_label.setBrush(QColor(MUTED))
        scene.addItem(self.tray_label)

    def apply(self, plan: BuildPlan, canvas: FrozenMap, ratio: float) -> None:
        for _ in self.apply_steps(plan, canvas, ratio):
            pass

    def apply_steps(self, plan: BuildPlan, canvas: FrozenMap, ratio: float) -> Iterator[None]:
        yield from self.tree.apply_steps(plan)
        central = self.tree.root.centralWidget()
        self.central_clip.setRect(QRectF(central.geometry()))
        dirty = set(self.tree.last_dirty)
        if ratio != self.ratio:
            dirty.update(self.tree.widgets)
        self.ratio = ratio
        wanted = {node.id for node in plan.nodes if node.slot in {"children", "pages", "non_visual", "tool_bar", "status_bar", "menu_bar", "dock"} and node.id in self.tree.widgets}
        # 原生属性可能已经应用，失败的缓存仍须在下一次刷新时重试。
        self._pending_images.intersection_update(wanted)
        self._pending_images.update(dirty & wanted)
        removed = set(self.items) - wanted
        # 先解除所有待删除父子图元的归属，避免释放父图元时顺带销毁仍有引用的子图元。
        previous_nodes = {node.id: node for node in self.plan.nodes} if self.plan else {}
        for key, item in self.items.items():
            if key in removed or (key in previous_nodes and previous_nodes[key].parent_id in removed):
                item.setParentItem(self.surface)
        for key in removed:
            item = self.items.pop(key)
            item.setParentItem(None)
            self.scene.removeItem(item)
        for node in plan.nodes:
            if node.id not in wanted:
                continue
            if node.id not in self.items:
                self.items[node.id] = NodeItem(node.id, self.surface)
                self._pending_images.add(node.id)
            item = self.items[node.id]
            parent_item = self.items.get(node.parent_id)
            parent = (parent_item.content_layer if parent_item else self.central_clip if node.slot == "children"
                      else self.surface if node.slot != "non_visual" else None)
            if item.parentItem() is not parent:
                item.setParentItem(parent)
                if parent is None and item.scene() is None:
                    self.scene.addItem(item)
            item.setTransform(QTransform())
            widget = self.tree.widgets[node.id]
            if node.slot == "non_visual":
                index = sum(other.slot == "non_visual" for other in plan.nodes[:plan.nodes.index(node)])
                columns = max(1, self.tree.root.width() // 184)
                item.setPos((index % columns) * 184, self.tree.root.height() + 40 + (index // columns) * 44)
                pixmap = QPixmap(176, 36)
                pixmap.fill(QColor("#f1f3f4"))
                painter = QPainter(pixmap)
                painter.setPen(QColor("#b9c0c3"))
                painter.drawRect(0, 0, 175, 35)
                painter.setPen(QColor("#30373b"))
                painter.drawText(pixmap.rect().adjusted(8, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter, node.name)
                painter.end()
                item.setPixmap(pixmap)
                item.setVisible(not node.designer_hidden)
                item.setZValue(10)
                self._pending_images.discard(node.id)
                continue
            if parent_item:
                position = widget.mapTo(self.tree.widgets[node.parent_id], QPoint())
                item.setPos(QPointF(position) - parent_item.content_layer.pos())
            else:
                item.setPos(QPointF(widget.mapTo(self.tree.root, QPoint())))
            area = content_rect(widget)
            item.content_layer.setPos(area.x(), area.y())
            item.content_layer.setRect(0, 0, area.width(), area.height())
            item.setZValue(float(node.stack_order or 0))
            visible = not node.designer_hidden
            if node.slot == "pages":
                parent_widget = self.tree.widgets[node.parent_id]
                current = parent_widget.tab_bar.currentIndex() if hasattr(parent_widget, "tab_bar") else parent_widget.currentIndex()
                visible = visible and parent_widget.pages.index(widget) == current
            if node.slot in {"menu_bar", "tool_bar", "status_bar", "dock"}:
                visible = visible and node.properties.get("visible", True)
            item.setVisible(visible)
            # 窗口条和页面的尺寸由父级管理，仍须按真实像素尺寸使缓存失效。
            pixmap = item.pixmap()
            if pixmap.width() != max(1, round(widget.width() * ratio)) or pixmap.height() != max(1, round(widget.height() * ratio)):
                self._pending_images.add(node.id)
            if node.id in self._pending_images:
                item.setPixmap(QPixmap.fromImage(self.tree.image(node.id, ratio)))
                self._pending_images.discard(node.id)
            yield None
        root = self.tree.root
        self.frame.configure(root)
        self.surface.setRect(0, 0, root.width(), root.height())
        self.empty_hint.setPos(self.surface.rect().center())
        self.empty_hint.setVisible(not any(node.slot == "children" for node in plan.nodes))
        self.surface.setBrush(root.centralWidget().palette().color(QPalette.ColorRole.Window))
        self.surface.grid_size = canvas["grid_size"]
        self.surface.show_grid = canvas["show_grid"]
        self.surface.update()
        count = sum(node.slot == "non_visual" for node in plan.nodes)
        self.tray_label.setVisible(bool(count))
        self.tray_label.setPos(0, root.height() + 16)
        tray_height = 40 + ((count + max(1, root.width() // 184) - 1) // max(1, root.width() // 184)) * 44 if count else 0
        self.scene.setSceneRect(self.frame.rect().adjusted(-20, -20, 20, 20 + tray_height))
        self.plan = plan

    def node_rect(self, node_id: str) -> QRectF:
        if node_id in self.items:
            return self.items[node_id].sceneBoundingRect()
        if self.plan and node_id == self.plan.nodes[0].id:
            return self.frame.rect()
        return self.surface.sceneBoundingRect()

    def dispose(self) -> None:
        self.tree.dispose()
        self.items.clear()
        self._pending_images.clear()
        self.scene.clear()
