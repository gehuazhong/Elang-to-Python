"""在 Windows 窗口中检查图标选择、颜色弹层、布局和重复打开，并保留截图。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, QSettings, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QColorDialog
from shiboken6 import isValid

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.build_plan import compile_plan
from core.commands.nodes import create_node, set_property
from core.models import new_project
from core.storage import commit_project, load_project
from panels.svg_editor import SvgDialog
from resources.svg_icons import ICONS, icon_svg
from runtime.builder import RuntimeTree
from scripts.source_fingerprint import source_fingerprint
from widgets.builtin import create_registry


def sample_project(registry):
    model = new_project("常用 SVG 图标")
    model = set_property(model, registry, model.root_id, "background_color", "#20252b")
    for index, icon in enumerate(ICONS):
        x, y = 14 + (index % 8) * 96, 10 + (index // 8) * 68
        model, key = create_node(model, registry, "builtin.svg_widget", x + 26, y)
        for name, value in (("geometry.width", 36), ("geometry.height", 36),
                            ("svg_data", icon_svg(icon.key, "#b7dcf2")), ("tool_tip", icon.label)):
            model = set_property(model, registry, key, name, value)
        model, key = create_node(model, registry, "builtin.label", x, y + 38)
        for name, value in (("geometry.width", 88), ("geometry.height", 26), ("text", icon.label),
                            ("alignment", "center"), ("foreground_color", "#d4d4d4")):
            model = set_property(model, registry, key, name, value)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", type=Path, default=Path("reports/svg-icons"))
    parser.add_argument("--write-example", action="store_true")
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    application = QApplication([])
    initialize(application, configure_logging=False)
    registry = create_registry()
    result = {"platform": application.platformName(), "icons": len(ICONS)}
    with tempfile.TemporaryDirectory() as temporary:
        window = MainWindow(registry, settings=QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat),
                            enable_recovery=False, persist_settings=False)
        dialog = None
        try:
            window.show()
            window.page.canvas.create_component("builtin.svg_widget", QPointF(40, 40))
            application.processEvents()
            spec = registry.require("builtin.svg_widget").property("svg_data")
            dialog = SvgDialog(spec, icon_svg("home", "#b7dcf2"), lambda value: True, window)
            dialog.show()
            QTest.qWait(150)
            assert dialog.icons.count() == 64
            dialog.category.setFocus()
            dialog.category.showPopup()
            application.processEvents()
            popup = dialog.category.view()
            assert popup.isVisible(), "分类列表没有展开。"
            category_index = popup.model().index(dialog.category.findData("消息"), 0)
            popup.scrollTo(category_index)
            QTest.mouseClick(popup.viewport(), Qt.MouseButton.LeftButton, pos=popup.visualRect(category_index).center())
            QTest.qWait(60)
            assert dialog.category.currentData() == "消息" and dialog.icons.count() == 8, (dialog.category.currentData(), dialog.icons.count())
            dialog.category.setCurrentIndex(0)
            QTest.keyClicks(dialog.search, "SEARCH")
            assert dialog.icons.count() == 1
            rect = dialog.icons.visualItemRect(dialog.icons.item(0))
            QTest.mouseClick(dialog.icons.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
            assert 'data-uiplay-icon="search"' in dialog.value()
            dialog.search.clear()
            dialog.stroke_width.setValue(2.4)
            errors = []

            def choose_color():
                try:
                    color = application.activeModalWidget()
                    assert isinstance(color, QColorDialog)
                    color.setCurrentColor(QColor("#58b8e8"))
                    color.accept()
                except BaseException as exc:
                    errors.append(str(exc))
                    if application.activeModalWidget():
                        application.activeModalWidget().reject()

            QTimer.singleShot(100, choose_color)
            dialog.color.button.click()
            assert not errors, errors
            assert dialog.value() == icon_svg("search", "#58b8e8", 2.4)
            QTest.qWait(100)
            for control in (dialog.search, dialog.category, dialog.icons, dialog.color, dialog.stroke_width, dialog.apply_button, *dialog.previews):
                assert control.width() > 20 and control.isVisible()
                assert dialog.rect().contains(control.mapTo(dialog, QPoint(0, 0)))
                assert dialog.rect().contains(control.mapTo(dialog, control.rect().bottomRight()))
            assert dialog.grab().save(str(args.report_dir / "icon-picker.png"))
            dialog.tabs.setCurrentIndex(1)
            QTest.qWait(60)
            assert dialog.grab().save(str(args.report_dir / "svg-source.png"))
            dialog.close()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            for _ in range(12):
                dialog = SvgDialog(spec, spec.default, lambda value: True, window)
                dialog.show()
                application.processEvents()
                assert dialog.value() == spec.default
                dialog.reject()
                dialog.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
                assert not isValid(dialog)
            result.update(mouse_search_selection=True, category_popup=True, color_dialog=True, layout=True, reopen_cycles=12,
                          device_pixel_ratio=window.devicePixelRatioF())
            target = Path("examples/常用SVG图标.uipro")
            if args.write_example:
                model = sample_project(registry)
                commit_project(target, model, expected_token=None)
            if target.is_file():
                model = load_project(target).model
                tree = RuntimeTree(registry, design_mode=False)
                try:
                    tree.apply(compile_plan(model, registry, "图标示例检查"))
                    tree.root.show()
                    QTest.qWait(100)
                    assert tree.root.grab().save(str(args.report_dir / "icon-gallery.png"))
                finally:
                    tree.dispose()
                result["example"] = str(target)
        finally:
            if dialog is not None and isValid(dialog):
                dialog.close()
                dialog.deleteLater()
            window.discard_all_for_test()
            window.close()
            window.deleteLater()
            application.processEvents()
    result["source_fingerprint"] = source_fingerprint(Path(__file__).resolve().parents[1])
    (args.report_dir / "native.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
