"""设计器属性输入的公共交互：滚轮浏览面板，显式操作才修改值。"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QAbstractScrollArea, QApplication, QComboBox, QDoubleSpinBox, QProxyStyle,
    QSizePolicy, QSpinBox, QStyle, QStyleHintReturn, QStyleOption, QWidget,
)


def scroll_parent(widget: QWidget, event: QWheelEvent) -> None:
    """保留触控板位移和滚动阶段，向最近的滚动区转发一次。"""
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            viewport = parent.viewport()
            forwarded = QWheelEvent(viewport.mapFromGlobal(event.globalPosition()), event.globalPosition(),
                                    event.pixelDelta(), event.angleDelta(), event.buttons(), event.modifiers(),
                                    event.phase(), event.inverted(), event.source(), event.pointingDevice())
            QApplication.sendEvent(viewport, forwarded)
            # 原事件已转发，不能再向父级传播一次。
            event.accept()
            return
        parent = parent.parentWidget()
    event.ignore()


class IntegerEditor(QSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        scroll_parent(self, event)


class DecimalEditor(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        scroll_parent(self, event)


class ChoicePopupStyle(QProxyStyle):
    def styleHint(self, hint: QStyle.StyleHint, option: QStyleOption | None = None,
                  widget: QWidget | None = None, returnData: QStyleHintReturn | None = None) -> int:
        if hint == QStyle.StyleHint.SH_ComboBox_Popup:
            # 列表式弹层遵守行数上限，长选项列表不占满屏幕。
            return 0
        return super().styleHint(hint, option, widget, returnData)


class ChoiceEditor(QComboBox):
    editing_finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._choice_style = ChoicePopupStyle()
        self._choice_style.setParent(self)
        self.setStyle(self._choice_style)
        self.setEditable(False)
        self.setMaxVisibleItems(12)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(8)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)
        self.view().installEventFilter(self)

    @property
    def choosing(self) -> bool:
        return self.view().isVisible()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.view() and event.type() == QEvent.Type.Hide:
            self.editing_finished.emit()
        return super().eventFilter(watched, event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.choosing:
            super().wheelEvent(event)
        else:
            scroll_parent(self, event)
