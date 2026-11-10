"""预览的原生窗口行为、协议、独立进程及设计器集成。"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, QProcess, QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import create_node, set_property
from core.commands.menus import add_menu, ensure_menu_bar
from core.errors import DesignerError
from core.models import ProjectModel
from core.events import set_event_enabled
from core.registry import WidgetRegistry
from preview.protocol import MAX_REPLY_BYTES, decode_message, encode_message, preview_plan
from preview.service import PreviewService
from panels.menu_editor import MenuEditor
from runtime.preview import PreviewRuntime
from tests.test_storage import wait_for


@pytest.fixture
def service(qt_app: QApplication, registry: WidgetRegistry) -> Iterator[PreviewService]:
    result = PreviewService(registry, startup_timeout_ms=10000, stop_timeout_ms=300)
    try:
        yield result
    finally:
        result.shutdown()
        result.deleteLater()
        qt_app.processEvents()


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    result = MainWindow(registry, settings=QSettings(str(tmp_path / "预览设置.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    result.show()
    qt_app.processEvents()
    try:
        yield result
    finally:
        result.discard_all_for_test()
        result.close()
        result.deleteLater()
        qt_app.processEvents()


def await_ready(service: PreviewService, qt_app: QApplication, state: str | None = None) -> None:
    wait_for(lambda: bool(service.last_error) or (service.last_ready is not None and
             (state is None or service.last_ready["state_id"] == state)), qt_app, 12)
    assert not service.last_error, service.last_error
    assert service.state == "running"


@pytest.mark.parametrize("border", ["standard", "fixed", "none"])
def test_runtime_is_interactive_and_has_real_window_properties(project: ProjectModel, registry: WidgetRegistry,
                                                             qt_app: QApplication, border: str) -> None:
    initialize(qt_app, configure_logging=False)
    project, button = create_node(project, registry, "builtin.button", 40, 56)
    project = set_event_enabled(project, registry, button, "clicked", True)
    project, label = create_node(project, registry, "builtin.label", 40, 112)
    for node, key, value in ((project.root_id, "border_style", border),
                             (project.root_id, "background_color", "#edf4fc"),
                             (button, "checkable", True), (button, "checked", False),
                             (button, "font_size", 15), (label, "visible", False)):
        project = set_property(project, registry, node, key, value)
    project = project.with_nodes({button: replace(project.nodes[button],
                                 designer=project.nodes[button].designer.changed(hidden=True))})
    before = project.to_bytes()
    preview = PreviewRuntime(registry)
    notices = QSignalSpy(preview.notice)
    closed = QSignalSpy(preview.closed)
    try:
        preview.show(preview_plan(project, registry, "运行快照"), project)
        qt_app.processEvents()
        root = preview.tree.root
        native = preview.tree.widgets[button]
        assert root.isVisible() and root.styleSheet() == ""
        assert not root.testAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        assert (root.width(), root.height()) == (800, 560)
        assert root.windowTitle() == "测试窗口"
        assert native.isVisible() and not preview.tree.widgets[label].isVisible()
        assert native.font().pointSize() == 15 and native.x() == 40 and native.y() == 56
        assert root.centralWidget().palette().color(QPalette.ColorRole.Window).name() == "#edf4fc"
        assert bool(root.windowFlags() & Qt.WindowType.FramelessWindowHint) == (border == "none")
        if border == "fixed":
            assert root.minimumSize() == root.maximumSize()
        assert notices.count() == 0
        QTest.mouseClick(native, Qt.MouseButton.LeftButton)
        assert native.isChecked() and notices.count() == 1
        assert "被单击" in notices.at(0)[0]
        assert project.to_bytes() == before
        QTest.keyClick(native, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert closed.count() == 1
    finally:
        preview.dispose()


def test_runtime_disabled_controls_and_focus_order(project: ProjectModel, registry: WidgetRegistry,
                                                  qt_app: QApplication) -> None:
    project, first = create_node(project, registry, "builtin.button", 20, 20)
    project, second = create_node(project, registry, "builtin.button", 20, 80)
    project, disabled = create_node(project, registry, "builtin.button", 20, 140)
    project = set_property(project, registry, disabled, "enabled", False)
    project = replace(project, data=project.data.changed(tab_order=[second, first, disabled]))
    preview = PreviewRuntime(registry)
    spy = QSignalSpy(preview.notice)
    try:
        preview.show(preview_plan(project, registry, "状态"), project)
        assert preview.tree.widgets[second].nextInFocusChain() is preview.tree.widgets[first]
        QTest.mouseClick(preview.tree.widgets[disabled], Qt.MouseButton.LeftButton)
        assert spy.count() == 0
    finally:
        preview.dispose()


def test_runtime_close_and_repeated_disposal_release_window(project: ProjectModel, registry: WidgetRegistry,
                                                          qt_app: QApplication) -> None:
    preview = PreviewRuntime(registry)
    preview.show(preview_plan(project, registry, "关闭检查"), project)
    root = preview.tree.root
    closed = QSignalSpy(preview.closed)
    destroyed = QSignalSpy(root.destroyed)
    root.close()
    qt_app.processEvents()
    assert closed.count() == 1
    preview.dispose()
    preview.dispose()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert destroyed.count() == 1 and preview.tree.root is None


def test_offscreen_position_is_corrected_only_in_preview(project: ProjectModel, registry: WidgetRegistry,
                                                        qt_app: QApplication) -> None:
    project = set_property(project, registry, project.root_id, "geometry.x", 999999)
    before = project.to_bytes()
    preview = PreviewRuntime(registry)
    try:
        preview.show(preview_plan(project, registry, "位置检查"), project)
        assert any(screen.availableGeometry().intersects(preview.tree.root.geometry()) for screen in qt_app.screens())
        assert project.to_bytes() == before
    finally:
        preview.dispose()


def test_unconnected_handlers_are_not_executed(project: ProjectModel, registry: WidgetRegistry,
                                                         qt_app: QApplication) -> None:
    handler = {"id": str(uuid4()), "code_name": "custom_handler"}
    project = replace(project, data=project.data.changed(handlers=[handler]))
    preview = PreviewRuntime(registry)
    notices = QSignalSpy(preview.notice)
    try:
        preview.show(preview_plan(project, registry, "事件限制"), project)
        assert notices.count() == 0
    finally:
        preview.dispose()


@pytest.mark.parametrize("data", [b"not json", b"[]", b"\xff", b'{"version":true}',
                                  b'{"version":99,"kind":"ready","request_id":"x"}'])
def test_invalid_protocol_is_rejected(data: bytes) -> None:
    with pytest.raises(DesignerError):
        decode_message(data, limit=MAX_REPLY_BYTES)


def test_protocol_keeps_chinese_and_rejects_oversized_messages() -> None:
    packet = encode_message("notice", "任务一", message="按钮被单击")
    assert decode_message(packet, limit=MAX_REPLY_BYTES)["message"] == "按钮被单击"
    with pytest.raises(DesignerError, match="大小"):
        decode_message(packet, limit=10)


def test_process_starts_without_writing_project_and_stops(project: ProjectModel, service: PreviewService,
                                                        qt_app: QApplication, tmp_path: Path) -> None:
    before = project.to_bytes()
    service.start(project, "状态一", "会话一")
    await_ready(service, qt_app)
    assert service.last_ready["process_id"] != os.getpid()
    assert service.last_ready["widget_count"] == 2
    assert service.last_ready["size"] == [800, 560]
    assert service.last_ready["title"] == project.name
    assert project.to_bytes() == before
    assert list(tmp_path.iterdir()) == []
    service.stop()
    wait_for(lambda: not service.active, qt_app)
    assert service.state == "idle" and not service.last_error


def test_repeated_preview_uses_latest_snapshot_and_new_process(project: ProjectModel, registry: WidgetRegistry,
                                                             service: PreviewService, qt_app: QApplication) -> None:
    service.start(project, "旧状态", "会话一")
    await_ready(service, qt_app)
    first_pid = service.last_ready["process_id"]
    updated = set_property(project, registry, project.root_id, "window_title", "新的预览标题")
    service.start(updated, "中间状态", "会话一")
    service.start(updated, "最新状态", "会话一")
    await_ready(service, qt_app, "最新状态")
    assert service.last_ready["title"] == "新的预览标题"
    assert service.last_ready["process_id"] != first_pid
    assert service.pending is None


def test_stop_during_start_does_not_leave_process(project: ProjectModel, service: PreviewService,
                                                qt_app: QApplication) -> None:
    service.start(project, "状态", "会话")
    service.stop()
    wait_for(lambda: not service.active, qt_app)
    assert not service.last_error


def test_parent_pipe_closed_causes_preview_exit(project: ProjectModel, service: PreviewService,
                                              qt_app: QApplication) -> None:
    service.start(project, "状态", "会话")
    await_ready(service, qt_app)
    service.process.closeWriteChannel()
    wait_for(lambda: not service.active, qt_app)
    assert not service.last_error


def test_crashed_process_is_reported_and_can_restart(project: ProjectModel, service: PreviewService,
                                                   qt_app: QApplication) -> None:
    errors = QSignalSpy(service.error)
    service.start(project, "状态一", "会话")
    await_ready(service, qt_app)
    service.process.kill()
    wait_for(lambda: not service.active, qt_app)
    assert errors.count() == 1 and "异常" in service.last_error
    service.start(project, "状态二", "会话")
    await_ready(service, qt_app, "状态二")


def test_failed_interpreter_start_is_reported(project: ProjectModel, service: PreviewService,
                                             qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "_command", lambda: ("不存在的预览解释器", []))
    service.start(project, "状态", "会话")
    wait_for(lambda: not service.active, qt_app)
    assert "无法启动" in service.last_error


def test_start_timeout_kills_only_its_process(project: ProjectModel, service: PreviewService,
                                             qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "_command", lambda: (sys.executable, ["-c", "import time; time.sleep(60)"]))
    service.startup_timer.setInterval(80)
    service.start(project, "状态", "会话")
    wait_for(lambda: not service.active, qt_app)
    assert "超时" in service.last_error


def test_invalid_worker_output_is_reported(project: ProjectModel, service: PreviewService,
                                         qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "_command", lambda: (sys.executable, ["-c", "print('invalid message', flush=True)"]))
    service.start(project, "状态", "会话")
    wait_for(lambda: not service.active, qt_app)
    assert "JSON" in service.last_error


def test_validation_failure_does_not_stop_existing_preview(project: ProjectModel, registry: WidgetRegistry,
                                                         service: PreviewService, qt_app: QApplication) -> None:
    service.start(project, "可见窗口", "会话")
    await_ready(service, qt_app)
    pid = service.last_ready["process_id"]
    hidden = set_property(project, registry, project.root_id, "visible", False)
    with pytest.raises(DesignerError, match="可见"):
        service.start(hidden, "隐藏窗口", "会话")
    assert service.active and service.last_ready["process_id"] == pid


def test_unknown_control_is_rejected_before_launch(project: ProjectModel, registry: WidgetRegistry,
                                                  service: PreviewService) -> None:
    project, button = create_node(project, registry, "builtin.button", 40, 40)
    project = project.with_nodes({button: replace(project.nodes[button], type_id="plugin.unknown")})
    with pytest.raises(DesignerError, match="适配器"):
        service.start(project, "状态", "会话")
    assert not service.active


def test_stopping_source_session_preserves_preview_of_another_session(project: ProjectModel, service: PreviewService,
                                                                    qt_app: QApplication) -> None:
    service.start(project, "第一份状态", "第一会话")
    await_ready(service, qt_app)
    service.stop_session("另一会话")
    assert service.state == "running"
    service.start(project, "第二份状态", "第二会话")
    service.stop_session("第一会话")
    await_ready(service, qt_app, "第二份状态")
    assert service.request.session_id == "第二会话"


def test_ui_commits_pending_text_and_runs_snapshot(window: MainWindow, qt_app: QApplication) -> None:
    document = window.document
    editor = window.properties.editors["window_title"]
    editor.setFocus()
    editor.selectAll()
    editor.insert("尚未保存的预览标题")
    window.actions["preview"].trigger()
    await_ready(window.preview_service, qt_app)
    assert window.preview_service.last_ready["title"] == "尚未保存的预览标题"
    assert document.path is None and document.dirty
    state, cursor, snapshot = document.state_id, document.history.cursor, document.model.to_bytes()
    assert window.actions["stop_preview"].isEnabled()
    assert window.actions["preview"].shortcut().toString() == "F5"
    window.actions["stop_preview"].trigger()
    wait_for(lambda: not window.preview_service.active, qt_app)
    assert document.state_id == state and document.history.cursor == cursor
    assert document.model.to_bytes() == snapshot
    assert not window.actions["stop_preview"].isEnabled()


@pytest.mark.parametrize("connected", [False, True])
def test_menu_only_editor_project_previews_and_restarts(window, qt_app, monkeypatch, connected):
    def edit(dialog):
        dialog.operate("add")
        dialog.title_edit.setText("文件(&F)")
        dialog.operate("child")
        dialog.title_edit.setText("新建项目")
        dialog.connected.setChecked(connected)
        dialog.accept()
        return dialog.result()

    monkeypatch.setattr(MenuEditor, "exec", edit)
    window.edit_menus()
    document = window.document
    assert len(document.model.nodes) == 5
    assert not any(node.slot == "children" for node in document.model.nodes.values())
    assert document.path is None
    before = document.model.to_bytes()
    window.actions["preview"].trigger()
    assert window.preview_service.active, window.output.toPlainText()
    await_ready(window.preview_service, qt_app)
    assert window.preview_service.last_ready["process_id"] != os.getpid()
    assert window.preview_service.last_ready["widget_count"] == 5
    assert document.model.to_bytes() == before
    first_pid = window.preview_service.last_ready["process_id"]
    key = next(node.id for node in document.model.nodes.values() if node.properties.get("text") == "新建项目")
    document.execute("修改菜单标题", lambda model: set_property(model, document.registry, key, "text", "再次新建"))
    window.actions["preview"].trigger()
    await_ready(window.preview_service, qt_app, document.state_id)
    assert window.preview_service.last_ready["process_id"] != first_pid
    window.actions["stop_preview"].trigger()
    wait_for(lambda: not window.preview_service.active, qt_app)
    assert not window.preview_service.last_error


@pytest.mark.parametrize("connected", [False, True])
def test_menu_only_child_process_click_reports_selected_events(project, registry, service, qt_app, monkeypatch, connected):
    project, bar = ensure_menu_bar(project, registry)
    project, parent = add_menu(project, registry, bar)
    project, leaf = add_menu(project, registry, parent)
    project = set_event_enabled(project, registry, leaf, "clicked", connected)
    before = project.to_bytes()
    messages = QSignalSpy(service.notice)
    monkeypatch.setattr(service, "_command", lambda: (sys.executable, ["-X", "utf8", "-u", "-m",
                                                                    "tests.preview_probe", "", "menu"]))
    service.start(project, "菜单点击", "会话")
    wait_for(lambda: not service.active, qt_app, 12)
    assert not service.last_error and service.last_ready is not None
    assert service.last_ready["process_id"] != os.getpid()
    clicks = [messages.at(i)[0] for i in range(messages.count()) if "被单击" in messages.at(i)[0]]
    assert len(clicks) == int(connected)
    assert not any("强制结束" in messages.at(i)[0] for i in range(messages.count()))
    assert project.to_bytes() == before


def test_ui_errors_are_chinese_and_in_output(window: MainWindow, qt_app: QApplication,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(window.preview_service, "_command", lambda: ("不存在的预览解释器", []))
    window.actions["preview"].trigger()
    wait_for(lambda: not window.preview_service.active, qt_app)
    assert "预览失败" in window.output.toPlainText()
    assert window.output_dock.isVisible()


def test_close_source_document_stops_preview(window: MainWindow, qt_app: QApplication) -> None:
    source = window.document
    window.preview_current()
    await_ready(window.preview_service, qt_app)
    other = window.new_document()
    assert window.preview_service.request.session_id == source.session_id
    window._close_document(source)
    wait_for(lambda: not window.preview_service.active, qt_app)
    assert window.document is other


def test_shutdown_waits_for_owned_process(window: MainWindow, qt_app: QApplication) -> None:
    window.preview_current()
    await_ready(window.preview_service, qt_app)
    process = window.preview_service.process
    window.discard_all_for_test()
    window.close()
    assert not window.preview_service.active
    assert process.state() == QProcess.ProcessState.NotRunning


@pytest.mark.parametrize("closing", ["escape", "close"])
def test_real_child_process_clicks_report_and_window_close_exits(project: ProjectModel, registry: WidgetRegistry,
                                                               service: PreviewService, qt_app: QApplication,
                                                               monkeypatch: pytest.MonkeyPatch, closing: str) -> None:
    project, button = create_node(project, registry, "builtin.button", 40, 40)
    project = set_property(project, registry, button, "checkable", True)
    project = set_event_enabled(project, registry, button, "clicked", True)
    before = project.to_bytes()
    messages = QSignalSpy(service.notice)
    monkeypatch.setattr(service, "_command", lambda: (sys.executable, ["-X", "utf8", "-u", "-m",
                                                                    "tests.preview_probe", "", closing]))
    service.start(project, "独立交互", "会话")
    wait_for(lambda: not service.active, qt_app, 12)
    assert not service.last_error and service.last_ready is not None
    assert any("被单击；已选中" in messages.at(i)[0] for i in range(messages.count()))
    assert not any("强制结束" in messages.at(i)[0] for i in range(messages.count()))
    assert project.to_bytes() == before


def test_disabled_frameless_window_can_be_stopped_from_designer(project: ProjectModel, registry: WidgetRegistry,
                                                               service: PreviewService, qt_app: QApplication) -> None:
    for key, value in (("enabled", False), ("border_style", "none"), ("close_button", False)):
        project = set_property(project, registry, project.root_id, key, value)
    service.start(project, "无边框状态", "会话")
    await_ready(service, qt_app)
    service.stop()
    wait_for(lambda: not service.active, qt_app)
    assert not service.last_error


def test_stdout_utf8_can_arrive_in_separate_chunks(project: ProjectModel, service: PreviewService,
                                                  qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    script = "import sys,time; data=sys.stdin.buffer.readline(); import json; req=json.loads(data); " \
             "packet=(json.dumps({'version':1,'kind':'notice','request_id':req['request_id'],'message':'中文消息'},ensure_ascii=False)+'\\n').encode('utf-8'); " \
             "split=packet.index('中'.encode('utf-8'))+1; " \
             "sys.stdout.buffer.write(packet[:split]); sys.stdout.buffer.flush(); time.sleep(.05); " \
             "sys.stdout.buffer.write(packet[split:]); sys.stdout.buffer.flush(); time.sleep(.05)"
    monkeypatch.setattr(service, "_command", lambda: (sys.executable, ["-X", "utf8", "-c", script]))
    messages = QSignalSpy(service.notice)
    service.start(project, "状态", "会话")
    wait_for(lambda: not service.active, qt_app)
    assert any(messages.at(i)[0] == "中文消息" for i in range(messages.count()))
    assert "就绪前退出" in service.last_error
