"""真实桌面编辑各列宽度，并检查画布、独立预览和导出的一致性。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

from PySide6.QtCore import QPoint, QPointF, QRect, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from app.bootstrap import initialize
from app.main_window import MainWindow
from app.window_geometry import fit_startup_window
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import set_property
from core.storage import atomic_write, commit_project, load_project
from panels.content_editor import ContentDialog
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
        QTest.qWait(80)
        prefix = f"自定义列宽_{round(window.devicePixelRatioF() * 100)}"
        document, panel = window.document, window.properties
        keys = []
        for kind in ("table_widget", "super_list"):
            key = window.page.canvas.create_component("builtin." + kind, QPointF(32, 32 + len(keys) * 200))
            keys.append(key)
            for prop, value in (("geometry.width", 590), ("geometry.height", 175),
                                ("table_data", {"headers": ["ID", "名称", "详细说明"],
                                                "rows": [["1", "订单同步", "同步订单状态与最新物流信息"],
                                                         ["2", "导出清单", "按选定时间生成报表"]]})):
                document.execute("准备列宽示例", lambda model, p=prop, v=value, k=key: set_property(model, registry, k, p, v))
            document.select(key)
            panel.refresh()
            panel.search.setText("内容")
            original, cursor = document.model, document.history.cursor
            failures = []
            def edit():
                dialog = app.activeModalWidget()
                try:
                    assert isinstance(dialog, ContentDialog)
                    QTest.qWait(30)
                    for column, width in enumerate((56, 160, 280)):
                        dialog.column_choice.setCurrentIndex(column)
                        dialog.column_width.setFocus()
                        dialog.column_width.lineEdit().selectAll()
                        QTest.keyClicks(dialog.column_width.lineEdit(), str(width))
                        QTest.keyClick(dialog.column_width, Qt.Key.Key_Tab)
                    assert dialog.column_widths == [56, 160, 280]
                    h = dialog.table.horizontalHeader()
                    start = QPoint(h.sectionViewportPosition(0) + h.sectionSize(0) - 1, h.height() // 2)
                    QTest.mousePress(h.viewport(), Qt.MouseButton.LeftButton, pos=start)
                    QTest.mouseMove(h.viewport(), start + QPoint(16, 0))
                    QTest.mouseRelease(h.viewport(), Qt.MouseButton.LeftButton, pos=start + QPoint(16, 0))
                    assert dialog.column_width.value() == 72
                    dialog.column_width.setValue(56)
                    assert dialog.screen().availableGeometry().contains(dialog.frameGeometry()), "列宽编辑窗口超出可用屏幕。"
                    for control in (dialog.column_choice, dialog.column_width, dialog.fit_column, dialog.reset_column):
                        assert dialog.rect().contains(QRect(control.mapTo(dialog, QPoint()), control.size())), "列宽控件被裁切。"
                    assert dialog.grab().save(str(reports / f"{prefix}_{kind}_编辑.png"))
                    buttons = dialog.findChild(QDialogButtonBox)
                    confirm = next(button for button in buttons.buttons() if button.text() == "确定")
                    QTest.mouseClick(confirm, Qt.MouseButton.LeftButton)
                except Exception as exc:
                    failures.append(exc)
                    if isinstance(dialog, ContentDialog):
                        dialog.reject()
            QTimer.singleShot(100, edit)
            QTest.mouseClick(panel.editors["table_data"].button, Qt.MouseButton.LeftButton)
            if failures:
                raise failures[0]
            app.processEvents()
            assert document.history.cursor == cursor + 1
            assert document.model.nodes[key].properties["table_data"]["column_widths"] == (56, 160, 280)
            assert tuple(window.page.canvas.renderer.tree.widgets[key].columnWidth(i) for i in range(3)) == (56, 160, 280)
            document.undo()
            assert document.model == original
            document.redo()
        window.page.canvas.fit_to_window()
        assert window.grab().save(str(reports / f"{prefix}_工作台.png"))
        with tempfile.TemporaryDirectory(prefix="列宽桌面_") as temporary:
            path = Path(temporary) / "列宽.uipro"
            commit_project(path, document.model, expected_token=None)
            model = load_project(path).model
            preview.show(compile_plan(model, registry, "桌面列宽"), model)
            QTest.qWait(50)
            assert preview.tree.root.grab().save(str(reports / f"{prefix}_预览.png"))
            for key in keys:
                assert tuple(preview.tree.widgets[key].columnWidth(i) for i in range(3)) == (56, 160, 280)
            preview.dispose()
            entry = export_project(model, registry, Path(temporary) / "导出")
            spec = importlib.util.spec_from_file_location("_桌面列宽导出", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            generated = module.create_window(app)
            try:
                generated.show()
                app.processEvents()
                for key in keys:
                    widget = generated.controls[model.nodes[key].code_name]
                    assert tuple(widget.columnWidth(i) for i in range(3)) == (56, 160, 280)
            finally:
                generated.close()
                generated.deleteLater()
        report = {"平台": app.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "表格与超级列表框逐列输入": "通过", "拖动列标题调宽": "通过", "编辑窗口与输入控件可见": "通过",
                  "单次提交与撤销": "通过", "保存加载及画布预览导出一致": "通过", "各列逻辑像素宽度": [56, 160, 280]}
        atomic_write(reports / f"{prefix}_桌面检查.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(report, ensure_ascii=False))
    finally:
        preview.dispose()
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    main()
