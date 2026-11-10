"""所属对象销毁时安全取消延迟调用，并释放回调引用。"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer


def defer(owner: QObject, callback: Callable[[], object]) -> None:
    # 使用所属定时器，避免取消临时回调后仍保留 Python 对象。
    timer = QTimer(owner)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.timeout.connect(timer.deleteLater)
    timer.start(0)
