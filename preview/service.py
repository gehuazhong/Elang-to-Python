"""管理预览进程、异步输出、重启和退出，不持有可变文档。"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

from core.errors import DesignerError, require
from core.models import ProjectModel
from core.registry import WidgetRegistry
from .protocol import MAX_REPLY_BYTES, MAX_REQUEST_BYTES, decode_message, encode_message, preview_plan

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreviewRequest:
    request_id: str
    session_id: str
    state_id: str
    name: str
    payload: bytes


class PreviewService(QObject):
    changed = Signal()
    ready = Signal(object)
    notice = Signal(str)
    error = Signal(str)

    def __init__(self, registry: WidgetRegistry, parent: QObject | None = None, *,
                 startup_timeout_ms: int = 15000, stop_timeout_ms: int = 1500) -> None:
        super().__init__(parent)
        self.registry = registry
        self.process: QProcess | None = None
        self.request: PreviewRequest | None = None
        self.pending: PreviewRequest | None = None
        self.state = "idle"
        self.last_ready: dict[str, Any] | None = None
        self.last_error = ""
        self._output = bytearray()
        self._stderr = bytearray()
        self._was_ready = False
        self._reported_error = False
        self._shutting_down = False
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.setInterval(startup_timeout_ms)
        self.startup_timer.timeout.connect(self._timeout)
        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.setInterval(stop_timeout_ms)
        self.stop_timer.timeout.connect(self._kill)

    @property
    def active(self) -> bool:
        return self.process is not None

    def start(self, model: ProjectModel, state_id: str, session_id: str) -> None:
        require(not self._shutting_down, "设计器正在关闭，不能启动预览。")
        preview_plan(model, self.registry, state_id)
        identifier = str(uuid4())
        payload = encode_message("start", identifier, state_id=state_id,
                                 registry_fingerprint=self.registry.fingerprint, model=model.to_dict())
        require(len(payload) <= MAX_REQUEST_BYTES, "项目快照过大，当前预览最多接收 32 兆字节。")
        request = PreviewRequest(identifier, session_id, state_id, model.name, payload)
        if self.active:
            self.pending = request
            self._request_stop()
        else:
            self._launch(request)

    def _command(self) -> tuple[str, list[str]]:
        if getattr(sys, "frozen", False):
            return sys.executable, ["--preview-worker"]
        return sys.executable, ["-X", "utf8", "-u", "-m", "preview.worker"]

    def _launch(self, request: PreviewRequest) -> None:
        self.request = request
        self.last_ready = None
        self.last_error = ""
        self._output.clear()
        self._stderr.clear()
        self._was_ready = self._reported_error = False
        self.state = "starting"
        process = QProcess(self)
        self.process = process
        process.setWorkingDirectory(str(Path(__file__).resolve().parents[1]))
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONIOENCODING", "utf-8")
        environment.insert("PYTHONUNBUFFERED", "1")
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.started.connect(lambda: self._started(process))
        process.readyReadStandardOutput.connect(lambda: self._read_output(process))
        process.readyReadStandardError.connect(lambda: self._read_error(process))
        process.errorOccurred.connect(lambda error: self._process_error(process, error))
        process.finished.connect(lambda code, status: self._finished(process, code, status))
        self.startup_timer.start()
        program, arguments = self._command()
        process.start(program, arguments)
        self.notice.emit(f"正在启动“{request.name}”的预览，无需保存或生成代码。")
        self.changed.emit()

    def _started(self, process: QProcess) -> None:
        if process is not self.process or self.request is None:
            return
        if process.write(self.request.payload) < 0:
            self._fail("预览快照发送失败。")
        elif self.state == "stopping":
            self._send_stop()

    def _read_output(self, process: QProcess) -> None:
        if process is not self.process:
            return
        self._output.extend(bytes(process.readAllStandardOutput()))
        try:
            while b"\n" in self._output:
                end = self._output.index(b"\n")
                data = bytes(self._output[:end + 1])
                del self._output[:end + 1]
                message = decode_message(data, limit=MAX_REPLY_BYTES)
                self._message(message)
            require(len(self._output) <= MAX_REPLY_BYTES, "预览输出超过允许大小。")
        except DesignerError as exc:
            self._output.clear()
            self._fail(str(exc))

    def _message(self, message: dict[str, Any]) -> None:
        request = self.request
        if request is None:
            return
        if message["request_id"] == "initializing" and message["kind"] == "error":
            self._fail(str(message.get("message", "预览初始化失败。")))
            return
        require(message["request_id"] == request.request_id, "收到了不属于当前预览的消息。")
        kind = message["kind"]
        if kind == "ready":
            require(message.get("state_id") == request.state_id, "预览使用了不一致的文档快照。")
            require(not self._was_ready, "预览重复报告就绪状态。")
            self._was_ready = True
            self.startup_timer.stop()
            if self.state != "stopping":
                self.state = "running"
                self.last_ready = message
                self.notice.emit(f"“{request.name}”预览已打开；退出键关闭，修改设计后再次预览可更新。")
                self.changed.emit()
                self.ready.emit(message)
        elif kind == "notice":
            require(isinstance(message.get("message"), str), "预览日志格式无效。")
            self.notice.emit(message["message"])
        elif kind == "error":
            require(isinstance(message.get("message"), str), "预览错误格式无效。")
            self._fail(message["message"])
        elif kind == "ended":
            require(self._was_ready or self.state == "stopping", "预览进程在窗口就绪前请求退出。")
            # 子进程先通知结束，父进程关闭输入管道，让读取线程正常退出。
            if self.process:
                self.process.closeWriteChannel()
            self.startup_timer.stop()
            self.stop_timer.start()
        else:
            raise DesignerError("收到了未知的预览消息。")

    def _read_error(self, process: QProcess) -> None:
        if process is self.process:
            self._stderr.extend(bytes(process.readAllStandardError()))
            del self._stderr[:-MAX_REPLY_BYTES]

    def _fail(self, message: str) -> None:
        if not self._reported_error:
            self._reported_error = True
            self.last_error = message
            logger.error("预览失败：%s", message, extra={"diagnostic_only": True})
            self.error.emit("预览失败：" + message)
        self._request_stop()

    def _process_error(self, process: QProcess, error: QProcess.ProcessError) -> None:
        if process is not self.process:
            return
        logger.warning("预览进程报告：%s", process.errorString(), extra={"diagnostic_only": True})
        if error == QProcess.ProcessError.FailedToStart:
            self._fail("无法启动 Python 预览进程，请检查解释器路径与运行环境。")
            self._finished(process, -1, QProcess.ExitStatus.CrashExit)
        elif self.state != "stopping":
            self._fail("预览进程异常退出或通信中断，设计文档保持不变。")

    def _timeout(self) -> None:
        if self.process is not None:
            self._fail("预览启动超时，正在结束本次预览；可稍后重试。")

    def _request_stop(self) -> None:
        if not self.process or self.state == "stopping":
            return
        self.state = "stopping"
        self.startup_timer.stop()
        if self.process.state() == QProcess.ProcessState.Running:
            self._send_stop()
        self.stop_timer.start()
        self.changed.emit()

    def _send_stop(self) -> None:
        if self.process and self.request:
            self.process.write(encode_message("stop", self.request.request_id))
            self.process.closeWriteChannel()

    def stop(self) -> None:
        self.pending = None
        self._request_stop()

    def stop_session(self, session_id: str) -> None:
        if self.pending and self.pending.session_id == session_id:
            self.pending = None
        if self.request and self.request.session_id == session_id:
            self._request_stop()

    def _kill(self) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.notice.emit("预览未及时响应关闭，已强制结束该预览进程。")
            self.process.kill()

    def _finished(self, process: QProcess, code: int, status: QProcess.ExitStatus) -> None:
        if process is not self.process:
            return
        self._read_output(process)
        self._read_error(process)
        if self._stderr:
            logger.info("预览进程诊断输出：%s", self._stderr.decode("utf-8", errors="replace"),
                        extra={"diagnostic_only": True})
        if self.state != "stopping" and not self._reported_error:
            if code != 0 or status != QProcess.ExitStatus.NormalExit:
                self._fail("预览进程异常退出，设计文档保持不变。")
            elif not self._was_ready:
                self._fail("预览进程在窗口就绪前退出，请查看预览日志。")
        self.startup_timer.stop()
        self.stop_timer.stop()
        self.process = None
        self.request = None
        self.state = "idle"
        process.deleteLater()
        next_request, self.pending = self.pending, None
        if not self._reported_error:
            self.notice.emit("预览已关闭。")
        self.changed.emit()
        if next_request is not None and not self._shutting_down:
            self._launch(next_request)

    def shutdown(self) -> None:
        self._shutting_down = True
        self.stop()
        process = self.process
        if process:
            # 退出设计器时有限等待，失败后只结束本服务启动的预览进程。
            if not process.waitForFinished(800):
                process.kill()
                process.waitForFinished(1200)
            if process is self.process and process.state() == QProcess.ProcessState.NotRunning:
                self._finished(process, process.exitCode(), process.exitStatus())
