"""使用真实桌面字体库和鼠标选择验证字体、字号属性。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from panels.font_editor import FontChoiceEditor, FontFamilyEditor, FontSizeEditor
from widgets.builtin import create_registry


def select_value(editor: FontChoiceEditor, value: str | int) -> None:
    index = editor.findData(value)
    if index < 0:
        raise RuntimeError("待检查的字体或字号不在选项中。")
    editor.setFocus()
    editor.showPopup()
    QApplication.processEvents()
    item = editor.model().index(index, editor.modelColumn())
    editor.view().scrollTo(item)
    QTest.mouseClick(editor.view().viewport(), Qt.MouseButton.LeftButton,
                     pos=editor.view().visualRect(item).center())
    QApplication.processEvents()


def capture(window: MainWindow, directory: Path, name: str) -> None:
    target = QApplication.activePopupWidget() or window
    if not target.grab().save(str(directory / name)):
        raise RuntimeError("字体选择桌面截图保存失败。")


def main() -> int:
    application = QApplication([])
    initialize(application)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    try:
        window.resize(1280, 820)
        window.show()
        window.activateWindow()
        QTest.qWait(100)
        canvas, document = window.page.canvas, window.document
        key = canvas.create_component("builtin.label", QPointF(48, 56))
        for name, value in (("text", "中文字体预览：我的工具"), ("geometry.width", 540), ("geometry.height", 56)):
            document.execute("准备字体检查", lambda model, p=name, v=value: set_property(model, window.registry, key, p, v))
        application.processEvents()
        window.properties.search.setText("字")
        application.processEvents()
        family = window.properties.editors["font_family"]
        size = window.properties.editors["font_size"]
        assert isinstance(family, FontFamilyEditor) and isinstance(size, FontSizeEditor)
        assert not family.isEditable() and not size.isEditable(), "字体和字号仍可手填。"
        assert QFontDatabase.families(), "真实桌面未枚举到系统字体。"
        assert family.count() == len(set(filter(None, QFontDatabase.families()))) + 1, "字体列表不完整。"
        family.showPopup()
        QTest.qWait(80)
        assert family.view().height() <= family.view().sizeHintForRow(0) * 12 + 20, "字体弹层超过十二行。"
        prefix = f"字体选择_{round(window.devicePixelRatioF() * 100)}"
        capture(window, directory, prefix + "_字体列表.png")
        QTest.keyClick(family.view(), Qt.Key.Key_Escape)
        application.processEvents()
        original, cursor = document.model, document.history.cursor
        family = window.properties.editors["font_family"]
        selected = "微软雅黑" if family.findData("微软雅黑") >= 0 else family.itemData(1)
        select_value(family, selected)
        assert document.history.cursor == cursor + 1
        size = window.properties.editors["font_size"]
        size.showPopup()
        QTest.qWait(80)
        assert size.view().height() <= size.view().sizeHintForRow(0) * 12 + 20, "字号弹层超过十二行。"
        capture(window, directory, prefix + "_字号列表.png")
        QTest.keyClick(size.view(), Qt.Key.Key_Escape)
        application.processEvents()
        select_value(window.properties.editors["font_size"], 18)
        assert document.history.cursor == cursor + 2
        font = canvas.renderer.tree.widgets[key].font()
        assert font.family() == selected and font.pointSize() == 18, "选择结果未更新画布。"
        capture(window, directory, prefix + "_应用效果.png")
        document.undo()
        document.undo()
        application.processEvents()
        assert document.model == original, "字体与字号撤销未恢复原值。"
        report = {"平台": application.platformName(), "设备像素比": window.devicePixelRatioF(),
                  "本机字体数量": len(set(QFontDatabase.families())), "实际选择字体": selected,
                  "字体与字号无需手填": "通过", "真实鼠标选择与即时更新": "通过",
                  "分别撤销恢复": "通过", "取消弹层不修改": "通过"}
        (directory / (prefix + "_桌面检查.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("字体选择桌面检查失败。")
        print("字体选择桌面检查失败，请查看日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    raise SystemExit(main())
