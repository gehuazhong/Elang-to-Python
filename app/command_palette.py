"""Search the existing menu actions without duplicating command behavior."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QHeaderView, QLabel, QLineEdit, QMenu, QMenuBar,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
from shiboken6 import isValid


def menu_commands(menu: QMenuBar | QMenu, prefix: str = "") -> list[tuple[str, QAction]]:
    commands = []
    # Resolve child menus through QObject ownership. In PySide 6.11, querying
    # QAction.menu() on temporary wrappers can invalidate the attached QMenu.
    submenus = {child.menuAction(): child for child in
                menu.findChildren(QMenu, options=Qt.FindChildOption.FindDirectChildrenOnly)}
    for action in menu.actions():
        if action.isSeparator() or not action.isVisible():
            continue
        label = action.text().replace("&", "")
        title = f"{prefix} › {label}" if prefix else label
        if action in submenus:
            commands.extend(menu_commands(submenus[action], title))
        elif action.objectName() != "commandPaletteAction":
            commands.append((title, action))
    return commands


class CommandPalette(QDialog):
    def __init__(self, menu_bar: QMenuBar, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("commandPalette")
        self.setWindowTitle("搜索命令")
        self.setModal(True)
        self.resize(min(620, parent.width() - 48), 390)
        self.commands = menu_commands(menu_bar)
        self.selected_action: QAction | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("输入命令名称，例如：导出、网格、恢复布局")
        self.search.setAccessibleName("搜索命令")
        self.search.setClearButtonEnabled(True)
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.results = QTreeWidget()
        self.results.setObjectName("commandResults")
        self.results.setColumnCount(2)
        self.results.setHeaderHidden(True)
        self.results.setRootIsDecorated(False)
        self.results.setUniformRowHeights(True)
        self.results.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.results, 1)
        self.hint = QLabel()
        self.hint.setObjectName("secondaryText")
        layout.addWidget(self.hint)
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self.accept)
        self.results.itemClicked.connect(lambda *_: self.accept())
        self._filter("")
        self.move(parent.mapToGlobal(parent.rect().topLeft()) +
                  QPoint((parent.width() - self.width()) // 2, 72))

    def _filter(self, text: str) -> None:
        self.results.clear()
        words = text.strip().casefold().split()
        first_enabled = None
        for command_index, (title, action) in enumerate(self.commands):
            if not isValid(action) or not action.isVisible():
                continue
            shortcut = action.shortcut().toString()
            if not all(word in f"{title} {shortcut}".casefold() for word in words):
                continue
            marker = "  ✓" if action.isCheckable() and action.isChecked() else ""
            item = QTreeWidgetItem(self.results, [title + marker, shortcut])
            # QVariant must not retain a raw QObject pointer: a background save
            # can rebuild the recent-files menu while this dialog is open.
            item.setData(0, Qt.ItemDataRole.UserRole, command_index)
            item.setToolTip(0, action.toolTip() or title)
            item.setIcon(0, action.icon())
            item.setDisabled(not action.isEnabled())
            if first_enabled is None and action.isEnabled():
                first_enabled = item
        if first_enabled is not None:
            self.results.setCurrentItem(first_enabled)
        count = self.results.topLevelItemCount()
        self.hint.setText(f"{count} 个命令    ↑ ↓ 选择    Enter 执行    Esc 关闭" if count else
                          "没有匹配的命令，请尝试其他关键词。")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.search and isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                step = -1 if event.key() == Qt.Key.Key_Up else 1
                index = self.results.indexOfTopLevelItem(self.results.currentItem()) + step
                while 0 <= index < self.results.topLevelItemCount():
                    item = self.results.topLevelItem(index)
                    if not item.isDisabled():
                        self.results.setCurrentItem(item)
                        self.results.scrollToItem(item)
                        break
                    index += step
                return True
        return super().eventFilter(watched, event)

    def accept(self) -> None:
        item = self.results.currentItem()
        if item is not None and not item.isDisabled():
            action = self.commands[item.data(0, Qt.ItemDataRole.UserRole)][1]
            if isValid(action) and action.isEnabled() and action.isVisible():
                self.selected_action = action
                super().accept()

    def trigger_selected(self) -> None:
        action = self.selected_action
        if action is not None and isValid(action) and action.isEnabled() and action.isVisible():
            action.trigger()
