"""Stacking changes only z order and remains one undoable transaction."""

from dataclasses import replace
from itertools import combinations

import pytest
from PySide6.QtWidgets import QMenu

from core.commands.arrange import STACKING, available_stacking, stack_nodes
from core.commands.nodes import create_node
from core.document import DocumentSession
from core.errors import DesignerError
from core.storage import commit_project, load_project
from tests.test_clipboard import open_context
from tests.test_multiselect import keys_of, window


def ordered(model, keys):
    return tuple(sorted(keys, key=lambda key: model.nodes[key].stack_order))


@pytest.mark.parametrize("mode,expected", [("raise", (0, 2, 1, 4, 3)), ("lower", (1, 0, 3, 2, 4)),
                                          ("front", (0, 2, 4, 1, 3)), ("back", (1, 3, 0, 2, 4))])
def test_multiselection_order_roundtrip(project, registry, qt_app, tmp_path, mode, expected):
    keys = []
    for _ in range(5):
        project, key = create_node(project, registry, "builtin.button", 20, 20)
        keys.append(key)
    document = DocumentSession(project, registry)
    try:
        document.select_many((keys[3], keys[1]))
        document.execute(mode, lambda m: stack_nodes(m, document.selected_ids, mode))
        assert ordered(document.model, keys) == tuple(keys[index] for index in expected)
        assert document.history.cursor == 1
        for key in keys:
            assert replace(document.model.nodes[key], stack_order=project.nodes[key].stack_order) == project.nodes[key]
        path = tmp_path / "stacking.uipro"
        commit_project(path, document.model, expected_token=None)
        assert load_project(path).model == document.model
        document.undo()
        assert document.model == project
        document.redo()
        assert ordered(document.model, keys) == tuple(keys[index] for index in expected)
    finally:
        document.close()


def test_boundary_noops_and_locked_selection(project, registry, qt_app):
    project, first = create_node(project, registry, "builtin.button", 20, 20)
    project, last = create_node(project, registry, "builtin.label", 20, 20)
    document = DocumentSession(project, registry)
    try:
        for keys, modes in (((first,), ("back", "lower")), ((last,), ("front", "raise")),
                            ((first, last), ("front", "back", "raise", "lower"))):
            for mode in modes:
                document.execute(mode, lambda m: stack_nodes(m, keys, mode))
        assert document.history.cursor == 0
        locked = project.with_nodes({first: replace(project.nodes[first], designer=project.nodes[first].designer.changed(locked=True))})
        with pytest.raises(DesignerError):
            stack_nodes(locked, (first,), "front")
        with pytest.raises(DesignerError):
            stack_nodes(project, (project.root_id,), "front")
        locked_parent = project.with_nodes({project.central_id: replace(project.nodes[project.central_id],
                                          designer=project.nodes[project.central_id].designer.changed(locked=True))})
        with pytest.raises(DesignerError):
            stack_nodes(locked_parent, (first,), "front")
    finally:
        document.close()


def test_canvas_z_order_and_menu_actions(window, qt_app):
    document = window.document
    keys = keys_of(window)
    document.select(keys[0])
    window.page.canvas.setFocus()
    window.edit_actions.refresh()
    assert window.actions["stack_front"].isEnabled()
    assert not window.actions["stack_back"].isEnabled()
    before = document.model
    menu = open_context(window, tree_id=keys[0])
    submenu = next(child for child in menu.findChildren(QMenu) if child.title() == "层级")
    next(action for action in submenu.actions() if action.objectName() == "stack_front").trigger()
    menu.close()
    qt_app.processEvents()
    assert document.model.nodes[keys[0]].stack_order == 2
    assert window.page.canvas.renderer.items[keys[0]].zValue() > window.page.canvas.renderer.items[keys[2]].zValue()
    window.edit_actions.undo()
    assert document.model == before
    document.select_many((keys[0], keys[1]))
    window.edit_actions.stack("front")
    assert ordered(document.model, keys) == (keys[2], keys[0], keys[1])


def test_menu_availability_matches_real_commands_for_every_selection(project, registry):
    keys = []
    for _ in range(5):
        project, key = create_node(project, registry, "builtin.button", 20, 20)
        keys.append(key)
    for count in range(1, len(keys) + 1):
        for selected in combinations(keys, count):
            expected = {mode for mode in STACKING if stack_nodes(project, selected, mode) != project}
            assert available_stacking(project, selected) == expected
