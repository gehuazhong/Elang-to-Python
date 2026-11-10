"""可搜索的组件能力清单，明确区分已实现和待接入的范围。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from core.registry import WidgetRegistry
from widgets.support import support_rows


class SupportDialog(QDialog):
    def __init__(self, registry: WidgetRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("组件支持清单")
        self.resize(1000, 650)
        layout = QVBoxLayout(self)
        count = sum(spec.toolbox for spec in registry.specs.values())
        text = QLabel(f"当前组件箱：{count} 类。下表同时列出未接入组件；已支持的属性可展开查看。\n"
                      "事件可在属性面板勾选连接；预览报告触发，导出自动连接对应处理函数。")
        text.setWordWrap(True)
        layout.addWidget(text)
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索中文组件、属性、事件或 Qt 类名")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["组件／属性", "支持状态", "容器规则", "保存／预览／导出", "说明"])
        self.tree.setColumnWidth(0, 195)
        self.tree.setColumnWidth(1, 90)
        self.tree.setColumnWidth(2, 110)
        self.tree.setColumnWidth(3, 145)
        self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for row in support_rows(registry):
            item = QTreeWidgetItem(self.tree, [row.label, row.status, row.parenting,
                                   "已接入" if row.type_id else "未接入", row.note])
            item.setToolTip(0, row.qt_class)
            item.setData(0, Qt.ItemDataRole.UserRole, row.qt_class + " " + row.category + " " + row.events)
            item.setToolTip(4, row.note)
            if row.type_id:
                spec = registry.require(row.type_id)
                for prop in spec.properties:
                    child = QTreeWidgetItem(item, [prop.label, "已接入", prop.group, "已接入", prop.description])
                    child.setToolTip(0, prop.key + (" → " + prop.qt_name if prop.qt_name else ""))
                for event in spec.events:
                    child = QTreeWidgetItem(item, [event.label, "已接入", "勾选连接", "已接入", "取消勾选即断开；已有业务文件保留。"])
                    child.setToolTip(0, event.qt_signal or event.qt_event)
        layout.addWidget(self.tree)
        buttons = QDialogButtonBox()
        buttons.addButton("关闭", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search.textChanged.connect(self.filter)

    def filter(self, query: str) -> None:
        query = query.strip().casefold()
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            match = not query or query in (item.text(0) + " " + item.text(1) + " " + item.data(0, Qt.ItemDataRole.UserRole)).casefold()
            child_match = False
            for child_index in range(item.childCount()):
                child = item.child(child_index)
                visible = match or query in (child.text(0) + " " + child.toolTip(0)).casefold()
                child.setHidden(not visible)
                child_match |= visible
            item.setHidden(not match and not child_match)
            item.setExpanded(bool(query and child_match and not match))
