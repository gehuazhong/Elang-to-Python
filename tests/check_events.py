"""真实桌面事件复选框、保存、预览和导出验证；使用独立临时项目。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox

from app.bootstrap import initialize
from app.main_window import MainWindow
from app.window_geometry import fit_startup_window
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import set_property
from core.events import event_enabled, set_event_enabled
from core.storage import atomic_write, commit_project, load_project
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def main() -> None:
    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    window = MainWindow(registry, enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(registry)
    reports = Path(__file__).resolve().parents[1] / "reports"
    reports.mkdir(exist_ok=True)
    try:
        fit_startup_window(window, restored=False)
        window.show()
        window.activateWindow()
        QTest.qWait(100)
        prefix = f"事件勾选_{round(window.devicePixelRatioF() * 100)}"
        document, panel = window.document, window.properties
        button = window.page.canvas.create_component("builtin.button", QPointF(48, 56))
        for node, key, value in ((document.model.root_id, "window_title", "事件勾选示例"),
                                 (document.model.root_id, "geometry.width", 420),
                                 (document.model.root_id, "geometry.height", 240),
                                 (button, "text", "点击测试事件"), (button, "geometry.width", 200),
                                 (button, "checkable", True)):
            document.execute("准备事件检查", lambda model, n=node, k=key, v=value:
                             set_property(model, registry, n, k, v))
        document.select(button)
        panel.refresh()
        panel.search.setText("事件")
        QTest.qWait(50)
        editor = panel.editors["event.clicked"]
        assert isinstance(editor, QCheckBox) and not editor.isChecked()
        viewport = panel.tree.viewport()
        assert viewport.rect().contains(QRect(editor.mapTo(viewport, QPoint()), editor.size()))
        QTest.mouseClick(editor, Qt.MouseButton.LeftButton, pos=QPoint(9, editor.height() // 2))
        app.processEvents()
        assert event_enabled(document.model, button, "clicked")
        assert panel.editors["event.clicked"].text() == "已连接"
        document.undo()
        app.processEvents()
        assert not panel.editors["event.clicked"].isChecked()
        document.redo()
        app.processEvents()
        assert window.grab().save(str(reports / f"{prefix}_已连接.png"))
        messages = []
        preview.notice.connect(messages.append)
        with tempfile.TemporaryDirectory(prefix="事件桌面_") as temporary:
            directory = Path(temporary)
            path = directory / "事件.uipro"
            commit_project(path, document.model, expected_token=None)
            model = load_project(path).model
            assert event_enabled(model, button, "clicked")
            before = model.to_bytes()
            preview.show(compile_plan(model, registry, "已连接"), model)
            QTest.mouseClick(preview.tree.widgets[button], Qt.MouseButton.LeftButton)
            assert messages == ["预览事件：按钮1 · 被单击；已选中"]
            assert model.to_bytes() == before
            assert preview.tree.root.grab().save(str(reports / f"{prefix}_预览.png"))
            disabled = set_event_enabled(model, registry, button, "clicked", False)
            preview.show(compile_plan(disabled, registry, "未连接"), disabled)
            preview.tree.widgets[button].click()
            assert len(messages) == 1
            preview.dispose()
            entry = export_project(model, registry, directory / "独立程序")
            name = model.data["handlers"][0]["code_name"]
            source = (f"def {name}(window, checked):\n"
                      "    assert checked is True\n    window.setWindowTitle('事件响应正常')\n").encode("utf-8")
            business = entry.parent / "event_handlers" / (name + ".py")
            atomic_write(business, source)
            spec = importlib.util.spec_from_file_location("_事件桌面导出", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for current, expected in ((model, "事件响应正常"), (disabled, "事件勾选示例")):
                export_project(current, registry, entry.parent)
                generated = module.create_window(app)
                try:
                    generated.controls[current.nodes[button].code_name].click()
                    assert generated.windowTitle() == expected
                    assert business.read_bytes() == source
                finally:
                    generated.close()
                    generated.deleteLater()
        window.activateWindow()
        editor = panel.editors["event.clicked"]
        editor.setFocus()
        QTest.keyClick(editor, Qt.Key.Key_Space)
        app.processEvents()
        assert not event_enabled(document.model, button, "clicked")
        assert window.grab().save(str(reports / f"{prefix}_未连接.png"))
        report = {"平台": app.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "复选框完整可见": "通过", "鼠标勾选与键盘取消": "通过", "保存加载与撤销重做": "通过",
                  "预览仅响应勾选项": "通过", "事件参数与导出执行": "通过", "取消连接及业务文件保护": "通过"}
        atomic_write(reports / f"{prefix}_桌面检查.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(report, ensure_ascii=False))
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    main()
