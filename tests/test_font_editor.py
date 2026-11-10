"""字体与字号选择的实际输入、继承、撤销及保存导出一致性。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from PySide6.QtCore import QPoint, QPointF, QStandardPaths, Qt
from PySide6.QtGui import QFontDatabase, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox

from app.main_window import MainWindow
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import set_property
from core.storage import commit_project, load_project
from panels.font_editor import FontFamilyEditor, FontSizeEditor
from runtime.builder import RuntimeTree
from tests.test_clipboard import add_button, window
from tests.test_codegen import load_export


@pytest.fixture(autouse=True)
def installed_test_font(qt_app: QApplication) -> Iterator[None]:
    """Windows 离屏插件不枚举系统字体，显式加载本机字库验证真实字体。"""
    identifier = -1
    if not any(QFontDatabase.families()):
        for directory in QStandardPaths.standardLocations(QStandardPaths.StandardLocation.FontsLocation):
            for filename in ("msyh.ttc", "simsun.ttc", "arial.ttf"):
                path = Path(directory) / filename
                if path.is_file():
                    identifier = QFontDatabase.addApplicationFont(str(path))
                    if identifier >= 0:
                        break
            if identifier >= 0:
                break
    if not any(QFontDatabase.families()):
        pytest.skip("测试环境没有可用字库，字体选择由真实桌面检查验证。")
    try:
        yield
    finally:
        if identifier >= 0:
            QFontDatabase.removeApplicationFont(identifier)


def choose(editor: QComboBox, value: str | int, qt_app: QApplication) -> None:
    index = editor.findData(value)
    assert index >= 0
    editor.setFocus()
    editor.showPopup()
    qt_app.processEvents()
    item = editor.model().index(index, editor.modelColumn())
    editor.view().scrollTo(item)
    QTest.mouseClick(editor.view().viewport(), Qt.MouseButton.LeftButton,
                     pos=editor.view().visualRect(item).center())
    qt_app.processEvents()


def test_fonts_are_installed_choices_and_sizes_cover_existing_values(qt_app: QApplication) -> None:
    family = FontFamilyEditor("")
    size = FontSizeEditor(13, 0, 96)
    try:
        assert not family.isEditable() and family.lineEdit() is None
        assert not size.isEditable() and size.lineEdit() is None
        assert family.currentData() == "" and family.currentText() == "继承默认"
        assert set(QFontDatabase.families()) <= {family.itemData(i) for i in range(family.count())}
        assert set(range(97)) <= {size.itemData(i) for i in range(size.count())}
        assert size.currentData() == 13 and size.currentText() == "13 磅"
        if family.count() > 1:
            assert family.itemData(1, Qt.ItemDataRole.FontRole).family() == family.itemData(1)
    finally:
        family.deleteLater()
        size.deleteLater()


@pytest.mark.parametrize("kind", ["builtin.button", "builtin.label", "builtin.line_edit", "builtin.group_box"])
def test_widget_font_properties_use_selection_editors(window: MainWindow, qt_app: QApplication, kind: str) -> None:
    key = window.page.canvas.create_component(kind, QPointF(40, 40))
    qt_app.processEvents()
    assert key == window.document.selected_id
    assert isinstance(window.properties.editors["font_family"], FontFamilyEditor)
    assert isinstance(window.properties.editors["font_size"], FontSizeEditor)
    window.document.select(window.document.model.root_id)
    qt_app.processEvents()
    assert isinstance(window.properties.editors["font_family"], FontFamilyEditor)
    assert isinstance(window.properties.editors["font_size"], FontSizeEditor)


def test_mouse_selection_updates_canvas_and_undo_redo(window: MainWindow, qt_app: QApplication) -> None:
    key = add_button(window)
    document = window.document
    original = document.model
    cursor = document.history.cursor
    family = window.properties.editors["font_family"]
    selected_family = family.itemData(1)
    choose(family, selected_family, qt_app)
    assert document.model.nodes[key].properties["font_family"] == selected_family
    assert window.page.canvas.renderer.tree.widgets[key].font().family() == selected_family
    assert document.history.cursor == cursor + 1
    choose(window.properties.editors["font_size"], 18, qt_app)
    assert window.page.canvas.renderer.tree.widgets[key].font().pointSize() == 18
    assert document.history.cursor == cursor + 2
    document.undo()
    document.undo()
    qt_app.processEvents()
    assert document.model == original
    assert window.properties.editors["font_family"].currentData() == ""
    assert window.properties.editors["font_size"].currentData() == 0
    document.redo()
    document.redo()
    qt_app.processEvents()
    assert window.properties.editors["font_family"].currentData() == selected_family
    assert window.properties.editors["font_size"].currentData() == 18


def test_inherit_default_keeps_parent_font_live(window: MainWindow, qt_app: QApplication) -> None:
    key = add_button(window)
    document = window.document
    parent_family = next(family for family in QFontDatabase.families() if family)
    for prop, value in (("font_family", parent_family), ("font_size", 16)):
        document.execute("设置父窗口字体", lambda model, p=prop, v=value:
                         set_property(model, window.registry, model.root_id, p, v))
    qt_app.processEvents()
    choose(window.properties.editors["font_size"], 24, qt_app)
    choose(window.properties.editors["font_size"], 0, qt_app)
    assert document.model.nodes[key].properties["font_size"] == 0
    assert window.page.canvas.renderer.tree.widgets[key].font().pointSize() == 16
    family = window.properties.editors["font_family"]
    choose(family, family.itemData(1), qt_app)
    choose(window.properties.editors["font_family"], "", qt_app)
    assert window.page.canvas.renderer.tree.widgets[key].font().family() == parent_family
    document.execute("改变父窗口字号", lambda model: set_property(model, window.registry, model.root_id, "font_size", 20))
    assert window.page.canvas.renderer.tree.widgets[key].font().pointSize() == 20


def test_empty_font_family_does_not_duplicate_inherited_choice(qt_app, monkeypatch):
    family = next(value for value in QFontDatabase.families() if value)
    monkeypatch.setattr(QFontDatabase, "families", lambda *args: ["", family])
    editor = FontFamilyEditor("")
    try:
        assert editor.count() == 2
        assert [editor.itemData(i) for i in range(editor.count())] == ["", family]
    finally:
        editor.deleteLater()


@pytest.mark.parametrize("prop", ["font_family", "font_size"])
def test_open_popup_survives_refresh_and_cancel_does_not_commit(window: MainWindow, qt_app: QApplication, prop: str) -> None:
    add_button(window)
    editor = window.properties.editors[prop]
    original = window.document.model
    editor.showPopup()
    qt_app.processEvents()
    assert editor.choosing
    window.properties.queue_refresh()
    qt_app.processEvents()
    assert window.properties.editors[prop] is editor and editor.view().isVisible()
    QTest.keyClick(editor.view(), Qt.Key.Key_Down)
    QTest.keyClick(editor.view(), Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert window.document.model == original
    assert not window.properties.editors[prop].choosing


def test_closed_font_choices_ignore_wheel_and_read_only_disables_selection(window: MainWindow, qt_app: QApplication) -> None:
    add_button(window)
    original = window.document.model
    for prop in ("font_family", "font_size"):
        editor = window.properties.editors[prop]
        editor.setFocus()
        event = QWheelEvent(QPointF(10, 10), QPointF(editor.mapToGlobal(QPoint(10, 10))), QPoint(), QPoint(0, -120),
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        value = editor.currentData()
        QApplication.sendEvent(editor, event)
        assert editor.currentData() == value
    assert window.document.model == original
    window.document.read_only = True
    window.properties.refresh()
    assert not window.properties.editors["font_family"].isEnabled()
    assert not window.properties.editors["font_size"].isEnabled()


def test_missing_font_is_preserved_until_user_selects(window: MainWindow, qt_app: QApplication, tmp_path: Path) -> None:
    key = add_button(window)
    missing = "项目专用字体（测试未安装）"
    document = window.document
    document.execute("载入外部字体设置", lambda model: set_property(model, window.registry, key, "font_family", missing))
    qt_app.processEvents()
    editor = window.properties.editors["font_family"]
    assert editor.currentData() == missing and "本机未找到" in editor.currentText()
    snapshot = document.model
    assert window.properties.commit_pending() and document.model == snapshot
    path = tmp_path / "保留字体.uipro"
    commit_project(path, snapshot, expected_token=None)
    assert load_project(path).model.nodes[key].properties["font_family"] == missing
    choose(editor, "", qt_app)
    assert document.model.nodes[key].properties["font_family"] == ""
    document.undo()
    qt_app.processEvents()
    assert window.properties.editors["font_family"].currentData() == missing


def test_selected_font_matches_preview_save_and_export(window: MainWindow, qt_app: QApplication, tmp_path: Path) -> None:
    key = add_button(window)
    family = window.properties.editors["font_family"]
    selected = family.itemData(1)
    choose(family, selected, qt_app)
    choose(window.properties.editors["font_size"], 17, qt_app)
    project = window.document.model
    path = tmp_path / "字体选择.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    runtime = RuntimeTree(window.registry, design_mode=False)
    exported = load_export(export_project(loaded, window.registry, tmp_path / "导出字体"), qt_app)
    try:
        runtime.apply(compile_plan(loaded, window.registry, "字体运行检查"))
        designed = window.page.canvas.renderer.tree.widgets[key]
        assert designed.font().family() == selected and designed.font().pointSize() == 17
        assert runtime.widgets[key].font() == designed.font()
        assert exported.controls[project.nodes[key].code_name].font() == designed.font()
    finally:
        runtime.dispose()
        exported.close()
        exported.deleteLater()


def test_font_database_failure_keeps_saved_value(qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: object) -> list[str]:
        raise RuntimeError("模拟字体服务暂时不可用")

    monkeypatch.setattr(QFontDatabase, "families", unavailable)
    editor = FontFamilyEditor("项目字体")
    try:
        assert editor.currentData() == "项目字体"
        assert editor.findData("") == 0
        assert "暂时无法读取" in editor.toolTip()
    finally:
        editor.deleteLater()
