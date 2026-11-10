"""在真实桌面选择程序图标，核对属性布局、原生窗口与导出效果。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

from PySide6.QtCore import QPoint, QRect, QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QFileDialog, QListView, QTreeView, QWidget

from app.bootstrap import initialize
from app.main_window import MainWindow
from app.window_geometry import fit_startup_window
from codegen.publisher import export_project
from core.build_plan import compile_plan
from core.commands.nodes import set_property
from core.storage import atomic_write, commit_project, load_project
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry


def check_icon(window: QWidget) -> None:
    picture = window.windowIcon().pixmap(32, 32).toImage()
    assert not picture.isNull(), "运行窗口没有程序图标。"
    assert picture.pixelColor(picture.width() // 2, picture.height() // 2).name() == "#287e59", "运行窗口图标内容不一致。"


def main() -> None:
    application = QApplication([])
    initialize(application, configure_logging=False)
    registry = create_registry()
    window = MainWindow(registry, enable_recovery=False, persist_settings=False)
    preview = PreviewRuntime(registry)
    generated = None
    reports = Path(__file__).resolve().parents[1] / "reports"
    reports.mkdir(exist_ok=True)
    try:
        fit_startup_window(window, restored=False)
        window.show()
        window.activateWindow()
        QTest.qWait(100)
        prefix = f"程序图标_{round(window.devicePixelRatioF() * 100)}"
        document, panel = window.document, window.properties
        for key, value in (("window_title", "程序图标示例"), ("geometry.width", 420), ("geometry.height", 240)):
            document.execute("准备图标检查", lambda model, k=key, v=value:
                             set_property(model, registry, model.root_id, k, v))
        panel.refresh()
        panel.search.setText("程序图标")
        application.processEvents()
        with tempfile.TemporaryDirectory(prefix="程序图标桌面_") as temporary:
            directory = Path(temporary)
            source = directory / "示例 程序图标.ico"
            image = QImage(64, 64, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#287e59"))
                painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
                painter.setPen(QPen(QColor("#ffffff"), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(14, 16, 36, 32, 3, 3)
                painter.drawLine(14, 25, 50, 25)
            finally:
                painter.end()
            assert image.save(str(source), "ICO"), "无法创建桌面检查图标。"
            failures: list[Exception] = []

            def choose_file() -> None:
                dialog = application.activeModalWidget()
                try:
                    assert isinstance(dialog, QFileDialog), "没有打开图标文件选择器。"
                    assert dialog.windowTitle() == "选择程序图标"
                    assert "*.ico" in dialog.nameFilters()[0]
                    dialog.setDirectory(str(directory))
                    QTest.qWait(50)
                    view = next(control for control in (dialog.findChild(QTreeView, "treeView"),
                                                        dialog.findChild(QListView, "listView"))
                                if control is not None and control.isVisible())
                    index = view.model().index(str(source))
                    assert index.isValid(), "图标文件未出现在选择列表中。"
                    view.scrollTo(index)
                    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.visualRect(index).center())
                    assert dialog.grab().save(str(reports / f"{prefix}_选择文件.png"))
                    buttons = dialog.findChild(QDialogButtonBox)
                    accept = next(button for button in buttons.buttons()
                                  if buttons.buttonRole(button) == QDialogButtonBox.ButtonRole.AcceptRole)
                    assert accept.isEnabled(), "图标导入按钮不可用。"
                    QTest.mouseClick(accept, Qt.MouseButton.LeftButton)
                except Exception as exc:
                    failures.append(exc)
                    if isinstance(dialog, QFileDialog):
                        dialog.reject()

            cursor = document.history.cursor
            QTimer.singleShot(150, choose_file)
            QTest.mouseClick(panel.editors["window_icon"].button, Qt.MouseButton.LeftButton)
            application.processEvents()
            if failures:
                raise failures[0]
            assert document.history.cursor == cursor + 1, "选择图标没有作为单次操作提交。"
            assert not window.page.canvas.renderer.frame.icon.isNull(), "标题栏图标未更新。"
            editor = panel.editors["window_icon"]
            viewport = panel.tree.viewport()
            assert viewport.rect().contains(QRect(editor.mapTo(viewport, QPoint()), editor.size())), "图标属性行超出可见列。"
            assert editor.rect().contains(editor.button.geometry()) and editor.rect().contains(editor.clear_button.geometry()), "图标按钮被裁切。"
            assert window.grab().save(str(reports / f"{prefix}_工作台.png"))
            source.unlink()
            saved = directory / "带图标项目.uipro"
            commit_project(saved, document.model, expected_token=None)
            model = load_project(saved).model
            preview.show(compile_plan(model, registry, "桌面图标预览"), model)
            QTest.qWait(100)
            root = preview.tree.root
            check_icon(root)
            frame = root.frameGeometry()
            assert root.screen().grabWindow(0, frame.x(), frame.y(), frame.width(), frame.height()).save(
                str(reports / f"{prefix}_预览窗口.png"))
            preview.dispose()
            entry = export_project(model, registry, directory / "独立程序")
            spec = importlib.util.spec_from_file_location("_图标桌面导出", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            generated = module.create_window(application)
            generated.show()
            QTest.qWait(50)
            check_icon(generated)
            generated.close()
            generated.deleteLater()
            generated = None
            window.activateWindow()
            QTest.mouseClick(panel.editors["window_icon"].clear_button, Qt.MouseButton.LeftButton)
            application.processEvents()
            assert window.page.canvas.renderer.frame.icon.isNull(), "清除图标未生效。"
            document.undo()
            application.processEvents()
            assert not window.page.canvas.renderer.frame.icon.isNull(), "清除图标无法撤销。"
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "图标文件对话框与鼠标选择": "通过", "属性行完整可见": "通过",
                  "标题栏即时更新": "通过", "删除源文件后保存加载与预览": "通过",
                  "独立导出图标": "通过", "清除与撤销": "通过"}
        atomic_write(reports / f"{prefix}_桌面检查.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
        print(json.dumps(report, ensure_ascii=False))
    finally:
        if generated is not None:
            generated.close()
            generated.deleteLater()
        preview.dispose()
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    main()
