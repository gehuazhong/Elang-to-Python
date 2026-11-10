"""Windows 工作台设置实机检查和截图，使用临时配置。"""

from pathlib import Path
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, QEvent, QSettings, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from app.bootstrap import initialize
from app.main_window import MainWindow
from app.settings_dialog import SettingsDialog
from app.window_geometry import fit_startup_window
from app.workbench_settings import current_preferences
from core.storage import atomic_write
from widgets.builtin import create_registry


def close_window(window):
    window.discard_all_for_test()
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def check_property_rows(panel):
    for index in range(panel.tree.topLevelItemCount()):
        group = panel.tree.topLevelItem(index)
        if not group.isExpanded() or group.isHidden():
            continue
        for row in range(group.childCount()):
            item = group.child(row)
            rect = panel.tree.visualItemRect(item)
            if item.isHidden():
                continue
            for column in (0, 1):
                editor = panel.tree.itemWidget(item, column)
                if editor is not None:
                    assert editor.geometry().top() >= rect.top(), (item.text(0), rect, editor.geometry())
                    assert editor.geometry().bottom() <= rect.bottom(), (item.text(0), rect, editor.geometry())


def main():
    app = QApplication([])
    initialize(app, configure_logging=False)
    output = ROOT / "reports/workbench-settings"
    output.mkdir(parents=True, exist_ok=True)
    registry = create_registry()
    result = {"platform": app.platformName()}
    with tempfile.TemporaryDirectory(prefix="workbench_settings_") as temporary:
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        window = MainWindow(registry, settings=settings, enable_recovery=False)
        fit_startup_window(window, restored=False)
        window.resize(1500, 950)
        window.show()
        QTest.qWait(100)
        before = window.document.model.to_bytes()
        dialog = SettingsDialog(window)
        try:
            dialog.show()
            dialog.font_size.setCurrentIndex(dialog.font_size.findData(12))
            dialog.icon_size.setCurrentIndex(dialog.icon_size.findData(24))
            dialog.density.setCurrentIndex(dialog.density.findData("comfortable"))
            QTest.qWait(100)
            assert window.toolbox.search.font().pointSize() == 12
            assert window.properties.search.font().pointSize() == 12
            assert window.document.model.to_bytes() == before
            check_property_rows(window.properties)
            assert dialog.grab().save(str(output / "settings-dialog.png"))
            assert window.grab().save(str(output / "font-preview.png"))
            dialog.preset.setCurrentIndex(dialog.preset.findData("right"))
            dialog.preset.activated.emit(dialog.preset.currentIndex())
            dialog.status_bar.setChecked(False)
            QTest.qWait(100)
            assert dialog.apply_changes()
            saved = current_preferences(window)
            dialog.font_size.setCurrentIndex(dialog.font_size.findData(18))
            QTest.qWait(50)
            dialog.reject()
            assert current_preferences(window) == saved
            QTest.qWait(100)
            check_property_rows(window.properties)
            assert window.grab().save(str(output / "custom-layout.png"))
            result["live_font_preview_and_project_isolation"] = "passed"
            result["apply_then_cancel"] = "passed"
        finally:
            dialog.deleteLater()
            close_window(window)
        reopened = MainWindow(registry, settings=settings, enable_recovery=False)
        try:
            fit_startup_window(reopened, restored=reopened.geometry_restored)
            reopened.show()
            QTest.qWait(100)
            assert current_preferences(reopened) == saved
            assert reopened.font().pointSize() == 12
            assert reopened.dockWidgetArea(reopened.toolbox_dock) == Qt.DockWidgetArea.RightDockWidgetArea
            assert reopened.dockWidgetArea(reopened.property_dock) == Qt.DockWidgetArea.LeftDockWidgetArea
            assert reopened.statusBar().isHidden()
            result["restart_restores_font_and_layout"] = "passed"
            dialog = SettingsDialog(reopened)
            try:
                dialog.resize(560, 440)
                dialog.show()
                QTest.qWait(100)
                assert dialog.ok_button.isVisible() and dialog.cancel_button.isVisible()
                assert dialog.rect().contains(dialog.ok_button.mapTo(dialog, dialog.ok_button.rect().center()))
                assert dialog.grab().save(str(output / "compact-dialog.png"))
                dialog.reset_defaults()
                dialog.accept()
                assert reopened.font().pointSize() == 9
                assert reopened.statusBar().isVisible()
                result["small_dialog_and_restore_defaults"] = "passed"
            finally:
                dialog.deleteLater()
        finally:
            close_window(reopened)
    atomic_write(output / "desktop.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
