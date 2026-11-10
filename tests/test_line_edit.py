"""单行编辑框的属性一致性、画布编辑、文件往返与真实预览回归。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from typing import Iterator

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QContextMenuEvent, QDropEvent, QInputMethodEvent, QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QToolButton

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, decode_fragment, encode_fragment, paste_fragment
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel
from core.events import set_event_enabled
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.canvas import DesignerCanvas
from designer.mime import component_mime
from preview.protocol import preview_plan
from preview.service import PreviewService
from runtime.builder import ECHO_MODES, RuntimeTree, verify_registry
from runtime.preview import PreviewRuntime
from tests.test_canvas import mouse_move
from tests.test_storage import wait_for


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    previous = qt_app.clipboard().mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    result = MainWindow(registry, enable_recovery=False, persist_settings=False,
                        settings=QSettings(str(tmp_path / "编辑框设置.ini"), QSettings.Format.IniFormat))
    result.show()
    result.activateWindow()
    qt_app.processEvents()
    try:
        yield result
    finally:
        result.discard_all_for_test()
        result.close()
        result.deleteLater()
        if saved:
            restored = QMimeData()
            for key, value in saved.items():
                restored.setData(key, value)
            qt_app.clipboard().setMimeData(restored)
        else:
            qt_app.clipboard().clear()
        qt_app.processEvents()


def test_registered_editor_starts_empty_with_placeholder(project: ProjectModel, registry: WidgetRegistry,
                                                        qt_app: QApplication) -> None:
    verify_registry(registry)
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    node = project.nodes[key]
    assert node.name == "单行编辑框1" and node.code_name == "line_edit_1"
    assert node.properties["text"] == "" and node.properties["placeholder_text"] == "请输入内容"
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "编辑框默认值"))
        native = tree.widgets[key]
        assert isinstance(native, QLineEdit)
        assert native.text() == "" and native.placeholderText() == "请输入内容"
        assert native.maxLength() == 32767 and native.hasFrame() and native.isClearButtonEnabled()
        assert not native.isReadOnly() and native.echoMode() == QLineEdit.EchoMode.Normal
        assert tree.image(key, 1.0).pixelColor(100, 16).alpha() > 0
    finally:
        tree.dispose()


@pytest.mark.parametrize("mode", list(ECHO_MODES))
def test_echo_modes_match_in_canvas_and_preview(project: ProjectModel, registry: WidgetRegistry,
                                                qt_app: QApplication, mode: str) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    project = set_property(project, registry, key, "text", "初始内容")
    project = set_property(project, registry, key, "echo_mode", mode)
    canvas = DesignerCanvas(DocumentSession(project, registry))
    preview = PreviewRuntime(registry)
    try:
        preview.show(preview_plan(project, registry, "显示方式"), project)
        for native in (canvas.renderer.tree.widgets[key], preview.tree.widgets[key]):
            assert native.echoMode() == ECHO_MODES[mode]
            assert native.text() == "初始内容"
            if mode == "normal":
                assert native.displayText() == "初始内容"
            elif mode == "no_echo":
                assert native.displayText() == ""
            else:
                assert native.displayText() != "初始内容"
    finally:
        preview.dispose()
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("member,value", [("max_length", -1), ("max_length", True), ("max_length", 32768),
                                        ("echo_mode", "invalid"), ("read_only", "是"),
                                        ("text", "第一行\n第二行"), ("text", "第一行\r第二行"),
                                        ("text", "甲\u2028乙"), ("text", "甲\u2029乙")])
def test_invalid_properties_preserve_history_and_model(project: ProjectModel, registry: WidgetRegistry,
                                                      member: str, value: object) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("无效属性", lambda model: set_property(model, registry, key, member, value))
    assert document.model is project and document.history.cursor == 0


def test_length_validation_matches_qt_and_undo_restores_untruncated_text(project: ProjectModel,
                                                                      registry: WidgetRegistry,
                                                                      qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    project = set_property(project, registry, key, "text", "初始文字")
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    try:
        with pytest.raises(DesignerError, match="最大长度"):
            document.execute("错误限制", lambda model: set_property(model, registry, key, "max_length", 2))
        assert document.model is project
        document.execute("缩短内容与长度", lambda model: set_property(
            set_property(model, registry, key, "text", "短文"), registry, key, "max_length", 2))
        assert canvas.renderer.tree.widgets[key].text() == "短文"
        document.undo()
        assert canvas.renderer.tree.widgets[key].text() == "初始文字"
        assert document.model == project
        document.redo()
        assert canvas.renderer.tree.widgets[key].text() == "短文"
        document.execute("扩展字符", lambda model: set_property(model, registry, key, "text", "\U00020000"))
        assert canvas.renderer.tree.widgets[key].text() == "\U00020000"
        with pytest.raises(DesignerError, match="最大长度"):
            document.execute("扩展字符超限", lambda model: set_property(model, registry, key, "max_length", 1))
    finally:
        canvas.dispose()
        canvas.close()


def test_editor_cannot_be_used_as_container(project: ProjectModel, registry: WidgetRegistry) -> None:
    project, editor = create_node(project, registry, "builtin.line_edit", 40, 48)
    project, label = create_node(project, registry, "builtin.label", 40, 100)
    node = replace(project.nodes[label], parent_id=editor, object_order=0, stack_order=0)
    with pytest.raises(DesignerError, match="容纳子控件"):
        validate_project(project.with_nodes({label: node}))


def test_design_cache_captures_clear_button_at_final_animation_frame(project: ProjectModel, registry: WidgetRegistry,
                                                                   qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "空编辑框"))
        project = set_property(project, registry, key, "text", "已有内容")
        tree.apply(compile_plan(project, registry, "显示清除按钮"))
        immediate = tree.image(key, 1.0)
        QTest.qWait(200)
        settled = tree.image(key, 1.0)
        assert immediate == settled
        project = set_property(project, registry, key, "clear_button", False)
        tree.apply(compile_plan(project, registry, "隐藏清除按钮"))
        hidden = tree.image(key, 1.0)
        assert any(immediate.pixel(x, y) != hidden.pixel(x, y)
                   for x in range(170, 195) for y in range(5, 27))
    finally:
        tree.dispose()


def test_all_properties_survive_copy_file_roundtrip_and_native_build(project: ProjectModel, registry: WidgetRegistry,
                                                                  qt_app: QApplication, tmp_path: Path) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    properties = {"text": "初始内容", "placeholder_text": "填写名称", "max_length": 20, "read_only": True,
                  "echo_mode": "password", "clear_button": False, "frame": False, "alignment": "right_vcenter",
                  "background_color": "#fff0df", "foreground_color": "#223344", "font_size": 14, "enabled": True,
                  "visible": True, "tool_tip": "填写用户名称", "font_family": "Microsoft YaHei UI"}
    for member, value in properties.items():
        project = set_property(project, registry, key, member, value)
    fragment = decode_fragment(encode_fragment(copy_fragment(project, registry, key)), registry)
    candidate, copied = paste_fragment(project, registry, fragment)
    assert copied != key and candidate.nodes[copied].properties == candidate.nodes[key].properties
    path = tmp_path / "编辑框.uipro"
    commit_project(path, candidate, expected_token=None)
    loaded = load_project(path).model
    assert loaded == candidate
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(loaded, registry, "编辑框文件往返"))
        native = tree.widgets[copied]
        assert native.text() == "初始内容" and native.maxLength() == 20 and native.isReadOnly()
        assert native.placeholderText() == "填写名称" and native.toolTip() == "填写用户名称"
        assert not native.hasFrame() and not native.isClearButtonEnabled()
        assert native.alignment() == Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        assert native.font().pointSize() == 14
        assert native.palette().color(QPalette.ColorRole.Base).name() == "#fff0df"
        assert native.palette().color(QPalette.ColorRole.Text).name() == "#223344"
    finally:
        tree.dispose()


def test_toolbox_search_double_click_and_mime_drop(window: MainWindow, qt_app: QApplication) -> None:
    toolbox, canvas = window.toolbox, window.page.canvas
    toolbox.search.setText("单行编辑框")
    items = [toolbox.tree.topLevelItem(i).child(j) for i in range(toolbox.tree.topLevelItemCount())
             for j in range(toolbox.tree.topLevelItem(i).childCount())]
    visible = [item for item in items if not item.isHidden()]
    assert len(visible) == 1 and visible[0].text(0) == "编辑框"
    toolbox.tree.itemDoubleClicked.emit(visible[0], 0)
    qt_app.processEvents()
    assert window.document.model.nodes[window.document.selected_id].type_id == "builtin.line_edit"
    point = canvas.mapFromScene(QPointF(104, 136))
    mime = component_mime("builtin.line_edit")
    event = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    canvas.dropEvent(event)
    qt_app.processEvents()
    assert event.isAccepted()
    node = window.document.model.nodes[window.document.selected_id]
    assert (node.geometry.x, node.geometry.y) == (104, 136)
    assert node.properties["text"] == ""
    assert window.object_tree.currentItem().text(1) == "单行编辑框"


def test_editor_uses_designer_gestures_and_context_actions(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    key = canvas.create_component("builtin.line_edit", QPointF(48, 48))
    qt_app.processEvents()
    text = window.properties.editors["text"]
    text.setFocus()
    text.insert("输入框初始文本")
    QTest.keyClick(text, Qt.Key.Key_Return)
    qt_app.processEvents()
    native = canvas.renderer.tree.widgets[key]
    edited = QSignalSpy(native.textEdited)
    point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
    target = point + QPoint(40, 24)
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    mouse_move(canvas, target)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
    assert edited.count() == 0 and not native.hasFocus()
    assert document.model.nodes[key].geometry.x > 48
    grip = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=grip)
    mouse_move(canvas, grip + QPoint(32, 16))
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=grip + QPoint(32, 16))
    assert document.model.nodes[key].geometry.width > 200
    before = document.model.to_bytes()
    point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
    QApplication.sendEvent(canvas.viewport(), QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point,
                                                               canvas.viewport().mapToGlobal(point)))
    menu = window.edit_actions.menu
    copy_action = next(action for action in menu.actions() if action.objectName() == "copy")
    assert copy_action.isEnabled()
    copy_action.trigger()
    menu.close()
    canvas.setFocus()
    QTest.keyClick(canvas, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    copied = document.selected_id
    assert copied != key and document.model.nodes[copied].properties["text"] == "输入框初始文本"
    QTest.keyClick(canvas, Qt.Key.Key_Delete)
    assert document.model.to_bytes() == before
    QTest.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert copied in document.model.nodes


def test_preview_input_clear_readonly_and_events_do_not_modify_design(project: ProjectModel, registry: WidgetRegistry,
                                                                     qt_app: QApplication) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    project = set_property(project, registry, key, "max_length", 8)
    for event in ("textChanged", "returnPressed", "editingFinished"):
        project = set_event_enabled(project, registry, key, event, True)
    preview = PreviewRuntime(registry)
    notices = QSignalSpy(preview.notice)
    before = project.to_bytes()
    try:
        preview.show(preview_plan(project, registry, "输入检查"), project)
        native = preview.tree.widgets[key]
        native.setFocus()
        committed = QInputMethodEvent()
        committed.setCommitString("中文输入")
        QApplication.sendEvent(native, committed)
        assert native.text() == "中文输入"
        QTest.keyClick(native, Qt.Key.Key_Return)
        assert all(any(event in notices.at(i)[0] for i in range(notices.count()))
                   for event in ("文本改变", "按下回车", "编辑完成"))
        assert all("中文输入" not in notices.at(i)[0] for i in range(notices.count()))
        QTest.keyClicks(native, "123456789")
        assert native.text() == "中文输入1234"
        qt_app.processEvents()
        clear = next(button for button in native.findChildren(QToolButton) if button.isVisible())
        QTest.mouseClick(clear, Qt.MouseButton.LeftButton)
        assert native.text() == ""
        native.setReadOnly(True)
        QTest.keyClicks(native, "blocked")
        assert native.text() == ""
        assert project.to_bytes() == before
    finally:
        preview.dispose()


def test_editor_runs_in_independent_preview_process(project: ProjectModel, registry: WidgetRegistry,
                                                   qt_app: QApplication, tmp_path: Path) -> None:
    project, key = create_node(project, registry, "builtin.line_edit", 40, 48)
    project = set_property(project, registry, key, "echo_mode", "password")
    service = PreviewService(registry, stop_timeout_ms=500)
    messages: list[str] = []
    service.notice.connect(messages.append)
    screenshot = tmp_path / "编辑框预览.png"
    service._command = lambda: (sys.executable, ["-X", "utf8", "-u", "-m", "tests.line_edit_probe", str(screenshot)])
    try:
        service.start(project, "独立编辑框预览", "编辑框会话")
        wait_for(lambda: not service.active, qt_app, 12)
        assert service.last_ready is not None and not service.last_error
        assert any("编辑框自动输入检查通过" in message for message in messages)
        assert all("中文测试" not in message for message in messages)
        assert screenshot.exists() and project.nodes[key].properties["text"] == ""
    finally:
        service.shutdown()
