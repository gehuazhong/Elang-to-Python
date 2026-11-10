"""属性滚轮、下拉弹层和未提交输入的交互回归。"""

from __future__ import annotations

from dataclasses import replace
import gc
from typing import Any
import weakref

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QColorDialog, QComboBox, QStyle, QStyleOptionSpinBox, QToolBar, QWidget

from app.main_window import MainWindow
from core.commands.nodes import create_node, set_property
from panels.object_tree import ObjectTree
from panels.properties import PropertyPanel
from tests.test_clipboard import window
from tests.test_font_editor import installed_test_font


@pytest.mark.parametrize("panel_type", [PropertyPanel, ObjectTree])
def test_cancelling_refresh_releases_python_panel(qt_app: QApplication, panel_type: type[QWidget]) -> None:
    def dispose_pending() -> weakref.ReferenceType[QWidget]:
        panel = panel_type()
        reference = weakref.ref(panel)
        panel.queue_refresh()
        panel.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qt_app.processEvents()
        return reference

    reference = dispose_pending()
    gc.collect()
    assert reference() is None, "原生面板已销毁，但取消的延迟刷新仍保留 Python 面板对象。"


def wheel(widget: QWidget, delta: int = -120, *, pixels: bool = False) -> None:
    position = widget.rect().center()
    event = QWheelEvent(QPointF(position), QPointF(widget.mapToGlobal(position)),
                        QPoint(0, delta) if pixels else QPoint(),
                        QPoint() if pixels else QPoint(0, delta),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                        Qt.ScrollPhase.ScrollUpdate if pixels else Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(widget, event)


def value(editor: QWidget) -> Any:
    return editor.currentData() if isinstance(editor, QComboBox) else editor.value()


@pytest.mark.parametrize("focused", [False, True])
@pytest.mark.parametrize("kind,prop", [
    (None, "geometry.width"), (None, "border_style"),
    ("button", "parent_id"), ("button", "font_size"),
    ("line_edit", "max_length"), ("double_spin_box", "value"),
    ("date_edit", "value"), ("time_edit", "value"), ("datetime_edit", "value"),
    ("tab_widget", "current_index"),
])
def test_wheel_never_changes_property(window: MainWindow, qt_app: QApplication,
                                     kind: str | None, prop: str, focused: bool) -> None:
    if kind:
        window.page.canvas.create_component("builtin." + kind, QPointF(40, 40))
    qt_app.processEvents()
    panel = window.properties
    editor = panel.editors[prop]
    panel.tree.expandAll()
    editor.setFocus() if focused else panel.search.setFocus()
    original, cursor, expected = window.document.model, window.document.history.cursor, value(editor)
    for delta in (-120, 120, -240):
        wheel(editor, delta)
        if isinstance(editor, QAbstractSpinBox):
            wheel(editor.lineEdit(), delta)
        assert value(editor) == expected, "滚轮误改了属性编辑器的值。"
    wheel(editor, -30, pixels=True)
    assert panel.commit_pending()
    panel.search.setFocus()
    qt_app.processEvents()
    assert window.document.model == original
    assert window.document.history.cursor == cursor


def test_wheel_over_editor_scrolls_property_tree(window: MainWindow, qt_app: QApplication) -> None:
    panel = window.properties
    panel.tree.expandAll()
    qt_app.processEvents()
    bar = panel.tree.verticalScrollBar()
    assert bar.maximum() > 0
    for prop in ("geometry.width", "border_style", "font_size"):
        bar.setValue(0)
        wheel(panel.editors[prop])
        assert bar.value() > 0, "属性值未改变，但滚轮也不能卡在编辑器上。"


@pytest.mark.parametrize("prop", ["name", "geometry.width"])
def test_window_wheel_dispatch_scrolls_once_without_edit(window: MainWindow, qt_app: QApplication, prop: str) -> None:
    panel = window.properties
    panel.tree.expandAll()
    qt_app.processEvents()
    editor = panel.editors[prop]
    bar = panel.tree.verticalScrollBar()
    bar.setValue(0)
    editor.setFocus()
    original = window.document.model
    position = editor.mapTo(window, editor.rect().center())
    QTest.wheelEvent(window.windowHandle(), position, QPoint(0, -120))
    qt_app.processEvents()
    actual = bar.value()
    assert actual > 0, "通过真实窗口分派的滚轮未能滚动属性区。"
    assert panel.commit_pending() and window.document.model == original
    bar.setValue(0)
    wheel(panel.tree.viewport())
    assert bar.value() == actual, "一个滚轮事件不能重复滚动两次。"


@pytest.mark.parametrize("prop", ["border_style", "font_size"])
def test_open_choice_survives_refresh_then_closes_cleanly(window: MainWindow, qt_app: QApplication, prop: str) -> None:
    panel = window.properties
    editor = panel.editors[prop]
    editor.showPopup()
    qt_app.processEvents()
    assert editor.view().isVisible()
    original = window.document.model
    panel.queue_refresh()
    qt_app.processEvents()
    assert panel.editors[prop] is editor and editor.view().isVisible(), "刷新中断了正在选择的弹层。"
    QTest.keyClick(editor.view(), Qt.Key.Key_Down)
    QTest.keyClick(editor.view(), Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert window.document.model == original
    assert not panel.editors[prop].view().isVisible()


def test_toolbar_zoom_does_not_change_on_wheel(window: MainWindow, qt_app: QApplication) -> None:
    original = window.page.canvas.zoom
    editor = window.zoom_combo
    index = editor.currentIndex()
    editor.setFocus()
    wheel(editor)
    qt_app.processEvents()
    assert editor.currentIndex() == index
    assert window.page.canvas.zoom == original


def test_toolbar_zoom_stays_inside_compact_window(window: MainWindow, qt_app: QApplication) -> None:
    window.resize(960, 620)
    qt_app.processEvents()
    toolbar = window.findChild(QToolBar, "mainToolbar")
    assert window.zoom_combo.isVisible()
    assert toolbar.rect().contains(window.zoom_combo.geometry())


@pytest.mark.parametrize("operation", ["keyboard", "button"])
def test_explicit_spin_change_survives_refresh_and_commits_once(window: MainWindow, qt_app: QApplication,
                                                               operation: str) -> None:
    panel = window.properties
    editor = panel.editors["geometry.width"]
    editor.setFocus()
    before, cursor = editor.value(), window.document.history.cursor
    if operation == "keyboard":
        QTest.keyClick(editor, Qt.Key.Key_Up)
    else:
        option = QStyleOptionSpinBox()
        editor.initStyleOption(option)
        button = editor.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option,
                                               QStyle.SubControl.SC_SpinBoxUp, editor)
        QTest.mouseClick(editor, Qt.MouseButton.LeftButton, pos=button.center())
    assert editor.value() == before + 1
    panel.queue_refresh()
    qt_app.processEvents()
    assert panel.editors["geometry.width"].value() == before + 1, "未提交的步进修改被后台刷新覆盖。"
    assert panel.commit_pending()
    qt_app.processEvents()
    root = window.document.model.nodes[window.document.model.root_id]
    assert root.geometry.width == before + 1
    assert window.document.history.cursor == cursor + 1
    window.document.undo()
    qt_app.processEvents()
    assert panel.editors["geometry.width"].value() == before


def test_open_choice_wheel_scrolls_options_without_commit(window: MainWindow, qt_app: QApplication) -> None:
    editor = window.properties.editors["font_size"]
    editor.showPopup()
    qt_app.processEvents()
    expected, original = editor.currentData(), window.document.model
    bar = editor.view().verticalScrollBar()
    bar.setValue(0)
    wheel(editor.view().viewport(), -480)
    qt_app.processEvents()
    assert bar.value() > 0
    assert editor.currentData() == expected and window.document.model == original
    QTest.keyClick(editor.view(), Qt.Key.Key_Escape)


def test_closed_choice_keyboard_remains_usable(window: MainWindow, qt_app: QApplication) -> None:
    editor = window.properties.editors["border_style"]
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_Down)
    qt_app.processEvents()
    assert window.document.model.nodes[window.document.model.root_id].properties["border_style"] == "fixed"


def test_noop_text_commit_releases_deferred_refresh(window: MainWindow, qt_app: QApplication) -> None:
    panel, document = window.properties, window.document
    editor = panel.editors["name"]
    editor.setFocus()
    editor.setCursorPosition(len(editor.text()))
    editor.insert(" ")
    document.execute("后台修改标题", lambda model: set_property(model, window.registry, model.root_id,
                                                               "window_title", "后台更新标题"))
    qt_app.processEvents()
    assert panel.editors["name"] is editor
    cursor = document.history.cursor
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert panel.editors["window_title"].text() == "后台更新标题", "无变化的提交也应恢复被延后的刷新。"
    assert document.history.cursor == cursor


def test_cancel_color_dialog_releases_deferred_refresh(window: MainWindow, qt_app: QApplication,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    panel, document = window.properties, window.document
    editor = panel.editors["background_color"]

    def cancel(dialog: QColorDialog) -> int:
        document.execute("弹窗期间修改标题", lambda model: set_property(model, window.registry, model.root_id,
                                                                       "window_title", "颜色取消后的标题"))
        qt_app.processEvents()
        assert panel.editors["background_color"] is editor
        return QColorDialog.DialogCode.Rejected

    monkeypatch.setattr(QColorDialog, "exec", cancel)
    editor._choose()
    qt_app.processEvents()
    assert panel.editors["window_title"].text() == "颜色取消后的标题"


def test_color_dialog_failure_keeps_value_and_reports_chinese_error(window: MainWindow, qt_app: QApplication,
                                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    editor = window.properties.editors["background_color"]
    original = window.document.model
    errors: list[str] = []
    editor.error.connect(errors.append)

    def fail(dialog: QColorDialog) -> int:
        raise RuntimeError("模拟颜色窗口异常")

    monkeypatch.setattr(QColorDialog, "exec", fail)
    editor._choose()
    assert not editor.choosing
    assert errors and "原设置仍保留" in errors[0]
    qt_app.processEvents()
    assert window.document.model == original


@pytest.mark.parametrize("kind", [PropertyPanel, ObjectTree])
def test_pending_refresh_cannot_access_deleted_panel(qt_app: QApplication, kind: type[QWidget]) -> None:
    panel = kind()
    panel.queue_refresh()
    panel.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()


def test_locked_ancestor_disables_geometry_without_blocking_selection(window: MainWindow, qt_app: QApplication) -> None:
    document = window.document
    group = window.page.canvas.create_component("builtin.group_box", QPointF(32, 32))
    children: list[str] = []

    def add_child(model: Any) -> Any:
        candidate, child = create_node(model, window.registry, "builtin.button", 16, 24, parent_id=group)
        children.append(child)
        return candidate

    document.execute("添加子控件", add_child)
    document.select(children[0])
    document.execute("锁定父容器", lambda model: model.with_nodes({group: replace(model.nodes[group],
                                               designer=model.nodes[group].designer.changed(locked=True))}))
    qt_app.processEvents()
    panel = window.properties
    assert not panel.editors["geometry.width"].isEnabled()
    assert not panel.editors["parent_id"].isEnabled()
    assert panel.editors["text"].isEnabled()
    assert panel.commit_pending()
    window.select_window()
    assert document.selected_id == document.model.root_id
