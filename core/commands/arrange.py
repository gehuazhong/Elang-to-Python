"""批量几何操作只构造候选模型，统一提交后才影响文档和历史。"""

from __future__ import annotations

from dataclasses import replace
import math

from core.errors import require
from core.models import ProjectModel, Rect, WidgetNode
from core.hierarchy import content_size, require_unlocked
from .nodes import delete_nodes
from layout.containers import managed_child

ARRANGEMENTS = {
    "left": "左对齐", "hcenter": "水平居中对齐", "right": "右对齐",
    "top": "顶端对齐", "vcenter": "垂直居中对齐", "bottom": "底端对齐",
    "horizontal": "水平等间距", "vertical": "垂直等间距",
    "same_width": "等宽", "same_height": "等高", "same_size": "等宽高",
}

STACKING = {"raise": "上移一层", "lower": "下移一层", "front": "置于顶层", "back": "置于底层"}


def _stacking_selection(model: ProjectModel, keys: tuple[str, ...]) -> tuple[list[WidgetNode], set[str]]:
    nodes = editable_siblings(model, keys)
    ordered = sorted((node for node in model.nodes.values()
                      if node.parent_id == nodes[0].parent_id and node.slot == "children"),
                     key=lambda node: node.stack_order)
    return ordered, set(keys)


def available_stacking(model: ProjectModel, keys: tuple[str, ...]) -> frozenset[str]:
    ordered, selected = _stacking_selection(model, keys)
    flags = [node.id in selected for node in ordered]
    allowed = set()
    if any(lower and not upper for lower, upper in zip(flags, flags[1:])):
        allowed.update(("raise", "front"))
    if any(upper and not lower for lower, upper in zip(flags, flags[1:])):
        allowed.update(("lower", "back"))
    return frozenset(allowed)


def stack_nodes(model: ProjectModel, keys: tuple[str, ...], mode: str) -> ProjectModel:
    require(mode in STACKING, "不支持此层级操作。")
    ordered, selected = _stacking_selection(model, keys)
    if mode in {"front", "back"}:
        chosen = [node for node in ordered if node.id in selected]
        others = [node for node in ordered if node.id not in selected]
        ordered = others + chosen if mode == "front" else chosen + others
    else:
        direction = 1 if mode == "raise" else -1
        indices = range(len(ordered) - 2, -1, -1) if direction == 1 else range(1, len(ordered))
        for index in indices:
            neighbor = index + direction
            if ordered[index].id in selected and ordered[neighbor].id not in selected:
                ordered[index], ordered[neighbor] = ordered[neighbor], ordered[index]
    return model.with_nodes({node.id: replace(node, stack_order=index) for index, node in enumerate(ordered)
                             if node.stack_order != index})


def editable_siblings(model: ProjectModel, keys: tuple[str, ...]) -> tuple[WidgetNode, ...]:
    require(bool(keys) and len(set(keys)) == len(keys), "请选择有效的控件集合。")
    require(all(key in model.nodes for key in keys), "所选控件已经不存在。")
    nodes = tuple(model.nodes[key] for key in keys)
    require(all(node.slot == "children" and node.geometry is not None and node.layout_item is None for node in nodes),
            "所选对象包含不能自由定位的组件。")
    require(len({node.parent_id for node in nodes}) == 1, "批量移动和排版要求控件位于同一容器。")
    require(not any(node.designer["locked"] for node in nodes), "所选控件包含锁定对象，请先解除锁定。")
    for node in nodes:
        require_unlocked(model, node.id)
        require(not managed_child(model, node.id), "自动布局中的控件不能自由排版。")
    return nodes


def bounding_rect(rectangles: tuple[Rect, ...]) -> Rect:
    require(bool(rectangles), "没有可计算范围的控件。")
    left, top = min(rect.x for rect in rectangles), min(rect.y for rect in rectangles)
    return Rect(left, top, max(rect.x + rect.width for rect in rectangles) - left,
                max(rect.y + rect.height for rect in rectangles) - top)


def constrain_delta(bounds: Rect, dx: float, dy: float, size: tuple[int, int], *, step: int = 1) -> tuple[int, int]:
    """按整体范围约束公共偏移，不逐个夹取坐标而破坏相对间距。"""
    x = math.floor((bounds.x + dx) / step + 0.5) * step - bounds.x
    y = math.floor((bounds.y + dy) / step + 0.5) * step - bounds.y
    def axis(value: int, start: int, length: int, extent: int) -> int:
        if length > extent:
            return 0
        return max(-start, min(value, extent - start - length))
    return axis(x, bounds.x, bounds.width, size[0]), axis(y, bounds.y, bounds.height, size[1])


def move_nodes(model: ProjectModel, keys: tuple[str, ...], dx: int, dy: int) -> ProjectModel:
    nodes = editable_siblings(model, keys)
    require(type(dx) is int and type(dy) is int, "移动距离必须为整数。")
    return model.with_nodes({node.id: replace(node, geometry=Rect.from_dict({**node.geometry.to_dict(),
                                "x": node.geometry.x + dx, "y": node.geometry.y + dy})) for node in nodes})


def arrange_nodes(model: ProjectModel, keys: tuple[str, ...], mode: str, primary: str) -> ProjectModel:
    require(mode in ARRANGEMENTS, "不支持此排版操作。")
    nodes = editable_siblings(model, keys)
    distribution = mode in {"horizontal", "vertical"}
    require(len(nodes) >= (3 if distribution else 2), "等间距至少选择三个控件。" if distribution else "排版至少选择两个控件。")
    require(primary in keys, "排版基准控件不在所选范围内。")
    anchor = model.nodes[primary].geometry
    positions: dict[str, tuple[int, int]] = {}
    if distribution:
        horizontal = mode == "horizontal"
        ordered = sorted(nodes, key=lambda node: ((node.geometry.x if horizontal else node.geometry.y), node.object_order, node.id))
        start = ordered[0].geometry.x if horizontal else ordered[0].geometry.y
        last = ordered[-1].geometry
        end = last.x + last.width if horizontal else last.y + last.height
        lengths = [node.geometry.width if horizontal else node.geometry.height for node in ordered]
        available = end - start - sum(lengths)
        require(available >= 0, "所选范围不足以排成不重叠的等间距，请先拉开首尾控件。")
        used = 0
        for index, node in enumerate(ordered):
            value = start + used + math.floor(index * available / (len(nodes) - 1) + 0.5)
            positions[node.id] = (value, node.geometry.y) if horizontal else (node.geometry.x, value)
            used += lengths[index]
    else:
        for node in nodes:
            rect = node.geometry
            x, y = rect.x, rect.y
            if mode == "left":
                x = anchor.x
            elif mode == "right":
                x = anchor.x + anchor.width - rect.width
            elif mode == "hcenter":
                x = math.floor(anchor.x + (anchor.width - rect.width) / 2 + 0.5)
            elif mode == "top":
                y = anchor.y
            elif mode == "bottom":
                y = anchor.y + anchor.height - rect.height
            elif mode == "vcenter":
                y = math.floor(anchor.y + (anchor.height - rect.height) / 2 + 0.5)
            positions[node.id] = x, y
    width, height = content_size(model, nodes[0].parent_id)
    changes = {}
    for node in nodes:
        x, y = positions[node.id]
        rect = node.geometry
        target_width = anchor.width if mode in {"same_width", "same_size"} else rect.width
        target_height = anchor.height if mode in {"same_height", "same_size"} else rect.height
        require(0 <= x and 0 <= y and x + target_width <= width and y + target_height <= height,
                "排版结果超出父容器，请调整基准控件或扩大窗口。")
        changes[node.id] = replace(node, geometry=Rect(x, y, target_width, target_height))
    return model.with_nodes(changes)
