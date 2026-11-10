"""剪贴板命令、右键命中、快捷键作用域及删除恢复回归。"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.clipboard import MAX_CLIPBOARD_BYTES, copy_fragment, decode_fragment, encode_fragment, paste_fragment
from core.commands.nodes import create_node, delete_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import FrozenMap, ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.clipboard import WIDGET_MIME, has_component, read_component


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    previous = qt_app.clipboard().mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    qt_app.clipboard().clear()
    result = MainWindow(registry, settings=QSettings(str(tmp_path / "剪贴板设置.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    result.show()
    result.activateWindow()
    QTest.qWait(20)
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


def add_button(window: MainWindow, position: QPointF = QPointF(48, 48)) -> str:
    key = window.page.canvas.create_component("builtin.button", position)
    QApplication.processEvents()
    return key


def open_context(window: MainWindow, position: QPointF | None = None, *, tree_id: str | None = None) -> QMenu:
    if tree_id is not None:
        view = window.object_tree
        point = view.visualItemRect(view._items[tree_id]).center()
    else:
        view = window.page.canvas
        point = view.mapFromScene(position) if position is not None else QPoint(20, 20)
    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, view.viewport().mapToGlobal(point))
    QApplication.sendEvent(view.viewport(), event)
    QApplication.processEvents()
    assert window.edit_actions.menu is not None and window.edit_actions.menu.isVisible()
    return window.edit_actions.menu


def activate(menu: QMenu, key: str) -> None:
    action = next(item for item in menu.actions() if item.objectName() == key)
    assert action.isEnabled(), key
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(action).center())
    QApplication.processEvents()


def test_paste_clones_values_and_is_single_undoable_command(project: ProjectModel, registry: WidgetRegistry,
                                                          tmp_path: Path) -> None:
    project, source = create_node(project, registry, "builtin.button", 40, 48)
    for key, value in (("text", "确认订单"), ("background_color", "#d0e0d0"), ("font_size", 16), ("checkable", True)):
        project = set_property(project, registry, source, key, value)
    fragment = decode_fragment(encode_fragment(copy_fragment(project, registry, source)), registry)
    candidate, copied = paste_fragment(project, registry, fragment)
    validate_project(candidate)
    assert candidate.nodes[copied].properties == project.nodes[source].properties
    assert candidate.nodes[copied].geometry.x == 56 and candidate.nodes[copied].geometry.y == 64
    assert candidate.nodes[copied].name != project.nodes[source].name
    assert candidate.nodes[copied].code_name != project.nodes[source].code_name
    document = DocumentSession(project, registry)
    document.execute("粘贴控件", lambda _: candidate)
    assert document.history.cursor == 1
    document.undo()
    assert document.model.to_bytes() == project.to_bytes()
    document.redo()
    assert document.model.to_bytes() == candidate.to_bytes()
    path = tmp_path / "复制后.uipro"
    commit_project(path, document.model, expected_token=None)
    assert load_project(path).model.to_bytes() == candidate.to_bytes()


def test_paste_remaps_handlers_self_connections_and_omits_external(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, source = create_node(project, registry, "builtin.button", 40, 40)
    project, label = create_node(project, registry, "builtin.label", 40, 100)
    handler_id = str(uuid4())
    connections = [dict(id=str(uuid4()), source_id=source, event="clicked", target=target, arguments=[], enabled=True)
                   for target in ({"kind": "handler", "handler_id": handler_id},
                                  {"kind": "slot", "node_id": source, "slot": "setEnabled"},
                                  {"kind": "slot", "node_id": label, "slot": "setText"})]
    project = replace(project, data=project.data.changed(connections=connections,
                      handlers=[{"id": handler_id, "code_name": "on_confirm", "parameters": []}], tab_order=[source]))
    fragment = copy_fragment(project, registry, source)
    assert fragment.omitted_connections == 1 and len(fragment.connections) == 2
    target = ProjectModel.from_dict(project.to_dict())
    result, key = paste_fragment(target, registry, fragment)
    validate_project(result)
    new_handler = result.data["handlers"][-1]
    assert new_handler["id"] != handler_id and new_handler["code_name"] != "on_confirm"
    first, second = result.data["connections"][-2:]
    assert first["source_id"] == key and first["target"]["handler_id"] == new_handler["id"]
    assert second["source_id"] == key and second["target"]["node_id"] == key
    assert result.data["tab_order"] == (source, key)
    document = DocumentSession(result, registry)
    document.execute("删除控件", lambda model: delete_node(model, key))
    assert len(document.model.data["connections"]) == 3
    assert document.model.data["tab_order"] == (source,)
    document.undo()
    assert document.model.to_bytes() == result.to_bytes()


@pytest.mark.parametrize("data", [b"invalid", b"[]", b"\xff", b'{"format":"uiplay-component","version":true}',
                                 b'{"format":"uiplay-component","version":1,"connections":[null],"handlers":[]}'])
def test_invalid_clipboard_reports_chinese(data: bytes, registry: WidgetRegistry) -> None:
    with pytest.raises(DesignerError):
        decode_fragment(data, registry)


@pytest.mark.parametrize("arguments", [None, False, 2, "参数", {}])
def test_copy_rejects_non_array_event_arguments(project: ProjectModel, registry: WidgetRegistry, arguments: object) -> None:
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    connection = {"id": str(uuid4()), "source_id": key, "event": "clicked", "enabled": True,
                  "target": {"kind": "slot", "node_id": key, "slot": "setEnabled"}, "arguments": arguments}
    project = replace(project, data=project.data.changed(connections=[connection]))
    with pytest.raises(DesignerError, match="参数"):
        copy_fragment(project, registry, key)


@pytest.mark.parametrize("field", ["duplicate", "unknown"])
def test_clipboard_does_not_silently_discard_fields(project: ProjectModel, registry: WidgetRegistry, field: str) -> None:
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    data = encode_fragment(copy_fragment(project, registry, key))
    if field == "duplicate":
        data = b'{"version": 99,' + data[1:]
    else:
        value = json.loads(data)
        value["external_references"] = ["不应丢弃的扩展"]
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
    with pytest.raises(DesignerError):
        decode_fragment(data, registry)


def test_clipboard_rejects_oversized_data(registry: WidgetRegistry) -> None:
    with pytest.raises(DesignerError, match="过大"):
        decode_fragment(b"x" * (MAX_CLIPBOARD_BYTES + 1), registry)


@pytest.mark.parametrize("case", ["root", "unknown", "version", "extension", "property", "layout"])
def test_unsupported_copy_does_not_lose_data(project: ProjectModel, registry: WidgetRegistry, case: str) -> None:
    project, key = create_node(project, registry, "builtin.button", 20, 20)
    node = project.nodes[key]
    changes = {"unknown": {"type_id": "plugin.unknown"}, "version": {"type_version": 8},
               "extension": {"extensions": FrozenMap({"resource_id": str(uuid4())})},
               "property": {"properties": node.properties.changed(image_id=str(uuid4()))},
               "layout": {"layout_item": FrozenMap({"index": 0})}}
    if case != "root":
        project = project.with_nodes({key: replace(node, **changes[case])})
    before = project.to_bytes()
    with pytest.raises(DesignerError):
        copy_fragment(project, registry, project.root_id if case == "root" else key)
    assert project.to_bytes() == before


def test_paste_snaps_to_click_and_clamps_to_window(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, source = create_node(project, registry, "builtin.button", 0, 0)
    fragment = copy_fragment(project, registry, source)
    first, key = paste_fragment(project, registry, fragment, position=(103, 139))
    assert (first.nodes[key].geometry.x, first.nodes[key].geometry.y) == (104, 136)
    second, key = paste_fragment(first, registry, fragment, position=(99999, -100))
    assert (second.nodes[key].geometry.x, second.nodes[key].geometry.y) == (680, 0)


def test_right_click_selects_target_deletes_and_undo_restores(window: MainWindow) -> None:
    first = add_button(window)
    second = add_button(window, QPointF(240, 48))
    document, canvas = window.document, window.page.canvas
    before = document.model.to_bytes()
    menu = open_context(window, canvas.renderer.node_rect(first).center())
    assert document.selected_id == first and window.object_tree.currentItem().text(0) == document.model.nodes[first].name
    activate(menu, "delete")
    assert first not in document.model.nodes and second in document.model.nodes
    assert first not in canvas.renderer.items and first not in window.object_tree._items
    assert window.properties._node_id == document.model.root_id
    window.actions["undo"].trigger()
    QApplication.processEvents()
    assert document.model.to_bytes() == before and first in canvas.renderer.items


@pytest.mark.parametrize("zoom", [50, 100, 150, 200])
def test_context_paste_uses_scene_coordinates(window: MainWindow, zoom: int) -> None:
    source = add_button(window)
    canvas = window.page.canvas
    canvas.set_zoom(zoom)
    window.edit_actions.copy()
    canvas.centerOn(280, 200)
    menu = open_context(window, QPointF(296, 200))
    assert not next(item for item in menu.actions() if item.objectName() == "delete").isEnabled()
    activate(menu, "paste")
    pasted = window.document.model.nodes[window.document.selected_id]
    assert pasted.id != source and (pasted.geometry.x, pasted.geometry.y) == (296, 200)


def test_shortcuts_repeat_paste_and_cross_documents(window: MainWindow) -> None:
    source = add_button(window)
    canvas, original = window.page.canvas, window.document
    QTest.keyClick(canvas, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert has_component()
    for offset in (16, 32):
        QTest.keyClick(canvas, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        QApplication.processEvents()
        assert window.document.model.nodes[window.document.selected_id].geometry.x == 48 + offset
    assert len({node.name for node in original.model.nodes.values()}) == len(original.model.nodes)
    latest = original.selected_id
    QTest.keyClick(canvas, Qt.Key.Key_Delete)
    QApplication.processEvents()
    assert latest not in original.model.nodes and source in original.model.nodes
    other = window.new_document()
    window.page.canvas.setFocus()
    QTest.keyClick(window.page.canvas, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    assert len(other.model.nodes) == 3 and other.selected_id != source
    assert other.model.nodes[other.selected_id].parent_id == other.model.central_id


def test_object_tree_context_and_delete_shortcut(window: MainWindow) -> None:
    first = add_button(window)
    add_button(window, QPointF(240, 48))
    menu = open_context(window, tree_id=first)
    assert window.document.selected_id == first
    activate(menu, "copy")
    assert read_component(window.registry).node.id == first
    window.object_tree.setFocus()
    QTest.keyClick(window.object_tree, Qt.Key.Key_Delete)
    QApplication.processEvents()
    assert first not in window.document.model.nodes


def test_text_shortcuts_only_edit_text(window: MainWindow) -> None:
    key = add_button(window)
    snapshot = window.document.model.to_bytes()
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    QTest.keyClick(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert QApplication.clipboard().text() == "按钮1" and not has_component()
    QTest.keyClick(editor, Qt.Key.Key_Delete)
    QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    assert editor.text() == "按钮1" and key in window.document.model.nodes
    assert window.document.model.to_bytes() == snapshot
    editor.selectAll()
    window.actions["copy"].trigger()
    window.actions["delete"].trigger()
    assert editor.text() == "" and key in window.document.model.nodes


def test_root_readonly_and_locked_menu_states(window: MainWindow) -> None:
    key = add_button(window)
    document = window.document
    document.execute("锁定", lambda model: model.with_nodes({key: replace(model.nodes[key],
                     designer=model.nodes[key].designer.changed(locked=True))}))
    menu = open_context(window, window.page.canvas.renderer.node_rect(key).center())
    assert not next(item for item in menu.actions() if item.objectName() == "delete").isEnabled()
    activate(menu, "copy")
    document.read_only = True
    document.status_changed.emit()
    menu = open_context(window, QPointF(360, 320))
    assert all(not item.isEnabled() for item in menu.actions() if item.objectName() in {"copy", "paste", "delete"})
    menu.close()
    assert key in document.model.nodes


def test_malformed_clipboard_paste_changes_neither_history_nor_model(window: MainWindow) -> None:
    add_button(window)
    document = window.document
    before, cursor = document.model.to_bytes(), document.history.cursor
    mime = QMimeData()
    mime.setData(WIDGET_MIME, b"not json")
    QApplication.clipboard().setMimeData(mime)
    QApplication.processEvents()
    window.actions["paste"].trigger()
    assert document.model.to_bytes() == before and document.history.cursor == cursor
    assert "剪贴板" in window.output.toPlainText()


def test_context_menu_does_not_delete_from_switched_document(window: MainWindow) -> None:
    key = add_button(window)
    old = window.document
    menu = open_context(window, window.page.canvas.renderer.node_rect(key).center())
    action = next(item for item in menu.actions() if item.objectName() == "delete")
    current = window.new_document()
    action.trigger()
    assert key in old.model.nodes and len(current.model.nodes) == 2
    assert "已变化" in window.output.toPlainText()


def test_keyboard_context_menu_uses_selected_object(window: MainWindow) -> None:
    key = add_button(window)
    canvas = window.page.canvas
    event = QContextMenuEvent(QContextMenuEvent.Reason.Keyboard, QPoint(), QPoint())
    QApplication.sendEvent(canvas.viewport(), event)
    QApplication.processEvents()
    assert window.document.selected_id == key
    activate(window.edit_actions.menu, "delete")
    assert key not in window.document.model.nodes


def test_paste_rejected_by_history_budget_leaves_redo_intact(window: MainWindow) -> None:
    add_button(window)
    window.edit_actions.copy()
    document = window.document
    document.undo()
    before, cursor = document.model.to_bytes(), document.history.cursor
    document.history.budget_bytes = 1
    window.page.canvas.setFocus()
    window.actions["paste"].trigger()
    assert document.model.to_bytes() == before and document.history.cursor == cursor and document.history.can_redo


def test_copy_pending_text_and_invalid_property_keeps_menu_closed(window: MainWindow) -> None:
    key = add_button(window)
    text = window.properties.editors["text"]
    text.setFocus()
    text.selectAll()
    text.insert("未按回车的标题")
    menu = open_context(window, window.page.canvas.renderer.node_rect(key).center())
    activate(menu, "copy")
    assert read_component(window.registry).node.properties["text"] == "未按回车的标题"
    editor = window.properties.editors["name"]
    editor.setFocus()
    editor.selectAll()
    editor.insert(" ")
    canvas = window.page.canvas
    point = canvas.mapFromScene(QPointF(400, 300))
    QApplication.sendEvent(canvas.viewport(), QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point,
                                                               canvas.viewport().mapToGlobal(point)))
    assert window.edit_actions.menu is None and window.document.selected_id == key


def test_source_document_can_close_before_pasting_label(window: MainWindow) -> None:
    source = window.document
    key = window.page.canvas.create_component("builtin.label", QPointF(32, 80))
    source.execute("标签属性", lambda model: set_property(model, window.registry, key, "text", "复制说明文字"))
    QApplication.processEvents()
    window.page.canvas.setFocus()
    window.edit_actions.copy()
    target = window.new_document()
    window._close_document(source)
    window.page.canvas.setFocus()
    window.edit_actions.paste()
    assert source.closed
    pasted = target.model.nodes[target.selected_id]
    assert pasted.type_id == "builtin.label" and pasted.properties["text"] == "复制说明文字"


def test_empty_clipboard_menu_disables_paste_and_cancel_is_no_edit(window: MainWindow) -> None:
    key = add_button(window)
    before, cursor = window.document.model.to_bytes(), window.document.history.cursor
    menu = open_context(window, window.page.canvas.renderer.node_rect(key).center())
    assert not next(item for item in menu.actions() if item.objectName() == "paste").isEnabled()
    QTest.keyClick(menu, Qt.Key.Key_Escape)
    QApplication.processEvents()
    assert window.edit_actions.menu is None
    assert window.document.model.to_bytes() == before and window.document.history.cursor == cursor


def test_pasted_controls_appear_in_independent_preview(window: MainWindow, qt_app: QApplication) -> None:
    from tests.test_preview import await_ready

    add_button(window)
    window.edit_actions.copy()
    window.edit_actions.paste()
    window.preview_current()
    await_ready(window.preview_service, qt_app)
    assert window.preview_service.last_ready["widget_count"] == 4


def test_edit_menu_with_text_focus_never_deletes_component(window: MainWindow) -> None:
    key = add_button(window)
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    menu_actions = window.menuBar().actions()
    edit_action = next(action for action in menu_actions if action.text() == "编辑")
    menu = edit_action.menu()
    menu.popup(editor.mapToGlobal(QPoint(0, editor.height())))
    QApplication.processEvents()
    action = window.actions["delete"]
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(action).center())
    assert editor.text() == "" and key in window.document.model.nodes
