"""实机验收右键复制、按落点粘贴、删除恢复及剪贴板生命周期。"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from designer.clipboard import has_component
from widgets.builtin import create_registry


def context(window: MainWindow, position: QPointF) -> QMenu:
    canvas = window.page.canvas
    point = canvas.mapFromScene(position)
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.RightButton, pos=point)
    if window.edit_actions.menu is None:
        # 合成鼠标不保证平台生成上下文事件，补发与原生输入相同的 Qt 事件。
        event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, canvas.viewport().mapToGlobal(point))
        QApplication.sendEvent(canvas.viewport(), event)
    QTest.qWait(40)
    assert window.edit_actions.menu is not None, "右键菜单未打开。"
    return window.edit_actions.menu


def choose(menu: QMenu, key: str) -> None:
    action = next(item for item in menu.actions() if item.objectName() == key)
    assert action.isEnabled(), "右键菜单操作不可用。"
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(action).center())
    QTest.qWait(30)


def screenshot(window: MainWindow, path: Path, menu: QMenu | None = None) -> None:
    if menu is None:
        assert window.grab().save(str(path)), "窗口截图保存失败。"
    else:
        # 弹出菜单属于独立窗口，分别保存以免抓取桌面上的其他应用。
        assert menu.grab().save(str(path)), "右键菜单截图保存失败。"


def main() -> int:
    app = QApplication([])
    initialize(app)
    probe = "--exit-probe" in sys.argv
    original = app.clipboard().mimeData()
    saved = {key: bytes(original.data(key)) for key in original.formats()} if original and not probe else {}
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    try:
        window.show()
        window.activateWindow()
        QTest.qWait(60)
        canvas, document = window.page.canvas, window.document
        key = canvas.create_component("builtin.button", QPointF(64, 64))
        document.execute("检查中文标题", lambda model: set_property(model, window.registry, key, "text", "确认提交"))
        canvas.setFocus()
        QApplication.processEvents()
        if probe:
            window.edit_actions.copy()
            assert has_component(), "退出前复制失败。"
            return 0
        menu = context(window, canvas.renderer.node_rect(key).center())
        screenshot(window, directory / "右键编辑_控件菜单.png", menu)
        choose(menu, "copy")
        assert has_component(), "右键复制没有写入剪贴板。"
        cursor = document.history.cursor
        menu = context(window, QPointF(280, 160))
        screenshot(window, directory / "右键编辑_空白菜单.png", menu)
        choose(menu, "paste")
        pasted = document.selected_id
        assert pasted != key and document.history.cursor == cursor + 1
        assert document.model.nodes[pasted].properties["text"] == "确认提交"
        assert (document.model.nodes[pasted].geometry.x, document.model.nodes[pasted].geometry.y) == (280, 160)
        screenshot(window, directory / "右键编辑_粘贴后.png")
        before = document.model.to_bytes()
        choose(context(window, canvas.renderer.node_rect(key).center()), "delete")
        assert key not in document.model.nodes and pasted in document.model.nodes
        canvas.setFocus()
        QTest.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(30)
        assert document.model.to_bytes() == before, "右键删除后撤销没有恢复。"
        process = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests.check_clipboard", "--exit-probe"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=15, check=False)
        assert process.returncode == 0, f"复制后退出进程异常，退出码：{process.returncode}。"
        report = {"平台": app.platformName(), "设备像素比": window.devicePixelRatioF(), "右键选中及删除": "通过",
                  "右键复制与落点粘贴": "通过", "粘贴位置": [280, 160], "单次提交及撤销恢复": "通过",
                  "复制后进程退出码": process.returncode,
                  "限制": "使用合成输入；测试后恢复原剪贴板内容，不保存用户项目。"}
        (directory / "右键编辑_桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("右键编辑桌面检查失败。")
        print("右键编辑桌面检查失败，请查看诊断日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()
        if not probe:
            if saved:
                restored = QMimeData()
                for key, data in saved.items():
                    restored.setData(key, data)
                app.clipboard().setMimeData(restored)
            else:
                app.clipboard().clear()


if __name__ == "__main__":
    raise SystemExit(main())
