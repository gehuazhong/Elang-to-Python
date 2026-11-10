"""用可运行参考模型核对顺序、迁移和文档提交语义。"""

from __future__ import annotations

import json
import keyword
import logging
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Literal
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)
Project = dict[str, Any]
OrderKind = Literal["object", "stack", "layout"]


class ContractError(ValueError):
    """数据或操作不符合已确定的架构契约。"""


def require(condition: bool, message: str) -> None:
    """使验证在解释器优化模式下仍然有效。"""
    if not condition:
        raise ContractError(message)


def canonical_bytes(project: Project) -> bytes:
    """产生稳定快照，并拒绝运行时对象及非有限数值。"""
    try:
        return json.dumps(
            project, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("项目含有不能保存为标准 JSON 的数据。") from exc


def _unique(items: list[Project], title: str) -> dict[str, Project]:
    result: dict[str, Project] = {}
    for item in items:
        require(isinstance(item, dict), f"{title}必须是对象。")
        identifier = item.get("id")
        require(isinstance(identifier, str), f"{title}缺少标识符。")
        try:
            UUID(identifier)
        except ValueError as exc:
            raise ContractError(f"{title}的标识符格式无效。") from exc
        require(identifier not in result, f"{title}的标识符重复。")
        result[identifier] = item
    return result


def _index(value: Any, title: str) -> int:
    require(type(value) is int and value >= 0, f"{title}必须是非负整数。")
    return value


def _dense(values: list[int], title: str) -> None:
    require(sorted(values) == list(range(len(values))), f"{title}必须唯一且连续。")


def validate_project(project: Project) -> None:
    """核对通用图结构；完整控件属性校验由后续注册层提供。"""
    require(isinstance(project, dict), "项目顶层必须是对象。")
    canonical_bytes(project)
    require(project.get("format") == "uipro", "项目格式标识不受支持。")
    require(type(project.get("schema_version")) is int
            and project["schema_version"] == 2, "只接受第二版项目契约。")
    require(isinstance(project.get("nodes"), list), "项目缺少节点数组。")
    nodes = _unique(project["nodes"], "节点")
    require(bool(nodes), "项目至少需要根窗口和工作区。")
    root_id = project.get("root_id")
    require(root_id in nodes, "项目的根节点不存在。")
    root = nodes[root_id]
    require(root.get("type_id") == "builtin.main_window"
            and root.get("parent_id") is None and root.get("slot") == "root",
            "根节点必须是主窗口。")
    require(sum(node.get("parent_id") is None for node in nodes.values()) == 1,
            "项目只能有一个根节点。")
    central = [node for node in nodes.values() if node.get("slot") == "central"]
    require(len(central) == 1 and central[0].get("parent_id") == root_id
            and central[0].get("type_id") == "builtin.central_widget",
            "根窗口必须有且只有一个工作区。")
    object_groups: dict[tuple[str | None, str], list[int]] = defaultdict(list)
    stack_groups: dict[str, list[int]] = defaultdict(list)
    layout_groups: dict[str, list[int]] = defaultdict(list)
    grid_groups: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    names: set[str] = set()
    code_names: set[str] = set()
    for node in nodes.values():
        require("order" not in node, "第二版不能保留混用的顺序字段。")
        name, code_name = node.get("name"), node.get("code_name")
        require(isinstance(name, str) and bool(name.strip()) and name not in names,
                "对象名称不能为空或重复。")
        require(isinstance(code_name, str) and code_name.isascii()
                and code_name.isidentifier() and not keyword.iskeyword(code_name)
                and code_name not in code_names, "代码名称必须合法且唯一。")
        names.add(name)
        code_names.add(code_name)
        parent_id, slot = node.get("parent_id"), node.get("slot")
        require(isinstance(slot, str), "节点缺少挂接位置。")
        require(parent_id is None or parent_id in nodes, "节点引用了不存在的父级。")
        seen: set[str] = set()
        ancestor: Project | None = node
        while ancestor is not None:
            require(ancestor["id"] not in seen, "父子关系不能形成循环。")
            seen.add(ancestor["id"])
            next_id = ancestor.get("parent_id")
            require(next_id is None or next_id in nodes, "祖先节点不存在。")
            ancestor = nodes.get(next_id)
        object_groups[(parent_id, slot)].append(_index(node.get("object_order"), "对象顺序"))
        rect = node.get("geometry")
        if rect is not None:
            require(isinstance(rect, dict) and set(rect) == {"x", "y", "width", "height"},
                    "几何矩形必须包含位置和尺寸。")
            require(all(type(value) is int for value in rect.values()), "几何必须使用整数逻辑像素。")
            require(rect["width"] > 0 and rect["height"] > 0, "控件尺寸必须为正。")
        if slot == "children":
            require(rect is not None and parent_id is not None, "普通可视控件需要父级及矩形。")
            stack_groups[parent_id].append(_index(node.get("stack_order"), "层叠顺序"))
            require(nodes[parent_id].get("type_id") not in {
                "builtin.button", "builtin.label", "builtin.timer", "builtin.main_window",
            }, "目标组件不接受普通子控件。")
        else:
            require(node.get("stack_order") is None, "结构或非可视节点没有自由层叠顺序。")
        if slot in {"central", "non_visual", "menu_bar", "status_bar"}:
            require(rect is None, "结构或非可视节点没有自由几何矩形。")
        layout = node.get("layout")
        if layout is not None:
            require(isinstance(layout, dict) and layout.get("kind") in {
                "absolute", "horizontal", "vertical", "grid",
            }, "布局方式不受支持。")
        parent_layout = (nodes[parent_id].get("layout") or {}) if parent_id else {}
        managed = slot == "children" and parent_layout.get("kind", "absolute") != "absolute"
        item = node.get("layout_item")
        if managed:
            require(isinstance(item, dict), "受布局管理的控件缺少布局项。")
            layout_groups[parent_id].append(_index(item.get("index"), "布局顺序"))
            if parent_layout["kind"] == "grid":
                row, column = _index(item.get("row"), "行号"), _index(item.get("column"), "列号")
                rows = _index(item.get("row_span"), "行跨度")
                columns = _index(item.get("column_span"), "列跨度")
                require(rows > 0 and columns > 0, "网格跨度必须为正。")
                for old_row, old_column, old_rows, old_columns in grid_groups[parent_id]:
                    overlaps = (row < old_row + old_rows and old_row < row + rows
                                and column < old_column + old_columns and old_column < column + columns)
                    require(not overlaps, "网格布局项不能重叠。")
                grid_groups[parent_id].append((row, column, rows, columns))
        else:
            require(item is None, "自由定位控件不能携带活动布局项。")
    for groups, title in ((object_groups, "对象顺序"), (stack_groups, "层叠顺序"),
                          (layout_groups, "布局顺序")):
        for values in groups.values():
            _dense(values, title)
    handlers = _unique(project.get("handlers", []), "处理函数")
    connections = _unique(project.get("connections", []), "事件连接")
    _unique(project.get("resources", []), "资源")
    for connection in connections.values():
        require(connection.get("source_id") in nodes, "事件源不存在。")
        target = connection.get("target", {})
        require(isinstance(target, dict), "事件目标格式无效。")
        if target.get("kind") == "handler":
            require(target.get("handler_id") in handlers, "处理函数目标不存在。")
        else:
            require(target.get("kind") == "slot" and target.get("node_id") in nodes,
                    "槽目标不存在。")
    tab_order = project.get("tab_order", [])
    require(isinstance(tab_order, list) and all(item in nodes for item in tab_order)
            and len(tab_order) == len(set(tab_order)), "制表顺序存在重复或无效引用。")


def migrate_project(project: Project) -> Project:
    """迁移旧顺序字段，保留未知扩展，不修改输入对象。"""
    result = deepcopy(project)
    if result.get("schema_version") == 2:
        validate_project(result)
        return result
    require(result.get("schema_version") == 1, "项目版本无法迁移。")
    nodes = {node["id"]: node for node in result["nodes"]}
    for node in nodes.values():
        previous = _index(node.pop("order", None), "旧版顺序")
        node["object_order"] = previous
        node["stack_order"] = previous if node["slot"] == "children" else None
        parent = nodes.get(node["parent_id"])
        parent_layout = (parent.get("layout") or {}) if parent else {}
        if node["slot"] == "children" and parent_layout.get("kind", "absolute") != "absolute":
            item = dict(node.get("layout_item") or {})
            item["index"] = previous
            node["layout_item"] = item
    result["schema_version"] = 2
    validate_project(result)
    return result


def ordered_children(project: Project, parent_id: str, kind: OrderKind) -> tuple[str, ...]:
    """三种顺序有独立用途，不能从 Qt 对象列表反推。"""
    nodes = [node for node in project["nodes"]
             if node["parent_id"] == parent_id and node["slot"] == "children"]
    if kind == "layout":
        require(all(node["layout_item"] is not None for node in nodes), "控件尚未纳入布局。")
        return tuple(node["id"] for node in sorted(nodes, key=lambda item: item["layout_item"]["index"]))
    field = "object_order" if kind == "object" else "stack_order"
    return tuple(node["id"] for node in sorted(nodes, key=lambda item: item[field]))


@dataclass(frozen=True)
class Snapshot:
    """用不可变字节隔离参考模型，生产实现应采用受影响分支的持久快照。"""

    state_id: str
    payload: bytes

    def project(self) -> Project:
        """返回独立副本，防止调用者绕过提交修改当前状态。"""
        return json.loads(self.payload)


@dataclass(frozen=True)
class SaveTicket:
    """保存回执必须对应当时捕获的会话和快照。"""

    session_id: str
    revision: int
    snapshot: Snapshot


class ReferenceHistory:
    """验证原子提交及保存点语义，不替代后续的 Qt 命令适配层。"""

    def __init__(self, project: Project, *, saved: bool = True) -> None:
        validate_project(project)
        first = Snapshot(str(uuid4()), canonical_bytes(project))
        self._states = [first]
        self._cursor = 0
        self._saved_id = first.state_id if saved else None
        self._preparing = False
        self._publishing = False
        self._pending: SaveTicket | None = None
        self._listeners: list[Callable[[Snapshot], None]] = []
        self.session_id = str(uuid4())
        self.revision = 0

    @property
    def current(self) -> Snapshot:
        return self._states[self._cursor]

    @property
    def dirty(self) -> bool:
        return self.current.state_id != self._saved_id

    @property
    def can_redo(self) -> bool:
        return self._cursor + 1 < len(self._states)

    def subscribe(self, listener: Callable[[Snapshot], None]) -> None:
        self._listeners.append(listener)

    def _require_idle(self) -> None:
        require(not self._preparing and not self._publishing,
                "文档准备或通知期间不能重入状态操作。")

    def _notify(self) -> None:
        self._publishing = True
        try:
            for listener in tuple(self._listeners):
                try:
                    listener(self.current)
                except Exception:
                    logger.exception("文档订阅者更新失败，已提交的文档与历史保持有效。")
        finally:
            self._publishing = False

    def apply(self, mutation: Callable[[Project], None], *, expected_revision: int | None = None) -> None:
        self._require_idle()
        require(expected_revision is None or expected_revision == self.revision,
                "编辑所依据的文档版本已经过期。")
        self._preparing = True
        try:
            candidate = self.current.project()
            mutation(candidate)
            validate_project(candidate)
            payload = canonical_bytes(candidate)
            if payload == self.current.payload:
                return
            after = Snapshot(str(uuid4()), payload)
            next_states = self._states[:self._cursor + 1] + [after]
            self._states, self._cursor = next_states, len(next_states) - 1
            self.revision += 1
        finally:
            self._preparing = False
        self._notify()

    def undo(self) -> None:
        self._require_idle()
        require(self._cursor > 0, "没有可以撤销的操作。")
        self._cursor -= 1
        self.revision += 1
        self._notify()

    def redo(self) -> None:
        self._require_idle()
        require(self.can_redo, "没有可以重做的操作。")
        self._cursor += 1
        self.revision += 1
        self._notify()

    def begin_save(self) -> SaveTicket:
        self._require_idle()
        require(self._pending is None, "同一文档只能有一个正在提交的保存任务。")
        ticket = SaveTicket(self.session_id, self.revision, self.current)
        self._pending = ticket
        return ticket

    def finish_save(self, ticket: SaveTicket, *, success: bool) -> None:
        self._require_idle()
        require(ticket.session_id == self.session_id and ticket is self._pending,
                "保存回执不属于当前会话的待完成任务。")
        if success:
            self._saved_id = ticket.snapshot.state_id
        self._pending = None
