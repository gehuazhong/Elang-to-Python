"""真实桌面验证原始大小编辑和缩放入口，保存未经裁切的工作台截图。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolBar

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.hierarchy import pages
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    try:
        window.resize(1480, 940)
        window.show()
        QTest.qWait(100)
        canvas, document = window.page.canvas, window.document
        prefix = f"原大画布_{round(window.devicePixelRatioF() * 100)}"
        assert canvas.zoom == 100, "首次打开窗口被自动缩小。"
        assert canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20), "设计窗口没有靠近左上方。"
        tab = canvas.create_component("builtin.tab_widget", QPointF(40, 64))
        first, second = pages(document.model, tab)
        label = canvas.create_component("builtin.label", QPointF(68, 120), parent_id=first.id)
        editor = canvas.create_component("builtin.line_edit", QPointF(68, 168), parent_id=first.id)
        buttons = [canvas.create_component("builtin.button", QPointF(x, 472)) for x in (40, 344, 632)]
        values = ((document.model.root_id, "window_title", "窗口设计"),
                  (tab, "geometry.width", 720), (tab, "geometry.height", 360),
                  (first.id, "text", "基本设置"), (second.id, "text", "其他设置"),
                  (label, "text", "请输入工具名称"), (label, "geometry.width", 200),
                  (editor, "text", "我的第一个工具"), (editor, "geometry.width", 300),
                  (buttons[0], "text", "确定"), (buttons[1], "text", "取消"), (buttons[2], "text", "应用"))
        for key, prop, value in values:
            document.execute("准备原大画布检查", lambda model, k=key, p=prop, v=value:
                             set_property(model, window.registry, k, p, v))
        document.select(editor)
        QTest.qWait(30)
        assert canvas.mapFromScene(QPointF(120, 32)) - canvas.mapFromScene(QPointF()) == QPoint(120, 32), "组件未按逻辑原始尺寸显示。"
        assert window.grab().save(str(directory / f"{prefix}_工作台.png")), "工作台截图保存失败。"
        original = document.model.to_bytes()
        window.resize(960, 620)
        QTest.qWait(50)
        assert canvas.zoom == 100, "调整工作台尺寸后自动缩小。"
        assert canvas.verticalScrollBar().isVisible(), "较小工作台缺少画布滚动条。"
        toolbar = window.findChild(QToolBar, "mainToolbar")
        for control in (window.zoom_combo, toolbar.widgetForAction(window.actions["original_size"]),
                        toolbar.widgetForAction(window.actions["fit"])):
            assert control.isVisible() and toolbar.rect().contains(control.geometry()), "紧凑工作台隐藏了缩放入口。"
        assert window.grab().save(str(directory / f"{prefix}_紧凑工作台.png")), "紧凑工作台截图保存失败。"
        canvas.setFocus()
        QTest.keyClick(canvas, Qt.Key.Key_9, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(30)
        assert canvas.zoom < 100, "查看全貌快捷键无效。"
        assert canvas.mapToScene(canvas.viewport().rect()).boundingRect().contains(canvas.renderer.frame.rect()), "查看全貌未显示完整窗口。"
        QTest.keyClick(canvas, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(30)
        assert canvas.zoom == 100 and canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20), "原始大小快捷键未恢复。"
        assert document.model.to_bytes() == original, "查看操作改变了设计文件。"
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "默认比例": canvas.zoom, "首次左上定位": "通过", "逻辑原始尺寸": "通过",
                  "小工作台保持原大与滚动条": "通过", "缩放入口可见": "通过",
                  "查看全貌与原始大小快捷键": "通过", "查看操作不改项目": "通过",
                  "限制": "使用真实窗口和合成输入；设备像素比为本次启动值，未验证系统跨屏切换。"}
        (directory / f"{prefix}_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("原大画布桌面检查失败。")
        print("原大画布桌面检查失败，请查看日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
