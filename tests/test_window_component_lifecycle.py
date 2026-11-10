"""Close auxiliary components only after the owning window accepts its close."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimer
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QMainWindow
from shiboken6 import isValid

from core.models import thaw
from runtime.advanced_dialogs import InputDialog
from runtime.advanced_widgets import start_advanced
from runtime.easy_widgets import CommonDialog


class RejectClose(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Close:
            event.ignore()
            return True
        return False


@pytest.mark.parametrize("kind", ["common_dialog", "input_dialog"])
@pytest.mark.parametrize("reject", [False, True])
def test_window_close_cleans_components_only_when_accepted(registry, qt_app, kind, reject):
    window = QMainWindow()
    guard = RejectClose(window)
    if reject:
        window.installEventFilter(guard)
    service = (CommonDialog if kind == "common_dialog" else InputDialog)(window)
    service.values = thaw(registry.require("builtin." + kind).defaults())
    service.design_mode = False
    if kind == "common_dialog":
        service.values.update(dialog_kind="color", use_native_dialog=False)
    timer = QTimer(window)
    timer.start(10000)
    controls = {"window": window, "service": service, "timer": timer}
    start_advanced(controls)
    window.show()
    service.open_dialog()
    original = service.dialog if kind == "common_dialog" else service.native
    cancelled = QSignalSpy(service.cancelled)
    service.cancelled.connect(service.open_dialog)
    try:
        assert window.close() is (not reject)
        qt_app.processEvents()
        active = service.dialog if kind == "common_dialog" else service.native
        assert cancelled.count() == 0
        if reject:
            assert active is original and original.isVisible()
            assert window.isVisible() and timer.isActive()
            window.removeEventFilter(guard)
            assert window.close()
            qt_app.processEvents()
            active = service.dialog if kind == "common_dialog" else service.native
        assert active is None
        assert not timer.isActive()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert not isValid(original)
    finally:
        service.cancelled.disconnect(service.open_dialog)
        service.dispose()
        window.removeEventFilter(guard)
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
