"""控件片段的校验、复制与粘贴；模型变更由文档统一提交。"""

from __future__ import annotations

import json
import keyword
import math
from dataclasses import dataclass, replace
from typing import Any
from uuid import uuid4

from core.errors import DesignerError, require
from core.models import FrozenMap, ProjectModel, Rect, WidgetNode, new_project, thaw
from core.registry import WidgetRegistry
from core.validation import identifier, validate_project
from core.hierarchy import content_size
from core.menu_values import resolve_pasted_shortcuts
from .hierarchy import require_container
from .nodes import resolve_radio_selection

MAX_CLIPBOARD_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ComponentFragment:
    id: str
    node: WidgetNode
    connections: tuple[FrozenMap, ...]
    handlers: tuple[FrozenMap, ...]
    in_tab_order: bool
    omitted_connections: int


def check_copyable(model: ProjectModel, registry: WidgetRegistry, node_id: str, *, include_children: bool = False) -> None:
    require(node_id in model.nodes, "所选控件已经不存在。")
    node = model.nodes[node_id]
    require(node.slot in {"children", "non_visual", "tool_bar", "status_bar", "dock"} or (include_children and node.slot == "pages"),
            "主窗口、工作区和单独的选择夹页面不能复制，请复制所属选择夹。")
    spec = registry.require(node.type_id)
    require(spec.toolbox or (include_children and node.slot == "pages"), "该组件尚未接入复制。")
    require(node.type_version == spec.version, "控件版本不一致，不能复制。")
    require(node.layout is None and node.layout_item is None and
            (include_children or not any(child.parent_id == node.id for child in model.nodes.values())),
            "带布局或子控件的对象尚未接入复制。")
    require(not node.extensions and not node.extra and
            set(node.properties) <= {prop.key for prop in spec.properties},
            "该控件包含尚未支持复制的扩展数据。")


def copy_fragment(model: ProjectModel, registry: WidgetRegistry, node_id: str) -> ComponentFragment:
    from .references import omit_external_references
    check_copyable(model, registry, node_id)
    connections: list[FrozenMap] = []
    handler_ids: set[str] = set()
    omitted = 0
    for connection in model.data["connections"]:
        target = connection["target"]
        if connection["source_id"] == node_id and (target["kind"] == "handler" or target.get("node_id") == node_id):
            connections.append(connection)
            if target["kind"] == "handler":
                handler_ids.add(target["handler_id"])
        elif connection["source_id"] == node_id or target.get("node_id") == node_id:
            omitted += 1
    handlers = tuple(item for item in model.data["handlers"] if item["id"] in handler_ids)
    node, omitted_references = omit_external_references(model.nodes[node_id], {model.nodes[node_id].code_name})
    omitted += omitted_references
    fragment = ComponentFragment(str(uuid4()), node, tuple(connections), handlers,
                                 node_id in model.data["tab_order"], omitted)
    validate_fragment(fragment, registry)
    return fragment


def validate_fragment(fragment: ComponentFragment, registry: WidgetRegistry, *, context: ProjectModel | None = None) -> None:
    identifier(fragment.id, "剪贴板片段")
    require(type(fragment.in_tab_order) is bool and type(fragment.omitted_connections) is int
            and fragment.omitted_connections >= 0, "剪贴板状态无效。")
    # 放入独立临时模型，复用项目结构及元数据校验，不把源项目写入剪贴板。
    model = new_project("剪贴板校验")
    visual = fragment.node.slot == "children"
    node = replace(fragment.node, parent_id=model.central_id if visual else model.root_id, object_order=0, stack_order=0 if visual else None)
    if node.type_id == "builtin.mdi_subwindow":
        from .nodes import create_node
        model, area = create_node(model, registry, "builtin.mdi_area", 0, 0)
        node = replace(node, parent_id=area)
    model = replace(model.with_nodes({node.id: node}), data=model.data.changed(
        connections=fragment.connections, handlers=fragment.handlers,
        tab_order=[node.id] if fragment.in_tab_order else []))
    if context is not None:
        model = context
        node = context.nodes[fragment.node.id]
    validate_project(model)
    registry.validate(model)
    check_copyable(model, registry, node.id, include_children=context is not None)
    handler_ids = {item["id"] for item in fragment.handlers}
    used_handlers: set[str] = set()
    for connection in fragment.connections:
        require(connection["source_id"] == node.id, "剪贴板不能包含外部事件源。")
        target = connection["target"]
        if target["kind"] == "handler":
            used_handlers.add(target["handler_id"])
        else:
            require(target["node_id"] == node.id, "剪贴板不能包含外部目标控件。")
        require(set(connection) <= {"id", "source_id", "event", "target", "arguments", "enabled"},
                "该事件连接包含尚未支持复制的扩展数据。")
        allowed = {"kind", "handler_id"} if target["kind"] == "handler" else {"kind", "node_id", "slot"}
        require(set(target) <= allowed, "事件目标包含尚未支持复制的扩展数据。")
        arguments = connection.get("arguments", ())
        require(isinstance(arguments, tuple), "事件参数必须为数组，无法复制该控件。")
        for argument in arguments:
            require(isinstance(argument, FrozenMap) and argument.get("kind") in {"constant", "event_arg"},
                    "该事件参数尚未支持复制。")
            if argument["kind"] == "constant":
                require(argument.get("value") is None or type(argument.get("value")) in {str, int, float, bool},
                        "资源或对象引用参数尚未支持复制。")
                require(argument.get("value_type") in {"string", "int", "integer", "float", "bool", "boolean"},
                        "该常量参数类型尚未支持复制。")
    require(handler_ids == used_handlers, "剪贴板包含未使用的处理函数。")
    for handler in fragment.handlers:
        require(set(handler) <= {"id", "name", "code_name", "parameters", "description"},
                "仅支持复制处理函数声明，外部代码和扩展尚未接入。")
        code = handler.get("code_name")
        require(isinstance(code, str) and code.isascii() and code.isidentifier() and not keyword.iskeyword(code),
                "处理函数代码名称无效。")


def encode_fragment(fragment: ComponentFragment) -> bytes:
    value = {"format": "uiplay-component", "version": 1, "id": fragment.id,
             "node": fragment.node.to_dict(), "connections": thaw(fragment.connections),
             "handlers": thaw(fragment.handlers), "in_tab_order": fragment.in_tab_order,
             "omitted_connections": fragment.omitted_connections}
    data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    require(len(data) <= MAX_CLIPBOARD_BYTES, "复制内容过大，最多允许八兆字节。")
    return data


def decode_fragment(data: bytes, registry: WidgetRegistry) -> ComponentFragment:
    require(len(data) <= MAX_CLIPBOARD_BYTES, "剪贴板内容过大，最多允许八兆字节。")

    def unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "剪贴板包含重复字段，无法粘贴。")
            result[key] = value
        return result

    try:
        value: Any = json.loads(data.decode("utf-8"), object_pairs_hook=unique_fields)
        require(isinstance(value, dict) and value.get("format") == "uiplay-component"
                and type(value.get("version")) is int and value["version"] == 1, "剪贴板控件格式或版本无效。")
        require(set(value) == {"format", "version", "id", "node", "connections", "handlers", "in_tab_order", "omitted_connections"},
                "剪贴板字段不完整或包含尚未支持的扩展，无法粘贴。")
        require(isinstance(value.get("connections"), list) and isinstance(value.get("handlers"), list),
                "剪贴板事件声明格式无效。")
        fragment = ComponentFragment(value["id"], WidgetNode.from_dict(value["node"]),
                                     tuple(FrozenMap(item) for item in value["connections"]),
                                     tuple(FrozenMap(item) for item in value["handlers"]),
                                     value["in_tab_order"], value["omitted_connections"])
        validate_fragment(fragment, registry)
        return fragment
    except DesignerError:
        raise
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise DesignerError("剪贴板控件数据损坏，无法粘贴。") from exc


def unique_name(base: str, used: set[str], suffix: str) -> str:
    candidate = base + suffix
    number = 2
    while candidate in used:
        candidate = base + suffix + str(number)
        number += 1
    used.add(candidate)
    return candidate


def paste_fragment(model: ProjectModel, registry: WidgetRegistry, fragment: ComponentFragment, *,
                   position: tuple[int, int] | None = None, offset: int = 16,
                   parent_id: str | None = None) -> tuple[ProjectModel, str]:
    validate_fragment(fragment, registry)
    if fragment.node.slot != "children":
        from .nodes import create_node
        candidate, key = create_node(model, registry, fragment.node.type_id, 0, 0)
        created = candidate.nodes[key]
        copied = replace(created, properties=fragment.node.properties, designer=fragment.node.designer,
                         name=unique_name(fragment.node.name, {node.name for node in model.nodes.values()}, "副本"),
                         code_name=unique_name(fragment.node.code_name, {node.code_name for node in model.nodes.values()}
                                               | {item.get("code_name", "") for item in model.data["handlers"]}, "_copy"))
        return _paste_events(candidate.with_nodes({key: copied}), fragment, copied), key
    parent_id = parent_id or model.central_id
    if fragment.node.type_id == "builtin.mdi_subwindow" and model.nodes[parent_id].type_id != "builtin.mdi_area":
        from .nodes import create_node
        model, parent_id = create_node(model, registry, "builtin.mdi_area", 0, 0, parent_id=parent_id)
    require_container(model, registry, parent_id)
    central = model.nodes[parent_id]
    require(not central.designer["locked"] and not model.nodes[model.root_id].designer["locked"],
            "目标窗口或工作区已锁定，不能粘贴。")
    require((central.layout or {}).get("kind", "absolute") == "absolute", "目标工作区的布局尚未支持粘贴。")
    original = fragment.node
    rect = original.geometry
    width, height = content_size(model, parent_id)
    if parent_id != model.central_id:
        require(rect.width <= width and rect.height <= height, "目标容器放不下该控件，请先扩大容器。")
    x, y = position if position is not None else (rect.x + offset, rect.y + offset)
    step = model.data["canvas"]["grid_size"] if model.data["canvas"]["snap_to_grid"] else 1
    x = max(0, min(math.floor(x / step + 0.5) * step, max(0, width - rect.width)))
    y = max(0, min(math.floor(y / step + 0.5) * step, max(0, height - rect.height)))
    names = {node.name for node in model.nodes.values()}
    codes = {node.code_name for node in model.nodes.values()} | {item.get("code_name", "") for item in model.data["handlers"]}
    siblings = [node for node in model.nodes.values() if node.parent_id == central.id and node.slot == "children"]
    node = replace(original, id=str(uuid4()), parent_id=central.id,
                   name=unique_name(original.name, names, "副本"), code_name=unique_name(original.code_name, codes, "_copy"),
                   object_order=len(siblings), stack_order=len(siblings), geometry=Rect(x, y, rect.width, rect.height))
    candidate = _paste_events(model.with_nodes({node.id: node}), fragment, node)
    candidate = resolve_pasted_shortcuts(candidate, registry, (node.id,))
    return resolve_radio_selection(candidate, (node.id,)), node.id


def _paste_events(model: ProjectModel, fragment: ComponentFragment, node: WidgetNode) -> ProjectModel:
    remap = {fragment.node.id: node.id}
    codes = {item.code_name for item in model.nodes.values()} | {item.get("code_name", "") for item in model.data["handlers"]}
    handler_remap: dict[str, str] = {}
    handlers: list[FrozenMap] = []
    for handler in fragment.handlers:
        handler_remap[handler["id"]] = str(uuid4())
        handlers.append(handler.changed(id=handler_remap[handler["id"]], code_name=unique_name(handler["code_name"], codes, "_copy")))
    connections: list[FrozenMap] = []
    for connection in fragment.connections:
        target = connection["target"]
        member = "handler_id" if target["kind"] == "handler" else "node_id"
        target_remap = handler_remap if target["kind"] == "handler" else remap
        connections.append(connection.changed(id=str(uuid4()), source_id=node.id,
                                              target=target.changed(**{member: target_remap[target[member]]})))
    return replace(model, data=model.data.changed(
        connections=(*model.data["connections"], *connections), handlers=(*model.data["handlers"], *handlers),
        tab_order=(*model.data["tab_order"], node.id) if fragment.in_tab_order else model.data["tab_order"]))
