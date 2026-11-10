"""易语言式菜单树编辑；确认前所有操作仅修改独立草稿。"""

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QKeySequenceEdit, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from core.commands.menus import add_menu, ensure_menu_bar, menu_children, move_menu, remove_menu, rename_menu
from core.errors import DesignerError, require
from core.events import event_enabled, set_event_enabled
from core.hierarchy import ancestors
from core.validation import validate_project


class MenuEditor(QDialog):
    def __init__(self, model, registry, parent=None, selected_id=None):
        draft, bar_id = ensure_menu_bar(model, registry)
        super().__init__(parent)
        self.setWindowTitle("菜单编辑器")
        self.setObjectName("menuEditor")
        self.resize(820, 560)
        self.setMinimumSize(700, 480)
        self.registry = registry
        self.original = model
        self.model, self.bar_id = draft, bar_id
        self.selected_id = None
        self._refreshing = False
        layout = QVBoxLayout(self)
        hint = QLabel("设置菜单标题和层级；右移成为上一项的子菜单，左移返回上一层。标题填 - 可设置分隔线。")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        body = QHBoxLayout()
        layout.addLayout(body, 1)
        left = QVBoxLayout()
        body.addLayout(left, 3)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["菜单标题", "名称"])
        self.tree.setColumnWidth(0, 240)
        self.tree.setUniformRowHeights(True)
        self.tree.currentItemChanged.connect(self._selection_changed)
        left.addWidget(self.tree, 1)
        self.buttons = {}
        for row in ((('add', '增加同级'), ('child', '增加子菜单'), ('separator', '插入分隔线'), ('delete', '删除')),
                    (('up', '上移'), ('down', '下移'), ('left', '左移'), ('right', '右移'))):
            buttons = QHBoxLayout()
            left.addLayout(buttons)
            for key, title in row:
                button = QPushButton(title)
                button.setAutoDefault(False)
                button.clicked.connect(lambda checked=False, operation=key: self.operate(operation))
                self.buttons[key] = button
                buttons.addWidget(button)
        self.fields = QGroupBox("菜单属性")
        body.addWidget(self.fields, 2)
        form = QFormLayout(self.fields)
        self.title_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.code_edit = QLineEdit()
        self.code_edit.setToolTip("Python 中通过 window.controls[代码名称] 访问菜单项。已有事件处理函数名称保持不变。")
        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setMaximumSequenceLength(1)
        self.shortcut_edit.setClearButtonEnabled(True)
        self.status_edit = QLineEdit()
        for title, field in (("标题", self.title_edit), ("名称", self.name_edit), ("代码名称", self.code_edit),
                             ("快捷键", self.shortcut_edit), ("状态提示", self.status_edit)):
            field.setAccessibleName(title)
            form.addRow(title, field)
        self.checkable = QCheckBox("可选中（点击切换勾选状态）")
        self.checked = QCheckBox("选中")
        self.disabled = QCheckBox("禁止")
        self.visible = QCheckBox("可视")
        self.separator = QCheckBox("分隔线")
        self.connected = QCheckBox("连接被单击事件")
        for box in (self.checkable, self.checked, self.disabled, self.visible, self.separator, self.connected):
            form.addRow(box)
        self.checked.toggled.connect(lambda value: self.checkable.setChecked(True) if value else None)
        self.checkable.toggled.connect(lambda value: self.checked.setChecked(False) if not value else None)
        self.separator.toggled.connect(self._separator_toggled)
        self.error_label = QLabel()
        self.error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.error_label.setObjectName("errorText")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        self.dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.dialog_buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        self.dialog_buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        self.dialog_buttons.accepted.connect(self.accept)
        self.dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(self.dialog_buttons)
        self._rebuild(selected_id)

    def _separator_toggled(self, value):
        if self._refreshing:
            return
        if value:
            self.checkable.setChecked(False)
            self.connected.setChecked(False)
            self.shortcut_edit.clear()
        for field in (self.checkable, self.checked, self.connected, self.shortcut_edit):
            field.setEnabled(not value)

    def _rebuild(self, selection=None):
        self._refreshing = True
        try:
            self.tree.clear()
            self.items = {}

            def append(parent_key, tree_parent):
                for node in menu_children(self.model, parent_key):
                    props = node.properties
                    label = "────────" if props.get("separator") else props["text"]
                    if not props.get("visible", True):
                        label += " （不可视）"
                    if not props.get("enabled", True):
                        label += " （禁止）"
                    item = QTreeWidgetItem(tree_parent, [label, node.name])
                    item.setData(0, Qt.ItemDataRole.UserRole, node.id)
                    self.items[node.id] = item
                    append(node.id, item)

            append(self.bar_id, self.tree)
            self.tree.expandAll()
            self.selected_id = selection if selection in self.items else next(iter(self.items), None)
            if self.selected_id:
                self.tree.setCurrentItem(self.items[self.selected_id])
        finally:
            self._refreshing = False
        self._load_fields()

    def _load_fields(self):
        self._refreshing = True
        try:
            node = self.model.nodes.get(self.selected_id)
            editable = bool(node and all(not self.model.nodes[key].designer["locked"]
                                        for key in (node.id, *ancestors(self.model, node.id))))
            self.fields.setEnabled(editable)
            for key, button in self.buttons.items():
                button.setEnabled(editable or key == "add" and node is None)
            self.buttons["separator"].setEnabled(editable and self.model.nodes[node.parent_id].slot == "menu")
            if node is None:
                for field in (self.title_edit, self.name_edit, self.code_edit, self.status_edit):
                    field.clear()
                self.shortcut_edit.clear()
                return
            values = self.registry.require(node.type_id).defaults().changed(**node.properties)
            self.title_edit.setText(values["text"])
            self.name_edit.setText(node.name)
            self.code_edit.setText(node.code_name)
            self.shortcut_edit.setKeySequence(QKeySequence.fromString(values["shortcut"], QKeySequence.SequenceFormat.PortableText))
            self.status_edit.setText(values["status_tip"])
            self.checkable.setChecked(values["checkable"])
            self.checked.setChecked(values["checked"])
            self.disabled.setChecked(not values["enabled"])
            self.visible.setChecked(values["visible"])
            self.separator.setChecked(values["separator"])
            self.connected.setChecked(event_enabled(self.model, node.id, "clicked"))
            for field in (self.checkable, self.checked, self.connected, self.shortcut_edit):
                field.setEnabled(not values["separator"])
            self.shortcut_edit.setEnabled(not values["separator"] and not menu_children(self.model, node.id))
        finally:
            self._refreshing = False

    def flush(self):
        if not self.selected_id or not self.fields.isEnabled():
            return True
        try:
            key = self.selected_id
            result = rename_menu(self.model, key, self.name_edit.text(), self.code_edit.text().strip())
            separator = self.separator.isChecked() or self.title_edit.text().strip() == "-"
            node = result.nodes[key]
            values = dict(text="-" if separator else self.title_edit.text(), separator=separator,
                          shortcut="" if separator else self.shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
                          checkable=not separator and self.checkable.isChecked(), checked=not separator and self.checked.isChecked(),
                          enabled=not self.disabled.isChecked(), visible=self.visible.isChecked(), status_tip=self.status_edit.text())
            result = result.with_nodes({key: replace(node, properties=node.properties.changed(**values))})
            if separator:
                result = replace(result, data=result.data.changed(connections=tuple(
                    connection.changed(enabled=False) if connection["source_id"] == key else connection
                    for connection in result.data["connections"])))
            else:
                result = set_event_enabled(result, self.registry, key, "clicked", self.connected.isChecked())
            validate_project(result)
            self.registry.validate(result)
            self.model = result
            self.error_label.clear()
            return True
        except DesignerError as exc:
            self.error_label.setText(str(exc))
            return False

    def _selection_changed(self, current, previous):
        if self._refreshing:
            return
        target = current.data(0, Qt.ItemDataRole.UserRole) if current else None
        if self.flush():
            self._rebuild(target)
        else:
            self._refreshing = True
            self.tree.setCurrentItem(previous)
            self._refreshing = False

    def operate(self, operation):
        if not self.flush():
            return
        try:
            key = self.selected_id
            if operation in {"add", "child", "separator"}:
                node = self.model.nodes.get(key)
                parent = key if operation == "child" and node else node.parent_id if node else self.bar_id
                result, selected = add_menu(self.model, self.registry, parent,
                                            after_id=key if operation != "child" else None, separator=operation == "separator")
            elif operation == "delete":
                require(key is not None, "请选择菜单项。")
                parent = self.model.nodes[key].parent_id
                siblings = menu_children(self.model, parent)
                index = next(i for i, node in enumerate(siblings) if node.id == key)
                result = remove_menu(self.model, key)
                remaining = menu_children(result, parent)
                selected = remaining[min(index, len(remaining) - 1)].id if remaining else parent
            else:
                require(key is not None, "请选择菜单项。")
                result, selected = move_menu(self.model, self.registry, key, operation), key
            validate_project(result)
            self.registry.validate(result)
            self.model = result
            self._rebuild(selected)
            if operation in {"add", "child"}:
                self.title_edit.setFocus()
                self.title_edit.selectAll()
        except DesignerError as exc:
            self.error_label.setText(str(exc))

    def accept(self):
        if not self.flush():
            return
        try:
            if not menu_children(self.model, self.bar_id):
                self.model = remove_menu(self.model, self.bar_id)
            validate_project(self.model)
            self.registry.validate(self.model)
        except DesignerError as exc:
            self.error_label.setText(str(exc))
            return
        super().accept()
