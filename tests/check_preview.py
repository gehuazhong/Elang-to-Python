"""桌面预览验收：真实进程、原生按钮交互、停止与截图。"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolBar

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.events import set_event_enabled
from tests.test_storage import wait_for
from widgets.builtin import create_registry


def main() -> int:
    app = QApplication([])
    initialize(app)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    try:
        window.show()
        document = window.document
        label = window.page.canvas.create_component("builtin.label", QPointF(48, 40))
        button = window.page.canvas.create_component("builtin.button", QPointF(48, 112))
        for node, key, value in ((document.model.root_id, "window_title", "我的应用"),
                                 (document.model.root_id, "geometry.width", 640),
                                 (document.model.root_id, "geometry.height", 420),
                                 (label, "text", "这是正在运行的窗口"), (label, "font_size", 18),
                                 (label, "geometry.width", 430), (label, "geometry.height", 40),
                                 (button, "text", "点击切换选中状态"), (button, "geometry.width", 210),
                                 (button, "checkable", True)):
            document.execute("配置预览检查", lambda model, n=node, k=key, v=value:
                             set_property(model, window.registry, n, k, v))
        document.execute("勾选按钮事件", lambda model: set_event_enabled(model, window.registry, button, "clicked", True))
        window.page.canvas.fit_to_window()
        before = document.model.to_bytes()
        state, cursor = document.state_id, document.history.cursor
        service = window.preview_service
        # 测试子进程复用正式 Worker，仅添加自动点击和截图；正式入口没有这些测试指令。
        screenshot = directory / "预览_运行窗口.png"
        service._command = lambda: (sys.executable, ["-X", "utf8", "-u", "-m", "tests.preview_probe", str(screenshot), "keep"])
        window.preview_current()
        wait_for(lambda: service.last_ready is not None or bool(service.last_error), app, 12)
        assert not service.last_error, service.last_error
        wait_for(lambda: "被单击；已选中" in window.output.toPlainText(), app)
        QTest.qWait(150)
        assert screenshot.exists(), "预览截图未生成。"
        assert document.model.to_bytes() == before and document.state_id == state and document.history.cursor == cursor
        assert window.grab().save(str(directory / "预览_设计器.png")), "设计器截图失败。"
        window.resize(960, 620)
        QTest.qWait(100)
        toolbar = window.findChild(QToolBar, "mainToolbar")
        assert window.zoom_combo.isVisible(), "预览运行时的缩放选择被工具栏挤出。"
        assert toolbar.rect().contains(window.zoom_combo.geometry()), "缩放选择超出工具栏可见边界。"
        for key in ("preview", "stop_preview", "fit"):
            control = toolbar.widgetForAction(window.actions[key])
            assert control.isVisible() and toolbar.rect().contains(control.geometry()), "预览或画布操作被工具栏挤出。"
        window.page.canvas.fit_to_window()
        QTest.qWait(50)
        assert window.grab().save(str(directory / "预览_紧凑布局.png")), "紧凑布局截图失败。"
        process_id = service.last_ready["process_id"]
        window.actions["stop_preview"].trigger()
        wait_for(lambda: not service.active, app)
        assert not service.last_error
        report = {"平台": app.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "独立预览进程": process_id, "内容区尺寸": [640, 420], "原生按钮交互及中文日志": "通过",
                  "未保存项目预览": document.path is None, "设计文档与撤销历史不变": "通过",
                  "停止预览": "通过", "截图说明": "运行窗口截图由 Qt 抓取内容区，不包含操作系统边框。",
                  "紧凑布局预览与缩放入口": "通过",
                  "限制": "使用合成点击；不覆盖物理鼠标、跨屏或操作系统缩放切换。"}
        (directory / "预览_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("桌面预览检查失败。")
        print("桌面预览检查失败，请查看诊断日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
