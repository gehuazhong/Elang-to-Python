"""仅用于测试的预览子进程，沿用正式协议并自动点击、截图及退出。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.bootstrap import initialize
from preview.worker import Worker


class ProbeWorker(Worker):
    def __init__(self, application: QApplication, path: Path | None, closing: str) -> None:
        super().__init__(application, sys.stdout.buffer)
        self.path = path
        self.closing = closing

    def send(self, kind: str, **values: Any) -> None:
        super().send(kind, **values)
        if kind == "ready":
            QTimer.singleShot(100, self.check_window)

    def check_window(self) -> None:
        try:
            root = self.runtime.tree.root
            if self.closing == "menu":
                bar = root.menuWidget()
                parent = bar.actions()[0]
                QTest.mouseClick(bar, Qt.MouseButton.LeftButton, pos=bar.actionGeometry(parent).center())
                menu = parent.menu()
                if not menu.isVisible():
                    raise RuntimeError("预览菜单未展开。")
                action = menu.actions()[0]
                QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(action).center())
                if menu.isVisible():
                    raise RuntimeError("预览菜单点击未完成。")
            else:
                button = next(widget for widget in self.runtime.tree.widgets.values() if isinstance(widget, QPushButton))
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                if not root.grab().save(str(self.path)):
                    raise RuntimeError("预览截图保存失败。")
            if self.closing == "escape":
                QTest.keyClick(root, Qt.Key.Key_Escape)
            elif self.closing in {"close", "menu"}:
                root.close()
        except Exception:
            logging.getLogger(__name__).exception("预览检查失败。")
            self.fail("预览自动交互检查失败。")


def main() -> int:
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    initialize(app, configure_logging=False)
    path = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
    closing = sys.argv[2] if len(sys.argv) > 2 else "escape"
    worker = ProbeWorker(app, path, closing)
    return worker.run()


if __name__ == "__main__":
    raise SystemExit(main())
