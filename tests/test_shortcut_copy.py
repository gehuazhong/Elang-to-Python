"""带快捷键的组件复制时仅清除冲突副本，保持事件、源组件和撤销。"""

import pytest
from dataclasses import replace

from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.group_clipboard import copy_group, paste_group
from core.commands.tree_clipboard import copy_tree, paste_tree
from core.commands.menus import add_menu, ensure_menu_bar
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.events import event_enabled, set_event_enabled
from core.models import new_project
from tests.test_clipboard import add_button, window


@pytest.mark.parametrize("mode", ["single", "group", "tree"])
@pytest.mark.parametrize("destination", ["same", "empty", "menu_conflict"])
def test_paste_shortcuts_resolves_only_collisions(project, registry, mode, destination):
    source = project
    if mode == "tree":
        source, container = create_node(source, registry, "builtin.group_box", 0, 0)
    else:
        container = source.central_id
    source, button = create_node(source, registry, "builtin.button", 0, 0, parent_id=container)
    source, label = create_node(source, registry, "builtin.label", 0, 60, parent_id=container)
    source = set_property(source, registry, button, "shortcut", "Ctrl+K")
    source = set_event_enabled(source, registry, button, "clicked", True)
    copy, paste, keys = {
        "single": (copy_fragment, paste_fragment, button),
        "group": (copy_group, paste_group, (button, label)),
        "tree": (copy_tree, paste_tree, (container,)),
    }[mode]
    fragment = copy(source, registry, keys)
    target = source if destination == "same" else new_project("目标")
    if destination == "menu_conflict":
        target, bar = ensure_menu_bar(target, registry)
        target, menu = add_menu(target, registry, bar)
        target = set_property(target, registry, menu, "shortcut", "Ctrl+K")
    document = DocumentSession(target, registry)
    document.execute("粘贴", lambda model: paste(model, registry, fragment)[0])
    created = next(node for key, node in document.model.nodes.items()
                   if key not in target.nodes and node.type_id == "builtin.button")
    assert created.properties["shortcut"] == ("Ctrl+K" if destination == "empty" else "")
    assert event_enabled(document.model, created.id, "clicked")
    assert source.nodes[button].properties["shortcut"] == "Ctrl+K"
    document.undo()
    assert document.model == target
    document.redo()
    assert document.model.nodes[created.id].properties == created.properties


def test_paste_reports_shortcut_conflict_in_status_bar(window):
    key = add_button(window)
    document, registry = window.document, window.registry
    document.execute("设置快捷键", lambda model: set_property(model, registry, key, "shortcut", "Ctrl+K"))
    document.select(key)
    window.edit_actions._copy_node()
    window.edit_actions._paste_node()
    assert "快捷键" in window.statusBar().currentMessage()
    assert document.model.nodes[document.selected_id].properties["shortcut"] == ""


def test_future_component_shortcut_data_is_preserved(project, registry):
    from core.build_plan import compile_plan

    model, key = create_node(project, registry, "builtin.button", 0, 0)
    node = model.nodes[key]
    model = model.with_nodes({key: replace(node, type_version=node.type_version + 1,
                                         properties=node.properties.changed(shortcut={"future_binding": True}))})
    plan = compile_plan(model, registry, "future", allow_unknown=True)
    assert next(node for node in plan.nodes if node.id == key).unknown
    assert model.nodes[key].properties["shortcut"]["future_binding"]


def test_copy_enables_paste_without_waiting_for_clipboard_notification(window):
    from PySide6.QtCore import QSignalBlocker
    from PySide6.QtWidgets import QApplication

    add_button(window)
    clipboard = QApplication.clipboard()
    clipboard.clear()
    window.edit_actions.refresh()
    assert not window.actions["paste"].isEnabled()
    with QSignalBlocker(clipboard):
        window.edit_actions._copy_node()
        assert window.actions["paste"].isEnabled()
