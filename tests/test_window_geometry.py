"""启动尺寸与已保存窗口位置在不同逻辑屏幕范围内的回归。"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QMainWindow

from app.window_geometry import fit_startup_window


@pytest.mark.parametrize("available", [QRect(0, 0, 960, 516), QRect(0, 0, 1280, 680),
                                        QRect(0, 0, 1920, 1040), QRect(-1920, 0, 1920, 1040)])
def test_initial_window_fits_available_logical_screen(qt_app: QApplication, available: QRect) -> None:
    window = QMainWindow()
    try:
        window.setMinimumSize(960, 620)
        window.resize(1280, 820)
        fit_startup_window(window, restored=False, available=available)
        assert window.width() <= available.width() - 40
        assert window.height() <= available.height() - 70
        assert available.contains(window.frameGeometry())
    finally:
        window.deleteLater()


def test_restored_window_keeps_valid_user_position(qt_app: QApplication) -> None:
    window = QMainWindow()
    try:
        window.setMinimumSize(960, 620)
        window.setGeometry(140, 180, 1000, 660)
        before = window.geometry()
        fit_startup_window(window, restored=True, available=QRect(0, 0, 1920, 1040))
        assert window.geometry() == before
    finally:
        window.deleteLater()


def test_restored_window_from_larger_screen_is_reachable(qt_app: QApplication) -> None:
    window = QMainWindow()
    try:
        window.setMinimumSize(960, 620)
        window.setGeometry(1920, 180, 1400, 900)
        available = QRect(0, 0, 960, 516)
        fit_startup_window(window, restored=True, available=available)
        assert available.contains(window.frameGeometry())
    finally:
        window.deleteLater()
