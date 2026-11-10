"""真实鼠标事件覆盖缩放、取消、屏幕缩放与键盘微调。"""

from __future__ import annotations

from dataclasses import replace

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.commands.nodes import create_node, set_property
from core.document import DocumentSession
from core.errors import DesignerError
from core.models import ProjectModel, Rect
from core.registry import WidgetRegistry
from designer.canvas import DesignerCanvas
from designer.geometry import resized_rect


def move_pointer(canvas: DesignerCanvas, point: QPoint, *, shift: bool = False) -> None:
    event = QMouseEvent(QEvent.Type.MouseMove, QPointF(point), QPointF(canvas.viewport().mapToGlobal(point)),
                        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(canvas.viewport(), event)


def populated_canvas(project: ProjectModel, registry: WidgetRegistry) -> tuple[DesignerCanvas, str]:
    project, key = create_node(project, registry, "builtin.button", 80, 80)
    project = set_property(project, registry, key, "geometry.width", 160)
    project = set_property(project, registry, key, "geometry.height", 96)
    document = DocumentSession(project, registry, saved=True)
    canvas = DesignerCanvas(document)
    canvas.resize(1080, 780)
    canvas.show()
    document.select(key)
    return canvas, key


@pytest.mark.parametrize("zoom", [50, 100, 150, 200])
@pytest.mark.parametrize("handle", ["nw", "n", "ne", "w", "e", "sw", "s", "se"])
def test_all_handles_commit_one_command_and_undo_exactly(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication, zoom: int, handle: str) -> None:
    canvas, key = populated_canvas(project, registry)
    document = canvas.document
    try:
        canvas.set_zoom(zoom)
        qt_app.processEvents()
        grip = canvas.adornments.handles[handle]
        assert grip.isVisible()
        device_rect = grip.deviceTransform(canvas.viewportTransform()).mapRect(grip.rect())
        assert device_rect.width() == pytest.approx(7)
        press = canvas.mapFromScene(grip.scenePos())
        target = press + QPoint(round(40 * zoom / 100), round(24 * zoom / 100))
        original = document.model
        native = canvas.renderer.tree.widgets[key]
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        assert canvas._resize is not None
        move_pointer(canvas, target)
        assert document.model is original and document.history.cursor == 0
        assert native.width() == 160 and native.height() == 96
        assert canvas.adornments.badge.isVisible()
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        expected = Rect(120 if "w" in handle else 80, 104 if "n" in handle else 80,
                        120 if "w" in handle else 200 if "e" in handle else 160,
                        72 if "n" in handle else 120 if "s" in handle else 96)
        assert document.model.nodes[key].geometry == expected
        assert document.history.cursor == 1
        assert native.width() == expected.width and native.height() == expected.height
        assert canvas.renderer.items[key].transform().isIdentity()
        assert not canvas.adornments.badge.isVisible()
        document.undo()
        assert document.model.to_bytes() == original.to_bytes() and not document.dirty
        assert canvas.renderer.items[key].pos() == QPointF(80, 80)
        document.redo()
        assert document.model.nodes[key].geometry == expected
    finally:
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("border", ["standard", "fixed", "none"])
@pytest.mark.parametrize("handle", ["e", "s", "se"])
def test_window_resize_preserves_screen_position_and_child_coordinates(project: ProjectModel, registry: WidgetRegistry,
                                                                      qt_app: QApplication, border: str, handle: str) -> None:
    project = set_property(project, registry, project.root_id, "border_style", border)
    canvas, key = populated_canvas(project, registry)
    document = canvas.document
    document.select(document.model.root_id)
    try:
        qt_app.processEvents()
        assert {key for key, grip in canvas.adornments.handles.items() if grip.isVisible()} == {"e", "s", "se"}
        press = canvas.mapFromScene(canvas.adornments.handles[handle].scenePos())
        target = press + QPoint(-80, -40)
        old = document.model.nodes[document.model.root_id].geometry
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        move_pointer(canvas, target)
        assert canvas.renderer.tree.root.width() == old.width
        assert document.model.nodes[document.model.root_id].geometry == old
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        expected = Rect(old.x, old.y, 720 if "e" in handle else 800, 520 if "s" in handle else 560)
        assert document.model.nodes[document.model.root_id].geometry == expected
        assert canvas.renderer.surface.rect().width() == expected.width
        assert canvas.renderer.surface.rect().height() == expected.height
        assert canvas.renderer.items[key].pos() == QPointF(80, 80)
        document.undo()
        assert canvas.renderer.surface.rect().width() == 800
        assert canvas.renderer.surface.rect().height() == 560
    finally:
        canvas.dispose()
        canvas.close()


@pytest.mark.parametrize("cancel", ["escape", "zoom", "selection", "edit", "readonly", "hide"])
def test_resize_cancellation_restores_temporary_pixels(project: ProjectModel, registry: WidgetRegistry,
                                                      qt_app: QApplication, cancel: str) -> None:
    canvas, key = populated_canvas(project, registry)
    document = canvas.document
    try:
        qt_app.processEvents()
        press = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        move_pointer(canvas, press + QPoint(40, 24))
        assert not canvas.renderer.items[key].transform().isIdentity()
        if cancel == "escape":
            QTest.keyClick(canvas, Qt.Key.Key_Escape)
        elif cancel == "zoom":
            canvas.set_zoom(75)
        elif cancel == "selection":
            document.select(document.model.root_id)
        elif cancel == "edit":
            document.execute("外部属性变化", lambda model: set_property(model, registry, key, "text", "已修改"))
        elif cancel == "readonly":
            document.read_only = True
            document.status_changed.emit()
        else:
            canvas.hide()
        assert not canvas.gesture_active
        assert canvas.renderer.items[key].transform().isIdentity()
        assert document.model.nodes[key].geometry == Rect(80, 80, 160, 96)
        assert document.history.cursor == int(cancel == "edit")
    finally:
        canvas.dispose()
        canvas.close()


def test_returning_to_initial_size_is_noop_and_shift_bypasses_grid(project: ProjectModel, registry: WidgetRegistry,
                                                                qt_app: QApplication) -> None:
    canvas, key = populated_canvas(project, registry)
    try:
        qt_app.processEvents()
        press = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        move_pointer(canvas, press + QPoint(40, 24))
        move_pointer(canvas, press)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        assert canvas.document.history.cursor == 0
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press)
        move_pointer(canvas, press + QPoint(13, 11), shift=True)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=press + QPoint(13, 11))
        assert canvas.document.model.nodes[key].geometry == Rect(80, 80, 173, 107)
    finally:
        canvas.dispose()
        canvas.close()


def test_locked_objects_have_no_handles_and_keys_do_not_edit(project: ProjectModel, registry: WidgetRegistry,
                                                            qt_app: QApplication) -> None:
    canvas, key = populated_canvas(project, registry)
    document = canvas.document
    try:
        document.execute("锁定对象", lambda model: model.with_nodes({key: replace(model.nodes[key],
                         designer=model.nodes[key].designer.changed(locked=True))}))
        assert not any(handle.isVisible() for handle in canvas.adornments.handles.values())
        cursor = document.history.cursor
        QTest.keyClick(canvas, Qt.Key.Key_Right)
        assert document.history.cursor == cursor
    finally:
        canvas.dispose()
        canvas.close()


def test_keyboard_nudge_is_in_model_pixels_not_zoom_pixels(project: ProjectModel, registry: WidgetRegistry,
                                                         qt_app: QApplication) -> None:
    canvas, key = populated_canvas(project, registry)
    try:
        canvas.set_zoom(50)
        QTest.keyClick(canvas, Qt.Key.Key_Right)
        QTest.keyClick(canvas, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
        assert canvas.document.model.nodes[key].geometry == Rect(81, 90, 160, 96)
        canvas.document.undo()
        assert canvas.document.model.nodes[key].geometry == Rect(81, 80, 160, 96)
    finally:
        canvas.dispose()
        canvas.close()


def test_resize_crossing_opposite_edge_stops_at_one_pixel() -> None:
    original = Rect(80, 80, 160, 96)
    assert resized_rect(original, "nw", 500, 500, step=8, bounds=(800, 560)) == Rect(239, 175, 1, 1)
    assert resized_rect(original, "se", -500, -500, step=8, bounds=(800, 560)) == Rect(80, 80, 1, 1)
    assert resized_rect(original, "se", 5000, 5000, step=8, bounds=(800, 560)) == Rect(80, 80, 720, 480)
    outside = resized_rect(Rect(-100, -100, 20, 20), "nw", 500, 500, step=8, bounds=(800, 560))
    assert outside.width == 1 and outside.height == 1


def test_window_resize_cancel_restores_frame_and_surface(project: ProjectModel, registry: WidgetRegistry,
                                                       qt_app: QApplication) -> None:
    canvas, _ = populated_canvas(project, registry)
    document = canvas.document
    document.select(document.model.root_id)
    try:
        qt_app.processEvents()
        original_frame = canvas.renderer.frame.rect()
        original_surface = canvas.renderer.surface.rect()
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        move_pointer(canvas, point - QPoint(80, 40))
        assert canvas.renderer.frame.rect() != original_frame
        QTest.keyClick(canvas, Qt.Key.Key_Escape)
        assert canvas.renderer.frame.rect() == original_frame
        assert canvas.renderer.surface.rect() == original_surface
        assert document.history.cursor == 0 and not document.dirty
    finally:
        canvas.dispose()
        canvas.close()


def test_rejected_resize_restores_preview(project: ProjectModel, registry: WidgetRegistry,
                                        qt_app: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    canvas, key = populated_canvas(project, registry)
    try:
        qt_app.processEvents()
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        move_pointer(canvas, point + QPoint(40, 24))

        def reject(*args: object, **kwargs: object) -> None:
            raise DesignerError("测试拒绝提交。")

        monkeypatch.setattr(canvas.document, "execute", reject)
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(40, 24))
        assert canvas.renderer.items[key].transform().isIdentity()
        assert canvas.renderer.items[key].pos() == QPointF(80, 80)
        assert canvas.document.model.nodes[key].geometry == Rect(80, 80, 160, 96)
        assert canvas.document.history.cursor == 0
    finally:
        canvas.dispose()
        canvas.close()
