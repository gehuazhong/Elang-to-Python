"""容器嵌套、坐标、裁切、整树复制和原生运行一致性回归。"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from uuid import uuid4

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.arrange import arrange_nodes
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.hierarchy import reparent_node
from core.commands.nodes import create_node, delete_node, set_property
from core.commands.tree_clipboard import copy_tree, decode_tree, encode_tree, paste_tree
from core.document import DocumentSession
from core.errors import DesignerError
from core.hierarchy import absolute_position, content_origin, content_size, subtree_ids
from core.models import FrozenMap, ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.canvas import DesignerCanvas
from designer.clipboard import TREE_MIME, read_component
from runtime.builder import RuntimeTree
from tests.test_canvas import mouse_move
from tests.test_clipboard import window, open_context
from tests.test_codegen import load_export


def nested(project: ProjectModel, registry: WidgetRegistry) -> tuple[ProjectModel, tuple[str, ...]]:
    project, group = create_node(project, registry, "builtin.group_box", 32, 40)
    project = set_property(project, registry, group, "geometry.width", 460)
    project = set_property(project, registry, group, "geometry.height", 320)
    project, frame = create_node(project, registry, "builtin.frame", 16, 20, parent_id=group)
    project = set_property(project, registry, frame, "geometry.width", 240)
    project = set_property(project, registry, frame, "geometry.height", 160)
    project, button = create_node(project, registry, "builtin.button", 12, 16, parent_id=frame)
    project, radio = create_node(project, registry, "builtin.radio_button", 16, 204, parent_id=group)
    project = set_property(project, registry, radio, "checked", True)
    return project, (group, frame, button, radio)


def test_container_roundtrip_native_export_and_coordinates(project: ProjectModel, registry: WidgetRegistry,
                                                         qt_app: QApplication, tmp_path: Path) -> None:
    project, keys = nested(project, registry)
    project = set_property(project, registry, keys[0], "font_size", 18)
    project = set_property(project, registry, keys[0], "content_top", 48)
    path = tmp_path / "嵌套项目.uipro"
    commit_project(path, project, expected_token=None)
    loaded = load_project(path).model
    assert loaded == project
    canvas = DesignerCanvas(DocumentSession(loaded, registry))
    generated = load_export(export_project(loaded, registry, tmp_path / "容器导出"), qt_app)
    try:
        qt_app.processEvents()
        for key in keys:
            node = loaded.nodes[key]
            native = canvas.renderer.tree.widgets[key]
            actual = generated.controls[node.code_name]
            expected_x, expected_y = absolute_position(loaded, key)
            assert native.mapTo(canvas.renderer.tree.root, QPoint()) == QPoint(expected_x, expected_y)
            assert canvas.renderer.items[key].scenePos() == QPointF(expected_x, expected_y)
            assert actual.geometry() == native.geometry()
            assert actual.contentsRect() == native.contentsRect()
            assert actual.parentWidget() is generated.controls[loaded.nodes[node.parent_id].code_name]
    finally:
        generated.close()
        generated.deleteLater()
        canvas.dispose()
        canvas.close()


def test_parent_move_undo_delete_redo_keeps_live_child_items(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, keys = nested(project, registry)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    errors = []
    canvas.error.connect(errors.append)
    try:
        original = canvas.renderer.items[keys[2]].scenePos()
        document.execute("移动父容器", lambda model: set_property(model, registry, keys[0], "geometry.x", 72))
        assert canvas.renderer.items[keys[2]].scenePos() == original + QPointF(40, 0)
        document.undo()
        assert canvas.renderer.items[keys[2]].scenePos() == original
        for _ in range(5):
            document.execute("删除整棵控件树", lambda model: delete_node(model, keys[0]))
            assert not set(keys).intersection(canvas.renderer.items)
            document.undo()
            assert all(key in canvas.renderer.items for key in keys)
            document.redo()
            document.undo()
        assert not errors
        assert document.model == project
    finally:
        canvas.dispose()
        canvas.close()


def test_reparent_preserves_screen_position_and_undo(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, keys = nested(project, registry)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    errors = []
    canvas.error.connect(errors.append)
    try:
        before = absolute_position(project, keys[2])
        document.execute("移至工作区", lambda model: reparent_node(model, registry, keys[2], model.central_id))
        assert absolute_position(document.model, keys[2]) == before
        assert document.model.nodes[keys[2]].parent_id == project.central_id
        assert canvas.renderer.items[keys[2]].parentItem() is canvas.renderer.central_clip
        document.undo()
        assert document.model == project
        assert canvas.renderer.items[keys[2]].parentItem() is canvas.renderer.items[keys[1]].content_layer
        assert not errors
    finally:
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("case", ["self", "descendant", "leaf", "locked_parent", "locked_child", "too_small"])
def test_invalid_reparent_is_atomic(project: ProjectModel, registry: WidgetRegistry, case: str) -> None:
    project, keys = nested(project, registry)
    group, frame, button, radio = keys
    key, parent = group, frame
    if case == "self":
        parent = group
    elif case == "leaf":
        key, parent = radio, button
    elif case == "locked_parent":
        project = project.with_nodes({frame: replace(project.nodes[frame], designer=project.nodes[frame].designer.changed(locked=True))})
        key, parent = radio, frame
    elif case == "locked_child":
        project = project.with_nodes({button: replace(project.nodes[button], designer=project.nodes[button].designer.changed(locked=True))})
        key, parent = button, project.central_id
    elif case == "too_small":
        key, parent = frame, group
        project = set_property(project, registry, group, "geometry.width", 150)
        project = reparent_node(project, registry, frame, project.central_id)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("错误调整容器", lambda model: reparent_node(model, registry, key, parent))
    assert document.model is project and document.history.cursor == 0


def test_container_lock_blocks_child_move_create_delete(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = nested(project, registry)
    group, frame, button, _ = keys
    project = project.with_nodes({group: replace(project.nodes[group], designer=project.nodes[group].designer.changed(locked=True))})
    document = DocumentSession(project, registry)
    for action in (lambda model: set_property(model, registry, button, "geometry.x", 16),
                   lambda model: create_node(model, registry, "builtin.button", 0, 0, parent_id=frame)[0],
                   lambda model: delete_node(model, button)):
        with pytest.raises(DesignerError, match="锁定"):
            document.execute("锁定操作", action)
        assert document.model is project


def test_container_child_clipping_visibility_and_stacking(project: ProjectModel, registry: WidgetRegistry, qt_app: QApplication) -> None:
    project, keys = nested(project, registry)
    frame, button = keys[1:3]
    project = set_property(project, registry, button, "geometry.x", 200)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    try:
        child = canvas.renderer.items[button]
        outside = child.mapToScene(QPointF(110, 20))
        assert child not in canvas.scene().items(outside)
        frame_node = document.model.nodes[frame]
        document.execute("隐藏父容器", lambda model: model.with_nodes({frame: replace(frame_node, designer=frame_node.designer.changed(hidden=True))}))
        assert not canvas.renderer.items[button].isVisible()
        document.undo()
        assert canvas.renderer.items[button].isVisible()
        project2, overlay = create_node(document.model, registry, "builtin.label", 32, 40)
        project2 = set_property(project2, registry, overlay, "geometry.width", 500)
        project2 = set_property(project2, registry, overlay, "geometry.height", 400)
        document.execute("增加覆盖组件", lambda model: project2)
        point = canvas.mapFromScene(canvas.renderer.node_rect(keys[3]).center())
        assert canvas.node_at(point) == overlay
    finally:
        canvas.dispose()
        canvas.close()


def test_tree_clipboard_preserves_nested_geometry_connections_and_focus(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = nested(project, registry)
    group, frame, button, radio = keys
    handler_id = str(uuid4())
    project = replace(project, data=project.data.changed(
        tab_order=(button, radio), handlers=({"id": handler_id, "name": "处理事件", "code_name": "handle_click", "parameters": []},),
        connections=({"id": str(uuid4()), "source_id": button, "event": "clicked", "target": {"kind": "handler", "handler_id": handler_id},
                      "arguments": [], "enabled": True},)))
    validate_project(project)
    fragment = decode_tree(encode_tree(copy_tree(project, registry, (group, frame, button))), registry)
    assert fragment.roots == (group,) and len(fragment.nodes) == 4
    document = DocumentSession(project, registry)
    created = []

    def paste(model: ProjectModel) -> ProjectModel:
        result, roots = paste_tree(model, registry, fragment)
        created.extend(roots)
        return result

    document.execute("粘贴容器树", paste)
    copied_ids = subtree_ids(document.model, tuple(created))
    assert len(copied_ids) == 4
    for original, copy_key in zip(keys, copied_ids):
        if original != group:
            assert document.model.nodes[copy_key].geometry == project.nodes[original].geometry
        assert document.model.nodes[copy_key].properties == project.nodes[original].properties
    assert document.model.data["connections"][-1]["source_id"] in copied_ids
    assert document.model.data["connections"][-1]["target"]["handler_id"] != handler_id
    assert set(document.model.data["tab_order"][-2:]) <= set(copied_ids)
    document.undo()
    assert document.model == project
    document.redo()
    assert all(key in document.model.nodes for key in copied_ids)


@pytest.mark.parametrize("corruption", ["duplicate", "cycle", "foreign_parent", "foreign_tab", "unknown", "duplicate_order"])
def test_tree_clipboard_rejects_corrupt_structure(project: ProjectModel, registry: WidgetRegistry, corruption: str) -> None:
    project, keys = nested(project, registry)
    payload = json.loads(encode_tree(copy_tree(project, registry, (keys[0],))))
    if corruption == "duplicate":
        payload["nodes"].append(payload["nodes"][0])
    elif corruption == "cycle":
        payload["nodes"][0]["parent_id"] = keys[2]
    elif corruption == "foreign_parent":
        payload["nodes"][2]["parent_id"] = str(uuid4())
    elif corruption == "foreign_tab":
        payload["tab_order"] = [str(uuid4())]
    elif corruption == "unknown":
        payload["extra"] = True
    else:
        payload["nodes"][-1]["object_order"] = payload["nodes"][1]["object_order"]
    with pytest.raises(DesignerError):
        decode_tree(json.dumps(payload).encode("utf-8"), registry)


def test_radio_groups_are_independent_and_reparent_resolves_conflict(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, first = create_node(project, registry, "builtin.group_box", 16, 16)
    project, second = create_node(project, registry, "builtin.group_box", 352, 16)
    project, radio1 = create_node(project, registry, "builtin.radio_button", 8, 8, parent_id=first)
    project, radio2 = create_node(project, registry, "builtin.radio_button", 8, 8, parent_id=second)
    project = set_property(project, registry, radio1, "checked", True)
    project = set_property(project, registry, radio2, "checked", True)
    registry.validate(project)
    document = DocumentSession(project, registry)
    document.execute("调整单选分组", lambda model: reparent_node(model, registry, radio1, second))
    assert document.model.nodes[radio1].properties["checked"] and not document.model.nodes[radio2].properties["checked"]
    document.undo()
    assert document.model == project


def test_child_paste_and_arrange_respect_content_bounds(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = nested(project, registry)
    fragment = copy_fragment(project, registry, keys[2])
    copied, key = paste_fragment(project, registry, fragment, parent_id=keys[1], position=(1000, 1000))
    width, height = content_size(copied, keys[1])
    rect = copied.nodes[key].geometry
    assert rect.x + rect.width == width and rect.y + rect.height == height
    result = arrange_nodes(copied, (keys[2], key), "left", keys[2])
    assert result.nodes[key].geometry.x == result.nodes[keys[2]].geometry.x
    assert result.nodes[key].parent_id == keys[1]


def test_canvas_drop_nested_move_and_property_parent_change(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    group = canvas.create_component("builtin.group_box", QPointF(32, 40))
    child = canvas.create_component("builtin.button", QPointF(72, 104))
    qt_app.processEvents()
    assert document.model.nodes[child].parent_id == group
    assert window.object_tree.currentItem().parent().text(0) == document.model.nodes[group].name
    point = canvas.mapFromScene(canvas.renderer.node_rect(child).center())
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    mouse_move(canvas, point + QPoint(24, 16))
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(24, 16))
    qt_app.processEvents()
    assert document.model.nodes[child].geometry.x > 28
    before = document.model
    parent_editor = window.properties.editors["parent_id"]
    parent_editor.activated.emit(parent_editor.findData(document.model.central_id))
    qt_app.processEvents()
    assert document.model.nodes[child].parent_id == document.model.central_id
    document.undo()
    assert document.model == before


def test_ui_container_copy_paste_delete_undo_and_context(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    group = canvas.create_component("builtin.group_box", QPointF(32, 40))
    child = canvas.create_component("builtin.button", QPointF(72, 104))
    document.select(group)
    qt_app.processEvents()
    canvas.setFocus()
    window.edit_actions.copy()
    assert qt_app.clipboard().mimeData().hasFormat(TREE_MIME)
    assert len(read_component(window.registry).nodes) == 2
    before = document.model
    window.edit_actions.paste()
    copied = document.selected_id
    assert document.model.nodes[copied].parent_id == document.model.central_id
    assert len(subtree_ids(document.model, (copied,))) == 2
    window.edit_actions.delete()
    document.undo()
    assert copied in document.model.nodes
    document.undo()
    assert document.model == before
    document.select(child)
    qt_app.processEvents()
    point = canvas.mapFromScene(canvas.renderer.node_rect(child).center())
    menu = open_context(window, point)
    assert any(action.text() == "移入容器" for action in menu.actions())
    menu.close()


def test_incremental_build_preserves_reparented_child_before_parent_deletion(project: ProjectModel, registry: WidgetRegistry,
                                                                          qt_app: QApplication) -> None:
    project, keys = nested(project, registry)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "初始嵌套"))
        child = tree.widgets[keys[2]]
        updated = reparent_node(project, registry, keys[2], project.central_id)
        updated = delete_node(updated, keys[0])
        for _ in tree.apply_steps(compile_plan(updated, registry, "移出子控件并删除原容器")):
            # 分批构建会让出事件循环，父控件的延迟删除可能先于后续子控件处理。
            qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert tree.widgets[keys[2]] is child
        assert child.parentWidget() is tree.widgets[project.central_id]
        assert child.mapTo(tree.root, QPoint()) == QPoint(*absolute_position(updated, keys[2]))
    finally:
        tree.dispose()
