"""属性面板的日期时间编辑，存储值使用固定规范格式。"""

from __future__ import annotations

from PySide6.QtCore import QDate, QEvent, QObject, QTime, QTimeZone, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QDateTimeEdit, QWidget

from runtime.widget_properties import temporal_value
from .value_editors import scroll_parent


class TemporalEditor(QDateTimeEdit):
    editing_finished = Signal()

    def __init__(self, kind: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setTimeZone(QTimeZone.utc())
        self.setKeyboardTracking(False)
        self.setDateRange(QDate(1752, 1, 1), QDate(9999, 12, 31))
        self.setTimeRange(QTime(0, 0), QTime(23, 59, 59))
        self.setCalendarPopup(kind != "time")
        if kind != "time":
            self.calendarWidget().installEventFilter(self)
        self.setDisplayFormat({"date": "yyyy年MM月dd日", "time": "HH时mm分ss秒",
                               "datetime": "yyyy年MM月dd日 HH时mm分ss秒"}[kind])
        if kind == "date":
            self.setDate(temporal_value(value, kind))
        elif kind == "time":
            self.setTime(temporal_value(value, kind))
        else:
            self.setDateTime(temporal_value(value, kind))

    def value(self) -> str:
        if self.kind == "date":
            return self.date().toString("yyyy-MM-dd")
        if self.kind == "time":
            return self.time().toString("HH:mm:ss")
        return self.dateTime().toString("yyyy-MM-ddTHH:mm:ss")

    @property
    def choosing(self) -> bool:
        """保存回执等刷新不能打断用户正在操作的下拉日历。"""
        return self.kind != "time" and self.calendarWidget().isVisible()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if self.kind != "time" and watched is self.calendarWidget() and event.type() == QEvent.Type.Hide:
            self.editing_finished.emit()
        return super().eventFilter(watched, event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        scroll_parent(self, event)
