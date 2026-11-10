"""对象层级显示、选择联动与右键操作，父级调整复用文档命令。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QItemSelectionModel, QTimer, Qt, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QWidget

from core.document import DocumentSession
from resources.icons import ui_icon


class ObjectTree(QTreeWidget):
    context_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("objectTree")
        self.setUniformRowHeights(True)
        self.setHeaderLabels(["对象", "类型"])
        self.setIndentation(15)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(130)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(1, 64)
        self.document: DocumentSession | None = None
        self._unsubscribe: Callable[[], None] | None = None
        self._items: dict[str, QTreeWidgetItem] = {}
        self._refreshing = False
        self._pending = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh)
        self.before_selection: Callable[[], bool] | None = None
        self._structure: tuple[tuple[object, ...], ...] = ()
        self.itemSelectionChanged.connect(self._selected)

    def bind(self, document: DocumentSession | None) -> None:
        if self.document:
            self.document.selection_changed.disconnect(self.select_node)
        if self._unsubscribe:
            self._unsubscribe()
        self.document = document
        self._structure = ()
        self._unsubscribe = None
        if document:
            document.selection_changed.connect(self.select_node)
            self._unsubscribe = document.subscribe(lambda change: self.queue_refresh())
        self.refresh()

    def queue_refresh(self) -> None:
        if not self._pending:
            self._pending = True
            self._refresh_timer.start(0)

    def refresh(self) -> None:
        self._pending = False
        self._refresh_timer.stop()
        self._refreshing = True
        try:
            if self.document is None or self.document.closed:
                self.clear()
                self._items.clear()
                self._structure = ()
                return
            model = self.document.model
            structure = tuple((node.id, node.parent_id, node.slot, node.object_order) for node in model.nodes.values())
            if structure == self._structure:
                # 属性修改只更新行文字，保留折叠状态、滚动位置和当前索引。
                for key, item in self._items.items():
                    node = model.nodes[key]
                    spec = self.document.registry.get(node.type_id)
                    item.setText(0, node.name)
                    item.setText(1, spec.label if spec else "未知组件")
                    item.setToolTip(0, node.name)
                    item.setToolTip(1, spec.label if spec else "未知组件")
                return
            expanded = {key: item.isExpanded() for key, item in self._items.items()}
            scroll = self.verticalScrollBar().value()
            self.clear()
            self._items.clear()
            children: dict[str | None, list[str]] = {}
            for node in model.nodes.values():
                children.setdefault(node.parent_id, []).append(node.id)
            pending = [model.root_id]
            while pending:
                key = pending.pop()
                node = model.nodes[key]
                spec = self.document.registry.get(node.type_id)
                parent = self._items.get(node.parent_id, self)
                item = QTreeWidgetItem(parent, [node.name, spec.label if spec else "未知组件"])
                icon_name = {"root": "window", "central": "central"}.get(node.slot, node.type_id.rsplit(".", 1)[-1])
                item.setIcon(0, ui_icon(icon_name))
                item.setData(0, Qt.ItemDataRole.UserRole, node.id)
                item.setToolTip(0, node.name)
                item.setToolTip(1, spec.label if spec else "未知组件")
                self._items[key] = item
                pending.extend(reversed(sorted(children.get(key, []), key=lambda child: (
                    model.nodes[child].slot, model.nodes[child].object_order))))
            self._structure = structure
            selected = self._items.get(self.document.selected_id)
            if selected is not None:
                self.setCurrentItem(selected, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
            for key, item in self._items.items():
                item.setSelected(key in self.document.selected_ids)
            for key, item in self._items.items():
                item.setExpanded(expanded.get(key, True))
            self.verticalScrollBar().setValue(scroll)
        finally:
            self._refreshing = False

    def select_node(self, node_id: str) -> None:
        if not self.document:
            return
        self._refreshing = True
        try:
            if node_id in self._items:
                self.setCurrentItem(self._items[node_id], 0, QItemSelectionModel.SelectionFlag.NoUpdate)
            selected = set(self.document.selected_ids)
            for key, item in self._items.items():
                item.setSelected(key in selected)
        finally:
            self._refreshing = False

    def _selected(self) -> None:
        item = self.currentItem()
        if not self._refreshing and self.document:
            if self.before_selection is not None and not self.before_selection():
                self.select_node(self.document.selected_id)
                return
            keys = tuple(item.data(0, Qt.ItemDataRole.UserRole) for item in self.selectedItems())
            primary = item.data(0, Qt.ItemDataRole.UserRole) if item else None
            if primary and not self.document.read_only and not self.document.editing_suspended:
                from core.hierarchy import ancestors, pages
                from core.commands.pages import select_page
                model = self.document.model
                for key in reversed((primary, *ancestors(model, primary))):
                    node = model.nodes[key]
                    if node.slot == "pages":
                        index = next(index for index, page in enumerate(pages(model, node.parent_id)) if page.id == key)
                        if model.nodes[node.parent_id].properties.get("current_index", 0) != index:
                            self.document.execute("查看选择夹页面", lambda candidate, p=node.parent_id, i=index:
                                select_page(candidate, self.document.registry, p, i))
            self.document.select_many(keys, primary=primary)
            self.select_node(self.document.selected_id)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        item = self.currentItem() if event.reason() == QContextMenuEvent.Reason.Keyboard else self.itemAt(event.pos())
        node_id = item.data(0, Qt.ItemDataRole.UserRole) if item else ""
        self.context_requested.emit(node_id, event.globalPos())
        event.accept()
