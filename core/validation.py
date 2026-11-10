"""在提交前验证结构和引用；注册层另外校验具体属性。"""

from __future__ import annotations

import keyword
from collections import defaultdict
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from .errors import DesignerError, require
from .models import ProjectModel, Rect


def identifier(value: Any, title: str) -> None:
    require(isinstance(value, str), f"{title}缺少有效标识符。")
    try:
        UUID(value)
    except (ValueError, AttributeError) as exc:
        raise DesignerError(f"{title}的标识符格式无效。") from exc


def index(value: Any, title: str) -> int:
    require(type(value) is int and value >= 0, f"{title}必须为非负整数。")
    return value


def records(value: Any, title: str) -> dict[str, Mapping[str, Any]]:
    require(isinstance(value, tuple), f"{title}必须为数组。")
    result: dict[str, Mapping[str, Any]] = {}
    for item in value:
        require(isinstance(item, Mapping), f"{title}内容必须为对象。")
        key = item.get("id")
        identifier(key, title)
        require(key not in result, f"{title}存在重复标识符。")
        result[key] = item
    return result


def validate_project(model: ProjectModel) -> None:
    data, nodes = model.data, model.nodes
    require(data.get("format") == "uipro" and type(data.get("schema_version")) is int
            and data["schema_version"] == 2, "项目格式或版本不受支持。")
    identifier(data.get("document_id"), "项目")
    require(isinstance(data.get("name"), str) and bool(data["name"].strip()), "项目名称不能为空。")
    require(isinstance(data.get("root_id"), str) and data["root_id"] in nodes, "根窗口不存在。")
    root = nodes[model.root_id]
    require(root.parent_id is None and root.slot == "root" and root.type_id == "builtin.main_window",
            "根节点必须是主窗口。")
    central = [node for node in nodes.values() if node.slot == "central"]
    require(len(central) == 1 and central[0].parent_id == root.id
            and central[0].type_id == "builtin.central_widget", "主窗口必须有且只有一个工作区。")
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    grids: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    names: set[str] = set()
    codes: set[str] = set()
    for node in nodes.values():
        identifier(node.id, "控件")
        require(isinstance(node.type_id, str) and bool(node.type_id), "控件类型不能为空。")
        require(type(node.type_version) is int and node.type_version >= 1, "控件类型版本无效。")
        require(isinstance(node.name, str) and bool(node.name.strip()) and node.name not in names,
                "控件名称不能为空或重复。")
        require(isinstance(node.code_name, str) and node.code_name.isascii()
                and node.code_name.isidentifier() and not keyword.iskeyword(node.code_name)
                and node.code_name not in codes, "代码名称无效或重复。")
        names.add(node.name)
        codes.add(node.code_name)
        require(node.slot in {"root", "central", "children", "pages", "non_visual", "tool_bar", "menu_bar", "status_bar", "menu", "action", "dock"},
                "控件挂接位置无效。")
        require(node is root or (isinstance(node.parent_id, str) and node.parent_id in nodes), "控件父级不存在。")
        require(node is root or node.slot != "root", "项目不能有多个根窗口。")
        seen = {node.id}
        parent_id = node.parent_id
        while parent_id is not None:
            require(isinstance(parent_id, str) and parent_id in nodes, "祖先节点不存在。")
            require(parent_id not in seen, "控件层级不能形成循环。")
            seen.add(parent_id)
            parent_id = nodes[parent_id].parent_id
        groups[("object", node.parent_id, node.slot)].append(index(node.object_order, "对象顺序"))
        require(all(type(node.designer.get(key)) is bool for key in ("locked", "hidden")), "设计状态必须为布尔值。")
        if node.geometry:
            Rect.from_dict(node.geometry.to_dict())
        require((node.geometry is not None) == (node.slot in {"root", "children"}), "控件几何与可视类型不一致。")
        if node.slot == "children":
            groups[("stack", node.parent_id)].append(index(node.stack_order, "层叠顺序"))
            require(nodes[node.parent_id].type_id not in {
                "builtin.main_window", "builtin.button", "builtin.label", "builtin.line_edit", "builtin.timer",
                "builtin.text_edit", "builtin.combo_box", "builtin.check_box", "builtin.radio_button", "builtin.spin_box",
                "builtin.progress_bar", "builtin.slider", "builtin.list_widget", "builtin.table_widget", "builtin.tree_widget",
                "builtin.double_spin_box", "builtin.date_edit", "builtin.time_edit", "builtin.datetime_edit", "builtin.calendar",
                "builtin.tool_button", "builtin.command_link_button", "builtin.dial", "builtin.scroll_bar", "builtin.lcd_number"},
                    "目标控件不能容纳子控件。")
        else:
            require(node.stack_order is None, "结构及非可视节点没有层叠顺序。")
        if node.layout is not None:
            require(node.layout.get("kind") in {"absolute", "horizontal", "vertical", "grid"}, "布局类型无效。")
            margins = node.layout.get("margins")
            require(isinstance(margins, tuple) and len(margins) == 4
                    and all(type(value) is int and value >= 0 for value in margins), "布局边距无效。")
            index(node.layout.get("spacing"), "布局间距")
        parent_layout = (nodes[node.parent_id].layout or {}) if node.parent_id else {}
        managed = node.slot == "children" and parent_layout.get("kind", "absolute") != "absolute"
        if managed:
            require(node.layout_item is not None, "布局中的控件缺少布局项。")
            item = node.layout_item
            groups[("layout", node.parent_id)].append(index(item.get("index"), "布局顺序"))
            if parent_layout["kind"] == "grid":
                row, col = index(item.get("row"), "布局行号"), index(item.get("column"), "布局列号")
                rows, cols = index(item.get("row_span"), "行跨度"), index(item.get("column_span"), "列跨度")
                require(rows > 0 and cols > 0, "网格跨度必须为正。")
                require(all(not (row < old_row + old_rows and old_row < row + rows
                                 and col < old_col + old_cols and old_col < col + cols)
                            for old_row, old_col, old_rows, old_cols in grids[node.parent_id]), "网格布局项不能重叠。")
                grids[node.parent_id].append((row, col, rows, cols))
        else:
            require(node.layout_item is None, "自由定位控件不能携带活动布局项。")
    for values in groups.values():
        require(sorted(values) == list(range(len(values))), "各自作用域的顺序必须唯一且连续。")
    handlers = records(data.get("handlers"), "处理函数")
    resources = records(data.get("resources"), "资源")
    for resource in resources.values():
        require(isinstance(resource.get("path"), str) and isinstance(resource.get("sha256"), str), "资源路径或摘要无效。")
    for connection in records(data.get("connections"), "事件连接").values():
        source = connection.get("source_id")
        require(isinstance(source, str) and source in nodes, "事件源不存在。")
        target = connection.get("target")
        require(isinstance(target, Mapping), "事件目标无效。")
        if target.get("kind") == "handler":
            require(isinstance(target.get("handler_id"), str) and target["handler_id"] in handlers, "处理函数不存在。")
        else:
            require(target.get("kind") == "slot" and isinstance(target.get("node_id"), str)
                    and target["node_id"] in nodes, "事件目标控件不存在。")
    tabs = data.get("tab_order")
    require(isinstance(tabs, tuple) and all(isinstance(key, str) and key in nodes for key in tabs)
            and len(set(tabs)) == len(tabs), "焦点顺序包含重复或无效控件。")
    canvas = data.get("canvas")
    require(isinstance(canvas, Mapping) and type(canvas.get("grid_size")) is int
            and 2 <= canvas["grid_size"] <= 128, "网格大小必须在 2 到 128 之间。")
    for key in ("show_grid", "snap_to_grid", "show_guides", "snap_to_guides"):
        require(type(canvas.get(key)) is bool, "画布开关必须为布尔值。")
    require(isinstance(data.get("codegen"), Mapping) and isinstance(data.get("extensions"), Mapping),
            "生成设置和扩展字段必须为对象。")
