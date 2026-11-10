"""属性编辑通过文档命令提交，控件中文名由元数据提供。"""

from __future__ import annotations

from layout.containers import PAGE_TYPES, managed_child

import logging
from typing import Any, Callable

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QKeySequence
from PySide6.QtWidgets import (
    QAbstractSpinBox, QApplication, QCheckBox, QDoubleSpinBox, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
    QKeySequenceEdit, QPushButton, QSizePolicy, QSpinBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.commands.nodes import set_property
from core.commands.hierarchy import reparent_node
from core.hierarchy import ancestors
from core.document import DocumentSession
from core.errors import DesignerError
from core.events import event_enabled, set_event_enabled
from resources.colors import COLORS, MUTED, TEXT
from .color_editor import ColorEditor
from .content_editor import ContentEditor
from .temporal_editor import TemporalEditor
from .image_editor import ImageEditor
from .font_editor import FontFamilyEditor, FontSizeEditor
from .value_editors import ChoiceEditor, DecimalEditor, IntegerEditor

logger = logging.getLogger(__name__)


class PropertyPanel(QWidget):
    error = Signal(str)
    menu_edit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("propertyPanel")
        self.setMinimumWidth(280)
        self.document: DocumentSession | None = None
        self.editors: dict[str, QWidget] = {}
        self._unsubscribe: Callable[[], None] | None = None
        self._refreshing = False
        self._pending = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh)
        self._row_timer = QTimer(self)
        self._row_timer.setSingleShot(True)
        self._row_timer.timeout.connect(self._sync_row_sizes)
        self._node_id = ""
        self._dirty_values: set[str] = set()
        self._deferred_refresh = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 6, 7, 6)
        layout.setSpacing(6)
        self.heading = QLabel("尚未选择对象")
        self.heading.setTextFormat(Qt.TextFormat.PlainText)
        self.heading.setObjectName("panelHeading")
        self.heading.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.heading)
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索属性或事件")
        self.search.setToolTip("按中文属性或事件名筛选，例如：边框、背景、被单击。")
        self.search.setAccessibleName("搜索属性")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        self.validation_message = QLabel()
        self.validation_message.setTextFormat(Qt.TextFormat.PlainText)
        self.validation_message.setWordWrap(True)
        self.validation_message.setObjectName("propertyValidationMessage")
        self.validation_message.setStyleSheet(f"color: {COLORS['error']};")
        self.validation_message.hide()
        layout.addWidget(self.validation_message)
        self.tree = QTreeWidget()
        self.tree.setObjectName("propertyTree")
        self.tree.setHeaderLabels(["属性", "属性值"])
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(12)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(0, 110)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tree)
        self.tree.setToolTip("文字和数值按回车或离开输入框应用。")

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.FontChange) and hasattr(self, "_row_timer"):
            self._row_timer.start(0)

    def _sync_row_sizes(self) -> None:
        # QSS and inherited fonts can arrive after editors were inserted.
        minimum = max(self.property("workbench_row_height") or 28, self.tree.fontMetrics().height() + 6)
        for index in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(index)
            if group.childCount():
                font = QFont(self.tree.font())
                font.setBold(True)
                group.setFont(0, font)
                group.setSizeHint(0, QSize(0, minimum))
            for row in range(group.childCount()):
                item = group.child(row)
                for column in (0, 1):
                    editor = self.tree.itemWidget(item, column)
                    if editor is not None:
                        editor.ensurePolished()
                        item.setSizeHint(column, QSize(0, max(minimum, editor.sizeHint().height())))
        # Reposition persistent cell editors after font or density changes.
        self.tree.doItemsLayout()

    def sync_font_metrics(self) -> None:
        self._row_timer.start(0)

    def bind(self, document: DocumentSession | None) -> None:
        if self.document:
            self.document.selection_changed.disconnect(self.queue_refresh)
        if self._unsubscribe:
            self._unsubscribe()
        self.document = document
        self.validation_message.hide()
        self._node_id = ""
        self._unsubscribe = None
        if document:
            document.selection_changed.connect(self.queue_refresh)
            self._unsubscribe = document.subscribe(lambda change: self.queue_refresh())
        self.refresh()

    def queue_refresh(self, node_id: str = "") -> None:
        if not self._pending:
            self._pending = True
            self._refresh_timer.start(0)

    def refresh(self) -> None:
        self._pending = False
        self._refresh_timer.stop()
        document = self.document
        if document and not document.closed and document.selected_id == self._node_id:
            if self._dirty_values:
                self._deferred_refresh = True
                return
            for editor in self.editors.values():
                if isinstance(editor, (ColorEditor, ContentEditor, TemporalEditor, ImageEditor, ChoiceEditor)) and editor.choosing:
                    self._deferred_refresh = True
                    return
                text_edit = self._text_editor(editor)
                if text_edit and text_edit.isModified():
                    # 保存回执或其他对象的变化不能清空用户尚未提交的输入。
                    self._deferred_refresh = True
                    return
        self._refreshing = True
        self._deferred_refresh = False
        try:
            scroll = self.tree.verticalScrollBar().value()
            same_node = bool(document and document.selected_id == self._node_id)
            focus = QApplication.focusWidget()
            focus_key = next((key for key, editor in self.editors.items()
                              if focus is not None and (editor is focus or editor.isAncestorOf(focus))), None) if same_node else None
            focused_text = self._text_editor(self.editors[focus_key]) if focus_key else None
            text_cursor = focused_text.cursorPosition() if focused_text else 0
            selection_start = focused_text.selectionStart() if focused_text else -1
            selection_length = len(focused_text.selectedText()) if focused_text else 0
            collapsed = {self.tree.topLevelItem(i).text(0) for i in range(self.tree.topLevelItemCount())
                         if not self.tree.topLevelItem(i).isExpanded()} if same_node else {"高级", "行为", "事件"}
            self.tree.clear()
            self.editors.clear()
            self._dirty_values.clear()
            document = self.document
            if document is None or document.closed:
                self.heading.setText("尚未选择对象")
                self._node_id = ""
                return
            node = document.model.nodes[document.selected_id]
            geometry_editable = not managed_child(document.model, node.id) and all(not document.model.nodes[key].designer["locked"]
                                    for key in (node.id, *ancestors(document.model, node.id)))
            self._node_id = node.id
            self.validation_message.hide()
            spec = document.registry.get(node.type_id)
            if len(document.selected_ids) > 1:
                self.heading.setText(f"已选择 {len(document.selected_ids)} 个控件")
                self.validation_message.setText(f"排版基准：{node.name}。可整组移动、复制、删除或使用“排版”菜单。单独选择一个控件可编辑属性。")
                self.validation_message.setStyleSheet(f"color: {MUTED};")
                self.validation_message.show()
                self.tree.setHeaderLabels(["对象", "位置与尺寸"])
                self.search.setPlaceholderText("搜索所选对象")
                for key in document.selected_ids:
                    selected = document.model.nodes[key]
                    geometry = selected.geometry
                    details = (f"{geometry.x}, {geometry.y}　·　{geometry.width} × {geometry.height}" if geometry else "由容器管理")
                    item = QTreeWidgetItem([selected.name, details])
                    item.setToolTip(0, selected.name + ("（对齐基准）" if key == node.id else ""))
                    if key == node.id:
                        font = item.font(0)
                        font.setBold(True)
                        item.setFont(0, font)
                    self.tree.addTopLevelItem(item)
                self._filter(self.search.text())
                return
            self.validation_message.setStyleSheet(f"color: {COLORS['error']};")
            self.tree.setHeaderLabels(["属性", "属性值"])
            self.search.setPlaceholderText("搜索属性")
            self.heading.setText(f"{node.name} · {spec.label if spec else '未知组件'}")
            self.heading.setToolTip(self.heading.text())
            if not same_node:
                self.search.clear()
            groups: dict[str, QTreeWidgetItem] = {}
            group_order = {name: index for index, name in enumerate(("基本", "位置与尺寸", "容器", "布局", "布局项", "页面", "表头", "内容", "时钟", "对话框", "绘图", "数值", "日期时间", "窗口", "外观", "行为", "事件", "高级"))}

            def add(key: str, label: str, group: str, editor: QWidget, *, editable: bool = True,
                    span: bool = False) -> None:
                if group not in groups:
                    parent = QTreeWidgetItem([group])
                    position = sum(group_order.get(name, 99) <= group_order.get(group, 99) for name in groups)
                    self.tree.insertTopLevelItem(position, parent)
                    parent.setFirstColumnSpanned(True)
                    parent.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    font = parent.font(0)
                    font.setBold(True)
                    parent.setFont(0, font)
                    parent.setForeground(0, QBrush(QColor(TEXT)))
                    parent.setSizeHint(0, QSize(0, 28))
                    groups[group] = parent
                item = QTreeWidgetItem(groups[group], [label])
                item.setFirstColumnSpanned(span)
                if span:
                    item.setData(0, Qt.ItemDataRole.UserRole, label)
                    item.setText(0, "")
                self.tree.setItemWidget(item, 0 if span else 1, editor)
                editor.ensurePolished()
                hint = editor.sizeHint()
                row_height = max(30 if span else 28, hint.height())
                item.setSizeHint(0 if span else 1, QSize(0, row_height))
                editor.setEnabled(editable and not document.read_only and not document.editing_suspended)
                self.editors[key] = editor
                editor.setProperty("property_key", key)
                if isinstance(editor, (ChoiceEditor, TemporalEditor, ColorEditor)):
                    editor.editing_finished.connect(self.queue_refresh)
                if isinstance(editor, TemporalEditor):
                    editor.dateTimeChanged.connect(lambda value, member=key: self._mark_dirty(member))
                elif isinstance(editor, (QSpinBox, QDoubleSpinBox)):
                    editor.valueChanged.connect(lambda value, member=key: self._mark_dirty(member))

            for key, label, value, editable in (("name", "名称", node.name, True),
                                                  ("code_name", "代码名称", node.code_name, False)):
                editor = QLineEdit(value)
                add(key, label, "高级" if key == "code_name" else "基本", editor, editable=editable)
                if key == "code_name":
                    editor.setReadOnly(True)
                    editor.setEnabled(True)
                    editor.setToolTip("此名称由设计器维护，可选中复制，用于导出项目的业务代码。")
                if editable:
                    editor.editingFinished.connect(lambda member=key, control=editor: self._commit(member, control.text()))
            if node.slot in {"root", "menu_bar", "menu"}:
                editor = QPushButton("编辑菜单…")
                editor.clicked.connect(self.menu_edit_requested)
                add("menu_editor", "菜单", "基本", editor)
            if node.geometry:
                for fields in ((("x", "位置X"), ("y", "位置Y")), (("width", "宽度"), ("height", "高度"))):
                    pair = QWidget()
                    row = QHBoxLayout(pair)
                    row.setContentsMargins(8, 1, 1, 1)
                    row.setSpacing(5)
                    pair_key = "pair_" + fields[0][0]
                    for member, label in fields:
                        editor = IntegerEditor()
                        editor.setRange(1, 16384) if member in {"width", "height"} else editor.setRange(-1_000_000, 1_000_000)
                        editor.setKeyboardTracking(False)
                        editor.setValue(getattr(node.geometry, member))
                        editor.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
                        editor.setMinimumWidth(0)
                        editor.setAccessibleName(label)
                        key = "geometry." + member
                        editor.setProperty("property_key", key)
                        self.editors[key] = editor
                        editor.valueChanged.connect(lambda value, member=key: self._mark_dirty(member))
                        caption = QLabel(label)
                        caption.setBuddy(editor)
                        row.addWidget(caption)
                        row.addWidget(editor, 1)
                        if node.slot == "root":
                            editor.setToolTip("窗口内容区尺寸，不包含系统标题栏和边框。" if member in {"width", "height"}
                                              else "运行时窗口的屏幕位置，不改变设计画布中的位置。")
                        if not geometry_editable:
                            editor.setToolTip("位置和尺寸由自动布局或锁定状态管理；布局项可设置伸缩和行列。")
                        editor.editingFinished.connect(lambda field=key, control=editor: self._commit(field, control.value()))
                    add(pair_key, "、".join(label for _, label in fields), "位置与尺寸", pair,
                        editable=geometry_editable, span=True)
                    self.editors.pop(pair_key)
            if node.slot == "children":
                editor = ChoiceEditor()
                for candidate in document.model.nodes.values():
                    parent_spec = document.registry.get(candidate.type_id)
                    if parent_spec and parent_spec.can_contain and candidate.type_id not in PAGE_TYPES and candidate.id != node.id and node.id not in ancestors(document.model, candidate.id):
                        editor.addItem(candidate.name, candidate.id)
                editor.setCurrentIndex(editor.findData(node.parent_id))
                editor.activated.connect(lambda index, control=editor: self._commit("parent_id", control.itemData(index)))
                editor.setToolTip("切换所属容器，尽量保留窗口内位置；目标放不下时会提示。")
                parent_editable = all(not document.model.nodes[key].designer["locked"] for key in (node.id, *ancestors(document.model, node.id)))
                add("parent_id", "所属容器", "容器", editor, editable=parent_editable)
                if managed_child(document.model, node.id):
                    order = IntegerEditor()
                    order.setRange(0, sum(child.parent_id == node.parent_id and child.slot == "children"
                                          for child in document.model.nodes.values()) - 1)
                    order.setValue(node.object_order)
                    order.setKeyboardTracking(False)
                    order.editingFinished.connect(lambda control=order: self._commit("layout_order", control.value()))
                    add("layout_order", "布局顺序", "布局项", order, editable=parent_editable)
            if spec and node.type_version == spec.version:
                for prop in spec.properties:
                    if prop.group == "布局项" and not managed_child(document.model, node.id):
                        continue
                    value = node.properties.get(prop.key, prop.default)
                    if node.type_id in PAGE_TYPES and prop.key == "current_index":
                        from core.hierarchy import pages
                        editor = ChoiceEditor()
                        for index, page in enumerate(pages(document.model, node.id)):
                            editor.addItem(page.properties.get("text", page.properties.get("title", page.name)), index)
                        editor.setCurrentIndex(value)
                        editor.activated.connect(lambda index, key=prop.key: self._commit(key, index))
                    elif prop.key == "navigation_page":
                        from core.hierarchy import pages
                        from layout.containers import NAVIGATION_PAGE_TYPES
                        editor = ChoiceEditor()
                        editor.addItem("不关联", "")
                        for container in document.model.nodes.values():
                            if container.type_id in NAVIGATION_PAGE_TYPES:
                                for page in pages(document.model, container.id):
                                    title = page.properties.get("text", page.name)
                                    editor.addItem(f"{container.name} / {title} ({page.code_name})", page.code_name)
                        editor.setCurrentIndex(editor.findData(value))
                        editor.activated.connect(lambda index, key=prop.key, control=editor: self._commit(key, control.itemData(index)))
                    elif prop.key == "trigger_control":
                        editor = ChoiceEditor()
                        editor.addItem("不绑定（业务代码调用）", "")
                        for button in document.model.nodes.values():
                            if button.type_id in {"builtin.button", "builtin.tool_button", "builtin.command_link_button"}:
                                editor.addItem(button.name, button.code_name)
                        editor.setCurrentIndex(editor.findData(value))
                        editor.activated.connect(lambda index, key=prop.key, control=editor: self._commit(key, control.itemData(index)))
                    elif prop.key in {"font_family", "current_font"}:
                        editor = FontFamilyEditor(value)
                        editor.activated.connect(lambda index, key=prop.key, control=editor: self._commit(key, control.itemData(index)))
                    elif prop.key == "font_size":
                        editor = FontSizeEditor(value, int(prop.minimum), int(prop.maximum))
                        editor.activated.connect(lambda index, key=prop.key, control=editor: self._commit(key, control.itemData(index)))
                    elif prop.value_type == "shortcut":
                        editor = QKeySequenceEdit(QKeySequence.fromString(value, QKeySequence.SequenceFormat.PortableText))
                        editor.setMaximumSequenceLength(node.properties.get("maximum_sequence_length", 1) if prop.key == "key_sequence" else 1)
                        editor.setClearButtonEnabled(True)
                        editor.editingFinished.connect(lambda key=prop.key, control=editor:
                                                       self._commit(key, control.keySequence().toString(QKeySequence.SequenceFormat.PortableText)))
                    elif prop.value_type == "image":
                        editor = ImageEditor(value, icon=prop.key in {"window_icon", "icon"})
                        editor.value_committed.connect(lambda picture, key=prop.key: self._commit(key, picture))
                        editor.error.connect(self.error)
                        editor.editing_finished.connect(self.queue_refresh)
                    elif prop.value_type in {"multiline", "string_list", "table", "tree"}:
                        editor = ContentEditor(prop, value, lambda value, key=prop.key: self._commit(key, value),
                                               column_default=node.properties.get("column_width", 100))
                        editor.editing_finished.connect(self.queue_refresh)
                    elif prop.key == "scale_children":
                        editor = QCheckBox("组件随窗口缩放")
                        editor.setChecked(value)
                        editor.setAccessibleName("组件随窗口缩放")
                        editor.toggled.connect(lambda checked, key=prop.key: self._commit(key, checked))
                    elif prop.value_type == "bool":
                        editor = QCheckBox("开启" if value else "关闭")
                        editor.setChecked(value)
                        editor.toggled.connect(lambda checked, control=editor: control.setText("开启" if checked else "关闭"))
                        editor.toggled.connect(lambda checked, key=prop.key: self._commit(key, checked))
                    elif prop.value_type == "enum":
                        editor = ChoiceEditor()
                        for option, label in prop.options:
                            editor.addItem(label, option)
                        editor.setCurrentIndex(editor.findData(value))
                        editor.activated.connect(lambda index, key=prop.key, control=editor: self._commit(key, control.itemData(index)))
                    elif prop.value_type in {"date", "time", "datetime"}:
                        editor = TemporalEditor(prop.value_type, value)
                        editor.editingFinished.connect(lambda key=prop.key, control=editor: self._commit(key, control.value()))
                    elif prop.value_type in {"int", "float"}:
                        editor = DecimalEditor() if prop.value_type == "float" else IntegerEditor()
                        if isinstance(editor, QDoubleSpinBox):
                            editor.setDecimals(6)
                        editor.setRange(prop.minimum, prop.maximum)
                        editor.setKeyboardTracking(False)
                        editor.setValue(value)
                        editor.editingFinished.connect(lambda key=prop.key, control=editor: self._commit(key, control.value()))
                    elif prop.value_type == "color":
                        editor = ColorEditor(value)
                        editor.value_committed.connect(lambda text, key=prop.key: self._commit(key, text))
                        editor.error.connect(self.error)
                    else:
                        editor = QLineEdit(value)
                        editor.editingFinished.connect(lambda key=prop.key, control=editor: self._commit(key, control.text()))
                    add(prop.key, prop.label, prop.group, editor, editable=not prop.read_only, span=prop.key == "scale_children")
                    if prop.description:
                        editor.setToolTip(prop.description)
                    if prop.key == "border_style":
                        editor.setToolTip("标准边框允许调整窗口大小；固定边框锁定运行时尺寸；无边框隐藏标题栏。")
                    if node.type_id == "builtin.line_edit":
                        tips = {
                            "text": "设计时在此修改初始文本；按 F5 后可在预览窗口中输入。",
                            "placeholder_text": "内容为空时显示的提示文字，与鼠标悬停的提示文本不同。",
                            "max_length": "按 Qt 文本长度计数，部分字符占两位；不能小于已有文本长度。",
                            "read_only": "只限制预览中的输入，仍可在设计器修改属性。",
                            "echo_mode": "控制画布和预览中的文字显示；项目文件保存初始文本，不作加密。",
                        }
                        if prop.key in tips:
                            editor.setToolTip(tips[prop.key])
                    if prop.key in {"minimize_button", "maximize_button", "close_button"}:
                        border = node.properties.get("border_style", "standard")
                        available = border != "none" and not (prop.key == "maximize_button" and border == "fixed")
                        editor.setEnabled(editor.isEnabled() and available)
                        editor.setToolTip("无边框时不显示窗口按钮；固定边框不提供最大化。")
                for event_spec in spec.events:
                    checked = event_enabled(document.model, node.id, event_spec.key)
                    editor = QCheckBox("已连接" if checked else "未连接")
                    editor.setChecked(checked)
                    editor.setAccessibleName(event_spec.label)
                    editor.setToolTip("勾选后连接此事件，取消勾选后不再连接；预览时显示触发提示，导出时自动连接处理函数。")
                    editor.toggled.connect(lambda value, control=editor: control.setText("已连接" if value else "未连接"))
                    editor.toggled.connect(lambda value, key=event_spec.key: self._commit("event." + key, value))
                    add("event." + event_spec.key, event_spec.label, "事件", editor,
                        editable=not (node.slot == "menu" and node.properties.get("separator", False)))
            self.tree.expandAll()
            for group in groups.values():
                if group.text(0) in collapsed:
                    group.setExpanded(False)
            self._filter(self.search.text())
            if focus_key in self.editors:
                editor = self.editors[focus_key]
                text_edit = self._text_editor(editor)
                target = text_edit if text_edit is not None else editor
                target.setFocus(Qt.FocusReason.OtherFocusReason)
                if text_edit is not None:
                    if selection_start >= 0:
                        text_edit.setSelection(selection_start, selection_length)
                    else:
                        text_edit.setCursorPosition(min(text_cursor, len(text_edit.text())))
            self.tree.verticalScrollBar().setValue(scroll if same_node else 0)
        finally:
            self._refreshing = False

    def _commit(self, key: str, value: Any) -> bool:
        document = self.document
        if self._refreshing or document is None or document.closed or document.selected_id != self._node_id:
            return True
        try:
            node_id = self._node_id
            if key.startswith("event."):
                document.execute("连接事件" if value else "断开事件", lambda model:
                                 set_event_enabled(model, document.registry, node_id, key[6:], value))
            else:
                document.execute("修改属性", lambda model: reparent_node(model, document.registry, node_id, value)
                                 if key == "parent_id" else set_property(model, document.registry, node_id, key, value))
            editor = self.editors.get(key)
            if isinstance(editor, QLineEdit):
                editor.setModified(False)
            elif isinstance(editor, QAbstractSpinBox):
                editor.lineEdit().setModified(False)
            elif isinstance(editor, ColorEditor):
                editor.line_edit.setModified(False)
            self._dirty_values.discard(key)
            self.validation_message.hide()
            if self._deferred_refresh:
                self.queue_refresh()
            return True
        except DesignerError as exc:
            message = str(exc)
            repeated = not self.validation_message.isHidden() and self.validation_message.text() == message
            self.validation_message.setText(message)
            self.validation_message.show()
            if not repeated:
                self.error.emit(message)
            self.queue_refresh()
            return False

    def _mark_dirty(self, key: str) -> None:
        # 步进按钮和上下键会清除文本修改标记，需要单独记录待提交值。
        if not self._refreshing:
            self._dirty_values.add(key)

    @staticmethod
    def _text_editor(editor: QWidget) -> QLineEdit | None:
        if isinstance(editor, QLineEdit):
            return editor
        if isinstance(editor, QAbstractSpinBox):
            return editor.lineEdit()
        if isinstance(editor, ColorEditor):
            return editor.line_edit
        return None

    def _filter(self, text: str) -> None:
        query = text.strip()
        if self.document and len(self.document.selected_ids) > 1:
            for index in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(index)
                item.setHidden(bool(query) and query not in item.text(0) and query not in item.text(1))
            return
        for index in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(index)
            matches = False
            for child_index in range(group.childCount()):
                item = group.child(child_index)
                keywords = item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)
                match = not query or query in keywords or query in group.text(0)
                item.setHidden(not match)
                matches |= match
            group.setHidden(not matches)
            if query and matches:
                group.setExpanded(True)

    def commit_pending(self) -> bool:
        focus = QApplication.focusWidget()
        for key, editor in tuple(self.editors.items()):
            if key == "code_name" or not editor.isEnabled():
                continue
            focused = focus is not None and (editor is focus or editor.isAncestorOf(focus))
            if isinstance(editor, QLineEdit) and (editor.isModified() or focused):
                if not self._commit(key, editor.text()):
                    editor.setFocus()
                    return False
                editor.setModified(False)
            if isinstance(editor, (QSpinBox, QDoubleSpinBox, TemporalEditor)) and (key in self._dirty_values or editor.lineEdit().isModified() or focused):
                editor.interpretText()
                if not self._commit(key, editor.value()):
                    editor.setFocus()
                    return False
                editor.lineEdit().setModified(False)
            if isinstance(editor, ColorEditor) and (editor.line_edit.isModified() or focused):
                if not self._commit(key, editor.line_edit.text()):
                    editor.line_edit.setFocus()
                    return False
                editor.line_edit.setModified(False)
        return True
