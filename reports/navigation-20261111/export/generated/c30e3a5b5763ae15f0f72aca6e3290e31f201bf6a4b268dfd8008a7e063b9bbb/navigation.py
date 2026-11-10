"""Page navigation shared by the designer, preview and standalone exports."""

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QAbstractButton, QStackedWidget, QToolBox
from shiboken6 import isValid

from .easy_widgets import SelectionTabs


NAVIGATION_KEYS = {"navigation_page", "navigation_style"}
ACTIVE_PROPERTY = "uiplayNavigationActive"
SIDEBAR_STYLE = """
QAbstractButton {
    background: transparent; border: none; border-left: 3px solid transparent;
    border-radius: 5px; text-align: left; padding: 0px 12px;
}
QAbstractButton:hover, QAbstractButton:focus { background: rgba(128, 128, 128, 28); }
QAbstractButton:pressed { background: rgba(128, 128, 128, 48); }
QAbstractButton[uiplayNavigationActive="true"] {
    background: rgba(90, 150, 220, 42); border-left-color: palette(highlight);
}
QAbstractButton[uiplayNavigationActive="true"]:hover { background: rgba(90, 150, 220, 60); }
QAbstractButton[uiplayNavigationActive="true"]:pressed { background: rgba(90, 150, 220, 80); }
QAbstractButton:disabled { background: transparent; border-left-color: transparent; }
"""


def apply_navigation_style(widget, values):
    # Called after the normal stylesheet is restored on every property update.
    if isinstance(widget, QAbstractButton) and values.get("navigation_style") == "sidebar":
        custom = widget.styleSheet()
        if custom and "{" not in custom:
            custom = "QAbstractButton {" + custom + "}"
        widget.setStyleSheet(SIDEBAR_STYLE + "\n" + custom)


def set_active(button, active):
    if isValid(button) and button.property(ACTIVE_PROPERTY) is not active:
        button.setProperty(ACTIVE_PROPERTY, active)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()


class PageNavigation(QObject):
    def __init__(self, button, container, page, design_mode):
        super().__init__(button)
        self.button, self.container, self.page = button, container, page
        self.design_mode = design_mode
        self.connections = [container.currentChanged.connect(self.sync),
                            container.destroyed.connect(self.dispose), page.destroyed.connect(self.dispose)]
        if isinstance(container, SelectionTabs):
            self.connections.append(container.tabMoved.connect(self.sync))
        if not design_mode:
            self.connections.append(button.clicked.connect(self.activate))

    def index(self):
        if not isValid(self.container) or not isValid(self.page):
            return -1
        if isinstance(self.container, SelectionTabs):
            return next((index for index, page in enumerate(self.container.pages) if page is self.page), -1)
        return self.container.indexOf(self.page)

    @Slot()
    def activate(self):
        index = self.index()
        if index < 0:
            return
        if isinstance(self.container, SelectionTabs):
            if self.container.tab_bar.currentIndex() != index:
                self.container.set_current_page(index)
        elif self.container.currentIndex() != index:
            self.container.setCurrentIndex(index)
        self.sync()

    @Slot()
    def sync(self):
        index = self.index()
        current = (self.container.tab_bar.currentIndex() if isinstance(self.container, SelectionTabs)
                   else self.container.currentIndex()) if isValid(self.container) else -1
        set_active(self.button, index >= 0 and current == index)

    @Slot()
    def dispose(self):
        for connection in self.connections:
            QObject.disconnect(connection)
        self.connections.clear()
        if isValid(self.button):
            if getattr(self.button, "_page_navigation", None) is self:
                self.button._page_navigation = None
            set_active(self.button, False)
        self.deleteLater()


def configure_navigation(controls, records, design_mode=False):
    """Records use stable code names, while each click resolves the live page index."""
    records = {key: (parent, slot, values) for key, parent, slot, values in records}
    dirty = set()
    for key, button in controls.items():
        if not isinstance(button, QAbstractButton):
            continue
        values = records.get(key, (None, None, {}))[2]
        target = values.get("navigation_page", "")
        parent, slot, _ = records.get(target, (None, None, {}))
        container, page = controls.get(parent), controls.get(target)
        valid = slot == "pages" and isinstance(container, (SelectionTabs, QStackedWidget, QToolBox)) and page is not None
        previous = getattr(button, "_page_navigation", None)
        if previous is not None and (not valid or previous.container is not container
                                     or previous.page is not page or previous.design_mode != design_mode):
            previous.dispose()
            previous = None
            dirty.add(key)
        if valid:
            if previous is None:
                previous = PageNavigation(button, container, page, design_mode)
                button._page_navigation = previous
            previous.sync()
            dirty.add(key)
    return dirty


def dispose_navigation(controls):
    for widget in controls.values():
        binding = getattr(widget, "_page_navigation", None)
        if binding is not None and isValid(binding):
            binding.dispose()
