"""Copied controls must refer to their copies, including nonvisual components."""

from dataclasses import replace

import pytest

from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.group_clipboard import copy_group, decode_group, encode_group, paste_group
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.events import set_event_enabled
from core.models import new_project
from tests.test_clipboard import window


@pytest.mark.parametrize("with_event", [False, True])
def test_group_remaps_internal_dialog_trigger(project, registry, with_event):
    project, button = create_node(project, registry, "builtin.button", 16, 16)
    project, dialog = create_node(project, registry, "builtin.dialog", 180, 16)
    project = set_property(project, registry, dialog, "trigger_control", project.nodes[button].code_name)
    if with_event:
        project = set_event_enabled(project, registry, dialog, "accepted", True)
    fragment = copy_group(project, registry, (button, dialog))
    for destination in (project, new_project()):
        pasted, keys = paste_group(destination, registry, fragment, offset=0)
        assert pasted.nodes[keys[1]].properties["trigger_control"] == pasted.nodes[keys[0]].code_name
        registry.validate(pasted)


def test_group_clears_external_dialog_triggers(project, registry):
    project, button = create_node(project, registry, "builtin.button", 16, 16)
    dialogs = []
    for _ in range(2):
        project, key = create_node(project, registry, "builtin.dialog", 160, 16)
        project = set_property(project, registry, key, "trigger_control", project.nodes[button].code_name)
        dialogs.append(key)
    fragment = copy_group(project, registry, tuple(dialogs))
    assert fragment.omitted_connections == 2
    assert all(node.properties["trigger_control"] == "" for node in fragment.nodes)


def test_nonvisual_group_can_be_pasted_into_another_project(project, registry):
    project, button = create_node(project, registry, "builtin.button", 16, 16)
    project, timer = create_node(project, registry, "builtin.timer", 0, 0)
    project, dialog = create_node(project, registry, "builtin.input_dialog", 0, 0)
    project = set_property(project, registry, dialog, "trigger_control", project.nodes[button].code_name)
    fragment = copy_group(project, registry, (timer, dialog))
    assert fragment.omitted_connections == 1
    destination = new_project()
    pasted, keys = paste_group(destination, registry, fragment)
    assert [pasted.nodes[key].object_order for key in keys] == [0, 1]
    assert all(pasted.nodes[key].parent_id == destination.root_id for key in keys)
    assert all(pasted.nodes[key].geometry is None and pasted.nodes[key].stack_order is None for key in keys)
    registry.validate(pasted)


def test_nonvisual_roundtrip_preserves_events_and_atomic_history(project, registry):
    project, timer = create_node(project, registry, "builtin.timer", 0, 0)
    project, dialog = create_node(project, registry, "builtin.input_dialog", 0, 0)
    for key, event in ((timer, "timeout"), (dialog, "accepted")):
        project = set_event_enabled(project, registry, key, event, True)
    fragment = decode_group(encode_group(copy_group(project, registry, (timer, dialog))), registry)
    document = DocumentSession(project, registry)
    before = document.model.to_bytes()
    document.execute("Paste services", lambda model: paste_group(model, registry, fragment)[0])
    after = document.model.to_bytes()
    assert len(document.model.data["connections"]) == len(document.model.data["handlers"]) == 4
    assert len({item["code_name"] for item in document.model.data["handlers"]}) == 4
    document.undo()
    assert document.model.to_bytes() == before
    document.redo()
    assert document.model.to_bytes() == after


def test_nonvisual_group_rejects_locked_root_and_malformed_geometry(project, registry):
    project, a = create_node(project, registry, "builtin.timer", 0, 0)
    project, b = create_node(project, registry, "builtin.input_dialog", 0, 0)
    fragment = copy_group(project, registry, (a, b))
    root = project.nodes[project.root_id]
    locked = project.with_nodes({root.id: replace(root, designer=root.designer.changed(locked=True))})
    with pytest.raises(DesignerError, match="锁定"):
        paste_group(locked, registry, fragment)
    malformed = replace(fragment, nodes=(replace(fragment.nodes[0], stack_order=0), fragment.nodes[1]))
    with pytest.raises(DesignerError):
        decode_group(encode_group(malformed), registry)


@pytest.mark.parametrize("grouped", [False, True])
def test_copy_button_group_clears_external_members(project, registry, grouped):
    project, button = create_node(project, registry, "builtin.button", 0, 0)
    project = set_property(project, registry, button, "checkable", True)
    project, group = create_node(project, registry, "builtin.button_group", 0, 0)
    project = set_property(project, registry, group, "members", (project.nodes[button].code_name,))
    if grouped:
        project, timer = create_node(project, registry, "builtin.timer", 0, 0)
        fragment = copy_group(project, registry, (group, timer))
        result, keys = paste_group(new_project(), registry, fragment)
        node = result.nodes[keys[0]]
    else:
        fragment = copy_fragment(project, registry, group)
        result, key = paste_fragment(new_project(), registry, fragment)
        node = result.nodes[key]
    assert fragment.omitted_connections == 1
    assert node.properties["members"] == ()
    registry.validate(result)


def test_single_nonvisual_copy_avoids_existing_handler_names(project, registry):
    project, timer = create_node(project, registry, "builtin.timer", 0, 0)
    project = set_event_enabled(project, registry, timer, "timeout", True)
    handler = project.data["handlers"][0]
    project = replace(project, data=project.data.changed(handlers=(
        handler.changed(code_name=project.nodes[timer].code_name + "_copy"),)))
    registry.validate(project)
    pasted, key = paste_fragment(project, registry, copy_fragment(project, registry, timer))
    assert pasted.nodes[key].code_name not in {item["code_name"] for item in pasted.data["handlers"]}
    registry.validate(pasted)


def test_creation_avoids_existing_handler_names(project, registry):
    project, timer = create_node(project, registry, "builtin.timer", 0, 0)
    project = set_event_enabled(project, registry, timer, "timeout", True)
    handler = project.data["handlers"][0]
    project = replace(project, data=project.data.changed(handlers=(handler.changed(code_name="timer_2"),)))
    result, key = create_node(project, registry, "builtin.timer", 0, 0)
    assert result.nodes[key].code_name == "timer_3"
    registry.validate(result)


@pytest.mark.parametrize("kinds", [("timer", "input_dialog"), ("dock_widget", "dock_widget")])
def test_designer_copy_paste_and_undo_for_noncanvas_groups(window, qt_app, kinds):
    document, canvas = window.document, window.page.canvas
    keys = []
    for kind in kinds:
        def create(model):
            result, key = create_node(model, window.registry, "builtin." + kind, 0, 0)
            keys.append(key)
            return result
        document.execute("Create", create)
    window.object_tree.setFocus()
    qt_app.processEvents()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    for key, modifier in zip(keys, (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ControlModifier)):
        point = window.object_tree.visualItemRect(window.object_tree._items[key]).center()
        QTest.mouseClick(window.object_tree.viewport(), Qt.MouseButton.LeftButton, modifier, point)
    assert set(document.selected_ids) == set(keys)
    window.edit_actions.refresh()
    assert window.actions["copy"].isEnabled()
    before = document.model.to_bytes()
    window.actions["copy"].trigger()
    assert window.actions["paste"].isEnabled()
    window.actions["paste"].trigger()
    qt_app.processEvents()
    assert len(document.model.nodes) == 6
    assert len(document.selected_ids) == 2
    assert not set(document.selected_ids) & set(keys)
    assert set(document.selected_ids) <= set(window.object_tree._items)
    copied_keys = document.selected_ids
    after = document.model.to_bytes()
    document.undo()
    assert document.model.to_bytes() == before
    document.redo()
    assert document.model.to_bytes() == after
    qt_app.processEvents()
    document.select_many(copied_keys)
    assert not window.actions["arrange_same_size"].isEnabled()
    window.actions["delete"].trigger()
    assert document.model.to_bytes() == before
    document.undo()
    assert document.model.to_bytes() == after


def test_designer_keeps_structural_objects_separate_from_multiselection(window, qt_app):
    keys = []
    for kind in ("timer", "tool_bar"):
        def create(model):
            result, key = create_node(model, window.registry, "builtin." + kind, 0, 0)
            keys.append(key)
            return result
        window.document.execute("Create", create)
    window.document.select_many(tuple(keys))
    window.object_tree.setFocus()
    qt_app.processEvents()
    window.edit_actions.refresh()
    assert window.document.selected_ids == (keys[-1],)
    window.document.select_many((keys[-1], keys[0]))
    assert window.document.selected_ids == (keys[0],)
