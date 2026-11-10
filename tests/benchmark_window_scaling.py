"""测量窗口跟随缩放的真实画布手势和绘制，独立于日常单元测试。"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from time import perf_counter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from core.commands.nodes import set_property
from core.document import DocumentSession
from core.storage import atomic_write
from tests.benchmark_canvas import MeasuredCanvas, project_fixture
from widgets.builtin import create_registry


def worker(count: int) -> dict[str, object]:
    application = QApplication([])
    initialize(application, configure_logging=False)
    registry = create_registry()
    model = project_fixture(count)
    model = set_property(model, registry, model.root_id, "scale_children", True)
    document = DocumentSession(model, registry, saved=True)
    canvas = MeasuredCanvas(document)
    errors: list[str] = []
    canvas.error.connect(errors.append)
    try:
        canvas.resize(1100, 800)
        canvas.show()
        deadline = perf_counter() + 10
        while not canvas.ready and perf_counter() < deadline:
            application.processEvents()
        assert canvas.ready, "缩放检查画布未准备好。"
        canvas.fit_to_window()
        document.select(model.root_id)
        application.processEvents()
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        samples: list[float] = []
        paints_before = canvas.paints
        for index in range(35):
            target = point + QPoint(20 + index % 15, 20 + index % 9)
            started = perf_counter()
            event = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                                Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(canvas.viewport(), event)
            application.processEvents()
            canvas.viewport().repaint()
            assert not errors, errors
            assert canvas._resize is not None and canvas._resize.preview_applied
            assert document.model == model and document.history.cursor == 0
            if index >= 5:
                samples.append((perf_counter() - started) * 1000)
        started = perf_counter()
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        application.processEvents()
        canvas.viewport().repaint()
        commit = (perf_counter() - started) * 1000
        assert document.history.cursor == 1
        document.undo()
        application.processEvents()
        assert document.model == model and not errors
        return {"控件数量": count, "平台": application.platformName(), "样本数": len(samples),
                "中位数毫秒": round(statistics.median(samples), 3),
                "第九十五百分位毫秒": round(sorted(samples)[math.ceil(len(samples) * 0.95) - 1], 3),
                "提交到稳定画面毫秒": round(commit, 3), "绘制次数": canvas.paints - paints_before,
                "手势一次提交与完整撤销": "通过", "原始耗时毫秒": [round(value, 3) for value in samples]}
    finally:
        canvas.dispose()
        canvas.close()


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), ensure_ascii=False))
        return
    results = []
    for count in (100, 500, 1000):
        process = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests.benchmark_window_scaling", "--worker", str(count)],
                                 capture_output=True, text=True, encoding="utf-8", timeout=90, check=True)
        results.append(json.loads(process.stdout))
    report = {"说明": "每种规模独立进程，五帧预热后记录三十次窗口跟随拉伸及同步绘制；不等于物理输入延迟。",
              "结果": results}
    destination = Path(__file__).resolve().parents[1] / "reports" / "窗口跟随缩放基准_0.7.4.json"
    atomic_write(destination, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
