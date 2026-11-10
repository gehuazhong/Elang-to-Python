"""Common file/color/font dialogs must survive callbacks and release native objects."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QColorDialog, QDialog, QFileDialog, QWidget
from shiboken6 import delete, isValid

from core.models import thaw
from runtime.easy_widgets import CommonDialog


@pytest.fixture
def common_dialog(registry, qt_app):
    owner = QWidget()
    service = CommonDialog(owner)
    service.values = thaw(registry.require("builtin.common_dialog").defaults())
    service.values.update(dialog_kind="color", use_native_dialog=False)
    yield service, owner
    if isValid(owner):
        delete(owner)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_dispose_is_silent_and_cannot_reopen_from_cancel_callback(common_dialog):
    service, owner = common_dialog
    service.open_dialog()
    dialog = service.dialog
    cancelled = QSignalSpy(service.cancelled)
    service.cancelled.connect(service.open_dialog)
    service.dispose()
    assert service.dialog is None
    assert cancelled.count() == 0
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not isValid(dialog)
    assert not owner.findChildren(QDialog)


def test_externally_destroyed_dialog_can_be_reopened(common_dialog):
    service, owner = common_dialog
    service.open_dialog()
    original = service.dialog
    delete(original)
    service.open_dialog()
    assert service.dialog is not original and isValid(service.dialog)
    assert service.dialog.isVisible()


@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.parametrize("kind", ["color", "font", "open_file", "open_files", "save_file", "directory"])
def test_stale_finished_signal_does_not_finish_reopened_dialog(common_dialog, accept, kind, tmp_path):
    service, owner = common_dialog
    source = tmp_path / "selected.txt"
    source.write_text("selection", encoding="utf-8")
    service.values.update(dialog_kind=kind, confirm_overwrite=False)
    service.open_dialog()
    first = service.dialog
    signal = service.accepted if accept else service.cancelled
    signal.connect(lambda *args: service.open_dialog())
    if isinstance(first, QColorDialog):
        first.setCurrentColor(QColor("#234567"))
    elif isinstance(first, QFileDialog):
        first.selectFile(str(tmp_path if kind == "directory" else source))
    first.accept() if accept else first.reject()
    second = service.dialog
    assert second is not None and second is not first
    first.finished.emit(QDialog.DialogCode.Rejected)
    assert service.dialog is second and second.isVisible()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not isValid(first) and isValid(second)
    assert owner.findChildren(QDialog) == [second]


def test_failure_before_open_does_not_leak_dialog(common_dialog, monkeypatch):
    service, owner = common_dialog
    service.values["dialog_kind"] = "open_file"
    cancelled = QSignalSpy(service.cancelled)

    def fail(dialog, value):
        raise RuntimeError("dialog configuration failed")

    monkeypatch.setattr(QFileDialog, "setNameFilter", fail)
    for _ in range(3):
        service.open_dialog()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert cancelled.count() == 3
    assert not owner.findChildren(QDialog)


def test_result_callback_may_destroy_finished_dialog(common_dialog, capsys):
    service, owner = common_dialog
    service.open_dialog()
    original = service.dialog
    service.accepted.connect(lambda value: delete(original))
    original.setCurrentColor(QColor("#345678"))
    original.accept()
    assert service.result == "#345678" and service.dialog is None
    assert "Traceback" not in capsys.readouterr().err


def test_failed_open_clears_previous_result(common_dialog, monkeypatch):
    service, owner = common_dialog
    service.open_dialog()
    service.dialog.setCurrentColor(QColor("#345678"))
    service.dialog.accept()
    assert service.result == "#345678"

    def fail(dialog):
        raise RuntimeError("open failed")

    monkeypatch.setattr(QColorDialog, "open", fail)
    service.open_dialog()
    assert service.result is None and service.dialog is None
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not owner.findChildren(QDialog)


def test_result_callback_can_destroy_owner(common_dialog, capsys):
    service, owner = common_dialog
    service.open_dialog()
    service.accepted.connect(lambda value: delete(owner))
    service.dialog.accept()
    assert not isValid(owner)
    assert "Traceback" not in capsys.readouterr().err
