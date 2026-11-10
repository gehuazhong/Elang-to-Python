"""多列表格内容的列宽草稿、保存撤销、原生显示及独立导出回归。"""

from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QInputDialog, QTableWidget, QTableWidgetItem

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, decode_fragment, encode_fragment, paste_fragment
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import thaw
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from panels.content_editor import ContentDialog
from runtime.builder import RuntimeTree
from runtime.preview import PreviewRuntime
from tests.test_appearance import designed_window
from tests.test_codegen import load_export


KINDS = ("table_widget", "super_list")
DATA = {"headers": ["ID", "名称", "说明"], "rows": [["1", "项目一", "这里是比较长的项目说明"], ["2", "项目二", ""]],
        "column_widths": [56, 160, 280]}


def widths(widget):
    return tuple(widget.columnWidth(column) for column in range(widget.columnCount()))


def header(widget):
    return widget.horizontalHeader() if isinstance(widget, QTableWidget) else widget.header()


@pytest.mark.parametrize("kind", KINDS)
def test_widths_match_canvas_preview_export_and_survive_save_copy(project, registry, qt_app, tmp_path, kind):
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    project = set_property(project, registry, key, "table_data", DATA)
    project = set_property(project, registry, key, "geometry.width", 650)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    preview = PreviewRuntime(registry)
    path = tmp_path / "自定义列宽.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    fragment = decode_fragment(encode_fragment(copy_fragment(loaded, registry, key)), registry)
    copied, copied_key = paste_fragment(loaded, registry, fragment)
    assert copied.nodes[copied_key].properties["table_data"]["column_widths"] == (56, 160, 280)
    generated = load_export(export_project(loaded, registry, tmp_path / "导出"), qt_app)
    try:
        preview.show(compile_plan(loaded, registry, "列宽预览"), loaded)
        generated.show()
        qt_app.processEvents()
        for widget in (canvas.renderer.tree.widgets[key], preview.tree.widgets[key], generated.controls[project.nodes[key].code_name]):
            assert widths(widget) == (56, 160, 280)
            assert not header(widget).stretchLastSection()
        before = canvas.renderer.tree.image(key, 1)
        changed = {**DATA, "column_widths": [80, 160, 320]}
        document.execute("修改各列宽度", lambda model: set_property(model, registry, key, "table_data", changed))
        assert widths(canvas.renderer.tree.widgets[key]) == (80, 160, 320)
        assert canvas.renderer.tree.image(key, 1) != before
        document.undo()
        assert widths(canvas.renderer.tree.widgets[key]) == (56, 160, 280)
        document.redo()
        assert widths(canvas.renderer.tree.widgets[key]) == (80, 160, 320)
        preview.tree.widgets[key].setColumnWidth(0, 99)
        assert loaded.to_bytes() == project.to_bytes()
        widget = generated.controls[project.nodes[key].code_name]
        widget.resize(160, widget.height())
        qt_app.processEvents()
        assert widths(widget) == (56, 160, 280)
        assert widget.horizontalScrollBar().maximum() > 0
    finally:
        canvas.dispose()
        canvas.close()
        preview.dispose()
        generated.close()
        generated.deleteLater()


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("stretch", [False, True])
def test_default_width_only_changes_unspecified_columns_and_last_fill(project, registry, qt_app, kind, stretch):
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    project = set_property(project, registry, key, "geometry.width", 650)
    project = set_property(project, registry, key, "stretch_last_section", stretch)
    project = set_property(project, registry, key, "table_data", {**DATA, "column_widths": [56, 0, 0]})
    tree = RuntimeTree(registry, design_mode=False)
    try:
        for default in (120, 180):
            project = set_property(project, registry, key, "column_width", default)
            tree.apply(compile_plan(project, registry, str(default)))
            tree.root.show()
            qt_app.processEvents()
            widget = tree.widgets[key]
            assert widths(widget)[:2] == (56, default)
            assert header(widget).stretchLastSection() == stretch
            assert widget.columnWidth(2) > default if stretch else widget.columnWidth(2) == default
        project = set_property(project, registry, key, "table_data", DATA)
        tree.apply(compile_plan(project, registry, "固定末列"))
        qt_app.processEvents()
        assert widths(widget) == (56, 160, 280)
        project = set_property(project, registry, key, "table_data", {**DATA, "column_widths": [0, 0, 0]})
        tree.apply(compile_plan(project, registry, "恢复默认"))
        qt_app.processEvents()
        assert widths(widget)[:2] == (180, 180)
        assert header(widget).stretchLastSection() == stretch
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", KINDS)
def test_old_projects_without_widths_keep_default_and_roundtrip_unchanged(project, registry, qt_app, kind):
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    node = project.nodes[key]
    old = {name: thaw(value) for name, value in node.properties.items() if name not in {"stretch_last_section", "column_width"}}
    if kind == "super_list":
        old["column_width"] = 137
    project = project.with_nodes({key: replace(node, properties=node.properties.__class__(old))})
    registry.validate(project)
    tree = RuntimeTree(registry)
    try:
        before = project.to_bytes()
        tree.apply(compile_plan(project, registry, "旧项目"))
        assert tree.widgets[key].columnWidth(0) == (137 if kind == "super_list" else 100)
        assert header(tree.widgets[key]).stretchLastSection()
        assert project.to_bytes() == before
    finally:
        tree.dispose()


@pytest.mark.parametrize("invalid", [[56], [56, 160, 280, 10], [True, 160, 280], [-1, 160, 280],
                                     [2001, 160, 280], [56.5, 160, 280], ["56", 160, 280], None, {}])
def test_invalid_widths_rejected_without_document_or_export_changes(project, registry, tmp_path, invalid):
    project, key = create_node(project, registry, "builtin.table_widget", 24, 24)
    project = set_property(project, registry, key, "table_data", DATA)
    document = DocumentSession(project, registry)
    export_project(project, registry, tmp_path)
    pointer = (tmp_path / "current.json").read_bytes()
    with pytest.raises(DesignerError):
        document.execute("无效列宽", lambda model: set_property(model, registry, key, "table_data", {**DATA, "column_widths": invalid}))
    assert document.model == project and document.history.cursor == 0
    assert (tmp_path / "current.json").read_bytes() == pointer


@pytest.mark.parametrize("kind", KINDS)
def test_content_dialog_edit_drag_fit_add_remove_and_reset(qt_app, registry, kind, monkeypatch):
    prop = registry.require("builtin." + kind).property("table_data")
    saved = []
    dialog = ContentDialog(prop, DATA, lambda value: saved.append(value) or True, column_default=140)
    try:
        dialog.show()
        qt_app.processEvents()
        assert dialog.value()["column_widths"] == [56, 160, 280]
        assert widths(dialog.table) == (56, 160, 280)
        dialog.column_width.setValue(64)
        assert dialog.table.columnWidth(0) == 64
        h = dialog.table.horizontalHeader()
        start = QPoint(h.sectionViewportPosition(0) + h.sectionSize(0) - 1, h.height() // 2)
        QTest.mousePress(h.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(h.viewport(), start + QPoint(24, 0))
        QTest.mouseRelease(h.viewport(), Qt.MouseButton.LeftButton, pos=start + QPoint(24, 0))
        assert dialog.table.columnWidth(0) == 88
        assert dialog.column_width.value() == dialog.column_widths[0] == 88
        dialog.column_choice.setCurrentIndex(2)
        dialog.fit_column.click()
        assert dialog.column_widths[2] == dialog.table.columnWidth(2)
        assert dialog.column_widths[2] != 280
        dialog.column_choice.setCurrentIndex(1)
        dialog.remove_column()
        assert dialog.value()["headers"] == ["ID", "说明"]
        assert dialog.column_widths == [88, dialog.table.columnWidth(1)]
        dialog.add_column()
        assert dialog.column_widths[-1] == 0 and dialog.table.columnWidth(2) == 140
        monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("新增说明", True))
        dialog.rename_column(2)
        assert "新增说明" in dialog.column_choice.currentText()
        dialog.table.setCurrentCell(0, 0)
        dialog.move_row(1)
        assert dialog.column_widths[0] == 88
        dialog.column_choice.setCurrentIndex(0)
        dialog.reset_column.click()
        assert dialog.column_widths[0] == 0 and dialog.table.columnWidth(0) == 140
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert saved[0]["column_widths"][0] == 0
    finally:
        dialog.close()
        dialog.deleteLater()


def test_empty_table_can_set_width_without_rows_and_rebuild_columns(qt_app, registry):
    prop = registry.require("builtin.table_widget").property("table_data")
    dialog = ContentDialog(prop, {"headers": ["ID", "说明"], "rows": []}, lambda value: True)
    try:
        dialog.column_width.setValue(52)
        dialog.column_choice.setCurrentIndex(1)
        dialog.remove_column()
        assert dialog.value() == {"headers": ["ID"], "rows": [], "column_widths": [52]}
        dialog.remove_column()
        assert dialog.value() == {"headers": [], "rows": []}
        assert not dialog.column_width.isEnabled()
        dialog.add_column()
        assert dialog.column_width.isEnabled() and dialog.column_width.value() == 0
        assert dialog.value() == {"headers": ["列1"], "rows": []}
    finally:
        dialog.deleteLater()


def test_content_dialog_cancel_is_clean_and_cell_edit_keeps_widths(qt_app, registry):
    prop = registry.require("builtin.table_widget").property("table_data")
    saved = []
    dialog = ContentDialog(prop, DATA, lambda value: saved.append(value) or True)
    try:
        dialog.column_width.setValue(72)
        dialog.reject()
        assert not saved and DATA["column_widths"] == [56, 160, 280]
    finally:
        dialog.deleteLater()
    dialog = ContentDialog(prop, DATA, lambda value: saved.append(value) or True)
    try:
        dialog.show()
        qt_app.processEvents()
        dialog.table.item(0, 1).setText("新名称")
        dialog.accept()
        assert saved[0]["column_widths"] == (56, 160, 280)
        assert saved[0]["rows"][0][1] == "新名称"
    finally:
        dialog.deleteLater()


def test_property_editor_uses_component_default_and_one_undo_command(designed_window, qt_app):
    window = designed_window
    document, panel = window.document, window.properties
    project, key = create_node(document.model, window.registry, "builtin.super_list", 24, 24)
    project = set_property(project, window.registry, key, "column_width", 144)
    document.execute("准备多列组件", lambda model: project)
    document.select(key)
    panel.refresh()
    cursor, original = document.history.cursor, document.model
    failures = []
    def edit():
        dialog = QApplication.activeModalWidget()
        try:
            assert isinstance(dialog, ContentDialog)
            assert dialog.column_default == 144
            assert widths(dialog.table) == (144, 144, 144)
            dialog.column_width.setValue(56)
            dialog.column_choice.setCurrentIndex(2)
            dialog.column_width.setValue(256)
            dialog.accept()
        except Exception as exc:
            failures.append(exc)
            dialog.reject()
    QTimer.singleShot(30, edit)
    panel.editors["table_data"].button.click()
    if failures:
        raise failures[0]
    assert document.history.cursor == cursor + 1
    assert widths(window.page.canvas.renderer.tree.widgets[key]) == (56, 144, 256)
    document.undo()
    assert document.model == original


def test_custom_widths_run_in_isolated_export_with_preserved_business(project, registry, tmp_path):
    for kind in KINDS:
        project, key = create_node(project, registry, "builtin." + kind, 24, 24)
        project = set_property(project, registry, key, "table_data", DATA)
    entry = export_project(project, registry, tmp_path)
    handlers = entry.with_name("handlers.py")
    business = "def connect_events(window):\n    window.setProperty('business_loaded', True)\n"
    handlers.write_text(business, encoding="utf-8")
    export_project(project, registry, tmp_path)
    assert handlers.read_text(encoding="utf-8") == business
    code = '''import importlib.util, pathlib, sys
from PySide6.QtWidgets import QApplication
spec = importlib.util.spec_from_file_location("entry", pathlib.Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = QApplication([])
window = module.create_window(app)
window.show()
app.processEvents()
for name in ("table_widget_1", "super_list_1"):
    widget = window.controls[name]
    assert tuple(widget.columnWidth(i) for i in range(3)) == (56, 160, 280)
assert window.property("business_loaded") is True
assert not any(name in sys.modules for name in ("core", "runtime", "app"))
window.close()
print("独立列宽通过")
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(entry)],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "独立列宽通过" in result.stdout
