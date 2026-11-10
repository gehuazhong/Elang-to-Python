"""历史只保留变化节点；当前快照与保存快照共享未变节点。"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any

from core.errors import require
from core.models import FrozenMap, ProjectModel, WidgetNode, thaw


@dataclass(frozen=True, slots=True)
class NodeDelta:
    id: str
    before: WidgetNode | None
    after: WidgetNode | None


@dataclass(frozen=True, slots=True)
class EditCommand:
    title: str
    before_id: str
    after_id: str
    nodes: tuple[NodeDelta, ...]
    before_data: FrozenMap | None
    after_data: FrozenMap | None
    retained_bytes: int

    @classmethod
    def prepare(cls, title: str, before_id: str, after_id: str,
                before: ProjectModel, after: ProjectModel) -> EditCommand | None:
        changed = tuple(NodeDelta(key, before.nodes.get(key), after.nodes.get(key))
                        for key in sorted(before.nodes.keys() | after.nodes.keys())
                        if before.nodes.get(key) != after.nodes.get(key))
        metadata_changed = before.data != after.data
        if not changed and not metadata_changed:
            return None
        payload: dict[str, Any] = {
            "nodes": [(item.before.to_dict() if item.before else None,
                       item.after.to_dict() if item.after else None) for item in changed],
            "data": [thaw(before.data), thaw(after.data)] if metadata_changed else None,
        }
        # 使用保留数据的 UTF-8 字节数作确定性预算，进程实际内存另行观测。
        cost = len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        return cls(title, before_id, after_id, changed, before.data if metadata_changed else None,
                   after.data if metadata_changed else None, cost)

    def apply(self, current: ProjectModel, *, forward: bool) -> ProjectModel:
        result = current.with_nodes({item.id: item.after if forward else item.before for item in self.nodes})
        metadata = self.after_data if forward else self.before_data
        return replace(result, data=metadata) if metadata is not None else result


class CommandHistory:
    def __init__(self, budget_bytes: int = 64 * 1024 * 1024) -> None:
        self.commands: list[EditCommand] = []
        self.cursor = 0
        self.budget_bytes = budget_bytes
        self.retained_bytes = 0

    def push(self, command: EditCommand) -> None:
        require(command.retained_bytes <= self.budget_bytes, "本次操作超出撤销历史预算，请缩小操作范围。")
        retained = self.commands[:self.cursor] + [command]
        total = sum(item.retained_bytes for item in retained)
        while total > self.budget_bytes:
            total -= retained.pop(0).retained_bytes
        self.commands = retained
        self.cursor = len(retained)
        self.retained_bytes = total

    @property
    def can_undo(self) -> bool:
        return self.cursor > 0

    @property
    def can_redo(self) -> bool:
        return self.cursor < len(self.commands)
