"""比较代理场景和控件直接绘制的离屏开销，结果不代替桌面交互验收。"""

from __future__ import annotations

import json
import logging
import math
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import PySide6
from PySide6.QtCore import QPoint, Qt, qVersion
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QGraphicsScene, QGraphicsView,
    QGroupBox, QLabel, QLineEdit, QListWidget, QMainWindow,
    QProgressBar, QPushButton, QSlider, QTreeWidget, QTreeWidgetItem, QWidget,
)

from .gesture_probe import GestureCapture, capture_gesture

logger = logging.getLogger(__name__)


def private_memory() -> int | None:
    """通过系统进程计数读取私有内存，包含 Qt 的原生分配。"""
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Process -Id {os.getpid()}).PrivateMemorySize64"],
            capture_output=True, text=True, check=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return int(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        logger.exception("系统内存指标读取失败，此项记为未测。")
        return None


def make_surface(count: int) -> tuple[QMainWindow, list[QWidget]]:
    root = QMainWindow()
    root.setWindowTitle("画布基准")
    central = QWidget()
    root.setCentralWidget(central)
    columns = 12
    root.resize(1020, math.ceil(count / columns) * 40 + 20)
    controls: list[QWidget] = []
    for index in range(count):
        kind = index % 10
        text = f"组件{index}"
        control: QWidget
        if kind == 0:
            control = QPushButton(text, central)
        elif kind == 1:
            control = QLabel(text, central)
        elif kind == 2:
            control = QLineEdit(text, central)
        elif kind == 3:
            control = QCheckBox(text, central)
        elif kind == 4:
            combo = QComboBox(central)
            combo.addItems(["第一项", "第二项", "第三项"])
            control = combo
        elif kind == 5:
            progress = QProgressBar(central)
            progress.setValue(50)
            control = progress
        elif kind == 6:
            control = QSlider(Qt.Orientation.Horizontal, central)
        elif kind == 7:
            control = QGroupBox(text, central)
        elif kind == 8:
            listing = QListWidget(central)
            listing.addItems(["第一项", "第二项"])
            control = listing
        else:
            tree = QTreeWidget(central)
            tree.setHeaderHidden(True)
            tree.addTopLevelItem(QTreeWidgetItem(["根节点"]))
            control = tree
        control.setObjectName(f"control_{index}")
        control.setGeometry(10 + index % columns * 84, 10 + index // columns * 40, 80, 32)
        controls.append(control)
    return root, controls


def worker(count: int, backend: str) -> dict[str, Any]:
    app = QApplication(["画布基准", "-platform", "offscreen"])
    baseline = private_memory()
    started = perf_counter()
    root, controls = make_surface(count)
    scene: QGraphicsScene | None = None
    view: QGraphicsView | None = None
    width, height = 1100, 760
    proxy = None
    if backend in {"proxy", "snapshot"}:
        scene = QGraphicsScene()
        proxy = scene.addWidget(root)
        view = QGraphicsView(scene)
        view.resize(width, height)
        view.show()
        app.processEvents()
        view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        scale = view.transform().m11()
        paint_width, paint_height = view.viewport().width(), view.viewport().height()
    else:
        root.show()
        app.processEvents()
        paint_width, paint_height = width, height
        scale = min(width / root.width(), height / root.height())
    creation_ms = (perf_counter() - started) * 1000
    image = QImage(paint_width, paint_height, QImage.Format.Format_ARGB32_Premultiplied)
    gesture: GestureCapture | None = None
    preparation_ms: float | None = None
    if backend == "snapshot" and view is not None and proxy is not None:
        started = perf_counter()
        gesture = capture_gesture(view, proxy, controls[:20])
        preparation_ms = (perf_counter() - started) * 1000
    occupied = private_memory()
    elapsed: list[float] = []
    for frame in range(65):
        control = controls[frame % len(controls)]
        started = perf_counter()
        if gesture is None:
            control.move(control.x() + (1 if frame % 2 else -1), control.y())
        app.processEvents()
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        try:
            if gesture is not None:
                gesture.paint(painter, frame % 16, frame % 8)
            elif view is not None:
                view.render(painter)
            else:
                painter.scale(scale, scale)
                root.render(painter, QPoint(0, 0))
        finally:
            painter.end()
        if frame >= 5:
            elapsed.append((perf_counter() - started) * 1000)
    measurements = sorted(elapsed)
    result = {
        "绘制路径": {"proxy": "代理场景", "direct": "控件直接绘制", "snapshot": "手势快照合成"}[backend],
        "控件数量": count,
        "创建耗时毫秒": round(creation_ms, 3),
        "重绘样本数": len(elapsed),
        "同步更新及重绘中位数毫秒": round(statistics.median(elapsed), 3),
        "同步更新及重绘百分之九十五分位毫秒": round(measurements[math.ceil(len(measurements) * 0.95) - 1], 3),
        "手势快照准备毫秒": round(preparation_ms, 3) if preparation_ms is not None else None,
        "手势快照数量": len(gesture.previews) if gesture is not None else 0,
        "适应窗口缩放比例": round(scale, 4),
        "进程私有内存增加字节": occupied - baseline if occupied is not None and baseline is not None else None,
        "画面尺寸": [paint_width, paint_height],
    }
    if gesture is not None:
        gesture.restore()
    if scene is not None:
        scene.clear()
    else:
        root.close()
        root.deleteLater()
    if view is not None:
        view.close()
        view.deleteLater()
    app.processEvents()
    return result


def main() -> int:
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "--worker":
            count, backend = int(sys.argv[2]), sys.argv[3]
            if count not in {100, 500, 1000} or backend not in {"proxy", "direct", "snapshot"}:
                raise ValueError("基准参数不受支持。")
            print(json.dumps(worker(count, backend), ensure_ascii=False))
            return 0
        if len(sys.argv) != 1:
            print("用法：直接运行画布基准模块，无需参数。")
            return 2
        measurements: list[dict[str, Any]] = []
        root = Path(__file__).resolve().parents[1]
        for count in (100, 500, 1000):
            for backend in ("proxy", "direct", "snapshot"):
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", "-m", "architecture_checks.qt_probe",
                     "--worker", str(count), backend],
                    cwd=root, capture_output=True, text=True, encoding="utf-8",
                    check=True, timeout=90,
                )
                measurements.append(json.loads(result.stdout))
        report = {
            "说明": "离屏混合控件的同步更新与重绘实验；不是桌面拖动帧率或产品性能承诺。",
            "Python": platform.python_version(), "PySide6": PySide6.__version__, "Qt": qVersion(),
            "系统": platform.platform(), "处理器": platform.processor(), "逻辑处理器数量": os.cpu_count(),
            "平台插件": "offscreen", "预热次数": 5, "正式次数": 60,
            "测试方式": "每组使用独立进程；全窗口适应视口；真实路径每次移动一个控件；快照路径合成二十个临时控件画面；分别统计准备与连续重绘。",
            "未覆盖": ["真实显示器合成", "高分辨率显示切换", "长时间输入", "完整手势状态机", "应用增量渲染策略"],
            "结果": measurements,
        }
        target = root / "reports" / "画布基准.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        logger.exception("画布基准执行失败。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
