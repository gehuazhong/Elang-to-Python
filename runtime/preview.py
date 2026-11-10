"""以运行模式消费同一构建计划，交互状态只存在于预览窗口。"""

from __future__ import annotations

import logging
from time import monotonic

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QAbstractButton, QApplication, QKeySequenceEdit, QWidget

from core.build_plan import BuildPlan
from core.deferred import defer
from core.events import event_bindings
from core.models import ProjectModel
from core.registry import WidgetRegistry
from .builder import RuntimeTree
from .easy_widgets import start_components
from .advanced_widgets import start_advanced
from .events import EventConnections

logger = logging.getLogger(__name__)


class PreviewRuntime(QObject):
    notice = Signal(str)
    closed = Signal()

    def __init__(self, registry: WidgetRegistry, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.tree = RuntimeTree(registry, design_mode=False)
        self._disposed = False
        self._closing = False
        self._timer_counts: dict[str, int] = {}
        self._timer_notices: dict[str, float] = {}
        self._connections: EventConnections | None = None
        self._event_notices: dict[tuple[str, str], float] = {}

    def show(self, plan: BuildPlan, model: ProjectModel) -> None:
        try:
            if self._connections is not None:
                self._connections.dispose()
                self._connections.deleteLater()
            self._disposed = False
            self._closing = False
            self._timer_counts.clear()
            self._timer_notices.clear()
            self._event_notices.clear()
            self.tree.apply(plan)
            if self.tree.scaler is not None:
                self.tree.scaler.error.connect(self.notice)
            root = self.tree.root
            for first, second in zip(plan.tab_order, plan.tab_order[1:]):
                QWidget.setTabOrder(self.tree.widgets[first], self.tree.widgets[second])
            controls = {model.nodes[key].code_name: widget for key, widget in self.tree.widgets.items()}
            self._connections = EventConnections(root, controls, event_bindings(model, self.tree.registry),
                                                 self._event_notice, self.notice.emit)
            application = QApplication.instance()
            application.installEventFilter(self)
            # 已失效的屏幕位置仅在预览时移回可见屏幕，不回写文档。
            if not any(screen.availableGeometry().intersects(root.geometry()) for screen in application.screens()):
                screen = application.primaryScreen()
                if screen:
                    area = screen.availableGeometry()
                    root.move(area.left() + max(0, (area.width() - root.width()) // 2),
                              area.top() + max(0, (area.height() - root.height()) // 2))
                    self.notice.emit("预览窗口原位置在屏幕之外，已移回当前屏幕；项目位置保持不变。")
            root.show()
            start_components({model.nodes[key].code_name: widget for key, widget in self.tree.widgets.items()})
            start_advanced(self.tree.widgets)
            root.raise_()
            root.activateWindow()
            if model.data["resources"]:
                self.notice.emit("项目中的旧式外部资源清单仅保留；图片框和画板请通过图片属性重新导入快照。")
        except Exception:
            self.dispose()
            raise

    def _event_notice(self, binding: dict, arguments: tuple) -> None:
        name, label = binding["name"], binding["label"]
        if binding["signal"] == "timeout":
            self._timer_notice(name)
            return
        if binding["signal"] == "clicked":
            widget = self._connections._controls[binding["control"]]
            if isinstance(widget, QAbstractButton):
                self._clicked(name, widget, bool(arguments[0]) if arguments else False)
                return
        if binding["event"] in {"MouseMove", "Paint", "Resize", "Move", "DragMove"} or binding["signal"] in {"updateRequest", "rendered", "loadProgress"}:
            key, now = (binding["control"], binding["key"]), monotonic()
            if now - self._event_notices.get(key, -1) < 1:
                return
            self._event_notices[key] = now
        # 预览只报告触发，不执行导出目录中的业务代码，也不记录输入内容。
        self.notice.emit(f"预览事件：{name} · {label}")

    def _clicked(self, name: str, button: QAbstractButton, checked: bool) -> None:
        state = ("；已选中" if checked else "；未选中") if button.isCheckable() else ""
        self.notice.emit(f"预览事件：{name} · 被单击{state}")

    def _timer_notice(self, name: str) -> None:
        """只合并日志提示，时钟自身的每次信号仍正常交给业务槽。"""
        count = self._timer_counts.get(name, 0) + 1
        self._timer_counts[name] = count
        now = monotonic()
        if count == 1 or now - self._timer_notices.get(name, 0) >= 1:
            self._timer_notices[name] = now
            self.notice.emit(f"预览事件：{name} · 周期事件（本次累计 {count} 次）")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        root = self.tree.root
        if root is None or self._disposed:
            return False
        if watched is root and event.type() == QEvent.Type.Close and not self._closing:
            self._closing = True
            defer(self, self.closed.emit)
        if isinstance(watched, QWidget) and (watched is root or root.isAncestorOf(watched)):
            if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
                # 录入组件需要收到 Esc 本身；Shift+F5 仍可随时停止预览。
                if isinstance(watched, QKeySequenceEdit) and event.key() == Qt.Key.Key_Escape:
                    return False
                if event.key() == Qt.Key.Key_Escape and watched.window() is not root:
                    return False
                stop_key = event.key() == Qt.Key.Key_Escape or (event.key() == Qt.Key.Key_F5 and
                           bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                if stop_key:
                    if not self._closing:
                        self._closing = True
                        defer(self, self.closed.emit)
                    event.accept()
                    return True
        return False

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        application = QApplication.instance()
        if application:
            application.removeEventFilter(self)
        if self._connections is not None:
            self._connections.dispose()
            self._connections = None
        self.tree.dispose()
