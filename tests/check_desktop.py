"""在实际 Windows 平台插件上执行窗口、拖放事件链和保存检查。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.pop("QT_QPA_PLATFORM", None)

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.main_window import MainWindow
from core.commands.nodes import set_property
from designer.mime import component_mime
from tests.test_storage import wait_for


def main() -> None:
    application = QApplication([])
    initialize(application, configure_logging=False)
    from widgets.builtin import create_registry

    window = MainWindow(create_registry(), enable_recovery=False, persist_settings=False)
    screen = application.primaryScreen()
    area = screen.availableGeometry()
    window.resize(min(1280, area.width() - 40), min(820, area.height() - 70))
    window.show()
    application.processEvents()
    canvas = window.page.canvas
    point = canvas.mapFromScene(QPointF(56, 56))
    # 拖放事件借用 MIME 指针，变量必须存活到整条事件链结束。
    mime = component_mime("builtin.button")
    enter = QDragEnterEvent(point, Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(canvas.viewport(), enter)
    moving = QDragMoveEvent(point, Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(canvas.viewport(), moving)
    drop = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(canvas.viewport(), drop)
    assert enter.isAccepted() and moving.isAccepted() and drop.isAccepted(), "桌面拖放事件链未完成。"
    document = window.document
    button = document.selected_id
    assert document.model.nodes[button].geometry.x == 56
    document.execute("中文标题", lambda model: set_property(model, window.registry, button, "text", "确认"))
    label = canvas.create_component("builtin.label", QPointF(56, 128))
    document.execute("中文说明", lambda model: set_property(model, window.registry, label, "text", "拖动控件，编辑中文属性"))
    document.execute("说明宽度", lambda model: set_property(model, window.registry, label, "geometry.width", 280))
    document.select(button)
    application.processEvents()
    with TemporaryDirectory(prefix="uiplay-desktop-") as directory:
        window.save_service.save(document, Path(directory) / "桌面检查.uipro")
        wait_for(lambda: not document.saving, application)
        assert not document.dirty, "桌面检查保存未完成。"
        report = {
            "平台插件": application.platformName(),
            "设备像素比": window.devicePixelRatioF(),
            "逻辑分辨率": [screen.geometry().width(), screen.geometry().height()],
            "窗口尺寸": [window.width(), window.height()],
            "已通过": ["中文主窗口启动", "组件 MIME 拖放事件链", "中文属性应用", "后台保存完成"],
            "未覆盖": ["用户物理鼠标操作", "中文输入法候选窗口", "系统显示缩放切换", "跨屏拖动"],
        }
        root = Path(__file__).resolve().parents[1]
        assert window.grab().save(str(root / "reports" / "第二阶段主窗口.png")), "窗口截图保存失败。"
        (root / "reports" / "第二阶段桌面检查.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        window.discard_all_for_test()
        window.close()


if __name__ == "__main__":
    main()
