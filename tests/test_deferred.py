"""延迟回调执行与取消均应释放 Python 和原生对象。"""

from __future__ import annotations

import gc
import weakref

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal
from PySide6.QtWidgets import QApplication

from core.deferred import defer


class Receiver(QObject):
    notified = Signal()

    def __init__(self, calls: list[str]) -> None:
        super().__init__()
        self.calls = calls
        self.notified.connect(self.receive)

    def receive(self) -> None:
        self.calls.append("已执行")


@pytest.mark.parametrize("signal", [False, True])
def test_deferred_callback_runs_once_and_releases_timer(qt_app: QApplication, signal: bool) -> None:
    calls: list[str] = []
    receiver = Receiver(calls)
    defer(receiver, receiver.notified.emit if signal else receiver.receive)
    assert not calls
    qt_app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    assert calls == ["已执行"] and not receiver.children()
    receiver.deleteLater()


@pytest.mark.parametrize("signal", [False, True])
def test_cancelled_callback_does_not_keep_receiver_alive(qt_app: QApplication, signal: bool) -> None:
    calls: list[str] = []

    def discard() -> weakref.ReferenceType[Receiver]:
        receiver = Receiver(calls)
        reference = weakref.ref(receiver)
        defer(receiver, receiver.notified.emit if signal else receiver.receive)
        receiver.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qt_app.processEvents()
        return reference

    references = [discard() for _ in range(30)]
    gc.collect()
    assert not calls and all(reference() is None for reference in references)
