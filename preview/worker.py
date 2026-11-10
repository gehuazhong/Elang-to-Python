"""预览子进程入口；输入线程只读消息，全部 Qt 操作在主线程执行。"""

from __future__ import annotations

import logging
import os
import sys
from threading import Event, Thread
from typing import Any, BinaryIO

from PySide6.QtCore import QObject, QTimer, Qt, Signal, QCoreApplication
from PySide6.QtWidgets import QApplication

from app.bootstrap import initialize
from app.diagnostics import configure_file_logging
from core.errors import DesignerError, require
from core.models import ProjectModel
from runtime.builder import verify_registry
from runtime.preview import PreviewRuntime
from widgets.builtin import create_registry
from .protocol import MAX_REQUEST_BYTES, decode_message, encode_message, preview_plan
from .stdio import inherited_pipe

logger = logging.getLogger(__name__)


class InputBridge(QObject):
    received = Signal(bytes)
    ended = Signal()

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.stopped = Event()

    def read(self, stream: BinaryIO) -> None:
        pending = bytearray()
        try:
            while not self.stopped.is_set():
                chunk = stream.read(65536)
                if self.stopped.is_set():
                    break
                if not chunk:
                    if pending:
                        self.received.emit(bytes(pending))
                    break
                pending.extend(chunk)
                while b"\n" in pending:
                    end = pending.index(b"\n") + 1
                    self.received.emit(bytes(pending[:end]))
                    del pending[:end]
                    if end > MAX_REQUEST_BYTES or self.stopped.is_set():
                        return
                if len(pending) > MAX_REQUEST_BYTES:
                    self.received.emit(bytes(pending))
                    break
        except (OSError, ValueError):
            if not self.stopped.is_set():
                logger.exception("读取预览控制消息失败。")
        finally:
            if not self.stopped.is_set():
                self.ended.emit()


class Worker(QObject):
    def __init__(self, application: QApplication, stream: BinaryIO) -> None:
        super().__init__(application)
        self.application = application
        self.stream = stream
        self.request_id = "initializing"
        self.runtime: PreviewRuntime | None = None
        self.finished = False
        self.bridge = InputBridge(self)
        self.bridge.received.connect(self.receive, Qt.ConnectionType.QueuedConnection)
        self.bridge.ended.connect(self.stop, Qt.ConnectionType.QueuedConnection)
        self.input_timer = QTimer(self)
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(lambda: self.fail("等待预览快照超时。"))
        self.input_timer.start(15000)

    def run(self, source: BinaryIO | None = None) -> int:
        # 直接读取原始管道，避免退出时后台线程占用 Python 缓冲流的锁。
        reader = Thread(target=self.bridge.read, args=(source if source is not None else inherited_pipe("input"),), daemon=True)
        reader.start()
        try:
            return self.application.exec()
        finally:
            self.bridge.stopped.set()
            # 正常退出由父进程响应结束消息关闭管道；异常父进程也不能阻塞退出。
            reader.join(timeout=1)
            if self.runtime:
                self.runtime.dispose()

    def send(self, kind: str, **values: Any) -> None:
        try:
            self.stream.write(encode_message(kind, self.request_id, **values))
            self.stream.flush()
        except (OSError, ValueError):
            self.stop()

    def receive(self, data: bytes) -> None:
        if self.finished:
            return
        try:
            value = decode_message(data, limit=MAX_REQUEST_BYTES)
            if value["kind"] == "start":
                require(self.runtime is None, "预览进程不能重复初始化。")
                self.request_id = value["request_id"]
                self.input_timer.stop()
                registry = create_registry()
                require(value.get("registry_fingerprint") == registry.fingerprint,
                        "预览与设计器的控件注册表不一致，请重新启动设计器。")
                state_id = value.get("state_id")
                require(isinstance(state_id, str) and bool(state_id), "预览快照缺少状态标识。")
                model = ProjectModel.from_dict(value.get("model"))
                plan = preview_plan(model, registry, state_id)
                verify_registry(registry)
                self.runtime = PreviewRuntime(registry, self)
                self.runtime.notice.connect(lambda message: self.send("notice", message=message))
                self.runtime.closed.connect(self.stop)
                self.runtime.show(plan, model)
                root = self.runtime.tree.root
                self.send("ready", state_id=state_id, process_id=os.getpid(), title=root.windowTitle(),
                          size=[root.width(), root.height()], widget_count=len(self.runtime.tree.widgets))
            elif value["kind"] == "stop":
                require(value["request_id"] == self.request_id, "停止消息不属于当前预览。")
                self.stop()
            else:
                raise DesignerError("不支持该预览消息类型。")
        except Exception as exc:
            logger.exception("预览构建或消息处理失败。")
            self.fail(str(exc) if isinstance(exc, DesignerError) else "预览窗口构建失败，详细原因已写入预览日志。")

    def fail(self, message: str) -> None:
        if not self.finished:
            self.send("error", message=message)
            self.stop(code=1)

    def stop(self, *, code: int = 0) -> None:
        if self.finished:
            return
        self.finished = True
        self.bridge.stopped.set()
        self.input_timer.stop()
        if self.runtime:
            self.runtime.dispose()
        self.send("ended")
        self.application.exit(code)


def main() -> int:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    application = QApplication([sys.argv[0]])
    application.setQuitOnLastWindowClosed(False)
    worker = Worker(application, inherited_pipe("output"))
    try:
        directory = initialize(application, configure_logging=False)
        configure_file_logging(directory, "预览.log")
        return worker.run()
    except Exception:
        logger.exception("预览进程初始化失败。")
        worker.fail("预览进程初始化失败，请检查运行环境与预览日志。")
        return 1
    finally:
        if worker.runtime:
            worker.runtime.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
