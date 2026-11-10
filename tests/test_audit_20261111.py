"""Regression coverage for command context and item-based view refreshes."""

from pathlib import Path
from threading import Event

import pytest
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QTreeWidgetItem
from shiboken6 import isValid

from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.recovery import RecoveryService
from core.storage import commit_project, load_project
from runtime.builder import RuntimeTree
from tests.test_workbench_commands import window


def choose_command(window, text):
    observed = []

    def choose():
        dialog = QApplication.activeModalWidget()
        try:
            dialog.search.setFocus()
            QApplication.processEvents()
            dialog.search.setText(text)
            item = dialog.results.topLevelItem(0)
            observed.append(item is not None and not item.isDisabled())
            if observed[-1]:
                dialog.results.setCurrentItem(item)
                QTest.keyClick(dialog.search, Qt.Key.Key_Return)
        finally:
            if dialog.isVisible():
                dialog.reject()

    QTimer.singleShot(0, choose)
    window.show_commands()
    assert observed == [True]


@pytest.mark.parametrize("command", ["排版 等宽高", "编辑 撤销"])
def test_palette_keeps_canvas_command_context(window, qt_app, command):
    document = window.document
    keys = []

    def populate(model):
        for kind, x in (("button", 40), ("label", 200)):
            model, key = create_node(model, window.registry, "builtin." + kind, x, 40)
            keys.append(key)
        return model

    document.execute("populate", populate)
    document.select_many(tuple(keys))
    window.page.canvas.setFocus()
    qt_app.processEvents()
    cursor = document.history.cursor
    choose_command(window, command)
    if command.endswith("撤销"):
        assert document.history.cursor == cursor - 1
    else:
        assert document.history.cursor == cursor + 1
        first, second = (document.model.nodes[key].geometry for key in keys)
        assert (first.width, first.height) == (second.width, second.height)


@pytest.mark.parametrize("sort_column", [0, 1])
def test_sorted_table_refresh_keeps_cells_in_their_rows(project, registry, qt_app, sort_column):
    project, key = create_node(project, registry, "builtin.table_widget", 20, 20)
    project = set_property(project, registry, key, "sorting", True)
    data = {"headers": ["ID", "Value"], "rows": [["c", "3"], ["a", "1"], ["b", "2"]]}
    project = set_property(project, registry, key, "table_data", data)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        widget.sortItems(sort_column, Qt.SortOrder.AscendingOrder)
        data = {**data, "rows": [["z", "9"], ["x", "7"], ["y", "8"]]}
        project = set_property(project, registry, key, "table_data", data)
        tree.apply(compile_plan(project, registry, "content"))
        actual = [[widget.item(row, column).text() if widget.item(row, column) else None
                   for column in range(2)] for row in range(3)]
        assert actual == [["x", "7"], ["y", "8"], ["z", "9"]]
        assert widget.isSortingEnabled()
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ["list_widget", "table_widget", "tree_widget", "super_list"])
def test_item_view_style_refresh_preserves_item_and_selection(project, registry, qt_app, kind):
    project, key = create_node(project, registry, "builtin." + kind, 20, 20)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        if kind == "list_widget":
            item = widget.item(0)
            widget.setCurrentItem(item)
            item.setText("user edit")
        elif kind == "table_widget":
            item = widget.item(0, 0)
            widget.setCurrentItem(item)
            item.setText("user edit")
        else:
            item = widget.topLevelItem(0)
            widget.setCurrentItem(item)
            item.setText(0, "user edit")
            item.setExpanded(False)
        project = set_property(project, registry, key, "foreground_color", "#246b92")
        tree.apply(compile_plan(project, registry, "style"))
        assert isValid(item)
        assert widget.currentItem() is item
        assert (item.text(0) if kind in {"tree_widget", "super_list"} else item.text()) == "user edit"
        if kind == "tree_widget":
            assert not item.isExpanded()
    finally:
        tree.dispose()


@pytest.mark.parametrize("operation", ["open", "save", "export"])
@pytest.mark.parametrize("value", [123, ["invalid"], "\x00invalid"])
def test_invalid_file_directory_settings_fall_back_to_home(window, monkeypatch, operation, value):
    key = "files/export_directory" if operation == "export" else "files/default_directory"
    window.settings.setValue(key, value)
    seen = []

    def choose(parent, initial, *, save=False):
        seen.append(initial.parent if save else initial)
        return None

    def choose_export(parent, title, directory, options):
        seen.append(Path(directory))
        return ""

    monkeypatch.setattr("app.main_window.choose_project_file", choose)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", choose_export)
    {"open": window.open_dialog, "save": window.save_current, "export": window.export_python_dialog}[operation]()
    assert seen == [Path.home()]


def test_recovery_shutdown_releases_document_subscriptions(project, registry, qt_app, tmp_path):
    document = DocumentSession(project, registry)
    baseline = len(document._listeners)
    service = RecoveryService(tmp_path / "recovery")
    service.watch(document)
    assert len(document._listeners) == baseline + 1
    service.shutdown()
    assert len(document._listeners) == baseline
    assert not service._watches
    service.flush_due(force=True)
    service.shutdown()


def test_combo_style_refresh_preserves_current_selection(project, registry, qt_app):
    project, key = create_node(project, registry, "builtin.combo_box", 20, 20)
    project = set_property(project, registry, key, "items", ["first", "second", "third"])
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        widget.setCurrentIndex(2)
        project = set_property(project, registry, key, "foreground_color", "#246b92")
        tree.apply(compile_plan(project, registry, "style"))
        assert widget.currentIndex() == 2
    finally:
        tree.dispose()


@pytest.mark.parametrize("kind", ["tree_widget", "tree_view"])
def test_tree_expansion_changes_only_with_content_or_expanded_setting(project, registry, qt_app, kind):
    project, key = create_node(project, registry, "builtin." + kind, 20, 20)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        index = widget.model().index(0, 0)
        widget.setExpanded(index, False)
        project = set_property(project, registry, key, "foreground_color", "#246b92")
        tree.apply(compile_plan(project, registry, "style"))
        assert not widget.isExpanded(index)
        for expanded in (False, True):
            project = set_property(project, registry, key, "expanded", expanded)
            tree.apply(compile_plan(project, registry, str(expanded)))
            assert widget.isExpanded(widget.model().index(0, 0)) == expanded
        project = set_property(project, registry, key, "tree_data", [
            {"text": "new", "children": [{"text": "child", "children": []}]}])
        tree.apply(compile_plan(project, registry, "content"))
        assert widget.model().index(0, 0).data() == "new"
        assert widget.isExpanded(widget.model().index(0, 0))
    finally:
        tree.dispose()


def test_super_list_check_and_edit_settings_update_retained_rows(project, registry, qt_app):
    project, key = create_node(project, registry, "builtin.super_list", 20, 20)
    project = set_property(project, registry, key, "checkboxes", True)
    project = set_property(project, registry, key, "editable", True)
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        item = widget.topLevelItem(0)
        assert type(item.data(0, Qt.ItemDataRole.CheckStateRole)) is int
        item.setCheckState(0, Qt.CheckState.Checked)
        project = set_property(project, registry, key, "row_height", 40)
        tree.apply(compile_plan(project, registry, "height"))
        assert widget.topLevelItem(0) is item
        assert item.checkState(0) == Qt.CheckState.Checked
        assert item.sizeHint(0).height() == 40
        for name in ("checkboxes", "editable"):
            project = set_property(project, registry, key, name, False)
        tree.apply(compile_plan(project, registry, "flags"))
        assert not item.flags() & (Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable)
        assert item.data(0, Qt.ItemDataRole.CheckStateRole) is None
        project = set_property(project, registry, key, "checkboxes", True)
        project = set_property(project, registry, key, "checked_rows", ["1"])
        tree.apply(compile_plan(project, registry, "checks"))
        assert item.checkState(0) == Qt.CheckState.Checked
        assert widget.topLevelItem(0) is item
    finally:
        tree.dispose()


def test_super_list_preserves_runtime_rows_without_design_metadata(project, registry, qt_app):
    project, key = create_node(project, registry, "builtin.super_list", 20, 20)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        tree.apply(compile_plan(project, registry, "initial"))
        widget = tree.widgets[key]
        added = QTreeWidgetItem(widget, ["runtime row"])
        project = set_property(project, registry, key, "checkboxes", True)
        tree.apply(compile_plan(project, registry, "checks"))
        assert isValid(added) and added.text(0) == "runtime row"
        assert type(added.data(0, Qt.ItemDataRole.CheckStateRole)) is int
        assert added.checkState(0) == Qt.CheckState.Unchecked
    finally:
        tree.dispose()


@pytest.mark.parametrize("saved", [False, True])
def test_shutdown_waits_for_recovery_and_archives_only_saved_snapshots(project, registry, qt_app,
                                                                     tmp_path, monkeypatch, saved):
    document = DocumentSession(project, registry)
    service = RecoveryService(tmp_path / "recovery")
    started, release = Event(), Event()

    def delayed_commit(*args, **kwargs):
        started.set()
        assert release.wait(5)
        return commit_project(*args, **kwargs)

    monkeypatch.setattr("core.recovery.commit_project", delayed_commit)
    try:
        service.watch(document)
        path = service._watches[document.session_id].path
        service.flush_due(force=True)
        assert started.wait(5)
        if saved:
            target = tmp_path / "saved.uipro"
            ticket = document.begin_save(target, None)
            token = commit_project(target, document.model, expected_token=None)
            document.finish_save(ticket, success=True, token=token)
            service.mark_saved(document)
        release.set()
        service.shutdown()
        qt_app.processEvents()
        assert service.discover() == ([] if saved else [path])
        assert load_project(path.with_name("dismissed.uipro") if saved else path).model == project
    finally:
        release.set()
        service.shutdown()
