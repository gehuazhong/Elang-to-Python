"""真实桌面检查属性滚轮、下拉滚动、数值提交及编辑器外观。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.storage import atomic_write
from tests.test_property_interactions import value, wheel
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="uiplay-input-check-") as temporary:
        window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False,
                            settings=QSettings(str(Path(temporary) / "设置.ini"), QSettings.Format.IniFormat))
        try:
            window.show()
            window.activateWindow()
            QTest.qWait(100)
            prefix = f"属性交互_{round(window.devicePixelRatioF() * 100)}"
            panel, document = window.properties, window.document
            cases = 0
            for kind, prop in ((None, "geometry.width"), (None, "border_style"),
                               ("double_spin_box", "value"), ("date_edit", "value"),
                               ("time_edit", "value"), ("datetime_edit", "value"),
                               ("timer", "interval"), ("tab_widget", "current_index")):
                if kind:
                    window.page.canvas.create_component("builtin." + kind, QPointF(32, 32))
                else:
                    document.select(document.model.root_id)
                QTest.qWait(20)
                panel.tree.expandAll()
                editor = panel.editors[prop]
                editor.setFocus()
                previous = value(editor)
                snapshot, cursor = document.model, document.history.cursor
                for delta in (-120, 120, -480):
                    wheel(editor, delta)
                    assert value(editor) == previous
                assert panel.commit_pending()
                assert document.model == snapshot and document.history.cursor == cursor
                cases += 1
                if kind in {"double_spin_box", "datetime_edit"}:
                    panel.search.setText("当前")
                    QTest.qWait(20)
                    assert window.grab().save(str(directory / f"{prefix}_{kind}.png"))
                    panel.search.clear()

            document.select(document.model.root_id)
            QTest.qWait(20)
            panel.tree.expandAll()
            bar = panel.tree.verticalScrollBar()
            bar.setValue(0)
            wheel(panel.editors["geometry.width"])
            assert bar.value() > 0
            bar.setValue(0)
            assert window.grab().save(str(directory / f"{prefix}_工作台.png"))

            editor = panel.editors["font_size"]
            editor.showPopup()
            QTest.qWait(30)
            popup = application.activePopupWidget()
            assert popup is not None
            assert popup.grab().save(str(directory / f"{prefix}_字号列表.png"))
            original = document.model
            editor.view().verticalScrollBar().setValue(0)
            wheel(editor.view().viewport(), -480)
            assert editor.view().verticalScrollBar().value() > 0
            assert document.model == original
            QTest.keyClick(editor.view(), Qt.Key.Key_Escape)
            QTest.qWait(20)

            editor = panel.editors["geometry.width"]
            editor.setFocus()
            expected = editor.value() + 1
            QTest.keyClick(editor, Qt.Key.Key_Up)
            panel.queue_refresh()
            QTest.qWait(20)
            assert panel.editors["geometry.width"].value() == expected
            assert panel.commit_pending()
            assert document.model.nodes[document.model.root_id].geometry.width == expected

            report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                      "属性滚轮场景数": cases, "误改值与撤销记录": "未出现", "属性区继续滚动": "通过",
                      "已展开下拉列表正常滚动": "通过", "步进输入抵御刷新并正确提交": "通过",
                      "限制": "真实桌面配合合成 Qt 输入，尚未覆盖物理滚轮和多种触控板驱动。"}
            atomic_write(directory / f"{prefix}_桌面检查.json", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"))
            print(json.dumps(report, ensure_ascii=False))
            return 0
        except Exception:
            logging.getLogger(__name__).exception("属性交互桌面检查失败。")
            return 1
        finally:
            window.discard_all_for_test()
            window.close()


if __name__ == "__main__":
    raise SystemExit(main())
