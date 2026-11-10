"""运行窗口拉伸适配，导出项目携带同一份实现。"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QMainWindow, QWidget

from .scaling import ScaleItem, Size, scale_layout

logger = logging.getLogger(__name__)


class WindowScaler(QObject):
    error = Signal(str)

    def __init__(self, root: QMainWindow, central: QWidget, base_size: Size,
                 items: tuple[ScaleItem, ...], controls: Mapping[str, QWidget]) -> None:
        super().__init__(root)
        self.central = central
        self.base_size = base_size
        self.items = items
        self.controls = dict(controls)
        self._applying = False
        self._disposed = False
        self._failed = False
        central.installEventFilter(self)
        self.apply()

    def apply(self) -> None:
        if self._disposed or self._applying:
            return
        self._applying = True
        try:
            area = self.central.contentsRect()
            if area.width() <= 0 or area.height() <= 0:
                return
            rectangles = scale_layout(self.items, self.base_size, (area.width(), area.height()))
            for item in self.items:
                if item.kind == "central":
                    continue
                widget = self.controls[item.key]
                x, y, width, height = rectangles[item.key]
                # 页面边界由选择夹定义；普通子控件相对父容器内容区。
                offset = widget.parentWidget().contentsRect().topLeft()
                widget.setGeometry(x + (offset.x() if item.kind != "pages" else 0),
                                   y + (offset.y() if item.kind != "pages" else 0), width, height)
            self._failed = False
        except Exception:
            if not self._failed:
                logger.exception("组件随窗口缩放失败，原项目数据未改变。")
                self.error.emit("组件随窗口缩放失败，详细原因已写入日志。")
            self._failed = True
        finally:
            self._applying = False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.central and event.type() in {QEvent.Type.Resize, QEvent.Type.Show}:
            self.apply()
        return False

    def dispose(self) -> None:
        if not self._disposed:
            self._disposed = True
            self.central.removeEventFilter(self)
            self.controls.clear()
            self.deleteLater()
