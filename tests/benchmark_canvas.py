"""测量已接入事件和绘制的第二阶段画布；独立运行，不混入单元测试。"""

from __future__ import annotations

import json
import math
import os
import platform
import statistics
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import PySide6
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, qVersion
from PySide6.QtGui import QMouseEvent, QPaintEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from core.document import DocumentSession
from core.models import ProjectModel, Rect, new_node, new_project
from core.storage import load_project
from designer.canvas import DesignerCanvas
from widgets.builtin import create_registry


class MeasuredCanvas(DesignerCanvas):
    paints = 0

    def paintEvent(self, event: QPaintEvent) -> None:
        self.paints += 1
        super().paintEvent(event)


def project_fixture(count: int) -> ProjectModel:
    model = new_project("画布性能验证")
    nodes = dict(model.nodes)
    width, height = 2288, math.ceil(count / 20) * 38 + 48
    nodes[model.root_id] = replace(nodes[model.root_id], geometry=Rect(100, 100, width, height))
    for index in range(count):
        kind = "builtin.button" if index % 2 == 0 else "builtin.label"
        node = new_node(kind, f"控件{index}", f"widget_{index}", model.central_id, "children", index,
                        Rect(24 + index % 20 * 112, 24 + index // 20 * 38, 100, 30), {"text": f"控件{index}"})
        nodes[node.id] = node
    return replace(model, nodes=nodes)


def worker(count: int) -> dict[str, object]:
    application = QApplication([])
    initialize(application, configure_logging=False)
    registry = create_registry()
    fixture = project_fixture(count)
    with TemporaryDirectory(prefix="uiplay-benchmark-") as directory:
        path = Path(directory) / "压力项目.uipro"
        path.write_bytes(fixture.to_bytes())
        started = perf_counter()
        model = load_project(path).model
        document = DocumentSession(model, registry, saved=True)
        canvas = MeasuredCanvas(document)
        canvas.resize(1100, 760)
        root = model.nodes[model.root_id].geometry
        zoom = max(25, min(100, int(min(980 / root.width, 640 / root.height) * 100)))
        canvas.set_zoom(zoom)
        canvas.show()
        deadline = perf_counter() + 10
        while not canvas.ready and perf_counter() < deadline:
            application.processEvents()
        assert canvas.ready, "画布构建未能完成。"
        application.processEvents()
        canvas.viewport().repaint()
        loading = (perf_counter() - started) * 1000
        key = next(node.id for node in model.nodes.values() if node.slot == "children" and node.object_order == 0)
        point = canvas.mapFromScene(canvas.renderer.node_rect(key).center())
        started = perf_counter()
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)

        def move(target: QPoint) -> None:
            event = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                                Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(canvas.viewport(), event)

        target = point + QPoint(20, 20)
        move(target)
        application.processEvents()
        canvas.viewport().repaint()
        preparation = (perf_counter() - started) * 1000
        samples: list[float] = []
        paints_before = canvas.paints
        for index in range(65):
            target = point + QPoint(20 + index % 15, 20 + index % 9)
            started = perf_counter()
            move(target)
            application.processEvents()
            canvas.viewport().repaint()
            if index >= 5:
                samples.append((perf_counter() - started) * 1000)
        assert document.history.cursor == 0, "手势中不应提交命令。"
        started = perf_counter()
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        application.processEvents()
        canvas.viewport().repaint()
        commit = (perf_counter() - started) * 1000
        assert document.history.cursor == 1, "手势结束必须恰好提交一个命令。"
        started = perf_counter()
        document.undo()
        application.processEvents()
        canvas.viewport().repaint()
        undo = (perf_counter() - started) * 1000
        assert document.model.to_bytes() == model.to_bytes(), "撤销必须恢复完整模型。"
        result = {
            "控件数量": count, "画布缩放百分比": zoom, "平台插件": application.platformName(),
            "设备像素比": canvas.viewport().devicePixelRatioF(), "加载到绘制完成毫秒": round(loading, 3),
            "构建批次数": len(canvas.build_batch_times),
            "最大构建批次毫秒": round(max(canvas.build_batch_times, default=0), 3),
            "首次手势准备毫秒": round(preparation, 3), "连续手势样本数": len(samples),
            "连续手势中位数毫秒": round(statistics.median(samples), 3),
            "连续手势第九十五百分位毫秒": round(sorted(samples)[math.ceil(len(samples) * 0.95) - 1], 3),
            "提交到稳定画面毫秒": round(commit, 3), "撤销到稳定画面毫秒": round(undo, 3),
            "实际绘制次数": canvas.paints - paints_before, "原始帧耗时毫秒": [round(value, 3) for value in samples],
        }
        canvas.dispose()
        canvas.close()
        return result


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), ensure_ascii=False))
        return
    results = []
    for count in (100, 500, 1000):
        completed = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests.benchmark_canvas", "--worker", str(count)],
                                   capture_output=True, text=True, encoding="utf-8", timeout=60, check=True)
        results.append(json.loads(completed.stdout))
    report = {
        "说明": "真实画布的合成 Qt 输入事件、模型提交和同步视口绘制；不包含操作系统显示器合成与物理鼠标延迟。",
        "Python": platform.python_version(), "PySide6": PySide6.__version__, "Qt": qVersion(),
        "系统": platform.platform(), "预热帧数": 5, "正式帧数": 60,
        "方法": "每种规模独立进程；加载只测一次；首次按下和移动单独测量；连续手势包含强制实际重绘。",
        "结果": results,
    }
    path = Path(__file__).resolve().parents[1] / "reports" / "第二阶段画布基准.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
