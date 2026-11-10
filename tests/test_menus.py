"""菜单草稿、层级、原生运行与独立导出的行为回归。"""

from dataclasses import replace

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QGraphicsScene
from shiboken6 import isValid

from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.menus import add_menu, ensure_menu_bar, menu_children, move_menu, remove_menu, rename_menu
from core.commands.nodes import create_node, set_property
from core.errors import DesignerError
from core.events import event_enabled, set_event_enabled
from core.hierarchy import content_size, window_bars
from core.menu_values import normalize_shortcut
from core.storage import commit_project, load_project
from core.validation import validate_project
from designer.renderer import CanvasRenderer
from panels.menu_editor import MenuEditor
from runtime.builder import RuntimeTree
from runtime.preview import PreviewRuntime
from tests.test_clipboard import window
from tests.test_codegen import load_export


def sample(project, registry):
    project, bar = ensure_menu_bar(project, registry)
    keys = {"bar": bar}
    for name, parent, text, values in (
        ("file", "bar", "文件(&F)", {}),
        ("open", "file", "打开(&O)", {"shortcut": "Ctrl+O"}),
        ("recent", "file", "最近文件", {}),
        ("recent_one", "recent", "示例项目", {}),
        ("separator", "file", "-", {"separator": True}),
        ("disabled", "file", "禁止操作", {"enabled": False}),
        ("hidden", "file", "隐藏操作", {"visible": False}),
        ("view", "bar", "视图(&V)", {}),
        ("grid", "view", "显示网格", {"checked": True, "shortcut": "Ctrl+G"}),
    ):
        project, key = add_menu(project, registry, keys[parent], separator=values.get("separator", False))
        keys[name] = key
        project = rename_menu(project, key, name, "menu_" + name)
        for field, value in {"text": text, **values}.items():
            project = set_property(project, registry, key, field, value)
    return project, keys


def test_structure_preserves_identity_and_connections(project, registry):
    project, keys = sample(project, registry)
    project = set_event_enabled(project, registry, keys["recent_one"], "clicked", True)
    original = project
    moved = move_menu(project, registry, keys["recent_one"], "left")
    assert moved.nodes[keys["recent_one"]].parent_id == keys["file"]
    moved = move_menu(moved, registry, keys["recent_one"], "right")
    assert moved == original
    moved = move_menu(moved, registry, keys["view"], "up")
    assert menu_children(moved, keys["bar"])[0].id == keys["view"]
    moved = move_menu(moved, registry, keys["view"], "down")
    assert moved == original
    removed = remove_menu(project, keys["recent"])
    assert keys["recent_one"] not in removed.nodes and not removed.data["connections"]
    assert removed.data["handlers"] == original.data["handlers"]
    validate_project(removed)
    registry.validate(removed)


def test_locked_menu_and_depth_limits(project, registry):
    project, keys = sample(project, registry)
    node = project.nodes[keys["recent_one"]]
    locked = project.with_nodes({node.id: replace(node, designer=node.designer.changed(locked=True))})
    with pytest.raises(DesignerError, match="锁定"):
        move_menu(locked, registry, keys["recent"], "down")
    with pytest.raises(DesignerError, match="锁定"):
        remove_menu(locked, keys["recent"])
    key = keys["recent_one"]
    for _ in range(5):
        project, key = add_menu(project, registry, key)
    with pytest.raises(DesignerError, match="八层"):
        add_menu(project, registry, key)
    with pytest.raises(DesignerError, match="分隔线"):
        add_menu(project, registry, keys["bar"], separator=True)


@pytest.mark.parametrize("changes, match", [
    ({"text": ""}, "标题"), ({"shortcut": "Ctrl+G"}, "重复"),
    ({"shortcut": "invalid key"}, "快捷键"), ({"separator": True}, "分隔线"),
])
def test_invalid_menu_values_are_rejected(project, registry, changes, match):
    project, keys = sample(project, registry)
    node = project.nodes[keys["open"]]
    candidate = project.with_nodes({node.id: replace(node, properties=node.properties.changed(**changes))})
    with pytest.raises(DesignerError, match=match):
        registry.validate(candidate)


@pytest.mark.parametrize("shortcut", ["Ctrl+O", "Shift+F1", "Ctrl++", "Ctrl+,", "Ctrl+PgUp", "Alt+Space", "Meta+Ctrl+Alt+Shift+Z"])
def test_shortcuts_roundtrip_through_qt(shortcut, qt_app):
    assert normalize_shortcut(shortcut) == shortcut
    assert QKeySequence(shortcut).toString(QKeySequence.SequenceFormat.PortableText) == shortcut


def test_editor_cancel_validation_separator_and_confirm(window, qt_app, monkeypatch):
    document = window.document
    baseline, cursor = document.model, document.history.cursor

    def edit(dialog):
        dialog.operate("add")
        dialog.title_edit.setText("文件(&F)")
        dialog.operate("child")
        dialog.title_edit.setText("打开")
        dialog.connected.setChecked(True)
        dialog.shortcut_edit.setKeySequence(QKeySequence("Ctrl+O"))
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert document.model == baseline
        return dialog.result()

    monkeypatch.setattr(MenuEditor, "exec", edit)
    window.edit_menus()
    assert document.history.cursor == cursor + 1
    result = document.model
    assert len([node for node in result.nodes.values() if node.slot == "menu"]) == 2
    assert event_enabled(result, document.selected_id, "clicked")
    document.undo()
    assert document.model == baseline
    document.redo()
    assert document.model == result

    def cancel(dialog):
        dialog.operate("add")
        dialog.reject()
        return dialog.result()

    monkeypatch.setattr(MenuEditor, "exec", cancel)
    window.edit_menus()
    assert document.model == result and document.history.cursor == cursor + 1
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not window.findChildren(MenuEditor)


def test_editor_preserves_invalid_input_and_disables_separator_events(project, registry, qt_app):
    project, keys = sample(project, registry)
    dialog = MenuEditor(project, registry, selected_id=keys["open"])
    try:
        dialog.name_edit.setText("file")
        dialog.tree.setCurrentItem(dialog.items[keys["view"]])
        assert dialog.selected_id == keys["open"]
        assert dialog.name_edit.text() == "file" and "重复" in dialog.error_label.text()
        dialog.name_edit.setText("open")
        dialog.title_edit.setText("-")
        dialog.accept()
        assert dialog.model.nodes[keys["open"]].properties["separator"]
        assert not dialog.model.nodes[keys["open"]].properties["shortcut"]
    finally:
        dialog.deleteLater()


def test_runtime_hierarchy_properties_cache_and_removal(project, registry, qt_app):
    project, keys = sample(project, registry)
    project, tool = create_node(project, registry, "builtin.tool_bar", 0, 0)
    project, status = create_node(project, registry, "builtin.status_bar", 0, 0)
    scene = QGraphicsScene()
    renderer = CanvasRenderer(scene, registry)
    tree = renderer.tree
    try:
        renderer.apply(compile_plan(project, registry, "initial"), project.data["canvas"], 1)
        bar = tree.widgets[keys["bar"]]
        file = tree.widgets[keys["file"]]
        assert bar.actions() == [file, tree.widgets[keys["view"]]]
        assert file.menu().actions() == [tree.widgets[node.id] for node in menu_children(project, keys["file"])]
        assert tree.widgets[keys["recent"]].menu().actions() == [tree.widgets[keys["recent_one"]]]
        assert tree.widgets[keys["separator"]].isSeparator()
        assert tree.widgets[keys["separator"]].text() == ""
        assert tree.widgets[keys["grid"]].isChecked()
        assert not tree.widgets[keys["disabled"]].isEnabled()
        assert not tree.widgets[keys["hidden"]].isVisible()
        assert tree.widgets[keys["open"]].shortcut().toString() == "Ctrl+O"
        assert window_bars(project) == (64, 28)
        assert tree.root.centralWidget().y() == 64
        assert tree.root.centralWidget().height() == content_size(project, project.central_id)[1]
        image_before = renderer.items[keys["bar"]].pixmap().cacheKey()
        changed = set_property(project, registry, keys["file"], "text", "新的文件菜单")
        renderer.apply(compile_plan(changed, registry, "changed"), changed.data["canvas"], 1)
        assert renderer.items[keys["bar"]].pixmap().cacheKey() != image_before
        leaf = tree.widgets[keys["recent_one"]]
        moved = move_menu(changed, registry, keys["recent_one"], "left")
        moved = remove_menu(moved, keys["recent"])
        renderer.apply(compile_plan(moved, registry, "moved"), moved.data["canvas"], 1)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert isValid(leaf) and leaf in file.menu().actions()
        removed = remove_menu(moved, keys["bar"])
        renderer.apply(compile_plan(removed, registry, "removed"), removed.data["canvas"], 1)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert tree.root.menuWidget() is None
        assert tree.root.centralWidget().y() == 36
        assert not isValid(leaf)
        renderer.apply(compile_plan(project, registry, "undo"), project.data["canvas"], 1)
        assert tree.root.centralWidget().y() == 64
    finally:
        tree.dispose()


def test_preview_events_checked_shortcuts_and_ancestor_state(project, registry, qt_app):
    project, keys = sample(project, registry)
    project = set_event_enabled(project, registry, keys["grid"], "clicked", True)
    runtime = PreviewRuntime(registry)
    notices = []
    runtime.notice.connect(notices.append)
    try:
        runtime.show(compile_plan(project, registry, "initial"), project)
        action = runtime.tree.widgets[keys["grid"]]
        action.trigger()
        assert not action.isChecked() and len(notices) == 1
        root = runtime.tree.root
        root.activateWindow()
        root.setFocus()
        QTest.qWait(50)
        QTest.keyClick(root, Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier)
        assert action.isChecked() and len(notices) == 2
        for field in ("enabled", "visible"):
            candidate = set_property(project, registry, keys["view"], field, False)
            runtime.show(compile_plan(candidate, registry, field), candidate)
            root.activateWindow()
            QTest.qWait(30)
            before = len(notices)
            QTest.keyClick(root, Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier)
            assert len(notices) == before
    finally:
        runtime.dispose()


def test_menu_save_export_and_business_preservation(project, registry, qt_app, tmp_path):
    project, keys = sample(project, registry)
    project = set_event_enabled(project, registry, keys["grid"], "clicked", True)
    path = tmp_path / "菜单.uipro"
    commit_project(path, project, expected_token=None)
    assert load_project(path).model == project
    entry = export_project(project, registry, tmp_path / "导出")
    handler = project.data["handlers"][0]["code_name"]
    business = entry.parent / "event_handlers" / (handler + ".py")
    payload = f'def {handler}(window, *args):\n    window.setWindowTitle("menu event " + str(args[0]))\n'
    business.write_text(payload, encoding="utf-8")
    exported = load_export(entry, qt_app)
    try:
        exported.controls["menu_grid"].trigger()
        assert exported.windowTitle() == "menu event False"
        assert exported.menuBar().actions()[0] is exported.controls["menu_file"]
        assert exported.controls["menu_recent"].menu().actions() == [exported.controls["menu_recent_one"]]
        assert not exported.controls["menu_hidden"].isVisible()
    finally:
        exported.close()
        exported.deleteLater()
    export_project(project, registry, entry.parent)
    assert business.read_text(encoding="utf-8") == payload
