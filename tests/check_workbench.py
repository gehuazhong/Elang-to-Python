"""工作台实机检查：属性键盘输入、边框选择、紧凑布局和样式隔离。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolBar

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from widgets.builtin import create_registry


def capture(window: MainWindow, directory: Path, name: str) -> None:
    QApplication.processEvents()
    if not window.grab().save(str(directory / name)):
        raise RuntimeError("工作台截图保存失败。")


def main() -> int:
    application = QApplication([])
    initialize(application)
    palette = QPalette(application.palette())
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    try:
        window.show()
        window.resize(1280, 820)
        QTest.qWait(100)
        canvas, document = window.page.canvas, window.document
        canvas.fit_to_window()
        capture(window, directory, "工作台_空窗口.png")

        title = canvas.create_component("builtin.label", QPointF(40, 36))
        detail = canvas.create_component("builtin.label", QPointF(40, 88))
        confirm = canvas.create_component("builtin.button", QPointF(296, 248))
        cancel = canvas.create_component("builtin.button", QPointF(432, 248))
        for node, key, value in ((document.model.root_id, "window_title", "界面设置"),
                                 (document.model.root_id, "geometry.width", 600),
                                 (document.model.root_id, "geometry.height", 340),
                                 (title, "text", "界面设置"), (title, "font_size", 18),
                                 (title, "geometry.width", 400), (title, "geometry.height", 40),
                                 (detail, "text", "修改界面后，按 F5 查看运行效果。"),
                                 (detail, "geometry.width", 460), (confirm, "text", "确定"),
                                 (cancel, "text", "取消")):
            document.execute("设置工作台检查内容", lambda model, n=node, k=key, v=value:
                             set_property(model, window.registry, n, k, v))
        document.select(confirm)
        QTest.qWait(30)
        canvas.fit_to_window()
        cursor = document.history.cursor
        editor = window.properties.editors["text"]
        editor.setFocus()
        editor.selectAll()
        editor.insert("应用设置")
        assert editor.hasFocus(), "属性输入框未取得键盘焦点。"
        capture(window, directory, "工作台_属性输入.png")
        QTest.keyClick(editor, Qt.Key.Key_Return)
        QTest.qWait(30)
        assert document.model.nodes[confirm].properties["text"] == "应用设置", "属性输入未提交。"
        assert document.history.cursor == cursor + 1, "属性修改没有按一次操作提交。"
        document.undo()
        QTest.qWait(30)
        assert document.model.nodes[confirm].properties["text"] == "确定", "属性撤销未恢复。"
        window.select_window()
        QTest.qWait(30)
        capture(window, directory, "工作台_窗口属性.png")

        window.properties.search.setText("边框")
        QTest.qWait(30)
        combo = window.properties.editors["border_style"]
        combo.setFocus()
        combo.showPopup()
        QTest.qWait(30)
        QTest.keyClick(combo.view(), Qt.Key.Key_Down)
        QTest.keyClick(combo.view(), Qt.Key.Key_Return)
        QTest.qWait(30)
        assert document.model.nodes[document.model.root_id].properties["border_style"] == "fixed", "边框下拉选择未提交。"
        assert not window.properties.editors["maximize_button"].isEnabled(), "固定边框的禁用状态未生效。"
        document.undo()
        QTest.qWait(30)
        window.properties.search.clear()

        assert application.palette() == palette, "工作台样式改变了应用默认调色板。"
        native = canvas.renderer.tree.widgets[confirm]
        assert native.styleSheet() == "", "工作台样式传入了设计控件。"
        assert native.palette().color(QPalette.ColorRole.Highlight) == palette.color(QPalette.ColorRole.Highlight)
        assert window.palette().color(QPalette.ColorRole.Highlight) != native.palette().color(QPalette.ColorRole.Highlight)

        document.select(confirm)
        QTest.qWait(30)
        capture(window, directory, "工作台_主窗口.png")
        window.resize(960, 620)
        QTest.qWait(60)
        canvas.fit_to_window()
        toolbar = window.findChild(QToolBar, "mainToolbar")
        assert window.zoom_combo.isVisible() and toolbar.rect().contains(window.zoom_combo.geometry()), "缩放入口被挤出。"
        assert canvas.mapToScene(canvas.viewport().rect()).boundingRect().contains(canvas.renderer.frame.rect()), "设计窗口被裁切。"
        capture(window, directory, "工作台_紧凑布局.png")
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "工具栏高度": toolbar.height(), "紧凑窗口": [window.width(), window.height()],
                  "属性焦点与回车提交": "通过", "属性撤销": "通过", "边框下拉键盘选择": "通过",
                  "固定边框禁用状态": "通过", "缩放入口及窗口适配": "通过", "工作台与设计控件样式隔离": "通过",
                  "限制": "使用真实窗口与合成输入；未覆盖物理输入、跨屏或系统显示缩放切换。"}
        (directory / "工作台_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("工作台桌面检查失败。")
        print("工作台桌面检查失败，请查看诊断日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
