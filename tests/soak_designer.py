"""持续执行混合编辑和交付流程，记录资源趋势；不接触用户工程。"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import gc
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import traceback
import weakref
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Any, Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QComboBox

from app.bootstrap import initialize
from app.main_window import MainWindow
from architecture_checks.qt_probe import private_memory
from codegen.publisher import export_project
from core.commands.nodes import create_node, delete_node, move_node, resize_node, set_property
from core.commands.tree_clipboard import copy_tree, paste_tree
from core.document import DocumentSession
from core.errors import DesignerError
from core.hierarchy import pages
from core.models import ProjectModel, new_project
from core.registry import WidgetRegistry
from core.storage import atomic_write, load_project
from tests.test_property_interactions import value, wheel
from tests.test_storage import wait_for
from widgets.builtin import create_registry


class ErrorCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.ERROR)
        self.errors: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.errors.append(record.getMessage())


def sample(registry: WidgetRegistry) -> ProjectModel:
    model = new_project("持续编辑测试窗口")
    model = set_property(model, registry, model.root_id, "geometry.width", 1440)
    model = set_property(model, registry, model.root_id, "geometry.height", 1080)
    for index, spec in enumerate(item for item in registry.specs.values() if item.toolbox):
        model, key = create_node(model, registry, spec.type_id, 24 + index % 5 * 240, 24 + index // 5 * 120)
        if spec.type_id == "builtin.group_box":
            model, _ = create_node(model, registry, "builtin.line_edit", 12, 24, parent_id=key)
        if spec.type_id == "builtin.tab_widget":
            for page in pages(model, key):
                model, _ = create_node(model, registry, "builtin.button", 16, 24, parent_id=page.id)
    return model


def check_export(project: ProjectModel, registry: WidgetRegistry, directory: Path) -> None:
    entry = export_project(project, registry, directory)
    code = """
import importlib.util,sys
from PySide6.QtWidgets import QApplication
app=QApplication([])
spec=importlib.util.spec_from_file_location('export_check',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
window=module.create_window(app)
window.show()
app.processEvents()
assert len(window.controls)==int(sys.argv[2])
window.resize(1280,960)
app.processEvents()
window.close()
window.deleteLater()
app.processEvents()
"""
    process = subprocess.run([sys.executable, "-X", "utf8", "-", str(entry), str(len(project.nodes))],
                             input=code, cwd=directory, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert process.returncode == 0, process.stderr[-4000:]


def run_cycle(application: QApplication, registry: WidgetRegistry, baseline: ProjectModel,
              rng: random.Random, cycle: int, counters: Counter[str], covered: set[str]) -> tuple[weakref.ReferenceType[QObject], ...]:
    with TemporaryDirectory(prefix="uiplay-soak-") as temporary:
        directory = Path(temporary)
        window = MainWindow(registry, settings=QSettings(str(directory / "设置.ini"), QSettings.Format.IniFormat),
                            enable_recovery=False, persist_settings=False)
        window.discard_all_for_test()
        document = DocumentSession(baseline, registry, saved=True, parent=window)
        window._add_document(document)
        references = tuple(weakref.ref(item) for item in (window, window.properties, window.object_tree,
                                                         window.page.canvas, document))
        window.show()
        wait_for(lambda: window.page.canvas.ready, application)
        root_destroyed = QSignalSpy(window.page.canvas.renderer.tree.root.destroyed)
        window_destroyed = QSignalSpy(window.destroyed)
        errors: list[str] = []
        window.page.canvas.error.connect(errors.append)
        window.preview_service.error.connect(errors.append)

        def execute(transform: Callable[[ProjectModel], ProjectModel]) -> None:
            previous, cursor = document.model, document.history.cursor
            document.execute("持续编辑检查", transform)
            after = document.model
            if after != previous:
                assert document.history.cursor == cursor + 1
                document.undo()
                assert document.model == previous
                document.redo()
                assert document.model == after
                counters["命令提交与撤销重做"] += 1
            application.processEvents()
            assert not errors, errors

        try:
            for operation in range(36):
                children = [node for node in document.model.nodes.values() if node.slot == "children"]
                node = rng.choice(children)
                mode = rng.randrange(6)
                if mode == 0:
                    execute(lambda model: move_node(model, node.id, node.geometry.x + rng.randint(-8, 8),
                                                     node.geometry.y + rng.randint(-8, 8)))
                elif mode == 1:
                    execute(lambda model: set_property(model, registry, node.id, "font_size", rng.choice((0, 10, 12, 16, 24))))
                elif mode == 2:
                    root = document.model.nodes[document.model.root_id]
                    execute(lambda model: resize_node(model, model.root_id,
                                                       replace(root.geometry, width=rng.randint(1280, 1600), height=rng.randint(900, 1200))))
                elif mode == 3:
                    execute(lambda model: set_property(model, registry, model.root_id, "scale_children",
                                                       not model.nodes[model.root_id].properties.get("scale_children", False)))
                elif mode == 4:
                    fragment = copy_tree(document.model, registry, (node.id,))
                    before = document.model
                    document.execute("持续复制检查", lambda model: paste_tree(model, registry, fragment)[0])
                    document.undo()
                    assert document.model == before
                    counters["整树复制与撤销"] += 1
                else:
                    before = document.model
                    document.execute("持续删除检查", lambda model: delete_node(model, node.id))
                    document.undo()
                    assert document.model == before
                    counters["删除与撤销"] += 1
                document.select(node.id)
                application.processEvents()
                covered.add(node.type_id)
                for editor in tuple(window.properties.editors.values()):
                    if isinstance(editor, (QAbstractSpinBox, QComboBox)) and editor.isEnabled():
                        expected = value(editor)
                        wheel(editor, rng.choice((-120, 120)))
                        assert value(editor) == expected
                        counters["滚轮值保持"] += 1
                QTest.qWait(8)

            document.select(document.model.root_id)
            application.processEvents()
            for node in tuple(document.model.nodes.values()):
                if node.slot in {"non_visual", "tool_bar", "status_bar"}:
                    document.select(node.id)
                    application.processEvents()
                    covered.add(node.type_id)
                    for editor in tuple(window.properties.editors.values()):
                        if isinstance(editor, (QAbstractSpinBox, QComboBox)) and editor.isEnabled():
                            expected = value(editor)
                            wheel(editor)
                            assert value(editor) == expected
                            counters["滚轮值保持"] += 1
            document.select(document.model.root_id)
            application.processEvents()
            width = window.properties.editors["geometry.width"]
            width.setFocus()
            expected = width.value() + 1
            QTest.keyClick(width, Qt.Key.Key_Up)
            window.properties.queue_refresh()
            application.processEvents()
            assert window.properties.editors["geometry.width"].value() == expected
            assert window.properties.commit_pending()
            application.processEvents()
            assert document.model.nodes[document.model.root_id].geometry.width == expected
            counters["步进输入与刷新"] += 1

            snapshot, cursor = document.model, document.history.cursor
            try:
                document.execute("无效尺寸检查", lambda model: set_property(model, registry, model.root_id, "geometry.width", 0))
            except DesignerError:
                pass
            else:
                raise AssertionError("无效尺寸没有被拒绝。")
            assert document.model == snapshot and document.history.cursor == cursor
            counters["错误命令不改变状态"] += 1

            path = directory / "持续编辑.uipro"
            window.save_service.save(document, path)
            document.execute("保存中继续编辑", lambda model: set_property(model, registry, model.root_id,
                                                                         "window_title", f"保存期间编辑{cycle}"))
            wait_for(lambda: not document.saving, application)
            assert load_project(path).model == snapshot and document.dirty
            latest = document.model
            window.save_service.save(document, path)
            wait_for(lambda: not document.saving, application)
            assert load_project(path).model == latest and not document.dirty
            assert load_project(path.with_suffix(".uipro.bak")).model == snapshot
            counters["异步保存、继续编辑及备份"] += 1

            if cycle % 10 == 0:
                window.preview_current()
                wait_for(lambda: window.preview_service.last_ready is not None or bool(errors), application, 20)
                assert not errors and window.preview_service.last_ready["widget_count"] == len(latest.nodes)
                window.preview_service.stop()
                wait_for(lambda: not window.preview_service.active, application, 5)
                counters["独立预览启动与停止"] += 1
                check_export(latest, registry, directory / "导出")
                counters["独立导出运行"] += 1

            while document.history.can_undo:
                document.undo()
            assert document.model == baseline
            counters["完整历史还原"] += 1
            assert not errors, errors
        finally:
            window.discard_all_for_test()
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            application.processEvents()
        assert root_destroyed.count() == 1 and window_destroyed.count() == 1
        counters["原生根窗口与工作台释放"] += 1
        return references


def source_digest(base: Path) -> str:
    checksum = hashlib.sha256()
    for folder in ("app", "core", "designer", "panels", "runtime", "layout", "preview", "codegen", "widgets"):
        for path in sorted((base / folder).rglob("*.py")):
            checksum.update(str(path.relative_to(base)).encode("utf-8"))
            checksum.update(path.read_bytes())
    return checksum.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="持续混合编辑、保存、撤销、预览与导出压力检查")
    parser.add_argument("--seconds", type=int, default=600, help="至少持续的秒数")
    parser.add_argument("--seed", type=int, default=20261107, help="可复现的随机种子")
    parser.add_argument("--report", type=Path, default=Path("reports/稳定性持续检查.json"), help="报告路径")
    args = parser.parse_args()
    if args.seconds < 1:
        parser.error("持续时间必须大于零。")
    application = QApplication([])
    initialize(application, configure_logging=False)
    application.setQuitOnLastWindowClosed(False)
    capture = ErrorCapture()
    logging.getLogger().addHandler(capture)
    registry, rng = create_registry(), random.Random(args.seed)
    baseline = sample(registry)
    counters: Counter[str] = Counter()
    covered: set[str] = set()
    readings: list[dict[str, Any]] = []
    cycles = 0
    started, progress = monotonic(), monotonic()
    report: dict[str, Any] = {"开始时间": datetime.now(timezone.utc).isoformat(), "随机种子": args.seed,
                              "平台": application.platformName(), "要求持续秒数": args.seconds,
                              "源码摘要": source_digest(Path(__file__).resolve().parents[1]),
                              "基准节点数": len(baseline.nodes), "基准组件种类": sum(spec.toolbox for spec in registry.specs.values())}
    failure = ""
    try:
        while monotonic() - started < args.seconds:
            references = run_cycle(application, registry, baseline, rng, cycles, counters, covered)
            cycles += 1
            gc.collect()
            assert all(reference() is None for reference in references), "关闭后仍有面板、画布或文档包装对象被保留。"
            counters["面板画布文档包装对象释放"] += 1
            assert not capture.errors, capture.errors[-5:]
            if cycles % 5 == 0:
                readings.append({"轮次": cycles, "秒": round(monotonic() - started, 2), "私有内存字节": private_memory(),
                                 "剩余顶层窗口": len(application.topLevelWidgets())})
            if monotonic() - progress >= 30:
                print(json.dumps({"累计轮次": cycles, "持续秒数": round(monotonic() - started),
                                  "检查计数": dict(counters)}, ensure_ascii=False), flush=True)
                progress = monotonic()
    except (Exception, KeyboardInterrupt) as exc:
        failure = f"{type(exc).__name__}：{exc}"
        report["异常位置"] = traceback.format_exc()
        logging.getLogger(__name__).exception("持续检查失败。")
    finally:
        report.update({"结束时间": datetime.now(timezone.utc).isoformat(), "实际持续秒数": round(monotonic() - started, 3),
                       "完成轮次": cycles, "检查计数": dict(counters), "轮流选中的组件": sorted(covered),
                       "资源序列": readings, "异常": failure, "错误日志": capture.errors,
                       "通过": not failure and monotonic() - started >= args.seconds,
                       "限制": "离屏合成输入；记录本次时段的资源趋势，不代替物理输入、多机器兼容性与长期现场验证。"})
        atomic_write(args.report.resolve(), (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        logging.getLogger().removeHandler(capture)
    print(json.dumps({key: report[key] for key in ("通过", "完成轮次", "实际持续秒数", "异常")}, ensure_ascii=False))
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
