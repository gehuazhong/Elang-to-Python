"""选择夹页面的增删和切换全部进入文档历史。"""

from __future__ import annotations

from dataclasses import replace

from core.errors import require
from core.hierarchy import pages, require_unlocked
from core.models import ProjectModel, new_node
from core.registry import WidgetRegistry
from layout.containers import PAGE_TYPES


def add_page(model: ProjectModel, registry: WidgetRegistry, tab_id: str) -> tuple[ProjectModel, str]:
    require(tab_id in model.nodes and model.nodes[tab_id].type_id in PAGE_TYPES, "请选择一个页面容器。")
    require_unlocked(model, tab_id)
    siblings = pages(model, tab_id)
    require(len(siblings) < 50, "选择夹最多允许五十页。")
    number = 1
    names = {node.name for node in model.nodes.values()}
    codes = {node.code_name for node in model.nodes.values()}
    while f"页面{number}" in names or f"tab_page_{number}" in codes:
        number += 1
    kind = "builtin.wizard_page" if model.nodes[tab_id].type_id == "builtin.wizard" else "builtin.tab_page"
    values = registry.require(kind).defaults().changed(**{
        "title" if kind == "builtin.wizard_page" else "text": f"第{len(siblings) + 1}页"})
    node = new_node(kind, f"页面{number}", f"tab_page_{number}", tab_id, "pages", len(siblings), None, values)
    return model.with_nodes({node.id: node}), node.id


def select_page(model: ProjectModel, registry: WidgetRegistry, tab_id: str, index: int) -> ProjectModel:
    from .nodes import set_property
    return set_property(model, registry, tab_id, "current_index", index)
