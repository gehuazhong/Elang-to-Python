"""复用正式预览进程，自动验证编辑框输入、密码显示、事件和退出。"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from app.bootstrap import initialize
from preview.worker import Worker


class LineEditProbe(Worker):
    def send(self, kind: str, **values: Any) -> None:
        super().send(kind, **values)
        if kind == "ready":
            QTimer.singleShot(100, self.check_input)

    def check_input(self) -> None:
        try:
            native = next(widget for widget in self.runtime.tree.widgets.values() if isinstance(widget, QLineEdit))
            native.setFocus()
            native.selectAll()
            event = QInputMethodEvent()
            event.setCommitString("中文测试")
            QApplication.sendEvent(native, event)
            assert native.text() == "中文测试", "预览中的中文输入未生效。"
            if native.echoMode() == QLineEdit.EchoMode.Password:
                assert native.displayText() != native.text(), "密码显示未生效。"
            QTest.keyClick(native, Qt.Key.Key_Return)
            path = Path(sys.argv[1])
            if not self.runtime.tree.root.grab().save(str(path)):
                raise RuntimeError("编辑框预览截图失败。")
            self.send("notice", message="编辑框自动输入检查通过。")
            QTest.keyClick(native, Qt.Key.Key_Escape)
        except Exception:
            logging.getLogger(__name__).exception("编辑框预览交互验证失败。")
            self.fail("编辑框预览交互验证失败。")


def main() -> int:
    application = QApplication([])
    application.setQuitOnLastWindowClosed(False)
    initialize(application, configure_logging=False)
    return LineEditProbe(application, sys.stdout.buffer).run()


if __name__ == "__main__":
    raise SystemExit(main())
