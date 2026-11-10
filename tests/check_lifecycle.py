"""独立进程观测重复创建与关闭后的私有内存，不替代长期泄漏验证。"""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path
from time import perf_counter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from architecture_checks.qt_probe import private_memory
from core.document import DocumentSession
from designer.canvas import DesignerCanvas
from tests.benchmark_canvas import project_fixture
from widgets.builtin import create_registry


def main(cycles: int = 40, report_name: str = "第二阶段生命周期.json") -> None:
    application = QApplication([])
    initialize(application, configure_logging=False)
    registry = create_registry()
    model = project_fixture(100)
    readings: list[int | None] = []
    destroyed_count = 0
    for cycle in range(cycles + 3):
        document = DocumentSession(model, registry)
        canvas = DesignerCanvas(document)
        canvas.show()
        deadline = perf_counter() + 5
        while not canvas.ready and perf_counter() < deadline:
            application.processEvents()
        assert canvas.ready, "生命周期验证中的画布未能构建完成。"
        destroyed = QSignalSpy(canvas.renderer.tree.root.destroyed)
        canvas.dispose()
        canvas.close()
        canvas.deleteLater()
        document.close()
        document.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        application.processEvents()
        assert destroyed.count() == 1, "原生窗口未被销毁。"
        destroyed_count += destroyed.count()
        del canvas, document, destroyed
        gc.collect()
        if cycle >= 3:
            readings.append(private_memory())
    report = {"说明": f"三轮预热后观测 {cycles} 轮，每轮一百控件；只验证此规模和本次生命周期。",
              "原生根窗口销毁次数": destroyed_count, "私有内存字节序列": readings,
              "内存读数用途": "保留完整预热后的序列，结合销毁信号判断是否趋稳，不据此宣称不存在任何泄漏。"}
    path = Path(__file__).resolve().parents[1] / "reports" / report_name
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
