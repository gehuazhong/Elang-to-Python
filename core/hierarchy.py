"""设计控件的内容坐标、祖先关系与容器范围，不依赖原生窗口。"""

from __future__ import annotations

from .errors import require
from .models import ProjectModel, WidgetNode
from layout.containers import PAGE_TYPES, inset_rect, tab_margins

CONTAINER_MARGINS = {"builtin.group_box": (12, 32, 12, 12), "builtin.frame": (12, 12, 12, 12)}


def pages(model: ProjectModel, key: str) -> tuple[WidgetNode, ...]:
    return tuple(sorted((node for node in model.nodes.values() if node.parent_id == key and node.slot == "pages"),
                        key=lambda node: node.object_order))


def active_page(model: ProjectModel, key: str) -> str:
    if model.nodes[key].type_id in PAGE_TYPES:
        available = pages(model, key)
        require(bool(available), "选择夹至少需要一个页面。")
        return available[model.nodes[key].properties.get("current_index", 0)].id
    return key


def window_bars(model: ProjectModel) -> tuple[int, int]:
    def height(slot: str) -> int:
        return sum(node.properties.get("bar_height", 36 if slot == "tool_bar" else 28)
                   for node in model.nodes.values() if node.slot == slot and node.properties.get("visible", True))
    return height("menu_bar") + height("tool_bar"), height("status_bar")


def content_margins(node: WidgetNode) -> tuple[int, int, int, int]:
    defaults = CONTAINER_MARGINS.get(node.type_id, (0, 0, 0, 0))
    return tuple(node.properties.get("content_" + side, default)
                 for side, default in zip(("left", "top", "right", "bottom"), defaults))


def ancestors(model: ProjectModel, key: str) -> tuple[str, ...]:
    result = []
    current = model.nodes[key].parent_id
    while current is not None:
        require(current not in result and current != key, "控件层级不能形成循环。")
        result.append(current)
        current = model.nodes[current].parent_id
    return tuple(result)


def require_unlocked(model: ProjectModel, key: str) -> None:
    require(all(not model.nodes[item].designer["locked"] for item in (key, *ancestors(model, key))),
            "控件或所属容器已锁定，请先解除锁定。")


def selected_roots(model: ProjectModel, keys: tuple[str, ...]) -> tuple[str, ...]:
    selected = set(keys)
    return tuple(key for key in dict.fromkeys(keys) if not selected.intersection(ancestors(model, key)))


def subtree_ids(model: ProjectModel, roots: tuple[str, ...]) -> tuple[str, ...]:
    children: dict[str | None, list[WidgetNode]] = {}
    for node in model.nodes.values():
        children.setdefault(node.parent_id, []).append(node)
    result, pending = [], list(reversed(roots))
    while pending:
        key = pending.pop()
        require(key not in result, "控件层级不能包含循环或重复节点。")
        result.append(key)
        pending.extend(child.id for child in reversed(sorted(children.get(key, ()), key=lambda item: item.object_order)))
    return tuple(result)


def content_size(model: ProjectModel, key: str) -> tuple[int, int]:
    node = model.nodes[key]
    if node.slot == "dock":
        return node.properties.get("dock_width", 280), node.properties.get("dock_height", 220)
    if node.type_id == "builtin.scroll_area" and not node.properties.get("widget_resizable", False):
        return node.properties.get("content_width", 640), node.properties.get("content_height", 480)
    if node.slot == "pages":
        parent = model.nodes[node.parent_id]
        if parent.type_id == "builtin.tab_widget":
            return inset_rect(parent.geometry.width, parent.geometry.height,
                              tab_margins(parent.properties, len(pages(model, parent.id))))[2:]
        rect = model.nodes[node.parent_id].geometry
        return max(1, rect.width - 2), max(1, rect.height - 31)
    rect = model.nodes[model.root_id].geometry if node.slot == "central" else node.geometry
    require(rect is not None, "无法确定容器的内容范围。")
    left, top, right, bottom = content_margins(node)
    if node.slot == "central":
        toolbar, statusbar = window_bars(model)
        return rect.width, max(1, rect.height - toolbar - statusbar)
    return max(1, rect.width - left - right), max(1, rect.height - top - bottom)


def absolute_position(model: ProjectModel, key: str) -> tuple[int, int]:
    node = model.nodes[key]
    if node.slot == "root":
        return 0, 0
    if node.slot == "central":
        return 0, window_bars(model)[0]
    if node.slot == "dock":
        root = model.nodes[model.root_id].geometry
        area = node.properties.get("dock_area", "left")
        width, height = content_size(model, key)
        return (max(0, root.width - width) if area == "right" else 0,
                max(0, root.height - height) if area == "bottom" else window_bars(model)[0])
    if node.slot == "pages":
        x, y = absolute_position(model, node.parent_id)
        parent = model.nodes[node.parent_id]
        if parent.type_id == "builtin.tab_widget":
            left, top, _, _ = inset_rect(parent.geometry.width, parent.geometry.height,
                                        tab_margins(parent.properties, len(pages(model, parent.id))))
            return x + left, y + top
        return x + 1, y + 30
    require(node.geometry is not None, "该组件没有画布坐标。")
    x, y = node.geometry.x, node.geometry.y
    for parent_id in ancestors(model, key):
        parent = model.nodes[parent_id]
        if parent.slot == "root":
            break
        if parent.slot == "central":
            y += window_bars(model)[0]
        if parent.slot == "pages":
            owner = model.nodes[parent.parent_id]
            if owner.type_id == "builtin.tab_widget":
                left, top, _, _ = inset_rect(owner.geometry.width, owner.geometry.height,
                                            tab_margins(owner.properties, len(pages(model, owner.id))))
                x += left
                y += top
            else:
                x += 1
                y += 30
        left, top, _, _ = content_margins(parent)
        x += left + (parent.geometry.x if parent.geometry else 0)
        y += top + (parent.geometry.y if parent.geometry else 0)
    return x, y


def content_origin(model: ProjectModel, key: str) -> tuple[int, int]:
    x, y = absolute_position(model, key)
    left, top, _, _ = content_margins(model.nodes[key])
    return x + left, y + top
