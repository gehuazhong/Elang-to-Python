"""窗口边框、外观属性、坐标及旧项目兼容性的回归。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from PySide6.QtCore import QPointF, QSettings, QTimer, Qt
from PySide6.QtGui import QColor, QDropEvent, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QColorDialog, QComboBox

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import commit_project, load_project
from designer.canvas import DesignerCanvas
from designer.mime import component_mime
from panels.color_editor import ColorEditor
from runtime.builder import RuntimeTree


@pytest.fixture
def designed_window(qt_app: QApplication, registry: WidgetRegistry, tmp_path: Path) -> Iterator[MainWindow]:
    initialize(qt_app, configure_logging=False)
    window = MainWindow(registry, settings=QSettings(str(tmp_path / "设置.ini"), QSettings.Format.IniFormat),
                        enable_recovery=False, persist_settings=False)
    window.show()
    qt_app.processEvents()
    try:
        yield window
    finally:
        window.discard_all_for_test()
        window.close()
        window.deleteLater()
        qt_app.processEvents()


@pytest.mark.parametrize("border", ["standard", "fixed", "none"])
def test_border_keeps_content_geometry_and_rejects_titlebar_drop(project: ProjectModel, registry: WidgetRegistry,
                                                               qt_app: QApplication, border: str) -> None:
    project = set_property(project, registry, project.root_id, "border_style", border)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    canvas.resize(1080, 760)
    canvas.show()
    try:
        key = canvas.create_component("builtin.button", QPointF(80, 80))
        qt_app.processEvents()
        assert canvas.renderer.items[key].pos() == QPointF(80, 80)
        assert canvas.renderer.surface.rect().topLeft() == QPointF(0, 0)
        assert canvas.renderer.surface.rect().width() == 800
        frame = canvas.renderer.frame
        assert frame.rect().top() == (0 if border == "none" else -39)
        assert frame.frameless == (border == "none")
        point = canvas.mapFromScene(QPointF(150, -18))
        mime = component_mime("builtin.button")
        drop = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                          Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        count = len(document.model.nodes)
        canvas.dropEvent(drop)
        assert not drop.isAccepted() and len(document.model.nodes) == count
        QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        assert document.selected_id == document.model.root_id
    finally:
        canvas.dispose()
        canvas.close()


def test_real_window_flags_fixed_size_and_undo(project: ProjectModel, registry: WidgetRegistry,
                                             qt_app: QApplication) -> None:
    document = DocumentSession(project, registry)
    tree = RuntimeTree(registry, design_mode=False)
    try:
        document.execute("固定边框", lambda model: set_property(model, registry, model.root_id, "border_style", "fixed"))
        tree.apply(compile_plan(document.model, registry, document.state_id))
        assert tree.root.minimumSize() == tree.root.maximumSize()
        assert not tree.root.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint
        document.undo()
        tree.apply(compile_plan(document.model, registry, document.state_id))
        assert tree.root.minimumWidth() == 0 and tree.root.maximumWidth() > 800
        assert tree.root.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint
        for key, value in (("border_style", "none"), ("stay_on_top", True)):
            document.execute("窗口属性", lambda model, k=key, v=value: set_property(model, registry, model.root_id, k, v))
        tree.apply(compile_plan(document.model, registry, document.state_id))
        assert tree.root.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert tree.root.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        assert tree.root.pos().x() == 100 and tree.root.pos().y() == 100
    finally:
        tree.dispose()


@pytest.mark.parametrize("key,button,flag", [
    ("minimize_button", "minimize", Qt.WindowType.WindowMinimizeButtonHint),
    ("maximize_button", "maximize", Qt.WindowType.WindowMaximizeButtonHint),
    ("close_button", "close", Qt.WindowType.WindowCloseButtonHint),
])
def test_window_buttons_follow_native_flags_and_undo(project: ProjectModel, registry: WidgetRegistry,
                                                    qt_app: QApplication, key: str, button: str,
                                                    flag: Qt.WindowType) -> None:
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    try:
        assert button in canvas.renderer.frame.buttons
        document.execute("隐藏窗口按钮", lambda model: set_property(model, registry, model.root_id, key, False))
        assert not canvas.renderer.tree.root.windowFlags() & flag
        assert button not in canvas.renderer.frame.buttons
        document.undo()
        assert canvas.renderer.tree.root.windowFlags() & flag
        assert button in canvas.renderer.frame.buttons
    finally:
        canvas.dispose()
        canvas.close()


def test_background_font_inheritance_reset_and_save(project: ProjectModel, registry: WidgetRegistry,
                                                  qt_app: QApplication, tmp_path: Path) -> None:
    project, label = create_node(project, registry, "builtin.label", 40, 48)
    project = set_property(project, registry, label, "text", "")
    tree = RuntimeTree(registry)
    try:
        for key, value in (("background_color", "#edf4fc"), ("foreground_color", "#334455"), ("font_size", 17)):
            project = set_property(project, registry, project.root_id, key, value)
        tree.apply(compile_plan(project, registry, "外观甲"))
        central = tree.widgets[project.central_id]
        assert central.palette().color(QPalette.ColorRole.Window).name() == "#edf4fc"
        assert tree.widgets[label].font().pointSize() == 17
        assert tree.widgets[label].palette().color(QPalette.ColorRole.WindowText).name() == "#334455"
        assert tree.image(label, 1.0).pixelColor(60, 16).alpha() == 0
        project = set_property(project, registry, label, "background_color", "#ffeedd")
        tree.apply(compile_plan(project, registry, "外观乙"))
        assert tree.image(label, 1.0).pixelColor(60, 16).name() == "#ffeedd"
        project = set_property(project, registry, label, "background_color", "")
        project = set_property(project, registry, project.root_id, "font_size", 0)
        tree.apply(compile_plan(project, registry, "外观丙"))
        assert tree.image(label, 1.0).pixelColor(60, 16).alpha() == 0
        assert tree.widgets[label].font().pointSize() == qt_app.font().pointSize()
        path = tmp_path / "窗口外观.uipro"
        commit_project(path, project, expected_token=None)
        assert load_project(path).model.to_bytes() == project.to_bytes()
    finally:
        tree.dispose()


@pytest.mark.parametrize("key,value", [("background_color", "red"), ("background_color", "#fff;"),
                                     ("font_size", True), ("font_size", -1), ("font_size", 97),
                                     ("border_style", "不存在的边框")])
def test_invalid_appearance_is_rejected_without_changing_document(project: ProjectModel, registry: WidgetRegistry,
                                                                qt_app: QApplication, key: str, value: object) -> None:
    document = DocumentSession(project, registry)
    with pytest.raises(DesignerError):
        document.execute("无效属性", lambda model: set_property(model, registry, model.root_id, key, value))
    assert document.model is project and document.history.cursor == 0


def test_window_panel_filter_actions_and_editor_theme_are_independent(designed_window: MainWindow,
                                                                   qt_app: QApplication) -> None:
    window = designed_window
    document = window.document
    panel = window.properties
    assert window.dockWidgetArea(window.object_dock) == Qt.DockWidgetArea.LeftDockWidgetArea
    assert window.page.canvas.renderer.tree.root.styleSheet() == ""
    assert window.page.canvas.zoom == 100
    editor = panel.editors["border_style"]
    assert isinstance(editor, QComboBox)
    editor.setCurrentIndex(editor.findData("none"))
    editor.activated.emit(editor.currentIndex())
    qt_app.processEvents()
    assert window.page.canvas.renderer.frame.frameless
    assert not panel.editors["close_button"].isEnabled()
    document.undo()
    qt_app.processEvents()
    assert not window.page.canvas.renderer.frame.frameless
    assert isinstance(panel.editors["close_button"], QCheckBox)
    assert panel.editors["close_button"].isEnabled()
    panel.search.setText("边框")
    visible = [panel.tree.topLevelItem(i).text(0) for i in range(panel.tree.topLevelItemCount())
               if not panel.tree.topLevelItem(i).isHidden()]
    assert visible == ["窗口"]
    panel.search.clear()
    color = panel.editors["background_color"]
    assert isinstance(color, ColorEditor)
    color.line_edit.setText("#eef5fb")
    color.line_edit.editingFinished.emit()
    qt_app.processEvents()
    assert window.page.canvas.renderer.surface.brush().color().name() == "#eef5fb"
    key = window.page.canvas.create_component("builtin.button", QPointF(40, 40))
    qt_app.processEvents()
    assert document.selected_id == key
    window.property_dock.hide()
    window.page.window_button.click()
    qt_app.processEvents()
    assert document.selected_id == document.model.root_id
    assert "border_style" in panel.editors
    assert window.property_dock.isVisible()


@pytest.mark.parametrize("accepted", [True, False])
def test_color_dialog_commits_only_after_accepting(designed_window: MainWindow, qt_app: QApplication,
                                                  accepted: bool) -> None:
    window = designed_window
    editor = window.properties.editors["background_color"]
    cursor = window.document.history.cursor

    def finish_dialog() -> None:
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QColorDialog)
        dialog.setCurrentColor(QColor("#ddeeff"))
        dialog.accept() if accepted else dialog.reject()

    QTimer.singleShot(0, finish_dialog)
    editor.button.click()
    qt_app.processEvents()
    assert window.document.history.cursor == cursor + int(accepted)
    assert window.page.canvas.renderer.surface.brush().color().name() == ("#ddeeff" if accepted else "#ffffff")
