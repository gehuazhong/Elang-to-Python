"""把模型或构建计划转换为共用的缩放基准，并生成一次可撤销修改。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Any, Protocol

from layout.scaling import ScaleItem, scale_layout
from layout.containers import LAYOUT_TYPES, tab_margins
from .hierarchy import content_size, CONTAINER_MARGINS
from .models import ProjectModel, Rect


class ScaleSource(Protocol):
    id: str
    parent_id: str | None
    slot: str
    type_id: str
    geometry: Rect | None
    properties: Mapping[str, Any]


def scale_items(nodes: Iterable[ScaleSource]) -> tuple[ScaleItem, ...]:
    by_parent: dict[str | None, list[ScaleSource]] = {}
    central: ScaleSource | None = None
    for node in nodes:
        if node.slot == "central":
            central = node
        by_parent.setdefault(node.parent_id, []).append(node)
    if central is None:
        raise ValueError("组件跟随缩放缺少工作区。")
    result: list[ScaleItem] = []
    by_id = {node.id: node for siblings in by_parent.values() for node in siblings}
    pending = [central]
    while pending:
        node = pending.pop()
        if node.slot not in {"central", "children", "pages"}:
            continue
        defaults = CONTAINER_MARGINS.get(node.type_id, (0, 0, 0, 0))
        margins = tuple(node.properties.get("content_" + name, value)
                        for name, value in zip(("left", "top", "right", "bottom"), defaults))
        minimum = (max(64 if node.type_id == "builtin.tab_widget" else 1, margins[0] + margins[2] + 1),
                   max(64 if node.type_id == "builtin.tab_widget" else 1, margins[1] + margins[3] + 1))
        rect = node.geometry
        page_insets = (1, 30, 1, 1)
        if node.slot == "pages" and by_id[node.parent_id].type_id == "builtin.tab_widget":
            owner = by_id[node.parent_id]
            page_insets = tab_margins(owner.properties, sum(child.slot == "pages" for child in by_parent[owner.id]))
        result.append(ScaleItem(node.id, node.parent_id, node.slot,
                                (rect.x, rect.y, rect.width, rect.height) if rect else None, margins, minimum, page_insets))
        if node.type_id not in LAYOUT_TYPES | {"builtin.splitter", "builtin.scroll_area", "builtin.mdi_area",
                                               "builtin.stacked_widget", "builtin.tool_box", "builtin.wizard", "builtin.dialog"}:
            pending.extend(reversed(sorted(by_parent.get(node.id, ()), key=lambda child: child.id)))
    return tuple(result)


def scale_base_size(nodes: Iterable[ScaleSource]) -> tuple[int, int]:
    records = tuple(nodes)
    root = next(node for node in records if node.slot == "root")
    bars = sum(node.properties.get("bar_height", 36 if node.slot == "tool_bar" else 28)
               for node in records if node.slot in {"menu_bar", "tool_bar", "status_bar"} and node.properties.get("visible", True))
    return root.geometry.width, max(1, root.geometry.height - bars)


def follow_window_resize(before: ProjectModel, after: ProjectModel) -> ProjectModel:
    root = before.nodes[before.root_id]
    target = after.nodes[after.root_id]
    if not root.properties.get("scale_children", False) or (root.geometry.width, root.geometry.height) == (target.geometry.width, target.geometry.height):
        return after
    rectangles = scale_layout(scale_items(before.nodes.values()), content_size(before, before.central_id),
                              content_size(after, after.central_id))
    return after.with_nodes({key: replace(after.nodes[key], geometry=Rect(*rect)) for key, rect in rectangles.items()
                             if after.nodes[key].slot == "children"})
