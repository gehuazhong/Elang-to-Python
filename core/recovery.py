"""停顿和最长间隔触发持久恢复副本；恢复不覆盖原项目。"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Callable

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot

from .document import ChangeSet, DocumentSession
from .errors import DesignerError, require
from .models import ProjectModel
from .storage import FileLease, commit_project, file_token

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RecoveryWatch:
    document: DocumentSession
    path: Path
    unsubscribe: Callable[[], None]
    edited_at: float
    first_pending_at: float
    lease: FileLease
    written_state: str | None = None
    running: bool = False
    dismissed: bool = False
    archive_after_write: bool = False
    retry_after: float = 0.0


class RecoveryService(QObject):
    result_ready = Signal(str, str, str)
    notice = Signal(str)

    def __init__(self, directory: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="恢复副本")
        self._watches: dict[str, RecoveryWatch] = {}
        self._closed = False
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self.flush_due)
        self.result_ready.connect(self._finish, Qt.ConnectionType.QueuedConnection)
        self._timer.start()

    def watch(self, document: DocumentSession) -> None:
        require(not self._closed, "恢复服务已停止。")
        path = self.directory / document.model.data["document_id"] / document.session_id / "snapshot.uipro"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            lease = FileLease(path.parent / "session")
        except OSError:
            logger.exception("当前文档的恢复目录无法建立：%s", path.parent)
            self.notice.emit("当前文档的自动恢复暂不可用，请检查目录权限；仍可手动保存。")
            return
        if not lease.acquired:
            self.notice.emit("恢复会话目录正在使用，当前文档暂时不能自动恢复。")
            return

        def changed(change: ChangeSet) -> None:
            watch = self._watches.get(document.session_id)
            if watch:
                watch.edited_at = monotonic()

        now = monotonic()
        self._watches[document.session_id] = RecoveryWatch(document, path, document.subscribe(changed), now, now, lease)

    def flush_due(self, *, force: bool = False) -> None:
        if self._closed:
            return
        now = monotonic()
        for session_id, watch in tuple(self._watches.items()):
            document = watch.document
            if watch.dismissed or watch.running or document.closed or document.read_only or now < watch.retry_after:
                continue
            if not document.dirty or watch.written_state == document.state_id:
                watch.first_pending_at = now
                continue
            if not force and now - watch.edited_at < 2 and now - watch.first_pending_at < 15:
                continue
            model, state_id, source, path = document.model, document.state_id, document.resource_base, watch.path
            watch.running = True

            def worker(key: str = session_id, state: str = state_id, target: Path = path,
                       snapshot: ProjectModel = model, resource_source: Path | None = source) -> None:
                error = ""
                lease: FileLease | None = None
                try:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    lease = FileLease(target)
                    if not lease.acquired:
                        raise DesignerError("恢复副本正在被使用。")
                    commit_project(target, snapshot, expected_token=file_token(target), resource_source=resource_source)
                except Exception:
                    logger.exception("恢复副本写入失败：%s", target)
                    error = "恢复副本未能写入，请检查磁盘空间和目录权限。"
                finally:
                    if lease:
                        lease.release()
                self.result_ready.emit(key, state, error)

            self._pool.submit(worker)

    @Slot(str, str, str)
    def _finish(self, session_id: str, state_id: str, error: str) -> None:
        watch = self._watches.get(session_id)
        if watch is None:
            return
        watch.running = False
        watch.first_pending_at = monotonic()
        if not error:
            watch.written_state = state_id
        else:
            watch.retry_after = monotonic() + 15
        if watch.archive_after_write:
            self.archive(watch.path)
            watch.archive_after_write = False
            watch.written_state = None
        if watch.dismissed:
            self.archive(watch.path)
            watch.lease.release()
            self._watches.pop(session_id, None)
        elif error:
            self.notice.emit(error)

    def discover(self, *, include_active: bool = False) -> list[Path]:
        paths: list[tuple[float, Path]] = []
        try:
            for path in self.directory.glob("*/*/snapshot.uipro"):
                lease: FileLease | None = None
                try:
                    if not include_active:
                        lease = FileLease(path.parent / "session")
                        if not lease.acquired:
                            continue
                    paths.append((path.stat().st_mtime, path))
                except FileNotFoundError:
                    # 其他进程可能恰好保存或归档了扫描得到的恢复记录。
                    continue
                except OSError:
                    logger.warning("恢复记录暂时无法读取：%s", path, exc_info=True)
                finally:
                    if lease is not None:
                        lease.release()
        except OSError:
            logger.warning("恢复目录暂时无法扫描：%s", self.directory, exc_info=True)
        return [path for _, path in sorted(paths, key=lambda item: item[0], reverse=True)]

    def archive(self, path: Path) -> None:
        if not path.resolve().is_relative_to(self.directory):
            return
        try:
            if path.exists():
                path.replace(path.with_name("dismissed.uipro"))
        except OSError:
            logger.exception("恢复记录暂时无法归档：%s", path)

    def dismiss(self, document: DocumentSession) -> None:
        watch = self._watches.get(document.session_id)
        if watch:
            watch.unsubscribe()
            watch.dismissed = True
            if not watch.running:
                self.archive(watch.path)
                watch.lease.release()
                self._watches.pop(document.session_id, None)

    def mark_saved(self, document: DocumentSession) -> None:
        watch = self._watches.get(document.session_id)
        if watch is None or document.dirty:
            return
        if watch.running:
            watch.archive_after_write = True
        else:
            self.archive(watch.path)
            watch.written_state = None

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._timer.stop()
        self._pool.shutdown(wait=True)
        for watch in self._watches.values():
            watch.unsubscribe()
            if watch.dismissed or watch.archive_after_write:
                self.archive(watch.path)
            watch.lease.release()
        self._watches.clear()
