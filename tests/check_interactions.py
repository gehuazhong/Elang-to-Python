"""真实桌面检查缩放手柄和紧凑布局，输出独立截图及结果。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    try:
        window.show()
        window.resize(1280, 820)
        canvas, document = window.page.canvas, window.document
        QTest.qWait(120)
        canvas.fit_to_window()
        application.processEvents()
        assert window.grab().save(str(directory / "交互优化_空窗口.png")), "空窗口截图失败。"
        label = canvas.create_component("builtin.label", QPointF(48, 48))
        button = canvas.create_component("builtin.button", QPointF(48, 128))
        for node, key, value in ((document.model.root_id, "window_title", "我的应用"),
                                 (label, "text", "欢迎使用我的应用"), (label, "font_size", 18),
                                 (label, "geometry.width", 360), (label, "geometry.height", 40),
                                 (button, "text", "开始使用"), (button, "geometry.width", 160)):
            document.execute("设置检查内容", lambda model, n=node, k=key, v=value:
                             set_property(model, window.registry, n, k, v))
        document.select(button)
        QTest.qWait(40)
        before = document.model
        cursor = document.history.cursor
        grip = canvas.adornments.handles["se"]
        press = canvas.mapFromScene(grip.scenePos())
        target = press + QPoint(round(48 * canvas.zoom / 100), round(24 * canvas.zoom / 100))
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        move = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                           Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(canvas.viewport(), move)
        assert document.model is before, "拖动中不应修改文档。"
        assert canvas.adornments.badge.isVisible(), "尺寸提示没有显示。"
        assert window.grab().save(str(directory / "交互优化_拖动尺寸.png")), "手势截图失败。"
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        QTest.qWait(40)
        assert document.history.cursor == cursor + 1, "缩放手势必须只提交一次。"
        rect = document.model.nodes[button].geometry
        assert (rect.width, rect.height) == (208, 64), "屏幕坐标转换不正确。"
        assert canvas.renderer.tree.widgets[button].width() == rect.width, "原生控件尺寸不同步。"
        assert window.grab().save(str(directory / "交互优化_主窗口.png")), "主窗口截图失败。"
        document.undo()
        assert document.model.to_bytes() == before.to_bytes(), "撤销没有完整恢复。"
        document.redo()
        window.resize(960, 620)
        QTest.qWait(80)
        canvas.fit_to_window()
        application.processEvents()
        assert canvas.mapToScene(canvas.viewport().rect()).boundingRect().contains(canvas.renderer.frame.rect()), "紧凑布局窗口被裁切。"
        assert window.zoom_combo.isVisible(), "紧凑布局下缩放选择不可见。"
        assert window.grab().save(str(directory / "交互优化_紧凑布局.png")), "紧凑布局截图失败。"
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "桌面缩放手势": "通过", "单条撤销与重做": "通过", "临时几何不写模型": "通过",
                  "提交尺寸": [rect.width, rect.height], "紧凑布局": [window.width(), window.height()],
                  "限制": "使用合成鼠标事件；不覆盖物理鼠标、跨屏移动或系统缩放切换。"}
        (directory / "交互优化_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("交互桌面检查失败。")
        print("交互桌面检查失败，请查看诊断日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
