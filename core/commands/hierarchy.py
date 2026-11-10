"""变更父容器时保留窗口内位置，关联顺序和互斥状态一次提交。"""

from __future__ import annotations

from dataclasses import replace

from core.errors import require
from core.hierarchy import ancestors, absolute_position, content_origin, content_size, require_unlocked
from core.models import ProjectModel, Rect
from core.registry import WidgetRegistry
from .nodes import resolve_radio_selection


def require_container(model: ProjectModel, registry: WidgetRegistry, parent_id: str) -> None:
    require(parent_id in model.nodes, "目标容器已经不存在。")
    parent = model.nodes[parent_id]
    require(registry.require(parent.type_id).can_contain, "目标控件不能容纳子控件。")
    require_unlocked(model, parent_id)
    require(parent.layout is None or parent.layout.get("kind") == "absolute", "目标容器暂不支持此布局方式。")


def reparent_node(model: ProjectModel, registry: WidgetRegistry, key: str, parent_id: str) -> ProjectModel:
    require(key in model.nodes and model.nodes[key].slot == "children", "只能调整画布组件的所属容器。")
    require_container(model, registry, parent_id)
    require(key != parent_id and key not in ancestors(model, parent_id), "不能把容器移入自身或自己的子控件。")
    require_unlocked(model, key)
    node = model.nodes[key]
    if node.parent_id == parent_id:
        return model
    x, y = absolute_position(model, key)
    px, py = content_origin(model, parent_id)
    width, height = content_size(model, parent_id)
    require(node.geometry.width <= width and node.geometry.height <= height, "目标容器放不下该控件，请先扩大容器。")
    x = max(0, min(x - px, width - node.geometry.width))
    y = max(0, min(y - py, height - node.geometry.height))
    old = [item for item in model.nodes.values() if item.parent_id == node.parent_id and item.slot == "children" and item.id != key]
    new_count = sum(item.parent_id == parent_id and item.slot == "children" for item in model.nodes.values())
    changes = {item.id: replace(item, object_order=index) for index, item in enumerate(sorted(old, key=lambda item: item.object_order))}
    for index, item in enumerate(sorted(old, key=lambda item: item.stack_order)):
        changes[item.id] = replace(changes[item.id], stack_order=index)
    changes[key] = replace(node, parent_id=parent_id, object_order=new_count, stack_order=new_count,
                           geometry=Rect(x, y, node.geometry.width, node.geometry.height))
    return resolve_radio_selection(model.with_nodes(changes), (key,))
