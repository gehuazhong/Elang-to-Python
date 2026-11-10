"""由不可变文档生成确定性的构建计划，可在未创建窗口时编译。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errors import require
from .models import FrozenMap, ProjectModel, Rect
from .registry import WidgetRegistry
from .validation import validate_project


@dataclass(frozen=True, slots=True)
class NodePlan:
    id: str
    type_id: str
    parent_id: str | None
    slot: str
    name: str
    geometry: Rect | None
    stack_order: int | None
    properties: FrozenMap
    designer_hidden: bool
    unknown: bool
    code_name: str = ""


@dataclass(frozen=True, slots=True)
class BuildPlan:
    version: int
    state_id: str
    registry_fingerprint: str
    nodes: tuple[NodePlan, ...]
    tab_order: tuple[str, ...]
    diagnostics: tuple[str, ...]


def preview_window_resize(plan: BuildPlan, geometry: Rect) -> BuildPlan:
    """只改变已验证计划的窗口几何；属性语义和顺序直接沿用原计划。"""
    from .window_scaling import scale_base_size, scale_items
    from layout.scaling import scale_layout

    require(bool(plan.nodes) and plan.nodes[0].slot == "root", "窗口缩放预览缺少根节点。")
    root = plan.nodes[0]
    geometry = Rect.from_dict(geometry.to_dict())
    require(root.geometry is not None and (geometry.x, geometry.y) == (root.geometry.x, root.geometry.y),
            "窗口缩放预览不能修改屏幕位置。")
    bars = sum(node.properties.get("bar_height", 36 if node.slot == "tool_bar" else 28)
               for node in plan.nodes if node.slot in {"menu_bar", "tool_bar", "status_bar"} and node.properties.get("visible", True))
    require(bars < geometry.height, "菜单栏、工具条和状态条不能占满窗口高度。")
    target = (replace(root, geometry=geometry), *plan.nodes[1:])
    if root.properties.get("scale_children", False):
        rectangles = scale_layout(scale_items(plan.nodes), scale_base_size(plan.nodes), scale_base_size(target))
        target = tuple(replace(node, geometry=Rect(*rectangles[node.id]))
                       if node.slot == "children" and node.id in rectangles else node for node in target)
    return replace(plan, nodes=target)


def compile_plan(model: ProjectModel, registry: WidgetRegistry, state_id: str,
                 *, allow_unknown: bool = False) -> BuildPlan:
    validate_project(model)
    registry.validate(model)
    require(bool(registry.fingerprint), "控件注册表尚未冻结。")
    children: dict[str | None, list[str]] = {}
    for node in model.nodes.values():
        require(node.layout is None or node.layout["kind"] == "absolute",
                "本阶段尚不支持编辑自动布局项目，原文件保持不变。")
        children.setdefault(node.parent_id, []).append(node.id)
    ordered: list[str] = []
    pending = [model.root_id]
    while pending:
        key = pending.pop()
        ordered.append(key)
        pending.extend(reversed(sorted(children.get(key, []), key=lambda child: (
            model.nodes[child].slot, model.nodes[child].object_order, child))))
    plans: list[NodePlan] = []
    diagnostics: list[str] = []
    for key in ordered:
        node = model.nodes[key]
        spec = registry.get(node.type_id)
        unknown = spec is None or node.type_version != spec.version
        require(allow_unknown or not unknown, f"“{node.name}”缺少兼容的构建适配器。")
        values = spec.defaults().changed(**node.properties) if not unknown else node.properties
        if not unknown:
            values = FrozenMap({prop.key: prop.normalize(values[prop.key]) for prop in spec.properties})
        else:
            diagnostics.append(f"“{node.name}”暂不支持显示或运行，其原始数据已保留。")
        plans.append(NodePlan(node.id, node.type_id, node.parent_id, node.slot, node.name,
                              node.geometry, node.stack_order, values, node.designer["hidden"], unknown, node.code_name))
    return BuildPlan(1, state_id, registry.fingerprint, tuple(plans), tuple(model.data["tab_order"]),
                     tuple(diagnostics))
