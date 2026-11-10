"""菜单草稿的结构操作，保持节点与事件处理函数身份。"""

from dataclasses import replace
import keyword

from core.errors import require
from core.hierarchy import ancestors, require_unlocked, subtree_ids
from core.menu_values import normalize_shortcut
from core.models import new_node
from .nodes import delete_node


def menu_children(model, parent_id):
    return tuple(sorted((node for node in model.nodes.values() if node.parent_id == parent_id and node.slot == "menu"),
                        key=lambda node: node.object_order))


def ensure_menu_bar(model, registry):
    existing = next((node for node in model.nodes.values() if node.slot == "menu_bar"), None)
    if existing:
        return model, existing.id
    require_unlocked(model, model.root_id)
    node = new_node("builtin.menu_bar", unique_name(model, "菜单栏"), unique_code(model, "menu_bar"),
                    model.root_id, "menu_bar", 0, None, registry.require("builtin.menu_bar").defaults())
    return model.with_nodes({node.id: node}), node.id


def unique_name(model, base):
    names = {node.name for node in model.nodes.values()}
    candidate, number = base, 2
    while candidate in names:
        candidate, number = f"{base}{number}", number + 1
    return candidate


def unique_code(model, base):
    codes = {node.code_name for node in model.nodes.values()}
    candidate, number = base, 2
    while candidate in codes:
        candidate, number = f"{base}_{number}", number + 1
    return candidate


def add_menu(model, registry, parent_id, *, after_id=None, separator=False):
    require_unlocked(model, parent_id)
    parent = model.nodes[parent_id]
    require(parent.type_id in {"builtin.menu_bar", "builtin.menu_item"}, "请选择菜单栏或父菜单。")
    require(not parent.properties.get("separator", False), "分隔线不能包含子菜单。")
    require(not separator or parent.slot == "menu", "顶层菜单不能是分隔线。")
    require(sum(node.slot == "menu" for node in model.nodes.values()) < 200, "每个窗口最多允许二百个菜单项。")
    siblings = menu_children(model, parent_id)
    order = len(siblings) if after_id is None else next(node.object_order + 1 for node in siblings if node.id == after_id)
    spec = registry.require("builtin.menu_item")
    node = new_node(spec.type_id, unique_name(model, "分隔线" if separator else "菜单"), unique_code(model, "menu_1"),
                    parent_id, "menu", order, None, spec.defaults().changed(text="-" if separator else "新菜单", separator=separator))
    result = model.with_nodes({**{other.id: replace(other, object_order=other.object_order + 1)
                                 for other in siblings if other.object_order >= order}, node.id: node})
    registry.validate(result)
    return result, node.id


def move_menu(model, registry, key, direction):
    node = model.nodes[key]
    require(node.slot == "menu", "请选择一个菜单项。")
    require_unlocked(model, key)
    require(all(not model.nodes[child].designer["locked"] for child in subtree_ids(model, (key,))),
            "移动范围内包含锁定菜单。")
    siblings = list(menu_children(model, node.parent_id))
    index = siblings.index(node)
    if direction in {"up", "down"}:
        target = index + (-1 if direction == "up" else 1)
        require(0 <= target < len(siblings), "菜单已位于当前层级的边界。")
        other = siblings[target]
        require_unlocked(model, other.id)
        result = model.with_nodes({node.id: replace(node, object_order=target), other.id: replace(other, object_order=index)})
    else:
        if direction == "right":
            require(index > 0, "第一项不能右移，请先在它前面添加父菜单。")
            parent = siblings[index - 1]
            require(not parent.properties.get("separator", False), "分隔线不能作为父菜单。")
            new_order = len(menu_children(model, parent.id))
        else:
            require(direction == "left" and model.nodes[node.parent_id].slot == "menu", "顶层菜单不能继续左移。")
            previous_parent = model.nodes[node.parent_id]
            parent = model.nodes[previous_parent.parent_id]
            new_order = previous_parent.object_order + 1
        require_unlocked(model, parent.id)
        changes = {other.id: replace(other, object_order=other.object_order - 1) for other in siblings if other.object_order > index}
        changes.update({other.id: replace(other, object_order=other.object_order + 1)
                        for other in menu_children(model, parent.id) if other.object_order >= new_order})
        changes[key] = replace(node, parent_id=parent.id, object_order=new_order)
        result = model.with_nodes(changes)
    registry.validate(result)
    return result


def rename_menu(model, key, name, code):
    require_unlocked(model, key)
    require(bool(name.strip()), "菜单名称不能为空。")
    require(code.isascii() and code.isidentifier() and not keyword.iskeyword(code), "代码名称必须是有效英文标识符。")
    require(all(node.id == key or node.name != name.strip() for node in model.nodes.values()), "菜单名称不能与其他对象重复。")
    require(all(node.id == key or node.code_name != code for node in model.nodes.values()), "代码名称不能与其他对象重复。")
    return model.with_nodes({key: replace(model.nodes[key], name=name.strip(), code_name=code)})


def remove_menu(model, key):
    return delete_node(model, key)


def validate_menus(model):
    items = [node for node in model.nodes.values() if node.type_id == "builtin.menu_item"]
    require(len(items) <= 200, "每个窗口最多允许二百个菜单项。")
    shortcuts = set()
    for node in items:
        parent = model.nodes[node.parent_id]
        require(parent.type_id in {"builtin.menu_bar", "builtin.menu_item"}, "菜单项必须属于菜单栏或另一个菜单项。")
        require(sum(model.nodes[key].slot == "menu" for key in ancestors(model, node.id)) < 8, "菜单层级不能超过八层。")
        props = node.properties
        separator = props.get("separator", False)
        require(bool(props.get("text", "新菜单").strip()) or separator, "菜单标题不能为空。")
        children = menu_children(model, node.id)
        require(not separator or (parent.slot != "menu_bar" and not children), "分隔线不能位于顶层或包含子菜单。")
        require(not props.get("checked", False) or props.get("checkable", False), "选中菜单必须开启可选中。")
        require(not separator or not (props.get("checkable", False) or props.get("shortcut", "")), "分隔线不能设置选中或快捷键。")
        shortcut = normalize_shortcut(props.get("shortcut", ""))
        require(not children or not shortcut, "包含子菜单的菜单项不能设置快捷键。")
        if shortcut:
            require(shortcut.casefold() not in shortcuts, "菜单快捷键重复，请为每个菜单项设置不同快捷键。")
            shortcuts.add(shortcut.casefold())
        require(not separator or not any(item["source_id"] == node.id and item.get("enabled", True)
                                        for item in model.data["connections"]), "分隔线不能连接事件。")
