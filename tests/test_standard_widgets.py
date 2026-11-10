"""常用组件的编辑、关联属性、序列化、预览和独立导出回归。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QTableWidgetItem

from codegen.publisher import export_project
from core.events import set_event_enabled
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, decode_fragment, encode_fragment, paste_fragment
from core.commands.group_clipboard import copy_group, paste_group
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.metadata import PropertySpec
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.canvas import DesignerCanvas
from designer.mime import component_mime
from panels.content_editor import ContentDialog, ContentEditor
from panels.properties import PropertyPanel
from runtime.builder import RuntimeTree, verify_registry
from runtime.preview import PreviewRuntime
from runtime.widget_properties import ENUMS
from tests.test_codegen import load_export


TYPES = ("text_edit", "combo_box", "check_box", "radio_button", "spin_box", "progress_bar", "slider",
         "list_widget", "table_widget", "tree_widget")
VALUES: dict[str, dict[str, Any]] = {
    "text_edit": {"text": "第一行\n第二行 <b>纯文本</b>\n", "read_only": True, "line_wrap": "none", "tab_changes_focus": True},
    "combo_box": {"items": ["重复", "重复", "末项"], "current_index": 2, "editable": True, "insert_policy": "bottom"},
    "check_box": {"tristate": True, "check_state": "partial"},
    "radio_button": {"checked": True},
    "spin_box": {"maximum": 500, "value": 138, "single_step": 3, "prefix": "数量：", "suffix": " 件", "button_symbols": "plus_minus"},
    "progress_bar": {"value": 63, "format": "%v / %m", "inverted": True},
    "slider": {"value": 24, "orientation": "vertical", "tick_position": "both", "tick_interval": 5},
    "list_widget": {"items": ["", "中文", "重复", "重复"], "current_index": 1, "edit_triggers": "double_click"},
    "table_widget": {"table_data": {"headers": ["名称", "数量", "备注"], "rows": [["中文", "10", ""], ["引号'\\", "20", "末行"]]},
                     "show_vertical_header": False, "selection_behavior": "columns", "edit_triggers": "all"},
    "tree_widget": {"tree_data": [{"text": "分组", "children": [{"text": "子项目", "children": [{"text": "孙项目", "children": []}]}]},
                                   {"text": "末项", "children": []}], "header_text": "项目目录", "expanded": False, "edit_triggers": "double_click"},
}


def configured(project: ProjectModel, registry: WidgetRegistry, kind: str) -> tuple[ProjectModel, str]:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    for prop, value in {**VALUES[kind], "font_bold": True, "font_italic": True, "font_underline": True,
                        "font_strikeout": True, "status_tip": "状态说明", "layout_direction": "right_to_left"}.items():
        project = set_property(project, registry, key, prop, value)
    return project, key


def content(widget: Any, kind: str) -> Any:
    if kind == "text_edit":
        return widget.toPlainText()
    if kind == "combo_box":
        return [widget.itemText(i) for i in range(widget.count())], widget.currentIndex()
    if kind == "list_widget":
        return [widget.item(i).text() for i in range(widget.count())], widget.currentRow()
    if kind == "check_box":
        return widget.checkState()
    if kind == "table_widget":
        return ([widget.horizontalHeaderItem(i).text() for i in range(widget.columnCount())],
                [[widget.item(r, c).text() for c in range(widget.columnCount())] for r in range(widget.rowCount())],
                widget.horizontalHeader().isHidden(), widget.verticalHeader().isHidden())
    if kind == "tree_widget":
        def collect(parent: Any) -> Any:
            return [(parent.child(i).text(0), collect(parent.child(i)), parent.child(i).isExpanded()) for i in range(parent.childCount())]
        return widget.headerItem().text(0), collect(widget.invisibleRootItem())
    return widget.isChecked() if kind == "radio_button" else (widget.minimum(), widget.maximum(), widget.value())


@pytest.mark.parametrize("kind", TYPES)
def test_complete_roundtrip_native_export_and_copy(project: ProjectModel, registry: WidgetRegistry,
                                                  qt_app: QApplication, tmp_path: Path, kind: str) -> None:
    verify_registry(registry)
    project, key = configured(project, registry, kind)
    document = DocumentSession(project, registry)
    fragment = decode_fragment(encode_fragment(copy_fragment(project, registry, key)), registry)
    copied, copied_key = paste_fragment(project, registry, fragment)
    assert copied.nodes[copied_key].properties == project.nodes[key].properties
    registry.validate(copied)
    path = tmp_path / "组件.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    tree = RuntimeTree(registry, design_mode=False)
    preview = PreviewRuntime(registry)
    generated = load_export(export_project(loaded, registry, tmp_path / "独立导出"), qt_app)
    try:
        plan = compile_plan(loaded, registry, "组件一致性")
        tree.apply(plan)
        preview.show(plan, loaded)
        expected = tree.widgets[key]
        for actual in (preview.tree.widgets[key], generated.controls[loaded.nodes[key].code_name]):
            assert content(actual, kind) == content(expected, kind)
            assert actual.geometry() == expected.geometry()
            assert actual.font() == expected.font()
            assert actual.isHidden() == expected.isHidden()
            for prop in registry.require("builtin." + kind).properties:
                if prop.qt_name and prop.key != "visible":
                    assert actual.property(prop.qt_name) == expected.property(prop.qt_name), prop.key
        assert not tree.image(key, 1).isNull()
        assert document.model.to_bytes() == project.to_bytes()
    finally:
        generated.close()
        generated.deleteLater()
        preview.dispose()
        tree.dispose()


@pytest.mark.parametrize("kind", TYPES)
def test_mime_creation_property_panel_and_history(project: ProjectModel, registry: WidgetRegistry,
                                                 qt_app: QApplication, kind: str) -> None:
    document = DocumentSession(project, registry)
    canvas, panel = DesignerCanvas(document), PropertyPanel()
    panel.bind(document)
    canvas.show()
    qt_app.processEvents()
    try:
        point = canvas.mapFromScene(QPointF(40, 48))
        mime = component_mime("builtin." + kind)
        event = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                           Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        canvas.dropEvent(event)
        qt_app.processEvents()
        assert event.isAccepted()
        key = document.selected_id
        assert document.model.nodes[key].type_id == "builtin." + kind
        spec = registry.require("builtin." + kind)
        # Layout item controls are shown only while a native layout owns the widget.
        assert {prop.key for prop in spec.properties if prop.group != "布局项"} <= panel.editors.keys()
        assert not {prop.key for prop in spec.properties if prop.group == "布局项"} & panel.editors.keys()
        for prop in spec.properties:
            if prop.value_type in {"multiline", "string_list", "table", "tree"}:
                assert isinstance(panel.editors[prop.key], ContentEditor)
        document.undo()
        assert key not in document.model.nodes
        document.redo()
        assert key in document.model.nodes
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("kind", ("spin_box", "slider", "progress_bar"))
def test_range_change_clamps_once_and_undo_restores(project: ProjectModel, registry: WidgetRegistry,
                                                 qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    project = set_property(project, registry, key, "value", 75)
    document = DocumentSession(project, registry)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(document.model, registry, "初始范围"))
        document.execute("缩小范围", lambda m: set_property(m, registry, key, "maximum", 20))
        assert document.model.nodes[key].properties["value"] == 20 and document.history.cursor == 1
        tree.apply(compile_plan(document.model, registry, "缩小范围"))
        assert tree.widgets[key].value() == 20
        document.undo()
        tree.apply(compile_plan(document.model, registry, "撤销范围"))
        assert tree.widgets[key].value() == 75 and tree.widgets[key].maximum() == 100
        before = document.model
        for prop, value in (("minimum", 101), ("maximum", -1), ("value", 101), ("value", True)):
            with pytest.raises(DesignerError):
                document.execute("错误范围", lambda m: set_property(m, registry, key, prop, value))
            assert document.model is before
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ("combo_box", "list_widget"))
def test_deleting_items_adjusts_index_in_same_command(project: ProjectModel, registry: WidgetRegistry, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    project = set_property(project, registry, key, "current_index", 2)
    document = DocumentSession(project, registry)
    document.execute("清空项目", lambda m: set_property(m, registry, key, "items", []))
    assert document.model.nodes[key].properties["current_index"] == -1
    document.undo()
    assert document.model.nodes[key].properties["current_index"] == 2
    with pytest.raises(DesignerError):
        document.execute("无效选项", lambda m: set_property(m, registry, key, "current_index", 3))


def test_radio_exclusivity_copy_and_undo(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, first = create_node(project, registry, "builtin.radio_button", 24, 24)
    project, second = create_node(project, registry, "builtin.radio_button", 24, 64)
    project = set_property(project, registry, first, "checked", True)
    document = DocumentSession(project, registry)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(document.model, registry, "单选初始"))
        document.execute("选中第二项", lambda m: set_property(m, registry, second, "checked", True))
        tree.apply(compile_plan(document.model, registry, "单选变化"))
        assert tree.widgets[second].isChecked() and not tree.widgets[first].isChecked()
        document.undo()
        tree.apply(compile_plan(document.model, registry, "单选撤销"))
        assert tree.widgets[first].isChecked() and not tree.widgets[second].isChecked()
        copied, keys = paste_group(document.model, registry, copy_group(document.model, registry, (first, second)))
        registry.validate(copied)
        assert not copied.nodes[first].properties["checked"] and copied.nodes[keys[0]].properties["checked"]
        conflicting = replace(project.nodes[second], properties=project.nodes[second].properties.changed(checked=True))
        with pytest.raises(DesignerError, match="只能选中一个"):
            registry.validate(project.with_nodes({second: conflicting}))
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind,value", [
    ("string_list", ["第一行\n第二行"]), ("string_list", [1]), ("string_list", [""] * 1001),
    ("table", {"headers": ["标题"], "rows": [["内容", "多余"]]}),
    ("table", {"headers": ["标题"], "rows": [[""]] * 201}),
    ("tree", [{"text": "节点", "children": [], "未知": 1}]),
    ("tree", [{"text": "节点", "children": "错误"}]),
])
def test_invalid_collection_is_rejected(kind: str, value: Any) -> None:
    with pytest.raises(DesignerError):
        PropertySpec("content", "内容", "内容", kind, None).normalize(value)


def test_collection_defaults_cannot_mutate_frozen_registry(registry: WidgetRegistry) -> None:
    value = registry.require("builtin.table_widget").property("table_data").default
    with pytest.raises(TypeError):
        value["headers"] = ("错误修改",)
    tree = registry.require("builtin.tree_widget").property("tree_data").default
    with pytest.raises(TypeError):
        tree[0]["text"] = "错误修改"
    fingerprint = registry.fingerprint
    assert registry.freeze().fingerprint == fingerprint


def test_button_checked_and_checkable_remain_consistent(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.button", 24, 24)
    document = DocumentSession(project, registry)
    document.execute("选中按钮", lambda m: set_property(m, registry, key, "checked", True))
    assert document.model.nodes[key].properties["checkable"]
    document.execute("关闭选中能力", lambda m: set_property(m, registry, key, "checkable", False))
    assert not document.model.nodes[key].properties["checked"]
    document.undo()
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(document.model, registry, "恢复按钮选中"))
        assert tree.widgets[key].isCheckable() and tree.widgets[key].isChecked()
    finally:
        tree.dispose()


def test_partial_check_and_multiline_normalize(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, key = create_node(project, registry, "builtin.check_box", 24, 24)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError, match="允许半选"):
        document.execute("无效半选", lambda m: set_property(m, registry, key, "check_state", "partial"))
    document.execute("开启半选", lambda m: set_property(m, registry, key, "tristate", True))
    document.execute("设置半选", lambda m: set_property(m, registry, key, "check_state", "partial"))
    document.execute("关闭半选", lambda m: set_property(m, registry, key, "tristate", False))
    assert document.model.nodes[key].properties["check_state"] == "unchecked"
    document.undo()
    assert document.model.nodes[key].properties["check_state"] == "partial"
    prop = registry.require("builtin.text_edit").property("text")
    assert prop.normalize("甲\r\n乙\r丙\u2028丁\u2029") == "甲\n乙\n丙\n丁\n"


@pytest.mark.parametrize("kind", TYPES)
def test_leaf_widgets_reject_design_children(project: ProjectModel, registry: WidgetRegistry, kind: str) -> None:
    project, parent = create_node(project, registry, "builtin." + kind, 24, 24)
    project, child = create_node(project, registry, "builtin.label", 24, 24)
    node = replace(project.nodes[child], parent_id=parent, object_order=0, stack_order=0)
    with pytest.raises(DesignerError, match="容纳子控件"):
        validate_project(project.with_nodes({child: node}))


def test_content_editors_preserve_blank_cells_order_and_hierarchy(qt_app: QApplication, registry: WidgetRegistry) -> None:
    saved = []
    table_prop = registry.require("builtin.table_widget").property("table_data")
    dialog = ContentDialog(table_prop, {"headers": ["甲", "乙"], "rows": [["", "尾行"]]}, lambda value: saved.append(value) or True)
    try:
        dialog.add_row()
        dialog.table.setItem(1, 0, QTableWidgetItem("第二行"))
        dialog.move_row(-1)
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert saved[0]["rows"] == (("第二行", ""), ("", "尾行"))
    finally:
        dialog.deleteLater()
    prop = registry.require("builtin.tree_widget").property("tree_data")
    dialog = ContentDialog(prop, [], lambda value: saved.append(value) or True)
    try:
        dialog.add_tree_item(False)
        dialog.tree.currentItem().setText(0, "根")
        dialog.add_tree_item(True)
        dialog.tree.currentItem().setText(0, "子")
        dialog.accept()
        assert saved[-1][0]["children"][0]["text"] == "子"
    finally:
        dialog.deleteLater()


def test_dialog_keeps_draft_when_validation_or_commit_fails(qt_app: QApplication, registry: WidgetRegistry) -> None:
    prop = registry.require("builtin.list_widget").property("items")
    dialog = ContentDialog(prop, ["原文"], lambda value: False)
    try:
        dialog.table.item(0, 0).setText("草稿")
        dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted and dialog.value() == ["草稿"]
        dialog.table.item(0, 0).setText("错误\n换行")
        dialog.accept()
        assert "换行" in dialog.error_label.text()
    finally:
        dialog.deleteLater()


def test_new_preview_events_hide_user_content(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    keys = {}
    for kind in TYPES:
        project, keys[kind] = create_node(project, registry, "builtin." + kind, 24, 24)
    for kind, event in (("text_edit", "textChanged"), ("combo_box", "currentIndexChanged"),
                        ("spin_box", "valueChanged"), ("slider", "valueChanged"),
                        ("check_box", "clicked"), ("list_widget", "itemSelectionChanged")):
        project = set_event_enabled(project, registry, keys[kind], event, True)
    preview = PreviewRuntime(registry)
    spy = QSignalSpy(preview.notice)
    before = project.to_bytes()
    try:
        preview.show(compile_plan(project, registry, "预览事件"), project)
        controls = {kind: preview.tree.widgets[key] for kind, key in keys.items()}
        controls["text_edit"].setPlainText("不应记录的内容")
        controls["combo_box"].setCurrentIndex(1)
        controls["spin_box"].setValue(12)
        controls["slider"].setValue(23)
        controls["check_box"].click()
        controls["list_widget"].setCurrentRow(1)
        messages = [spy.at(i)[0] for i in range(spy.count())]
        assert all(any(name in message for message in messages) for name in ("文本改变", "值改变", "被单击", "选择改变"))
        assert all("不应记录的内容" not in message for message in messages)
        assert project.to_bytes() == before
    finally:
        preview.dispose()


def test_all_widgets_export_without_designer_dependencies(project: ProjectModel, registry: WidgetRegistry, tmp_path: Path) -> None:
    for kind in TYPES:
        project, _ = configured(project, registry, kind)
    entry = export_project(project, registry, tmp_path / "独立项目")
    code = '''import importlib.util, sys
from PySide6.QtWidgets import QApplication
application = QApplication([])
spec = importlib.util.spec_from_file_location("独立入口", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window = module.create_window(application)
assert len(window.controls) == 12
assert window.controls['text_edit_1'].toPlainText().startswith('第一行\\n')
assert window.controls['combo_box_1'].currentIndex() == 2
assert window.controls['table_widget_1'].item(1, 2).text() == '末行'
assert window.controls['tree_widget_1'].topLevelItem(0).child(0).child(0).text(0) == '孙项目'
assert not any(name in sys.modules for name in ('core', 'runtime', 'app', 'widgets'))
window.close()
print('全部新增组件独立运行通过')
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(entry)],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", TYPES)
def test_every_registered_enum_applies_on_reused_widget(project: ProjectModel, registry: WidgetRegistry,
                                                      qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    if kind == "check_box":
        project = set_property(project, registry, key, "tristate", True)
    tree = RuntimeTree(registry)
    try:
        for prop in registry.require("builtin." + kind).properties:
            if prop.value_type != "enum":
                continue
            for value, _ in prop.options:
                project = set_property(project, registry, key, prop.key, value)
                tree.apply(compile_plan(project, registry, "枚举往返"))
                if prop.qt_name and prop.key in ENUMS:
                    assert tree.widgets[key].property(prop.qt_name) == ENUMS[prop.key][value]
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind,prop,value", [
    ("text_edit", "text", "显示在视口中的文字"), ("list_widget", "items", ["内容已改变"]),
    ("table_widget", "table_data", {"headers": ["列"], "rows": [["内容已改变"]]}),
    ("tree_widget", "tree_data", [{"text": "内容已改变", "children": []}]),
])
def test_cached_viewport_changes_after_content_edit(project: ProjectModel, registry: WidgetRegistry,
                                                  qt_app: QApplication, kind: str, prop: str, value: Any) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "原内容"))
        before = tree.image(key, 1)
        project = set_property(project, registry, key, prop, value)
        tree.apply(compile_plan(project, registry, "修改内容"))
        after = tree.image(key, 1)
        assert before != after
        assert any(before.pixel(x, y) != after.pixel(x, y) for x in range(15, 120) for y in range(5, 80))
    finally:
        tree.dispose()


def test_modal_content_editor_survives_model_refresh_and_undo(project: ProjectModel, registry: WidgetRegistry,
                                                            qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.table_widget", 24, 24)
    document = DocumentSession(project, registry)
    document.select(key)
    panel = PropertyPanel()
    panel.bind(document)
    panel.show()
    editor = panel.editors["table_data"]
    checks = []

    def interact() -> None:
        dialog = qt_app.activeModalWidget()
        if not isinstance(dialog, ContentDialog):
            checks.append("未打开内容窗口")
            return
        try:
            document.execute("后台状态更新", lambda m: set_property(m, registry, m.root_id, "window_title", "更新标题"))
            qt_app.processEvents()
            assert panel.editors["table_data"] is editor
            dialog.table.setCurrentCell(0, 0)
            dialog.table.editItem(dialog.table.item(0, 0))
            field = qt_app.focusWidget()
            field.selectAll()
            QTest.keyClicks(field, "committed")
            buttons = dialog.findChild(QDialogButtonBox)
            button = next(item for item in buttons.buttons() if item.text() == "确定")
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            checks.append("通过")
        except Exception as exc:
            checks.append(str(exc))
            dialog.reject()

    QTimer.singleShot(0, interact)
    try:
        editor.choose()
        qt_app.processEvents()
        assert checks == ["通过"]
        assert document.model.nodes[key].properties["table_data"]["rows"][0][0] == "committed"
        document.undo()
        assert document.model.nodes[key].properties == project.nodes[key].properties
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
