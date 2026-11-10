"""原大编辑、左上定位、显式缩放和滚动后拖放坐标的回归。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QDropEvent, QWheelEvent
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from core.commands.nodes import set_property
from core.document import DocumentSession
from core.registry import WidgetRegistry
from core.storage import commit_project
from designer.canvas import DesignerCanvas
from designer.mime import component_mime
from tests.benchmark_canvas import project_fixture
from tests.test_clipboard import window
from tests.test_storage import wait_for


def send_wheel(canvas: DesignerCanvas, delta: int, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
               position: QPoint = QPoint(220, 180), pixel_delta: int = 0) -> None:
    event = QWheelEvent(QPointF(position), QPointF(canvas.viewport().mapToGlobal(position)), QPoint(0, pixel_delta),
                        QPoint(0, delta), Qt.MouseButton.NoButton, modifiers, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(canvas.viewport(), event)


@pytest.mark.parametrize("size", [(960, 620), (1480, 980)])
def test_new_document_opens_at_original_size_in_top_left(window: MainWindow, qt_app: QApplication,
                                                        size: tuple[int, int]) -> None:
    window.resize(*size)
    qt_app.processEvents()
    window.new_document()
    qt_app.processEvents()
    canvas = window.page.canvas
    assert canvas.zoom == 100 and canvas.transform().isIdentity()
    assert canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20)
    start, end = canvas.mapFromScene(QPointF()), canvas.mapFromScene(QPointF(120, 32))
    assert end - start == QPoint(120, 32)
    before = canvas.mapToScene(QPoint())
    window.resize(1100, 760)
    qt_app.processEvents()
    assert canvas.zoom == 100 and canvas.mapToScene(QPoint()) == before


def test_reopen_large_window_uses_scrollbars_without_changing_project(window: MainWindow, qt_app: QApplication,
                                                                   tmp_path: Path) -> None:
    document = window.document
    project = set_property(document.model, window.registry, document.model.root_id, "geometry.width", 1600)
    project = set_property(project, window.registry, project.root_id, "geometry.height", 1200)
    path = tmp_path / "原大设计窗口.uipro"
    commit_project(path, project, expected_token=None)
    loaded = window.open_path(path)
    qt_app.processEvents()
    canvas = window.page.canvas
    assert canvas.zoom == 100
    assert canvas.horizontalScrollBar().maximum() > canvas.horizontalScrollBar().minimum()
    assert canvas.verticalScrollBar().maximum() > canvas.verticalScrollBar().minimum()
    assert loaded.model.to_bytes() == project.to_bytes() and not loaded.dirty
    canvas.fit_to_window()
    assert canvas.zoom < 100
    assert loaded.model.to_bytes() == project.to_bytes() and loaded.history.cursor == 0
    window.actions["original_size"].trigger()
    qt_app.processEvents()
    assert canvas.zoom == 100
    assert canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20)
    assert loaded.model.to_bytes() == project.to_bytes() and not loaded.dirty
    assert window.actions["original_size"].shortcut().toString() == "Ctrl+0"
    assert window.actions["fit"].shortcut().toString() == "Ctrl+9"


def test_switching_tabs_preserves_independent_zoom_and_scroll(window: MainWindow, qt_app: QApplication) -> None:
    first = window.page
    first.canvas.set_zoom(150)
    first.canvas.horizontalScrollBar().setValue(160)
    first.canvas.verticalScrollBar().setValue(120)
    origin = first.canvas.mapToScene(QPoint())
    window.new_document()
    qt_app.processEvents()
    assert window.page.canvas.zoom == 100
    window.tabs.setCurrentWidget(first)
    qt_app.processEvents()
    assert first.canvas.zoom == 150 and first.canvas.mapToScene(QPoint()) == origin
    assert window.zoom_combo.currentData() == 150


def test_scroll_wheel_never_scales_without_control(window: MainWindow, qt_app: QApplication) -> None:
    canvas = window.page.canvas
    window.resize(960, 620)
    qt_app.processEvents()
    origin = canvas.mapToScene(QPoint())
    send_wheel(canvas, -120)
    assert canvas.zoom == 100 and canvas.mapToScene(QPoint()).y() > origin.y()
    position = QPoint(220, 180)
    anchor = canvas.mapToScene(position)
    send_wheel(canvas, 120, Qt.KeyboardModifier.ControlModifier, position)
    assert canvas.zoom == 125
    assert (canvas.mapFromScene(anchor) - position).manhattanLength() <= 2
    send_wheel(canvas, 0, Qt.KeyboardModifier.ControlModifier, position)
    assert canvas.zoom == 125
    send_wheel(canvas, 0, Qt.KeyboardModifier.ControlModifier, position, pixel_delta=15)
    assert canvas.zoom == 150


def test_drop_after_scrolling_keeps_document_coordinates(window: MainWindow, qt_app: QApplication) -> None:
    window.resize(960, 620)
    qt_app.processEvents()
    canvas = window.page.canvas
    canvas.horizontalScrollBar().setValue(150)
    canvas.verticalScrollBar().setValue(100)
    point = canvas.mapFromScene(QPointF(248, 224))
    assert canvas.viewport().rect().contains(point)
    mime = component_mime("builtin.button")
    event = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    origin = canvas.mapToScene(QPoint())
    canvas.dropEvent(event)
    assert event.isAccepted()
    node = window.document.model.nodes[window.document.selected_id]
    assert (node.geometry.x, node.geometry.y) == (248, 224)
    assert canvas.zoom == 100 and canvas.mapToScene(QPoint()) == origin
    window.document.undo()
    assert node.id not in window.document.model.nodes


def test_delayed_large_build_stays_original_size(registry: WidgetRegistry, qt_app: QApplication) -> None:
    document = DocumentSession(project_fixture(150), registry)
    canvas = DesignerCanvas(document)
    try:
        canvas.resize(400, 300)
        canvas.show()
        canvas.resize(900, 700)
        wait_for(lambda: canvas.ready, qt_app)
        qt_app.processEvents()
        assert canvas.zoom == 100
        assert canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20)
        assert len(canvas.renderer.items) == 150
    finally:
        canvas.dispose()
        canvas.close()


def test_explicit_fit_during_large_build_can_be_cancelled(registry: WidgetRegistry, qt_app: QApplication) -> None:
    canvas = DesignerCanvas(DocumentSession(project_fixture(150), registry))
    try:
        canvas.resize(600, 400)
        canvas.show()
        canvas.fit_to_window()
        canvas.reset_view()
        wait_for(lambda: canvas.ready, qt_app)
        assert canvas.zoom == 100
        assert canvas.mapFromScene(canvas.renderer.frame.rect().topLeft()) == QPoint(20, 20)
    finally:
        canvas.dispose()
        canvas.close()
