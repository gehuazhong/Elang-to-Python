"""Project-level invariants for layouts, references and native extensions."""

from urllib.parse import urlsplit
from xml.etree import ElementTree
from .errors import require
from layout.containers import grid_cells

BUTTON_TYPES = frozenset("builtin." + key for key in
                         ("button", "tool_button", "command_link_button", "check_box", "radio_button"))
BUTTON_NAMES = frozenset(("确定", "取消", "是", "否", "应用", "关闭", "重试", "帮助"))


def validate_advanced(model, registry):
    codes = {node.code_name: node for node in model.nodes.values()}
    grouped = set()
    for node in model.nodes.values():
        spec = registry.get(node.type_id)
        if spec is None:
            continue
        values = spec.defaults().changed(**node.properties)
        if node.type_id == "builtin.mdi_subwindow":
            require(model.nodes[node.parent_id].type_id == "builtin.mdi_area", "多文档子窗口只能放入多文档区域。")
        if node.type_id == "builtin.mdi_area":
            require(all(child.type_id == "builtin.mdi_subwindow" for child in model.nodes.values()
                        if child.parent_id == node.id), "多文档区域仅容纳子窗口；请将控件放入子窗口。")
        if node.type_id == "builtin.grid_layout":
            entries = [(child.id, child.properties) for child in sorted(model.nodes.values(), key=lambda n: n.object_order)
                       if child.parent_id == node.id]
            try:
                grid_cells(entries, values["columns"])
            except ValueError as exc:
                require(False, str(exc))
        if node.type_id == "builtin.splitter":
            require(all(text.isascii() and text.isdigit() and 0 < int(text) <= 16384 for text in values["sizes"]),
                    "分区尺寸必须为一至一万六千三百八十四的整数。")
            count = sum(child.parent_id == node.id for child in model.nodes.values())
            require(not values["sizes"] or len(values["sizes"]) == count, "分区尺寸数量必须与子控件数量一致。")
        if node.type_id in {"builtin.message_box", "builtin.dialog_button_box"}:
            require(bool(values["buttons"]) and len(set(values["buttons"])) == len(values["buttons"])
                    and set(values["buttons"]) <= BUTTON_NAMES, "按钮名称无效、重复或为空。")
            if node.type_id == "builtin.message_box":
                require(values.get("default_button", "auto") == "auto" or values["default_button"] in values["buttons"],
                        "默认按钮必须包含在对话框按钮列表中。")
        if node.type_id == "builtin.button_group":
            members = values["members"]
            require(len(set(members)) == len(members), "按钮组成员不能重复。")
            require(all(name in codes and codes[name].type_id in BUTTON_TYPES for name in members), "按钮组成员必须是已存在的按钮。")
            require(not grouped.intersection(members), "一个按钮只能属于一个显式按钮组。")
            grouped.update(members)
            require(not values["exclusive"] or sum(codes[name].properties.get("checked", False)
                    or codes[name].properties.get("check_state") == "checked" for name in members) <= 1,
                    "互斥按钮组只能选中一个成员。")
        if node.type_id in {"builtin.rhi_widget", "builtin.opengl_widget"}:
            require(values["samples"] in {1, 2, 4, 8}, "采样数只支持一、二、四或八。")
        if node.type_id == "builtin.svg_widget":
            data = values["svg_data"]
            require("<!DOCTYPE" not in data.upper() and "<!ENTITY" not in data.upper(), "SVG 不支持文档类型或实体声明。")
            try:
                root = ElementTree.fromstring(data)
                require(root.tag in {"svg", "{http://www.w3.org/2000/svg}svg"}, "SVG 内容必须以 svg 元素为根。")
            except ElementTree.ParseError:
                require(False, "SVG 内容不是有效的 XML。")
        if node.type_id == "builtin.web_view" and values["source_mode"] == "url":
            try:
                url = urlsplit(values["url"])
                require(url.scheme in {"http", "https", "file", "about"}
                        and (bool(url.netloc) if url.scheme in {"http", "https"} else bool(url.path)), "请输入有效的网页地址。")
            except ValueError:
                require(False, "请输入有效的网页地址。")
        if node.type_id == "builtin.input_dialog" and values["input_mode"] == "integer":
            require(all(float(values[key]).is_integer() for key in ("minimum", "maximum", "value")), "整数输入模式的范围和值必须为整数。")
        if node.type_id == "builtin.input_dialog":
            require(not (values.get("multiline") and values.get("input_items")), "多行文本输入不能同时使用候选列表。")
