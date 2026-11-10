"""只有本层解释构建计划中的属性；画布不另写属性赋值规则。"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from PySide6.QtCore import QAbstractAnimation, QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QImage, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractScrollArea, QAbstractSpinBox, QCalendarWidget, QCheckBox, QComboBox, QCommandLinkButton,
    QDateEdit, QDateTimeEdit, QDial, QDoubleSpinBox, QFrame, QGroupBox, QLabel, QLCDNumber, QLineEdit, QListWidget, QMainWindow,
    QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QSlider, QSpinBox,
    QMenuBar, QScrollBar, QTabBar, QTableWidget, QTimeEdit, QToolButton, QTreeWidget, QWidget,
    QFontComboBox, QKeySequenceEdit, QTextBrowser, QTextEdit,
)

from core.build_plan import BuildPlan, NodePlan
from core.errors import DesignerError, require
from core.registry import WidgetRegistry
from core.window_scaling import scale_base_size, scale_items
from widgets.catalog import SUPPORTED_SLOTS
from layout.runtime import WindowScaler
from .appearance import APPEARANCE_KEYS, WINDOW_KEYS, apply_appearance, apply_window_options
from .widget_properties import (ALIGNMENTS, ECHO_MODES, COMPOSITE_KEYS, ContainerFrame, ContainerGroupBox,
                                apply_content_margins, apply_widget_properties)
from .easy_widgets import EASY_FACTORIES, EASY_KEYS, CommonDialog, SelectionTabs, apply_easy_properties
from .menus import MENU_KEYS, apply_menu_properties, arrange_menus
from .control_features import FEATURE_KEYS, apply_control_features, prepare_group_states, finish_group_states
from .navigation import NAVIGATION_KEYS, apply_navigation_style, configure_navigation, dispose_navigation
from .property_completion import (SHARED_KEYS as COMPLETION_SHARED, COMPOSITE_KEYS as COMPLETION_KEYS,
                                  apply_completed_properties, finish_completed_properties)
from .advanced_widgets import (ADVANCED_FACTORIES, ADVANCED_KEYS, LAYOUT_ITEM_KEYS, content_host,
                               apply_advanced_properties, arrange_advanced, dispose_advanced, render_chrome)

logger = logging.getLogger(__name__)
FACTORIES: dict[str, type[QObject]] = {kind.__name__: kind for kind in (
    QWidget, QMainWindow, QPushButton, QLabel, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QRadioButton, QSpinBox, QProgressBar, QSlider, QListWidget, QTableWidget, QTreeWidget,
    QGroupBox, QFrame, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit, QCalendarWidget,
    QToolButton, QCommandLinkButton, QDial, QScrollBar, QLCDNumber, QAction, QMenuBar,
    QFontComboBox, QKeySequenceEdit, QTextBrowser, QTextEdit,
)}
FACTORIES.update(QGroupBox=ContainerGroupBox, QFrame=ContainerFrame)
FACTORIES.update(EASY_FACTORIES)
FACTORIES.update(ADVANCED_FACTORIES)


def verify_event_targets(model, registry, bindings) -> None:
    classes = {node.code_name: FACTORIES[registry.require(node.type_id).qt_class] for node in model.nodes.values()}
    for binding in bindings:
        if "slot" in binding:
            require(callable(getattr(classes[binding["target"]], binding["slot"], None)),
                    f"“{binding['name']}”的事件目标组件不支持所选操作。")


def verify_registry(registry: WidgetRegistry) -> None:
    """启动时验证已经注册的真实 Qt 类和可写属性。"""
    for spec in registry.specs.values():
        require(spec.slot in SUPPORTED_SLOTS, f"“{spec.label}”的挂接位置尚未接入。")
        require(spec.qt_class in FACTORIES, f"“{spec.label}”缺少控件工厂。")
        probe = FACTORIES[spec.qt_class]()
        try:
            # 元对象包装只在所属探针存活期间使用，不跨实例保存包装引用。
            meta = probe.metaObject()
            require(len({event.key for event in spec.events}) == len(spec.events), f"“{spec.label}”的事件键不能重复。")
            for event in spec.events:
                require(bool(event.qt_signal) != bool(event.qt_event), f"“{spec.label}”的事件必须对应唯一来源。")
                if event.qt_event:
                    require(isinstance(probe, QWidget) and hasattr(QEvent.Type, event.qt_event),
                            f"“{spec.label}”的“{event.label}”没有对应的 Qt 事件。")
                else:
                    signal = getattr(probe, event.qt_signal, None)
                    require(signal is not None and callable(getattr(signal, "connect", None)),
                            f"“{spec.label}”的“{event.label}”没有对应的 Qt 信号。")
            for prop in spec.properties:
                if prop.qt_name:
                    index = meta.indexOfProperty(prop.qt_name)
                    require(index >= 0 and meta.property(index).isWritable(),
                            f"“{spec.label}”的“{prop.label}”无法写入当前 Qt 版本。")
                else:
                    require(prop.key in APPEARANCE_KEYS or prop.key in COMPOSITE_KEYS.get(spec.qt_class, ())
                            or prop.key in EASY_KEYS.get(spec.qt_class, ()) or prop.key in MENU_KEYS.get(spec.qt_class, ())
                            or prop.key in FEATURE_KEYS.get(spec.qt_class, ())
                            or (spec.qt_class in {"QPushButton", "QToolButton", "QCommandLinkButton"} and prop.key in NAVIGATION_KEYS)
                            or prop.key in COMPLETION_SHARED or prop.key in COMPLETION_KEYS.get(spec.qt_class, ())
                            or (spec.slot == "children" and prop.key in LAYOUT_ITEM_KEYS)
                            or prop.key in ADVANCED_KEYS.get(spec.qt_class, ())
                            or (spec.slot == "pages" and prop.key == "text")
                            or (spec.slot == "root" and prop.key in WINDOW_KEYS),
                            f"“{spec.label}”的“{prop.label}”缺少复合属性适配器。")
        finally:
            probe.deleteLater()


class RuntimeTree:
    def __init__(self, registry: WidgetRegistry, *, design_mode: bool = True) -> None:
        self.registry = registry
        self.design_mode = design_mode
        self.widgets: dict[str, QObject] = {}
        self.plans: dict[str, NodePlan] = {}
        self.root: QMainWindow | None = None
        self.scaler: WindowScaler | None = None
        self.last_dirty: frozenset[str] = frozenset()
        self._native_geometry = {}

    def apply(self, plan: BuildPlan) -> frozenset[str]:
        for _ in self.apply_steps(plan):
            pass
        return self.last_dirty

    def apply_steps(self, plan: BuildPlan) -> Iterator[None]:
        require(plan.version == 1 and plan.registry_fingerprint == self.registry.fingerprint,
                "构建计划与控件注册表不匹配。")
        prepare_group_states(self.widgets)
        if self.scaler is not None:
            self.scaler.dispose()
            self.scaler = None
        upcoming = {node.id: node for node in plan.nodes}
        removed = set(self.widgets) - set(upcoming)
        dispose_navigation({key: self.widgets[key] for key in removed})
        retained_root = next((widget for key, widget in self.widgets.items()
                              if key not in removed and self.plans[key].slot == "root"), None)
        for key in self.widgets.keys() - removed:
            if self.plans[key].parent_id in removed:
                # 分批构建可能处理延迟删除，先把保留的子树移出待删除父级。
                # 临时挂到根窗口，避免新父级仍是旧后代时形成短暂的循环。
                widget = self.widgets[key]
                if isinstance(widget, QWidget):
                    widget.hide()
                widget.setParent(retained_root)
        for key in removed:
            node = self.plans[key]
            widget = self.widgets[key]
            if node.parent_id not in removed:
                dispose_advanced(widget)
                if isinstance(widget, CommonDialog):
                    widget.dispose()
                if isinstance(widget, QWidget):
                    widget.hide()
                if isinstance(widget, QTimer):
                    widget.stop()
                widget.setParent(None)
                widget.deleteLater()
        for key in removed:
            self.widgets.pop(key)
            self._native_geometry.pop(key, None)
        dirty: set[str] = set()
        inherited: set[str] = set()
        for node in plan.nodes:
            previous = self.plans.get(node.id)
            if node.slot not in SUPPORTED_SLOTS:
                continue
            created = node.id not in self.widgets
            if created:
                parent = content_host(self.widgets.get(node.parent_id))
                if node.unknown:
                    widget = QLabel(parent)
                    widget.setTextFormat(Qt.TextFormat.PlainText)
                    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    widget.setStyleSheet("background: #fff2cf; color: #72520c; border: 1px dashed #c5a64e;")
                else:
                    spec = self.registry.require(node.type_id)
                    widget = FACTORIES[spec.qt_class](parent)
                    if isinstance(widget, QLabel):
                        widget.setTextFormat(Qt.TextFormat.PlainText)
                self.widgets[node.id] = widget
                widget.setProperty("uiplay_node", True)
                if node.slot == "root":
                    require(isinstance(widget, QMainWindow), "根控件必须是主窗口。")
                    self.root = widget
                    if self.design_mode:
                        widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
                elif node.slot == "central":
                    require(isinstance(parent, QMainWindow), "工作区缺少所属窗口。")
                    parent.setCentralWidget(widget)
                    palette = widget.palette()
                    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
                    widget.setPalette(palette)
                    widget.setAutoFillBackground(True)
                elif node.slot == "tool_bar":
                    parent.addToolBar(Qt.ToolBarArea.TopToolBarArea, widget)
                elif node.slot == "status_bar":
                    parent.setStatusBar(widget)
            widget = self.widgets[node.id]
            properties_changed = (created or previous.properties != node.properties or previous.name != node.name
                                  or previous.parent_id != node.parent_id or node.parent_id in inherited)
            if created or previous != node or properties_changed:
                if not created and previous.parent_id != node.parent_id:
                    widget.setParent(content_host(self.widgets.get(node.parent_id)))
                    dirty.add(node.id)
                if properties_changed:
                    inherited.add(node.id)
                    widget.setObjectName(node.name)
                    if node.unknown:
                        widget.setText(f"未知组件\n{node.name}")
                    else:
                        spec = self.registry.require(node.type_id)
                        apply_widget_properties(widget, node.properties,
                                                ((prop.key, prop.qt_name, prop.label) for prop in spec.properties))
                        apply_easy_properties(widget, node.properties)
                        apply_advanced_properties(widget, node.properties, self.design_mode)
                        apply_control_features(widget, node.properties)
                        apply_menu_properties(widget, node.properties)
                        apply_completed_properties(widget, node.properties)
                        if isinstance(widget, QWidget):
                            apply_appearance(widget, node.properties)
                            apply_navigation_style(widget, node.properties)
                        if node.slot == "root":
                            apply_window_options(widget, node.properties)
                if node.geometry:
                    rect = node.geometry
                    if node.slot == "root":
                        widget.resize(rect.width, rect.height)
                        if node.properties.get("border_style") == "fixed":
                            widget.setFixedSize(rect.width, rect.height)
                        if not self.design_mode:
                            widget.move(rect.x, rect.y)
                    else:
                        parent = widget.parentWidget()
                        offset = parent.contentsRect().topLeft() if parent else QPoint()
                        widget.setGeometry(rect.x + offset.x(), rect.y + offset.y(), rect.width, rect.height)
                if isinstance(widget, QWidget):
                    apply_content_margins(widget, node.properties)
                    if node.slot == "pages":
                        widget.setProperty("page_visible", not node.designer_hidden if self.design_mode else node.properties.get("visible", True))
                    if node.slot != "root":
                        visible = (not node.designer_hidden if self.design_mode and node.slot not in {"menu_bar", "tool_bar", "status_bar"}
                                   else node.properties.get("visible", True))
                        widget.setVisible(visible)
                old_size = (previous.geometry.width, previous.geometry.height) if previous and previous.geometry else None
                new_size = (node.geometry.width, node.geometry.height) if node.geometry else None
                if old_size != new_size or properties_changed:
                    dirty.add(node.id)
                    if properties_changed and node.slot in {"root", "central"}:
                        dirty.update(upcoming)
                        inherited.update(upcoming)
            yield None
        require(self.root is not None, "构建计划缺少根窗口。")
        menu_nodes = tuple(node for node in plan.nodes if node.slot in {"menu_bar", "menu"})
        old_menus = tuple(node for node in self.plans.values() if node.slot in {"menu_bar", "menu"})
        if menu_nodes != old_menus:
            arrange_menus(self.root, self.widgets, [(node.id, node.parent_id, node.slot) for node in menu_nodes])
            dirty.update(node.id for node in menu_nodes if node.slot == "menu_bar")
        for node in plan.nodes:
            widget = self.widgets.get(node.id)
            if isinstance(widget, SelectionTabs):
                page_nodes = tuple(page for page in plan.nodes if page.parent_id == node.id and page.slot == "pages")
                previous_pages = tuple(page for page in self.plans.values() if page.parent_id == node.id and page.slot == "pages")
                if previous_pages != page_nodes:
                    # 页标题属于页面属性，但显示在父选择夹的图像缓存中。
                    dirty.add(node.id)
                children = [(self.widgets[page.id], page.properties["text"]) for page in page_nodes]
                widget.set_pages(children, node.properties["current_index"])
        code_widgets = {node.code_name: self.widgets[node.id] for node in plan.nodes}
        arrange_advanced(self.root, {**self.widgets, **code_widgets},
                         [(node.id, node.parent_id, node.slot, node.properties) for node in plan.nodes], self.design_mode)
        finish_completed_properties(self.widgets)
        navigation_dirty = configure_navigation(code_widgets,
            [(node.code_name, upcoming[node.parent_id].code_name if node.parent_id else None,
              node.slot, node.properties) for node in plan.nodes], self.design_mode)
        dirty.update(node.id for node in plan.nodes if node.code_name in navigation_dirty)
        finish_group_states(self.widgets, [(node.id, node.properties.get("checked", False)) for node in plan.nodes
                                           if node.type_id == "builtin.group_box" and not node.unknown])
        self.root.ensurePolished()
        self.root.layout().activate()
        if self.design_mode and any(type(widget) in ADVANCED_FACTORIES.values() for widget in self.widgets.values()):
            # Deliver native page/viewport geometry while WA_DontShowOnScreen keeps the
            # backing window off the desktop. Rendering individual children is too late.
            self.root.show()
            for child in self.root.findChildren(QWidget):
                if child.layout() is not None:
                    child.layout().activate()
        native_managed = set()
        for node in plan.nodes:
            widget = self.widgets[node.id]
            if type(widget) in ADVANCED_FACTORIES.values() or node.parent_id in native_managed:
                native_managed.add(node.id)
            if isinstance(widget, QWidget) and node.id in native_managed:
                geometry = widget.geometry().getRect()
                if self._native_geometry.get(node.id) != geometry:
                    dirty.add(node.id)
                    self._native_geometry[node.id] = geometry
        if not self.design_mode and plan.nodes[0].properties.get("scale_children", False):
            items = scale_items(plan.nodes)
            self.scaler = WindowScaler(self.root, self.root.centralWidget(), scale_base_size(plan.nodes), items,
                                       {item.key: self.widgets[item.key] for item in items})
        for node in sorted((item for item in plan.nodes if item.stack_order is not None),
                           key=lambda item: (item.parent_id or "", item.stack_order)):
            widget = self.widgets.get(node.id)
            if widget:
                widget.raise_()
            yield None
        self.plans = upcoming
        self.last_dirty = frozenset(dirty)

    def image(self, node_id: str, ratio: float) -> QImage:
        widget = self.widgets[node_id]
        width, height = max(1, round(widget.width() * ratio)), max(1, round(widget.height() * ratio))
        require(width * height <= 16_777_216, "控件绘制尺寸过大，请缩小控件或画布缩放比例。")
        image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        require(not image.isNull(), "无法分配控件绘制缓存。")
        image.setDevicePixelRatio(ratio)
        image.fill(Qt.GlobalColor.transparent)
        if isinstance(widget, QTabBar) and widget.autoHide() and widget.count() < 2:
            return image
        widget.ensurePolished()
        if self.design_mode and isinstance(widget, (QLineEdit, QKeySequenceEdit)):
            # 画布是静态缓存，完成内部淡入动画，避免保存透明的清除按钮首帧。
            for animation in widget.findChildren(QAbstractAnimation):
                duration = animation.totalDuration()
                if duration >= 0 and animation.state() == QAbstractAnimation.State.Running:
                    animation.setCurrentTime(duration)
        painter = QPainter(image)
        try:
            # 子节点各自绘制；保留标签透明背景，避免遮挡下方控件。
            # 编辑框的清除按钮是内部子控件，应进入缓存；设计节点仍分别绘制。
            flags = (QWidget.RenderFlag.DrawChildren if isinstance(widget, (QLineEdit, QKeySequenceEdit, QAbstractScrollArea, QAbstractSpinBox, QComboBox, QCalendarWidget))
                     or self.plans[node_id].slot in {"menu_bar", "tool_bar", "status_bar"}
                     else QWidget.RenderFlag(0))
            if type(widget) in ADVANCED_FACTORIES.values():
                render_chrome(widget, painter)
            else:
                widget.render(painter, QPoint(), renderFlags=flags)
            if isinstance(widget, SelectionTabs) and not widget.tab_bar.isHidden():
                widget.tab_bar.render(painter, widget.tab_bar.pos(), renderFlags=QWidget.RenderFlag.DrawChildren)
        finally:
            painter.end()
        return image

    def dispose(self) -> None:
        dispose_navigation(self.widgets)
        if self.scaler is not None:
            self.scaler.dispose()
            self.scaler = None
        for widget in self.widgets.values():
            dispose_advanced(widget)
            if isinstance(widget, CommonDialog):
                widget.dispose()
            if isinstance(widget, QTimer):
                widget.stop()
            if isinstance(widget, QWidget) and widget is not self.root and widget.parentWidget() is None:
                # 根窗口替换过程被取消时，释放暂未重新挂接的保留子树。
                widget.hide()
                widget.deleteLater()
        if self.root:
            self.root.close()
            self.root.deleteLater()
        self.widgets.clear()
        self.plans.clear()
        self._native_geometry.clear()
        self.root = None
