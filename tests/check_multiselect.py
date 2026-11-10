"""在真实桌面窗口中验证框选、批量排版、右键复制和撤销恢复。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QPointF, Qt
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from widgets.builtin import create_registry


def main() -> int:
    application = QApplication([])
    initialize(application)
    previous = application.clipboard().mimeData()
    saved = {key: bytes(previous.data(key)) for key in previous.formats()} if previous else {}
    directory = Path(__file__).resolve().parents[1] / "reports"
    directory.mkdir(exist_ok=True)
    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    try:
        window.show()
        window.activateWindow()
        QTest.qWait(80)
        canvas, document = window.page.canvas, window.document
        keys = []
        for type_id, position, text in (("builtin.button", QPointF(64, 48), "执行处理"),
                                        ("builtin.label", QPointF(264, 112), "请输入要处理的内容"),
                                        ("builtin.line_edit", QPointF(504, 192), "")):
            key = canvas.create_component(type_id, position)
            keys.append(key)
            document.execute("配置桌面检查", lambda model, key=key, value=text: set_property(model, window.registry, key, "text", value))
        canvas.fit_to_window()
        QTest.qWait(30)
        before, cursor = document.model.to_bytes(), document.history.cursor
        start = canvas.mapFromScene(QPointF(24, 24))
        end = canvas.mapFromScene(QPointF(760, 256))
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
        move = QMouseEvent(QEvent.Type.MouseMove, QPointF(end), QPointF(canvas.viewport().mapToGlobal(end)),
                          Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        application.sendEvent(canvas.viewport(), move)
        assert canvas.drop_outline.isVisible()
        QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
        application.processEvents()
        assert set(document.selected_ids) == set(keys)
        assert len(window.object_tree.selectedItems()) == 3
        assert document.model.to_bytes() == before and document.history.cursor == cursor
        assert window.grab().save(str(directory / "多选_工作台.png"))
        point = canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center())
        context = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, canvas.viewport().mapToGlobal(point))
        application.sendEvent(canvas.viewport(), context)
        application.processEvents()
        menu = window.edit_actions.menu
        assert menu and menu.isVisible() and len(document.selected_ids) == 3
        assert any(action.text() == "排版" for action in menu.actions())
        assert window.grab().save(str(directory / "多选_右键菜单.png"))
        action = next(action for action in menu.actions() if action.objectName() == "copy")
        QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(action).center())
        application.processEvents()
        canvas.setFocus()
        QTest.keyClick(canvas, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        application.processEvents()
        copies = document.selected_ids
        assert len(copies) == 3 and not set(copies) & set(keys) and document.history.cursor == cursor + 1, window.output.toPlainText()
        QTest.keyClick(canvas, Qt.Key.Key_Delete)
        assert document.history.cursor == cursor + 2
        QTest.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert set(copies) <= set(document.model.nodes)
        QTest.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert document.model.to_bytes() == before
        document.select_many(tuple(keys), primary=keys[0])
        window.actions["arrange_left"].trigger()
        assert all(document.model.nodes[key].geometry.x == 64 for key in keys)
        for mode in ("same_width", "same_height", "same_size"):
            before_size, size_cursor = document.model.to_bytes(), document.history.cursor
            primary = document.model.nodes[document.selected_id].geometry
            original = {key: document.model.nodes[key].geometry for key in keys}
            menu = None
            if mode == "same_size":
                point = canvas.mapFromScene(canvas.renderer.node_rect(keys[0]).center())
                application.sendEvent(canvas.viewport(), QContextMenuEvent(
                    QContextMenuEvent.Reason.Mouse, point, canvas.viewport().mapToGlobal(point)))
                menu = window.edit_actions.menu
                submenu = next(child for child in menu.findChildren(QMenu) if child.title() == "排版")
                submenu.popup(menu.mapToGlobal(menu.actionGeometry(submenu.menuAction()).topRight()))
                QTest.qWait(50)
                assert submenu.grab().save(str(directory / "多选_等宽高菜单.png"))
                action = next(item for item in submenu.actions() if item.objectName() == "arrange_" + mode)
                QTest.mouseClick(submenu, Qt.MouseButton.LeftButton, pos=submenu.actionGeometry(action).center())
            else:
                window.actions["arrange_" + mode].trigger()
            application.processEvents()
            for key in keys:
                rect = document.model.nodes[key].geometry
                assert (rect.x, rect.y) == (original[key].x, original[key].y)
                assert rect.width == (original[key].width if mode == "same_height" else primary.width)
                assert rect.height == (original[key].height if mode == "same_width" else primary.height)
                assert canvas.renderer.tree.widgets[key].geometry().getRect() == (rect.x, rect.y, rect.width, rect.height)
            assert document.history.cursor == size_cursor + 1
            document.undo()
            assert document.model.to_bytes() == before_size
            if menu is not None and window.edit_actions.menu is menu:
                menu.close()
        window.resize(960, 620)
        canvas.fit_to_window()
        QTest.qWait(50)
        assert window.grab().save(str(directory / "多选_紧凑排版.png"))
        result = {"平台": application.platformName(), "框选与对象树同步": "通过", "选择不修改项目": "通过",
                  "右键保留多选": "通过", "整组复制粘贴与删除": "通过", "撤销恢复整个集合": "通过",
                  "菜单对齐": "通过", "等宽等高等宽高及撤销": "通过", "右键等宽高实际点击": "通过", "紧凑窗口": [960, 620],
                  "限制": "真实桌面窗口与合成输入；不覆盖物理鼠标、多屏和系统缩放切换。"}
        (directory / "多选_桌面检查.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        logging.getLogger(__name__).exception("多选桌面检查失败。")
        print("多选桌面检查失败，请查看本地诊断日志。")
        return 1
    finally:
        window.discard_all_for_test()
        window.close()
        if saved:
            restored = QMimeData()
            for key, value in saved.items():
                restored.setData(key, value)
            application.clipboard().setMimeData(restored)
        else:
            application.clipboard().clear()


if __name__ == "__main__":
    raise SystemExit(main())
