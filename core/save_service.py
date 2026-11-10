"""后台只处理不可变数据，回执通过队列回到界面线程。"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal, Slot

from .document import DocumentSession, SaveTicket
from .errors import DesignerError, require
from .storage import FileLease, commit_project, file_token, path_key

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SaveResult:
    ticket: SaveTicket
    token: str | None
    error: str | None


class SaveService(QObject):
    result_ready = Signal(object)
    finished = Signal(object, bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="项目保存")
        self._leases: dict[str, FileLease] = {}
        self._jobs: dict[str, tuple[DocumentSession, FileLease, bool]] = {}
        self.result_ready.connect(self._finish, Qt.ConnectionType.QueuedConnection)

    def attach(self, document: DocumentSession, lease: FileLease) -> None:
        if lease.acquired:
            self._leases[document.session_id] = lease

    def save(self, document: DocumentSession, target: Path) -> None:
        target = target.expanduser().resolve()
        current = self._leases.get(document.session_id)
        reuse = current is not None and path_key(current.path) == path_key(target)
        lease = current if reuse else FileLease(target)
        require(lease.acquired, "目标文件正在被其他文档或程序使用，请选择另一个位置。")
        try:
            same_path = document.path is not None and path_key(document.path) == path_key(target)
            require(not (document.read_only and same_path), "只读项目不能覆盖保存，请另存为。")
            expected = document.disk_token if same_path else file_token(target)
            ticket = document.begin_save(target, expected)
        except Exception:
            if not reuse:
                lease.release()
            raise
        self._jobs[ticket.task_id] = (document, lease, reuse)
        source = document.resource_base

        def worker() -> None:
            try:
                token = commit_project(target, ticket.model, expected_token=expected, resource_source=source)
                result = SaveResult(ticket, token, None)
            except Exception as exc:
                logger.exception("项目保存失败：%s", target)
                message = str(exc) if isinstance(exc, DesignerError) else "项目保存失败，请检查磁盘空间与文件权限。"
                result = SaveResult(ticket, None, message)
            self.result_ready.emit(result)

        try:
            self._pool.submit(worker)
        except RuntimeError:
            self._jobs.pop(ticket.task_id)
            if not reuse:
                lease.release()
            document.finish_save(ticket, success=False)
            raise DesignerError("保存服务已停止。")

    @Slot(object)
    def _finish(self, result: SaveResult) -> None:
        job = self._jobs.pop(result.ticket.task_id, None)
        if job is None:
            logger.warning("忽略已经结束的保存任务回执。")
            return
        document, lease, reuse = job
        success = result.error is None
        if success:
            old = self._leases.get(document.session_id)
            self._leases[document.session_id] = lease
            if old is not None and old is not lease:
                old.release()
        elif not reuse:
            lease.release()
        document.finish_save(result.ticket, success=success, token=result.token)
        self.finished.emit(document, success, result.error or "项目已保存。")

    def release(self, document: DocumentSession) -> None:
        require(not document.saving, "文档正在保存，暂时不能释放写锁。")
        lease = self._leases.pop(document.session_id, None)
        if lease:
            lease.release()

    def shutdown(self) -> None:
        require(not self._jobs, "仍有未完成的保存任务。")
        self._pool.shutdown(wait=False)
        for lease in self._leases.values():
            lease.release()
        self._leases.clear()
