"""按可用逻辑屏幕安排首次启动尺寸，避免高缩放下底部超出屏幕。"""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QDockWidget, QMainWindow


def fit_startup_window(window: QMainWindow, *, restored: bool, available: QRect | None = None) -> None:
    screen = window.screen()
    if available is None:
        if screen is None:
            return
        available = screen.availableGeometry()
    # 预留系统标题栏、窗口边框及边缘距离，不缩小组件字体。
    maximum_width = max(1, available.width() - 40)
    maximum_height = max(1, available.height() - 70)
    window.setMinimumSize(min(960, maximum_width), min(620, maximum_height))
    if not restored and not getattr(window, "layout_restored", False) and available.height() < 620:
        output = window.findChild(QDockWidget, "output")
        toolbox = window.findChild(QDockWidget, "toolbox")
        objects = window.findChild(QDockWidget, "objects")
        if output is not None:
            output.hide()
        if toolbox is not None and objects is not None:
            window.tabifyDockWidget(toolbox, objects)
            toolbox.raise_()
    if restored and window.isMaximized():
        return
    width = min(window.width() if restored else 1280, maximum_width)
    height = min(window.height() if restored else 820, maximum_height)
    window.resize(width, height)
    if not restored or not available.contains(window.frameGeometry()):
        window.move(available.x() + (available.width() - window.width()) // 2,
                    available.y() + (available.height() - window.height()) // 2)
