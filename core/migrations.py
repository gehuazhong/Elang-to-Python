"""只在副本上迁移旧格式，原文件保持不变。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import DesignerError, require


def migrate(value: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(value, dict), "项目顶层必须是对象。")
    version = value.get("schema_version")
    require(type(version) is int and version in (1, 2), "项目版本不受支持，请使用兼容版本打开。")
    result = deepcopy(value)
    if version == 2:
        return result
    try:
        nodes = {node["id"]: node for node in result["nodes"]}
        require(len(nodes) == len(result["nodes"]), "旧项目存在重复节点。")
        for node in nodes.values():
            previous = node.pop("order")
            require(type(previous) is int and previous >= 0, "旧版控件顺序无效。")
            node["object_order"] = previous
            node["stack_order"] = previous if node["slot"] == "children" else None
            parent = nodes.get(node["parent_id"])
            layout = (parent.get("layout") or {}) if parent else {}
            if node["slot"] == "children" and layout.get("kind", "absolute") != "absolute":
                node["layout_item"] = {**(node.get("layout_item") or {}), "index": previous}
    except (KeyError, TypeError, AttributeError) as exc:
        raise DesignerError("旧项目结构不完整，无法迁移。") from exc
    result["schema_version"] = 2
    return result
