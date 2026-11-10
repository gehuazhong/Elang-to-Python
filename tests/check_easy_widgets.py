"""真实桌面验证易语言基础组件示例、分页交互与中文对话框。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import tempfile
from typing import Any

from PySide6.QtCore import QPointF, QMimeData, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.events import set_event_enabled
from core.commands.pages import select_page
from core.errors import require
from core.hierarchy import pages, subtree_ids
from core.models import ProjectModel
from core.storage import atomic_write
from panels.image_editor import import_image
from runtime.easy_widgets import CommonDialog
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    previous = application.clipboard().mimeData()
    clipboard = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(window.registry)
    try:
        window.show()
        window.resize(1480, 980)
        window.activateWindow()
        QTest.qWait(80)
        canvas, document = window.page.canvas, window.document

        def assign(node: str, values: dict[str, Any]) -> None:
            for key, value in values.items():
                document.execute("配置示例属性", lambda model, n=node, k=key, v=value:
                                 set_property(model, window.registry, n, k, v))

        def create(kind: str, values: dict[str, Any], x: int = 0, y: int = 0,
                   width: int | None = None, height: int | None = None, parent: str | None = None) -> str:
            created: list[str] = []
            def change(model: ProjectModel) -> ProjectModel:
                candidate, key = create_node(model, window.registry, "builtin." + kind, x, y, parent_id=parent)
                created.append(key)
                data = dict(values)
                if width is not None:
                    data["geometry.width"] = width
                if height is not None:
                    data["geometry.height"] = height
                for name, value in data.items():
                    candidate = set_property(candidate, window.registry, key, name, value)
                return candidate
            document.execute("创建基础组件示例", change)
            return created[0]

        assign(document.model.root_id, {"window_title": "中文工具开发示例", "geometry.width": 960, "geometry.height": 720})
        toolbar = create("tool_bar", {"items": ["新建任务", "打开项目", "-", "保存项目"], "bar_height": 36})
        status = create("status_bar", {"text": "就绪", "panels": ["中文组件", "独立导出"], "bar_height": 28})
        create("label", {"text": "中文工具开发示例", "font_bold": True, "font_size": 15}, 20, 12, 400, 32)
        tab = create("tab_widget", {}, 20, 64, 920, 564)
        first, second = pages(document.model, tab)
        assign(first.id, {"text": "任务与数据"})
        assign(second.id, {"text": "画板演示"})
        group = create("group_box", {"text": "任务设置"}, 16, 16, 300, 488, first.id)
        create("label", {"text": "任务名称"}, 12, 4, 240, 24, group)
        create("line_edit", {"placeholder_text": "请输入任务名称", "text": "第一个 Python 工具"}, 12, 38, 240, 32, group)
        create("radio_button", {"text": "按顺序处理", "checked": True}, 12, 88, 240, 30, group)
        create("check_box", {"text": "处理完成后提醒", "check_state": "checked"}, 12, 124, 240, 30, group)
        create("combo_box", {"items": ["标准模式", "快速模式", "仅检查"]}, 12, 172, 240, 32, group)
        button = create("button", {"text": "选择文件…"}, 12, 220, 240, 38, group)
        create("label", {"text": "通用对话框已绑定上方按钮。\n按预览后可实际选择文件。", "word_wrap": True,
                         "foreground_color": "#67716b"}, 12, 282, 240, 72, group)
        create("label", {"text": "时钟在运行时每秒触发一次周期事件。", "word_wrap": True,
                         "foreground_color": "#67716b"}, 12, 368, 240, 48, group)
        create("label", {"text": "任务清单", "font_bold": True}, 344, 16, 240, 28, first.id)
        super_list = create("super_list", {"table_data": {"headers": ["任务", "状态", "文件数"], "rows": [
            ["资料整理", "待处理", "12"], ["报表汇总", "已完成", "8"], ["图片分类", "待处理", "24"]]},
            "checkboxes": True, "checked_rows": ["1", "3"], "multi_select": True, "column_width": 160},
            344, 56, 548, 240, first.id)
        create("label", {"text": "处理步骤", "font_bold": True}, 344, 318, 240, 28, first.id)
        create("list_widget", {"items": ["导入文件", "检查内容", "保存结果"], "current_index": 0},
               344, 358, 244, 146, first.id)
        with tempfile.TemporaryDirectory(prefix="基础图片验证_") as temporary:
            path = Path(temporary) / "项目图片.png"
            picture = QImage(320, 160, QImage.Format.Format_ARGB32)
            picture.fill(QColor("#edf2ef"))
            painter = QPainter(picture)
            painter.fillRect(22, 26, 88, 108, QColor("#426e5c"))
            painter.setPen(QPen(QColor("#ffffff"), 3))
            for y in (50, 72, 94):
                painter.drawLine(38, y, 91, y)
            painter.setPen(QColor("#355345"))
            painter.drawText(134, 68, "项目图片")
            painter.drawText(134, 96, "随设计项目保存")
            painter.end()
            require(picture.save(str(path)), "示例图片生成失败。")
            image = import_image(path)
        create("picture_box", {"image": image, "image_mode": "fit"}, 612, 358, 280, 146, first.id)
        create("label", {"text": "预览时按住鼠标左键绘画；画笔和底色可在属性中修改。"}, 16, 16, 870, 28, second.id)
        board = create("drawing_board", {"pen_color": "#426e5c", "pen_width": 4, "paper_color": "#f8faf8"},
                       16, 64, 876, 438, second.id)
        clock = create("timer", {"interval": 1000})
        dialog_id = create("common_dialog", {"title": "选择要处理的文件", "dialog_kind": "open_files",
                                             "trigger_control": document.model.nodes[button].code_name})
        document.select(super_list)
        canvas.fit_to_window()
        QTest.qWait(80)
        require(window.grab().save(str(directory / "基础组件_工作台.png")), "工作台截图失败。")
        document.execute("勾选时钟周期事件", lambda model: set_event_enabled(model, window.registry, clock, "timeout", True))
        expected = document.model.to_bytes()

        tabs = canvas.renderer.tree.widgets[tab]
        point = canvas.mapFromScene(canvas.renderer.items[tab].mapToScene(QPointF(tabs.tab_bar.tabRect(1).center())))
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        QTest.qWait(50)
        require(document.model.nodes[tab].properties["current_index"] == 1, "画布页签切换失败。")
        require(canvas.renderer.items[board].isVisible() and not canvas.renderer.items[super_list].isVisible(), "页面子控件显隐错误。")
        require(window.grab().save(str(directory / "基础组件_画板页.png")), "画板页截图失败。")
        document.undo()
        require(document.model.to_bytes() == expected, "页签切换撤销失败。")
        document.select(tab)
        QTest.qWait(20)
        canvas.setFocus()
        window.edit_actions.copy()
        window.edit_actions.paste()
        copied = document.selected_id
        require(len(subtree_ids(document.model, (copied,))) == len(subtree_ids(document.model, (tab,))), "选择夹整树复制失败。")
        document.undo()
        require(document.model.to_bytes() == expected, "选择夹复制撤销失败。")
        document.select(clock)
        QTest.qWait(30)
        require(window.grab().save(str(directory / "基础组件_时钟属性.png")), "时钟属性截图失败。")
        require(window.edit_actions.node_states()[2], "时钟不能通过编辑操作删除。")

        messages: list[str] = []
        preview.notice.connect(messages.append)
        preview.show(compile_plan(document.model, window.registry, "基础组件桌面检查"), document.model)
        QTest.qWait(100)
        require(preview.tree.root.grab().save(str(directory / "基础组件_预览.png")), "预览截图失败。")
        preview.tree.widgets[button].click()
        QTest.qWait(100)
        dialog = preview.tree.widgets[dialog_id]
        require(isinstance(dialog, CommonDialog) and isinstance(dialog.dialog, QFileDialog), "通用对话框没有由按钮触发。")
        require(dialog.dialog.grab().save(str(directory / "基础组件_通用对话框.png")), "通用对话框截图失败。")
        dialog.dialog.reject()
        preview.tree.widgets[tab].set_current_page(1)
        preview.tree.widgets[board].draw_line(24, 32, 160, 96)
        preview.tree.widgets[toolbar].actions()[0].trigger()
        preview.tree.widgets[status].showMessage("操作已触发")
        QTest.qWait(1050)
        require(any("周期事件" in message for message in messages), "时钟没有周期事件。")
        require(document.model.to_bytes() == expected, "预览改写了设计项目。")
        atomic_write(directory / "易语言基础组件示例.uipro", expected)
        result = {"平台": application.platformName(), "组件箱种类": sum(spec.toolbox for spec in window.registry.specs.values()),
                  "示例覆盖基础种类": 16, "分页点击与撤销": "通过", "选择夹整树复制撤销": "通过", "非可视组件选中": "通过",
                  "通用对话框按钮触发": "通过", "时钟画板工具条状态条运行": "通过", "预览不改写项目": "通过",
                  "限制": "真实窗口和合成输入，未覆盖系统输入法、物理鼠标、多屏及显示缩放切换。"}
        atomic_write(directory / "基础组件_桌面检查.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("基础组件桌面检查失败。")
        print("基础组件桌面检查失败，请查看本地日志。")
        return 1
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()
        if clipboard:
            mime = QMimeData()
            for key, value in clipboard.items():
                mime.setData(key, value)
            application.clipboard().setMimeData(mime)
        else:
            application.clipboard().clear()
        application.processEvents()


if __name__ == "__main__":
    raise SystemExit(main())
