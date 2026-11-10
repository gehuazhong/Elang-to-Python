"""容器片段复制完整子树，保留局部坐标、内部连接和焦点顺序。"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any
from uuid import uuid4

from core.errors import DesignerError, require
from core.hierarchy import content_size, selected_roots, subtree_ids
from core.menu_values import resolve_pasted_shortcuts
from core.models import FrozenMap, ProjectModel, Rect, WidgetNode, new_project, thaw
from core.registry import WidgetRegistry
from core.storage import unique_object
from core.validation import identifier, validate_project
from .arrange import bounding_rect, constrain_delta
from .clipboard import ComponentFragment, MAX_CLIPBOARD_BYTES, check_copyable, unique_name, validate_fragment
from .hierarchy import require_container
from .nodes import resolve_radio_selection
from .references import omit_external_references, remap_references


@dataclass(frozen=True, slots=True)
class TreeFragment:
    id: str
    nodes: tuple[WidgetNode, ...]
    roots: tuple[str, ...]
    connections: tuple[FrozenMap, ...]
    handlers: tuple[FrozenMap, ...]
    tab_order: tuple[str, ...]
    omitted_connections: int


def copy_tree(model: ProjectModel, registry: WidgetRegistry, keys: tuple[str, ...]) -> TreeFragment:
    roots = selected_roots(model, keys)
    require(bool(roots) and len({model.nodes[key].parent_id for key in roots}) == 1, "复制的顶层组件须位于同一容器。")
    roots = tuple(sorted(roots, key=lambda key: model.nodes[key].object_order))
    included = subtree_ids(model, roots)
    for key in included:
        check_copyable(model, registry, key, include_children=True)
    connections, omitted = [], 0
    included_set = set(included)
    for connection in model.data["connections"]:
        source, target = connection["source_id"], connection["target"]
        if source in included_set and (target["kind"] == "handler" or target.get("node_id") in included_set):
            connections.append(connection)
        elif source in included_set or target.get("node_id") in included_set:
            omitted += 1
    used = {connection["target"]["handler_id"] for connection in connections if connection["target"]["kind"] == "handler"}
    copied_nodes = []
    codes = {model.nodes[key].code_name for key in included}
    for key in included:
        node, omitted_references = omit_external_references(model.nodes[key], codes)
        omitted += omitted_references
        copied_nodes.append(node)
    result = TreeFragment(str(uuid4()), tuple(copied_nodes), roots, tuple(connections),
                          tuple(item for item in model.data["handlers"] if item["id"] in used),
                          tuple(key for key in model.data["tab_order"] if key in included_set), omitted)
    validate_tree(result, registry)
    return result


def validate_tree(fragment: TreeFragment, registry: WidgetRegistry) -> None:
    identifier(fragment.id, "控件树剪贴板")
    require(1 <= len(fragment.nodes) <= 1000, "控件树复制最多支持一千个节点。")
    nodes = {node.id: node for node in fragment.nodes}
    require(len(nodes) == len(fragment.nodes), "控件树包含重复节点。")
    require(bool(fragment.roots) and len(set(fragment.roots)) == len(fragment.roots)
            and set(fragment.roots) <= nodes.keys(), "控件树根节点无效。")
    require(type(fragment.omitted_connections) is int and fragment.omitted_connections >= 0, "剪贴板状态无效。")
    require(len({nodes[key].parent_id for key in fragment.roots}) == 1, "控件树顶层节点须属于同一容器。")
    root_set = set(fragment.roots)
    root_slot = nodes[fragment.roots[0]].slot
    require(root_slot in {"children", "dock"} and all(nodes[key].slot == root_slot for key in root_set), "控件树顶层挂接位置必须相同。")
    require(all((node.parent_id not in nodes) == (node.id in root_set) for node in nodes.values()), "控件树包含断开的父子关系。")
    require(len({nodes[key].object_order for key in fragment.roots}) == len(root_set)
            and (root_slot == "dock" or len({nodes[key].stack_order for key in fragment.roots}) == len(root_set)), "控件树顶层顺序重复。")
    model = new_project("控件树校验")
    require(not set(nodes).intersection(model.nodes), "控件树标识冲突。")
    stack = {key: index for index, key in enumerate(sorted(fragment.roots, key=lambda key: nodes[key].stack_order or 0))}
    parent = model.root_id if root_slot == "dock" else model.central_id
    if all(nodes[key].type_id == "builtin.mdi_subwindow" for key in fragment.roots):
        from .nodes import create_node
        model, parent = create_node(model, registry, "builtin.mdi_area", 0, 0)
    for index, key in enumerate(sorted(fragment.roots, key=lambda key: nodes[key].object_order)):
        nodes[key] = replace(nodes[key], parent_id=parent, object_order=index, stack_order=stack[key] if root_slot == "children" else None)
    model = replace(model.with_nodes(nodes), data=model.data.changed(connections=fragment.connections,
                    handlers=fragment.handlers, tab_order=fragment.tab_order))
    validate_project(model)
    registry.validate(model)
    require(set(subtree_ids(model, fragment.roots)) == set(nodes), "控件树存在未连接的节点。")
    require(set(fragment.tab_order) <= nodes.keys(), "焦点顺序不能引用外部控件。")
    for key in nodes:
        check_copyable(model, registry, key, include_children=True)
    used = set()
    for connection in fragment.connections:
        source, target = connection["source_id"], connection["target"]
        require(source in nodes, "控件树不能包含外部事件源。")
        mapped, handlers = connection, ()
        if target["kind"] == "handler":
            used.add(target["handler_id"])
            handlers = tuple(item for item in fragment.handlers if item["id"] == target["handler_id"])
        else:
            require(target["node_id"] in nodes, "控件树不能引用外部事件目标。")
            mapped = connection.changed(target=target.changed(node_id=source))
        validate_fragment(ComponentFragment(fragment.id, nodes[source], (mapped,), handlers, False, 0), registry, context=model)
    require(used == {item["id"] for item in fragment.handlers}, "控件树包含未使用的处理函数。")


def encode_tree(fragment: TreeFragment) -> bytes:
    value = {"format": "uiplay-widget-tree", "version": 1, "id": fragment.id,
             "nodes": [node.to_dict() for node in fragment.nodes], "roots": list(fragment.roots),
             "connections": thaw(fragment.connections), "handlers": thaw(fragment.handlers),
             "tab_order": list(fragment.tab_order), "omitted_connections": fragment.omitted_connections}
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    require(len(payload) <= MAX_CLIPBOARD_BYTES, "复制内容最多允许八兆字节。")
    return payload


def decode_tree(payload: bytes, registry: WidgetRegistry) -> TreeFragment:
    require(len(payload) <= MAX_CLIPBOARD_BYTES, "剪贴板内容最多允许八兆字节。")
    try:
        value: Any = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
        require(isinstance(value, dict) and value.get("format") == "uiplay-widget-tree"
                and type(value.get("version")) is int and value["version"] == 1, "控件树剪贴板格式无效。")
        require(set(value) == {"format", "version", "id", "nodes", "roots", "connections", "handlers", "tab_order", "omitted_connections"},
                "控件树剪贴板字段无效。")
        require(all(isinstance(value[key], list) for key in ("nodes", "roots", "connections", "handlers", "tab_order")),
                "控件树剪贴板数组格式无效。")
        fragment = TreeFragment(value["id"], tuple(WidgetNode.from_dict(node) for node in value["nodes"]), tuple(value["roots"]),
                                tuple(FrozenMap(item) for item in value["connections"]), tuple(FrozenMap(item) for item in value["handlers"]),
                                tuple(value["tab_order"]), value["omitted_connections"])
        validate_tree(fragment, registry)
        return fragment
    except DesignerError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise DesignerError("控件树剪贴板损坏，无法粘贴。") from exc


def paste_tree(model: ProjectModel, registry: WidgetRegistry, fragment: TreeFragment, *,
               position: tuple[int, int] | None = None, offset: int = 16,
               parent_id: str | None = None) -> tuple[ProjectModel, tuple[str, ...]]:
    validate_tree(fragment, registry)
    parent_id = parent_id or model.central_id
    originals = {node.id: node for node in fragment.nodes}
    root_slot = originals[fragment.roots[0]].slot
    if root_slot == "dock":
        from core.hierarchy import require_unlocked
        parent_id = model.root_id
        require_unlocked(model, parent_id)
        dx, dy = 0, 0
    else:
        if all(originals[key].type_id == "builtin.mdi_subwindow" for key in fragment.roots) and model.nodes[parent_id].type_id != "builtin.mdi_area":
            from .nodes import create_node
            model, parent_id = create_node(model, registry, "builtin.mdi_area", 0, 0, parent_id=parent_id)
        require_container(model, registry, parent_id)
        bounds = bounding_rect(tuple(originals[key].geometry for key in fragment.roots))
        size = content_size(model, parent_id)
        require(bounds.width <= size[0] and bounds.height <= size[1], "目标容器放不下复制的控件树，请先扩大容器。")
        dx, dy = (position[0] - bounds.x, position[1] - bounds.y) if position else (offset, offset)
        canvas = model.data["canvas"]
        dx, dy = constrain_delta(bounds, dx, dy, size, step=canvas["grid_size"] if canvas["snap_to_grid"] else 1)
    names = {node.name for node in model.nodes.values()}
    codes = {node.code_name for node in model.nodes.values()} | {item.get("code_name", "") for item in model.data["handlers"]}
    remap = {key: str(uuid4()) for key in originals}
    root_set = set(fragment.roots)
    order_offset = sum(node.parent_id == parent_id and node.slot == root_slot for node in model.nodes.values())
    orders = {key: order_offset + index for index, key in enumerate(sorted(fragment.roots, key=lambda key: originals[key].object_order))}
    stacks = {key: order_offset + index for index, key in enumerate(sorted(fragment.roots, key=lambda key: originals[key].stack_order or 0))}
    changes = {}
    for node in fragment.nodes:
        root = node.id in root_set
        rect = node.geometry
        copied = replace(node, id=remap[node.id], parent_id=parent_id if root else remap[node.parent_id],
                         name=unique_name(node.name, names, "副本"), code_name=unique_name(node.code_name, codes, "_copy"),
                         object_order=orders[node.id] if root else node.object_order,
                         stack_order=stacks[node.id] if root and root_slot == "children" else node.stack_order,
                         geometry=Rect(rect.x + dx, rect.y + dy, rect.width, rect.height) if root and rect else rect)
        changes[copied.id] = copied
    code_map = {node.code_name: changes[remap[node.id]].code_name for node in fragment.nodes}
    for key, node in tuple(changes.items()):
        changes[key] = remap_references(node, code_map)
    handler_map = {item["id"]: str(uuid4()) for item in fragment.handlers}
    handlers = tuple(item.changed(id=handler_map[item["id"]], code_name=unique_name(item["code_name"], codes, "_copy"))
                     for item in fragment.handlers)
    connections = []
    for connection in fragment.connections:
        target = connection["target"]
        member = "handler_id" if target["kind"] == "handler" else "node_id"
        mapping = handler_map if target["kind"] == "handler" else remap
        connections.append(connection.changed(id=str(uuid4()), source_id=remap[connection["source_id"]],
                                               target=target.changed(**{member: mapping[target[member]]})))
    result = replace(model.with_nodes(changes), data=model.data.changed(connections=(*model.data["connections"], *connections),
                     handlers=(*model.data["handlers"], *handlers), tab_order=(*model.data["tab_order"], *(remap[key] for key in fragment.tab_order))))
    result = resolve_pasted_shortcuts(result, registry, tuple(changes))
    return resolve_radio_selection(result, tuple(changes)), tuple(remap[key] for key in fragment.roots)
