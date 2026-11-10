"""选择、框选、拖放与批量移动；手势期间只更新图元位置。"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from time import perf_counter

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import (
    QColor, QContextMenuEvent, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent,
    QKeyEvent, QMouseEvent, QPen, QShowEvent, QTransform, QWheelEvent,
)
from PySide6.QtWidgets import QApplication, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QWidget

from core.build_plan import BuildPlan, compile_plan, preview_window_resize
from core.commands.nodes import create_node, move_node, resize_node
from core.commands.arrange import bounding_rect, constrain_delta, delete_nodes, editable_siblings, move_nodes
from core.document import ChangeSet, DocumentSession
from core.deferred import defer
from core.errors import DesignerError, require
from core.models import ProjectModel, Rect
from core.hierarchy import ancestors, content_origin, content_size, selected_roots
from layout.containers import managed_child
from resources.colors import ACCENT, CANVAS
from .mime import component_type
from .renderer import CanvasRenderer, NodeItem
from .geometry import resized_rect
from .selection import HANDLE_CURSORS, ResizeHandle, SelectionAdornments

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MoveGesture:
    node_id: str
    press: QPoint
    scene_press: QPointF
    original: Rect
    original_display: QPointF
    revision: int
    target: tuple[int, int]
    moving: bool = False


@dataclass(slots=True)
class ResizeGesture:
    node_id: str
    handle: str
    press: QPoint
    scene_press: QPointF
    original: Rect
    original_display: QPointF
    revision: int
    target: Rect
    root: bool
    moving: bool = False
    preview_applied: bool = False
    base_plan: BuildPlan | None = None


@dataclass(slots=True)
class GroupMoveGesture:
    keys: tuple[str, ...]
    press: QPoint
    scene_press: QPointF
    originals: dict[str, QPointF]
    bounds: Rect
    area: tuple[int, int]
    revision: int
    delta: tuple[int, int] = (0, 0)
    moving: bool = False


@dataclass(slots=True)
class MarqueeGesture:
    press: QPoint
    start: QPointF
    previous: tuple[str, ...]
    primary: str
    additive: bool
    revision: int
    area: QRectF
    moving: bool = False


class DesignerCanvas(QGraphicsView):
    notice = Signal(str)
    error = Signal(str)
    zoom_changed = Signal(int)
    context_requested = Signal(object, object)
    menu_edit_requested = Signal()

    def __init__(self, document: DocumentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document = document
        self.before_interaction: Callable[[], bool] | None = None
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QColor(CANVAS))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.renderer = CanvasRenderer(self._scene, document.registry)
        self.selection = QGraphicsRectItem()
        pen = QPen(QColor(ACCENT), 1)
        pen.setCosmetic(True)
        self.selection.setPen(pen)
        self.selection.setZValue(1_000_000)
        self.selection.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(self.selection)
        self.adornments = SelectionAdornments(self.selection)
        self.drop_outline = QGraphicsRectItem()
        drop_pen = QPen(QColor(ACCENT), 1, Qt.PenStyle.DashLine)
        drop_pen.setCosmetic(True)
        self.drop_outline.setPen(drop_pen)
        self.drop_outline.setZValue(1_000_001)
        self.drop_outline.hide()
        self._scene.addItem(self.drop_outline)
        self._gesture: MoveGesture | None = None
        self._resize: ResizeGesture | None = None
        self._group: GroupMoveGesture | None = None
        self._marquee: MarqueeGesture | None = None
        self._selection_items: list[QGraphicsRectItem] = []
        self._zoom = 100
        self._fit_pending = False
        self._origin_pending = False
        self._view_initialized = False
        self._disposed = False
        self._ready = False
        self._candidate: CanvasRenderer | None = None
        self._steps: Iterator[None] | None = None
        self._build_timer = QTimer(self)
        self._build_timer.setSingleShot(True)
        self._build_timer.timeout.connect(self._advance_build)
        self.build_batch_times: list[float] = []
        self._unsubscribe = document.subscribe(self._changed)
        document.selection_changed.connect(self._select)
        document.status_changed.connect(self._status_changed)
        try:
            self.refresh()
        except Exception:
            self.dispose()
            raise

    @property
    def zoom(self) -> int:
        return self._zoom

    @property
    def gesture_active(self) -> bool:
        return any(value is not None for value in (self._gesture, self._resize, self._group, self._marquee))

    @property
    def ready(self) -> bool:
        return self._ready

    def refresh(self) -> None:
        plan = compile_plan(self.document.model, self.document.registry, self.document.state_id, allow_unknown=True)
        ratio = self.viewport().devicePixelRatioF() * max(1, self._zoom / 100)
        if not self._ready and len(plan.nodes) > 100:
            self._start_build(plan, ratio)
            return
        self.renderer.apply(plan, self.document.model.data["canvas"], ratio)
        self._ready = True
        self._select(self.document.selected_id)
        if plan.diagnostics:
            self.notice.emit("；".join(plan.diagnostics))

    def _start_build(self, plan: BuildPlan, ratio: float) -> None:
        self._cancel_build()
        self.document.editing_suspended = True
        scene = QGraphicsScene(self)
        self._candidate = CanvasRenderer(scene, self.document.registry)
        self._steps = self._candidate.apply_steps(plan, self.document.model.data["canvas"], ratio)
        self.build_batch_times.clear()
        self.notice.emit("正在准备画布，完成后即可编辑；关闭标签可取消。")
        self.document.status_changed.emit()
        self._build_timer.start(0)

    def _advance_build(self) -> None:
        if self._disposed or self._steps is None:
            return
        started = perf_counter()
        try:
            # 为单个 Qt 操作及最终发布预留时间，整个批次目标为八毫秒。
            while perf_counter() - started < 0.006:
                next(self._steps)
        except StopIteration:
            candidate = self._candidate
            self._steps, self._candidate = None, None
            previous = self.renderer
            previous.scene.removeItem(self.selection)
            previous.scene.removeItem(self.drop_outline)
            candidate.scene.addItem(self.selection)
            candidate.scene.addItem(self.drop_outline)
            self.renderer, self._scene = candidate, candidate.scene
            self.setScene(self._scene)
            previous.dispose()
            previous.scene.deleteLater()
            self._ready = True
            self.document.editing_suspended = False
            self._select(self.document.selected_id)
            if self._fit_pending:
                self.fit_to_window()
            elif self._origin_pending:
                self._scroll_to_origin()
            self.document.status_changed.emit()
            self.notice.emit("画布已就绪，可以开始编辑。")
        except Exception as exc:
            logger.exception("分批构建画布失败，未发布部分控件树。")
            self._cancel_build()
            self.document.editing_suspended = True
            self.document.status_changed.emit()
            self.error.emit(str(exc) if isinstance(exc, DesignerError) else "画布构建失败，文档数据仍保留，可保存后重新打开。")
        else:
            self._build_timer.start(0)
        finally:
            self.build_batch_times.append((perf_counter() - started) * 1000)

    def _cancel_build(self) -> None:
        self._build_timer.stop()
        if self._steps is not None:
            self._steps.close()
            self._steps = None
        if self._candidate:
            self._candidate.dispose()
            self._candidate.scene.deleteLater()
            self._candidate = None
        self.document.editing_suspended = False

    def _changed(self, change: ChangeSet) -> None:
        self.cancel_gesture()
        try:
            self.refresh()
        except Exception as exc:
            logger.exception("画布刷新失败，文档数据仍然有效。")
            self.error.emit(str(exc) if isinstance(exc, DesignerError) else "画布刷新失败，请保存项目后重新打开。")

    def _select(self, node_id: str) -> None:
        if self._disposed:
            return
        if not self._ready:
            self.selection.hide()
            return
        if self._marquee and (self._marquee.previous != self.document.selected_ids or self._marquee.primary != node_id):
            self._marquee = None
            self.drop_outline.hide()
        if self._group and self._group.keys != self.document.selected_ids:
            self.cancel_gesture()
        for item in self._selection_items:
            item.hide()
        if len(self.document.selected_ids) > 1:
            if self._gesture or self._resize:
                self.cancel_gesture()
            rectangles = [(key, self.renderer.node_rect(key)) for key in self.document.selected_ids
                          if key in self.renderer.items and self.renderer.items[key].isVisible()]
            if not rectangles:
                self.selection.hide()
                return
            combined = QRectF(rectangles[0][1])
            for index, (key, rect) in enumerate(rectangles):
                combined = combined.united(rect)
                if index == len(self._selection_items):
                    outline = QGraphicsRectItem(self.selection)
                    outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                    self._selection_items.append(outline)
                outline = self._selection_items[index]
                pen = QPen(QColor(ACCENT), 2 if key == node_id else 1)
                pen.setCosmetic(True)
                outline.setPen(pen)
                outline.setRect(rect)
                outline.show()
            self.adornments.update(combined, None, root=False, editable=False, zoom=self._zoom)
            self.selection.show()
            return
        gesture = self._resize or self._gesture
        if gesture and gesture.node_id != node_id:
            self.cancel_gesture()
        node = self.document.model.nodes.get(node_id)
        if node is None:
            self.selection.hide()
            return
        geometry = node.geometry
        if self._resize:
            geometry = self._resize.target
        elif self._gesture and geometry:
            x, y = self._gesture.target
            geometry = Rect(x, y, geometry.width, geometry.height)
        display_rect = self.renderer.node_rect(node_id)
        if self._resize and node_id in self.renderer.items and self.document.registry.require(node.type_id).can_contain:
            display_rect = QRectF(self.renderer.items[node_id].scenePos().x(), self.renderer.items[node_id].scenePos().y(),
                                  geometry.width, geometry.height)
        self.adornments.update(display_rect, geometry,
                               root=node.slot == "root", editable=self._can_resize(node_id), zoom=self._zoom,
                               moving=bool((self._resize and self._resize.moving) or (self._gesture and self._gesture.moving)))
        self.selection.setVisible(node_id not in self.renderer.items or self.renderer.items[node_id].isVisible())

    def _can_resize(self, node_id: str) -> bool:
        node = self.document.model.nodes.get(node_id)
        return bool(node and node.geometry and node.slot in {"root", "children"} and not managed_child(self.document.model, node_id) and
                    not any(self.document.model.nodes[key].designer["locked"] for key in (node_id, *ancestors(self.document.model, node_id)))
                    and not self.document.read_only and
                    not self.document.editing_suspended and not self.document.closed)

    def _status_changed(self) -> None:
        if self._disposed:
            return
        if self.document.read_only or self.document.editing_suspended:
            self.cancel_gesture()
        self._select(self.document.selected_id)

    def _handle_at(self, point: QPoint) -> ResizeHandle | None:
        if len(self.document.selected_ids) != 1 or not self._can_resize(self.document.selected_id):
            return None
        return next((item for item in self.items(point) if isinstance(item, ResizeHandle) and item.isVisible()), None)

    def set_zoom(self, percent: int) -> None:
        if self._disposed:
            return
        self.cancel_gesture()
        self._fit_pending = False
        previous_zoom, previous_transform = self._zoom, self.transform()
        origin = self.mapToScene(QPoint())
        self._zoom = max(25, min(300, percent))
        self.setTransform(QTransform.fromScale(self._zoom / 100, self._zoom / 100))
        try:
            self.refresh()
            self._place_scene_point(origin, QPoint())
        except Exception as exc:
            logger.exception("画布缩放失败，正在恢复原比例。")
            self._zoom = previous_zoom
            self.setTransform(previous_transform)
            self._place_scene_point(origin, QPoint())
            try:
                self.refresh()
            except Exception:
                logger.exception("恢复画布缓存失败，文档数据仍然保留。")
            message = str(exc) if isinstance(exc, DesignerError) else "画布缩放失败，详细原因已写入诊断日志。"
            self.error.emit(message)
        self.zoom_changed.emit(self._zoom)

    def _place_scene_point(self, position: QPointF, target: QPoint) -> None:
        """通过滚动保持查看位置；靠近场景边缘时交由滚动范围约束。"""
        offset = self.mapFromScene(position) - target
        horizontal, vertical = self.horizontalScrollBar(), self.verticalScrollBar()
        horizontal.setValue(horizontal.value() + offset.x())
        vertical.setValue(vertical.value() + offset.y())

    def _scroll_to_origin(self) -> None:
        if self._disposed:
            return
        if not self._ready:
            self._origin_pending = True
            return
        self._origin_pending = False
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().minimum())
        self.verticalScrollBar().setValue(self.verticalScrollBar().minimum())

    def reset_view(self) -> None:
        """恢复原始大小和窗口起点，不修改项目尺寸或撤销历史。"""
        self.set_zoom(100)
        self._scroll_to_origin()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._view_initialized:
            self._view_initialized = True
            # 首次定位只改变滚动位置，绝不按布局过程中的临时尺寸缩小窗口。
            defer(self, self._scroll_to_origin)

    def fit_to_window(self) -> None:
        if self._disposed:
            return
        if not self._ready:
            self._fit_pending = True
            return
        self._fit_pending = False
        area = self.sceneRect()
        scale = min((self.viewport().width() - 4) / max(1, area.width()),
                    (self.viewport().height() - 4) / max(1, area.height()))
        self.set_zoom(min(100, math.floor(scale * 100)))
        self._scroll_to_origin()

    def _snap(self, x: float, y: float, width: int, height: int, parent_id: str | None = None) -> tuple[int, int]:
        settings = self.document.model.data["canvas"]
        step = settings["grid_size"] if settings["snap_to_grid"] else 1
        left, top = math.floor(x / step + 0.5) * step, math.floor(y / step + 0.5) * step
        area = content_size(self.document.model, parent_id or self.document.model.central_id)
        return max(0, min(left, max(0, area[0] - width))), max(0, min(top, max(0, area[1] - height)))

    def container_at(self, position: QPointF) -> str:
        """按实际层叠命中可用容器；被其他控件遮挡的容器不能接收拖放。"""
        for item in self.scene().items(position):
            if isinstance(item, NodeItem):
                key = item.node_id
                if self.document.model.nodes[key].slot in {"non_visual", "tool_bar", "status_bar", "menu_bar", "menu"}:
                    return self.document.model.central_id
                spec = self.document.registry.get(self.document.model.nodes[key].type_id)
                if spec and spec.can_contain and item.content_layer.contains(item.content_layer.mapFromScene(position)):
                    from core.hierarchy import active_page
                    return active_page(self.document.model, key)
                return self.document.model.nodes[key].parent_id
        return self.document.model.central_id

    def _content_origin(self, parent_id):
        from runtime.advanced_widgets import content_host
        widget = self.renderer.tree.widgets.get(parent_id)
        if widget is not None and content_host(widget) is not widget:
            host = content_host(widget)
            position = host.mapTo(self.renderer.tree.root, host.contentsRect().topLeft())
            return position.x(), position.y()
        item = self.renderer.items.get(parent_id)
        if item is not None:
            position = item.content_layer.mapToScene(QPointF())
            return position.x(), position.y()
        if parent_id == self.document.model.central_id:
            area = self.renderer.tree.root.centralWidget().geometry()
            return area.x(), area.y()
        return content_origin(self.document.model, parent_id)

    def _drop_geometry(self, type_id: str, position: QPointF) -> tuple[str, int, int, int, int]:
        parent_id = self.container_at(position)
        spec = self.document.registry.require(type_id)
        width, height = spec.default_size
        if spec.slot != "children":
            return self.document.model.central_id, 0, 0, width, height
        area = content_size(self.document.model, parent_id)
        require(width <= area[0] and height <= area[1], "目标容器放不下该组件，请先扩大容器或放到工作区。")
        ox, oy = self._content_origin(parent_id)
        x, y = self._snap(position.x() - ox, position.y() - oy, width, height, parent_id)
        return parent_id, x, y, width, height

    def create_component(self, type_id: str, position: QPointF | None = None, *, parent_id: str | None = None) -> str | None:
        self.cancel_gesture()
        if not self.prepare_interaction():
            return None
        try:
            spec = self.document.registry.require(type_id)
            width, height = spec.default_size
            if spec.slot == "pages":
                parent_id = parent_id or (self.container_at(position) if position is not None else self.document.selected_id)
                x, y = 0, 0
            elif spec.slot != "children":
                parent_id, x, y = self.document.model.root_id, 0, 0
            elif parent_id is not None:
                from core.hierarchy import active_page
                parent_id = active_page(self.document.model, parent_id)
                position = position or QPointF()
                ox, oy = self._content_origin(parent_id)
                x, y = self._snap(position.x() - ox, position.y() - oy, width, height, parent_id)
            elif position is None:
                center = self.mapToScene(self.viewport().rect().center())
                position = center - QPointF(width / 2, height / 2)
                parent_id = self.document.model.central_id
                ox, oy = self._content_origin(parent_id)
                x, y = self._snap(position.x() - ox, position.y() - oy, width, height)
            else:
                parent_id, x, y, width, height = self._drop_geometry(type_id, position)
            created: list[str] = []

            def transform(model: ProjectModel) -> ProjectModel:
                updated, node_id = create_node(model, self.document.registry, type_id, x, y, parent_id=parent_id)
                created.append(node_id)
                return updated

            self.document.execute(f"创建{spec.label}", transform)
            self.document.select(created[0])
            self.notice.emit(f"已创建{spec.label}，可在属性面板编辑；非可视组件在画布下方选择。")
            self.setFocus()
            return created[0]
        except DesignerError as exc:
            self.error.emit(str(exc))
            return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._ready:
            event.accept()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            event.accept()
            return
        if not self.prepare_interaction():
            event.accept()
            return
        self.setFocus()
        self.cancel_gesture()
        point = event.position().toPoint()
        handle = self._handle_at(point)
        if handle is not None:
            node = self.document.model.nodes[self.document.selected_id]
            self._resize = ResizeGesture(node.id, handle.name, point, self.mapToScene(point), node.geometry,
                                          (QPointF(self.renderer.items[node.id].pos()) if node.id in self.renderer.items else QPointF()), self.document.revision,
                                          node.geometry, node.slot == "root")
            self.viewport().setCursor(HANDLE_CURSORS[handle.name])
            event.accept()
            return
        hit = next((item for item in self.items(point) if isinstance(item, NodeItem)), None)
        node_id = hit.node_id if hit else self.document.model.root_id
        if hit and self.document.model.nodes[node_id].type_id == "builtin.tab_widget":
            widget = self.renderer.tree.widgets[node_id]
            local = hit.mapFromScene(self.mapToScene(point)).toPoint()
            bar_point = widget.tab_bar.mapFrom(widget, local)
            index = widget.tab_bar.tabAt(bar_point)
            if not widget.tab_bar.isHidden() and widget.tab_bar.rect().contains(bar_point) and 0 <= index < widget.tab_bar.count():
                try:
                    from core.commands.pages import select_page
                    self.document.execute("切换选择夹页面", lambda model: select_page(model, self.document.registry, node_id, index))
                    self.document.select(node_id)
                except DesignerError as exc:
                    self.error.emit(str(exc))
                event.accept()
                return
        multiple = bool(event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier))
        if hit and multiple:
            keys = tuple(key for key in self.document.selected_ids if self.document.model.nodes[key].slot == "children")
            self.document.select_many(tuple(key for key in keys if key != node_id) if node_id in keys else (*keys, node_id))
            event.accept()
            return
        if not hit and self.renderer.surface.rect().contains(self.mapToScene(point)):
            self._marquee = MarqueeGesture(point, self.mapToScene(point), self.document.selected_ids,
                                           self.document.selected_id, multiple, self.document.revision, QRectF())
            event.accept()
            return
        if node_id not in self.document.selected_ids:
            self.document.select(node_id)
        elif len(self.document.selected_ids) > 1:
            self.document.select_many(self.document.selected_ids, primary=node_id)
        if hit and len(self.document.selected_ids) > 1:
            if not self.document.read_only and not self.document.editing_suspended:
                try:
                    nodes = editable_siblings(self.document.model, self.document.selected_ids)
                    parent = self.renderer.tree.widgets[nodes[0].parent_id]
                    area = parent.contentsRect()
                    self._group = GroupMoveGesture(self.document.selected_ids, point, self.mapToScene(point),
                        {key: QPointF(self.renderer.items[key].pos()) for key in self.document.selected_ids},
                        bounding_rect(tuple(node.geometry for node in nodes)), (area.width(), area.height()), self.document.revision)
                except DesignerError as exc:
                    self.notice.emit(str(exc))
            event.accept()
            return
        node = self.document.model.nodes[node_id]
        if hit and self._can_resize(node_id):
            self._gesture = MoveGesture(node_id, point, self.mapToScene(point), node.geometry,
                                        QPointF(hit.pos()), self.document.revision, (node.geometry.x, node.geometry.y))
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._marquee:
            self._marquee_move(event)
            return
        if self._group:
            self._group_move(event)
            return
        if self._resize:
            self._resize_move(event)
            return
        gesture = self._gesture
        if gesture is None:
            handle = self._handle_at(event.position().toPoint()) if self._ready else None
            self.viewport().setCursor(HANDLE_CURSORS[handle.name] if handle else Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton) or gesture.revision != self.document.revision:
            self.cancel_gesture()
            event.accept()
            return
        if (event.position().toPoint() - gesture.press).manhattanLength() < QApplication.startDragDistance() and not gesture.moving:
            return
        gesture.moving = True
        delta = self.mapToScene(event.position().toPoint()) - gesture.scene_press
        old = gesture.original
        x, y = self._snap(old.x + delta.x(), old.y + delta.y(), old.width, old.height,
                          self.document.model.nodes[gesture.node_id].parent_id)
        gesture.target = (x, y)
        item = self.renderer.items[gesture.node_id]
        item.setPos(gesture.original_display + QPointF(x - old.x, y - old.y))
        self._select(gesture.node_id)
        self.notice.emit(f"正在移动，位置（{x}，{y}）；松开提交，按退出键取消。")
        event.accept()

    def _marquee_move(self, event: QMouseEvent) -> None:
        gesture = self._marquee
        if not event.buttons() & Qt.MouseButton.LeftButton or gesture.revision != self.document.revision:
            self.cancel_gesture()
            return
        if not gesture.moving and (event.position().toPoint() - gesture.press).manhattanLength() < QApplication.startDragDistance():
            return
        gesture.moving = True
        gesture.area = QRectF(gesture.start, self.mapToScene(event.position().toPoint())).normalized().intersected(self.renderer.surface.rect())
        self.drop_outline.setRect(gesture.area)
        self.drop_outline.show()
        self.notice.emit("拖动框选完整包含的控件；按住控制键或上档键可追加选择，按退出键取消。")
        event.accept()

    def _group_move(self, event: QMouseEvent) -> None:
        gesture = self._group
        if not event.buttons() & Qt.MouseButton.LeftButton or gesture.revision != self.document.revision:
            self.cancel_gesture()
            return
        if not gesture.moving and (event.position().toPoint() - gesture.press).manhattanLength() < QApplication.startDragDistance():
            return
        gesture.moving = True
        delta = self.mapToScene(event.position().toPoint()) - gesture.scene_press
        settings = self.document.model.data["canvas"]
        step = settings["grid_size"] if settings["snap_to_grid"] and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
        dx, dy = constrain_delta(gesture.bounds, delta.x(), delta.y(), gesture.area, step=step)
        gesture.delta = dx, dy
        for key, original in gesture.originals.items():
            self.renderer.items[key].setPos(original + QPointF(dx, dy))
        self._select(self.document.selected_id)
        self.notice.emit(f"正在移动 {len(gesture.keys)} 个控件，偏移（{dx}，{dy}）；松开提交，按退出键取消。")
        event.accept()

    def _resize_move(self, event: QMouseEvent) -> None:
        gesture = self._resize
        if gesture is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton) or gesture.revision != self.document.revision:
            self.cancel_gesture()
            event.accept()
            return
        if (event.position().toPoint() - gesture.press).manhattanLength() < QApplication.startDragDistance() and not gesture.moving:
            return
        gesture.moving = True
        delta = self.mapToScene(event.position().toPoint()) - gesture.scene_press
        settings = self.document.model.data["canvas"]
        snap = settings["snap_to_grid"] and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        parent_id = self.document.model.nodes[gesture.node_id].parent_id
        area = content_size(self.document.model, parent_id or self.document.model.central_id)
        target = resized_rect(gesture.original, gesture.handle, delta.x(), delta.y(),
                              step=settings["grid_size"] if snap else 1,
                              bounds=area, root=gesture.root)
        if target == gesture.target:
            event.accept()
            return
        gesture.target = target
        if gesture.root:
            if self.document.model.nodes[gesture.node_id].properties.get("scale_children", False):
                try:
                    if gesture.base_plan is None:
                        gesture.base_plan = self.renderer.plan
                    require(gesture.base_plan is not None, "窗口缩放预览尚未准备好。")
                    plan = preview_window_resize(gesture.base_plan, target)
                    gesture.preview_applied = True
                    self.renderer.apply(plan, self.document.model.data["canvas"], self.renderer.ratio)
                except Exception as exc:
                    logger.exception("组件跟随窗口的临时预览失败。")
                    self.cancel_gesture()
                    self.error.emit(str(exc) if isinstance(exc, DesignerError) else "组件缩放预览失败，已恢复原尺寸。")
                    event.accept()
                    return
            else:
                self.renderer.frame.preview_size(target.width, target.height)
                self.renderer.surface.setRect(0, 0, target.width, target.height)
                self.renderer.empty_hint.setPos(self.renderer.surface.rect().center())
        else:
            item = self.renderer.items[gesture.node_id]
            item.setPos(gesture.original_display + QPointF(target.x - gesture.original.x, target.y - gesture.original.y))
            spec = self.document.registry.require(self.document.model.nodes[gesture.node_id].type_id)
            if not spec.can_contain:
                item.setTransform(QTransform.fromScale(target.width / gesture.original.width, target.height / gesture.original.height))
        self._select(gesture.node_id)
        self.notice.emit(f"正在调整尺寸：宽 {target.width}，高 {target.height}；松开提交，按退出键取消。")
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            event.accept()
            return
        if self._marquee:
            gesture, self._marquee = self._marquee, None
            self.drop_outline.hide()
            if gesture.revision == self.document.revision:
                if gesture.moving:
                    keys = tuple(key for key, item in self.renderer.items.items() if item.isVisible()
                                 and gesture.area.contains(self.renderer.node_rect(key)))
                    selected = (*gesture.previous, *keys) if gesture.additive else keys
                    selected = tuple(key for key in selected if self.document.model.nodes[key].slot == "children")
                    self.document.select_many(selected_roots(self.document.model, selected))
                    self.notice.emit(f"已框选 {len(set(selected))} 个控件。")
                elif not gesture.additive:
                    self.document.select(self.document.model.root_id)
            event.accept()
            return
        if self._group:
            gesture = self._group
            self.cancel_gesture()
            if gesture.moving:
                try:
                    self.document.execute("移动多个控件", lambda model: move_nodes(model, gesture.keys, *gesture.delta),
                                          expected_revision=gesture.revision)
                except DesignerError as exc:
                    self.error.emit(str(exc))
            event.accept()
            return
        if self._resize:
            gesture = self._resize
            retain_preview = gesture.moving and gesture.root and gesture.preview_applied
            if retain_preview:
                # 成功提交可直接沿用已绘制的候选画面，失败时再还原。
                self._resize = None
                self.drop_outline.hide()
                self.viewport().unsetCursor()
            else:
                self.cancel_gesture()
            if gesture.moving:
                try:
                    if not gesture.root:
                        ratio = self.renderer.ratio
                        require(round(gesture.target.width * ratio) * round(gesture.target.height * ratio) <= 16_777_216,
                                "控件绘制尺寸过大，请缩小控件或画布缩放比例。")
                    self.document.execute("调整窗口尺寸" if gesture.root else "调整控件尺寸",
                                          lambda model: resize_node(model, gesture.node_id, gesture.target),
                                          expected_revision=gesture.revision)
                    self.notice.emit(f"尺寸已更新：宽 {gesture.target.width}，高 {gesture.target.height}。")
                except DesignerError as exc:
                    if retain_preview:
                        self.refresh()
                    self.error.emit(str(exc))
                except Exception:
                    if retain_preview:
                        self.refresh()
                    logger.exception("调整尺寸失败，已取消临时预览。")
                    self.error.emit("调整尺寸失败，详细原因已写入诊断日志。")
            self._select(self.document.selected_id)
            event.accept()
            return
        gesture = self._gesture
        self._gesture = None
        if gesture and gesture.moving:
            x, y = gesture.target
            try:
                self.document.execute("移动控件", lambda model: move_node(model, gesture.node_id, x, y),
                                      expected_revision=gesture.revision)
            except DesignerError as exc:
                self.refresh()
                self.error.emit(str(exc))
        self._select(self.document.selected_id)
        event.accept()

    def cancel_gesture(self) -> None:
        if self._disposed:
            return
        self._marquee = None
        if self._group:
            gesture, self._group = self._group, None
            for key, position in gesture.originals.items():
                item = self.renderer.items.get(key)
                if item:
                    item.setPos(position)
            self._select(self.document.selected_id)
        if self._resize:
            gesture, self._resize = self._resize, None
            if gesture.root:
                if gesture.preview_applied:
                    self.refresh()
                else:
                    self.renderer.frame.preview_size(gesture.original.width, gesture.original.height)
                    self.renderer.surface.setRect(0, 0, gesture.original.width, gesture.original.height)
                    self.renderer.empty_hint.setPos(self.renderer.surface.rect().center())
            else:
                item = self.renderer.items.get(gesture.node_id)
                if item:
                    item.setTransform(QTransform())
                    item.setPos(gesture.original_display)
            self._select(self.document.selected_id)
        if self._gesture:
            item = self.renderer.items.get(self._gesture.node_id)
            if item:
                item.setPos(self._gesture.original_display)
            self._gesture = None
            self._select(self.document.selected_id)
        self.drop_outline.hide()
        self.viewport().unsetCursor()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self._ready and not self._disposed and event.button() == Qt.MouseButton.LeftButton:
            key = self.node_at(event.position().toPoint())
            if self.document.model.nodes[key].slot == "menu_bar":
                self.cancel_gesture()
                self.menu_edit_requested.emit()
                event.accept()
                return
        self.mousePressEvent(event)

    def node_at(self, point: QPoint) -> str:
        handle = self._handle_at(point)
        if handle is not None:
            return self.document.selected_id
        hit = next((item for item in self.items(point) if isinstance(item, NodeItem)), None)
        return hit.node_id if hit else self.document.model.root_id

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self._ready and not self._disposed:
            keyboard = event.reason() == QContextMenuEvent.Reason.Keyboard
            position = None if keyboard else event.pos()
            global_position = (self.viewport().mapToGlobal(self.mapFromScene(
                self.renderer.node_rect(self.document.selected_id).center())) if keyboard else event.globalPos())
            self.context_requested.emit(position, global_position)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_gesture()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.key() in {Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down}:
            self._nudge(event.key(), bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def _nudge(self, key: int, accelerated: bool) -> None:
        self.cancel_gesture()
        if not self.prepare_interaction():
            return
        if len(self.document.selected_ids) > 1:
            try:
                keys = self.document.selected_ids
                nodes = editable_siblings(self.document.model, keys)
                parent = self.renderer.tree.widgets[nodes[0].parent_id].contentsRect()
                dx, dy = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                          Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}[key]
                step = 10 if accelerated else 1
                delta = constrain_delta(bounding_rect(tuple(node.geometry for node in nodes)), dx * step, dy * step,
                                          (parent.width(), parent.height()))
                self.document.execute("微调多个控件", lambda model: move_nodes(model, keys, *delta))
            except DesignerError as exc:
                self.error.emit(str(exc))
            return
        node = self.document.model.nodes[self.document.selected_id]
        if node.slot != "children" or not self._can_resize(node.id):
            return
        dx, dy = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                  Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}[key]
        step = 10 if accelerated else 1
        rect = node.geometry
        width, height = content_size(self.document.model, node.parent_id)
        x = max(0, min(rect.x + dx * step, max(0, width - rect.width)))
        y = max(0, min(rect.y + dy * step, max(0, height - rect.height)))
        try:
            self.document.execute("微调控件位置", lambda model: move_node(model, node.id, x, y))
            self.notice.emit(f"位置已更新：横向 {x}，纵向 {y}。")
        except DesignerError as exc:
            self.error.emit(str(exc))

    def delete_selected(self) -> None:
        self.cancel_gesture()
        if not self.prepare_interaction():
            return
        try:
            keys = self.document.selected_ids
            self.document.execute("删除控件" if len(keys) == 1 else "删除多个控件", lambda model: delete_nodes(model, keys))
            self.notice.emit(f"已删除 {len(keys)} 个控件；按 Ctrl+Z 可以恢复。")
        except DesignerError as exc:
            self.error.emit(str(exc))

    def prepare_interaction(self) -> bool:
        """由工作台提交待编辑属性，独立画布无需依赖属性面板。"""
        return self.before_interaction is None or self.before_interaction()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        try:
            component_type(event.mimeData(), self.document.registry)
            if self.document.read_only:
                event.ignore()
                return
            event.acceptProposedAction()
            self.notice.emit("拖到白色窗口区域，松开即可创建控件。")
        except DesignerError:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        try:
            spec = self.document.registry.require(component_type(event.mimeData(), self.document.registry))
            position = self.mapToScene(event.position().toPoint())
            if (spec.slot != "non_visual" and not self.renderer.surface.rect().contains(position)) or self.document.read_only:
                self.drop_outline.hide()
                event.ignore()
                return
            parent_id, x, y, width, height = self._drop_geometry(spec.type_id, position)
            ox, oy = self._content_origin(parent_id)
            self.drop_outline.setRect(x + ox, y + oy, width, height)
            self.drop_outline.show()
            self.notice.emit("松开后添加到非可视组件区。" if spec.slot == "non_visual" else
                             "松开后固定挂接到窗口。" if spec.slot in {"tool_bar", "status_bar"} else
                             f"松开后添加到{self.document.model.nodes[parent_id].name}。")
            event.acceptProposedAction()
        except DesignerError:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        self.drop_outline.hide()
        try:
            type_id = component_type(event.mimeData(), self.document.registry)
            position = self.mapToScene(event.position().toPoint())
            spec = self.document.registry.require(type_id)
            if self.document.read_only or (spec.slot != "non_visual" and not self.renderer.surface.rect().contains(position)):
                event.ignore()
                return
            if self.create_component(type_id, position):
                event.acceptProposedAction()
        except DesignerError as exc:
            self.error.emit(str(exc))
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.drop_outline.hide()
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.cancel_gesture()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y() or event.pixelDelta().y()
            if delta:
                anchor = event.position().toPoint()
                position = self.mapToScene(anchor)
                self.set_zoom(self._zoom + (25 if delta > 0 else -25))
                self._place_scene_point(position, anchor)
            event.accept()
        else:
            super().wheelEvent(event)

    def event(self, event: QEvent) -> bool:
        if hasattr(self, "_gesture") and event.type() in {QEvent.Type.WindowDeactivate, QEvent.Type.Hide,
                                                          QEvent.Type.UngrabMouse}:
            self.cancel_gesture()
        result = super().event(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange and hasattr(self, "renderer") and not self._disposed:
            self.cancel_gesture()
            self.refresh()
        return result

    def dispose(self) -> None:
        if self._disposed:
            return
        self.cancel_gesture()
        self._cancel_build()
        self._disposed = True
        self.before_interaction = None
        self._unsubscribe()
        self.document.selection_changed.disconnect(self._select)
        self.document.status_changed.disconnect(self._status_changed)
        self.renderer.dispose()
