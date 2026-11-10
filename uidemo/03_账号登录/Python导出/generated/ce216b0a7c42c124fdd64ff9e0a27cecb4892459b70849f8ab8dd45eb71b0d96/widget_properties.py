"""画布、预览与独立导出共用的组件属性适配，不依赖设计器模型。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
from typing import Any

from PySide6.QtCore import QDate, QDateTime, QEvent, QTime, QTimeZone, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QCalendarWidget, QCheckBox, QComboBox, QDateEdit, QDateTimeEdit,
    QDoubleSpinBox, QFrame, QGroupBox, QHeaderView, QLabel, QLCDNumber, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QProgressBar, QRadioButton,
    QAbstractSlider, QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QTimeEdit, QTreeWidget, QTreeWidgetItem, QWidget,
)

logger = logging.getLogger(__name__)


def restore_content_margins(widget: QWidget, event: QEvent) -> None:
    margins = getattr(widget, "_design_content_margins", None)
    if margins is not None and not getattr(widget, "_restoring_margins", False) and event.type() in {
        QEvent.Type.StyleChange, QEvent.Type.FontChange, QEvent.Type.Polish, QEvent.Type.PolishRequest,
        QEvent.Type.Resize, QEvent.Type.LayoutRequest, QEvent.Type.ParentChange,
    }:
        widget._restoring_margins = True
        try:
            widget.setContentsMargins(*margins)
        finally:
            widget._restoring_margins = False


class ContainerGroupBox(QGroupBox):
    """在原生样式更新后保持项目明确声明的内容区。"""

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        restore_content_margins(self, event)
        return result


class ContainerFrame(QFrame):
    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        restore_content_margins(self, event)
        return result


ALIGNMENTS = {"left_vcenter": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
              "center": Qt.AlignmentFlag.AlignCenter,
              "right_vcenter": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter}
ECHO_MODES = {"normal": QLineEdit.EchoMode.Normal, "password": QLineEdit.EchoMode.Password,
              "no_echo": QLineEdit.EchoMode.NoEcho, "password_echo_on_edit": QLineEdit.EchoMode.PasswordEchoOnEdit}
ENUMS: dict[str, Mapping[str, Any]] = {
    "alignment": ALIGNMENTS,
    "echo_mode": ECHO_MODES,
    "layout_direction": {"left_to_right": Qt.LayoutDirection.LeftToRight, "right_to_left": Qt.LayoutDirection.RightToLeft},
    "orientation": {"horizontal": Qt.Orientation.Horizontal, "vertical": Qt.Orientation.Vertical},
    "frame_shape": {"none": QFrame.Shape.NoFrame, "box": QFrame.Shape.Box, "panel": QFrame.Shape.Panel, "styled": QFrame.Shape.StyledPanel},
    "line_wrap": {"none": QPlainTextEdit.LineWrapMode.NoWrap, "widget": QPlainTextEdit.LineWrapMode.WidgetWidth},
    "insert_policy": {"none": QComboBox.InsertPolicy.NoInsert, "bottom": QComboBox.InsertPolicy.InsertAtBottom, "top": QComboBox.InsertPolicy.InsertAtTop},
    "button_symbols": {"arrows": QAbstractSpinBox.ButtonSymbols.UpDownArrows, "plus_minus": QAbstractSpinBox.ButtonSymbols.PlusMinus, "none": QAbstractSpinBox.ButtonSymbols.NoButtons},
    "tick_position": {"none": QSlider.TickPosition.NoTicks, "above": QSlider.TickPosition.TicksAbove,
                      "below": QSlider.TickPosition.TicksBelow, "both": QSlider.TickPosition.TicksBothSides},
    "selection_mode": {"single": QAbstractItemView.SelectionMode.SingleSelection, "extended": QAbstractItemView.SelectionMode.ExtendedSelection,
                       "multi": QAbstractItemView.SelectionMode.MultiSelection, "none": QAbstractItemView.SelectionMode.NoSelection},
    "selection_behavior": {"items": QAbstractItemView.SelectionBehavior.SelectItems, "rows": QAbstractItemView.SelectionBehavior.SelectRows,
                           "columns": QAbstractItemView.SelectionBehavior.SelectColumns},
    "edit_triggers": {"none": QAbstractItemView.EditTrigger.NoEditTriggers, "double_click": QAbstractItemView.EditTrigger.DoubleClicked,
                      "all": QAbstractItemView.EditTrigger.AllEditTriggers},
    "frame_shadow": {"plain": QFrame.Shadow.Plain, "raised": QFrame.Shadow.Raised, "sunken": QFrame.Shadow.Sunken},
    "first_day": {"monday": Qt.DayOfWeek.Monday, "sunday": Qt.DayOfWeek.Sunday},
    "calendar_selection": {"single": QCalendarWidget.SelectionMode.SingleSelection, "none": QCalendarWidget.SelectionMode.NoSelection},
    "weekday_format": {"short": QCalendarWidget.HorizontalHeaderFormat.ShortDayNames, "long": QCalendarWidget.HorizontalHeaderFormat.LongDayNames,
                       "none": QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader},
    "week_numbers": {"none": QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader, "iso": QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers},
    "arrow_type": {"none": Qt.ArrowType.NoArrow, "up": Qt.ArrowType.UpArrow, "down": Qt.ArrowType.DownArrow,
                   "left": Qt.ArrowType.LeftArrow, "right": Qt.ArrowType.RightArrow},
    "tool_style": {"text": Qt.ToolButtonStyle.ToolButtonTextOnly, "icon": Qt.ToolButtonStyle.ToolButtonIconOnly,
                   "beside": Qt.ToolButtonStyle.ToolButtonTextBesideIcon, "under": Qt.ToolButtonStyle.ToolButtonTextUnderIcon},
    "segment_style": {"flat": QLCDNumber.SegmentStyle.Flat, "filled": QLCDNumber.SegmentStyle.Filled, "outline": QLCDNumber.SegmentStyle.Outline},
}
COMPOSITE_KEYS: dict[str, frozenset[str]] = {
    "QComboBox": frozenset({"items", "current_index"}),
    "QListWidget": frozenset({"items", "current_index"}),
    "QCheckBox": frozenset({"check_state"}),
    "QSpinBox": frozenset({"minimum", "maximum", "value"}),
    "QProgressBar": frozenset({"minimum", "maximum", "value"}),
    "QSlider": frozenset({"minimum", "maximum", "value"}),
    "QTableWidget": frozenset({"table_data", "show_horizontal_header", "show_vertical_header", "stretch_last_section", "column_width"}),
    "QTreeWidget": frozenset({"tree_data", "header_text", "expanded"}),
    **{name: frozenset({"minimum", "maximum", "value"}) for name in (
        "QDoubleSpinBox", "QDial", "QScrollBar", "QDateEdit", "QTimeEdit", "QDateTimeEdit", "QCalendarWidget")},
    **{name: frozenset({"content_left", "content_top", "content_right", "content_bottom"}) for name in ("QGroupBox", "QFrame")},
    "QLCDNumber": frozenset({"value"}),
}


def temporal_value(value: str, kind: str) -> QDate | QTime | QDateTime:
    if kind == "date":
        return QDate.fromString(value, "yyyy-MM-dd")
    if kind == "time":
        return QTime.fromString(value, "HH:mm:ss")
    # 使用无夏令时跳变的固定时区表达界面上的日历字段，不从宿主环境推断时间含义。
    return QDateTime(QDate.fromString(value[:10], "yyyy-MM-dd"), QTime.fromString(value[11:], "HH:mm:ss"), QTimeZone.utc())


def apply_content_margins(widget: QWidget, values: Mapping[str, Any]) -> None:
    """Qt 分组框在字体和样式初始化时重算边距，须在外观和几何设置后固定内容区。"""
    if "content_left" in values and isinstance(widget, (QFrame, QGroupBox)):
        widget.ensurePolished()
        widget._design_content_margins = tuple(values["content_" + side] for side in ("left", "top", "right", "bottom"))
        widget.setContentsMargins(*widget._design_content_margins)


def apply_column_widths(header: QHeaderView, data: Mapping[str, Any], default: int, stretch_last: bool) -> None:
    """逐列宽度优先于默认宽度；明确设置的末列不参与自动填满。"""
    widths = data.get("column_widths", (0,) * len(data["headers"]))
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    header.setMinimumSectionSize(1)
    header.setDefaultSectionSize(default)
    for column, width in enumerate(widths):
        header.resizeSection(column, width or default)
    header.setStretchLastSection(bool(stretch_last and widths and not widths[-1]))


def apply_widget_properties(widget: QWidget, values: Mapping[str, Any],
                            bindings: Iterable[tuple[str, str | None, str]]) -> None:
    """先配置行为，再填入集合，最后应用范围和选中值，避免 Qt 隐式截断。"""
    radio = isinstance(widget, QRadioButton)
    try:
        if isinstance(widget, QLabel):
            widget.setTextFormat(Qt.TextFormat.PlainText)
        if radio:
            # 增量重建或撤销时允许清除旧选中值，最终互斥由文档校验保证。
            widget.setAutoExclusive(False)
        meta = widget.metaObject()
        for key, qt_name, label in bindings:
            if qt_name is None or key == "visible" or (radio and key == "auto_exclusive"):
                continue
            value = values[key]
            if key in ENUMS:
                value = ENUMS[key][value]
            index = meta.indexOfProperty(qt_name)
            if index < 0 or not meta.property(index).write(widget, value):
                raise RuntimeError(f"无法设置“{widget.objectName()}”的“{label}”。")
        if isinstance(widget, (QSpinBox, QDoubleSpinBox, QAbstractSlider, QProgressBar)):
            widget.setRange(values["minimum"], values["maximum"])
            widget.setValue(values["value"])
        if isinstance(widget, QDateTimeEdit):
            widget.setTimeZone(QTimeZone.utc())
            if isinstance(widget, QTimeEdit):
                widget.setDate(QDate(2000, 1, 1))
                widget.setTimeRange(temporal_value(values["minimum"], "time"), temporal_value(values["maximum"], "time"))
                widget.setTime(temporal_value(values["value"], "time"))
            elif isinstance(widget, QDateEdit):
                widget.setTime(QTime(0, 0))
                widget.setDateRange(temporal_value(values["minimum"], "date"), temporal_value(values["maximum"], "date"))
                widget.setDate(temporal_value(values["value"], "date"))
            else:
                widget.setDateTimeRange(temporal_value(values["minimum"], "datetime"), temporal_value(values["maximum"], "datetime"))
                widget.setDateTime(temporal_value(values["value"], "datetime"))
        if isinstance(widget, QCalendarWidget):
            widget.setDateRange(temporal_value(values["minimum"], "date"), temporal_value(values["maximum"], "date"))
            widget.setSelectedDate(temporal_value(values["value"], "date"))
            widget.showSelectedDate()
            widget.setMinimumSize(1, 1)
        if isinstance(widget, QLCDNumber):
            if widget.checkOverflow(values["value"]):
                raise RuntimeError("液晶数字的显示位数不足。")
            widget.display(values["value"])
        if isinstance(widget, QCheckBox):
            widget.setCheckState({"unchecked": Qt.CheckState.Unchecked, "checked": Qt.CheckState.Checked,
                                  "partial": Qt.CheckState.PartiallyChecked}[values["check_state"]])
        if isinstance(widget, QComboBox):
            widget.clear()
            widget.addItems(list(values["items"]))
            widget.setCurrentIndex(values["current_index"])
        if isinstance(widget, QListWidget):
            widget.clear()
            for text in values["items"]:
                item = QListWidgetItem(text, widget)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            widget.setCurrentRow(values["current_index"])
        if isinstance(widget, QTableWidget):
            data = values["table_data"]
            widget.clear()
            widget.setColumnCount(len(data["headers"]))
            widget.setRowCount(len(data["rows"]))
            widget.setHorizontalHeaderLabels(list(data["headers"]))
            for row_index, row in enumerate(data["rows"]):
                for column, text in enumerate(row):
                    widget.setItem(row_index, column, QTableWidgetItem(text))
            widget.horizontalHeader().setVisible(values["show_horizontal_header"])
            widget.verticalHeader().setVisible(values["show_vertical_header"])
            apply_column_widths(widget.horizontalHeader(), data, values["column_width"], values["stretch_last_section"])
        if isinstance(widget, QTreeWidget) and "tree_data" in values:
            widget.clear()
            widget.setColumnCount(1)
            widget.setHeaderLabels([values["header_text"]])

            def append(items: Iterable[Mapping[str, Any]], parent: QTreeWidget | QTreeWidgetItem) -> None:
                for value in items:
                    item = QTreeWidgetItem(parent, [value["text"]])
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    append(value["children"], item)

            append(values["tree_data"], widget)
            widget.expandAll() if values["expanded"] else widget.collapseAll()
    except Exception:
        logger.exception("组件属性应用失败：%s", widget.objectName())
        raise
    finally:
        if radio:
            widget.setAutoExclusive(values.get("auto_exclusive", True))
