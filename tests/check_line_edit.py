"""真实桌面检查单行编辑框拖放、属性、保存和独立预览。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.storage import load_project
from designer.mime import component_mime
from tests.test_storage import wait_for
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="编辑框验证_") as temporary:
        window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False,
                            settings=QSettings(str(Path(temporary) / "设置.ini"), QSettings.Format.IniFormat))
        try:
            window.show()
            window.activateWindow()
            QTest.qWait(80)
            canvas, document = window.page.canvas, window.document
            for member, value in (("window_title", "填写账户信息"), ("geometry.width", 520), ("geometry.height", 300)):
                document.execute("设置示例窗口", lambda model, key=member, current=value:
                                 set_property(model, window.registry, model.root_id, key, current))
            canvas.fit_to_window()
            title = canvas.create_component("builtin.label", QPointF(40, 32))
            document.execute("设置标题", lambda model: set_property(model, window.registry, title, "text", "账户名称"))
            point = canvas.mapFromScene(QPointF(40, 72))
            mime = component_mime("builtin.line_edit")
            enter = QDragEnterEvent(point, Qt.DropAction.CopyAction, mime,
                                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(canvas.viewport(), enter)
            drop = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                              Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(canvas.viewport(), drop)
            assert drop.isAccepted(), "编辑框拖放未被接受。"
            key = document.selected_id
            assert isinstance(canvas.renderer.tree.widgets[key], QLineEdit), "未创建原生编辑框。"
            for member, value in (("name", "账户编辑框"), ("placeholder_text", "请输入账户名称"),
                                   ("geometry.width", 344), ("max_length", 32)):
                document.execute("设置编辑框", lambda model, prop=member, current=value:
                                 set_property(model, window.registry, key, prop, current))
            button = canvas.create_component("builtin.button", QPointF(264, 160))
            document.execute("设置按钮", lambda model: set_property(model, window.registry, button, "text", "确认"))
            document.select(key)
            QTest.qWait(30)
            editor = window.properties.editors["placeholder_text"]
            editor.setFocus()
            editor.selectAll()
            editor.insert("请输入您的账户名称")
            QTest.keyClick(editor, Qt.Key.Key_Return)
            QTest.qWait(30)
            assert canvas.renderer.tree.widgets[key].placeholderText() == "请输入您的账户名称"
            assert window.grab().save(str(directory / "编辑框_设计器.png")), "设计器截图失败。"
            editor = window.properties.editors["text"]
            editor.setFocus()
            editor.insert("初始内容")
            QTest.keyClick(editor, Qt.Key.Key_Return)
            QTest.qWait(30)
            assert canvas.renderer.tree.widgets[key].text() == "初始内容"
            assert window.grab().save(str(directory / "编辑框_已有文本.png")), "已有文本截图失败。"
            saved_path = Path(temporary) / "编辑框项目.uipro"
            window.save_service.save(document, saved_path)
            wait_for(lambda: not document.saving, application)
            assert load_project(saved_path).model == document.model, "保存后的编辑框与文档不一致。"

            before, state, cursor = document.model.to_bytes(), document.state_id, document.history.cursor
            service = window.preview_service
            screenshot = directory / "编辑框_预览.png"
            service._command = lambda: (sys.executable, ["-X", "utf8", "-u", "-m", "tests.line_edit_probe", str(screenshot)])
            window.preview_current()
            wait_for(lambda: not service.active, application, 12)
            assert not service.last_error and service.last_ready is not None, "独立预览失败。"
            assert "编辑框自动输入检查通过" in window.output.toPlainText(), "子进程输入检查没有完成。"
            assert "中文测试" not in window.output.toPlainText(), "预览日志记录了输入内容。"
            assert document.model.to_bytes() == before and document.state_id == state and document.history.cursor == cursor
            report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                      "编辑框拖放创建": "通过", "占位文本实时更新": "通过", "初始文本编辑": "通过",
                      "保存加载完整还原": "通过", "独立进程中文输入及回车": "通过",
                      "预览日志不包含输入内容": "通过", "预览不修改设计文档": "通过",
                      "限制": "使用真实窗口及合成输入；未覆盖物理鼠标、输入法候选窗口或跨屏显示缩放。"}
            (directory / "编辑框_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False))
            return 0
        except Exception:
            logging.getLogger(__name__).exception("编辑框桌面检查失败。")
            print("编辑框桌面检查失败，请查看诊断日志。")
            return 1
        finally:
            window.discard_all_for_test()
            window.close()


if __name__ == "__main__":
    raise SystemExit(main())
