"""创建、删除和属性几何修改的候选模型构造。"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from core.errors import require
from core.models import ProjectModel, Rect, WidgetNode, new_node
from core.registry import WidgetRegistry
from core.value_types import quantize_number
from core.hierarchy import require_unlocked
from layout.containers import PAGE_TYPES, managed_child


def create_node(model: ProjectModel, registry: WidgetRegistry, type_id: str, x: int, y: int,
                *, parent_id: str | None = None) -> tuple[ProjectModel, str]:
    from .hierarchy import require_container

    parent_id = parent_id or model.central_id
    spec = registry.require(type_id)
    require(spec.toolbox, "该组件不能从组件箱直接创建。")
    if type_id == "builtin.wizard_page":
        from core.hierarchy import ancestors
        from .pages import add_page
        wizard = next((key for key in (parent_id, *ancestors(model, parent_id))
                       if model.nodes[key].type_id == "builtin.wizard"), None)
        if wizard is None:
            parent_id = next((key for key in (parent_id, *ancestors(model, parent_id))
                              if registry.require(model.nodes[key].type_id).can_contain), model.central_id)
            model, wizard = create_node(model, registry, "builtin.wizard", x, y, parent_id=parent_id)
        return add_page(model, registry, wizard)
    if type_id == "builtin.mdi_subwindow" and model.nodes[parent_id].type_id != "builtin.mdi_area":
        model, parent_id = create_node(model, registry, "builtin.mdi_area", x, y, parent_id=parent_id)
        x, y = 0, 0
    elif type_id != "builtin.mdi_subwindow" and spec.slot == "children" and model.nodes[parent_id].type_id == "builtin.mdi_area":
        model, parent_id = create_node(model, registry, "builtin.mdi_subwindow", 0, 0, parent_id=parent_id)
    if spec.slot in {"non_visual", "tool_bar", "status_bar", "dock"}:
        parent_id = model.root_id
        require_unlocked(model, parent_id)
        require(spec.slot in {"non_visual", "dock"} or not any(node.slot == spec.slot for node in model.nodes.values()),
                "窗口中已存在此组件，请在对象树中选择并编辑。")
    else:
        from core.hierarchy import active_page
        parent_id = active_page(model, parent_id)
        require_container(model, registry, parent_id)
    number = 1
    names = {node.name for node in model.nodes.values()}
    codes = {node.code_name for node in model.nodes.values()}
    while f"{spec.label}{number}" in names or f"{spec.code_prefix}_{number}" in codes:
        number += 1
    siblings = [node for node in model.nodes.values() if node.parent_id == parent_id and node.slot == spec.slot]
    width, height = spec.default_size
    node = new_node(type_id, f"{spec.label}{number}", f"{spec.code_prefix}_{number}", parent_id,
                    spec.slot, len(siblings), Rect(x, y, width, height) if spec.slot == "children" else None, spec.defaults())
    if spec.text_from_name and "text" in node.properties:
        node = replace(node, properties=node.properties.changed(text=node.name))
    result = model.with_nodes({node.id: node})
    if type_id in PAGE_TYPES:
        from .pages import add_page
        result, _ = add_page(result, registry, node.id)
        result, _ = add_page(result, registry, node.id)
    return result, node.id


def set_property(model: ProjectModel, registry: WidgetRegistry, node_id: str, key: str, value: Any) -> ProjectModel:
    require(node_id in model.nodes, "所选控件已经不存在。")
    node = model.nodes[node_id]
    if key == "name":
        require(isinstance(value, str) and bool(value.strip()), "名称不能为空。")
        changed = replace(node, name=value.strip())
    elif key == "layout_order":
        require_unlocked(model, node_id)
        require(managed_child(model, node_id), "只有自动布局中的控件可以设置布局顺序。")
        siblings = sorted((other for other in model.nodes.values() if other.parent_id == node.parent_id
                           and other.slot == "children"), key=lambda other: other.object_order)
        require(type(value) is int and 0 <= value < len(siblings), "布局顺序超出有效范围。")
        siblings.remove(node)
        siblings.insert(value, node)
        return model.with_nodes({other.id: replace(other, object_order=index) for index, other in enumerate(siblings)})
    elif key.startswith("geometry."):
        require_unlocked(model, node_id)
        require(not managed_child(model, node_id), "该控件的位置和尺寸由自动布局管理。")
        require(node.geometry is not None, "该控件的位置和尺寸由容器管理。")
        member = key.split(".", 1)[1]
        require(member in {"x", "y", "width", "height"}, "几何属性无效。")
        values = {**node.geometry.to_dict(), member: value}
        changed = replace(node, geometry=Rect.from_dict(values))
    else:
        spec = registry.require(node.type_id).property(key)
        require(not spec.read_only, "该属性只允许查看。")
        changed = replace(node, properties=node.properties.changed(**{key: spec.normalize(value)}))
        values = registry.require(node.type_id).defaults().changed(**changed.properties)
        if key in {"layout_row", "layout_column"}:
            other = "layout_column" if key == "layout_row" else "layout_row"
            changed = replace(changed, properties=changed.properties.changed(**{
                other: -1 if value == -1 else max(0, values[other])}))
        if node.type_id in {"builtin.button", "builtin.tool_button", "builtin.command_link_button", "builtin.menu_item", "builtin.group_box"}:
            if key == "checked" and value:
                changed = replace(changed, properties=changed.properties.changed(checkable=True))
            elif key == "checkable" and not value:
                changed = replace(changed, properties=changed.properties.changed(checked=False))
        if key == "decimals" and node.type_id == "builtin.double_spin_box":
            adjusted = {field: quantize_number(values[field], value) for field in ("minimum", "maximum", "value", "single_step")}
            adjusted["single_step"] = max(adjusted["single_step"], 10 ** -value)
            changed = replace(changed, properties=changed.properties.changed(**adjusted))
        if key in {"minimum", "maximum"} and "value" in values:
            require(values["minimum"] <= values["maximum"], "最小值不能大于最大值。")
            changed = replace(changed, properties=changed.properties.changed(
                value=max(values["minimum"], min(values["maximum"], values["value"]))))
        if key == "items" and node.type_id in {"builtin.combo_box", "builtin.list_widget", "builtin.tab_bar"}:
            changed = replace(changed, properties=changed.properties.changed(current_index=min(values["current_index"], len(values["items"]) - 1)))
        if key == "table_data" and node.type_id == "builtin.super_list":
            changed = replace(changed, properties=changed.properties.changed(
                checked_rows=tuple(item for item in values["checked_rows"] if int(item) <= len(value["rows"]))))
        if key == "tristate" and not value and values.get("check_state") == "partial":
            changed = replace(changed, properties=changed.properties.changed(check_state="unchecked"))
    result = model.with_nodes({node_id: changed})
    if node.slot == "root" and key in {"geometry.width", "geometry.height"}:
        from core.window_scaling import follow_window_resize
        result = follow_window_resize(model, result)
    if key in {"checked", "auto_exclusive", "check_state", "members", "exclusive"}:
        result = resolve_explicit_groups(result, node_id)
        result = resolve_radio_selection(result, (node_id,))
    return result


def resolve_explicit_groups(model, preferred):
    for group in model.nodes.values():
        if group.type_id != "builtin.button_group" or not group.properties.get("exclusive", True):
            continue
        members = [node for node in model.nodes.values() if node.code_name in group.properties.get("members", ())
                   and (node.properties.get("checked", False) or node.properties.get("check_state") == "checked")]
        members.sort(key=lambda node: node.id != preferred)
        changes = {node.id: replace(node, properties=node.properties.changed(**{
            "check_state": "unchecked"} if node.type_id == "builtin.check_box" else {"checked": False})) for node in members[1:]}
        model = model.with_nodes(changes)
    return model


def resolve_radio_selection(model: ProjectModel, preferred_ids: tuple[str, ...]) -> ProjectModel:
    """属性修改和粘贴使用同一互斥规则，关联取消选中进入同一条撤销记录。"""
    explicit_members = {name for group in model.nodes.values() if group.type_id == "builtin.button_group"
                        for name in group.properties.get("members", ())}
    for key in preferred_ids:
        node = model.nodes[key]
        if node.code_name in explicit_members or node.type_id != "builtin.radio_button" or not node.properties.get("auto_exclusive", True) or not node.properties.get("checked", False):
            continue
        changes = {other.id: replace(other, properties=other.properties.changed(checked=False))
                   for other in model.nodes.values() if other.id != key and other.parent_id == node.parent_id
                   and other.type_id == "builtin.radio_button" and other.properties.get("auto_exclusive", True)
                   and other.code_name not in explicit_members
                   and other.properties.get("checked", False)}
        model = model.with_nodes(changes)
    return model


def move_node(model: ProjectModel, node_id: str, x: int, y: int) -> ProjectModel:
    require(node_id in model.nodes, "所选控件已经不存在。")
    require(not managed_child(model, node_id), "自动布局中的控件不能自由移动。")
    node = model.nodes[node_id]
    require(node.slot == "children" and node.geometry is not None, "此对象不能在画布自由移动。")
    require_unlocked(model, node_id)
    return model.with_nodes({node_id: replace(node, geometry=replace(node.geometry, x=x, y=y))})


def resize_node(model: ProjectModel, node_id: str, geometry: Rect) -> ProjectModel:
    require(node_id in model.nodes, "所选对象已经不存在。")
    require(not managed_child(model, node_id), "自动布局中的控件不能自由调整尺寸。")
    node = model.nodes[node_id]
    require(node.slot in {"root", "children"} and node.geometry is not None, "此对象的尺寸由容器管理。")
    require_unlocked(model, node_id)
    geometry = Rect.from_dict(geometry.to_dict())
    if node.slot == "root":
        require((geometry.x, geometry.y) == (node.geometry.x, node.geometry.y), "画布缩放不能修改窗口的屏幕位置。")
    result = model.with_nodes({node_id: replace(node, geometry=geometry)})
    if node.slot == "root":
        from core.window_scaling import follow_window_resize
        result = follow_window_resize(model, result)
    return result


def delete_node(model: ProjectModel, node_id: str) -> ProjectModel:
    return delete_nodes(model, (node_id,))


def delete_nodes(model: ProjectModel, node_ids: tuple[str, ...]) -> ProjectModel:
    require(bool(node_ids) and all(key in model.nodes and model.nodes[key].slot in {"children", "pages", "non_visual", "tool_bar", "status_bar", "menu_bar", "menu", "dock"} for key in node_ids),
            "根窗口和工作区不能删除。")
    children: dict[str | None, list[str]] = {}
    for node in model.nodes.values():
        children.setdefault(node.parent_id, []).append(node.id)
    removed = set(node_ids)
    for key in node_ids:
        require_unlocked(model, key)
    pending = list(removed)
    while pending:
        parent = pending.pop()
        for key in children.get(parent, ()):
            if key not in removed:
                removed.add(key)
                pending.append(key)
    require(all(not model.nodes[key].designer["locked"] for key in removed), "删除范围内包含锁定控件。")
    result = model.with_nodes({key: None for key in removed})
    from core.hierarchy import pages
    for tab in (item for item in result.nodes.values() if item.type_id in PAGE_TYPES):
        remaining = pages(result, tab.id)
        require(bool(remaining), "选择夹至少需要保留一个页面。")
        previous_pages = pages(model, tab.id)
        selected = previous_pages[model.nodes[tab.id].properties.get("current_index", 0)].id
        current = next((index for index, page in enumerate(remaining) if page.id == selected), min(tab.properties.get("current_index", 0), len(remaining) - 1))
        result = result.with_nodes({tab.id: replace(tab, properties=tab.properties.changed(current_index=current))})
    removed_codes = {model.nodes[key].code_name for key in removed}
    for reference in ("trigger_control", "navigation_page"):
        result = result.with_nodes({node.id: replace(node, properties=node.properties.changed(**{reference: ""}))
                                   for node in result.nodes.values() if node.properties.get(reference) in removed_codes})
    result = result.with_nodes({node.id: replace(node, properties=node.properties.changed(
        members=tuple(name for name in node.properties["members"] if name not in removed_codes)))
        for node in result.nodes.values() if node.type_id == "builtin.button_group"})
    changes = {}
    scopes: dict[tuple[str | None, str], list[WidgetNode]] = {}
    for node in result.nodes.values():
        scopes.setdefault((node.parent_id, node.slot), []).append(node)
    for (_, slot), group in scopes.items():
        siblings = sorted(group, key=lambda node: node.object_order)
        for order, node in enumerate(siblings):
            changes[node.id] = replace(node, object_order=order)
        if slot == "children":
            for order, node in enumerate(sorted(siblings, key=lambda node: node.stack_order)):
                changes[node.id] = replace(changes[node.id], stack_order=order)
    connections = [item for item in model.data["connections"] if item["source_id"] not in removed
                   and item["target"].get("node_id") not in removed]
    return replace(result.with_nodes(changes), data=model.data.changed(
        connections=connections, tab_order=[key for key in model.data["tab_order"] if key not in removed]))
