"""多行文字、列表、表格与树形内容的中文编辑窗口。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QHBoxLayout, QInputDialog, QLabel,
    QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from core.errors import DesignerError
from core.metadata import PropertySpec
from core.models import thaw
from .value_editors import ChoiceEditor, IntegerEditor


class ContentDialog(QDialog):
    def __init__(self, spec: PropertySpec, value: Any, commit: Callable[[Any], bool],
                 parent: QWidget | None = None, *, column_default: int = 100) -> None:
        super().__init__(parent)
        self.spec, self.commit = spec, commit
        self.column_default = column_default
        self.column_widths: list[int] = []
        self._updating_columns = False
        self.setWindowTitle("编辑" + spec.label)
        self.resize(620, 440)
        layout = QVBoxLayout(self)
        help_text = {"multiline": "填写初始文本，换行会保留。",
                     "string_list": "双击修改项目；可以增加、删除或调整顺序。项目编号从零开始。",
                     "table": "双击单元格编辑、双击列标题改名。选择列后设置宽度，也可拖动列标题边界；列宽与数据一起保存。",
                     "tree": "双击修改文字；选择节点后可添加同级或子级。"}[spec.value_type]
        tip = QLabel(help_text)
        tip.setWordWrap(True)
        layout.addWidget(tip)
        self.table: QTableWidget | None = None
        self.tree: QTreeWidget | None = None
        self.text: QPlainTextEdit | None = None
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.error_label.setObjectName("errorText")
        toolbar = QHBoxLayout()

        def button(title: str, callback: Callable[[], None]) -> None:
            control = QPushButton(title)
            control.clicked.connect(callback)
            toolbar.addWidget(control)

        if spec.value_type == "multiline":
            self.text = QPlainTextEdit(value)
            self.text.setAccessibleName("多行文本内容")
            layout.addWidget(self.text)
        elif spec.value_type in {"string_list", "table"}:
            self.table = QTableWidget()
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setAlternatingRowColors(True)
            if spec.value_type == "string_list":
                headers, rows = ["项目文字"], [[item] for item in value]
            else:
                headers, rows = value["headers"], value["rows"]
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(list(headers))
            for row, cells in enumerate(rows):
                for column, text in enumerate(cells):
                    self.table.setItem(row, column, QTableWidgetItem(text))
            header = self.table.horizontalHeader()
            header.setStretchLastSection(spec.value_type == "string_list")
            if spec.value_type == "table":
                self.column_widths = list(value.get("column_widths", [0] * len(headers)))
                header.setMinimumSectionSize(1)
                header.setMaximumSectionSize(2000)
                header.setDefaultSectionSize(column_default)
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                for column, width in enumerate(self.column_widths):
                    header.resizeSection(column, width or column_default)
            self.table.horizontalHeader().sectionDoubleClicked.connect(self.rename_column)
            button("增加项目" if spec.value_type == "string_list" else "增加行", self.add_row)
            button("删除项目" if spec.value_type == "string_list" else "删除行", self.remove_row)
            button("上移", lambda: self.move_row(-1))
            button("下移", lambda: self.move_row(1))
            if spec.value_type == "table":
                button("增加列", self.add_column)
                button("删除列", self.remove_column)
            layout.addWidget(self.table)
        else:
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["节点文字"])
            self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

            def append(items: Any, parent_item: QTreeWidget | QTreeWidgetItem) -> None:
                for item in items:
                    created = self.make_tree_item(parent_item, item["text"])
                    append(item["children"], created)

            append(value, self.tree)
            self.tree.expandAll()
            button("增加同级", lambda: self.add_tree_item(False))
            button("增加子级", lambda: self.add_tree_item(True))
            button("删除节点", self.remove_tree_item)
            button("上移", lambda: self.move_tree_item(-1))
            button("下移", lambda: self.move_tree_item(1))
            layout.addWidget(self.tree)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        if spec.value_type == "table":
            widths_row = QHBoxLayout()
            widths_row.addWidget(QLabel("当前列"))
            self.column_choice = ChoiceEditor()
            self.column_choice.setAccessibleName("选择要设置宽度的列")
            widths_row.addWidget(self.column_choice, 1)
            widths_row.addWidget(QLabel("列宽"))
            self.column_width = IntegerEditor()
            self.column_width.setAccessibleName("当前列宽度")
            self.column_width.setRange(0, 2000)
            self.column_width.setSpecialValueText(f"默认（{column_default}）")
            self.column_width.setSuffix(" 像素")
            self.column_width.setToolTip("输入一到二千个逻辑像素；零表示使用组件的默认列宽。")
            widths_row.addWidget(self.column_width)
            self.fit_column = QPushButton("适应内容")
            self.fit_column.setToolTip("根据当前列标题和单元格内容计算列宽并保存。")
            widths_row.addWidget(self.fit_column)
            self.reset_column = QPushButton("恢复默认")
            widths_row.addWidget(self.reset_column)
            layout.addLayout(widths_row)
            self.column_choice.currentIndexChanged.connect(self.select_column)
            self.column_width.valueChanged.connect(self.set_column_width)
            self.fit_column.clicked.connect(self.fit_column_to_contents)
            self.reset_column.clicked.connect(lambda: self.column_width.setValue(0))
            self.table.horizontalHeader().sectionResized.connect(self.column_resized)
            self.table.horizontalHeader().sectionClicked.connect(self.column_choice.setCurrentIndex)
            self.table.currentCellChanged.connect(lambda row, column, old_row, old_column:
                                                 self.column_choice.setCurrentIndex(column) if column >= 0 else None)
            self.refresh_columns(0)
        layout.addWidget(self.error_label)
        buttons = QDialogButtonBox()
        buttons.addButton("确定", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if spec.value_type == "table":
            area = self.screen().availableGeometry()
            self.resize(min(680, area.width() - 32), min(480, area.height() - 64))

    def refresh_columns(self, column: int) -> None:
        with QSignalBlocker(self.column_choice):
            self.column_choice.clear()
            for index in range(self.table.columnCount()):
                item = self.table.horizontalHeaderItem(index)
                self.column_choice.addItem(f"{index + 1} · {item.text() if item else ''}")
            self.column_choice.setCurrentIndex(min(column, self.table.columnCount() - 1))
        self.select_column(self.column_choice.currentIndex())

    def select_column(self, column: int) -> None:
        available = 0 <= column < len(self.column_widths)
        for control in (self.column_choice, self.column_width, self.fit_column, self.reset_column):
            control.setEnabled(available)
        with QSignalBlocker(self.column_width):
            self.column_width.setValue(self.column_widths[column] if available else 0)

    def set_column_width(self, width: int) -> None:
        column = self.column_choice.currentIndex()
        if not 0 <= column < len(self.column_widths):
            return
        self.column_widths[column] = width
        self._updating_columns = True
        try:
            self.table.setColumnWidth(column, width or self.column_default)
        finally:
            self._updating_columns = False

    def column_resized(self, column: int, old_size: int, size: int) -> None:
        if self._updating_columns or not 0 <= column < len(self.column_widths):
            return
        self.column_widths[column] = size
        self.column_choice.setCurrentIndex(column)
        self.select_column(column)

    def fit_column_to_contents(self) -> None:
        column = self.column_choice.currentIndex()
        if column >= 0:
            self.table.resizeColumnToContents(column)
            self.column_width.setValue(self.table.columnWidth(column))

    def add_row(self) -> None:
        limit = 1000 if self.spec.value_type == "string_list" else 200
        if self.table.rowCount() >= limit:
            self.error_label.setText(f"最多允许 {limit} 行。")
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column in range(self.table.columnCount()):
            self.table.setItem(row, column, QTableWidgetItem(""))
        self.table.setCurrentCell(row, 0)

    def remove_row(self) -> None:
        if self.table.currentRow() >= 0:
            self.table.removeRow(self.table.currentRow())

    def move_row(self, delta: int) -> None:
        row = self.table.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self.table.rowCount():
            return
        for column in range(self.table.columnCount()):
            first, second = self.table.takeItem(row, column), self.table.takeItem(target, column)
            if second is not None:
                self.table.setItem(row, column, second)
            if first is not None:
                self.table.setItem(target, column, first)
        self.table.setCurrentCell(target, 0)

    def add_column(self) -> None:
        column = self.table.columnCount()
        if column >= 50:
            self.error_label.setText("最多允许五十列。")
            return
        self._updating_columns = True
        try:
            self.column_widths.append(0)
            self.table.insertColumn(column)
            self.table.setHorizontalHeaderItem(column, QTableWidgetItem(f"列{column + 1}"))
            self.table.setColumnWidth(column, self.column_default)
            for row in range(self.table.rowCount()):
                self.table.setItem(row, column, QTableWidgetItem(""))
        finally:
            self._updating_columns = False
        self.refresh_columns(column)

    def remove_column(self) -> None:
        column = self.column_choice.currentIndex()
        if column >= 0:
            self._updating_columns = True
            try:
                self.column_widths.pop(column)
                self.table.removeColumn(column)
            finally:
                self._updating_columns = False
            self.refresh_columns(column)

    def rename_column(self, column: int) -> None:
        if self.spec.value_type != "table":
            return
        old = self.table.horizontalHeaderItem(column)
        value, accepted = QInputDialog.getText(self, "修改列标题", "列标题", text=old.text() if old else "")
        if accepted:
            self.table.setHorizontalHeaderItem(column, QTableWidgetItem(value))
            self.refresh_columns(column)

    @staticmethod
    def make_tree_item(parent: QTreeWidget | QTreeWidgetItem, text: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parent, [text])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        return item

    def add_tree_item(self, child: bool) -> None:
        current = self.tree.currentItem()
        parent = (current if child else current.parent()) if current else None
        ancestor, depth = parent, 1
        while ancestor is not None:
            depth += 1
            ancestor = ancestor.parent()
        count, pending = 0, [self.tree.invisibleRootItem()]
        while pending:
            item = pending.pop()
            count += item.childCount()
            pending.extend(item.child(index) for index in range(item.childCount()))
        if depth > 12 or count >= 1000:
            self.error_label.setText("树形内容最多允许十二层、一千个节点。")
            return
        item = self.make_tree_item(parent if parent is not None else self.tree, "新节点")
        if parent:
            parent.setExpanded(True)
        self.tree.setCurrentItem(item)
        self.tree.editItem(item, 0)

    def remove_tree_item(self) -> None:
        item = self.tree.currentItem()
        if item:
            parent = item.parent() or self.tree.invisibleRootItem()
            parent.takeChild(parent.indexOfChild(item))

    def move_tree_item(self, delta: int) -> None:
        item = self.tree.currentItem()
        if item:
            parent = item.parent() or self.tree.invisibleRootItem()
            index = parent.indexOfChild(item)
            if 0 <= index + delta < parent.childCount():
                parent.takeChild(index)
                parent.insertChild(index + delta, item)
                self.tree.setCurrentItem(item)

    def value(self) -> Any:
        if self.text is not None:
            return self.text.toPlainText()
        if self.table is not None:
            rows = [[self.table.item(row, column).text() if self.table.item(row, column) is not None else ""
                     for column in range(self.table.columnCount())] for row in range(self.table.rowCount())]
            if self.spec.value_type == "string_list":
                return [row[0] for row in rows]
            result = {"headers": [self.table.horizontalHeaderItem(column).text() if self.table.horizontalHeaderItem(column) else ""
                                  for column in range(self.table.columnCount())], "rows": rows}
            if any(self.column_widths):
                result["column_widths"] = list(self.column_widths)
            return result

        def collect(parent: QTreeWidgetItem) -> list[dict[str, Any]]:
            return [{"text": parent.child(index).text(0), "children": collect(parent.child(index))}
                    for index in range(parent.childCount())]

        return collect(self.tree.invisibleRootItem())

    def accept(self) -> None:
        # 先让单元格编辑器提交当前文字，再读取数据；错误时保留整份草稿。
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        try:
            value = self.spec.normalize(self.value())
            if not self.commit(value):
                self.error_label.setText("属性未能应用，请检查属性面板提示；编辑内容已保留。")
                return
        except DesignerError as exc:
            self.error_label.setText(str(exc))
            return
        super().accept()


class ContentEditor(QWidget):
    editing_finished = Signal()

    def __init__(self, spec: PropertySpec, value: Any, commit: Callable[[Any], bool],
                 parent: QWidget | None = None, *, column_default: int = 100) -> None:
        super().__init__(parent)
        self.spec, self.current_value, self.commit = spec, value, commit
        self.column_default = column_default
        self.choosing = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(self.summary(spec, value))
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setToolTip(label.text())
        layout.addWidget(label, 1)
        self.button = QPushButton("图标…" if spec.key == "svg_data" else "编辑…")
        self.button.setAccessibleName("编辑" + spec.label)
        self.button.clicked.connect(self.choose)
        layout.addWidget(self.button)

    @staticmethod
    def summary(spec: PropertySpec, value: Any) -> str:
        if spec.key == "svg_data":
            from resources.svg_icons import ICON_BY_KEY, identify_icon
            icon = identify_icon(value)
            return ICON_BY_KEY[icon[0]].label if icon else "自定义 SVG"
        if spec.value_type == "multiline":
            return "空文本" if not value else f"{len(value.splitlines())} 行文字"
        if spec.value_type == "table":
            return f"{len(value['rows'])} 行 × {len(value['headers'])} 列"
        if spec.value_type == "tree":
            return f"{len(value)} 个根节点"
        return f"{len(value)} 个项目"

    def choose(self) -> None:
        self.choosing = True
        dialog = None
        try:
            if self.spec.key == "svg_data":
                from .svg_editor import SvgDialog
                dialog = SvgDialog(self.spec, self.current_value, self.commit, self)
            else:
                dialog = ContentDialog(self.spec, thaw(self.current_value), self.commit, self, column_default=self.column_default)
            dialog.exec()
        finally:
            if dialog is not None:
                dialog.deleteLater()
            self.choosing = False
            self.editing_finished.emit()
