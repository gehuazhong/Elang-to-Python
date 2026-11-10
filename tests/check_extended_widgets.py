"""真实桌面的容器、日期输入、整树剪贴板和能力清单验收。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, QMimeData, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableView

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.events import set_event_enabled
from core.errors import require
from core.hierarchy import absolute_position, subtree_ids
from core.models import ProjectModel
from core.storage import atomic_write
from panels.support_dialog import SupportDialog
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    previous = application.clipboard().mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(window.registry)
    try:
        window.show()
        window.resize(1460, 970)
        window.activateWindow()
        QTest.qWait(100)
        canvas, document = window.page.canvas, window.document

        def assign(node_id: str, values: dict[str, Any]) -> None:
            for key, value in values.items():
                document.execute("配置扩展组件示例", lambda model, n=node_id, k=key, v=value:
                                 set_property(model, window.registry, n, k, v))

        def create(kind: str, x: int, y: int, width: int, height: int,
                   values: dict[str, Any], parent: str | None = None) -> str:
            created: list[str] = []

            def change(model: ProjectModel) -> ProjectModel:
                candidate, node_id = create_node(model, window.registry, "builtin." + kind, x, y, parent_id=parent)
                created.append(node_id)
                for key, value in {"geometry.width": width, "geometry.height": height, **values}.items():
                    candidate = set_property(candidate, window.registry, node_id, key, value)
                return candidate

            document.execute("创建扩展组件示例", change)
            return created[0]

        assign(document.model.root_id, {"geometry.width": 920, "geometry.height": 680, "window_title": "任务参数设置"})
        create("label", 24, 16, 680, 32, {"text": "任务参数设置", "font_size": 16, "font_bold": True})
        create("label", 24, 50, 760, 24, {"text": "设置执行时间、计算精度和运行方式。按预览可操作这些组件。", "foreground_color": "#62676d"})
        group = create("group_box", 24, 96, 440, 304, {"text": "执行参数"})
        create("label", 12, 8, 112, 32, {"text": "执行日期"}, group)
        date = create("date_edit", 140, 8, 244, 32, {"value": "2024-02-29"}, group)
        create("label", 12, 60, 112, 32, {"text": "开始时间"}, group)
        create("time_edit", 140, 60, 244, 32, {"value": "09:30:00"}, group)
        create("label", 12, 112, 112, 32, {"text": "计算系数"}, group)
        number = create("double_spin_box", 140, 112, 244, 32, {"decimals": 3, "value": 12.345, "single_step": 0.125}, group)
        create("label", 12, 164, 112, 32, {"text": "截止时间"}, group)
        create("datetime_edit", 140, 164, 256, 32, {"value": "2024-03-10T02:30:00"}, group)
        create("check_box", 12, 218, 340, 32, {"text": "完成后显示通知", "check_state": "checked"}, group)
        frame = create("frame", 24, 424, 440, 152, {"frame_shape": "styled"})
        create("label", 8, 4, 220, 26, {"text": "运行方式", "font_bold": True}, frame)
        radio = create("radio_button", 8, 40, 160, 32, {"text": "按顺序执行", "checked": True}, frame)
        create("radio_button", 208, 40, 160, 32, {"text": "同时执行"}, frame)
        create("tool_button", 8, 88, 168, 30, {"text": "更多设置", "arrow_type": "down", "tool_style": "beside"}, frame)
        create("calendar", 488, 96, 404, 288, {"value": "2024-02-29", "grid_visible": True})
        create("label", 488, 402, 160, 24, {"text": "任务优先级"})
        dial = create("dial", 488, 432, 112, 112, {"value": 65, "notches_visible": True})
        create("label", 648, 402, 200, 24, {"text": "预计处理数量"})
        create("lcd_number", 648, 438, 244, 64, {"value": 2048, "digit_count": 6})
        create("scroll_bar", 648, 532, 244, 24, {"value": 40, "page_step": 20})
        command = create("command_link_button", 488, 590, 404, 66, {"text": "应用参数并继续", "description": "预览可触发中文事件提示"})
        canvas.fit_to_window()
        document.select(group)
        QTest.qWait(80)
        require(window.grab().save(str(directory / "扩展组件_工作台.png")), "工作台截图失败。")

        original = canvas.renderer.items[date].scenePos()
        assign(group, {"geometry.x": 32, "font_size": 12})
        QTest.qWait(50)
        require(canvas.renderer.items[date].scenePos() == original + QPointF(8, 0), "父容器移动没有带动子控件。")
        native = canvas.renderer.tree.widgets[date]
        require(native.mapTo(canvas.renderer.tree.root, QPoint()) == QPoint(*absolute_position(document.model, date)),
                "分组框更改字体后，原生控件坐标与模型不同。")
        document.undo()
        document.undo()
        QTest.qWait(30)
        require(canvas.renderer.items[date].scenePos() == original, "容器移动撤销没有恢复。")

        document.select(date)
        QTest.qWait(30)
        window.properties.search.setText("当前日期")
        QTest.qWait(30)
        editor = window.properties.editors["value"]
        editor.setFocus()
        QTest.mouseClick(editor, Qt.MouseButton.LeftButton, pos=QPoint(editor.width() - 9, editor.height() // 2))
        QTest.qWait(60)
        require(editor.calendarWidget().isVisible(), "日期属性的下拉日历没有打开。")
        window.properties.queue_refresh()
        QTest.qWait(30)
        require(window.properties.editors["value"] is editor and editor.calendarWidget().isVisible(),
                "属性刷新中断了正在选择的日期。")
        require(window.grab().save(str(directory / "扩展组件_日期属性.png")), "日期属性截图失败。")
        calendar = editor.calendarWidget()
        calendar.setSelectedDate(QDate(2024, 3, 1))
        dates = calendar.findChild(QTableView, "qt_calendar_calendarview")
        require(dates is not None, "日历没有日期表格。")
        QTest.mouseClick(dates.viewport(), Qt.MouseButton.LeftButton, pos=dates.visualRect(dates.currentIndex()).center())
        canvas.setFocus()
        QTest.qWait(50)
        require(document.model.nodes[date].properties["value"] == "2024-03-01", "日历选择未提交到模型。")
        document.undo()
        QTest.qWait(30)
        require(document.model.nodes[date].properties["value"] == "2024-02-29", "日期修改撤销失败。")

        document.select(radio)
        QTest.qWait(30)
        parent_editor = window.properties.editors["parent_id"]
        parent_editor.activated.emit(parent_editor.findData(group))
        QTest.qWait(30)
        require(document.model.nodes[radio].parent_id == group, "所属容器修改没有生效。")
        document.undo()
        document.select(group)
        QTest.qWait(30)
        canvas.setFocus()
        for node, event in ((number, "valueChanged"), (dial, "valueChanged"), (command, "clicked")):
            document.execute("勾选预览事件", lambda model, n=node, e=event: set_event_enabled(model, window.registry, n, e, True))
        snapshot = document.model.to_bytes()
        descendants = len(subtree_ids(document.model, (group,)))
        window.edit_actions.copy()
        window.edit_actions.paste()
        copied = document.selected_id
        require(copied != group and len(subtree_ids(document.model, (copied,))) == descendants, "整树复制不完整。")
        window.edit_actions.delete()
        document.undo()
        document.undo()
        require(document.model.to_bytes() == snapshot, "整树复制撤销未还原。")

        support = SupportDialog(window.registry, window)
        try:
            support.show()
            support.search.setText("日期")
            QTest.qWait(60)
            require(any(not support.tree.topLevelItem(i).isHidden() for i in range(support.tree.topLevelItemCount())),
                    "组件支持清单搜索没有结果。")
            require(support.grab().save(str(directory / "扩展组件_支持清单.png")), "支持清单截图失败。")
        finally:
            support.close()
            support.deleteLater()

        messages: list[str] = []
        preview.notice.connect(messages.append)
        preview.show(compile_plan(document.model, window.registry, "扩展组件桌面预览"), document.model)
        QTest.qWait(100)
        require(preview.tree.root.grab().save(str(directory / "扩展组件_预览.png")), "预览截图失败。")
        preview.tree.widgets[number].stepUp()
        preview.tree.widgets[dial].setValue(72)
        preview.tree.widgets[command].click()
        QTest.qWait(30)
        require(len(messages) >= 3, "扩展组件原生事件未触发。")
        require(document.model.to_bytes() == snapshot, "预览改写了设计项目。")
        atomic_write(directory / "容器与日期示例.uipro", snapshot)
        result = {"平台": application.platformName(), "组件箱种类": sum(spec.toolbox for spec in window.registry.specs.values()),
                  "示例对象数": len(document.model.nodes), "容器坐标与字体变更": "通过", "日期属性下拉与撤销": "通过",
                  "父级属性调整": "通过", "整树复制删除撤销": "通过", "支持清单搜索": "通过",
                  "原生事件与预览隔离": "通过", "限制": "真实窗口和合成输入；未覆盖物理输入法、多屏及显示缩放切换。"}
        atomic_write(directory / "扩展组件_桌面检查.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("扩展组件桌面检查失败。")
        print("扩展组件桌面检查失败，请查看本地诊断日志。")
        return 1
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()
        if saved:
            restored = QMimeData()
            for key, value in saved.items():
                restored.setData(key, value)
            application.clipboard().setMimeData(restored)
        else:
            application.clipboard().clear()
        application.processEvents()


if __name__ == "__main__":
    raise SystemExit(main())
