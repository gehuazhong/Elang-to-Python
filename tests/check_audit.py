"""在真实桌面复查属性提交、输入焦点、文本历史及对象树状态。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QPointF, QSettings, Qt
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
    with TemporaryDirectory(prefix="界面回归_") as temporary:
        window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False,
                            settings=QSettings(str(Path(temporary) / "设置.ini"), QSettings.Format.IniFormat))
        try:
            window.show()
            window.activateWindow()
            QTest.qWait(100)
            canvas, document = window.page.canvas, window.document
            first = canvas.create_component("builtin.button", QPointF(48, 48))
            second = canvas.create_component("builtin.label", QPointF(48, 120))
            document.select(first)
            QTest.qWait(30)
            name = window.properties.editors["name"]
            name.setFocus()
            name.selectAll()
            name.insert(" ")
            cursor = document.history.cursor
            point = canvas.mapFromScene(canvas.renderer.node_rect(second).center())
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
            QTest.qWait(30)
            assert document.selected_id == first, "非法名称未能阻止画布切换。"
            assert window.properties.editors["name"].text() == " ", "非法输入被清空。"
            assert window.properties.validation_message.isVisible(), "属性区未显示校验提示。"
            assert document.history.cursor == cursor, "校验失败不应写入撤销历史。"
            assert window.grab().save(str(directory / "全量回归_属性校验.png")), "属性校验截图失败。"

            name.selectAll()
            name.insert("确认按钮")
            QTest.keyClick(name, Qt.Key.Key_Return)
            QTest.qWait(30)
            name = window.properties.editors["name"]
            assert name.hasFocus() and name.cursorPosition() == 4, "回车后焦点或光标丢失。"
            assert document.model.nodes[first].name == "确认按钮", "纠正后的名称未提交。"
            tree = window.object_tree
            tree.setFocus()
            QTest.keyClick(tree, Qt.Key.Key_Down)
            QTest.qWait(30)
            assert document.selected_id == second, "对象树键盘切换失败。"
            central = document.model.central_id
            tree._items[central].setExpanded(False)
            document.execute("修改标签", lambda model: set_property(model, window.registry, second, "text", "操作提示"))
            QTest.qWait(30)
            assert not tree._items[central].isExpanded(), "属性刷新重置了对象树折叠状态。"

            search = window.properties.search
            search.setFocus()
            search.insert("文本")
            cursor = document.history.cursor
            QTest.keyClick(search, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
            assert search.text() == "" and window.actions["redo"].isEnabled(), "文本撤销状态不正确。"
            window.actions["redo"].trigger()
            assert search.text() == "文本", "菜单未重做文本输入。"
            assert document.history.cursor == cursor, "文本历史影响了文档历史。"
            search.clear()
            window.output.setFocus()
            window.undo()
            assert document.history.cursor == cursor, "只读输出区错误地撤销了设计内容。"
            canvas.setFocus()
            assert window.grab().save(str(directory / "全量回归_工作台.png")), "工作台截图失败。"
            report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                      "非法属性阻止切换并保留输入": "通过", "中文就地校验提示": "通过",
                      "回车后焦点与光标保留": "通过", "对象树键盘选择": "通过",
                      "对象树折叠状态保留": "通过", "文本撤销重做隔离": "通过",
                      "只读输出不撤销设计": "通过",
                      "限制": "使用真实窗口和合成输入；未覆盖物理输入、中文输入法组合态、跨屏和系统缩放切换。"}
            (directory / "全量回归_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False))
            return 0
        except Exception:
            logging.getLogger(__name__).exception("全量回归桌面检查失败。")
            print("全量回归桌面检查失败，请查看诊断日志。")
            return 1
        finally:
            window.discard_all_for_test()
            window.close()


if __name__ == "__main__":
    raise SystemExit(main())
