"""文档是唯一修改入口；准备、回放和通知具有明确边界。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4

from PySide6.QtCore import QObject, Signal

from .commands.base import CommandHistory, EditCommand
from .errors import require
from .models import ProjectModel
from .registry import WidgetRegistry
from .validation import validate_project

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChangeSet:
    ids: frozenset[str]
    revision: int
    state_id: str


@dataclass(frozen=True, slots=True)
class SaveTicket:
    session_id: str
    task_id: str
    revision: int
    state_id: str
    model: ProjectModel
    target: Path
    expected_token: str | None


class DocumentSession(QObject):
    status_changed = Signal()
    selection_changed = Signal(str)

    def __init__(self, model: ProjectModel, registry: WidgetRegistry, *, saved: bool = False,
                 budget_bytes: int = 64 * 1024 * 1024, parent: QObject | None = None) -> None:
        super().__init__(parent)
        validate_project(model)
        registry.validate(model)
        self.registry = registry
        self._model = model
        self._state_id = str(uuid4())
        self._saved_id = self._state_id if saved else None
        self.session_id = str(uuid4())
        self.revision = 0
        self.history = CommandHistory(budget_bytes)
        self.selected_id = model.root_id
        self.selected_ids: tuple[str, ...] = (model.root_id,)
        self.path: Path | None = None
        self.disk_token: str | None = None
        self.resource_base: Path | None = None
        self.read_only = False
        self.editing_suspended = False
        self.closed = False
        self._busy = False
        self._pending: SaveTicket | None = None
        self._listeners: list[Callable[[ChangeSet], None]] = []

    @property
    def model(self) -> ProjectModel:
        return self._model

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def dirty(self) -> bool:
        return self._state_id != self._saved_id

    @property
    def saving(self) -> bool:
        return self._pending is not None

    def subscribe(self, listener: Callable[[ChangeSet], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def _require_idle(self) -> None:
        require(not self.closed, "该文档已经关闭。")
        require(not self._busy, "文档准备或通知期间不能重入状态操作。")

    def _publish(self, ids: frozenset[str]) -> None:
        self._busy = True
        try:
            remaining = tuple(key for key in self.selected_ids if key in self._model.nodes)
            self.selected_ids = remaining or (self._model.root_id,)
            if self.selected_id not in self.selected_ids:
                self.selected_id = self.selected_ids[-1]
            change = ChangeSet(ids, self.revision, self._state_id)
            for listener in tuple(self._listeners):
                try:
                    listener(change)
                except Exception:
                    logger.exception("文档视图刷新失败，已提交的数据保持有效。")
            if self.selected_id not in self._model.nodes:
                self.selected_id = self._model.root_id
            self.selection_changed.emit(self.selected_id)
            self.status_changed.emit()
        finally:
            self._busy = False

    def execute(self, title: str, transform: Callable[[ProjectModel], ProjectModel],
                *, expected_revision: int | None = None) -> None:
        self._require_idle()
        require(not self.editing_suspended, "画布正在构建，请稍候再编辑。")
        require(not self.read_only, "当前文档以只读方式打开，请先另存为。")
        require(expected_revision is None or expected_revision == self.revision, "编辑依据的文档版本已经过期。")
        self._busy = True
        try:
            candidate = transform(self._model)
            validate_project(candidate)
            self.registry.validate(candidate)
            command = EditCommand.prepare(title, self._state_id, str(uuid4()), self._model, candidate)
            if command is None:
                return
            self.history.push(command)
            self._model, self._state_id = candidate, command.after_id
            self.revision += 1
        finally:
            self._busy = False
        self._publish(frozenset(item.id for item in command.nodes))

    def undo(self) -> None:
        self._require_idle()
        require(not self.editing_suspended, "画布正在构建，请稍候再撤销。")
        require(not self.read_only and self.history.can_undo, "没有可以撤销的操作。")
        command = self.history.commands[self.history.cursor - 1]
        candidate = command.apply(self._model, forward=False)
        self.history.cursor -= 1
        self._model, self._state_id = candidate, command.before_id
        self.revision += 1
        self._publish(frozenset(item.id for item in command.nodes))

    def redo(self) -> None:
        self._require_idle()
        require(not self.editing_suspended, "画布正在构建，请稍候再重做。")
        require(not self.read_only and self.history.can_redo, "没有可以重做的操作。")
        command = self.history.commands[self.history.cursor]
        candidate = command.apply(self._model, forward=True)
        self.history.cursor += 1
        self._model, self._state_id = candidate, command.after_id
        self.revision += 1
        self._publish(frozenset(item.id for item in command.nodes))

    def select(self, node_id: str) -> None:
        self.select_many((node_id,), primary=node_id)

    def select_many(self, node_ids: tuple[str, ...], *, primary: str | None = None) -> None:
        require(not self.closed, "该文档已经关闭。")
        keys = tuple(dict.fromkeys(node_ids)) or (self._model.root_id,)
        require(all(key in self._model.nodes for key in keys), "所选控件已经不存在。")
        current = primary if primary in keys else keys[-1]
        # 画布控件、非可视组件和停靠窗口分别多选；结构节点保持单选。
        slot = self._model.nodes[current].slot
        if slot not in {"children", "non_visual", "dock"}:
            keys = (current,)
        else:
            keys = tuple(key for key in keys if self._model.nodes[key].slot == slot)
        if keys != self.selected_ids or current != self.selected_id:
            self.selected_ids, self.selected_id = keys, current
            self.selection_changed.emit(current)

    def begin_save(self, target: Path, expected_token: str | None) -> SaveTicket:
        self._require_idle()
        require(self._pending is None, "该文档正在保存，请稍后再试。")
        ticket = SaveTicket(self.session_id, str(uuid4()), self.revision, self._state_id,
                            self._model, target, expected_token)
        self._pending = ticket
        self.status_changed.emit()
        return ticket

    def finish_save(self, ticket: SaveTicket, *, success: bool, token: str | None = None) -> None:
        self._require_idle()
        require(ticket is self._pending and ticket.session_id == self.session_id, "保存回执不属于当前任务。")
        if success:
            self._saved_id = ticket.state_id
            self.path, self.disk_token = ticket.target, token
            self.resource_base = ticket.target.parent
            self.read_only = False
        self._pending = None
        self.status_changed.emit()

    def close(self) -> None:
        self._require_idle()
        require(not self.saving, "文档仍在保存，完成后才能关闭。")
        self.closed = True
        self._listeners.clear()
