"""界面显示中文摘要，完整异常另外写入诊断日志。"""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class LogBridge(QObject):
    message = Signal(str)


class PanelLogHandler(logging.Handler):
    def __init__(self, bridge: LogBridge) -> None:
        super().__init__(logging.INFO)
        self.bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        if getattr(record, "diagnostic_only", False):
            return
        level = "错误" if record.levelno >= logging.ERROR else "警告" if record.levelno >= logging.WARNING else "信息"
        try:
            self.bridge.message.emit(f"{level}：{record.getMessage()}")
        except RuntimeError:
            return


class OutputPanel(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("outputPanel")
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)
        self.setPlaceholderText("项目操作、保存结果和错误信息显示在这里。")
        self.bridge = LogBridge(self)
        self.bridge.message.connect(self.write_message, Qt.ConnectionType.QueuedConnection)
        self.handler = PanelLogHandler(self.bridge)
        logging.getLogger().addHandler(self.handler)

    def write_message(self, message: str) -> None:
        self.appendPlainText(f"{datetime.now():%H:%M:%S}  {message}")

    def dispose(self) -> None:
        logging.getLogger().removeHandler(self.handler)
        self.handler.close()
