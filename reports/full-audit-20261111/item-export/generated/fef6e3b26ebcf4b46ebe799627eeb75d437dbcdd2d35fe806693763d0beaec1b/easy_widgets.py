"""基础组件运行适配；随独立项目导出，不依赖设计器模块。"""

from __future__ import annotations

import base64
from collections.abc import Mapping
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QMouseEvent, QPainter, QPen, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractButton, QColorDialog, QDialog, QFileDialog, QFontDialog,
    QLabel, QStatusBar, QTabBar, QToolBar, QTreeWidget, QTreeWidgetItem, QWidget,
)
from .application import configure_file_dialog
from .widget_properties import apply_column_widths, table_content_key
try:
    from .layout.containers import inset_rect, tab_header_visible, tab_margins
except ImportError:
    from layout.containers import inset_rect, tab_header_visible, tab_margins

logger = logging.getLogger(__name__)


def decoded_image(value: str) -> QImage:
    image = QImage()
    if value:
        if not image.loadFromData(base64.b64decode(value, validate=True), "PNG"):
            raise ValueError("图片内容损坏，无法显示。")
    return image


def image_asset(module_file: str, relative_path: str) -> str:
    """独立导出使用相对于生成模块的图片路径。"""
    try:
        return base64.b64encode((Path(module_file).parent / relative_path).read_bytes()).decode("ascii")
    except OSError as exc:
        raise RuntimeError("导出图片文件缺失，请重新导出完整项目。") from exc


class PictureBox(QWidget):
    clicked = Signal()
    doubleClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.picture = QImage()
        self.mode = "fit"
        self.border = True
        self.image_alignment = Qt.AlignmentFlag.AlignCenter
        self.smooth_scaling = True
        self.image_opacity = 1.0

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), self.palette().window())
            area = self.rect().adjusted(1, 1, -1, -1) if self.border else self.rect()
            if not self.picture.isNull():
                target = QRect(area)
                if self.mode != "stretch":
                    size = self.picture.size()
                    if self.mode == "fit":
                        size.scale(area.size(), Qt.AspectRatioMode.KeepAspectRatio)
                    target.setSize(size)
                    target.moveCenter(area.center())
                    if self.image_alignment & Qt.AlignmentFlag.AlignLeft:
                        target.moveLeft(area.left())
                    elif self.image_alignment & Qt.AlignmentFlag.AlignRight:
                        target.moveRight(area.right())
                    if self.image_alignment & Qt.AlignmentFlag.AlignTop:
                        target.moveTop(area.top())
                    elif self.image_alignment & Qt.AlignmentFlag.AlignBottom:
                        target.moveBottom(area.bottom())
                painter.save()
                try:
                    painter.setClipRect(area)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.smooth_scaling)
                    painter.setOpacity(self.image_opacity)
                    painter.drawImage(target, self.picture)
                finally:
                    # 图片只裁切内容区，边框使用原来的绘制范围。
                    painter.restore()
            else:
                painter.setPen(self.palette().mid().color())
                painter.drawText(area, Qt.AlignmentFlag.AlignCenter, "图片框")
            if self.border:
                painter.setPen(self.palette().mid().color())
                painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        finally:
            painter.end()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class DrawingBoard(QWidget):
    pressed = Signal(int, int)
    released = Signal(int, int)
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.paper = QColor("#ffffff")
        self.pen_color = QColor("#20252b")
        self.pen_width = 2
        self.pen_style = Qt.PenStyle.SolidLine
        self.antialiasing = True
        self.border = True
        self.drawing_enabled = True
        self.background = QImage()
        self.ink = QImage()
        self.previous: QPoint | None = None

    def resizeEvent(self, event: QResizeEvent) -> None:
        old = self.ink
        self.ink = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self.ink.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.ink)
        if not old.isNull():
            painter.drawImage(0, 0, old)
        painter.end()
        super().resizeEvent(event)

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), self.paper)
            if not self.background.isNull():
                painter.drawImage(0, 0, self.background)
            painter.drawImage(0, 0, self.ink)
            if self.border:
                painter.setPen(self.palette().mid().color())
                painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        finally:
            painter.end()

    def draw_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        if self.ink.isNull():
            self.ink = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
            self.ink.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.ink)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, self.antialiasing)
            painter.setPen(QPen(self.pen_color, self.pen_width, self.pen_style, Qt.PenCapStyle.RoundCap))
            painter.drawLine(x1, y1, x2, y2)
        finally:
            painter.end()
        self.update()
        self.changed.emit()

    def clear(self) -> None:
        self.ink.fill(Qt.GlobalColor.transparent)
        self.update()
        self.changed.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.previous = event.position().toPoint() if self.drawing_enabled else None
            self.pressed.emit(int(event.position().x()), int(event.position().y()))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.previous is not None and event.buttons() & Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            self.draw_line(self.previous.x(), self.previous.y(), point.x(), point.y())
            self.previous = point
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.previous = None
            self.released.emit(int(event.position().x()), int(event.position().y()))
        super().mouseReleaseEvent(event)


class SelectionTabs(QWidget):
    """四向页签与页面共享可预测的内容边界。"""

    currentChanged = Signal(int)
    tabBarClicked = Signal(int)
    tabBarDoubleClicked = Signal(int)
    tabCloseRequested = Signal(int)
    tabMoved = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tab_bar = QTabBar(self)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setUsesScrollButtons(True)
        self.pages: list[QWidget] = []
        self.options: dict[str, Any] = {}
        self.tab_bar.currentChanged.connect(self.set_current_page)
        self.tab_bar.tabBarClicked.connect(self.tabBarClicked)
        self.tab_bar.tabBarDoubleClicked.connect(self.tabBarDoubleClicked)
        self.tab_bar.tabCloseRequested.connect(self.tabCloseRequested)
        self.tab_bar.tabMoved.connect(self._tab_moved)

    def configure(self, values: Mapping[str, Any]) -> None:
        self.options = dict(values)
        direction = {"top": "North", "bottom": "South", "left": "West", "right": "East"}[values.get("tab_position", "top")]
        shape = "Triangular" if values.get("tab_shape", "rounded") == "triangular" else "Rounded"
        self.tab_bar.setShape(getattr(QTabBar.Shape, shape + direction))
        self.tab_bar.setExpanding(values.get("expanding", False))
        self.tab_bar.setUsesScrollButtons(values.get("uses_scroll_buttons", True))
        self.tab_bar.setMovable(values.get("movable", False))
        self.tab_bar.setTabsClosable(values.get("tabs_closable", False))
        self.tab_bar.setDocumentMode(values.get("document_mode", False))
        self.tab_bar.setDrawBase(values.get("draw_base", True))
        self.tab_bar.setIconSize(QSize(values.get("icon_width", 16), values.get("icon_height", 16)))
        self.tab_bar.setElideMode({"none": Qt.TextElideMode.ElideNone, "left": Qt.TextElideMode.ElideLeft,
                                  "middle": Qt.TextElideMode.ElideMiddle, "right": Qt.TextElideMode.ElideRight}[values.get("elide_mode", "right")])
        self.arrange_pages()

    def set_pages(self, pages: list[tuple[QWidget, str]], index: int) -> None:
        previous = self.tab_bar.blockSignals(True)
        try:
            while self.tab_bar.count():
                self.tab_bar.removeTab(0)
            incoming = [page for page, _ in pages]
            for page in self.pages:
                if page not in incoming:
                    page.hide()
            self.pages = incoming
            for page, title in pages:
                page.setParent(self)
                picture = page.property("tab_icon") or ""
                icon = QIcon(QPixmap.fromImage(decoded_image(picture))) if picture else QIcon()
                tab = self.tab_bar.addTab(icon, title)
                self.tab_bar.setTabToolTip(tab, page.toolTip())
            self.tab_bar.setCurrentIndex(index)
        finally:
            self.tab_bar.blockSignals(previous)
        self.arrange_pages()

    def set_current_page(self, index: int) -> None:
        if not 0 <= index < self.tab_bar.count():
            return
        if index != self.tab_bar.currentIndex():
            self.tab_bar.setCurrentIndex(index)
            return
        self.arrange_pages()
        self.currentChanged.emit(index)

    def _tab_moved(self, source: int, destination: int) -> None:
        self.pages.insert(destination, self.pages.pop(source))
        self.arrange_pages()
        self.tabMoved.emit(source, destination)

    def arrange_pages(self) -> None:
        width, height = self.width(), self.height()
        x, y, page_width, page_height = inset_rect(width, height, tab_margins(self.options, len(self.pages)))
        position = self.options.get("tab_position", "top")
        bar = {"top": (0, 0, width, y), "bottom": (0, y + page_height, width, height - y - page_height),
               "left": (0, 0, x, height), "right": (x + page_width, 0, width - x - page_width, height)}[position]
        visible = tab_header_visible(self.options, len(self.pages))
        self.tab_bar.setGeometry(*bar)
        self.tab_bar.setVisible(visible)
        for index, page in enumerate(self.pages):
            page.setGeometry(x, y, page_width, page_height)
            page.setVisible(index == self.tab_bar.currentIndex() and page.property("page_visible") is not False)
        self.tab_bar.raise_()
        self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.arrange_pages()
        super().resizeEvent(event)

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        if self.options.get("pane_border", True):
            x, y, width, height = inset_rect(self.width(), self.height(), tab_margins(self.options, len(self.pages)))
            painter.setPen(self.palette().mid().color())
            painter.drawRect(x - 1, y - 1, width + 1, height + 1)
        painter.end()


class SuperList(QTreeWidget):
    """报表式超级列表框：多列、勾选、排序和原生表项事件。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setUniformRowHeights(True)

    def configure(self, values: Mapping[str, Any]) -> None:
        previous = self.blockSignals(True)
        try:
            self.setSortingEnabled(False)
            data = values["table_data"]
            content = table_content_key(data)
            changed = getattr(self, "_table_source", None) != content
            if changed:
                self.clear()
                self.setColumnCount(len(data["headers"]))
                for row, cells in enumerate(data["rows"]):
                    item = QTreeWidgetItem(self, list(cells))
                    item.setData(0, Qt.ItemDataRole.UserRole, row)
                self._table_source = content
            self.setHeaderLabels(list(data["headers"]))
            checks = set(values["checked_rows"])
            check_source = (values["checkboxes"], frozenset(checks))
            checks_changed = changed or getattr(self, "_checks_source", None) != check_source
            for index in range(self.topLevelItemCount()):
                item = self.topLevelItem(index)
                row = item.data(0, Qt.ItemDataRole.UserRole)
                item.setSizeHint(0, QSize(0, values["row_height"]))
                flags = item.flags() & ~(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable)
                if values["editable"]:
                    flags |= Qt.ItemFlag.ItemIsEditable
                if values["checkboxes"]:
                    flags |= Qt.ItemFlag.ItemIsUserCheckable
                if checks_changed:
                    item.setData(0, Qt.ItemDataRole.CheckStateRole,
                                 (Qt.CheckState.Checked if str(row + 1) in checks else Qt.CheckState.Unchecked)
                                 if values["checkboxes"] else None)
                item.setFlags(flags)
            self._checks_source = check_source
            self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection if values["multi_select"] else QAbstractItemView.SelectionMode.SingleSelection)
            self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows if values["full_row"] else QAbstractItemView.SelectionBehavior.SelectItems)
            self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked if values["editable"] else QAbstractItemView.EditTrigger.NoEditTriggers)
            self.setAlternatingRowColors(values["alternating"])
            self.setHeaderHidden(not values["header_visible"])
            self.header().setSectionsMovable(True)
            apply_column_widths(self.header(), data, values["column_width"], values["stretch_last_section"])
            self.setSortingEnabled(values["sorting"])
        finally:
            self.blockSignals(previous)


class CommonDialog(QObject):
    """非可视对话框组件；运行时调用或由指定按钮触发。"""

    accepted = Signal(object)
    cancelled = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.values: dict[str, Any] = {}
        self.dialog: QDialog | None = None
        self.result: Any = None
        self._trigger: QAbstractButton | None = None

    def bind_trigger(self, button: QAbstractButton | None) -> None:
        if self._trigger is not None:
            try:
                self._trigger.clicked.disconnect(self.open_dialog)
            except (RuntimeError, TypeError):
                pass
        self._trigger = button
        if button is not None:
            button.clicked.connect(self.open_dialog)

    def open_dialog(self, checked: bool = False) -> None:
        if self.dialog is not None:
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        try:
            owner = self.parent() if isinstance(self.parent(), QWidget) else None
            kind = self.values.get("dialog_kind", "open_file")
            if kind == "color":
                dialog = QColorDialog(owner)
                dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, not self.values.get("use_native_dialog", False))
            elif kind == "font":
                dialog = QFontDialog(owner)
                dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, not self.values.get("use_native_dialog", False))
            else:
                dialog = QFileDialog(owner)
                configure_file_dialog(dialog)
                dialog.setOption(QFileDialog.Option.DontUseNativeDialog, not self.values.get("use_native_dialog", False))
                dialog.setOption(QFileDialog.Option.ReadOnly, self.values.get("read_only", False))
                dialog.setOption(QFileDialog.Option.DontConfirmOverwrite, not self.values.get("confirm_overwrite", True))
                dialog.setViewMode(QFileDialog.ViewMode.List if self.values.get("file_view_mode") == "list" else QFileDialog.ViewMode.Detail)
                modes = {"open_file": QFileDialog.FileMode.ExistingFile, "open_files": QFileDialog.FileMode.ExistingFiles,
                         "save_file": QFileDialog.FileMode.AnyFile, "directory": QFileDialog.FileMode.Directory}
                dialog.setFileMode(modes[kind])
                dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave if kind == "save_file" else QFileDialog.AcceptMode.AcceptOpen)
                dialog.setNameFilter(self.values.get("filter", "所有文件 (*)"))
                if self.values.get("initial_directory"):
                    dialog.setDirectory(self.values["initial_directory"])
                dialog.setDefaultSuffix(self.values.get("default_suffix", ""))
                if self.values.get("initial_file"):
                    dialog.selectFile(self.values["initial_file"])
                dialog.setLabelText(QFileDialog.DialogLabel.Accept, "保存" if kind == "save_file" else "选择")
                dialog.setLabelText(QFileDialog.DialogLabel.Reject, "取消")
            dialog.setWindowTitle(self.values.get("title", "请选择"))
            self.dialog = dialog
            dialog.finished.connect(self._finished)
            dialog.open()
        except Exception:
            logger.exception("打开通用对话框失败。")
            if self.dialog:
                self.dialog.deleteLater()
                self.dialog = None
            self.cancelled.emit()

    def _finished(self, code: int) -> None:
        dialog, self.dialog = self.dialog, None
        if dialog is None:
            return
        try:
            if code == QDialog.DialogCode.Accepted:
                if isinstance(dialog, QFileDialog):
                    self.result = dialog.selectedFiles()
                elif isinstance(dialog, QColorDialog):
                    self.result = dialog.selectedColor().name()
                else:
                    font = dialog.selectedFont()
                    self.result = {"字体": font.family(), "字号": font.pointSize(), "粗体": font.bold(), "斜体": font.italic()}
                self.accepted.emit(self.result)
            else:
                self.result = None
                self.cancelled.emit()
        finally:
            dialog.deleteLater()

    def dispose(self) -> None:
        self.bind_trigger(None)
        if self.dialog is not None:
            self.dialog.reject()


EASY_FACTORIES: dict[str, type[QObject]] = {cls.__name__: cls for cls in (
    DrawingBoard, PictureBox, SelectionTabs, SuperList, CommonDialog, QTimer, QToolBar, QStatusBar,
)}
EASY_KEYS = {
    "DrawingBoard": {"pen_color", "pen_width", "paper_color", "drawing_enabled", "image"},
    "PictureBox": {"image", "image_mode", "border"},
    "SelectionTabs": {"current_index", "tab_position", "header_visible", "tab_bar_auto_hide", "tab_bar_size",
                      "tab_shape", "expanding", "uses_scroll_buttons", "elide_mode", "document_mode", "draw_base",
                      "pane_border", "movable", "tabs_closable", "icon_width", "icon_height"},
    "QWidget": {"tab_icon"},
    "SuperList": {"table_data", "checkboxes", "checked_rows", "multi_select", "full_row", "editable", "sorting", "alternating", "header_visible", "column_width", "stretch_last_section", "row_height"},
    "CommonDialog": {"dialog_kind", "title", "filter", "initial_directory", "default_suffix", "trigger_control"},
    "QTimer": {"interval", "enabled", "auto_start", "single_shot"}, "QToolBar": {"items", "bar_height"},
    "QStatusBar": {"text", "panels", "bar_height", "size_grip"},
}


def apply_easy_properties(widget: QObject, values: Mapping[str, Any]) -> None:
    if "tab_icon" in values:
        widget.setProperty("tab_icon", values["tab_icon"])
    if isinstance(widget, QTimer):
        widget.stop()
        widget.setInterval(values["interval"])
        widget.setSingleShot(values["single_shot"])
        widget.setProperty("start_enabled", values["enabled"] and values["auto_start"])
    elif isinstance(widget, CommonDialog):
        widget.values = dict(values)
    elif isinstance(widget, DrawingBoard):
        widget.pen_color = QColor(values["pen_color"] or "#20252b")
        widget.pen_width = values["pen_width"]
        widget.pen_style = {"solid": Qt.PenStyle.SolidLine, "dash": Qt.PenStyle.DashLine, "dot": Qt.PenStyle.DotLine,
                            "dash_dot": Qt.PenStyle.DashDotLine}[values.get("pen_style", "solid")]
        widget.antialiasing = values.get("antialiasing", True)
        widget.border = values.get("border", True)
        widget.paper = QColor(values["paper_color"] or "#ffffff")
        widget.drawing_enabled = values["drawing_enabled"]
        widget.background = decoded_image(values["image"])
        widget.update()
    elif isinstance(widget, PictureBox):
        widget.picture = decoded_image(values["image"])
        widget.mode, widget.border = values["image_mode"], values["border"]
        from .property_completion import ALIGNMENTS
        widget.image_alignment = ALIGNMENTS[values.get("image_alignment", "center")]
        widget.smooth_scaling = values.get("smooth_scaling", True)
        widget.image_opacity = values.get("image_opacity", 1.0)
        widget.update()
    elif isinstance(widget, SelectionTabs):
        widget.configure(values)
    elif isinstance(widget, SuperList):
        widget.configure(values)
    elif isinstance(widget, QToolBar):
        for action in widget.actions():
            widget.removeAction(action)
            action.deleteLater()
        widget.setMovable(values.get("movable", False))
        widget.setFloatable(values.get("floatable", False))
        widget.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        widget.setFixedHeight(values["bar_height"])
        for text in values["items"]:
            widget.addSeparator() if text == "-" else widget.addAction(text)
    elif isinstance(widget, QStatusBar):
        for label in getattr(widget, "_status_labels", ()):
            widget.removeWidget(label)
            label.deleteLater()
        widget._status_labels = []
        for text in values["panels"]:
            label = QLabel(text, widget)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setMargin(4)
            widget.addPermanentWidget(label)
            widget._status_labels.append(label)
        widget.setFixedHeight(values["bar_height"])
        widget.setSizeGripEnabled(values["size_grip"])
        widget.showMessage(values["text"])


def start_components(controls: Mapping[str, QObject]) -> None:
    """完成全部控件创建后再启动，设计模式不调用本函数。"""
    for component in controls.values():
        if isinstance(component, CommonDialog):
            target = controls.get(component.values.get("trigger_control", ""))
            component.bind_trigger(target if isinstance(target, QAbstractButton) else None)
        elif isinstance(component, QTimer) and component.property("start_enabled"):
            component.start()
