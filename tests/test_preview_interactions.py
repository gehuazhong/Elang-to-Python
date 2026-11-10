"""预览中的弹层取消和窗口生命周期应与原生组件行为一致。"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from core.commands.nodes import create_node, set_property
from core.models import ProjectModel
from core.registry import WidgetRegistry
from preview.protocol import preview_plan
from runtime.preview import PreviewRuntime
from tests.test_font_editor import installed_test_font


@pytest.mark.parametrize("kind", ["combo_box", "font_combo_box", "common_dialog"])
def test_escape_cancels_popup_before_stopping_preview(project: ProjectModel, registry: WidgetRegistry,
                                                     qt_app: QApplication, kind: str) -> None:
    project, key = create_node(project, registry, "builtin." + kind, 24, 24)
    if kind == "common_dialog":
        project = set_property(project, registry, key, "dialog_kind", "color")
    preview = PreviewRuntime(registry)
    closed = QSignalSpy(preview.closed)
    try:
        preview.show(preview_plan(project, registry, "取消弹层"), project)
        QTest.qWaitForWindowActive(preview.tree.root)
        QTest.qWait(30)
        control = preview.tree.widgets[key]
        if kind in {"combo_box", "font_combo_box"}:
            control.showPopup()
            target = control.view()
        else:
            control.open_dialog()
            target = control.dialog
        qt_app.processEvents()
        assert target.isVisible()
        QTest.keyClick(target, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert not target.isVisible(), "退出键应先关闭当前弹层。"
        assert closed.count() == 0, "取消选项或对话框不应停止整个预览。"
        assert preview.tree.root.isVisible()
        QTest.keyClick(preview.tree.root, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert closed.count() == 1
    finally:
        preview.dispose()


def test_escape_closes_menu_before_stopping_preview(project, registry, qt_app):
    from core.commands.menus import add_menu, ensure_menu_bar

    model, bar = ensure_menu_bar(project, registry)
    model, menu = add_menu(model, registry, bar)
    model, leaf = add_menu(model, registry, menu)
    preview = PreviewRuntime(registry)
    closed = QSignalSpy(preview.closed)
    try:
        preview.show(preview_plan(model, registry, "menu_escape"), model)
        popup = preview.tree.widgets[menu].menu()
        popup.popup(preview.tree.root.mapToGlobal(preview.tree.root.rect().center()))
        qt_app.processEvents()
        assert popup.isVisible()
        QTest.keyClick(popup, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert not popup.isVisible() and closed.count() == 0
        assert preview.tree.root.isVisible()
        QTest.keyClick(preview.tree.root, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert closed.count() == 1
    finally:
        preview.dispose()


def test_preview_runtime_values_keep_native_wheel_behavior(project: ProjectModel, registry: WidgetRegistry,
                                                          qt_app: QApplication) -> None:
    from tests.test_property_interactions import wheel

    project, key = create_node(project, registry, "builtin.spin_box", 24, 24)
    project = set_property(project, registry, key, "value", 10)
    preview = PreviewRuntime(registry)
    try:
        preview.show(preview_plan(project, registry, "运行输入"), project)
        control = preview.tree.widgets[key]
        control.setFocus()
        wheel(control, 120)
        assert control.value() == 11, "属性面板的保护不应改变用户程序的组件行为。"
        assert project.nodes[key].properties["value"] == 10
    finally:
        preview.dispose()


def test_escape_can_be_recorded_as_a_shortcut_in_preview(project, registry, qt_app):
    model, key = create_node(project, registry, "builtin.key_sequence_edit", 24, 24)
    preview = PreviewRuntime(registry)
    closed = QSignalSpy(preview.closed)
    try:
        preview.show(preview_plan(model, registry, "record_escape"), model)
        control = preview.tree.widgets[key]
        control.setFocus()
        QTest.keyClick(control, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert control.keySequence().toString() == "Esc"
        assert closed.count() == 0
        QTest.keyClick(control, Qt.Key.Key_F5, Qt.KeyboardModifier.ShiftModifier)
        qt_app.processEvents()
        assert closed.count() == 1
    finally:
        preview.dispose()
