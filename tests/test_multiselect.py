"""多选、框选、整组移动、排版与剪贴板的模型及真实输入回归。"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pytest
from PySide6.QtCore import QEvent, QMimeData, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.arrange import ARRANGEMENTS, arrange_nodes, delete_nodes, move_nodes
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.group_clipboard import copy_group, decode_group, encode_group, paste_group
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import FrozenMap, ProjectModel, Rect, new_project
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.clipboard import GROUP_MIME
from tests.test_clipboard import activate, open_context


def populated(project: ProjectModel, registry: WidgetRegistry) -> tuple[ProjectModel, tuple[str, ...]]:
    keys = []
    for type_id, x, y in (("builtin.button", 40, 40), ("builtin.label", 240, 104), ("builtin.line_edit", 520, 184)):
        project, key = create_node(project, registry, type_id, x, y)
        keys.append(key)
    return project, tuple(keys)


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    previous = qt_app.clipboard().mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    result = MainWindow(registry, settings=QSettings(str(tmp_path / "多选.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    result.show()
    result.activateWindow()
    result.document.execute("布置控件", lambda model: populated(model, registry)[0])
    qt_app.processEvents()
    try:
        yield result
    finally:
        result.discard_all_for_test()
        result.close()
        result.deleteLater()
        if saved:
            restored = QMimeData()
            for key, data in saved.items():
                restored.setData(key, data)
            qt_app.clipboard().setMimeData(restored)
        else:
            qt_app.clipboard().clear()
        qt_app.processEvents()


def keys_of(window: MainWindow) -> tuple[str, ...]:
    return tuple(node.id for node in sorted(window.document.model.nodes.values(), key=lambda node: node.object_order)
                 if node.slot == "children")


def drag(window: MainWindow, start: QPoint, end: QPoint, *, release: bool = True,
         modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    canvas = window.page.canvas
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, modifiers, start)
    move = QMouseEvent(QEvent.Type.MouseMove, QPointF(end), QPointF(canvas.viewport().mapToGlobal(end)),
                      Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, modifiers)
    QApplication.sendEvent(canvas.viewport(), move)
    if release:
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, modifiers, end)


def test_selection_is_ephemeral_and_pruned(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = populated(project, registry)
    document = DocumentSession(project, registry, saved=True)
    document.select_many(keys)
    assert not document.dirty and document.history.cursor == 0
    assert document.selected_id == keys[-1]
    document.execute("删除一个", lambda model: delete_nodes(model, (keys[1],)))
    assert document.selected_ids == (keys[0], keys[2])
    document.undo()
    assert set(keys) <= set(document.model.nodes)
    document.select(project.root_id)
    assert document.selected_ids == (project.root_id,)


@pytest.mark.parametrize("zoom", [50, 100, 150])
def test_modifier_selection_and_tree_sync(window: MainWindow, qt_app: QApplication, zoom: int) -> None:
    canvas, document = window.page.canvas, window.document
    canvas.set_zoom(zoom)
    keys = keys_of(window)
    qt_app.processEvents()
    for key, modifier in zip(keys[:2], (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ControlModifier)):
        point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, modifier, point)
    qt_app.processEvents()
    assert document.selected_ids == keys[:2]
    assert {item.data(0, Qt.ItemDataRole.UserRole) for item in window.object_tree.selectedItems()} == set(keys[:2])
    assert "2 个控件" in window.properties.heading.text()
    assert not window.properties.editors
    assert not any(handle.isVisible() for handle in canvas.adornments.handles.values())
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
                     canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center()))
    assert document.selected_ids == (keys[1],)


@pytest.mark.parametrize("reverse", [False, True])
def test_marquee_complete_containment_and_additive(window: MainWindow, qt_app: QApplication, reverse: bool) -> None:
    canvas, document = window.page.canvas, window.document
    keys = keys_of(window)
    canvas.set_zoom(100)
    start, end = canvas.mapFromScene(QPointF(24, 24)), canvas.mapFromScene(QPointF(420, 150))
    before = document.model.to_bytes()
    drag(window, end if reverse else start, start if reverse else end)
    assert set(document.selected_ids) == set(keys[:2])
    assert document.model.to_bytes() == before
    start, end = canvas.mapFromScene(QPointF(500, 160)), canvas.mapFromScene(QPointF(740, 230))
    drag(window, start, end, modifiers=Qt.KeyboardModifier.ControlModifier)
    assert set(document.selected_ids) == set(keys)


@pytest.mark.parametrize("reason", ["escape", "deactivate", "revision", "selection"])
def test_marquee_cancel_preserves_selection(window: MainWindow, reason: str) -> None:
    canvas, document = window.page.canvas, window.document
    keys = keys_of(window)
    document.select_many(keys[:2])
    start, end = canvas.mapFromScene(QPointF(24, 24)), canvas.mapFromScene(QPointF(740, 240))
    drag(window, start, end, release=False)
    assert canvas.gesture_active
    if reason == "escape":
        QTest.keyClick(canvas, Qt.Key.Key_Escape)
    elif reason == "deactivate":
        QApplication.sendEvent(canvas, QEvent(QEvent.Type.WindowDeactivate))
    elif reason == "revision":
        document.execute("修改文本", lambda model: set_property(model, document.registry, keys[0], "text", "新标题"))
    else:
        document.select(keys[2])
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert document.selected_ids == ((keys[2],) if reason == "selection" else keys[:2])
    assert not canvas.gesture_active and not canvas.drop_outline.isVisible()


@pytest.mark.parametrize("zoom", [50, 100, 150, 200])
def test_group_drag_is_one_command_and_no_native_input(window: MainWindow, qt_app: QApplication, zoom: int) -> None:
    canvas, document = window.page.canvas, window.document
    keys = keys_of(window)[:2]
    document.select_many(keys)
    canvas.set_zoom(zoom)
    qt_app.processEvents()
    model, cursor = document.model, document.history.cursor
    start = canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center())
    end = start + QPoint(round(40 * zoom / 100), round(24 * zoom / 100))
    drag(window, start, end, release=False)
    assert document.model is model and document.history.cursor == cursor
    for key in keys:
        assert canvas.renderer.tree.widgets[key].x() == model.nodes[key].geometry.x
        assert canvas.renderer.items[key].pos().x() == model.nodes[key].geometry.x + 40
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert document.history.cursor == cursor + 1
    for key in keys:
        assert document.model.nodes[key].geometry.x == model.nodes[key].geometry.x + 40
        assert document.model.nodes[key].geometry.y == model.nodes[key].geometry.y + 24
    document.undo()
    assert document.model.to_bytes() == model.to_bytes()
    document.redo()
    assert document.history.cursor == cursor + 1


def test_group_drag_boundary_cancel_and_nudge(window: MainWindow) -> None:
    canvas, document = window.page.canvas, window.document
    keys = keys_of(window)
    document.select_many(keys)
    before = document.model
    start = canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center())
    drag(window, start, start - QPoint(800, 800), release=False)
    assert canvas._group.delta == (-40, -40)
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    assert document.model is before
    assert canvas.renderer.items[keys[0]].pos() == QPointF(40, 40)
    QTest.keyClick(canvas, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    for key in keys:
        assert document.model.nodes[key].geometry.x == before.nodes[key].geometry.x + 10


def test_tree_multiselect_and_text_select_all_isolation(window: MainWindow, qt_app: QApplication) -> None:
    keys = keys_of(window)
    tree = window.object_tree
    qt_app.processEvents()
    for key, modifier in zip(keys[:2], (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ControlModifier)):
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, modifier, tree.visualItemRect(tree._items[key]).center())
    assert set(window.document.selected_ids) == set(keys[:2])
    QTest.keyClick(tree, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert set(window.document.selected_ids) == set(keys)
    window.document.select(keys[0])
    window.properties.refresh()
    editor = window.properties.editors["text"]
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert editor.hasSelectedText() and window.document.selected_ids == (keys[0],)


@pytest.mark.parametrize("mode", list(ARRANGEMENTS))
def test_arrangement_is_atomic_and_roundtrips(project: ProjectModel, registry: WidgetRegistry,
                                             tmp_path: Path, mode: str) -> None:
    project, keys = populated(project, registry)
    document = DocumentSession(project, registry)
    anchor = project.nodes[keys[-1]].geometry
    if mode == "vertical":
        project = set_property(project, registry, keys[-1], "geometry.y", 400)
        document = DocumentSession(project, registry)
    document.execute("排版", lambda model: arrange_nodes(model, keys, mode, keys[-1]))
    assert document.history.cursor == 1
    rectangles = [document.model.nodes[key].geometry for key in keys]
    if mode == "left": assert all(rect.x == anchor.x for rect in rectangles)
    elif mode == "right": assert all(rect.x + rect.width == anchor.x + anchor.width for rect in rectangles)
    elif mode == "hcenter": assert all(abs(rect.x + rect.width / 2 - anchor.x - anchor.width / 2) <= 0.5 for rect in rectangles)
    elif mode == "top": assert all(rect.y == anchor.y for rect in rectangles)
    elif mode == "bottom": assert all(rect.y + rect.height == anchor.y + anchor.height for rect in rectangles)
    elif mode == "vcenter": assert all(abs(rect.y + rect.height / 2 - anchor.y - anchor.height / 2) <= 0.5 for rect in rectangles)
    elif mode in {"same_width", "same_height", "same_size"}:
        for key, rect in zip(keys, rectangles):
            original = project.nodes[key].geometry
            assert (rect.x, rect.y) == (original.x, original.y)
            assert rect.width == (original.width if mode == "same_height" else anchor.width)
            assert rect.height == (original.height if mode == "same_width" else anchor.height)
        assert document.model.nodes[keys[-1]].geometry == anchor
    else:
        horizontal = mode == "horizontal"
        gaps = [(b.x - a.x - a.width) if horizontal else (b.y - a.y - a.height) for a, b in zip(rectangles, rectangles[1:])]
        assert abs(gaps[0] - gaps[1]) <= 1
        assert rectangles[0] == project.nodes[keys[0]].geometry and rectangles[-1] == project.nodes[keys[-1]].geometry
    path = tmp_path / "排版.uipro"
    commit_project(path, document.model, expected_token=None)
    assert load_project(path).model.to_bytes() == document.model.to_bytes()
    document.undo()
    assert document.model.to_bytes() == project.to_bytes()
    document.redo()
    assert document.model.to_bytes() == load_project(path).model.to_bytes()


@pytest.mark.parametrize("mode, expected_sizes", [
    ("same_width", ((160, 40), (160, 24), (160, 32))),
    ("same_height", ((120, 24), (160, 24), (200, 24))),
    ("same_size", ((160, 24), (160, 24), (160, 24))),
])
@pytest.mark.parametrize("entry", ["menu", "canvas", "tree"])
def test_equal_size_actions_use_primary_and_update_canvas(window: MainWindow, qt_app: QApplication,
                                                          mode: str, expected_sizes: tuple, entry: str) -> None:
    document, canvas = window.document, window.page.canvas
    keys = keys_of(window)
    rectangles = (Rect(40, 40, 120, 40), Rect(240, 104, 160, 24), Rect(520, 184, 200, 32))
    document.execute("准备尺寸", lambda model: model.with_nodes({
        key: replace(model.nodes[key], geometry=rect) for key, rect in zip(keys, rectangles)}))
    document.select_many(keys, primary=keys[1])
    canvas.setFocus()
    qt_app.processEvents()
    window.edit_actions.refresh()
    before, cursor = document.model.to_bytes(), document.history.cursor
    menu = None
    if entry == "menu":
        action = window.actions["arrange_" + mode]
        assert action in window.edit_actions.arrange_menu.actions()
    else:
        menu = (open_context(window, canvas.renderer.node_rect(keys[0]).center()) if entry == "canvas"
                else open_context(window, tree_id=keys[0]))
        submenu = next(child for child in menu.findChildren(QMenu) if child.title() == "排版")
        action = next(item for item in submenu.actions() if item.objectName() == "arrange_" + mode)
    assert action.isEnabled() and action.text() == ARRANGEMENTS[mode]
    action.trigger()
    if menu is not None:
        menu.close()
    qt_app.processEvents()
    assert document.history.cursor == cursor + 1
    assert document.selected_ids == keys and document.selected_id == keys[1]
    for key, original, size in zip(keys, rectangles, expected_sizes):
        expected = (original.x, original.y, *size)
        assert document.model.nodes[key].geometry == Rect(*expected)
        assert canvas.renderer.tree.widgets[key].geometry().getRect() == expected
    after = document.model.to_bytes()
    document.undo()
    assert document.model.to_bytes() == before
    document.redo()
    assert document.model.to_bytes() == after
    cursor = document.history.cursor
    window.actions["arrange_" + mode].trigger()
    assert document.history.cursor == cursor


def test_equal_size_action_states(window: MainWindow) -> None:
    from app.command_palette import menu_commands

    document = window.document
    keys = keys_of(window)
    actions = [window.actions["arrange_" + mode] for mode in ("same_width", "same_height", "same_size")]
    commands = dict(menu_commands(window.menuBar()))
    for action in actions:
        assert commands["排版 › " + action.text()] is action
    window.page.canvas.setFocus()
    document.select(keys[0])
    window.edit_actions.refresh()
    assert all(not action.isEnabled() for action in actions)
    document.select_many(keys[:2])
    assert all(action.isEnabled() for action in actions)
    document.read_only = True
    document.status_changed.emit()
    assert all(not action.isEnabled() for action in actions)
    document.read_only = False
    document.editing_suspended = True
    document.status_changed.emit()
    assert all(not action.isEnabled() for action in actions)
    document.editing_suspended = False
    document.execute("锁定父容器", lambda model: model.with_nodes({model.central_id: replace(
        model.nodes[model.central_id], designer=model.nodes[model.central_id].designer.changed(locked=True))}))
    assert all(not action.isEnabled() for action in actions)


@pytest.mark.parametrize("mode", ["same_width", "same_height", "same_size"])
@pytest.mark.parametrize("nested", [False, True])
def test_equal_size_out_of_bounds_is_atomic(project: ProjectModel, registry: WidgetRegistry,
                                            mode: str, nested: bool) -> None:
    from core.hierarchy import content_size

    parent = project.central_id
    if nested:
        project, parent = create_node(project, registry, "builtin.group_box", 20, 20)
    keys = []
    for index in range(3):
        project, key = create_node(project, registry, "builtin.button", 0, 0, parent_id=parent)
        keys.append(key)
    width, height = content_size(project, parent)
    rectangles = (Rect(0, 0, 120, 80), Rect(10, 10, 40, 24), Rect(width - 40, height - 24, 40, 24))
    project = project.with_nodes({key: replace(project.nodes[key], geometry=rect) for key, rect in zip(keys, rectangles)})
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError, match="超出父容器"):
        document.execute("统一尺寸", lambda model: arrange_nodes(model, tuple(keys), mode, keys[0]))
    assert document.model is project and document.history.cursor == 0


@pytest.mark.parametrize("mode", ["same_width", "same_height", "same_size"])
def test_equal_size_rejects_layout_children_and_invalid_selection(project: ProjectModel, registry: WidgetRegistry,
                                                                  mode: str) -> None:
    project, layout = create_node(project, registry, "builtin.horizontal_layout", 20, 20)
    project, first = create_node(project, registry, "builtin.button", 0, 0, parent_id=layout)
    project, second = create_node(project, registry, "builtin.label", 0, 0, parent_id=layout)
    with pytest.raises(DesignerError, match="自动布局"):
        arrange_nodes(project, (first, second), mode, first)
    project, keys = populated(project, registry)
    for selection, primary, message in (((keys[0],), keys[0], "至少选择两个"),
                                        (keys[:2], keys[2], "基准"),
                                        ((keys[0], first), keys[0], "同一容器")):
        with pytest.raises(DesignerError, match=message):
            arrange_nodes(project, selection, mode, primary)


@pytest.mark.parametrize("mode", ["same_height", "same_size"])
def test_equal_size_component_minimum_failure_keeps_history(project: ProjectModel, registry: WidgetRegistry,
                                                            mode: str) -> None:
    project, keys = populated(project, registry)
    project, tab = create_node(project, registry, "builtin.tab_widget", 20, 280)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError, match="至少为六十四"):
        document.execute("统一尺寸", lambda model: arrange_nodes(model, (*keys, tab), mode, keys[0]))
    assert document.model is project and document.history.cursor == 0


def test_locked_batch_fails_without_partial_edits(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = populated(project, registry)
    node = project.nodes[keys[1]]
    project = project.with_nodes({node.id: replace(node, designer=node.designer.changed(locked=True))})
    document = DocumentSession(project, registry)
    for operation in (lambda model: delete_nodes(model, keys), lambda model: move_nodes(model, keys, 8, 8),
                      *(lambda model, mode=mode: arrange_nodes(model, keys, mode, keys[0])
                        for mode in ("top", "same_width", "same_height", "same_size"))):
        with pytest.raises(DesignerError, match="锁定"):
            document.execute("不应部分修改", operation)
        assert document.model is project and document.history.cursor == 0


def test_group_context_copy_cross_document_paste_delete_undo(window: MainWindow, qt_app: QApplication) -> None:
    keys = keys_of(window)
    source = window.document.model
    window.document.select_many(keys)
    canvas = window.page.canvas
    menu = open_context(window, canvas.renderer.node_rect(keys[0]).center())
    assert set(window.document.selected_ids) == set(keys)
    activate(menu, "copy")
    assert qt_app.clipboard().mimeData().hasFormat(GROUP_MIME)
    destination = window.new_document()
    window.page.canvas.setFocus()
    window.actions["paste"].trigger()
    pasted = destination.selected_ids
    assert len(pasted) == 3 and destination.history.cursor == 1
    for first, second in zip(keys, pasted):
        assert destination.model.nodes[second].geometry.x == source.nodes[first].geometry.x + 16
    cursor = destination.history.cursor
    window.actions["delete"].trigger()
    assert not set(pasted) & set(destination.model.nodes) and destination.history.cursor == cursor + 1
    destination.undo()
    assert set(pasted) <= set(destination.model.nodes)
    destination.undo()
    assert len(destination.model.nodes) == 2


def test_internal_connections_shared_handlers_and_order_survive(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = populated(project, registry)
    handler = keys[0]  # 控件和处理函数分别使用自己的标识空间。
    connections = [FrozenMap({"id": str(uuid4()), "source_id": key, "event": "clicked",
                             "target": {"kind": "handler", "handler_id": handler}, "arguments": []}) for key in keys[:2]]
    connections.append(FrozenMap({"id": str(uuid4()), "source_id": keys[0], "event": "clicked",
                                  "target": {"kind": "slot", "node_id": keys[1], "slot": "clear"}, "arguments": []}))
    project = replace(project, data=project.data.changed(connections=connections,
                      handlers=[{"id": handler, "code_name": "on_click", "name": "被单击", "parameters": []}],
                      tab_order=[keys[1], keys[0]]))
    first, second = project.nodes[keys[0]], project.nodes[keys[1]]
    project = project.with_nodes({first.id: replace(first, stack_order=1), second.id: replace(second, stack_order=0)})
    fragment = decode_group(encode_group(copy_group(project, registry, keys[:2])), registry)
    pasted, created = paste_group(new_project(), registry, fragment, position=(780, 550))
    validate_project(pasted)
    assert len(pasted.data["handlers"]) == 1 and len(pasted.data["connections"]) == 3
    assert pasted.data["tab_order"] == (created[1], created[0])
    assert pasted.nodes[created[0]].stack_order > pasted.nodes[created[1]].stack_order
    assert pasted.nodes[created[1]].geometry.x - pasted.nodes[created[0]].geometry.x == 200
    targets = pasted.data["connections"]
    assert targets[0]["target"]["handler_id"] == targets[1]["target"]["handler_id"]
    assert targets[2]["target"]["node_id"] == created[1] and targets[0]["source_id"] == created[0]
    single, key = paste_fragment(new_project(), registry, copy_fragment(project, registry, keys[0]))
    validate_project(single)
    assert single.data["connections"][0]["source_id"] == key


@pytest.mark.parametrize("change", ["extra", "duplicate", "external", "version", "extension"])
def test_corrupt_group_clipboard_is_rejected(project: ProjectModel, registry: WidgetRegistry, change: str) -> None:
    project, keys = populated(project, registry)
    value = json.loads(encode_group(copy_group(project, registry, keys)))
    if change == "extra": value["unknown"] = True
    elif change == "duplicate": value["nodes"][1]["id"] = value["nodes"][0]["id"]
    elif change == "external": value["tab_order"] = [str(uuid4())]
    elif change == "version": value["version"] = True
    else: value["nodes"][0]["extensions"] = {"future": "不能丢失"}
    with pytest.raises(DesignerError):
        decode_group(json.dumps(value).encode("utf-8"), registry)


def test_paste_too_large_group_does_not_distort(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, keys = populated(project, registry)
    fragment = copy_group(project, registry, keys)
    destination = new_project()
    destination = set_property(destination, registry, destination.root_id, "geometry.width", 300)
    with pytest.raises(DesignerError, match="大于目标窗口"):
        paste_group(destination, registry, fragment)


def test_tree_shift_range_and_inspector_summary(window: MainWindow, qt_app: QApplication) -> None:
    keys = keys_of(window)
    tree = window.object_tree
    qt_app.processEvents()
    for key, modifier in ((keys[0], Qt.KeyboardModifier.NoModifier), (keys[2], Qt.KeyboardModifier.ShiftModifier)):
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, modifier, tree.visualItemRect(tree._items[key]).center())
    assert set(window.document.selected_ids) == set(keys)
    window.properties.refresh()
    assert window.properties.tree.topLevelItemCount() == 3
    window.properties.search.setText("单行编辑框")
    assert sum(not window.properties.tree.topLevelItem(i).isHidden() for i in range(3)) == 1
    window.document.select(keys[0])
    window.properties.refresh()
    assert window.properties.tree.headerItem().text(0) == "属性"
    assert window.properties.editors["text"].isEnabled()


def test_pending_invalid_property_blocks_multi_selection(window: MainWindow, qt_app: QApplication) -> None:
    keys = keys_of(window)
    document, canvas = window.document, window.page.canvas
    document.select(keys[0])
    window.properties.refresh()
    editor = window.properties.editors["name"]
    editor.setText("")
    editor.setModified(True)
    editor.setFocus()
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
                     canvas.mapFromScene(canvas.renderer.node_rect(keys[1]).center()))
    assert document.selected_ids == (keys[0],)
    assert window.properties.validation_message.isVisible()


def test_menu_rejects_changed_alignment_anchor(window: MainWindow) -> None:
    keys = keys_of(window)
    document = window.document
    document.select_many(keys, primary=keys[0])
    menu = open_context(window, window.page.canvas.renderer.node_rect(keys[0]).center())
    document.select_many(keys, primary=keys[1])
    before = document.model.to_bytes()
    action = next(action for action in menu.actions() if action.objectName() == "delete")
    action.trigger()
    assert document.model.to_bytes() == before
    assert "菜单对应的设计内容已变化" in window.output.toPlainText()
    menu.close()


@pytest.mark.parametrize("mode", ["right", "horizontal"])
def test_impossible_arrangement_does_not_partially_apply(project: ProjectModel, registry: WidgetRegistry, mode: str) -> None:
    project, keys = populated(project, registry)
    if mode == "horizontal":
        for key in keys:
            project = set_property(project, registry, key, "geometry.x", 0)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("排版", lambda model: arrange_nodes(model, keys, mode, keys[0]))
    assert document.model is project and document.history.cursor == 0


def test_read_only_multi_selection_allows_copy_without_move(window: MainWindow) -> None:
    document, canvas = window.document, window.page.canvas
    keys = keys_of(window)
    document.select_many(keys)
    document.read_only = True
    document.status_changed.emit()
    before = document.model.to_bytes()
    start = canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center())
    drag(window, start, start + QPoint(40, 24))
    assert document.model.to_bytes() == before
    copyable, _, deletable = window.edit_actions.node_states()
    assert copyable and not deletable
    assert not window.actions["arrange_left"].isEnabled()
