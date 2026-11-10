"""多控件片段保留相对位置、内部连接和共享处理函数，兼容单控件剪贴板。"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any
from uuid import uuid4

from core.errors import DesignerError, require
from core.models import FrozenMap, ProjectModel, Rect, WidgetNode, new_project, thaw
from core.registry import WidgetRegistry
from core.validation import identifier, validate_project
from core.storage import unique_object
from .arrange import bounding_rect, constrain_delta
from .clipboard import ComponentFragment, MAX_CLIPBOARD_BYTES, check_copyable, unique_name, validate_fragment
from .nodes import resolve_radio_selection
from .hierarchy import require_container
from .references import omit_external_references, remap_references
from core.hierarchy import content_size, require_unlocked
from core.menu_values import resolve_pasted_shortcuts


@dataclass(frozen=True, slots=True)
class GroupFragment:
    id: str
    nodes: tuple[WidgetNode, ...]
    connections: tuple[FrozenMap, ...]
    handlers: tuple[FrozenMap, ...]
    tab_order: tuple[str, ...]
    omitted_connections: int


def copy_group(model: ProjectModel, registry: WidgetRegistry, keys: tuple[str, ...]) -> GroupFragment:
    require(len(keys) >= 2 and len(set(keys)) == len(keys), "整组复制至少选择两个不同控件。")
    for key in keys:
        check_copyable(model, registry, key)
    require(len({model.nodes[key].parent_id for key in keys}) == 1, "整组复制要求控件位于同一容器。")
    slots = {model.nodes[key].slot for key in keys}
    require(len(slots) == 1 and slots <= {"children", "non_visual"}, "请分别复制画布控件和非可视组件。")
    selected = set(keys)
    connections = []
    omitted = 0
    for connection in model.data["connections"]:
        source, target = connection["source_id"], connection["target"]
        if source in selected and (target["kind"] == "handler" or target.get("node_id") in selected):
            connections.append(connection)
        elif source in selected or target.get("node_id") in selected:
            omitted += 1
    handlers = {item["target"]["handler_id"] for item in connections if item["target"]["kind"] == "handler"}
    codes = {model.nodes[key].code_name for key in keys}
    nodes = []
    for node in sorted((model.nodes[key] for key in keys), key=lambda node: node.object_order):
        copied, omitted_references = omit_external_references(node, codes)
        nodes.append(copied)
        omitted += omitted_references
    nodes = tuple(nodes)
    result = GroupFragment(str(uuid4()), nodes, tuple(connections),
                           tuple(item for item in model.data["handlers"] if item["id"] in handlers),
                           tuple(key for key in model.data["tab_order"] if key in selected), omitted)
    validate_group(result, registry)
    return result


def validate_group(fragment: GroupFragment, registry: WidgetRegistry) -> None:
    identifier(fragment.id, "剪贴板片段")
    require(2 <= len(fragment.nodes) <= 1000, "整组剪贴板支持二至一千个控件。")
    require(type(fragment.omitted_connections) is int and fragment.omitted_connections >= 0, "剪贴板状态无效。")
    keys = {node.id for node in fragment.nodes}
    require(len(keys) == len(fragment.nodes), "剪贴板控件标识重复。")
    slot = fragment.nodes[0].slot
    require(slot in {"children", "non_visual"} and all(node.slot == slot for node in fragment.nodes),
            "整组剪贴板不能混合画布控件和非可视组件。")
    visual = slot == "children"
    require(visual or all(node.geometry is None and node.stack_order is None for node in fragment.nodes),
            "非可视组件不能包含画布位置或层级。")
    require(len({node.parent_id for node in fragment.nodes}) == 1, "剪贴板控件不属于同一容器。")
    require(len({node.object_order for node in fragment.nodes}) == len(keys)
            and (not visual or len({node.stack_order for node in fragment.nodes}) == len(keys)), "剪贴板控件顺序重复。")
    model = new_project("整组剪贴板校验")
    stack = {node.id: index for index, node in enumerate(sorted(fragment.nodes, key=lambda node: node.stack_order or 0))}
    nodes = {node.id: replace(node, parent_id=model.central_id if visual else model.root_id,
                             object_order=index, stack_order=stack[node.id] if visual else None)
             for index, node in enumerate(sorted(fragment.nodes, key=lambda node: node.object_order))}
    require(not (keys & set(model.nodes)), "剪贴板控件与临时容器标识冲突。")
    model = replace(model.with_nodes(nodes), data=model.data.changed(connections=fragment.connections,
                    handlers=fragment.handlers, tab_order=fragment.tab_order))
    validate_project(model)
    require(set(fragment.tab_order) <= keys, "剪贴板不能引用外部焦点对象。")
    registry.validate(model)
    for key in keys:
        check_copyable(model, registry, key)
    used = set()
    for connection in fragment.connections:
        source, target = connection["source_id"], connection["target"]
        require(source in keys, "剪贴板不能引用外部事件源。")
        handlers = ()
        mapped = connection
        if target["kind"] == "handler":
            used.add(target["handler_id"])
            handlers = tuple(item for item in fragment.handlers if item["id"] == target["handler_id"])
        else:
            require(target["node_id"] in keys, "剪贴板不能引用外部目标控件。")
            mapped = connection.changed(target=target.changed(node_id=source))
        # 复用单控件的事件字段、参数及处理函数声明校验，避免协议分叉。
        validate_fragment(ComponentFragment(fragment.id, nodes[source], (mapped,), handlers, False, 0), registry, context=model)
    require(used == {item["id"] for item in fragment.handlers}, "剪贴板包含未使用的处理函数。")


def encode_group(fragment: GroupFragment) -> bytes:
    value = {"format": "uiplay-components", "version": 2, "id": fragment.id,
             "nodes": [node.to_dict() for node in fragment.nodes], "connections": thaw(fragment.connections),
             "handlers": thaw(fragment.handlers), "tab_order": list(fragment.tab_order),
             "omitted_connections": fragment.omitted_connections}
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    require(len(payload) <= MAX_CLIPBOARD_BYTES, "复制内容过大，最多允许八兆字节。")
    return payload


def decode_group(payload: bytes, registry: WidgetRegistry) -> GroupFragment:
    require(len(payload) <= MAX_CLIPBOARD_BYTES, "剪贴板内容过大，最多允许八兆字节。")
    try:
        value: Any = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
        require(isinstance(value, dict) and value.get("format") == "uiplay-components"
                and type(value.get("version")) is int and value["version"] == 2, "整组剪贴板格式或版本无效。")
        require(set(value) == {"format", "version", "id", "nodes", "connections", "handlers", "tab_order", "omitted_connections"},
                "整组剪贴板字段无效。")
        require(all(isinstance(value[key], list) for key in ("nodes", "connections", "handlers", "tab_order")),
                "整组剪贴板数组格式无效。")
        fragment = GroupFragment(value["id"], tuple(WidgetNode.from_dict(node) for node in value["nodes"]),
                                 tuple(FrozenMap(item) for item in value["connections"]),
                                 tuple(FrozenMap(item) for item in value["handlers"]), tuple(value["tab_order"]),
                                 value["omitted_connections"])
        validate_group(fragment, registry)
        return fragment
    except DesignerError:
        raise
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise DesignerError("整组剪贴板数据损坏，无法粘贴。") from exc


def paste_group(model: ProjectModel, registry: WidgetRegistry, fragment: GroupFragment, *,
                position: tuple[int, int] | None = None, offset: int = 16,
                parent_id: str | None = None) -> tuple[ProjectModel, tuple[str, ...]]:
    validate_group(fragment, registry)
    slot = fragment.nodes[0].slot
    visual = slot == "children"
    parent_id = (parent_id or model.central_id) if visual else model.root_id
    require_unlocked(model, model.root_id)
    dx, dy = 0, 0
    if visual:
        require_container(model, registry, parent_id)
        bounds = bounding_rect(tuple(node.geometry for node in fragment.nodes))
        width, height = content_size(model, parent_id)
        require(bounds.width <= width and bounds.height <= height,
                "整组控件大于目标窗口，请先扩大窗口再粘贴。")
        dx, dy = (position[0] - bounds.x, position[1] - bounds.y) if position else (offset, offset)
        settings = model.data["canvas"]
        dx, dy = constrain_delta(bounds, dx, dy, (width, height),
                                  step=settings["grid_size"] if settings["snap_to_grid"] else 1)
    names = {node.name for node in model.nodes.values()}
    codes = {node.code_name for node in model.nodes.values()} | {item.get("code_name", "") for item in model.data["handlers"]}
    remap = {node.id: str(uuid4()) for node in fragment.nodes}
    handler_remap: dict[str, str] = {}
    offset_order = sum(node.parent_id == parent_id and node.slot == slot for node in model.nodes.values())
    stack = {node.id: offset_order + index for index, node in enumerate(sorted(fragment.nodes, key=lambda node: node.stack_order or 0))}
    changes = {}
    for index, node in enumerate(sorted(fragment.nodes, key=lambda node: node.object_order)):
        rect = node.geometry
        created = replace(node, id=remap[node.id], parent_id=parent_id,
                          name=unique_name(node.name, names, "副本"), code_name=unique_name(node.code_name, codes, "_copy"),
                          object_order=offset_order + index, stack_order=stack[node.id] if visual else None,
                          geometry=Rect(rect.x + dx, rect.y + dy, rect.width, rect.height) if visual else None)
        changes[created.id] = created
    code_map = {node.code_name: changes[remap[node.id]].code_name for node in fragment.nodes}
    changes = {key: remap_references(node, code_map) for key, node in changes.items()}
    handlers = []
    for handler in fragment.handlers:
        handler_remap[handler["id"]] = str(uuid4())
        handlers.append(handler.changed(id=handler_remap[handler["id"]], code_name=unique_name(handler["code_name"], codes, "_copy")))
    connections = []
    for connection in fragment.connections:
        target = connection["target"]
        member = "handler_id" if target["kind"] == "handler" else "node_id"
        target_remap = handler_remap if target["kind"] == "handler" else remap
        connections.append(connection.changed(id=str(uuid4()), source_id=remap[connection["source_id"]],
                           target=target.changed(**{member: target_remap[target[member]]})))
    result = replace(model.with_nodes(changes), data=model.data.changed(
        connections=(*model.data["connections"], *connections), handlers=(*model.data["handlers"], *handlers),
        tab_order=(*model.data["tab_order"], *(remap[key] for key in fragment.tab_order))))
    result = resolve_pasted_shortcuts(result, registry, tuple(changes))
    return resolve_radio_selection(result, tuple(changes)), tuple(changes)
