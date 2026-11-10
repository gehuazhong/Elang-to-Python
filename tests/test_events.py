"""事件勾选的保存、撤销、真实 Qt 交互、导出业务保护与生命周期回归。"""

from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaMethod, QPoint, Qt
from PySide6.QtGui import QFocusEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractItemView, QCalendarWidget, QCheckBox, QLineEdit, QListWidget, QPushButton, QSpinBox, QToolBar, QToolButton, QWidget
from shiboken6 import delete

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.clipboard import copy_fragment, paste_fragment
from core.commands.nodes import create_node, delete_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.events import event_bindings, event_enabled, set_event_enabled
from core.models import ProjectModel
from core.storage import commit_project, load_project
from panels.properties import PropertyPanel
from runtime.builder import FACTORIES, verify_registry
from runtime.events import EventConnections
from runtime.easy_widgets import SelectionTabs
from runtime.preview import PreviewRuntime
from tests.test_codegen import load_export
from widgets.builtin import create_registry
from widgets.events import EXCLUDED_SIGNALS


@pytest.mark.parametrize("type_id", list(create_registry().specs))
def test_catalog_covers_actual_native_signals(type_id, registry, qt_app):
    spec = registry.require(type_id)
    widget = FACTORIES[spec.qt_class]()
    try:
        meta = widget.metaObject()
        signals = {bytes(meta.method(i).name()).decode() for i in range(meta.methodCount())
                   if meta.method(i).methodType() == QMetaMethod.MethodType.Signal}
        declared = {event.qt_signal for event in spec.events if event.qt_signal}
        assert signals - EXCLUDED_SIGNALS.get(spec.qt_class, set()) == declared
        assert len({event.key for event in spec.events}) == len(spec.events)
        manager = EventConnections(widget, {"control": widget},
                                   [binding(signal=event.qt_signal) for event in spec.events if event.qt_signal],
                                   lambda item, args: None)
        manager.dispose()
        if isinstance(widget, QWidget):
            assert {"mouse_press", "key_press", "close", "focus_in", "drop"} <= {event.key for event in spec.events}
        else:
            assert all(not event.qt_event for event in spec.events)
    finally:
        delete(widget)


def test_catalog_is_verified_by_runtime(registry, qt_app):
    verify_registry(registry)


def test_checkbox_save_undo_redo_and_reenable_identity(project, registry, qt_app, tmp_path):
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    document = DocumentSession(project, registry)
    document.select(key)
    panel = PropertyPanel()
    panel.bind(document)
    try:
        editor = panel.editors["event.clicked"]
        assert isinstance(editor, QCheckBox) and not editor.isChecked()
        cursor = document.history.cursor
        editor.click()
        qt_app.processEvents()
        assert event_enabled(document.model, key, "clicked")
        assert document.history.cursor == cursor + 1
        connection = document.model.data["connections"][0]
        handler = document.model.data["handlers"][0]
        path = tmp_path / "事件项目.uipro"
        commit_project(path, document.model, expected_token=None)
        restored = load_project(path).model
        assert restored == document.model
        document.undo()
        qt_app.processEvents()
        assert not panel.editors["event.clicked"].isChecked()
        document.redo()
        qt_app.processEvents()
        panel.editors["event.clicked"].click()
        qt_app.processEvents()
        assert not event_enabled(document.model, key, "clicked")
        assert document.model.data["handlers"] == (handler,)
        panel.editors["event.clicked"].click()
        assert document.model.data["connections"] == (connection,)
        document.execute("删除组件", lambda model: delete_node(model, key))
        assert not document.model.data["connections"]
        document.undo()
        assert event_enabled(document.model, key, "clicked")
    finally:
        panel.bind(None)
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize("kind,event", [("button", "clicked"), ("timer", "timeout"),
                                       ("common_dialog", "accepted"), ("tool_bar", "actionTriggered"),
                                       ("status_bar", "messageChanged")])
def test_copy_remaps_checked_and_disabled_events(project, registry, kind, event):
    project, key = create_node(project, registry, "builtin." + kind, 40, 40)
    spec = registry.require(project.nodes[key].type_id)
    event = next(item.key for item in spec.events if item.qt_signal == event)
    project = set_event_enabled(project, registry, key, event, True)
    project = set_event_enabled(project, registry, key, "destroyed", True)
    project = set_event_enabled(project, registry, key, "destroyed", False)
    fragment = copy_fragment(project, registry, key)
    target = delete_node(project, key) if kind in {"tool_bar", "status_bar"} else project
    copied, new_key = paste_fragment(target, registry, fragment)
    assert event_enabled(copied, new_key, event)
    assert not event_enabled(copied, new_key, "destroyed")
    assert all(item["source_id"] == new_key for item in copied.data["connections"] if item["source_id"] != key)
    assert len({item["code_name"].casefold() for item in copied.data["handlers"]}) == len(copied.data["handlers"])


def test_preview_default_unchecked_rebinds_without_duplicate_or_leaked_connections(project, registry, qt_app):
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    preview = PreviewRuntime(registry)
    messages = []
    preview.notice.connect(messages.append)
    try:
        preview.show(compile_plan(project, registry, "未连接"), project)
        button = preview.tree.widgets[key]
        button.click()
        assert messages == []
        checked = set_event_enabled(project, registry, key, "clicked", True)
        for i in range(3):
            preview.show(compile_plan(checked, registry, str(i)), checked)
            button.click()
            assert len(messages) == i + 1
        unchecked = set_event_enabled(checked, registry, key, "clicked", False)
        preview.show(compile_plan(unchecked, registry, "断开"), unchecked)
        button.click()
        assert len(messages) == 3
        preview.dispose()
        button.click()
        assert len(messages) == 3
    finally:
        preview.dispose()


def binding(signal="", event="", control="control", **extra):
    return {"id": str(uuid4()), "control": control, "key": signal or event,
            "name": "测试组件", "label": "测试事件", "signal": signal, "event": event,
            "handler": "handler", "arguments": None, **extra}


def test_native_signal_arguments_and_disposal_preserve_other_subscribers(qt_app):
    root = QWidget()
    button, edit = QPushButton(root), QLineEdit(root)
    button.setCheckable(True)
    received, manual = [], []
    button.clicked[bool].connect(manual.append)
    manager = EventConnections(root, {"button": button, "edit": edit},
                               [binding(signal="clicked", control="button"), binding(signal="textChanged", control="edit")],
                               lambda item, args: received.append(args))
    try:
        button.click()
        edit.setText("真实中文参数")
        assert received == [(True,), ("真实中文参数",)]
        manager.dispose()
        button.click()
        assert received == [(True,), ("真实中文参数",)] and manual == [True, False]
    finally:
        delete(root)


@pytest.mark.parametrize("kind", ["button", "list", "spin"])
def test_mouse_key_and_focus_reach_internal_input_widgets(qt_app, kind):
    root = QWidget()
    widget = {"button": QPushButton, "list": QListWidget, "spin": QSpinBox}[kind](root)
    received = []
    manager = EventConnections(root, {"control": widget},
                               [binding(event="MouseButtonPress"), binding(event="KeyPress"), binding(event="FocusIn")],
                               lambda item, args: received.append(item["event"]))
    try:
        root.show()
        qt_app.processEvents()
        received.clear()
        target = widget.viewport() if kind == "list" else widget.lineEdit() if kind == "spin" else widget
        QTest.mouseClick(target, Qt.MouseButton.LeftButton, pos=QPoint(8, 8))
        assert received.count("MouseButtonPress") == 1
        QTest.keyClick(widget.lineEdit() if kind == "spin" else widget, Qt.Key.Key_A)
        assert received.count("KeyPress") == 1
        QCoreApplication.sendEvent(widget.lineEdit() if kind == "spin" else widget, QFocusEvent(QEvent.Type.FocusIn))
        assert "FocusIn" in received
    finally:
        manager.dispose()
        delete(root)


def test_close_event_can_cancel_and_binding_settings_are_restored(qt_app):
    root = QWidget()
    old_policy = root.contextMenuPolicy()
    def handler(item, args):
        if item["event"] == "Close":
            args[0].ignore()
            return True
    manager = EventConnections(root, {"control": root},
                               [binding(event="Close"), binding(event="MouseMove"), binding(event="Drop"),
                                binding(signal="customContextMenuRequested")], handler)
    try:
        root.show()
        assert root.hasMouseTracking() and root.acceptDrops()
        assert root.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
        assert not root.close() and root.isVisible()
        manager.dispose()
        assert not root.hasMouseTracking() and not root.acceptDrops()
        assert root.contextMenuPolicy() == old_policy
        assert root.close()
    finally:
        delete(root)


@pytest.mark.parametrize("kind", ["calendar", "tabs", "toolbar", "clear_button"])
def test_composite_widget_mouse_events_include_its_native_parts(qt_app, kind):
    root = QWidget()
    widget = {"calendar": QCalendarWidget, "tabs": SelectionTabs, "toolbar": QToolBar, "clear_button": QLineEdit}[kind](root)
    if kind == "calendar":
        view = widget.findChild(QAbstractItemView)
        target = view.viewport()
    elif kind == "tabs":
        widget.tab_bar.addTab("页面")
        target = widget.tab_bar
    elif kind == "toolbar":
        target = widget.widgetForAction(widget.addAction("按钮"))
    else:
        widget.setClearButtonEnabled(True)
        widget.setText("内容")
        target = widget.findChild(QToolButton)
    received = []
    manager = EventConnections(root, {"control": widget}, [binding(event="MouseButtonPress")],
                               lambda item, args: received.append(item["event"]))
    try:
        root.show()
        qt_app.processEvents()
        position = view.visualRect(view.currentIndex()).center() if kind == "calendar" else QPoint(8, 8)
        QTest.mouseClick(target, Qt.MouseButton.LeftButton, pos=position)
        assert received == ["MouseButtonPress"]
    finally:
        manager.dispose()
        delete(root)


def test_destroyed_and_handler_exceptions_do_not_leave_connections(qt_app):
    root, child = QWidget(), QWidget()
    received, errors = [], []
    def handler(item, args):
        received.append(item["signal"])
        raise ValueError("业务异常")
    manager = EventConnections(root, {"control": child}, [binding(signal="destroyed")], handler, errors.append)
    delete(child)
    manager.dispose()
    assert received == ["destroyed"] and len(errors) == 1
    delete(root)


def test_export_checked_handlers_run_and_reexport_preserves_code(project, registry, qt_app, tmp_path):
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    project = set_property(project, registry, key, "checkable", True)
    project = set_event_enabled(project, registry, key, "clicked", True)
    entry = export_project(project, registry, tmp_path)
    name = project.data["handlers"][0]["code_name"]
    path = tmp_path / "event_handlers" / (name + ".py")
    source = f"def {name}(window, *arguments):\n    window.setWindowTitle(str(arguments[0]))\n"
    path.write_text(source, encoding="utf-8")
    business = (tmp_path / "handlers.py").read_bytes()
    for enabled in (True, False, True):
        project = set_event_enabled(project, registry, key, "clicked", enabled)
        export_project(project, registry, tmp_path)
        assert path.read_text(encoding="utf-8") == source
        assert (tmp_path / "handlers.py").read_bytes() == business
        window = load_export(entry, qt_app)
        try:
            window.controls[project.nodes[key].code_name].click()
            assert window.windowTitle() == ("True" if enabled else project.name)
        finally:
            window.close()
            window.deleteLater()
    project = set_event_enabled(project, registry, project.root_id, "show", True)
    export_project(project, registry, tmp_path)
    assert len(list((tmp_path / "event_handlers").glob("*.py"))) == 2


def test_export_event_syntax_and_concurrent_edits_keep_previous_version(project, registry, tmp_path):
    project = set_event_enabled(project, registry, project.root_id, "show", True)
    entry = export_project(project, registry, tmp_path)
    pointer = entry.with_name("current.json").read_bytes()
    path = next((tmp_path / "event_handlers").glob("*.py"))
    original = path.read_bytes()
    changed = set_property(project, registry, project.root_id, "window_title", "新标题")
    path.write_text("语法错误(", encoding="utf-8")
    with pytest.raises(DesignerError, match="语法"):
        export_project(changed, registry, tmp_path)
    assert entry.with_name("current.json").read_bytes() == pointer
    path.write_bytes(original)
    def edit(phase):
        if phase == "before.publish":
            path.write_bytes(original + b"\n")
    with pytest.raises(DesignerError, match="发生了变化"):
        export_project(changed, registry, tmp_path, checkpoint=edit)
    assert entry.with_name("current.json").read_bytes() == pointer


def test_selected_event_export_runs_in_isolated_process(project, registry, tmp_path):
    project, key = create_node(project, registry, "builtin.line_edit", 40, 40)
    project = set_event_enabled(project, registry, key, "textChanged", True)
    entry = export_project(project, registry, tmp_path)
    name = project.data["handlers"][0]["code_name"]
    (tmp_path / "event_handlers" / (name + ".py")).write_text(
        "from __future__ import annotations\nfrom dataclasses import dataclass\n"
        "@dataclass\nclass Message:\n    text: str\n"
        f"def {name}(window, text):\n    window.setWindowTitle(Message(text).text)\n", encoding="utf-8")
    script = '''import importlib.util, pathlib, sys
from PySide6.QtWidgets import QApplication
entry = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("entry", entry)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = QApplication([])
window = module.create_window(app)
window.controls[sys.argv[2]].setText("事件独立执行")
assert window.windowTitle() == "事件独立执行"
assert not any(name in sys.modules for name in ("core", "app", "runtime"))
window.close()
print("独立事件通过")
'''
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", script, str(entry), project.nodes[key].code_name],
                            cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "独立事件通过" in result.stdout


def test_disabled_handler_file_is_neither_imported_nor_overwritten(project, registry, tmp_path, qt_app):
    enabled = set_event_enabled(project, registry, project.root_id, "show", True)
    entry = export_project(enabled, registry, tmp_path)
    path = next((tmp_path / "event_handlers").glob("*.py"))
    source = 'raise RuntimeError("未勾选不应加载业务模块")\n'
    path.write_text(source, encoding="utf-8")
    disabled = set_event_enabled(enabled, registry, project.root_id, "show", False)
    export_project(disabled, registry, tmp_path)
    window = load_export(entry, qt_app)
    try:
        window.show()
        assert path.read_text(encoding="utf-8") == source
    finally:
        window.close()
        window.deleteLater()


def test_legacy_slot_arguments_execute_and_invalid_target_preserves_export(project, registry, qt_app, tmp_path):
    project, button = create_node(project, registry, "builtin.button", 40, 40)
    project, label = create_node(project, registry, "builtin.label", 40, 100)
    connection = {"id": str(uuid4()), "source_id": button, "event": "clicked",
                  "target": {"kind": "slot", "node_id": label, "slot": "set_text"},
                  "arguments": [{"kind": "constant", "value_type": "string", "value": "连接成功"}]}
    project = replace(project, data=project.data.changed(connections=[connection]))
    preview = PreviewRuntime(registry)
    entry = export_project(project, registry, tmp_path)
    window = load_export(entry, qt_app)
    try:
        preview.show(compile_plan(project, registry, "旧式连接"), project)
        preview.tree.widgets[button].click()
        assert preview.tree.widgets[label].text() == "连接成功"
        window.controls[project.nodes[button].code_name].click()
        assert window.controls[project.nodes[label].code_name].text() == "连接成功"
        pointer = (tmp_path / "current.json").read_bytes()
        connection["target"]["slot"] = "set_value"
        invalid = replace(project, data=project.data.changed(connections=[connection]))
        with pytest.raises(DesignerError, match="目标组件"):
            export_project(invalid, registry, tmp_path)
        assert (tmp_path / "current.json").read_bytes() == pointer
    finally:
        preview.dispose()
        window.close()
        window.deleteLater()
