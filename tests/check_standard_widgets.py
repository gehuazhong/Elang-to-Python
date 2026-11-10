"""在真实桌面验证常用组件、中文内容窗口及预览，生成可复查截图。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import set_property
from core.storage import atomic_write
from panels.content_editor import ContentDialog
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(window.registry)
    try:
        window.show()
        window.resize(1440, 940)
        window.activateWindow()
        QTest.qWait(80)
        canvas, document = window.page.canvas, window.document

        def assign(node_id: str, values: dict[str, Any]) -> None:
            for key, value in values.items():
                document.execute("配置组件检查", lambda model, n=node_id, k=key, v=value:
                                 set_property(model, window.registry, n, k, v))

        assign(document.model.root_id, {"geometry.width": 920, "geometry.height": 660, "window_title": "批量任务工具"})
        specs = (
            ("label", 24, 16, 700, 32, {"text": "批量任务工具", "font_size": 16, "font_bold": True}),
            ("line_edit", 24, 64, 296, 32, {"placeholder_text": "输入任务名称"}),
            ("combo_box", 344, 64, 200, 32, {"items": ["全部任务", "待处理", "已完成"]}),
            ("spin_box", 568, 64, 136, 32, {"value": 3, "suffix": " 次"}),
            ("button", 728, 60, 152, 40, {"text": "开始处理"}),
            ("check_box", 24, 112, 160, 32, {"text": "完成后提醒", "check_state": "checked"}),
            ("radio_button", 208, 112, 180, 32, {"text": "顺序执行", "checked": True}),
            ("text_edit", 24, 164, 352, 148, {"text": "任务说明\n可在这里输入多行内容。\n设计时编辑属性，预览时直接输入。"}),
            ("tree_widget", 400, 164, 240, 160, {"header_text": "任务目录", "tree_data": [
                {"text": "工作项目", "children": [{"text": "资料整理", "children": []}, {"text": "清单导出", "children": []}]}]}),
            ("list_widget", 664, 164, 216, 200, {"items": ["导入资料", "核对内容", "导出结果"], "current_index": 1}),
            ("table_widget", 24, 344, 616, 208, {"table_data": {
                "headers": ["任务", "状态", "说明"], "rows": [["资料整理", "待处理", "共三份文件"], ["清单导出", "待处理", "核对后执行"]]}}),
            ("progress_bar", 24, 600, 416, 24, {"value": 42}),
            ("slider", 480, 592, 300, 40, {"value": 60, "tick_position": "below", "tick_interval": 10}),
        )
        keys = {}
        for kind, x, y, width, height, values in specs:
            key = canvas.create_component("builtin." + kind, QPointF(x, y))
            keys[kind] = key
            assign(key, {"geometry.width": width, "geometry.height": height, **values})
        canvas.fit_to_window()
        document.select(keys["table_widget"])
        QTest.qWait(50)
        assert len(document.model.nodes) == 15
        assert window.grab().save(str(directory / "常用组件_工作台.png"))
        before = document.model.to_bytes()
        checks = []

        def edit() -> None:
            dialog = application.activeModalWidget()
            try:
                assert isinstance(dialog, ContentDialog)
                assert dialog.grab().save(str(directory / "常用组件_表格编辑.png"))
                dialog.table.setCurrentCell(0, 0)
                dialog.table.editItem(dialog.table.item(0, 0))
                application.processEvents()
                field = application.focusWidget()
                field.selectAll()
                field.insert("采购清单")
                buttons = dialog.findChild(QDialogButtonBox)
                confirm = next(button for button in buttons.buttons() if button.text() == "确定")
                QTest.mouseClick(confirm, Qt.MouseButton.LeftButton)
                checks.append("通过")
            except Exception:
                logging.getLogger(__name__).exception("桌面内容窗口检查失败。")
                checks.append("失败")
                if isinstance(dialog, ContentDialog):
                    dialog.reject()

        QTimer.singleShot(40, edit)
        QTest.mouseClick(window.properties.editors["table_data"].button, Qt.MouseButton.LeftButton)
        application.processEvents()
        assert checks == ["通过"]
        assert document.model.nodes[keys["table_widget"]].properties["table_data"]["rows"][0][0] == "采购清单"
        document.undo()
        assert document.model.to_bytes() == before
        document.redo()
        snapshot = document.model.to_bytes()
        preview.show(compile_plan(document.model, window.registry, "桌面组件预览"), document.model)
        QTest.qWait(100)
        preview.tree.widgets[keys["text_edit"]].setFocus()
        preview.tree.widgets[keys["text_edit"]].insertPlainText("预览输入\n")
        preview.tree.widgets[keys["combo_box"]].setCurrentIndex(1)
        preview.tree.widgets[keys["spin_box"]].stepUp()
        preview.tree.widgets[keys["check_box"]].click()
        QTest.qWait(50)
        assert document.model.to_bytes() == snapshot
        assert preview.tree.root.grab().save(str(directory / "常用组件_预览.png"))
        atomic_write(directory / "常用组件示例.uipro", snapshot)
        result = {"平台": application.platformName(), "组件种类": len(keys), "属性与内容编辑窗口": "通过",
                  "表格中文输入与撤销重做": "通过", "原生预览交互": "通过", "预览不改写项目": "通过",
                  "限制": "真实桌面窗口与合成输入；未覆盖物理鼠标、系统输入法、多屏和显示缩放切换。"}
        atomic_write(directory / "常用组件_桌面检查.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("常用组件桌面检查失败。")
        print("常用组件桌面检查失败，请查看本地诊断日志。")
        return 1
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
