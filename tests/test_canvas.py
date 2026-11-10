"""通过真实 Qt 绘制和输入事件检验画布闭环。"""

from __future__ import annotations

from dataclasses import replace

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QDropEvent, QImage, QMouseEvent, QPainter
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel
from core.registry import WidgetRegistry
from designer.canvas import DesignerCanvas
from designer.mime import component_mime
from runtime.builder import RuntimeTree, verify_registry
from tests.benchmark_canvas import project_fixture
from tests.test_storage import wait_for


def mouse_move(canvas: DesignerCanvas, point: QPoint) -> None:
    event = QMouseEvent(QEvent.Type.MouseMove, QPointF(point), QPointF(canvas.viewport().mapToGlobal(point)),
                        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(canvas.viewport(), event)


def test_reflection_and_native_build_are_real(project: ProjectModel, registry: WidgetRegistry,
                                             qt_app: QApplication) -> None:
    verify_registry(registry)
    project, button = create_node(project, registry, "builtin.button", 40, 48)
    project, label = create_node(project, registry, "builtin.label", 40, 112)
    project = set_property(project, registry, label, "text", "<b>这是纯文本</b>")
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "测试状态"))
        assert isinstance(tree.widgets[button], QPushButton)
        assert isinstance(tree.widgets[label], QLabel)
        assert tree.widgets[label].textFormat() == Qt.TextFormat.PlainText
        assert tree.widgets[button].geometry().x() == 40
        image = tree.image(button, 2.0)
        assert image.devicePixelRatio() == 2.0 and image.width() == 240
        assert any(image.pixelColor(x, 40).alpha() > 0 for x in range(image.width()))
    finally:
        tree.dispose()


@pytest.mark.parametrize("zoom", [50, 100, 150, 200])
def test_move_commits_once_and_undo_restores_position(project: ProjectModel, registry: WidgetRegistry,
                                                    qt_app: QApplication, zoom: int) -> None:
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    canvas.resize(1080, 760)
    canvas.show()
    try:
        key = canvas.create_component("builtin.button", QPointF(80, 80))
        canvas.set_zoom(zoom)
        qt_app.processEvents()
        native = canvas.renderer.tree.widgets[key]
        clicks = QSignalSpy(native.clicked)
        original = document.model.nodes[key].geometry
        state, cursor = document.model, document.history.cursor
        point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
        target = point + QPoint(round(40 * zoom / 100), round(24 * zoom / 100))
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        mouse_move(canvas, target)
        assert document.model is state
        assert native.x() == original.x
        assert canvas.renderer.items[key].pos() != QPointF(original.x, original.y)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert document.history.cursor == cursor + 1
        assert document.model.nodes[key].geometry.x == original.x + 40
        assert document.model.nodes[key].geometry.y == original.y + 24
        assert clicks.count() == 0
        document.undo()
        assert document.model.nodes[key].geometry == original
        assert canvas.renderer.items[key].pos() == QPointF(original.x, original.y)
    finally:
        canvas.dispose()
        canvas.close()


def test_escape_and_model_change_cancel_temporary_position(project: ProjectModel, registry: WidgetRegistry,
                                                         qt_app: QApplication) -> None:
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    canvas.resize(1000, 720)
    canvas.show()
    try:
        key = canvas.create_component("builtin.label", QPointF(80, 80))
        qt_app.processEvents()
        original = canvas.renderer.items[key].pos()
        point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
        for cancel_with_edit in (False, True):
            cursor = document.history.cursor
            QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
            mouse_move(canvas, point + QPoint(60, 40))
            if cancel_with_edit:
                document.execute("改文本", lambda model: set_property(model, registry, key, "text", "修改后"))
            else:
                QTest.keyClick(canvas, Qt.Key.Key_Escape)
            QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(60, 40))
            assert canvas.renderer.items[key].pos() == original
            assert document.history.cursor == cursor + (1 if cancel_with_edit else 0)
    finally:
        canvas.dispose()
        canvas.close()


def test_drop_uses_registered_mime_and_correct_coordinates(project: ProjectModel, registry: WidgetRegistry,
                                                         qt_app: QApplication) -> None:
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    canvas.resize(1080, 760)
    canvas.show()
    try:
        qt_app.processEvents()
        point = canvas.mapFromScene(QPointF(104, 136))
        mime = component_mime("builtin.label")
        event = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                           Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        canvas.dropEvent(event)
        assert event.isAccepted()
        node = document.model.nodes[document.selected_id]
        assert node.geometry.x == 104 and node.geometry.y == 136
    finally:
        canvas.dispose()
        canvas.close()


def test_cached_label_preserves_transparent_overlap(project: ProjectModel, registry: WidgetRegistry,
                                                  qt_app: QApplication) -> None:
    project, button = create_node(project, registry, "builtin.button", 40, 40)
    project, label = create_node(project, registry, "builtin.label", 40, 40)
    project = set_property(project, registry, label, "text", "")
    tree = RuntimeTree(registry)
    try:
        tree.apply(compile_plan(project, registry, "测试状态"))
        image = tree.image(label, 1.0)
        assert image.pixelColor(60, 16).alpha() == 0
    finally:
        tree.dispose()


def test_large_build_yields_and_publishes_once(registry: WidgetRegistry, qt_app: QApplication) -> None:
    document = DocumentSession(project_fixture(300), registry)
    canvas = DesignerCanvas(document)
    pulses: list[int] = []
    timer = QTimer()
    timer.setInterval(0)
    timer.timeout.connect(lambda: pulses.append(1))
    timer.start()
    try:
        assert not canvas.ready and document.editing_suspended
        assert len(canvas.renderer.items) == 0
        canvas.show()
        wait_for(lambda: canvas.ready, qt_app)
        assert len(canvas.renderer.items) == 300
        assert len(canvas.build_batch_times) > 1 and len(pulses) > 1
        assert not document.editing_suspended
    finally:
        timer.stop()
        canvas.dispose()
        canvas.close()


def test_cancel_large_build_releases_unpublished_widgets(registry: WidgetRegistry, qt_app: QApplication) -> None:
    document = DocumentSession(project_fixture(300), registry)
    canvas = DesignerCanvas(document)
    canvas._advance_build()
    root = canvas._candidate.tree.root
    destroyed = QSignalSpy(root.destroyed)
    canvas.dispose()
    canvas.close()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert destroyed.count() == 1
    assert not document.editing_suspended


def test_reflection_can_be_verified_after_widgets_are_destroyed(registry: WidgetRegistry, qt_app: QApplication) -> None:
    for _ in range(3):
        verify_registry(registry)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_ten_document_cycles_destroy_native_roots(registry: WidgetRegistry, qt_app: QApplication) -> None:
    for _ in range(10):
        document = DocumentSession(project_fixture(20), registry)
        canvas = DesignerCanvas(document)
        root = canvas.renderer.tree.root
        destroyed = QSignalSpy(root.destroyed)
        canvas.dispose()
        canvas.close()
        canvas.deleteLater()
        document.close()
        document.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert destroyed.count() == 1


def test_failed_image_refresh_retries_all_pending_nodes(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    project, first = create_node(project, registry, "builtin.button", 40, 40)
    project, second = create_node(project, registry, "builtin.label", 40, 120)
    document = DocumentSession(project, registry)
    canvas = DesignerCanvas(document)
    renderer = canvas.renderer
    original_image = renderer.tree.image
    attempts: list[str] = []

    def fail_once(node_id: str, ratio: float) -> QImage:
        attempts.append(node_id)
        if len(attempts) == 1:
            raise DesignerError("模拟绘制缓存暂时不可用。")
        return original_image(node_id, ratio)

    try:
        old = {key: renderer.items[key].pixmap().cacheKey() for key in (first, second)}
        monkeypatch.setattr(renderer.tree, "image", fail_once)
        document.execute("修改窗口字体", lambda model: set_property(model, registry, model.root_id, "font_size", 16))
        assert len(attempts) == 1
        canvas.refresh()
        assert attempts.count(first) == 2 and attempts.count(second) == 1
        assert all(renderer.items[key].pixmap().cacheKey() != old[key] for key in old)
        assert renderer.plan.state_id == document.state_id
    finally:
        canvas.dispose()
        canvas.close()


def test_failed_zoom_restores_previous_scale(project: ProjectModel, registry: WidgetRegistry,
                                            qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    project, key = create_node(project, registry, "builtin.button", 40, 40)
    canvas = DesignerCanvas(DocumentSession(project, registry))
    original_image = canvas.renderer.tree.image

    def limited_image(node_id: str, ratio: float) -> QImage:
        if ratio > 1.0:
            raise DesignerError("模拟缩放后的缓存超限。")
        return original_image(node_id, ratio)

    try:
        monkeypatch.setattr(canvas.renderer.tree, "image", limited_image)
        errors = QSignalSpy(canvas.error)
        canvas.set_zoom(200)
        assert canvas.zoom == 100 and canvas.transform().m11() == 1.0
        assert canvas.renderer.ratio == 1.0
        assert canvas.renderer.items[key].pixmap().devicePixelRatio() == 1.0
        assert errors.count() == 1
    finally:
        canvas.dispose()
        canvas.close()
