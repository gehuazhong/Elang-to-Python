"""设计画布、预览及导出共享的菜单组装。"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

MENU_KEYS = {"QMenuBar": {"bar_height"}, "QAction": {"shortcut", "separator"}}


def apply_menu_properties(widget, values):
    if isinstance(widget, QMenuBar):
        widget.setNativeMenuBar(False)
        widget.setFixedHeight(values["bar_height"])
    elif isinstance(widget, QAction):
        widget.setText(values["text"])
        widget.setSeparator(values["separator"])
        widget.setCheckable(values["checkable"])
        widget.setChecked(values["checked"])
        widget.setEnabled(values["enabled"])
        widget.setVisible(values["visible"])
        widget.setStatusTip(values["status_tip"])
        widget.setShortcut(QKeySequence.fromString(values["shortcut"], QKeySequence.SequenceFormat.PortableText))
        widget.setShortcutContext(Qt.ShortcutContext.WindowShortcut)


def arrange_menus(root, controls, records):
    children = {}
    for key, parent_key, slot in records:
        children.setdefault(parent_key, []).append(key)
    for key, parent_key, slot in records:
        widget = controls[key]
        if slot == "menu_bar":
            container = widget
            if root.menuWidget() is not container:
                root.setMenuBar(container)
        else:
            submenu = widget.menu()
            if children.get(key):
                if submenu is None:
                    submenu = QMenu(root)
                    submenu.setSeparatorsCollapsible(False)
                    widget.setMenu(submenu)
                    widget.destroyed.connect(submenu.deleteLater)
                submenu.setTitle(widget.text())
                submenu.setEnabled(widget.isEnabled())
                container = submenu
            else:
                if submenu is not None:
                    widget.setMenu(None)
                    submenu.deleteLater()
                continue
        for action in container.actions():
            container.removeAction(action)
        for child in children.get(key, ()):
            container.addAction(controls[child])
