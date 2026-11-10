"""补充组件和属性从模型、原生交互到独立预览/导出的覆盖。"""

from dataclasses import replace
import os

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QFontDatabase, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QKeySequenceEdit, QLineEdit

from codegen.publisher import export_project
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.menus import add_menu, ensure_menu_bar
from core.commands.nodes import create_node, set_property
from core.commands.hierarchy import reparent_node
from core.document import DocumentSession
from core.errors import DesignerError
from core.events import set_event_enabled
from core.storage import commit_project, load_project
from panels.font_editor import FontFamilyEditor
from panels.properties import PropertyPanel
from preview.protocol import preview_plan
from runtime.builder import RuntimeTree
from runtime.events import EventConnections
from runtime.preview import PreviewRuntime
from tests.test_codegen import load_export
from tests.test_easy_widgets import image_value
from tests.test_events import binding
from tests.test_font_editor import installed_test_font
from tests.test_preview import service, await_ready
from tests.test_storage import wait_for
from widgets.catalog import SUPPORTED_SLOTS


NEW_TYPES = ("rich_text_edit", "text_browser", "font_combo_box", "key_sequence_edit")


def configure(model, registry, kind):
    model, key = create_node(model, registry, "builtin." + kind, 20, 40)
    values = {
        "rich_text_edit": {"text": "<p><b>中文内容</b></p>", "text_format": "rich", "document_margin": 9,
                           "tab_stop_distance": 48, "rich_line_wrap": "none"},
        "text_browser": {"text": '<p><a href="demo:item">打开项目</a></p>', "open_links": False},
        "font_combo_box": {"current_font": next(family for family in QFontDatabase.families() if family), "editable": False},
        "key_sequence_edit": {"key_sequence": "Ctrl+Shift+K", "clear_button": True},
    }[kind]
    for field, value in values.items():
        model = set_property(model, registry, key, field, value)
    signal = {"rich_text_edit": "textChanged", "text_browser": "anchorClicked",
              "font_combo_box": "currentFontChanged", "key_sequence_edit": "keySequenceChanged"}[kind]
    return set_event_enabled(model, registry, key, signal, True), key


def state(widget, kind):
    if kind == "rich_text_edit":
        return widget.toPlainText(), widget.document().documentMargin(), widget.tabStopDistance(), widget.lineWrapMode()
    if kind == "text_browser":
        return widget.toPlainText(), widget.isReadOnly(), widget.openLinks(), widget.openExternalLinks()
    if kind == "font_combo_box":
        return widget.currentFont().family(), widget.fontFilters(), widget.writingSystem(), widget.isEditable()
    return widget.keySequence().toString(QKeySequence.SequenceFormat.PortableText), widget.isClearButtonEnabled(), widget.maximumSequenceLength()


@pytest.mark.parametrize("kind", NEW_TYPES)
def test_new_component_persistence_copy_undo_runtime_and_export(project, registry, qt_app, tmp_path, kind):
    model, key = configure(project, registry, kind)
    document = DocumentSession(model, registry)
    document.execute("禁用组件", lambda value: set_property(value, registry, key, "enabled", False))
    document.undo()
    assert document.model == model
    fragment = copy_fragment(model, registry, key)
    copied, copied_key = paste_fragment(model, registry, fragment)
    assert copied.nodes[copied_key].properties == model.nodes[key].properties
    path = tmp_path / (kind + ".uipro")
    commit_project(path, model, expected_token=None)
    assert load_project(path).model == model
    tree = RuntimeTree(registry, design_mode=False)
    exported = None
    try:
        tree.apply(preview_plan(model, registry, kind))
        control = tree.widgets[key]
        expected = state(control, kind)
        if kind == "rich_text_edit":
            assert expected[:3] == ("中文内容", 9, 48)
        elif kind == "text_browser":
            assert expected == ("打开项目", True, False, False)
        elif kind == "font_combo_box":
            assert expected[0] == model.nodes[key].properties["current_font"] and not expected[-1]
        else:
            assert expected == ("Ctrl+Shift+K", True, 1)
        exported = load_export(export_project(model, registry, tmp_path / "export"), qt_app)
        assert state(exported.controls[model.nodes[key].code_name], kind) == expected
    finally:
        if exported is not None:
            exported.close()
            exported.deleteLater()
        tree.dispose()


def test_font_and_shortcut_properties_use_native_choosers(project, registry, qt_app):
    model, font = configure(project, registry, "font_combo_box")
    model, shortcut = configure(model, registry, "key_sequence_edit")
    document = DocumentSession(model, registry)
    panel = PropertyPanel()
    try:
        document.select(font)
        panel.bind(document)
        assert isinstance(panel.editors["current_font"], FontFamilyEditor)
        document.select(shortcut)
        panel.refresh()
        editor = panel.editors["key_sequence"]
        assert isinstance(editor, QKeySequenceEdit)
        editor.setKeySequence(QKeySequence("Alt+K"))
        editor.editingFinished.emit()
        assert document.model.nodes[shortcut].properties["key_sequence"] == "Alt+K"
        document.undo()
        assert document.model.nodes[shortcut].properties["key_sequence"] == "Ctrl+Shift+K"
    finally:
        panel.bind(None)
        panel.deleteLater()


def test_shortcut_input_receives_real_keyboard_and_signal_events(qt_app):
    widget = QKeySequenceEdit()
    widget.setMaximumSequenceLength(1)
    received = []
    manager = EventConnections(widget, {"control": widget},
                               [binding(event="KeyPress"), binding(signal="keySequenceChanged")],
                               lambda event, args: received.append((event["key"], args[0].key() if event["key"] == "KeyPress" else None)))
    try:
        widget.show()
        widget.activateWindow()
        widget.setFocus()
        QTest.qWait(30)
        QTest.keyClick(widget, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
        widget.clearFocus()
        QTest.qWait(1100)
        assert widget.keySequence().toString() == "Ctrl+K"
        assert any(key == "KeyPress" and value == Qt.Key.Key_K for key, value in received)
        assert any(key == "keySequenceChanged" for key, _ in received)
    finally:
        manager.dispose()
        widget.close()
        widget.deleteLater()


def test_rich_label_link_can_be_clicked_and_plain_mode_is_preserved(project, registry, qt_app):
    model, key = create_node(project, registry, "builtin.label", 20, 40)
    for field, value in {"text": '<a href="demo:item">打开项目</a>', "text_format": "rich"}.items():
        model = set_property(model, registry, key, field, value)
    model = set_event_enabled(model, registry, key, "linkActivated", True)
    preview = PreviewRuntime(registry)
    notices = []
    preview.notice.connect(notices.append)
    try:
        preview.show(preview_plan(model, registry, "link"), model)
        label = preview.tree.widgets[key]
        QTest.mouseClick(label, Qt.MouseButton.LeftButton, pos=QPoint(8, label.height() // 2))
        assert len(notices) == 1 and "链接被单击" in notices[0]
        plain = set_property(model, registry, key, "text_format", "plain")
        preview.show(preview_plan(plain, registry, "plain"), plain)
        assert label.textFormat() == Qt.TextFormat.PlainText
        QTest.mouseClick(label, Qt.MouseButton.LeftButton, pos=QPoint(8, label.height() // 2))
        assert len(notices) == 1
    finally:
        preview.dispose()


@pytest.mark.parametrize("kind", ["button", "tool_button", "command_link_button", "check_box", "radio_button"])
def test_button_icon_shortcut_and_restore_default(project, registry, qt_app, tmp_path, kind):
    model, key = create_node(project, registry, "builtin." + kind, 20, 40)
    model = set_property(model, registry, key, "text", "&Run")
    tree = RuntimeTree(registry, design_mode=False)
    exported = None
    try:
        tree.apply(preview_plan(model, registry, "default"))
        button = tree.widgets[key]
        original_icon = button.icon().cacheKey()
        original_size = button.iconSize()
        assert button.shortcut().toString() == "Alt+R"
        for field, value in {"icon": image_value(tmp_path), "icon_width": 28, "icon_height": 24, "shortcut": "Ctrl+K"}.items():
            model = set_property(model, registry, key, field, value)
        tree.apply(preview_plan(model, registry, "changed"))
        assert not button.icon().isNull() and button.iconSize().width() == 28 and button.iconSize().height() == 24
        fired = []
        button.clicked.connect(lambda checked=False: fired.append(checked))
        tree.root.show()
        tree.root.activateWindow()
        QTest.qWait(30)
        QTest.keyClick(tree.root, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
        wait_for(lambda: len(fired) == 1, qt_app)
        assert len(fired) == 1
        exported = load_export(export_project(model, registry, tmp_path / "export"), qt_app)
        target = exported.controls[model.nodes[key].code_name]
        assert not target.icon().isNull() and target.iconSize() == button.iconSize()
        assert target.shortcut() == button.shortcut()
        for field, value in {"icon": "", "icon_width": 0, "icon_height": 0, "shortcut": ""}.items():
            model = set_property(model, registry, key, field, value)
        tree.apply(preview_plan(model, registry, "restored"))
        assert button.icon().cacheKey() == original_icon and button.iconSize() == original_size
        assert button.shortcut().toString() == "Alt+R"
    finally:
        if exported:
            exported.close()
            exported.deleteLater()
        tree.dispose()


def test_menu_and_button_shortcut_conflicts_are_rejected(project, registry):
    model, button = create_node(project, registry, "builtin.button", 20, 40)
    model = set_property(model, registry, button, "shortcut", "ctrl+k")
    model, bar = ensure_menu_bar(model, registry)
    model, menu = add_menu(model, registry, bar)
    model = set_property(model, registry, menu, "shortcut", "Ctrl+K")
    with pytest.raises(DesignerError, match="快捷键重复"):
        registry.validate(model)


def test_group_checkbox_applies_after_children_and_preserves_disabled_children(project, registry, qt_app, tmp_path):
    model, group = create_node(project, registry, "builtin.group_box", 20, 40)
    model = set_property(model, registry, group, "checkable", True)
    model, enabled = create_node(model, registry, "builtin.button", 12, 12, parent_id=group)
    model, disabled = create_node(model, registry, "builtin.button", 12, 64, parent_id=group)
    model = set_property(model, registry, disabled, "enabled", False)
    tree = RuntimeTree(registry, design_mode=False)
    exported = None
    try:
        tree.apply(preview_plan(model, registry, "group"))
        checkbox = tree.widgets[group]
        assert not checkbox.isChecked() and not tree.widgets[enabled].isEnabled()
        checkbox.setChecked(True)
        assert tree.widgets[enabled].isEnabled() and not tree.widgets[disabled].isEnabled()
        changed = set_property(model, registry, enabled, "text", "修改内部属性")
        tree.apply(preview_plan(changed, registry, "child_changed"))
        assert not checkbox.isChecked() and not tree.widgets[enabled].isEnabled()
        checkbox.setChecked(True)
        assert tree.widgets[enabled].isEnabled() and not tree.widgets[disabled].isEnabled()
        exported = load_export(export_project(model, registry, tmp_path / "export"), qt_app)
        controls = exported.controls
        assert not controls[model.nodes[enabled].code_name].isEnabled()
        controls[model.nodes[group].code_name].setChecked(True)
        assert controls[model.nodes[enabled].code_name].isEnabled()
        assert not controls[model.nodes[disabled].code_name].isEnabled()
    finally:
        if exported:
            exported.close()
            exported.deleteLater()
        tree.dispose()


def test_every_registered_component_uses_real_preview_and_export(project, registry, service, qt_app, tmp_path):
    model = project
    for spec in registry.specs.values():
        assert spec.slot in SUPPORTED_SLOTS
        if spec.toolbox:
            model, key = create_node(model, registry, spec.type_id, 20, 40)
            if spec.events:
                model = set_event_enabled(model, registry, key, spec.events[0].key, True)
    model, bar = ensure_menu_bar(model, registry)
    model, parent = add_menu(model, registry, bar)
    model, leaf = add_menu(model, registry, parent)
    model = set_event_enabled(model, registry, leaf, "clicked", True)
    service.start(model, "全部组件", "覆盖检查")
    await_ready(service, qt_app)
    assert service.last_ready["process_id"] != os.getpid()
    assert service.last_ready["widget_count"] == len(model.nodes)
    service.stop()
    wait_for(lambda: not service.active, qt_app)
    exported = load_export(export_project(model, registry, tmp_path / "all"), qt_app)
    try:
        assert len(exported.controls) == len(model.nodes)
    finally:
        exported.close()
        exported.deleteLater()


def test_shortcut_input_text_is_drawn_on_design_canvas(project, registry, qt_app):
    model, key = configure(project, registry, "key_sequence_edit")
    tree = RuntimeTree(registry)
    try:
        tree.apply(preview_plan(model, registry, "shortcut_image"))
        first = tree.image(key, 1)
        model = set_property(model, registry, key, "key_sequence", "Alt+F12")
        tree.apply(preview_plan(model, registry, "changed_image"))
        assert tree.image(key, 1) != first
    finally:
        tree.dispose()


@pytest.mark.parametrize("outer_checked,inner_checked,child_enabled", [
    (outer, inner, child) for outer in (False, True) for inner in (False, True) for child in (False, True)
])
def test_nested_group_state_and_reparenting(project, registry, qt_app, tmp_path,
                                          outer_checked, inner_checked, child_enabled):
    model, outer = create_node(project, registry, "builtin.group_box", 0, 0)
    model, inner = create_node(model, registry, "builtin.group_box", 0, 0, parent_id=outer)
    model, child = create_node(model, registry, "builtin.button", 0, 0, parent_id=inner)
    for key, checked in ((outer, outer_checked), (inner, inner_checked)):
        model = set_property(model, registry, key, "checkable", True)
        model = set_property(model, registry, key, "checked", checked)
    model = set_property(model, registry, child, "enabled", child_enabled)
    tree = RuntimeTree(registry, design_mode=False)
    exported = None
    try:
        tree.apply(preview_plan(model, registry, "nested_group"))
        exported = load_export(export_project(model, registry, tmp_path / "nested"), qt_app)
        for controls in (tree.widgets, {key: exported.controls[node.code_name] for key, node in model.nodes.items()}):
            assert controls[child].isEnabled() == (outer_checked and inner_checked and child_enabled)
            controls[outer].setChecked(True)
            assert controls[child].isEnabled() == (inner_checked and child_enabled)
            controls[inner].setChecked(True)
            assert controls[child].isEnabled() == child_enabled
            controls[outer].setChecked(False)
            controls[outer].setChecked(True)
            assert controls[child].isEnabled() == child_enabled
        tree.apply(preview_plan(model, registry, "reset_nested_group"))
        moved = reparent_node(model, registry, child, model.central_id)
        tree.apply(preview_plan(moved, registry, "move_out_of_group"))
        assert tree.widgets[child].isEnabled() == child_enabled
    finally:
        if exported is not None:
            exported.close()
            exported.deleteLater()
        tree.dispose()


@pytest.mark.parametrize("kind", ["rich_text_edit", "text_browser", "font_combo_box"])
def test_extra_component_native_interaction_obeys_event_checkbox(project, registry, qt_app, kind):
    model, key = configure(project, registry, kind)
    preview = PreviewRuntime(registry)
    notices = []
    preview.notice.connect(notices.append)
    try:
        preview.show(preview_plan(model, registry, "extra_event"), model)
        widget = preview.tree.widgets[key]
        def interact():
            if kind == "rich_text_edit":
                QTest.keyClicks(widget, "hello")
            elif kind == "text_browser":
                QTest.mouseClick(widget.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(8, 12))
            else:
                QTest.keyClick(widget, Qt.Key.Key_Down)
        widget.setFocus()
        interact()
        assert notices
        event = {"rich_text_edit": "textChanged", "text_browser": "anchorClicked",
                 "font_combo_box": "currentFontChanged"}[kind]
        model = set_event_enabled(model, registry, key, event, False)
        preview.show(preview_plan(model, registry, "extra_event_off"), model)
        notices.clear()
        interact()
        assert not notices
    finally:
        preview.dispose()
