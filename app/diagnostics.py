"""滚动日志、未捕获异常摘要和不包含项目内容的本地诊断包。"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import io
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import platform
import sys
import threading
from types import TracebackType
from typing import Any
import traceback
import zipfile

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import qVersion

from core.errors import DesignerError
from core.storage import atomic_write
from .version import CHANNEL, VERSION

_errors: deque[dict[str, Any]] = deque(maxlen=20)


def configure_file_logging(directory: Path, name: str = "设计器.log") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    target = (directory / name).resolve()
    root = logging.getLogger()
    for handler in tuple(root.handlers):
        if getattr(handler, "_uiplay_file", False):
            if Path(handler.baseFilename) == target:
                return
            root.removeHandler(handler)
            handler.close()
    handler = RotatingFileHandler(target, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    handler._uiplay_file = True
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def record_exception(kind: type[BaseException], error: BaseException, trace: TracebackType | None) -> None:
    # 摘要只记录类型及代码位置，不包含异常消息、局部变量或项目文本。
    _errors.append({"时间": datetime.now(timezone.utc).isoformat(), "异常类型": kind.__name__,
                    "调用位置": [{"文件": Path(item.filename).name, "行号": item.lineno,
                                "函数": item.name} for item in traceback.extract_tb(trace)]})
    logging.getLogger(__name__).error("发生未处理的运行异常，请保存项目并查看本地日志。",
                                     exc_info=(kind, error, trace))


def install_exception_hooks() -> None:
    sys.excepthook = record_exception

    def thread_error(arguments: threading.ExceptHookArgs) -> None:
        record_exception(arguments.exc_type, arguments.exc_value, arguments.exc_traceback)

    threading.excepthook = thread_error


def export_diagnostics(target: Path, state: dict[str, Any]) -> None:
    report = {"产品": "中文界面设计器", "版本": VERSION, "通道": CHANNEL,
              "生成时间": datetime.now(timezone.utc).isoformat(), "系统": platform.system(),
              "系统版本": platform.version(), "架构": platform.machine(), "解释器版本": platform.python_version(),
              "界面绑定版本": pyside_version, "界面库版本": qVersion(),
              "便携包运行": bool(getattr(sys, "frozen", False)), "运行状态": state,
              "未处理异常摘要": list(_errors)}
    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("诊断.json", json.dumps(report, ensure_ascii=False, indent=2))
            archive.writestr("说明.txt", "此包仅包含环境、运行状态和异常位置摘要。\n不包含项目内容、业务文件、日志全文或文件路径；不会自动上传。\n")
        atomic_write(target, buffer.getvalue())
    except (OSError, ValueError, TypeError) as exc:
        raise DesignerError("诊断包导出失败，请检查目标目录和磁盘空间。") from exc
