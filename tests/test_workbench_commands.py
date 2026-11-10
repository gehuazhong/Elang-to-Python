"""Workbench navigation uses existing commands and preserves document semantics."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QSettings, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton
from shiboken6 import isValid

from app.command_palette import CommandPalette
from app.main_window import MainWindow


@pytest.fixture
def window(qt_app, registry, tmp_path):
    result = MainWindow(registry, settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    result.show()
    qt_app.processEvents()
    yield result
    result.discard_all_for_test()
    result.close()
    result.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_palette_filter_keyboard_and_menu_lifetime(window, qt_app):
    recent = window.recent_menu
    placeholder = recent.actions()[0]
    for _ in range(3):
        palette = CommandPalette(window.menuBar(), window)
        palette.show()
        qt_app.processEvents()
        palette.search.setText("视图 网格")
        assert palette.results.topLevelItemCount() == 2
        first = palette.results.currentItem()
        QTest.keyClick(palette.search, Qt.Key.Key_Down)
        assert palette.results.currentItem() is not first
        QTest.keyClick(palette.search, Qt.Key.Key_Up)
        assert palette.results.currentItem() is first
        palette.search.setText("ctrl+shift+e")
        assert palette.results.topLevelItemCount() == 1
        assert "导出 Python" in palette.results.currentItem().text(0)
        palette.search.setText("无此命令")
        assert palette.results.topLevelItemCount() == 0
        palette.accept()
        assert palette.isVisible()
        QTest.keyClick(palette.search, Qt.Key.Key_Escape)
        assert palette.selected_action is None
        palette.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert isValid(recent) and isValid(placeholder)
        assert recent.actions() == [placeholder]


def test_palette_executes_one_existing_command_and_undo(window, qt_app):
    before = window.document.model
    cursor = window.document.history.cursor

    def choose():
        palette = QApplication.activeModalWidget()
        assert isinstance(palette, CommandPalette)
        palette.search.setText("显示网格")
        QTest.keyClick(palette.search, Qt.Key.Key_Return)

    QTimer.singleShot(0, choose)
    window.actions["commands"].trigger()
    assert window.document.history.cursor == cursor + 1
    assert window.document.model.data["canvas"]["show_grid"] != before.data["canvas"]["show_grid"]
    window.document.undo()
    assert window.document.model == before


def test_palette_disabled_command_cannot_run(window, qt_app):
    palette = CommandPalette(window.menuBar(), window)
    palette.show()
    palette.search.setText("编辑 撤销")
    item = palette.results.topLevelItem(0)
    assert item is not None and item.isDisabled()
    palette.results.setCurrentItem(item)
    palette.accept()
    assert palette.selected_action is None and palette.isVisible()
    palette.reject()
    palette.deleteLater()


def test_palette_tolerates_recent_menu_refresh(window, qt_app):
    recent = window.recent_menu.addAction("recent-project.uipro")
    palette = CommandPalette(window.menuBar(), window)
    palette.search.setText("recent-project")
    assert palette.results.topLevelItemCount() == 1
    window.clear_recent_projects()
    assert not isValid(recent)
    palette.accept()
    assert palette.selected_action is None
    palette.search.clear()
    assert all("recent-project" not in palette.results.topLevelItem(i).text(0)
               for i in range(palette.results.topLevelItemCount()))
    palette.deleteLater()


def test_activity_buttons_restore_panels_without_document_edits(window, qt_app):
    before = window.document.model.to_bytes()
    for dock in (window.toolbox_dock, window.property_dock, window.object_dock, window.output_dock):
        action = dock.toggleViewAction()
        button = window.activity_bar.widgetForAction(action)
        assert button is not None and button.isChecked()
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        assert not dock.isVisible() and not button.isChecked()
        action.trigger()
        qt_app.processEvents()
        assert dock.isVisible() and button.isChecked()
    assert window.document.model.to_bytes() == before


def test_empty_workspace_can_create_document(window, qt_app):
    window.discard_all_for_test()
    qt_app.processEvents()
    assert window.welcome.isVisible() and not window.tabs.isVisible()
    assert window.document_status.text() == "未打开项目"
    button = next(button for button in window.welcome.findChildren(QPushButton)
                  if button.text().startswith("新建"))
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()
    assert window.document is not None and window.tabs.isVisible()
    assert not window.welcome.isVisible()
    assert window.document_status.text() == "未保存"


def test_component_search_expands_matches_and_handles_no_results(window, qt_app):
    box = window.toolbox
    box.tree.collapseAll()
    box.search.setText("BUTTON")
    assert not box.empty_hint.isVisible()
    groups = [box.tree.topLevelItem(i) for i in range(box.tree.topLevelItemCount())]
    assert all(group.isExpanded() for group in groups if not group.isHidden())
    box.search.setText("不存在的组件")
    assert box.empty_hint.isVisible()
    box.search.clear()
    assert not box.empty_hint.isVisible()
