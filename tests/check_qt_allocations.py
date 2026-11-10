"""隔离原生回调与属性编辑器的重复创建，定位私有内存增长来源。"""

from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimer
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from app.bootstrap import initialize
from app.theme import SHELL_STYLE
from architecture_checks.qt_probe import private_memory
from core.storage import atomic_write
from panels.value_editors import ChoiceEditor


class Receiver(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def received(self) -> None:
        self.calls += 1


def exercise(application: QApplication, kind: str, batch: int) -> None:
    if kind == "timers":
        receiver = Receiver()
        for _ in range(batch):
            QTimer.singleShot(0, receiver, receiver.received)
        application.processEvents()
        assert receiver.calls == batch
        receiver.deleteLater()
    else:
        parent = QWidget()
        parent.setStyleSheet(SHELL_STYLE)
        for _ in range(batch):
            editor = ChoiceEditor(parent) if kind == "choices" else QComboBox(parent)
            editor.addItems(["第一项", "第二项", "第三项"])
            editor.view()
        parent.show()
        application.processEvents()
        parent.close()
        parent.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()


def main() -> None:
    parser = argparse.ArgumentParser(description="原生对象分配隔离检查")
    parser.add_argument("--kind", choices=("timers", "choices", "native"), required=True, help="检查对象类型")
    parser.add_argument("--cycles", type=int, default=40, help="检查轮次")
    parser.add_argument("--batch", type=int, default=100, help="每轮对象数")
    args = parser.parse_args()
    application = QApplication([])
    initialize(application, configure_logging=False)
    application.setQuitOnLastWindowClosed(False)
    readings: list[dict[str, int | None]] = []
    for cycle in range(args.cycles + 3):
        exercise(application, args.kind, args.batch)
        gc.collect()
        if cycle >= 3:
            readings.append({"轮次": cycle - 2, "私有内存": private_memory(), "窗口数": len(application.allWidgets())})
        if (cycle + 1) % 10 == 0:
            print(json.dumps(readings[-1], ensure_ascii=False), flush=True)
    report = {"类型": args.kind, "每轮对象数": args.batch, "预热轮次": 3, "采样": readings}
    destination = Path(__file__).resolve().parents[1] / "reports" / f"原生分配隔离_{args.kind}.json"
    atomic_write(destination, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
