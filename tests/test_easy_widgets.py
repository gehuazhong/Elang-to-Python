"""易语言常用组件的项目、画布、预览和独立导出闭环。"""

from __future__ import annotations

import base64
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog, QFontDialog

from app.main_window import MainWindow
from codegen.publisher import export_project
from core.events import set_event_enabled
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.nodes import create_node, delete_node, set_property
from core.commands.pages import add_page, select_page
from core.commands.tree_clipboard import copy_tree, decode_tree, encode_tree, paste_tree
from core.document import DocumentSession
from core.errors import DesignerError
from core.hierarchy import absolute_position, active_page, content_size, pages, subtree_ids
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from panels.image_editor import import_image
from runtime.builder import RuntimeTree
from runtime.easy_widgets import CommonDialog, DrawingBoard, PictureBox, SelectionTabs, SuperList
from runtime.preview import PreviewRuntime
from tests.test_clipboard import window, open_context
from tests.test_codegen import load_export
from tests.test_storage import wait_for

KINDS = ("drawing_board", "picture_box", "tab_widget", "timer", "common_dialog", "super_list", "tool_bar", "status_bar")


def image_value(tmp_path: Path) -> str:
    source = tmp_path / "中文图片.png"
    image = QImage(64, 48, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2e735c"))
    assert image.save(str(source))
    value = import_image(source)
    source.unlink()
    return value


def complete_model(project: ProjectModel, registry: WidgetRegistry, tmp_path: Path) -> tuple[ProjectModel, dict[str, str]]:
    keys: dict[str, str] = {}
    for index, kind in enumerate(KINDS):
        project, keys[kind] = create_node(project, registry, "builtin." + kind, 24 + index * 8, 24 + index * 8)
    first, second = pages(project, keys["tab_widget"])
    project, keys["button"] = create_node(project, registry, "builtin.button", 16, 24, parent_id=first.id)
    project, keys["label"] = create_node(project, registry, "builtin.label", 32, 48, parent_id=second.id)
    project = set_property(project, registry, keys["picture_box"], "image", image_value(tmp_path))
    project = set_property(project, registry, keys["common_dialog"], "trigger_control", project.nodes[keys["button"]].code_name)
    project = set_property(project, registry, keys["timer"], "enabled", False)
    return project, keys


def test_all_requested_names_resolve_in_toolbox(window: MainWindow, qt_app: QApplication) -> None:
    panel = window.toolbox
    for name in ("按钮", "标签", "编辑框", "单选框", "分组框", "画板", "列表框", "时钟", "通用对话框", "图片框",
                 "选择夹", "选择框", "组合框", "超级列表框", "工具条", "状态条"):
        panel.search.setText(name)
        assert any(not panel.tree.topLevelItem(i).isHidden() for i in range(panel.tree.topLevelItemCount())), name


def test_picture_border_survives_image_clipping(qt_app: QApplication) -> None:
    widget = PictureBox()
    widget.resize(80, 60)
    palette = widget.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Mid, QColor("#b32937"))
    widget.setPalette(palette)
    widget.picture = QImage(16, 16, QImage.Format.Format_ARGB32)
    widget.picture.fill(QColor("#2e735c"))
    try:
        for mode in ("fit", "stretch", "center"):
            widget.mode = mode
            widget.border = True
            rendered = widget.grab().toImage()
            scale = rendered.devicePixelRatio()
            for x, y in ((0, 30), (79, 30), (40, 0), (40, 59)):
                assert rendered.pixelColor(round(x * scale), round(y * scale)) == QColor("#b32937"), mode
            assert rendered.pixelColor(round(40 * scale), round(30 * scale)) == QColor("#2e735c")
            widget.border = False
            rendered = widget.grab().toImage()
            assert rendered.pixelColor(0, round(30 * scale)) != QColor("#b32937"), mode
    finally:
        widget.close()
        widget.deleteLater()


def test_save_preview_and_export_preserve_pages_images_and_structures(project: ProjectModel, registry: WidgetRegistry,
                                                                     qt_app: QApplication, tmp_path: Path) -> None:
    project, keys = complete_model(project, registry, tmp_path)
    path = tmp_path / "全部基础组件.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    canvas = DesignerCanvas(DocumentSession(loaded, registry))
    exported = load_export(export_project(loaded, registry, tmp_path / "独立基础组件"), qt_app)
    try:
        qt_app.processEvents()
        assert len(exported.controls) == len(project.nodes) == len(canvas.renderer.tree.widgets)
        for key in keys.values():
            node = project.nodes[key]
            actual = exported.controls[node.code_name]
            native = canvas.renderer.tree.widgets[key]
            assert type(actual).__name__ == type(native).__name__
            if node.geometry:
                expected = QPoint(*absolute_position(project, key))
                assert native.mapTo(canvas.renderer.tree.root, QPoint()) == expected
                assert actual.mapTo(exported, QPoint()) == expected
                assert canvas.renderer.items[key].scenePos() == QPointF(expected)
        assert not exported.controls[project.nodes[keys["picture_box"]].code_name].picture.isNull()
        assert list((tmp_path / "独立基础组件/generated").glob("*/assets/*.png"))
        assert not canvas.renderer.tree.widgets[keys["timer"]].isActive()
        assert not exported.controls[project.nodes[keys["timer"]].code_name].isActive()
    finally:
        exported.close()
        exported.deleteLater()
        canvas.dispose()
        canvas.close()


def test_tabs_have_separate_children_and_reversible_page_deletion(project: ProjectModel, registry: WidgetRegistry,
                                                                qt_app: QApplication) -> None:
    project, tab = create_node(project, registry, "builtin.tab_widget", 32, 40)
    first, second = pages(project, tab)
    project, button = create_node(project, registry, "builtin.button", 16, 24, parent_id=first.id)
    project, label = create_node(project, registry, "builtin.label", 16, 24, parent_id=second.id)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    try:
        original_title_image = canvas.renderer.items[tab].pixmap().toImage()
        document.execute("修改页标题", lambda model: set_property(model, registry, first.id, "text", "完整的中文页面标题"))
        assert canvas.renderer.tree.widgets[tab].tab_bar.tabText(0) == "完整的中文页面标题"
        assert canvas.renderer.items[tab].pixmap().toImage() != original_title_image
        document.undo()
        assert canvas.renderer.items[button].isVisible()
        assert not canvas.renderer.items[label].isVisible()
        document.execute("切换页面", lambda model: select_page(model, registry, tab, 1))
        assert not canvas.renderer.items[button].isVisible()
        assert canvas.renderer.items[label].isVisible()
        snapshot = document.model
        document.execute("删除页面", lambda model: delete_node(model, first.id))
        assert button not in document.model.nodes and active_page(document.model, tab) == second.id
        with pytest.raises(DesignerError, match="至少"):
            document.execute("删除最后一页", lambda model: delete_node(model, second.id))
        document.undo()
        assert document.model == snapshot
        fragment = decode_tree(encode_tree(copy_tree(document.model, registry, (tab,))), registry)
        cloned, roots = paste_tree(document.model, registry, fragment)
        assert len(subtree_ids(cloned, roots)) == 5
        assert len(pages(cloned, roots[0])) == 2
    finally:
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("kind", KINDS)
def test_component_copy_delete_undo(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    fragment = copy_tree(project, registry, (key,)) if kind == "tab_widget" else copy_fragment(project, registry, key)
    empty = delete_node(project, key)
    candidate, _ = paste_tree(empty, registry, fragment) if kind == "tab_widget" else paste_fragment(empty, registry, fragment)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    errors: list[str] = []
    canvas.error.connect(errors.append)
    try:
        for _ in range(3):
            document.execute("删除基础组件", lambda model: delete_node(model, key))
            qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            document.undo()
            assert key in canvas.renderer.items
        assert not errors and document.model == project
        registry.validate(candidate)
    finally:
        canvas.dispose()
        canvas.close()


def test_timer_only_runs_in_preview_and_stops_on_dispose(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication) -> None:
    project, timer = create_node(project, registry, "builtin.timer", 0, 0)
    project = set_property(project, registry, timer, "interval", 10)
    project = set_event_enabled(project, registry, timer, "timeout", True)
    tree = RuntimeTree(registry)
    preview = PreviewRuntime(registry)
    try:
        plan = compile_plan(project, registry, "时钟检查")
        tree.apply(plan)
        assert isinstance(tree.widgets[timer], QTimer) and not tree.widgets[timer].isActive()
        messages = QSignalSpy(preview.notice)
        preview.show(plan, project)
        clock = preview.tree.widgets[timer]
        ticks = QSignalSpy(clock.timeout)
        wait_for(lambda: ticks.count() >= 2, qt_app)
        assert messages.count() >= 1 and clock.isActive()
        preview.dispose()
        assert not clock.isActive()
    finally:
        tree.dispose()
        preview.dispose()


@pytest.mark.parametrize("kind,expected", [("open_file", QFileDialog), ("open_files", QFileDialog),
    ("save_file", QFileDialog), ("directory", QFileDialog), ("color", QColorDialog), ("font", QFontDialog)])
def test_common_dialog_button_trigger_and_result(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication,
                                               kind: str, expected: type) -> None:
    project, button = create_node(project, registry, "builtin.button", 20, 20)
    project, key = create_node(project, registry, "builtin.common_dialog", 0, 0)
    project = set_property(project, registry, key, "dialog_kind", kind)
    project = set_property(project, registry, key, "trigger_control", project.nodes[button].code_name)
    preview = PreviewRuntime(registry)
    try:
        preview.show(compile_plan(project, registry, "对话框检查"), project)
        adapter = preview.tree.widgets[key]
        assert isinstance(adapter, CommonDialog) and adapter.dialog is None
        cancelled = QSignalSpy(adapter.cancelled)
        accepted = QSignalSpy(adapter.accepted)
        preview.tree.widgets[button].click()
        qt_app.processEvents()
        assert isinstance(adapter.dialog, expected) and adapter.dialog.windowTitle() == "请选择"
        if isinstance(adapter.dialog, QFileDialog):
            assert adapter.dialog.labelText(QFileDialog.DialogLabel.LookIn) == "查找位置："
            assert adapter.dialog.labelText(QFileDialog.DialogLabel.FileType) == "文件类型："
        first = adapter.dialog
        preview.tree.widgets[button].click()
        assert adapter.dialog is first
        if kind == "color":
            first.setCurrentColor(QColor("#397c61"))
            first.accept()
            assert accepted.count() == 1 and adapter.result == "#397c61"
        elif kind == "font":
            first.accept()
            assert accepted.count() == 1 and "字体" in adapter.result
        else:
            first.reject()
            assert cancelled.count() == 1
        assert adapter.dialog is None
    finally:
        preview.dispose()


def test_dialog_button_deletion_clears_binding_in_same_undo(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, button = create_node(project, registry, "builtin.button", 20, 20)
    project, key = create_node(project, registry, "builtin.common_dialog", 0, 0)
    project = set_property(project, registry, key, "trigger_control", project.nodes[button].code_name)
    document = DocumentSession(project, registry)
    document.execute("删除触发按钮", lambda model: delete_node(model, button))
    assert document.model.nodes[key].properties["trigger_control"] == ""
    document.undo()
    assert document.model == project
    fragment = copy_fragment(project, registry, key)
    assert fragment.omitted_connections == 1 and fragment.node.properties["trigger_control"] == ""


@pytest.mark.parametrize("kind", ["open_file", "open_files", "save_file", "directory"])
def test_file_dialog_returns_selection_without_writing_files(project: ProjectModel, registry: WidgetRegistry,
                                                            qt_app: QApplication, tmp_path: Path, kind: str) -> None:
    existing = tmp_path / "输入文件.txt"
    existing.write_text("对话框选择验证", encoding="utf-8")
    target = tmp_path if kind == "directory" else tmp_path / "尚未创建.txt" if kind == "save_file" else existing
    project, key = create_node(project, registry, "builtin.common_dialog", 0, 0)
    project = set_property(project, registry, key, "dialog_kind", kind)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "对话框返回值"))
        component = tree.widgets[key]
        accepted = QSignalSpy(component.accepted)
        component.open_dialog()
        component.dialog.selectFile(str(target))
        component.dialog.accept()
        wait_for(lambda: accepted.count() == 1, qt_app)
        assert [Path(path) for path in component.result] == [target]
        if kind == "save_file":
            assert not target.exists()
        assert existing.read_text(encoding="utf-8") == "对话框选择验证"
    finally:
        tree.dispose()


def test_super_list_checks_sort_selection_and_drawing_do_not_change_model(project: ProjectModel, registry: WidgetRegistry,
                                                                       qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.super_list", 20, 20)
    for name, value in {"table_data": {"headers": ["项目", "说明"], "rows": [["乙", "二"], ["甲", "一"]]},
                        "checkboxes": True, "checked_rows": ["2"], "sorting": True, "multi_select": True}.items():
        project = set_property(project, registry, key, name, value)
    project, board = create_node(project, registry, "builtin.drawing_board", 200, 280)
    before = project.to_bytes()
    preview = PreviewRuntime(registry)
    try:
        preview.show(compile_plan(project, registry, "基础交互"), project)
        view = preview.tree.widgets[key]
        assert isinstance(view, SuperList) and view.columnCount() == 2
        items = [view.topLevelItem(i) for i in range(view.topLevelItemCount())]
        checked = next(item for item in items if item.checkState(0) == Qt.CheckState.Checked)
        assert checked.text(0) == "甲"
        checked.setCheckState(0, Qt.CheckState.Unchecked)
        view.sortItems(0, Qt.SortOrder.AscendingOrder)
        drawing = preview.tree.widgets[board]
        assert isinstance(drawing, DrawingBoard)
        drawing.draw_line(12, 12, 60, 12)
        assert drawing.ink.pixelColor(24, 12).alpha() > 0
        drawing.clear()
        assert drawing.ink.pixelColor(24, 12).alpha() == 0
        assert project.to_bytes() == before
    finally:
        preview.dispose()


def test_canvas_tab_click_and_drop_reaches_active_page(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    tab = canvas.create_component("builtin.tab_widget", QPointF(32, 40))
    qt_app.processEvents()
    tabs = canvas.renderer.tree.widgets[tab]
    point = canvas.mapFromScene(canvas.renderer.items[tab].mapToScene(QPointF(tabs.tab_bar.tabRect(1).center())))
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    assert document.model.nodes[tab].properties["current_index"] == 1
    child = canvas.create_component("builtin.button", QPointF(64, 112))
    assert document.model.nodes[child].parent_id == pages(document.model, tab)[1].id
    document.select(tab)
    qt_app.processEvents()
    menu = open_context(window, tree_id=tab)
    assert any(action.text() == "添加页面" for action in menu.actions())
    menu.close()


@pytest.mark.parametrize("kind", ["timer", "common_dialog", "tool_bar", "status_bar"])
def test_special_components_can_be_selected_and_deleted(window: MainWindow, qt_app: QApplication, kind: str) -> None:
    canvas, document = window.page.canvas, window.document
    key = canvas.create_component("builtin." + kind)
    qt_app.processEvents()
    assert key in canvas.renderer.items
    point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
    assert canvas.node_at(point) == key
    document.select(key)
    qt_app.processEvents()
    assert window.edit_actions.node_states()[2]
    window.edit_actions.delete()
    assert key not in document.model.nodes
    document.undo()
    assert key in document.model.nodes


def test_easy_export_runs_with_isolated_imports(project: ProjectModel, registry: WidgetRegistry,
                                              tmp_path: Path, qt_app: QApplication) -> None:
    project, _ = complete_model(project, registry, tmp_path)
    entry = export_project(project, registry, tmp_path / "隔离导出")
    source = '''import importlib.util, sys
from PySide6.QtWidgets import QApplication
application = QApplication([])
spec = importlib.util.spec_from_file_location("入口", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window = module.create_window(application)
assert len(window.controls['tab_widget_1'].pages) == 2
assert not window.controls['picture_box_1'].picture.isNull()
assert not window.controls['timer_1'].isActive()
assert window.controls['super_list_1'].columnCount() == 3
assert not any(name in sys.modules for name in ('core', 'runtime', 'app', 'widgets'))
window.close()
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", source, str(entry)], cwd=tmp_path,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind,key,value", [("timer", "interval", 0), ("tab_widget", "current_index", 3),
    ("super_list", "checked_rows", ["999"]), ("picture_box", "image", "损坏"), ("common_dialog", "trigger_control", "missing")])
def test_invalid_easy_properties_are_atomic(project: ProjectModel, registry: WidgetRegistry, kind: str, key: str, value: object) -> None:
    project, node = create_node(project, registry, "builtin." + kind, 20, 20)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("无效基础属性", lambda model: set_property(model, registry, node, key, value))
    assert document.model is project and document.history.cursor == 0
