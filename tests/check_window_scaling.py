"""在真实桌面勾选窗口开关，验证拖动、预览拉伸和还原。"""

from __future__ import annotations

from dataclasses import replace
import json
import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import create_node, resize_node, set_property
from core.hierarchy import absolute_position, pages
from core.models import ProjectModel
from core.registry import WidgetRegistry
from core.storage import atomic_write
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def sample_project(registry: WidgetRegistry) -> ProjectModel:
    from core.models import new_project
    model = new_project("窗口组件跟随示例")
    keys = {}
    for kind, x, y in (("tab_widget", 32, 32), ("button", 32, 440), ("line_edit", 208, 440)):
        model, keys[kind] = create_node(model, registry, "builtin." + kind, x, y)
    for key, prop, value in ((keys["tab_widget"], "geometry.width", 720), (keys["tab_widget"], "geometry.height", 368),
                             (keys["button"], "text", "执行任务"), (keys["line_edit"], "text", "窗口拉伸时自动跟随")):
        model = set_property(model, registry, key, prop, value)
    first, second = pages(model, keys["tab_widget"])
    model = set_property(model, registry, first.id, "text", "任务设置")
    model = set_property(model, registry, second.id, "text", "其他页面")
    model, group = create_node(model, registry, "builtin.group_box", 24, 24, parent_id=first.id)
    model = set_property(model, registry, group, "text", "参数")
    model, label = create_node(model, registry, "builtin.label", 12, 16, parent_id=group)
    model = set_property(model, registry, label, "text", "字号保持原设置")
    model, edit = create_node(model, registry, "builtin.line_edit", 12, 64, parent_id=group)
    model, other = create_node(model, registry, "builtin.button", 32, 32, parent_id=second.id)
    model = set_property(model, registry, other, "text", "隐藏页也会跟随")
    return model


def main() -> int:
    application = QApplication([])
    initialize(application)
    registry = create_registry()
    window = MainWindow(registry, enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(registry)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    try:
        sample = sample_project(registry)
        path = directory / "窗口组件跟随示例.uipro"
        atomic_write(path, sample.to_bytes())
        window.open_path(path)
        window.resize(1480, 940)
        window.show()
        window.activateWindow()
        QTest.qWait(100)
        canvas, document = window.page.canvas, window.document
        window.select_window()
        application.processEvents()
        window.properties.search.setText("窗口")
        application.processEvents()
        checkbox = window.properties.editors["scale_children"]
        assert checkbox.isVisible() and not checkbox.isChecked(), "窗口跟随开关没有显示或默认状态错误。"
        QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton, pos=QPoint(10, checkbox.height() // 2))
        application.processEvents()
        assert document.model.nodes[document.model.root_id].properties["scale_children"], "窗口开关无法勾选。"
        atomic_write(path, document.model.to_bytes())
        prefix = f"窗口跟随_{round(window.devicePixelRatioF() * 100)}"
        assert window.grab().save(str(directory / (prefix + "_窗口属性.png")))
        original = document.model
        initial = original.nodes[original.root_id].geometry
        point = canvas.mapFromScene(canvas.adornments.handles["se"].scenePos())
        target = point + QPoint(112, 56)
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
        move = QMouseEvent(QEvent.Type.MouseMove, QPointF(target), QPointF(canvas.viewport().mapToGlobal(target)),
                           Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(canvas.viewport(), move)
        assert canvas._resize is not None and canvas._resize.preview_applied and document.model == original
        assert window.grab().save(str(directory / (prefix + "_拖动中.png")))
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert document.model.nodes[original.root_id].geometry == replace(initial, width=912, height=616)
        document.undo()
        assert document.model == original
        preview.show(compile_plan(original, registry, document.state_id), original)
        QTest.qWait(40)
        root = preview.tree.root
        for width, height in ((1120, 784), (640, 448), (800, 560)):
            root.resize(width, height)
            QTest.qWait(20)
            # 高显示缩放下系统可能限制顶层窗口尺寸，以实际内容区验收。
            expected = resize_node(original, original.root_id, replace(initial, width=root.width(), height=root.height()))
            for key, node in expected.nodes.items():
                if node.slot == "children":
                    widget = preview.tree.widgets[key]
                    assert (widget.width(), widget.height()) == (node.geometry.width, node.geometry.height), (
                        node.name, (widget.width(), widget.height()), node.geometry, (root.width(), root.height()),
                        (root.centralWidget().width(), root.centralWidget().height()))
                    assert widget.mapTo(root, QPoint()) == QPoint(*absolute_position(expected, key))
            assert root.grab().save(str(directory / (prefix + f"_预览_{width}.png")))
        assert document.model == original, "预览拉伸改写了项目。"
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "窗口属性开关可见与点击": "通过", "拖动实时跟随与一次撤销": "通过",
                  "嵌套分组框与隐藏页面": "通过", "预览放大缩小与还原": "通过", "预览不改项目": "通过"}
        (directory / (prefix + "_桌面检查.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("窗口组件跟随桌面检查失败。")
        print("窗口组件跟随检查失败，请查看日志。")
        return 1
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
