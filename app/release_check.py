"""在源码与便携包中执行相同的交付检查，不依赖测试框架。"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from dataclasses import replace
from typing import Any

from PySide6.QtCore import QBuffer, QEventLoop, QIODevice, QObject, QPoint, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QImage, QWheelEvent
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QFileSystemModel

from core.commands.nodes import resize_node, set_property
from core.commands.arrange import delete_nodes
from core.commands.group_clipboard import copy_group, paste_group
from core.commands.hierarchy import reparent_node
from core.commands.tree_clipboard import copy_tree, paste_tree
from core.document import DocumentSession
from core.errors import require
from core.events import event_enabled, set_event_enabled
from codegen.publisher import export_project
from core.hierarchy import absolute_position, subtree_ids
from core.models import ProjectModel, thaw
from core.storage import atomic_write, load_project
from panels.font_editor import FontFamilyEditor, FontSizeEditor
from panels.image_editor import ImageEditor, import_image
from panels.content_editor import ContentDialog
from .diagnostics import export_diagnostics
from .dialogs import PROJECT_FILE_FILTER
from .main_window import MainWindow
from .version import VERSION
from widgets.advanced import ADVANCED_TYPES


class ReleaseCheck(QObject):
    def __init__(self, application: QApplication, window: MainWindow, report: Path) -> None:
        super().__init__(window)
        self.application, self.window, self.report = application, window, report.resolve()
        self.temporary = tempfile.TemporaryDirectory(prefix="界面交付检查_")
        self.directory = Path(self.temporary.name)
        self.result: dict[str, Any] = {"版本": VERSION, "便携包": bool(getattr(sys, "frozen", False)),
                                       "平台": application.platformName(), "检查结果": "未完成"}
        self.done = False
        self.stopping = False
        self.menu_preview_model: ProjectModel | None = None
        self.menu_preview_started = False
        self.expected = b""
        self.advanced_ids = tuple("builtin." + key for key in ADVANCED_TYPES)
        # The legacy batch exercises free-positioned siblings and proportional scaling.
        # Native layouts, docks and child windows have their own ownership checks below.
        self.component_ids = tuple(spec.type_id for spec in sorted(window.registry.specs.values(),
                                   key=lambda item: item.slot not in {"tool_bar", "status_bar"})
                                   if spec.toolbox and spec.type_id not in self.advanced_ids)
        self.expected_count = 2 + len(self.component_ids)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.fail("交付检查超时。"))
        self.window.save_service.finished.connect(self.saved)
        self.window.preview_service.ready.connect(self.preview_ready)
        self.window.preview_service.error.connect(self.fail)
        self.window.preview_service.changed.connect(self.preview_changed)

    def start(self) -> None:
        self.timer.start(30000)
        try:
            screen = self.window.screen()
            require(screen is not None and screen.availableGeometry().contains(self.window.frameGeometry()),
                    "启动工作台超出可用屏幕范围。")
            self.result["启动工作台完整可达"] = "通过"
            document = self.window.document
            canvas = self.window.page.canvas
            require(canvas.zoom == 100, "首次显示没有使用原始大小。")
            require(canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20),
                    "首次显示没有定位到窗口左上方。")
            snapshot = document.model.to_bytes()
            self.window.actions["fit"].trigger()
            self.window.actions["original_size"].trigger()
            require(canvas.zoom == 100 and document.model.to_bytes() == snapshot,
                    "恢复原始大小失败或查看操作改变了项目。")
            self.result["默认原大与左上定位"] = "通过"
            self.result["查看全貌与原始大小恢复"] = "通过"
            self.check_property_input()
            family = self.window.properties.editors["font_family"]
            size = self.window.properties.editors["font_size"]
            require(isinstance(family, FontFamilyEditor) and isinstance(size, FontSizeEditor), "未接入字体字号选择器。")
            require(not family.isEditable() and not size.isEditable() and family.count() > 1, "本机字体列表不可选。")
            selected = family.itemData(1)
            family.setCurrentIndex(1)
            family.activated.emit(1)
            index = size.findData(18)
            size.setCurrentIndex(index)
            size.activated.emit(index)
            require(canvas.renderer.tree.root.font().family() == selected and canvas.renderer.tree.root.font().pointSize() == 18,
                    "字体或字号选择未应用到窗口。")
            document.undo()
            document.undo()
            self.window.properties.refresh()
            require(document.model.to_bytes() == snapshot, "字体字号撤销未恢复。")
            self.result["字体字号选择与撤销"] = "通过"
            keys = []
            for index, type_id in enumerate(self.component_ids):
                key = self.window.page.canvas.create_component(type_id, QPointF(48 + len(keys) * 96, 84 + len(keys) * 64),
                                                               parent_id=document.model.central_id)
                require(key is not None, "组件创建失败。")
                if (document.model.nodes[key].slot == "children" and document.model.nodes[key].parent_id == document.model.central_id
                        and not any(child.parent_id == key for child in document.model.nodes.values())):
                    keys.append(key)
            self.expected_count = len(document.model.nodes)
            document.select_many(tuple(keys), primary=keys[0])
            before = document.model.to_bytes()
            self.window.edit_actions.arrange("left")
            require(all(document.model.nodes[key].geometry.x == 48 for key in keys), "多选排版没有应用到全部控件。")
            document.undo()
            require(document.model.to_bytes() == before, "排版撤销未还原整个集合。")
            document.redo()
            fragment = copy_group(document.model, self.window.registry, tuple(keys))
            created = []

            def paste(model: ProjectModel) -> ProjectModel:
                candidate, copies = paste_group(model, self.window.registry, fragment)
                created.extend(copies)
                return candidate

            document.execute("验证整组粘贴", paste)
            require(len(document.model.nodes) == self.expected_count + len(keys), "整组粘贴未创建所有控件。")
            document.execute("验证整组删除", lambda model: delete_nodes(model, tuple(created)))
            document.undo()
            require(set(created) <= set(document.model.nodes), "整组删除无法撤销。")
            document.redo()
            self.result["多选排版与整组复制删除撤销"] = "通过"
            self.result["组件种类"] = len(self.component_ids) + len(self.advanced_ids)
            self.result["组件清单"] = [self.window.registry.require(key).label for key in (*self.component_ids, *self.advanced_ids)]
            self.check_containers()
            self.check_easy_widgets()
            self.check_window_icon()
            self.check_events()
            self.check_column_widths()
            self.check_project_file_filter()
            self.check_advanced()
            self.check_menus()
            self.check_input_components()
            document.execute("开启组件随窗口缩放", lambda model: set_property(model, self.window.registry, model.root_id,
                                                                            "scale_children", True))
            self.window.select_window()
            self.window.properties.refresh()
            require(self.window.properties.editors["scale_children"].isChecked(), "窗口缩放开关未显示为开启。")
            before_scaling = document.model
            original_rect = before_scaling.nodes[before_scaling.root_id].geometry
            document.execute("验证窗口与组件一起拉伸", lambda model: resize_node(model, model.root_id,
                             replace(original_rect, width=original_rect.width + 160, height=original_rect.height + 80)))
            button_id = next(node.id for node in before_scaling.nodes.values() if node.type_id == "builtin.button")
            require(document.model.nodes[button_id].geometry.width > before_scaling.nodes[button_id].geometry.width,
                    "窗口拉伸没有带动组件。")
            document.undo()
            require(document.model == before_scaling, "窗口跟随缩放无法整次撤销。")
            self.result["窗口跟随开关与整次撤销"] = "通过"
            document.execute("设置验收标题", lambda model: set_property(model, self.window.registry, model.root_id,
                                                                        "window_title", "便携版验收窗口"))
            self.expected = document.model.to_bytes()
            self.window.save_service.save(document, self.directory / "中文项目.uipro")
        except Exception:
            logging.getLogger(__name__).exception("交付初始化检查失败。")
            self.fail("创建控件或启动保存失败。")

    def check_advanced(self) -> None:
        from core.models import new_project
        from core.commands.nodes import create_node
        from core.build_plan import compile_plan
        from runtime.builder import RuntimeTree, FACTORIES
        model = new_project("新增组件交付检查")
        for type_id in self.advanced_ids:
            model, _ = create_node(model, self.window.registry, type_id, 8, 8)
        tree = RuntimeTree(self.window.registry)
        generated = None
        try:
            plan = compile_plan(model, self.window.registry, "advanced-release")
            tree.apply(plan)
            require(len(tree.widgets) == len(model.nodes), "新增组件构建数量不一致。")
            for node in plan.nodes:
                if node.slot in {"children", "pages", "dock"}:
                    require(not tree.image(node.id, 1).isNull(), "新增组件画布缓存为空。")
            entry = export_project(model, self.window.registry, self.directory / "新增组件导出")
            spec = importlib.util.spec_from_file_location("_advanced_release", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            generated = module.create_window(self.application)
            require(len(generated.controls) == len(model.nodes), "新增组件导出数量不一致。")
            for node in model.nodes.values():
                expected = FACTORIES[self.window.registry.require(node.type_id).qt_class]
                actual = generated.controls[node.code_name]
                require(type(actual).__name__ == expected.__name__ or actual.inherits(expected.__name__),
                        f"新增组件“{node.name}”导出类型错误。")
            self.result["新增35类组件构建画布与独立导出"] = "通过"
        finally:
            if generated is not None:
                generated.close()
                generated.deleteLater()
            tree.dispose()

    def check_input_components(self) -> None:
        document, registry = self.window.document, self.window.registry
        by_type = {node.type_id: node.id for node in document.model.nodes.values()}
        icon = document.model.nodes[document.model.root_id].properties["window_icon"]
        for kind, values in (
            ("rich_text_edit", {"text": "<p><b>交付富文本</b></p>", "text_format": "rich", "document_margin": 10}),
            ("text_browser", {"text": '<p><a href="demo:check">交付链接</a></p>', "open_links": False}),
            ("font_combo_box", {"current_font": self.application.font().family(), "editable": False}),
            ("key_sequence_edit", {"key_sequence": "Ctrl+Shift+K"}),
            ("button", {"icon": icon, "icon_width": 24, "icon_height": 24, "shortcut": "Ctrl+K"}),
            ("group_box", {"checkable": True, "checked": False}),
            ("label", {"text": '<a href="demo:check">链接</a>', "text_format": "rich"}),
        ):
            for key, value in values.items():
                document.execute("配置文本输入交付检查", lambda model, n=by_type["builtin." + kind], k=key, v=value:
                                 set_property(model, registry, n, k, v))
        tree = self.window.page.canvas.renderer.tree
        key = by_type["builtin.key_sequence_edit"]
        before = tree.image(key, 1)
        document.execute("检查快捷键画布", lambda model: set_property(model, registry, key, "key_sequence", "Alt+F12"))
        require(tree.image(key, 1) != before, "快捷键编辑框没有绘制实际文本。")
        document.undo()
        self.result["文本输入组件属性与画布"] = "通过"

    def check_project_file_filter(self) -> None:
        folder = self.directory / "中文项目 (筛选)"
        folder.mkdir()
        for name in ("库存管理台.uipro", "账号 登录.UIPRO"):
            atomic_write(folder / name, self.window.document.model.to_bytes())
        atomic_write(folder / "说明.txt", b"not a project")
        dialog = QFileDialog(self.window)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setWindowTitle("项目文件筛选检查")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(PROJECT_FILE_FILTER)
        dialog.setDirectory(str(folder))
        model = dialog.findChild(QFileSystemModel)

        def wait_for_names(expected: set[str]) -> None:
            loop = QEventLoop()
            poll, timeout = QTimer(), QTimer()
            timeout.setSingleShot(True)
            observed = set()

            def inspect():
                nonlocal observed
                root = model.index(dialog.directory().absolutePath())
                observed = {model.fileName(model.index(row, 0, root)) for row in range(model.rowCount(root))}
                if observed == expected:
                    loop.quit()

            poll.timeout.connect(inspect)
            timeout.timeout.connect(loop.quit)
            poll.start(10)
            timeout.start(3000)
            loop.exec()
            poll.stop()
            timeout.stop()
            require(observed == expected, "项目文件筛选隐藏了有效项目或显示了无关文件。")

        try:
            require(model.nameFilters() == ["*.uipro"], "文件对话框未正确解析项目扩展名。")
            dialog.show()
            for mode in (QFileDialog.ViewMode.List, QFileDialog.ViewMode.Detail):
                dialog.setViewMode(mode)
                for _ in range(3):
                    dialog.setDirectory(str(folder))
                    wait_for_names({"库存管理台.uipro", "账号 登录.UIPRO"})
                    dialog.setDirectory(str(folder.parent))
                    wait_for_names({folder.name})
            self.result["项目文件筛选与反复进入目录"] = "通过"
        finally:
            dialog.close()
            dialog.deleteLater()

    def check_property_input(self) -> None:
        panel, document = self.window.properties, self.window.document
        snapshot, cursor = document.model, document.history.cursor
        for key in ("geometry.width", "border_style", "font_family", "font_size"):
            editor = panel.editors[key]
            editor.setFocus()
            position = editor.rect().center()
            before = editor.currentData() if isinstance(editor, QComboBox) else editor.value()
            event = QWheelEvent(QPointF(position), QPointF(editor.mapToGlobal(position)), QPoint(), QPoint(0, -120),
                                Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                                Qt.ScrollPhase.NoScrollPhase, False)
            self.application.sendEvent(editor, event)
            after = editor.currentData() if isinstance(editor, QComboBox) else editor.value()
            require(after == before, "属性滚轮误改了编辑值。")
        require(panel.commit_pending() and document.model == snapshot and document.history.cursor == cursor,
                "滚轮操作改变了项目或撤销记录。")
        self.result["属性滚轮值与历史保护"] = "通过"
        editor = panel.editors["geometry.width"]
        editor.setFocus()
        target = editor.value() + 1
        editor.stepUp()
        panel.refresh()
        require(panel.editors["geometry.width"] is editor and editor.value() == target, "刷新丢失了步进输入。")
        require(panel.commit_pending() and document.model.nodes[document.model.root_id].geometry.width == target,
                "步进输入未正确提交。")
        document.undo()
        panel.refresh()
        require(document.model == snapshot, "步进输入撤销未还原项目。")
        self.result["步进输入保留与提交撤销"] = "通过"

    def check_events(self) -> None:
        document, panel = self.window.document, self.window.properties
        button = next(node.id for node in document.model.nodes.values() if node.type_id == "builtin.button")
        document.select(button)
        panel.refresh()
        editor = panel.editors["event.clicked"]
        require(isinstance(editor, QCheckBox) and not editor.isChecked(), "事件未以默认关闭的复选框显示。")
        editor.click()
        require(event_enabled(document.model, button, "clicked"), "勾选后事件未连接。")
        document.undo()
        require(not event_enabled(document.model, button, "clicked"), "事件连接无法撤销。")
        document.redo()
        panel.refresh()
        require(panel.editors["event.clicked"].isChecked(), "事件连接重做后复选框未同步。")
        self.result["事件勾选与撤销重做"] = "通过"

    def check_column_widths(self) -> None:
        document, registry = self.window.document, self.window.registry
        for kind, expected in (("table_widget", (56, 280)), ("super_list", (56, 160, 280))):
            node = next(node for node in document.model.nodes.values() if node.type_id == "builtin." + kind)
            prop = registry.require(node.type_id).property("table_data")
            original, cursor = document.model, document.history.cursor

            def commit(value: Any) -> bool:
                document.execute("设置各列宽度", lambda model: set_property(model, registry, node.id, "table_data", value))
                return True

            dialog = ContentDialog(prop, thaw(node.properties["table_data"]), commit,
                                   column_default=node.properties.get("column_width", 100))
            try:
                for column, width in enumerate(expected):
                    dialog.column_choice.setCurrentIndex(column)
                    dialog.column_width.setValue(width)
                dialog.accept()
                require(document.history.cursor == cursor + 1, "列宽与内容未作为单次操作提交。")
                require(document.model.nodes[node.id].properties["table_data"]["column_widths"] == expected,
                        "逐列宽度没有保存到组件。")
                document.undo()
                require(document.model == original, "列宽编辑无法完整撤销。")
                document.redo()
                widget = self.window.page.canvas.renderer.tree.widgets[node.id]
                require(tuple(widget.columnWidth(i) for i in range(widget.columnCount())) == expected,
                        "画布没有按各列宽度显示。")
            finally:
                dialog.deleteLater()
        self.result["逐列宽度编辑画布与撤销"] = "通过"

    def check_easy_widgets(self) -> None:
        from core.hierarchy import pages
        document, registry = self.window.document, self.window.registry
        by_type = {node.type_id: node.id for node in document.model.nodes.values()}
        tab = by_type["builtin.tab_widget"]
        page = pages(document.model, tab)[1]
        document.execute("移入选择夹页面", lambda model: reparent_node(model, registry, by_type["builtin.check_box"], page.id))
        document.execute("设置默认页", lambda model: set_property(model, registry, tab, "current_index", 1))
        document.execute("绑定通用对话框", lambda model: set_property(model, registry, by_type["builtin.common_dialog"], "trigger_control", "button_1"))
        picture = QImage(24, 16, QImage.Format.Format_ARGB32)
        picture.fill(QColor("#426e5c"))
        buffer = QBuffer()
        require(buffer.open(QIODevice.OpenModeFlag.WriteOnly) and picture.save(buffer, "PNG"), "无法准备交付图片。")
        image_data = bytes(buffer.data().toBase64()).decode("ascii")
        document.execute("导入交付图片", lambda model: set_property(model, registry, by_type["builtin.picture_box"], "image", image_data))
        fragment = copy_tree(document.model, registry, (tab,))
        original = document.model.to_bytes()
        copies: list[str] = []

        def clone(model: ProjectModel) -> ProjectModel:
            candidate, roots = paste_tree(model, registry, fragment)
            copies.extend(roots)
            return candidate

        document.execute("复制完整选择夹", clone)
        require(len(subtree_ids(document.model, tuple(copies))) == 4, "选择夹页面或子控件复制不完整。")
        document.undo()
        require(document.model.to_bytes() == original, "选择夹复制无法完整撤销。")
        self.result["选择夹页面与整树复制"] = "通过"

    def check_window_icon(self) -> None:
        document, registry = self.window.document, self.window.registry
        self.window.select_window()
        panel = self.window.properties
        panel.refresh()
        editor = panel.editors["window_icon"]
        require(isinstance(editor, ImageEditor) and editor.icon_mode, "窗口属性未接入程序图标选择器。")
        source = self.directory / "交付程序图标.ico"
        picture = QImage(64, 64, QImage.Format.Format_ARGB32)
        picture.fill(QColor("#426e5c"))
        require(picture.save(str(source), "ICO"), "便携环境无法生成图标检查文件。")
        value = import_image(source, icon=True)
        source.unlink()
        editor.value_committed.emit(value)
        panel.refresh()
        require(document.model.nodes[document.model.root_id].properties["window_icon"] == value,
                "程序图标没有写入项目。")
        frame = self.window.page.canvas.renderer.frame
        require(not frame.icon.isNull(), "画布标题栏没有更新程序图标。")
        panel.editors["window_icon"].clear_button.click()
        require(frame.icon.isNull(), "程序图标清除后未恢复默认。")
        document.undo()
        require(not frame.icon.isNull(), "程序图标清除无法撤销。")
        document.redo()
        require(frame.icon.isNull(), "程序图标清除无法重做。")
        document.undo()
        self.result["程序图标导入清除与撤销"] = "通过"

    def check_containers(self) -> None:
        document, registry = self.window.document, self.window.registry
        by_type = {node.type_id: node.id for node in document.model.nodes.values()}
        group, frame, radio = (by_type["builtin." + kind] for kind in ("group_box", "frame", "radio_button"))
        for node_id, values in (
            (group, {"geometry.width": 360, "geometry.height": 300}),
            (frame, {"geometry.width": 260, "geometry.height": 180}),
            (by_type["builtin.date_edit"], {"value": "2024-02-29"}),
            (by_type["builtin.double_spin_box"], {"decimals": 3, "value": 12.345}),
        ):
            for key, value in values.items():
                document.execute("配置扩展组件", lambda model, n=node_id, k=key, v=value:
                                 set_property(model, registry, n, k, v))
        document.execute("嵌套边框容器", lambda model: reparent_node(model, registry, frame, group))
        document.execute("嵌套单选框", lambda model: reparent_node(model, registry, radio, frame))
        original = document.model.to_bytes()
        fragment = copy_tree(document.model, registry, (group,))
        created: list[str] = []

        def paste(model: ProjectModel) -> ProjectModel:
            candidate, copies = paste_tree(model, registry, fragment)
            created.extend(copies)
            return candidate

        document.execute("验证整树粘贴", paste)
        require(len(subtree_ids(document.model, tuple(created))) == 3, "整树粘贴没有保留两层嵌套。")
        document.execute("验证整树删除", lambda model: delete_nodes(model, tuple(created)))
        require(document.model.to_bytes() == original, "整树删除没有完整还原原有对象。")
        document.undo()
        require(len(document.model.nodes) == self.expected_count + 3, "整树删除无法撤销。")
        document.redo()
        require(document.model.to_bytes() == original, "整树删除重做结果不一致。")
        self.result["容器嵌套与整树复制删除撤销"] = "通过"

    def saved(self, document: DocumentSession, success: bool, message: str) -> None:
        if self.done:
            return
        self.timer.start(30000)
        try:
            require(success, message)
            require(load_project(document.path).model.to_bytes() == self.expected, "保存与加载内容不一致。")
            self.result["保存与加载"] = "通过"
            path = document.path
            self.window._close_document(document)
            reopened = self.window.open_path(path)
            require(reopened.model.to_bytes() == self.expected, "重新打开项目内容不一致。")
            entry = self.window.export_python_to(self.directory / "独立代码")
            require(entry is not None, "未生成导出入口。")
            spec = importlib.util.spec_from_file_location("_交付导出入口", entry)
            require(spec is not None and spec.loader is not None, "无法加载导出入口。")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            event_name = next(handler["code_name"] for handler in reopened.model.data["handlers"])
            event_path = entry.parent / "event_handlers" / (event_name + ".py")
            event_code = (f"def {event_name}(window, *arguments):\n"
                          '    window.setProperty("event_check_count", (window.property("event_check_count") or 0) + 1)\n').encode("utf-8")
            atomic_write(event_path, event_code)
            export_project(reopened.model, self.window.registry, entry.parent)
            require(event_path.read_bytes() == event_code, "重复导出覆盖了事件业务代码。")
            generated = module.create_window(self.application)
            try:
                require(generated.windowTitle() == "便携版验收窗口", "导出窗口标题不一致。")
                for icon in (self.window.page.canvas.renderer.frame.icon, generated.windowIcon()):
                    require(not icon.isNull() and icon.pixmap(32, 32).toImage().pixelColor(16, 16) == QColor("#426e5c"),
                            "程序图标在重新打开项目或导出后不一致。")
                self.result["程序图标保存加载与导出"] = "通过"
                c = generated.controls
                require(c["rich_text_edit_1"].toPlainText() == "交付富文本" and
                        c["rich_text_edit_1"].document().documentMargin() == 10, "富文本内容或边距未导出。")
                require(c["text_browser_1"].toPlainText() == "交付链接" and not c["text_browser_1"].openLinks(),
                        "文本浏览器内容或链接行为未导出。")
                require(c["font_combo_box_1"].count() > 0 and not c["font_combo_box_1"].isEditable(),
                        "字体组合框丢失字体列表。")
                require(c["key_sequence_edit_1"].keySequence().toString() == "Ctrl+Shift+K" and
                        c["key_sequence_edit_1"].maximumSequenceLength() == 1, "快捷键编辑框属性未导出。")
                require(not c["button_1"].icon().isNull() and c["button_1"].iconSize().width() == 24 and
                        c["button_1"].shortcut().toString() == "Ctrl+K", "按钮图标或快捷键未导出。")
                require(c["label_1"].textFormat() == Qt.TextFormat.RichText, "标签富文本属性未导出。")
                require(not c["group_box_1"].isChecked() and not c["radio_button_1"].isEnabled(),
                        "取消分组选中后子控件仍启用。")
                c["group_box_1"].setChecked(True)
                require(c["radio_button_1"].isEnabled(), "重新勾选分组未恢复子控件。")
                self.result["富文本字体快捷键图标与分组导出"] = "通过"
                require(len(generated.controls) == self.expected_count, "导出组件数量不一致。")
                for node in reopened.model.nodes.values():
                    spec = self.window.registry.require(node.type_id)
                    require(generated.controls[node.code_name].inherits(spec.qt_class),
                            f"导出组件“{node.name}”类型不一致。")
                    if node.slot == "children":
                        actual = generated.controls[node.code_name]
                        parent = reopened.model.nodes[node.parent_id]
                        require(actual.parentWidget() is generated.controls[parent.code_name], "导出组件父级不一致。")
                        require(actual.mapTo(generated, QPoint()) == QPoint(*absolute_position(reopened.model, node.id)),
                                "导出容器内组件位置不一致。")
                require(generated.controls["date_edit_1"].date().toString("yyyy-MM-dd") == "2024-02-29", "闰年日期未正确导出。")
                require(generated.controls["double_spin_box_1"].value() == 12.345, "小数精度未正确导出。")
                require(len(generated.controls["tab_widget_1"].pages) == 2 and
                        generated.controls["tab_widget_1"].tab_bar.currentIndex() == 1, "选择夹默认页未正确导出。")
                require(generated.controls["check_box_1"].parentWidget() is generated.controls["tab_page_2"], "选择夹子控件挂接错误。")
                require(generated.controls["timer_1"].isActive(), "导出时钟未启动。")
                require(generated.controls["super_list_1"].columnCount() == 3, "超级列表框列未正确导出。")
                for name, expected_widths in (("table_widget_1", (56, 280)), ("super_list_1", (56, 160, 280))):
                    control = generated.controls[name]
                    require(tuple(control.columnWidth(i) for i in range(control.columnCount())) == expected_widths,
                            "保存加载或导出后丢失了自定义列宽。")
                self.result["逐列宽度保存加载与导出"] = "通过"
                require(generated.controls["common_dialog_1"]._trigger is generated.controls["button_1"], "通用对话框按钮未绑定。")
                generated.controls["common_dialog_1"].open_dialog()
                require(generated.controls["common_dialog_1"].dialog is not None, "通用对话框无法打开。")
                generated.controls["common_dialog_1"].dialog.reject()
                generated.controls["common_dialog_1"].bind_trigger(None)
                require(not generated.controls["picture_box_1"].picture.isNull(), "导出图片文件缺失或无法解码。")
                generated.controls["text_edit_1"].setPlainText("第一行\n第二行")
                require(generated.controls["text_edit_1"].toPlainText() == "第一行\n第二行", "多行输入失效。")
                require(generated.controls["combo_box_1"].count() == 3, "组合框项目未导出。")
                require(generated.controls["table_widget_1"].item(0, 0).text() == "项目一", "表格内容未导出。")
                require(generated.controls["tree_widget_1"].topLevelItem(0).child(0).text(0) == "项目一", "树形内容未导出。")
                require(all(generated.controls[name].x() == 48 for name in ("button_1", "label_1", "line_edit_1")),
                        "导出的排版位置与画布不一致。")
                generated.controls["line_edit_1"].setText("中文输入验证")
                require(generated.controls["line_edit_1"].text() == "中文输入验证", "导出编辑框无法输入。")
                generated.controls["button_1"].clicked.connect(lambda: generated.setWindowTitle("事件已执行"))
                generated.controls["button_1"].click()
                require(generated.windowTitle() == "事件已执行", "导出按钮信号失效。")
                require(generated.property("event_check_count") == 1, "勾选事件没有自动执行或发生重复连接。")
                self.result["事件自动连接与重复导出保护"] = "通过"
                original_rect = reopened.model.nodes[reopened.model.root_id].geometry
                generated.show()
                self.application.processEvents()
                generated.resize(original_rect.width + 160, original_rect.height + 80)
                self.application.processEvents()
                expected = resize_node(reopened.model, reopened.model.root_id,
                                       replace(original_rect, width=generated.width(), height=generated.height()))
                for node in expected.nodes.values():
                    if node.slot == "children":
                        control = generated.controls[node.code_name]
                        require((control.width(), control.height()) == (node.geometry.width, node.geometry.height),
                                "导出组件随窗口缩放后的尺寸不一致。")
                        require(control.mapTo(generated, QPoint()) == QPoint(*absolute_position(expected, node.id)),
                                "导出嵌套组件随窗口缩放后位置不一致。")
                generated.resize(original_rect.width, original_rect.height)
                self.result["导出窗口组件跟随缩放"] = "通过"
            finally:
                generated.close()
                generated.deleteLater()
            button = next(node.id for node in reopened.model.nodes.values() if node.type_id == "builtin.button")
            disabled = set_event_enabled(reopened.model, self.window.registry, button, "clicked", False)
            export_project(disabled, self.window.registry, entry.parent)
            disconnected = module.create_window(self.application)
            try:
                disconnected.controls["common_dialog_1"].bind_trigger(None)
                disconnected.controls["button_1"].click()
                require(disconnected.property("event_check_count") is None, "未勾选事件仍连接了处理函数。")
                require(event_path.read_bytes() == event_code, "取消勾选删除或修改了业务代码。")
                self.result["取消事件勾选后不连接"] = "通过"
            finally:
                disconnected.close()
                disconnected.deleteLater()
            self.result["代码导出与运行"] = "通过"
            self.result["嵌套坐标与日期小数导出"] = "通过"
            self.result["时钟对话框图片与窗口条导出"] = "通过"
            export_diagnostics(self.directory / "本地诊断.zip", {"检查": "交付"})
            self.result["诊断包"] = "通过"
            self.timer.start(30000)
            self.window.preview_current()
        except Exception:
            logging.getLogger(__name__).exception("交付保存或导出检查失败。")
            self.fail("保存、加载或导出检查失败，详细信息见本地日志。")

    def check_menus(self) -> None:
        from core.build_plan import compile_plan
        from core.models import new_project
        from panels.menu_editor import MenuEditor
        from runtime.builder import RuntimeTree

        registry = self.window.registry
        draft = MenuEditor(new_project("菜单交付检查"), registry, self.window)
        tree = RuntimeTree(registry, design_mode=False)
        try:
            draft.operate("add")
            draft.title_edit.setText("文件(&F)")
            draft.operate("child")
            draft.title_edit.setText("显示说明")
            draft.code_edit.setText("menu_check")
            draft.checked.setChecked(True)
            draft.shortcut_edit.setKeySequence("Ctrl+M")
            draft.connected.setChecked(True)
            draft.accept()
            require(draft.result() == 1, "菜单编辑器未能确认有效菜单。")
            model = draft.model
            key = draft.selected_id
            tree.apply(compile_plan(model, registry, "菜单交付"))
            action = tree.widgets[key]
            require(action.isChecked() and action.shortcut().toString() == "Ctrl+M", "原生菜单属性不一致。")
            require(tree.root.menuBar().actions()[0].menu().actions() == [action], "子菜单层级不一致。")
            entry = export_project(model, registry, self.directory / "菜单独立导出")
            spec = importlib.util.spec_from_file_location("_menu_release_check", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            generated = module.create_window(self.application)
            try:
                menu_action = generated.controls["menu_check"]
                require(menu_action.isChecked() and menu_action.shortcut().toString() == "Ctrl+M", "导出菜单属性丢失。")
                require(generated.menuBar().actions()[0].menu().actions() == [menu_action], "导出菜单层级丢失。")
                menu_action.trigger()
                require(not menu_action.isChecked(), "菜单选中状态未切换。")
            finally:
                generated.close()
                generated.deleteLater()
            self.result["菜单编辑器与层级快捷键导出"] = "通过"
            self.menu_preview_model = model
        finally:
            tree.dispose()
            draft.deleteLater()

    def preview_ready(self, message: dict[str, Any]) -> None:
        try:
            require(message["process_id"] != os.getpid(), "预览未使用独立进程。")
            if self.menu_preview_started:
                model = self.menu_preview_model
                require(message["widget_count"] == len(model.nodes) and message["title"] == model.name,
                        "只有菜单的项目预览内容不一致。")
                self.result["仅菜单项目独立预览启动"] = "通过"
                self.result["菜单预览进程"] = message["process_id"]
            else:
                require(message["widget_count"] == self.expected_count and message["title"] == "便携版验收窗口", "预览内容不一致。")
                self.result["独立预览启动"] = "通过"
                self.result["预览进程"] = message["process_id"]
            self.stopping = True
            QTimer.singleShot(100, self.window.preview_service.stop)
        except Exception:
            logging.getLogger(__name__).exception("交付预览检查失败。")
            self.fail("预览内容验证失败。")

    def preview_changed(self) -> None:
        if self.stopping and not self.window.preview_service.active and not self.done:
            if self.menu_preview_started:
                self.result["仅菜单项目独立预览停止"] = "通过"
                self.finish(0)
            else:
                self.result["独立预览停止"] = "通过"
                self.stopping = False
                self.menu_preview_started = True
                try:
                    require(self.menu_preview_model is not None, "缺少菜单预览检查项目。")
                    self.timer.start(30000)
                    self.window.preview_service.start(self.menu_preview_model, "菜单交付预览", "菜单交付会话")
                except Exception:
                    logging.getLogger(__name__).exception("仅菜单项目独立预览失败。")
                    self.fail("仅菜单项目无法启动独立预览。")

    def fail(self, message: str) -> None:
        if not self.done:
            self.result["错误"] = message
            self.finish(1)

    def finish(self, code: int) -> None:
        if self.done:
            return
        self.done = True
        self.timer.stop()
        self.result["检查结果"] = "通过" if code == 0 else "失败"
        try:
            self.report.parent.mkdir(parents=True, exist_ok=True)
            screenshot = self.report.with_suffix(".png")
            require(self.window.grab().save(str(screenshot)), "交付检查截图失败。")
            atomic_write(self.report, json.dumps(self.result, ensure_ascii=False, indent=2).encode("utf-8"))
        except Exception:
            logging.getLogger(__name__).exception("交付检查报告写入失败。")
            code = 1
        finally:
            self.window.preview_service.shutdown()
            # 保存任务尚未结束时交由事件循环等待回执，避免释放活动写锁。
            if any(self.window.tabs.widget(i).document.saving for i in range(self.window.tabs.count())):
                QTimer.singleShot(100, lambda: self.close_when_saved(code))
            else:
                self.close_when_saved(code)

    def close_when_saved(self, code: int) -> None:
        if any(self.window.tabs.widget(i).document.saving for i in range(self.window.tabs.count())):
            QTimer.singleShot(100, lambda: self.close_when_saved(code))
            return
        self.window.discard_all_for_test()
        self.window.close()
        self.temporary.cleanup()
        self.application.exit(code)
