"""在实际桌面检查启动工作台完整可达，特别覆盖高缩放小逻辑屏幕。"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolBar

from app.bootstrap import initialize
from app.main_window import MainWindow
from app.window_geometry import fit_startup_window
from core.storage import atomic_write
from widgets.builtin import create_registry


def main() -> None:
    application = QApplication([])
    initialize(application, configure_logging=False)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    try:
        fit_startup_window(window, restored=False)
        window.show()
        QTest.qWait(100)
        area = window.screen().availableGeometry()
        assert area.contains(window.frameGeometry()), "工作台含标题栏和边框的范围超出可用屏幕。"
        toolbar = window.findChild(QToolBar, "mainToolbar")
        assert window.zoom_combo.isVisible() and toolbar.rect().contains(window.zoom_combo.geometry())
        assert window.page.canvas.viewport().height() >= 100
        assert window.properties.tree.viewport().height() >= 100
        assert window.statusBar().isVisible()
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "可用逻辑屏幕": [area.x(), area.y(), area.width(), area.height()],
                  "窗口客户区": [window.width(), window.height()], "完整工作台可达": "通过",
                  "缩放入口与属性画布可用": "通过"}
        base = Path(__file__).resolve().parents[1] / "reports"
        name = f"启动屏幕适配_{round(window.devicePixelRatioF() * 100)}"
        assert window.grab().save(str(base / (name + ".png")))
        atomic_write(base / (name + ".json"), (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps(report, ensure_ascii=False))
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    main()
