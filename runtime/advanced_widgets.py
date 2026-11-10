"""Shared creation and ownership rules for preview and independent exports."""

from PySide6.QtCore import Qt, QPoint, QRect, QObject, QEvent, QTimer
from PySide6.QtWidgets import QWidget, QMainWindow
from shiboken6 import isValid
from .easy_widgets import CommonDialog
from .advanced_containers import (CONTAINER_FACTORIES, LayoutContainer, ScrollArea, Splitter,
                                  StackedWidget, ToolBox, MdiArea, MdiSubWindow, DockWidget, Wizard,
                                  DialogWindow, TriggerWindow)
from .advanced_dialogs import DIALOG_FACTORIES, DialogService
from .advanced_views import VIEW_FACTORIES, ButtonGroup
from .advanced_graphics import GRAPHICS_FACTORIES, SplashScreen, LazySurface

ADVANCED_FACTORIES = {**CONTAINER_FACTORIES, **DIALOG_FACTORIES, **VIEW_FACTORIES, **GRAPHICS_FACTORIES}
LAYOUT_ITEM_KEYS = frozenset({"layout_stretch", "layout_row", "layout_column", "layout_row_span", "layout_column_span"})
ADVANCED_KEYS = {
    **{name: frozenset("content_left content_top content_right content_bottom spacing columns".split())
       for name in ("QHBoxLayout", "QVBoxLayout", "QGridLayout", "QFormLayout")},
    "QSpacerItem": {"orientation", "minimum_extent", "expanding"},
    "QScrollArea": {"content_width", "content_height", "widget_resizable", "horizontal_policy", "vertical_policy", "scroll_x", "scroll_y"},
    "QSplitter": {"orientation", "handle_width", "children_collapsible", "sizes"},
    "QStackedWidget": {"current_index"}, "QToolBox": {"current_index"},
    "QMdiArea": {"view_mode", "arrangement"}, "QMdiSubWindow": {"title", "maximized"},
    "QWizardPage": {"title", "subtitle", "complete"},
    "QDialog": {"title", "trigger_control", "show_on_start", "modal"},
    "QDockWidget": {"title", "dock_area", "floating", "closable", "movable", "floatable", "dock_width", "dock_height"},
    "QWizard": {"title", "trigger_control", "show_on_start", "current_index", "wizard_style"},
    "QSplashScreen": {"image", "text", "text_color", "duration", "show_on_start", "trigger_control"},
    "QTabBar": {"items", "current_index", "tabs_closable", "movable", "expanding"},
    "QMessageBox": {"title", "trigger_control", "text", "icon_kind", "buttons"},
    "QErrorMessage": {"title", "trigger_control", "text"},
    "QInputDialog": {"title", "trigger_control", "label", "input_mode", "text_value", "minimum", "maximum", "value", "decimals", "password"},
    "QColorDialog": {"title", "trigger_control", "initial_color", "alpha_channel"},
    "QFontDialog": {"title", "trigger_control", "font_family", "font_size"},
    "QProgressDialog": {"title", "trigger_control", "text", "minimum", "maximum", "value", "cancel_text", "auto_close"},
    **{name: {"items", "table_data", "tree_data", "editable", "selection_mode", "alternating", "sorting", "view_mode"}
       for name in ("QListView", "QTableView", "QTreeView", "QColumnView")},
    "QUndoView": {"empty_label", "clean_icon"},
    "QDialogButtonBox": {"buttons", "orientation", "center_buttons", "close_parent_dialog"},
    "QButtonGroup": {"members", "exclusive"},
    "QGraphicsView": {"scene_width", "scene_height", "image", "text", "zoom", "interactive"},
    "QRhiWidget": {"clear_color", "samples"}, "QOpenGLWidget": {"clear_color", "samples"},
    "QSvgWidget": {"svg_data"}, "QWebEngineView": {"source_mode", "html", "url", "javascript", "zoom_factor"},
}


def content_host(widget):
    if isinstance(widget, (ScrollArea, DockWidget, MdiSubWindow)):
        return widget.widget()
    if isinstance(widget, MdiArea):
        return widget.viewport()
    return widget


def content_rect(widget):
    host = content_host(widget)
    if isinstance(widget, ScrollArea):
        host = widget.viewport()
    if host is not widget:
        return QRect(host.mapTo(widget, QPoint()), host.size())
    return widget.contentsRect()


def apply_advanced_properties(widget, values, design_mode=False):
    if type(widget) in ADVANCED_FACTORIES.values():
        widget.design_mode = design_mode
        widget.configure(values)


def arrange_advanced(root, controls, records, design_mode=False):
    # Records use stable code names in both preview and export.
    if not any(type(controls[key]) in ADVANCED_FACTORIES.values() for key, parent, slot, values in records):
        return
    by_parent = {}
    for key, parent, slot, values in records:
        by_parent.setdefault((parent, slot), []).append((key, controls[key], values))
    for key, parent, slot, values in records:
        widget = controls[key]
        children = by_parent.get((key, "children"), ())
        if isinstance(widget, (LayoutContainer, Splitter, MdiArea)):
            widget.set_children(children)
        if isinstance(widget, ScrollArea):
            widget.horizontalScrollBar().setValue(values["scroll_x"])
            widget.verticalScrollBar().setValue(values["scroll_y"])
        if isinstance(widget, (StackedWidget, ToolBox, Wizard)):
            pages = [(page, props.get("text", props.get("title", "")))
                     for name, page, props in by_parent.get((key, "pages"), ())]
            widget.set_pages(pages, values["current_index"])
        if isinstance(widget, DockWidget):
            area = {"left": Qt.DockWidgetArea.LeftDockWidgetArea, "right": Qt.DockWidgetArea.RightDockWidgetArea,
                    "top": Qt.DockWidgetArea.TopDockWidgetArea, "bottom": Qt.DockWidgetArea.BottomDockWidgetArea}[values["dock_area"]]
            root.addDockWidget(area, widget)
            widget.setFloating(values["floating"] and not design_mode)
            root.resizeDocks([widget], [values["dock_width"]], Qt.Orientation.Horizontal)
            root.resizeDocks([widget], [values["dock_height"]], Qt.Orientation.Vertical)
        if isinstance(widget, ButtonGroup):
            widget.setExclusive(False)
            for button in widget.buttons():
                widget.removeButton(button)
            for index, name in enumerate(values["members"]):
                widget.addButton(controls[name], index)
            by_name = {controls[name]: props for name, owner, child_slot, props in records}
            for button in widget.buttons():
                button.setChecked(False)
            widget.setExclusive(values["exclusive"])
            for button in widget.buttons():
                props = by_name[button]
                button.setChecked(props.get("checked", False) or props.get("check_state") == "checked")
        if isinstance(widget, TriggerWindow):
            widget.bind_trigger(None if design_mode else controls.get(values.get("trigger_control", "")))
        if isinstance(widget, (DialogWindow, Wizard, SplashScreen)) and not design_mode:
            widget.hide()
    for widget in controls.values():
        if isinstance(widget, QWidget) and widget.layout() is not None:
            widget.layout().activate()


def start_advanced(controls):
    roots = {widget for widget in controls.values() if isinstance(widget, QMainWindow)}
    for root in roots:
        if root.isWindow() and not hasattr(root, "_advanced_lifecycle"):
            root._advanced_lifecycle = AdvancedLifecycle(root, controls)
    for widget in controls.values():
        if isinstance(widget, LazySurface):
            widget.start()
        if isinstance(widget, (DialogWindow, Wizard, SplashScreen)) and widget.values.get("show_on_start"):
            widget.open_dialog()


class AdvancedLifecycle(QObject):
    def __init__(self, root, controls):
        super().__init__(root)
        self.controls = controls
        self._close_check = QTimer(self)
        self._close_check.setSingleShot(True)
        self._close_check.timeout.connect(self._finish_close)
        root.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Close:
            # Close filters run before business handlers can reject the request.
            self._close_check.start(0)
        return False

    def _finish_close(self):
        root = self.parent()
        if root.isVisible():
            return
        for widget in self.controls.values():
            if widget is root or not isValid(widget):
                continue
            if isinstance(widget, CommonDialog):
                widget.dispose()
            elif isinstance(widget, QTimer):
                widget.stop()
            else:
                dispose_advanced(widget)


def dispose_advanced(widget):
    if isinstance(widget, (TriggerWindow, LazySurface)):
        widget.dispose()


def render_chrome(widget, painter):
    """Paint native chrome, skipping separately cached design-node subtrees."""
    def render(current):
        if current is not widget and current.property("uiplay_node"):
            return
        if current is not widget and current.isHidden():
            return
        position = current.mapTo(widget, QPoint())
        painter.save()
        painter.setClipRect(QRect(position, current.size()), Qt.ClipOperation.IntersectClip)
        QWidget.render(current, painter, position, renderFlags=QWidget.RenderFlag(0))
        for child in current.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            render(child)
        painter.restore()
    render(widget)
