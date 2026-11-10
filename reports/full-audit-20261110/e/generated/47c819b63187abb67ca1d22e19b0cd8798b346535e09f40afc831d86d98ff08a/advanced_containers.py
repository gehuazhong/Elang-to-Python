"""Native container ownership and page handling, also shipped with exports."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDockWidget, QFormLayout, QGridLayout, QHBoxLayout,
    QMdiArea, QMdiSubWindow, QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QStackedWidget, QToolBox, QVBoxLayout, QWidget, QWizard, QWizardPage,
)

try:
    from .layout.containers import grid_cells
except ImportError:
    from layout.containers import grid_cells


BUTTONS = {name: getattr(QDialogButtonBox.StandardButton, key) for name, key in
           (("确定", "Ok"), ("取消", "Cancel"), ("是", "Yes"), ("否", "No"),
            ("应用", "Apply"), ("关闭", "Close"), ("重试", "Retry"), ("帮助", "Help"))}


class LayoutContainer(QWidget):
    kind = "horizontal"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.native_layout = {"horizontal": QHBoxLayout, "vertical": QVBoxLayout,
                              "grid": QGridLayout, "form": QFormLayout}[self.kind](self)
        self.values = {}

    def configure(self, values):
        self.values = values
        self.native_layout.setContentsMargins(*(values["content_" + side] for side in ("left", "top", "right", "bottom")))
        self.native_layout.setSpacing(values["spacing"])

    def set_children(self, entries):
        layout = self.native_layout
        if isinstance(layout, QFormLayout):
            while layout.rowCount():
                layout.takeRow(0)
        else:
            while layout.count():
                layout.takeAt(0)
        if self.kind == "grid":
            for row in range(layout.rowCount()):
                layout.setRowStretch(row, 0)
            for column in range(layout.columnCount()):
                layout.setColumnStretch(column, 0)
        cells = grid_cells([(key, values) for key, widget, values in entries], self.values.get("columns", 2)) if self.kind == "grid" else {}
        for index, (key, widget, values) in enumerate(entries):
            if self.kind in {"horizontal", "vertical"}:
                layout.addWidget(widget, values.get("layout_stretch", 0))
            elif self.kind == "grid":
                row, column, rows, columns = cells[key]
                layout.addWidget(widget, row, column, rows, columns)
                layout.setRowStretch(row, values.get("layout_stretch", 0))
                layout.setColumnStretch(column, values.get("layout_stretch", 0))
            else:
                role = QFormLayout.ItemRole.LabelRole if index % 2 == 0 else QFormLayout.ItemRole.FieldRole
                layout.setWidget(index // 2, role, widget)
        layout.invalidate()
        layout.activate()


class HorizontalLayout(LayoutContainer):
    kind = "horizontal"


class VerticalLayout(LayoutContainer):
    kind = "vertical"


class GridLayout(LayoutContainer):
    kind = "grid"


class FormLayout(LayoutContainer):
    kind = "form"


class Spacer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.native_item = QSpacerItem(0, 0)
        self.design_mode = True

    def configure(self, values):
        horizontal = values["orientation"] == "horizontal"
        grow = QSizePolicy.Policy.Expanding if values["expanding"] else QSizePolicy.Policy.Minimum
        x, y = (grow, QSizePolicy.Policy.Minimum) if horizontal else (QSizePolicy.Policy.Minimum, grow)
        self.native_item.changeSize(values["minimum_extent"] if horizontal else 0,
                                    values["minimum_extent"] if not horizontal else 0, x, y)
        self.setSizePolicy(x, y)
        self.setMinimumSize(self.native_item.minimumSize())
        self.setStyleSheet("border: 1px dashed #7b9ab6; background: #eef4f9;" if self.design_mode else "")

    def sizeHint(self):
        return self.native_item.sizeHint()


class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidget(QWidget())

    def configure(self, values):
        self.setWidgetResizable(values["widget_resizable"])
        if not values["widget_resizable"]:
            self.widget().resize(values["content_width"], values["content_height"])
        policies = {"as_needed": Qt.ScrollBarPolicy.ScrollBarAsNeeded, "always": Qt.ScrollBarPolicy.ScrollBarAlwaysOn,
                    "never": Qt.ScrollBarPolicy.ScrollBarAlwaysOff}
        self.setHorizontalScrollBarPolicy(policies[values["horizontal_policy"]])
        self.setVerticalScrollBarPolicy(policies[values["vertical_policy"]])


class Splitter(QSplitter):
    def configure(self, values):
        self.values = values
        self.setOrientation(Qt.Orientation.Horizontal if values["orientation"] == "horizontal" else Qt.Orientation.Vertical)
        self.setHandleWidth(values["handle_width"])
        self.setChildrenCollapsible(values["children_collapsible"])

    def set_children(self, entries):
        for index, (key, widget, values) in enumerate(entries):
            self.insertWidget(index, widget)
            self.setStretchFactor(index, values.get("layout_stretch", 0))
        sizes = [int(value) for value in self.values["sizes"]]
        self.setSizes(sizes if sizes else [100] * len(entries))


class StackedWidget(QStackedWidget):
    @property
    def pages(self):
        return [self.widget(index) for index in range(self.count())]

    def configure(self, values):
        self.values = values

    def set_pages(self, entries, index):
        wanted = [page for page, text in entries]
        for page in self.pages:
            if page not in wanted:
                self.removeWidget(page)
        for position, (page, text) in enumerate(entries):
            self.insertWidget(position, page)
        self.setCurrentIndex(index)
        for position, page in enumerate(self.pages):
            page.setVisible(position == index and page.property("page_visible") is not False)


class ToolBox(QToolBox):
    @property
    def pages(self):
        return [self.widget(index) for index in range(self.count())]

    def configure(self, values):
        self.values = values

    def set_pages(self, entries, index):
        wanted = [page for page, text in entries]
        for position in reversed(range(self.count())):
            if self.widget(position) not in wanted:
                self.removeItem(position)
        for position, (page, text) in enumerate(entries):
            current = self.indexOf(page)
            if current < 0:
                self.insertItem(position, page, text)
            elif current != position:
                self.removeItem(current)
                self.insertItem(position, page, text)
            self.setItemText(position, text)
            from PySide6.QtGui import QIcon, QPixmap
            from .easy_widgets import decoded_image
            picture = page.property("tab_icon") or ""
            self.setItemIcon(position, QIcon(QPixmap.fromImage(decoded_image(picture))) if picture else QIcon())
            self.setItemToolTip(position, page.toolTip())
        self.setCurrentIndex(index)


class MdiArea(QMdiArea):
    def configure(self, values):
        self.values = values
        self.setViewMode(QMdiArea.ViewMode.TabbedView if values["view_mode"] == "tabs" else QMdiArea.ViewMode.SubWindowView)
        self.setTabsClosable(True)

    def set_children(self, entries):
        for key, widget, values in entries:
            if widget not in self.subWindowList():
                self.addSubWindow(widget)
            widget.show()
            if values.get("maximized"):
                widget.showMaximized()
        if self.values["arrangement"] == "tile":
            self.tileSubWindows()
        elif self.values["arrangement"] == "cascade":
            self.cascadeSubWindows()


class MdiSubWindow(QMdiSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidget(QWidget())

    def configure(self, values):
        self.setWindowTitle(values["title"])


class TriggerWindow:
    def bind_trigger(self, button):
        previous = getattr(self, "_trigger", None)
        if previous is not None:
            try:
                previous.clicked.disconnect(self.open_dialog)
            except (RuntimeError, TypeError):
                pass
        self._trigger = button
        if button is not None:
            button.clicked.connect(self.open_dialog)

    def open_dialog(self, checked=False):
        self.show()
        self.raise_()
        self.activateWindow()

    def dispose(self):
        self.bind_trigger(None)
        self.close()


class DialogWindow(QDialog, TriggerWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.design_mode = True

    def configure(self, values):
        self.values = values
        flags = Qt.WindowType.Widget if self.design_mode else Qt.WindowType.Dialog
        self.setWindowFlags(flags)
        self.setWindowTitle(values["title"])
        self.setModal(values["modal"] and not self.design_mode)


class DockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidget(QWidget())

    def configure(self, values):
        self.values = values
        self.setWindowTitle(values["title"])
        features = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        for key, flag in (("closable", QDockWidget.DockWidgetFeature.DockWidgetClosable),
                          ("movable", QDockWidget.DockWidgetFeature.DockWidgetMovable),
                          ("floatable", QDockWidget.DockWidgetFeature.DockWidgetFloatable)):
            if values[key]:
                features |= flag
        self.setFeatures(features)


class WizardPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.complete = True

    def configure(self, values):
        self.setTitle(values["title"])
        self.setSubTitle(values["subtitle"])
        changed = self.complete != values["complete"]
        self.complete = values["complete"]
        if changed:
            self.completeChanged.emit()

    def isComplete(self):
        return self.complete


class Wizard(QWizard, TriggerWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.design_mode = True
        for button, label in ((QWizard.WizardButton.BackButton, "上一步"), (QWizard.WizardButton.NextButton, "下一步"),
                              (QWizard.WizardButton.FinishButton, "完成"), (QWizard.WizardButton.CancelButton, "取消")):
            self.setButtonText(button, label)

    @property
    def pages(self):
        return [self.page(index) for index in self.pageIds()]

    def currentIndex(self):
        return self.pageIds().index(self.currentId()) if self.currentId() in self.pageIds() else -1

    def configure(self, values):
        self.values = values
        self.setWindowFlags(Qt.WindowType.Widget if self.design_mode else Qt.WindowType.Dialog)
        self.setWindowTitle(values["title"])
        self.setWizardStyle({"modern": QWizard.WizardStyle.ModernStyle, "classic": QWizard.WizardStyle.ClassicStyle,
                             "mac": QWizard.WizardStyle.MacStyle}[values["wizard_style"]])

    def set_pages(self, entries, index):
        for key in self.pageIds():
            self.removePage(key)
        for position, (page, text) in enumerate(entries):
            self.setPage(position, page)
        self.setStartId(index)
        self.restart()


class DialogButtonBox(QDialogButtonBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = {}
        self.accepted.connect(self._accept_parent)
        self.rejected.connect(self._reject_parent)

    def configure(self, values):
        self.values = values
        buttons = QDialogButtonBox.StandardButton.NoButton
        for name in values["buttons"]:
            buttons |= BUTTONS[name]
        self.setStandardButtons(buttons)
        for name in values["buttons"]:
            self.button(BUTTONS[name]).setText(name)
        self.setOrientation(Qt.Orientation.Horizontal if values["orientation"] == "horizontal" else Qt.Orientation.Vertical)
        self.setCenterButtons(values["center_buttons"])

    def _dialog(self):
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QDialog):
            parent = parent.parentWidget()
        return parent if self.values.get("close_parent_dialog") else None

    def _accept_parent(self):
        dialog = self._dialog()
        if dialog is not None:
            dialog.accept()

    def _reject_parent(self):
        dialog = self._dialog()
        if dialog is not None:
            dialog.reject()


CONTAINER_FACTORIES = {
    "QHBoxLayout": HorizontalLayout, "QVBoxLayout": VerticalLayout, "QGridLayout": GridLayout,
    "QFormLayout": FormLayout, "QSpacerItem": Spacer, "QScrollArea": ScrollArea, "QSplitter": Splitter,
    "QStackedWidget": StackedWidget, "QToolBox": ToolBox, "QMdiArea": MdiArea, "QMdiSubWindow": MdiSubWindow,
    "QDialog": DialogWindow, "QDockWidget": DockWidget, "QWizard": Wizard, "QWizardPage": WizardPage,
    "QDialogButtonBox": DialogButtonBox,
}
