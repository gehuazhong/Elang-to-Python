"""Completion coverage: native rendering, ownership, persistence and export parity."""

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QGraphicsScene
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property, delete_node
from core.hierarchy import pages
from core.models import ProjectModel
from core.storage import commit_project, load_project
from codegen.generator import generate_files
from designer.renderer import CanvasRenderer
from runtime.builder import RuntimeTree
from widgets.advanced import ADVANCED_TYPES
from core.commands.tree_clipboard import copy_tree, paste_tree, decode_tree, encode_tree
from core.commands.clipboard import copy_fragment, paste_fragment
from core.document import DocumentSession
from core.errors import DesignerError
from codegen.publisher import export_project
from tests.test_codegen import load_export
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QDialogButtonBox
from PySide6.QtGui import QUndoCommand


@pytest.mark.parametrize("kind", ADVANCED_TYPES)
def test_component_roundtrip_and_canvas(qt_app, registry, project, kind):
    project, key = create_node(project, registry, "builtin." + kind, 16, 16)
    restored = ProjectModel.from_dict(project.to_dict())
    assert restored == project
    plan = compile_plan(restored, registry, "advanced")
    assert "advanced_widgets.py" in generate_files(restored, registry)
    scene = QGraphicsScene()
    renderer = CanvasRenderer(scene, registry)
    try:
        renderer.apply(plan, project.data["canvas"], 1)
        assert key in renderer.items
        assert not renderer.items[key].pixmap().isNull()
        renderer.apply(plan, project.data["canvas"], 1.5)
    finally:
        renderer.dispose()


@pytest.mark.parametrize("kind", ("horizontal_layout", "vertical_layout", "grid_layout", "form_layout",
                                  "scroll_area", "splitter", "stacked_widget", "tool_box", "mdi_area",
                                  "dialog", "dock_widget", "wizard"))
def test_container_child_ownership(qt_app, registry, project, kind):
    project, parent = create_node(project, registry, "builtin." + kind, 12, 12)
    project, first = create_node(project, registry, "builtin.button", 8, 8, parent_id=parent)
    project, second = create_node(project, registry, "builtin.line_edit", 8, 48, parent_id=parent)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "children"))
        qt_app.processEvents()
        assert tree.widgets[first].parentWidget() is not tree.root
        for key in (parent, first, second):
            assert not tree.image(key, 1).isNull()
        if kind in {"horizontal_layout", "vertical_layout", "grid_layout", "form_layout", "splitter"}:
            assert not tree.widgets[first].geometry().intersects(tree.widgets[second].geometry())
        project = delete_node(project, first)
        tree.apply(compile_plan(project, registry, "deleted"))
        qt_app.processEvents()
        assert first not in tree.widgets
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ADVANCED_TYPES)
def test_copy_undo_and_disk(qt_app, registry, project, tmp_path, kind):
    project, key = create_node(project, registry, "builtin." + kind, 16, 16)
    if kind == "wizard_page":
        key = project.nodes[key].parent_id
    if any(node.parent_id == key for node in project.nodes.values()):
        fragment = decode_tree(encode_tree(copy_tree(project, registry, (key,))), registry)
        pasted, keys = paste_tree(project, registry, fragment)
        copied = keys[0]
    else:
        pasted, copied = paste_fragment(project, registry, copy_fragment(project, registry, key))
    assert copied != key
    assert pasted.nodes[copied].properties == project.nodes[key].properties
    document = DocumentSession(project, registry)
    try:
        document.execute("copy", lambda model: pasted)
        document.undo()
        assert document.model == project
        document.redo()
        assert document.model == pasted
        path = tmp_path / "advanced.uipro"
        commit_project(path, pasted, expected_token=None)
        assert load_project(path).model == pasted
    finally:
        document.close()


@pytest.mark.parametrize("kind", [key for key in ADVANCED_TYPES if key not in {"web_view", "opengl_widget", "rhi_widget"}])
def test_export_native_parity(qt_app, registry, project, tmp_path, kind):
    project, key = create_node(project, registry, "builtin." + kind, 16, 16)
    if kind == "splash_screen":
        project = set_property(project, registry, key, "show_on_start", False)
    entry = export_project(project, registry, tmp_path)
    generated = load_export(entry, qt_app)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(project, registry, "parity"))
        actual, expected = generated.controls[project.nodes[key].code_name], tree.widgets[key]
        assert actual.metaObject().className() == expected.metaObject().className()
        if hasattr(expected, "geometry"):
            assert actual.geometry() == expected.geometry()
        if hasattr(expected, "data_model"):
            assert actual.model().rowCount() == expected.model().rowCount() > 0
            assert actual.model().index(0, 0).data() == expected.model().index(0, 0).data()
    finally:
        generated.close()
        generated.deleteLater()
        tree.dispose()


def test_explicit_group_cross_parent_and_deletion(qt_app, registry, project):
    project, frame = create_node(project, registry, "builtin.frame", 0, 0)
    project, a = create_node(project, registry, "builtin.radio_button", 0, 0)
    project, b = create_node(project, registry, "builtin.radio_button", 0, 0, parent_id=frame)
    project, group = create_node(project, registry, "builtin.button_group", 0, 0)
    project = set_property(project, registry, group, "members", [project.nodes[a].code_name, project.nodes[b].code_name])
    project = set_property(project, registry, a, "checked", True)
    project = set_property(project, registry, b, "checked", True)
    assert not project.nodes[a].properties["checked"]
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "group"))
        assert tree.widgets[b].isChecked()
        tree.widgets[a].click()
        assert not tree.widgets[b].isChecked()
        project = delete_node(project, a)
        assert project.nodes[group].properties["members"] == (project.nodes[b].code_name,)
        tree.apply(compile_plan(project, registry, "removed"))
    finally:
        tree.dispose()


def test_input_result_and_dialog_buttons(qt_app, registry, project):
    project, button = create_node(project, registry, "builtin.button", 0, 0)
    project, service = create_node(project, registry, "builtin.input_dialog", 0, 0)
    project = set_property(project, registry, service, "trigger_control", project.nodes[button].code_name)
    project, dialog = create_node(project, registry, "builtin.dialog", 0, 0)
    project, box = create_node(project, registry, "builtin.dialog_button_box", 8, 8, parent_id=dialog)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(project, registry, "dialog"))
        result = QSignalSpy(tree.widgets[service].accepted)
        tree.widgets[button].click()
        from PySide6.QtWidgets import QInputDialog
        assert tree.widgets[service].native.inputMode() == QInputDialog.InputMode.TextInput
        tree.widgets[service].native.setTextValue("result")
        tree.widgets[service].native.accept()
        assert result.count() == 1 and result.at(0) == ["result"]
        tree.widgets[dialog].open_dialog()
        accepted = QSignalSpy(tree.widgets[dialog].accepted)
        tree.widgets[box].button(QDialogButtonBox.StandardButton.Ok).click()
        assert accepted.count() == 1
    finally:
        tree.dispose()


def test_grid_rejects_overlap_and_undo_stack(qt_app, registry, project):
    project, grid = create_node(project, registry, "builtin.grid_layout", 0, 0)
    project, a = create_node(project, registry, "builtin.button", 0, 0, parent_id=grid)
    project, b = create_node(project, registry, "builtin.button", 0, 0, parent_id=grid)
    project = set_property(project, registry, a, "layout_row", 0)
    bad = set_property(project, registry, b, "layout_row", 0)
    with pytest.raises(DesignerError, match="重叠"):
        compile_plan(bad, registry, "invalid")
    project, undo = create_node(project, registry, "builtin.undo_view", 0, 0)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "undo"))
        view = tree.widgets[undo]
        view.undo_stack.push(QUndoCommand("business action"))
        assert view.model().rowCount() == 2
        view.undo_stack.undo()
        assert view.undo_stack.index() == 0
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ("stacked_widget", "tool_box", "wizard"))
def test_live_page_rebuild_keeps_children(qt_app, registry, project, kind):
    from core.commands.pages import add_page
    project, container = create_node(project, registry, "builtin." + kind, 0, 0)
    first, second = pages(project, container)
    project, child = create_node(project, registry, "builtin.line_edit", 8, 8, parent_id=second.id)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "first"))
        retained = tree.widgets[child]
        project, third = add_page(project, registry, container)
        project = set_property(project, registry, container, "current_index", 1)
        tree.apply(compile_plan(project, registry, "added"))
        project = delete_node(project, first.id)
        tree.apply(compile_plan(project, registry, "removed"))
        assert tree.widgets[child] is retained
        assert tree.widgets[container].currentIndex() == 0
        assert len(tree.widgets[container].pages) == 2
        assert tree.widgets[second.id].width() > 200
    finally:
        tree.dispose()


def test_first_toolbox_frame_has_full_page_geometry(qt_app, registry, project):
    project, box = create_node(project, registry, "builtin.tool_box", 0, 0)
    first = pages(project, box)[0]
    project, view = create_node(project, registry, "builtin.list_view", 8, 8, parent_id=first.id)
    renderer = CanvasRenderer(QGraphicsScene(), registry)
    try:
        renderer.apply(compile_plan(project, registry, "first-frame"), project.data["canvas"], 1)
        page_width = renderer.items[first.id].content_layer.rect().width()
        assert page_width > 300
        assert renderer.items[view].isVisible()
    finally:
        renderer.dispose()


def test_geometry_property_rows_are_visible(qt_app, registry, project):
    from panels.properties import PropertyPanel
    project, key = create_node(project, registry, "builtin.grid_layout", 0, 0)
    document = DocumentSession(project, registry)
    panel = PropertyPanel()
    try:
        panel.resize(340, 800)
        panel.bind(document)
        panel.show()
        document.select(key)
        qt_app.processEvents()
        for field in ("x", "y", "width", "height"):
            editor = panel.editors["geometry." + field]
            assert editor.isVisible() and editor.width() > 20 and editor.height() > 10
        child_model, child = create_node(document.model, registry, "builtin.button", 0, 0, parent_id=key)
        document.execute("add managed child", lambda current: child_model)
        document.select(child)
        qt_app.processEvents()
        assert {"layout_order", "layout_stretch", "layout_row", "layout_column", "layout_row_span", "layout_column_span"} <= panel.editors.keys()
        assert panel.editors["parent_id"].isEnabled()
        assert not panel.editors["geometry.width"].isEnabled()
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()
        document.close()


def test_layout_order_reflows_and_can_move_out(qt_app, registry, project):
    from core.commands.hierarchy import reparent_node
    project, layout = create_node(project, registry, "builtin.horizontal_layout", 0, 0)
    project, a = create_node(project, registry, "builtin.button", 0, 0, parent_id=layout)
    project, b = create_node(project, registry, "builtin.button", 0, 0, parent_id=layout)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "original"))
        assert tree.widgets[a].x() < tree.widgets[b].x()
        project = set_property(project, registry, b, "layout_order", 0)
        tree.apply(compile_plan(project, registry, "reordered"))
        assert tree.widgets[b].x() < tree.widgets[a].x()
        project = reparent_node(project, registry, a, project.central_id)
        tree.apply(compile_plan(project, registry, "detached"))
        assert tree.widgets[a].parentWidget() is tree.root.centralWidget()
    finally:
        tree.dispose()
