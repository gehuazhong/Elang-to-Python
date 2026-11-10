"""工作台设置的事务语义、持久化和项目隔离。"""

from dataclasses import replace
import json

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QRect, QSettings, QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDockWidget, QTabWidget

from app.main_window import MainWindow
from app.settings_dialog import SettingsDialog
from app.window_geometry import fit_startup_window
from app.workbench_settings import (SETTINGS_KEY, WorkbenchPreferences, apply_preferences,
                                    current_preferences, load_preferences, save_workbench)
from codegen.generator import generate_files
from core.commands.nodes import create_node


def dispose(window):
    window.discard_all_for_test()
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture
def window(qt_app, registry, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(registry, settings=settings, enable_recovery=False)
    window.show()
    qt_app.processEvents()
    yield window
    dispose(window)


def select(editor, value):
    index = editor.findData(value)
    assert index >= 0
    editor.setCurrentIndex(index)


def test_preview_cancel_restores_layout_and_leaves_settings_unwritten(window, qt_app):
    before = current_preferences(window)
    dialog = SettingsDialog(window)
    dialog.show()
    try:
        select(dialog.font_size, 14)
        select(dialog.density, "comfortable")
        select(dialog.document_tabs, "bottom")
        dialog.status_bar.setChecked(False)
        select(dialog.preset, "right")
        dialog.preset.activated.emit(dialog.preset.currentIndex())
        qt_app.processEvents()
        assert window.font().pointSize() == 14
        assert window.tabs.tabPosition() == QTabWidget.TabPosition.South
        assert window.dockWidgetArea(window.toolbox_dock) == Qt.DockWidgetArea.RightDockWidgetArea
        assert window.statusBar().isHidden()
        assert not window.settings.contains(SETTINGS_KEY)
        dialog.reject()
        qt_app.processEvents()
        assert current_preferences(window) == before
        assert window.toolbox.search.font().pointSize() == before.font_size
        assert window.dockWidgetArea(window.toolbox_dock) == Qt.DockWidgetArea.LeftDockWidgetArea
        assert not window.statusBar().isHidden()
        assert not window.settings.contains(SETTINGS_KEY)
    finally:
        dialog.deleteLater()


def test_apply_cancel_and_restart_use_last_applied_values(window, qt_app, registry):
    dialog = SettingsDialog(window)
    dialog.show()
    try:
        select(dialog.font_size, 12)
        select(dialog.icon_size, 24)
        dialog.main_toolbar.setChecked(False)
        dialog.activity_bar.setChecked(False)
        dialog.status_bar.setChecked(False)
        select(dialog.preset, "compact")
        dialog.preset.activated.emit(dialog.preset.currentIndex())
        qt_app.processEvents()
        assert dialog.apply_changes()
        saved = current_preferences(window)
        select(dialog.font_size, 18)
        dialog.main_toolbar.setChecked(True)
        dialog.reject()
        assert current_preferences(window) == saved
        assert load_preferences(window.settings) == saved
        second = MainWindow(registry, settings=window.settings, enable_recovery=False)
        try:
            second.show()
            qt_app.processEvents()
            assert current_preferences(second) == saved
            assert second.main_toolbar.iconSize().width() == 24
            assert second.object_dock in second.tabifiedDockWidgets(second.toolbox_dock)
            assert second.output_dock.isHidden()
            assert second.layout_restored
        finally:
            dispose(second)
    finally:
        dialog.deleteLater()


def test_font_preview_preserves_project_runtime_export_and_pending_editor(window, qt_app, registry):
    document = window.document
    document.execute("添加按钮", lambda model: create_node(model, registry, "builtin.button", 20, 20)[0])
    before = document.model.to_bytes()
    exports = generate_files(document.model, registry)
    canvas = window.page.canvas
    runtime_font = QFont(canvas.renderer.tree.root.font())
    application_font = QFont(qt_app.font())
    editor = window.properties.editors["name"]
    editor.setText("尚未提交")
    editor.setModified(True)
    apply_preferences(window, replace(current_preferences(window), font_family="Consolas", font_size=20, density="comfortable"))
    qt_app.processEvents()
    assert window.font().pointSize() == 20 and window.toolbox.search.font().pointSize() == 20
    assert qt_app.font() == application_font
    assert canvas.renderer.tree.root.font() == runtime_font
    assert document.model.to_bytes() == before
    assert generate_files(document.model, registry) == exports
    assert window.properties.editors["name"] is editor and editor.text() == "尚未提交"
    group = window.toolbox.tree.topLevelItem(0)
    assert group.font(0).pointSize() == 20
    assert group.child(0).sizeHint(0).height() >= window.toolbox.tree.fontMetrics().height()
    for index in range(window.properties.tree.topLevelItemCount()):
        group = window.properties.tree.topLevelItem(index)
        for row in range(group.childCount()):
            item = group.child(row)
            widget = window.properties.tree.itemWidget(item, 1)
            if widget:
                assert item.sizeHint(1).height() >= widget.sizeHint().height()
                if group.isExpanded() and not item.isHidden():
                    rect = window.properties.tree.visualItemRect(item)
                    assert widget.geometry().top() >= rect.top()
                    assert widget.geometry().bottom() <= rect.bottom()
    editor.setModified(False)
    document.select(next(node.id for node in document.model.nodes.values() if node.type_id == "builtin.button"))
    qt_app.processEvents()
    assert window.properties.editors["text"].font().pointSize() == 20


def test_panel_location_lock_visibility_and_reset_are_reversible(window, qt_app):
    dialog = SettingsDialog(window)
    dialog.show()
    try:
        visible, position = dialog.panel_editors["properties"]
        select(position, "floating")
        position.activated.emit(position.currentIndex())
        assert window.property_dock.isFloating()
        dialog.lock_panels.setChecked(True)
        assert not window.property_dock.isFloating()
        assert not position.isEnabled()
        assert not window.property_dock.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable
        visible.setChecked(False)
        assert window.property_dock.isHidden()
        dialog.reset_defaults()
        qt_app.processEvents()
        assert current_preferences(window) == WorkbenchPreferences()
        assert window.property_dock.isVisible() and position.isEnabled()
        assert dialog.apply_changes()
        dialog.reject()
        assert window.property_dock.isVisible()
    finally:
        dialog.deleteLater()


def test_menu_shortcut_and_window_close_cancel_preview(window, qt_app):
    assert window.actions["settings"].shortcut().toString() == "Ctrl+,"
    before = current_preferences(window)

    def close_dialog():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, SettingsDialog)
        select(dialog.font_size, 15)
        dialog.close()

    QTimer.singleShot(0, close_dialog)
    window.actions["settings"].trigger()
    assert current_preferences(window) == before
    assert not window.settings.contains(SETTINGS_KEY)


@pytest.mark.parametrize("payload", ["invalid", "[]", '{"font_size": 1000, "font_family": "", "density": "unknown", "lock_panels": "true"}'])
def test_bad_preferences_fall_back_safely(tmp_path, payload):
    settings = QSettings(str(tmp_path / "invalid.ini"), QSettings.Format.IniFormat)
    settings.setValue(SETTINGS_KEY, payload)
    assert load_preferences(settings) == WorkbenchPreferences()


def test_existing_layout_is_not_overwritten_on_small_first_start(window, qt_app, registry):
    window.actions["layout_right"].trigger()
    assert window.settings.contains("window/state_v2")
    window.settings.remove("window/geometry")
    second = MainWindow(registry, settings=window.settings, enable_recovery=False)
    try:
        assert second.layout_restored and not second.geometry_restored
        fit_startup_window(second, restored=False, available=QRect(0, 0, 1100, 600))
        assert second.dockWidgetArea(second.toolbox_dock) == Qt.DockWidgetArea.RightDockWidgetArea
        assert not second.output_dock.isHidden()
        assert not second.tabifiedDockWidgets(second.toolbox_dock)
    finally:
        dispose(second)


def test_settings_disabled_for_test_sessions(qt_app, registry, tmp_path):
    settings = QSettings(str(tmp_path / "no-write.ini"), QSettings.Format.IniFormat)
    settings.setValue(SETTINGS_KEY, json.dumps({"font_size": 18}))
    settings.sync()
    window = MainWindow(registry, settings=settings, persist_settings=False, enable_recovery=False)
    try:
        assert window.font().pointSize() == 9
        apply_preferences(window, replace(WorkbenchPreferences(), font_size=12))
        assert save_workbench(window)
        assert load_preferences(settings).font_size == 18
    finally:
        dispose(window)
    assert not settings.contains("window/state_v2")


def test_save_failure_keeps_cancel_baseline_and_previous_settings(window, monkeypatch):
    dialog = SettingsDialog(window)
    before = current_preferences(window)
    try:
        select(dialog.font_size, 16)
        with monkeypatch.context() as patch:
            patch.setattr(window.settings, "status", lambda: QSettings.Status.AccessError)
            assert not dialog.apply_changes()
            assert "保存失败" in dialog.message.text()
        assert not window.settings.contains(SETTINGS_KEY)
        assert not window.settings.contains("window/state_v2")
        dialog.reject()
        assert current_preferences(window) == before
    finally:
        dialog.deleteLater()


def test_enter_confirms_instead_of_resetting_preferences(window, qt_app):
    dialog = SettingsDialog(window)
    try:
        dialog.show()
        qt_app.processEvents()
        select(dialog.font_size, 12)
        assert dialog.ok_button.isDefault() and not dialog.reset_button.isDefault()
        QTest.keyClick(dialog, Qt.Key.Key_Return)
        assert dialog.result() == SettingsDialog.DialogCode.Accepted
        assert load_preferences(window.settings).font_size == 12
    finally:
        dialog.deleteLater()
