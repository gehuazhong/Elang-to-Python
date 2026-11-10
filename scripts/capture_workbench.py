"""Capture the current workbench and dialogs without changing example projects."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/vscode-workbench")
    parser.add_argument("--scale", choices=("1", "1.5", "2"), default="1")
    args = parser.parse_args()
    os.environ["QT_SCALE_FACTOR"] = args.scale

    from PySide6.QtCore import QCoreApplication, QEvent, QPointF, QSettings, Qt
    from PySide6.QtGui import QPalette
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog
    from app.bootstrap import initialize
    from app.command_palette import CommandPalette
    from app.main_window import MainWindow
    from app.window_geometry import fit_startup_window
    from panels.content_editor import ContentDialog
    from panels.menu_editor import MenuEditor
    from panels.support_dialog import SupportDialog
    from widgets.builtin import create_registry

    app = QApplication([])
    initialize(app, configure_logging=False)
    registry = create_registry()
    output = args.output.resolve() / f"scale-{args.scale}"
    output.mkdir(parents=True, exist_ok=True)
    report = {"platform": app.platformName(), "scale": args.scale, "screenshots": [], "checks": []}

    def capture(widget, name):
        app.processEvents()
        QTest.qWait(80)
        path = output / (name + ".png")
        assert widget.grab().save(str(path))
        report["screenshots"].append(path.name)

    def dialog_capture(dialog, name):
        try:
            dialog.show()
            capture(dialog, name)
        finally:
            dialog.close()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    with tempfile.TemporaryDirectory(prefix="uiplay_visual_") as temporary:
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False, persist_settings=False)
        try:
            fit_startup_window(window, restored=False)
            window.show()
            capture(window, "startup")
            assert window.screen().availableGeometry().contains(window.frameGeometry())
            report["checks"].append("Startup fits the available screen")
            available = window.screen().availableGeometry()
            large = (min(1440, available.width() - 40), min(900, available.height() - 70))
            compact = (min(960, available.width() - 40), min(620, available.height() - 70))
            window.resize(*large)
            capture(window, "workbench")
            window.resize(*compact)
            capture(window, "compact")
            assert window.width() == compact[0] and window.height() == compact[1]
            report["compact_size"] = list(compact)
            window.resize(*large)
            source = ROOT / "uidemo/01_库存管理台/库存管理台.uipro"
            before = source.read_bytes()
            document = window.open_path(source)
            key = next(node.id for node in document.model.nodes.values() if node.code_name == "search")
            document.select(key)
            window.page.canvas.fit_to_window()
            window.output.write_message("项目已打开。选择控件后，可在右侧编辑属性；F5 运行预览。")
            capture(window, "example")
            assert window.page.canvas.renderer.tree.root.styleSheet() == ""
            assert window.page.canvas.renderer.tree.root.palette().color(QPalette.ColorRole.Base).name() != "#1f1f1f"
            report["checks"].append("Designed window palette remains independent")
            baseline = document.model.to_bytes()
            for dock in (window.toolbox_dock, window.property_dock, window.object_dock, window.output_dock):
                dock.show()
                dock.raise_()
                app.processEvents()
                button = window.activity_bar.widgetForAction(dock.toggleViewAction())
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                assert not dock.isVisible()
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                assert dock.isVisible()
            assert document.model.to_bytes() == baseline
            report["checks"].append("Activity buttons toggle docks without editing the project")
            palette = CommandPalette(window.menuBar(), window)
            palette.search.setText("视图")
            assert palette.results.topLevelItemCount() >= 8
            dialog_capture(palette, "commands")
            window.properties.search.setText("字体")
            font = window.properties.editors["font_family"]
            font.showPopup()
            capture(font.view().window(), "font-list")
            font.hidePopup()
            window.properties.search.clear()
            color = QColorDialog(window)
            color.setWindowTitle("选择颜色")
            color.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
            dialog_capture(color, "color-dialog")
            files = QFileDialog(window, "打开项目", str(ROOT / "examples"), "界面项目 (*.uipro)")
            files.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            dialog_capture(files, "file-dialog")
            dialog_capture(MenuEditor(document.model, registry, window), "menu-editor")
            spec = next(prop for prop in registry.require("builtin.table_widget").properties if prop.key == "table_data")
            value = {"headers": ["名称", "状态"], "rows": [["示例项目", "已保存"]], "column_widths": [240, 120]}
            dialog_capture(ContentDialog(spec, value, lambda value: True, window), "content-editor")
            dialog_capture(SupportDialog(registry, window), "component-support")
            assert source.read_bytes() == before and document.model.to_bytes() == baseline
            report["checks"].append("Example source and document unchanged after dialog inspection")
            window.discard_all_for_test()
            capture(window, "empty-workspace")
            assert window.welcome.isVisible()
            window.new_document()
            canvas = window.page.canvas
            canvas.create_component("builtin.button", QPointF(40, 40))
            app.processEvents()
            for index in range(window.properties.tree.topLevelItemCount()):
                group = window.properties.tree.topLevelItem(index)
                for row in range(group.childCount()):
                    item = group.child(row)
                    for column in (0, 1):
                        editor = window.properties.tree.itemWidget(item, column)
                        if editor is not None:
                            assert item.sizeHint(column).height() >= editor.sizeHint().height()
            report["checks"].append("Property editor rows fit their content")
            report["passed"] = True
        finally:
            window.discard_all_for_test()
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    (output / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
