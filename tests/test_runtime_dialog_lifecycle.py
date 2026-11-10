"""A dialog result may immediately start another operation without losing it."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QMessageBox, QPushButton
from shiboken6 import delete, isValid

from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from runtime.builder import RuntimeTree


@pytest.fixture
def dialog_tree(project, registry, qt_app):
    trees = []

    def create(kind, **values):
        model, key = create_node(project, registry, "builtin." + kind, 0, 0)
        for prop, value in values.items():
            model = set_property(model, registry, key, prop, value)
        tree = RuntimeTree(registry, design_mode=False)
        trees.append(tree)
        tree.apply(compile_plan(model, registry, "dialog lifecycle"))
        service = tree.widgets[key]
        service.open_dialog()
        return service

    yield create
    for tree in trees:
        tree.dispose()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.mark.parametrize("accept", [True, False])
def test_result_callback_can_open_the_next_dialog(dialog_tree, qt_app, accept):
    service = dialog_tree("input_dialog")
    original = service.native
    signal = service.accepted if accept else service.cancelled
    signal.connect(lambda *args: service.open_dialog())
    original.accept() if accept else original.reject()
    assert service.native is not None and service.native is not original
    assert service.native.isVisible()


def test_progress_completion_is_emitted_once(dialog_tree):
    service = dialog_tree("progress_dialog")
    finished = QSignalSpy(service.accepted)
    service.setValue(100)
    service.setValue(100)
    service.setValue(101)
    assert finished.count() == 1


def test_cancelled_progress_ignores_late_updates(dialog_tree):
    service = dialog_tree("progress_dialog")
    finished, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    button = next(button for button in service.native.findChildren(QPushButton) if button.text() == "取消")
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert cancelled.count() == 1
    service.setValue(100)
    assert finished.count() == 0
    assert service.native is None


def test_busy_progress_does_not_report_completion(dialog_tree):
    service = dialog_tree("progress_dialog", maximum=0)
    finished = QSignalSpy(service.accepted)
    service.setValue(0)
    assert finished.count() == 0


def test_reopening_completed_progress_starts_from_initial_value(dialog_tree):
    service = dialog_tree("progress_dialog")
    service.setValue(100)
    service.open_dialog()
    assert service.native.value() == 0


@pytest.mark.parametrize("auto_close", [True, False])
@pytest.mark.parametrize("auto_reset", [True, False])
def test_progress_completion_options_and_reentrant_reopen(dialog_tree, auto_close, auto_reset):
    service = dialog_tree("progress_dialog", auto_close=auto_close, auto_reset=auto_reset, value=12)
    original = service.native
    finished, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    service.setValue(100)
    assert finished.count() == 1 and finished.at(0) == [100]
    assert service.native is (None if auto_close else original)
    assert original.isVisible() is (not auto_close)
    service.setValue(100)
    original.reject()
    assert finished.count() == 1 and cancelled.count() == 0
    service.open_dialog()
    current = service.native
    assert current is not original and current.value() == 12
    service.accepted.connect(lambda value: service.open_dialog())
    service.setValue(100)
    assert service.native is not current and service.native.value() == 12
    assert service.native.isVisible()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert isValid(service.native)


@pytest.mark.parametrize("action", ["close", "reject", "escape", "button"])
def test_progress_cancellation_opens_next_task_once(dialog_tree, action):
    service = dialog_tree("progress_dialog")
    original = service.native
    cancelled = QSignalSpy(service.cancelled)
    service.cancelled.connect(service.open_dialog)
    if action == "escape":
        QTest.keyClick(original, Qt.Key.Key_Escape)
    elif action == "button":
        original.findChild(QPushButton).click()
    else:
        getattr(original, action)()
    assert cancelled.count() == 1
    assert service.native is not original and service.native.value() == 0
    original.canceled.emit()
    original.finished.emit(0)
    assert cancelled.count() == 1
    assert service.native.isVisible()


@pytest.mark.parametrize("kind", ["input_dialog", "progress_dialog"])
def test_destroyed_native_can_be_reopened_and_disposed_silently(dialog_tree, kind):
    service = dialog_tree(kind)
    finished, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    delete(service.native)
    assert service.native is None
    service.open_dialog()
    current = service.native
    service.dispose()
    assert service.native is None and not current.isVisible()
    service.dispose()
    assert finished.count() == cancelled.count() == 0


def test_open_input_keeps_its_actual_mode_after_configuration_changes(dialog_tree):
    service = dialog_tree("input_dialog", input_mode="integer", value=23)
    finished = QSignalSpy(service.accepted)
    service.configure({**service.values, "input_mode": "text"})
    service.native.accept()
    assert finished.at(0) == [23]


@pytest.mark.parametrize("button, accepted", [
    (QMessageBox.StandardButton.Ok, True), (QMessageBox.StandardButton.Yes, True),
    (QMessageBox.StandardButton.Retry, True), (QMessageBox.StandardButton.Cancel, False),
    (QMessageBox.StandardButton.No, False), (QMessageBox.StandardButton.Close, False),
])
def test_message_buttons_report_one_result(dialog_tree, button, accepted):
    service = dialog_tree("message_box")
    finished, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    service.native.setStandardButtons(button)
    service.native.button(button).click()
    assert finished.count() == int(accepted)
    assert cancelled.count() == int(not accepted)
    if accepted:
        assert finished.at(0) == [button.value]


def test_modal_progress_ignores_completion_after_reentrant_cancellation(dialog_tree):
    service = dialog_tree("progress_dialog", modal=True)
    original = service.native
    service.setValue(1)
    finished, cancelled = QSignalSpy(service.accepted), QSignalSpy(service.cancelled)
    service.cancelled.connect(service.open_dialog)
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, original.close)
    service.setValue(100)
    assert cancelled.count() == 1 and finished.count() == 0
    assert service.native is not original and service.native.value() == 0
