"""核对真正的 Qt 排列、代理坐标、输入拦截及写锁行为。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QLockFile, QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter, QUndoCommand, QUndoStack
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGroupBox,
    QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QWidget,
)

from architecture_checks.gesture_probe import capture_gesture


class InputGuardView(QGraphicsView):
    """仅验证拦截入口，完整手势状态机留给第二阶段实现。"""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        event.accept()


def test_raise_does_not_change_layout_order(qt_app: QApplication) -> None:
    host = QWidget()
    layout = QHBoxLayout(host)
    first, second = QPushButton("第一个"), QPushButton("第二个")
    layout.addWidget(first)
    layout.addWidget(second)
    host.resize(400, 100)
    layout.activate()
    before = (first.geometry(), second.geometry())
    first.raise_()
    qt_app.processEvents()
    assert layout.indexOf(first) == 0 and layout.indexOf(second) == 1
    assert (first.geometry(), second.geometry()) == before
    assert host.children().index(first) > host.children().index(second)
    host.deleteLater()


@pytest.mark.parametrize("zoom", [0.5, 1.0, 1.5, 2.0])
def test_nested_proxy_coordinate_roundtrip(qt_app: QApplication, zoom: float) -> None:
    root = QMainWindow()
    root.resize(600, 400)
    central = QWidget()
    root.setCentralWidget(central)
    outer = QGroupBox("外层分组", central)
    outer.setGeometry(40, 40, 400, 260)
    inner = QGroupBox("内层分组", outer)
    inner.setGeometry(30, 40, 300, 160)
    button = QPushButton("定位目标", inner)
    button.setGeometry(24, 36, 120, 32)
    scene = QGraphicsScene()
    proxy = scene.addWidget(root)
    proxy.setPos(20, 30)
    view = QGraphicsView(scene)
    view.resize(900, 700)
    view.scale(zoom, zoom)
    view.show()
    qt_app.processEvents()
    native = button.mapTo(root, QPoint(0, 0))
    assert proxy.subWidgetRect(button).topLeft() == QPointF(native)
    expected = proxy.mapToScene(proxy.subWidgetRect(button).center())
    restored = view.mapToScene(view.mapFromScene(expected))
    assert abs(restored.x() - expected.x()) <= 1.0 / zoom
    assert abs(restored.y() - expected.y()) <= 1.0 / zoom
    destroyed = QSignalSpy(button.destroyed)
    scene.clear()
    assert destroyed.count() == 1
    view.close()
    view.deleteLater()


@pytest.mark.parametrize("guarded", [False, True])
def test_mouse_guard_blocks_real_button_signal(qt_app: QApplication, guarded: bool) -> None:
    root = QWidget()
    root.resize(300, 150)
    button = QPushButton("单击目标", root)
    button.setGeometry(40, 40, 120, 36)
    edit = QLineEdit(root)
    edit.setGeometry(40, 90, 160, 30)
    scene = QGraphicsScene()
    proxy = scene.addWidget(root)
    view = InputGuardView(scene) if guarded else QGraphicsView(scene)
    view.resize(500, 350)
    view.show()
    qt_app.processEvents()
    clicks = QSignalSpy(button.clicked)
    point = view.mapFromScene(proxy.mapToScene(proxy.subWidgetRect(button).center()))
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qt_app.processEvents()
    assert clicks.count() == (0 if guarded else 1)
    scene.clear()
    view.close()
    view.deleteLater()


def test_qt_undo_push_executes_only_once(qt_app: QApplication) -> None:
    values: list[int] = [0]

    class Command(QUndoCommand):
        def redo(self) -> None:
            values[0] += 1

        def undo(self) -> None:
            values[0] -= 1

    stack = QUndoStack()
    stack.push(Command())
    assert values == [1]
    stack.setClean()
    stack.push(Command())
    assert not stack.isClean()
    stack.undo()
    assert values == [1] and stack.isClean()


def test_second_writer_cannot_take_same_qt_lock(qt_app: QApplication, tmp_path: Path) -> None:
    path = str(tmp_path / "项目.uipro.lock")
    first, second = QLockFile(path), QLockFile(path)
    assert first.tryLock(0)
    try:
        assert not second.tryLock(0)
    finally:
        first.unlock()
    assert second.tryLock(0)
    second.unlock()


def test_snapshot_moves_visible_pixels_and_restores_original_widgets(qt_app: QApplication) -> None:
    root = QWidget()
    root.resize(300, 240)
    root.setStyleSheet("background-color: #0000ff;")
    button = QPushButton("", root)
    button.setStyleSheet("background-color: #ff0000; border: 0px;")
    button.setGeometry(30, 30, 80, 32)
    hidden = QPushButton("原本隐藏", root)
    hidden.hide()
    scene = QGraphicsScene()
    proxy = scene.addWidget(root)
    view = QGraphicsView(scene)
    view.resize(500, 400)
    view.show()
    qt_app.processEvents()
    before = button.geometry()
    original = view.mapFromScene(proxy.mapToScene(QPointF(35, 35)))
    gesture = capture_gesture(view, proxy, [button, button, hidden])
    assert len(gesture.previews) == 1
    assert gesture.background.pixelColor(original).blue() > 200
    image = QImage(gesture.background.size(), gesture.background.format())
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    gesture.paint(painter, 0, 80)
    painter.end()
    assert image.pixelColor(original).blue() > 200
    assert image.pixelColor(original + QPoint(0, 80)).red() > 200
    assert button.geometry() == before
    gesture.restore()
    gesture.restore()
    assert button.isVisible() and hidden.isHidden()
    assert view.updatesEnabled()
    scene.clear()
    view.close()
    view.deleteLater()


def test_snapshot_does_not_reflow_managed_layout(qt_app: QApplication) -> None:
    root = QWidget()
    root.resize(400, 100)
    layout = QHBoxLayout(root)
    first, second = QPushButton("第一个"), QPushButton("第二个")
    layout.addWidget(first)
    layout.addWidget(second)
    scene = QGraphicsScene()
    proxy = scene.addWidget(root)
    view = QGraphicsView(scene)
    view.show()
    qt_app.processEvents()
    before = (first.geometry(), second.geometry())
    original_policy = first.sizePolicy()
    gesture = capture_gesture(view, proxy, [first])
    layout.activate()
    assert (first.geometry(), second.geometry()) == before
    gesture.restore()
    layout.activate()
    assert (first.geometry(), second.geometry()) == before
    assert first.sizePolicy() == original_policy
    scene.clear()
    view.close()
    view.deleteLater()
