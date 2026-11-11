"""图标选择、草稿边界、文档事务与独立导出回归。"""

from __future__ import annotations

import subprocess
import sys

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QDialog
from shiboken6 import isValid

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.errors import DesignerError
from core.storage import commit_project, load_project
from core.svg_values import validate_svg
from panels.content_editor import ContentEditor
from panels.svg_editor import SvgDialog, svg_pixmap
from resources.svg_icons import CATEGORIES, ICONS, identify_icon, icon_svg, search_icons
from runtime.builder import RuntimeTree
from tests.test_appearance import designed_window


@pytest.fixture
def dialog(registry, qt_app):
    spec = registry.require("builtin.svg_widget").property("svg_data")
    commits = []
    dialog = SvgDialog(spec, spec.default, lambda value: commits.append(value) is None)
    dialog.commits = commits
    yield dialog
    dialog.close()
    dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def select(dialog, key):
    dialog.category.setCurrentIndex(0)
    dialog.search.clear()
    for row in range(dialog.icons.count()):
        if dialog.icons.item(row).data(Qt.ItemDataRole.UserRole) == key:
            dialog.icons.setCurrentRow(row)
            return
    raise AssertionError(key)


@pytest.mark.parametrize("icon", ICONS, ids=lambda icon: icon.key)
def test_catalog_renders_valid_transparent_vectors(icon, registry, project, qt_app):
    value = icon_svg(icon.key, "#287e59", 2.4)
    validate_svg(value)
    assert identify_icon(value) == (icon.key, "#287e59", 2.4)
    renderer = QSvgRenderer(value.encode())
    assert renderer.isValid() and renderer.viewBox().getRect() == (0, 0, 24, 24)
    image = svg_pixmap(value, 48, 2).toImage()
    pixels = [image.pixelColor(x, y) for x in range(96) for y in range(96)]
    assert any(pixel.alpha() == 255 and pixel.name() == "#287e59" for pixel in pixels)
    assert image.pixelColor(0, 0).alpha() == 0
    model, key = create_node(project, registry, "builtin.svg_widget", 20, 20)
    registry.validate(set_property(model, registry, key, "svg_data", value))


def test_search_categories_and_aliases():
    assert len(ICONS) == len({icon.key for icon in ICONS}) == 64
    assert len(CATEGORIES) == 8
    for query in ("搜索", "SEARCH", "放大镜", "  search   导航 "):
        assert [icon.key for icon in search_icons(query)] == ["search"]
    assert "mail" in {icon.key for icon in search_icons("私信")}
    assert search_icons("search", "媒体") == ()
    for category in CATEGORIES:
        assert len(search_icons(category=category)) == 8


@pytest.mark.parametrize("kwargs", [{"color": "red"}, {"color": '#fff\"/>'},
                                    {"stroke_width": float("nan")}, {"stroke_width": 0}, {"stroke_width": 5}])
def test_invalid_generation_parameters(kwargs):
    with pytest.raises(ValueError):
        icon_svg("home", **kwargs)


def test_custom_source_is_not_misidentified():
    assert identify_icon(icon_svg("home").replace("M3 11", "M4 11")) is None
    assert identify_icon("<svg/>") is None
    assert identify_icon('<!DOCTYPE svg [<!ENTITY x "x">]><svg/>') is None


def test_svg_validation_rejects_unpaired_surrogates():
    with pytest.raises(DesignerError, match="有效的 XML"):
        validate_svg("<svg>\ud800</svg>")


@pytest.mark.parametrize("data", ["<html/>", "<svg>", "<!DOCTYPE svg><svg/>",
                                 '<!ENTITY x "x"><svg/>', "<svg>" + "x" * 100_000 + "</svg>"],
                         ids=["wrong-root", "unclosed", "doctype", "entity", "too-long"])
def test_bad_source_cannot_apply_or_preview(dialog, data):
    dialog.tabs.setCurrentIndex(1)
    dialog.source.setPlainText(data)
    dialog.update_preview()
    dialog.accept()
    assert not dialog.commits and dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.error_label.text() and not dialog.apply_button.isEnabled()
    assert all(preview.pixmap().isNull() for preview in dialog.previews)
    with pytest.raises(DesignerError):
        validate_svg(data)


def test_selection_color_stroke_and_reopen(dialog, registry, qt_app):
    original = dialog.value()
    assert dialog.icons.count() == 64 and not dialog.color.isEnabled()
    assert dialog.value() == original and not dialog.commits
    select(dialog, "search")
    dialog.color.line_edit.setText("#287E59")
    dialog.stroke_width.setValue(2.4)
    expected = icon_svg("search", "#287e59", 2.4)
    assert dialog.value() == expected and not dialog.commits
    dialog.accept()
    assert dialog.commits == [expected]
    reopened = SvgDialog(dialog.spec, expected, lambda value: True)
    try:
        assert reopened.color.line_edit.text() == "#287e59"
        assert reopened.stroke_width.value() == 2.4
        assert reopened.value() == expected
        assert reopened.icons.selectedItems()[0].data(Qt.ItemDataRole.UserRole) == "search"
    finally:
        reopened.deleteLater()


def test_filter_keeps_draft_and_explains_no_results(dialog):
    select(dialog, "home")
    value = dialog.value()
    dialog.search.setText("no-such-icon")
    assert dialog.icons.count() == 0 and "没有匹配" in dialog.count_label.text()
    assert dialog.value() == value
    dialog.search.clear()
    dialog.category.setCurrentIndex(dialog.category.findData("媒体"))
    assert dialog.icons.count() == 8
    assert dialog.value() == value
    dialog.reject()
    assert not dialog.commits


def test_switching_tabs_never_overwrites_custom_draft(dialog):
    select(dialog, "home")
    dialog.tabs.setCurrentIndex(1)
    draft = dialog.value().replace("M3 11", "M4 11")
    dialog.source.setPlainText(draft)
    dialog.tabs.setCurrentIndex(0)
    dialog.tabs.setCurrentIndex(1)
    assert dialog.value() == draft
    assert not dialog.color.isEnabled() and not dialog.stroke_width.isEnabled()
    assert not dialog.icons.selectedItems()
    dialog.accept()
    assert dialog.commits == [draft]


def test_invalid_color_and_failed_commit_keep_draft(dialog):
    select(dialog, "home")
    dialog.color.line_edit.setText("invalid")
    dialog.accept()
    assert not dialog.commits and not dialog.apply_button.isEnabled()
    dialog.color.line_edit.setText("#123456")
    expected = dialog.value()
    assert dialog.apply_button.isEnabled()
    dialog.commit = lambda value: False
    dialog.accept()
    assert dialog.value() == expected and "编辑内容已保留" in dialog.error_label.text()
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_property_picker_is_one_undoable_change(designed_window, qt_app, monkeypatch, tmp_path):
    window = designed_window
    document, panel = window.document, window.properties
    key = window.page.canvas.create_component("builtin.svg_widget", QPointF(30, 30))
    qt_app.processEvents()
    editor = panel.editors["svg_data"]
    assert isinstance(editor, ContentEditor) and editor.button.text() == "图标…"
    old_value, cursor = document.model.nodes[key].properties["svg_data"], document.history.cursor
    dialogs = []

    def choose(dialog):
        dialogs.append(dialog)
        assert editor.choosing
        select(dialog, "home")
        dialog.color.line_edit.setText("#287e59")
        dialog.accept()
        panel.refresh()
        assert panel.editors["svg_data"] is editor
        return dialog.result()

    monkeypatch.setattr(SvgDialog, "exec", choose)
    editor.button.click()
    qt_app.processEvents()
    expected = icon_svg("home", "#287e59")
    assert document.model.nodes[key].properties["svg_data"] == expected
    assert document.history.cursor == cursor + 1
    assert window.page.canvas.renderer.tree.widgets[key].native.renderer().isValid()
    document.undo()
    qt_app.processEvents()
    assert document.model.nodes[key].properties["svg_data"] == old_value
    document.redo()
    qt_app.processEvents()
    assert document.model.nodes[key].properties["svg_data"] == expected
    path = tmp_path / "icons.uipro"
    commit_project(path, document.model, expected_token=None)
    assert load_project(path).model.nodes[key].properties["svg_data"] == expected
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert all(not isValid(dialog) for dialog in dialogs)


def test_cancelled_property_picker_does_not_dirty_document(designed_window, qt_app, monkeypatch):
    window = designed_window
    window.page.canvas.create_component("builtin.svg_widget", QPointF(30, 30))
    qt_app.processEvents()
    model, cursor = window.document.model, window.document.history.cursor

    def cancel(dialog):
        select(dialog, "user")
        dialog.reject()
        return dialog.result()

    monkeypatch.setattr(SvgDialog, "exec", cancel)
    window.properties.editors["svg_data"].button.click()
    qt_app.processEvents()
    assert window.document.model == model and window.document.history.cursor == cursor


def test_saved_icon_previews_and_exports_without_catalog(project, registry, qt_app, tmp_path):
    model, key = create_node(project, registry, "builtin.svg_widget", 20, 20)
    value = icon_svg("search", "#287e59", 2.4)
    model = set_property(model, registry, key, "svg_data", value)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(model, registry, "图标预览"))
        assert tree.widgets[key].native.renderer().isValid()
        assert tree.widgets[key].native.renderer().viewBox().width() == 24
    finally:
        tree.dispose()
    entry = export_project(model, registry, tmp_path / "standalone")
    probe = tmp_path / "probe.py"
    probe.write_text('''import importlib.util, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt
app = QApplication([])
spec = importlib.util.spec_from_file_location("exported", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window = module.create_window(app)
try:
    renderer = window.controls[sys.argv[2]].native.renderer()
    assert renderer.isValid() and renderer.viewBox().width() == 24
    image = QImage(96, 96, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    assert any(image.pixelColor(x,y).name() == "#287e59" and image.pixelColor(x,y).alpha() == 255
               for x in range(96) for y in range(96))
    assert not any(name == "resources.svg_icons" or name == "panels.svg_editor" for name in sys.modules)
    print("standalone svg passed")
finally:
    window.close()
    window.deleteLater()
    app.processEvents()
''', encoding="utf-8")
    result = subprocess.run([sys.executable, "-I", str(probe), str(entry), model.nodes[key].code_name],
                            cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "standalone svg passed" in result.stdout
