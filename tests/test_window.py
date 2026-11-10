"""多文档、面板、文件和关闭流程的集成回归。"""

from __future__ import annotations

import gc
from pathlib import Path
from typing import Iterator
import weakref

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app import main_window
from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.errors import DesignerError
from core.registry import WidgetRegistry
from core.storage import FileLease, commit_project, load_project
from core import save_service
from tests.test_storage import wait_for


@pytest.fixture
def window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    result = MainWindow(registry, settings=QSettings(str(tmp_path / "设置.ini"), QSettings.Format.IniFormat),
                        recovery_directory=tmp_path / "恢复副本", persist_settings=False)
    result.show()
    qt_app.processEvents()
    try:
        yield result
    finally:
        for index in range(result.tabs.count()):
            document = result.tabs.widget(index).document
            if document.saving:
                wait_for(lambda: not document.saving, qt_app)
        result.discard_all_for_test()
        result.close()
        result.deleteLater()
        qt_app.processEvents()


def test_properties_update_canvas_and_tree_without_extra_commands(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document = window.page.canvas, window.document
    key = canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    cursor = document.history.cursor
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.setText("提交中文标题")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert document.history.cursor == cursor + 1
    assert canvas.renderer.tree.widgets[key].text() == "提交中文标题"
    name = window.properties.editors["name"]
    name.setText("确认按钮")
    name.editingFinished.emit()
    qt_app.processEvents()
    assert window.object_tree.currentItem().text(0) == "确认按钮"
    assert canvas.renderer.tree.widgets[key].objectName() == "确认按钮"
    cursor = document.history.cursor
    window.properties.refresh()
    window.object_tree.refresh()
    qt_app.processEvents()
    assert document.history.cursor == cursor


def test_paired_geometry_rows_edit_and_search(window: MainWindow, qt_app: QApplication) -> None:
    panel, document = window.properties, window.document
    editor = panel.editors["geometry.width"]
    editor.setFocus()
    editor.setValue(704)
    editor.editingFinished.emit()
    qt_app.processEvents()
    assert document.model.nodes[document.model.root_id].geometry.width == 704
    assert window.page.canvas.renderer.surface.rect().width() == 704
    panel.search.setText("高度")
    groups = [panel.tree.topLevelItem(i) for i in range(panel.tree.topLevelItemCount())]
    visible = [group for group in groups if not group.isHidden()]
    assert len(visible) == 1 and visible[0].text(0) == "位置与尺寸"
    assert visible[0].child(0).isHidden()
    assert not visible[0].child(1).isHidden()
    document.undo()
    qt_app.processEvents()
    assert panel.editors["geometry.width"].value() == 800


def test_text_shortcuts_do_not_delete_or_undo_canvas(window: MainWindow, qt_app: QApplication) -> None:
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    document = window.document
    qt_app.processEvents()
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    cursor = document.history.cursor
    QTest.keyClick(editor, Qt.Key.Key_Delete)
    assert key in document.model.nodes and document.history.cursor == cursor
    QTest.keyClicks(editor, "temporary")
    window.undo()
    assert document.history.cursor == cursor


def test_multidocument_actions_are_isolated(window: MainWindow, qt_app: QApplication) -> None:
    first_page, first = window.page, window.document
    button = first_page.canvas.create_component("builtin.button", QPointF(40, 40))
    second = window.new_document()
    label = window.page.canvas.create_component("builtin.label", QPointF(60, 60))
    window.page.canvas.setFocus()
    window.undo()
    assert label not in second.model.nodes and button in first.model.nodes
    window.tabs.setCurrentWidget(first_page)
    first_page.canvas.setFocus()
    window.undo()
    assert button not in first.model.nodes
    assert window.properties.document is first and window.object_tree.document is first


def test_switching_tabs_commits_pending_text(window: MainWindow, qt_app: QApplication) -> None:
    first_page, document = window.page, window.document
    key = first_page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    second = window.new_document()
    window.tabs.setCurrentWidget(first_page)
    qt_app.processEvents()
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    editor.insert("切换前的完整文本")
    window.tabs.setCurrentIndex(1)
    assert document.model.nodes[key].properties["text"] == "切换前的完整文本"
    assert window.document is second


def test_save_load_backup_and_duplicate_open(window: MainWindow, qt_app: QApplication, tmp_path: Path) -> None:
    document = window.document
    key = window.page.canvas.create_component("builtin.label", QPointF(64, 88))
    path = tmp_path / "中文目录" / "窗口.uipro"
    path.parent.mkdir()
    window.save_service.save(document, path)
    wait_for(lambda: not document.saving, qt_app)
    original = load_project(path).model
    document.execute("修改文本", lambda model: set_property(model, window.registry, key, "text", "保存后的中文"))
    window.save_service.save(document, path)
    wait_for(lambda: not document.saving, qt_app)
    assert load_project(path.with_suffix(".uipro.bak")).model == original
    count = window.tabs.count()
    assert window.open_path(path) is document and window.tabs.count() == count
    window._close_document(document)
    reopened = window.open_path(path)
    assert reopened.model.nodes[key].properties["text"] == "保存后的中文"
    assert not reopened.dirty


def test_save_completion_preserves_text_being_typed(window: MainWindow, qt_app: QApplication, tmp_path: Path) -> None:
    document = window.document
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    window.save_service.save(document, tmp_path / "输入期间保存.uipro")
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    editor.insert("保存期间仍在输入")
    wait_for(lambda: not document.saving, qt_app)
    qt_app.processEvents()
    assert window.properties.editors["text"].text() == "保存期间仍在输入"
    QTest.keyClick(window.properties.editors["text"], Qt.Key.Key_Return)
    qt_app.processEvents()
    assert document.model.nodes[key].properties["text"] == "保存期间仍在输入"
    assert document.dirty


def test_corrupt_open_preserves_current_document(window: MainWindow, tmp_path: Path) -> None:
    original = window.document
    path = tmp_path / "损坏.uipro"
    path.write_text("无效内容", encoding="utf-8")
    with pytest.raises(DesignerError):
        window.open_path(path)
    assert window.document is original and window.tabs.count() == 1


def test_lock_conflict_opens_readonly_then_save_as_unlocks_editing(window: MainWindow, qt_app: QApplication,
                                                                 tmp_path: Path) -> None:
    path = tmp_path / "被占用.uipro"
    commit_project(path, window.document.model, expected_token=None)
    owner = FileLease(path)
    try:
        document = window.open_path(path)
        assert document.read_only
        with pytest.raises(DesignerError, match="只读"):
            document.execute("修改", lambda model: model)
        window.save_service.save(document, tmp_path / "新副本.uipro")
        wait_for(lambda: not document.saving, qt_app)
        assert not document.read_only
        key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
        assert key in document.model.nodes
    finally:
        owner.release()


def test_restore_opens_unsaved_copy(window: MainWindow, qt_app: QApplication) -> None:
    source = window.document
    window.page.canvas.create_component("builtin.label", QPointF(40, 40))
    window.recovery.flush_due(force=True)
    wait_for(lambda: bool(window.recovery.discover(include_active=True)), qt_app)
    restored = window.restore_project(window.recovery.discover(include_active=True)[0])
    assert restored.path is None and restored.dirty
    assert restored.model.to_bytes() == source.model.to_bytes()
    assert restored is not source


def test_close_can_cancel_or_discard(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    document = window.document
    window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    monkeypatch.setattr(main_window, "ask_save", lambda parent, name: "cancel")
    assert not window.request_close(0) and not document.closed
    monkeypatch.setattr(main_window, "ask_save", lambda parent, name: "discard")
    assert window.request_close(0) and document.closed
    assert window.tabs.count() == 0


def test_foreign_format_example_keeps_timer_and_events(window: MainWindow) -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "中文界面示例.uipro"
    document = window.open_path(path)
    assert len(document.model.nodes) == 5
    assert len(document.model.data["connections"]) == 2
    # 时钟现已接入非可视组件区，旧声明仍保留，设计时不会启动。
    timer = next(node for node in document.model.nodes.values() if node.type_id == "builtin.timer")
    assert timer.properties["auto_start"] is True
    assert not window.page.canvas.renderer.tree.widgets[timer.id].isActive()
    assert len(window.page.canvas.renderer.items) == 3


def test_close_waits_for_successful_save(window: MainWindow, qt_app: QApplication, tmp_path: Path) -> None:
    document = window.document
    window.save_service.save(document, tmp_path / "关闭前保存.uipro")
    assert not window.request_close(window.tabs.currentIndex())
    wait_for(lambda: document.closed, qt_app)
    assert window.tabs.count() == 0
    assert load_project(tmp_path / "关闭前保存.uipro").model == document.model


def test_failed_save_does_not_close_document(window: MainWindow, qt_app: QApplication, tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    document = window.document

    def fail(*args: object, **kwargs: object) -> str:
        raise PermissionError("模拟磁盘拒绝写入。")

    monkeypatch.setattr(save_service, "commit_project", fail)
    window.save_service.save(document, tmp_path / "保存失败.uipro")
    assert not window.request_close(window.tabs.currentIndex())
    wait_for(lambda: not document.saving, qt_app)
    assert not document.closed and document.dirty
    assert window.tabs.count() == 1
    assert not (tmp_path / "保存失败.uipro").exists()


@pytest.mark.parametrize("entry", ["canvas", "tree", "tree_keyboard", "create", "new_tab"])
def test_invalid_property_survives_selection_changes(window: MainWindow, qt_app: QApplication, entry: str) -> None:
    canvas, document = window.page.canvas, window.document
    first = canvas.create_component("builtin.button", QPointF(40, 40))
    second = canvas.create_component("builtin.label", QPointF(40, 110))
    document.select(first)
    qt_app.processEvents()
    editor = window.properties.editors["name"]
    editor.setFocus()
    editor.selectAll()
    editor.insert(" ")
    before, cursor = document.model, document.history.cursor
    if entry == "canvas":
        point = canvas.mapFromScene(canvas.renderer.node_rect(second).center())
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    elif entry == "tree":
        tree = window.object_tree
        point = tree.visualItemRect(tree._items[second]).center()
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=point)
    elif entry == "tree_keyboard":
        window.object_tree.setFocus()
        QTest.keyClick(window.object_tree, Qt.Key.Key_Down)
    elif entry == "create":
        assert canvas.create_component("builtin.button", QPointF(200, 40)) is None
    else:
        window.new_document()
    qt_app.processEvents()
    assert window.document is document
    assert document.selected_id == first
    assert window.object_tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == first
    assert window.properties.editors["name"].text() == " "
    assert document.model == before and document.history.cursor == cursor
    # 测试结束前纠正输入，避免它影响测试窗口关闭。
    window.properties.editors["name"].setText(document.model.nodes[first].name)


def test_search_undo_redo_actions_follow_text_history(window: MainWindow, qt_app: QApplication) -> None:
    search = window.properties.search
    search.setFocus()
    QTest.keyClicks(search, "temporary")
    qt_app.processEvents()
    assert not window.document.history.can_undo
    assert window.actions["undo"].isEnabled()
    QTest.keyClick(search, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert search.text() == ""
    assert window.actions["redo"].isEnabled()
    window.actions["redo"].trigger()
    assert search.text() == "temporary"
    assert window.document.history.cursor == 0
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    window.toolbox.tree.setFocus()
    QTest.keyClick(window.toolbox.tree, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert key not in window.document.model.nodes
    QTest.keyClick(window.toolbox.tree, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    assert key in window.document.model.nodes


def test_readonly_output_cannot_undo_design(window: MainWindow, qt_app: QApplication) -> None:
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    window.output.setFocus()
    cursor = window.document.history.cursor
    window.undo()
    assert key in window.document.model.nodes and window.document.history.cursor == cursor


def test_tree_retains_collapsed_branches_after_property_change(window: MainWindow, qt_app: QApplication) -> None:
    canvas, document, tree = window.page.canvas, window.document, window.object_tree
    key = canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    central = document.model.central_id
    tree._items[central].setExpanded(False)
    document.execute("修改文本", lambda model: set_property(model, window.registry, key, "text", "更新文本"))
    qt_app.processEvents()
    assert not tree._items[central].isExpanded()
    assert tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == key


def test_recovery_directory_failure_does_not_break_open_or_release_write_lock(window: MainWindow,
                                                                            tmp_path: Path,
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "可打开的项目.uipro"
    commit_project(path, window.document.model, expected_token=None)
    original_mkdir = Path.mkdir

    def fail_recovery_directory(target: Path, *args: object, **kwargs: object) -> None:
        if target.is_relative_to(window.recovery.directory):
            raise PermissionError("模拟恢复目录失去写权限。")
        original_mkdir(target, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_recovery_directory)
    opened = window.open_path(path)
    assert window.document is opened and not opened.read_only
    assert "自动恢复" in window.output.toPlainText()
    lease = FileLease(path)
    try:
        assert not lease.acquired
    finally:
        lease.release()


def test_return_keeps_property_keyboard_focus(window: MainWindow, qt_app: QApplication) -> None:
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    editor.insert("继续编辑")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qt_app.processEvents()
    editor = window.properties.editors["text"]
    assert editor.hasFocus()
    assert editor.cursorPosition() == len("继续编辑")
    editor.insert("内容")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert window.document.model.nodes[key].properties["text"] == "继续编辑内容"


@pytest.mark.parametrize("entry", ["canvas", "tree"])
def test_valid_pending_input_is_committed_before_selection(window: MainWindow, qt_app: QApplication, entry: str) -> None:
    canvas, document = window.page.canvas, window.document
    first = canvas.create_component("builtin.button", QPointF(40, 40))
    second = canvas.create_component("builtin.label", QPointF(40, 120))
    document.select(first)
    qt_app.processEvents()
    editor = window.properties.editors["text"]
    editor.setFocus()
    editor.selectAll()
    editor.insert("离开前提交")
    cursor = document.history.cursor
    if entry == "canvas":
        point = canvas.mapFromScene(canvas.renderer.node_rect(second).center())
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    else:
        tree = window.object_tree
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=tree.visualItemRect(tree._items[second]).center())
    qt_app.processEvents()
    assert document.selected_id == second
    assert document.model.nodes[first].properties["text"] == "离开前提交"
    assert document.history.cursor == cursor + 1


def test_closed_workbenches_release_focused_editors(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> None:
    initialize(qt_app, configure_logging=False)
    for index in range(3):
        workbench = MainWindow(registry, enable_recovery=False, persist_settings=False,
                               settings=QSettings(str(tmp_path / f"生命周期{index}.ini"), QSettings.Format.IniFormat))
        workbench.show()
        workbench.activateWindow()
        qt_app.processEvents()
        editor = workbench.properties.editors["name"]
        editor.setFocus()
        editor.insert("新")
        reference, editor_reference = weakref.ref(workbench), weakref.ref(editor)
        workbench.discard_all_for_test()
        workbench.close()
        workbench.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qt_app.processEvents()
        del editor, workbench
        gc.collect()
        assert reference() is None and editor_reference() is None
