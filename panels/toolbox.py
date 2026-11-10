"""可搜索的中文组件箱，拖放和双击共用注册表。"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QDrag, QFont, QIcon
from PySide6.QtWidgets import QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from core.registry import WidgetRegistry
from designer.mime import component_mime
from resources.icons import ui_icon


def component_icon(type_id: str) -> QIcon:
    return ui_icon(type_id.rsplit(".", 1)[-1])


class ComponentTree(QTreeWidget):
    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        item = self.currentItem()
        type_id = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not type_id:
            return
        drag = QDrag(self)
        drag.setMimeData(component_mime(type_id))
        drag.setPixmap(item.icon(0).pixmap(28, 28))
        drag.exec(Qt.DropAction.CopyAction)


class ToolboxPanel(QWidget):
    create_requested = Signal(str)

    def __init__(self, registry: WidgetRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("toolboxPanel")
        self.setMinimumWidth(182)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(6)
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索组件")
        self.search.setAccessibleName("搜索组件")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.tree = ComponentTree()
        self.tree.setObjectName("componentTree")
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setDragEnabled(True)
        self.tree.setIconSize(QSize(18, 18))
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        layout.addWidget(self.tree)
        self.empty_hint = QLabel("没有匹配的组件")
        self.empty_hint.setObjectName("secondaryText")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.hide()
        layout.addWidget(self.empty_hint)
        tip = QLabel("拖入画布，或双击添加")
        tip.setObjectName("secondaryText")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        groups: dict[str, QTreeWidgetItem] = {}
        basic = tuple("builtin." + kind for kind in ("button", "label", "line_edit", "radio_button", "group_box", "drawing_board",
                      "list_widget", "timer", "common_dialog", "picture_box", "tab_widget", "check_box", "combo_box", "super_list", "tool_bar", "status_bar"))
        ordered = sorted(registry.specs.values(), key=lambda spec: basic.index(spec.type_id) if spec.type_id in basic else len(basic))
        for spec in ordered:
            if not spec.toolbox:
                continue
            group_name = "常用组件" if spec.type_id in basic else spec.group
            if group_name not in groups:
                group = QTreeWidgetItem(self.tree, [group_name])
                group.setFlags(Qt.ItemFlag.ItemIsEnabled)
                font = group.font(0)
                font.setBold(True)
                group.setFont(0, font)
                groups[group_name] = group
            label = "编辑框" if spec.type_id == "builtin.line_edit" else spec.label
            item = QTreeWidgetItem(groups[group_name], [label])
            item.setData(0, Qt.ItemDataRole.UserRole, spec.type_id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, " ".join((spec.label, *spec.aliases)))
            item.setIcon(0, component_icon(spec.type_id))
            item.setSizeHint(0, QSize(120, 28))
            description = "添加后出现在画布下方的非可视组件区。" if spec.slot == "non_visual" else "拖入窗口，或双击创建。"
            item.setToolTip(0, spec.label + "：" + description + (" 常用名称：" + "、".join(spec.aliases) if spec.aliases else ""))
        self.tree.expandAll()
        self.search.textChanged.connect(self._filter)
        self.tree.itemDoubleClicked.connect(self._double_clicked)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange and hasattr(self, "tree"):
            self.sync_font_metrics()

    def sync_font_metrics(self):
        height = max(self.property("workbench_row_height") or 28, self.tree.fontMetrics().height() + 6)
        for index in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(index)
            font = QFont(self.tree.font())
            font.setBold(True)
            group.setFont(0, font)
            group.setSizeHint(0, QSize(120, height))
            for row in range(group.childCount()):
                group.child(row).setSizeHint(0, QSize(120, height))
        self.tree.doItemsLayout()

    def _filter(self, text: str) -> None:
        needle = text.strip().casefold()
        any_visible = False
        for index in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(index)
            visible = False
            for child_index in range(group.childCount()):
                item = group.child(child_index)
                searchable = item.data(0, Qt.ItemDataRole.UserRole + 1) + " " + item.data(0, Qt.ItemDataRole.UserRole)
                match = needle in searchable.casefold()
                item.setHidden(not match)
                visible |= match
            group.setHidden(not visible)
            if needle and visible:
                group.setExpanded(True)
            any_visible |= visible
        self.empty_hint.setVisible(not any_visible)

    def _double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        type_id = item.data(0, Qt.ItemDataRole.UserRole)
        if type_id:
            self.create_requested.emit(type_id)
