"""不依赖 Qt 的不可变项目模型；未知字段在往返时原样保留。"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from .errors import DesignerError, require


class FrozenMap(Mapping[str, Any]):
    """递归冻结 JSON 对象，避免界面绕过命令修改快照。"""

    __slots__ = ("_data",)

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        self._data = MappingProxyType({key: freeze(value) for key, value in (values or {}).items()})
        require(all(isinstance(key, str) for key in self._data), "数据字段名称必须是字符串。")

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def changed(self, **values: Any) -> FrozenMap:
        return FrozenMap({**self, **values})


def freeze(value: Any) -> Any:
    if isinstance(value, FrozenMap):
        return value
    if isinstance(value, Mapping):
        return FrozenMap(value)
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise DesignerError("项目包含不能保存的值或非有限数字。")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Rect:
        require(isinstance(value, Mapping) and set(value) == {"x", "y", "width", "height"},
                "位置和尺寸字段不完整。")
        require(all(type(item) is int for item in value.values()), "位置和尺寸必须为整数。")
        require(0 < value["width"] <= 16384 and 0 < value["height"] <= 16384,
                "宽度和高度必须在 1 到 16384 之间。")
        require(abs(value["x"]) <= 1_000_000 and abs(value["y"]) <= 1_000_000,
                "控件位置超出允许范围。")
        return cls(**value)

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


@dataclass(frozen=True, slots=True)
class WidgetNode:
    id: str
    type_id: str
    type_version: int
    name: str
    code_name: str
    parent_id: str | None
    slot: str
    object_order: int
    stack_order: int | None
    geometry: Rect | None
    properties: FrozenMap
    designer: FrozenMap
    layout: FrozenMap | None
    layout_item: FrozenMap | None
    extensions: FrozenMap
    extra: FrozenMap

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WidgetNode:
        require(isinstance(value, Mapping), "控件节点必须是对象。")
        required = set(cls.__dataclass_fields__) - {"extra"}
        require(required <= value.keys(), "控件节点缺少必要字段。")
        require("order" not in value, "第二版项目不能使用旧的混合顺序字段。")
        kwargs = {key: value[key] for key in required}
        labels = {"properties": "属性", "designer": "设计状态", "extensions": "扩展"}
        for key in ("properties", "designer", "extensions"):
            require(isinstance(kwargs[key], Mapping), f"控件的{labels[key]}数据格式无效。")
            kwargs[key] = FrozenMap(kwargs[key])
        for key in ("layout", "layout_item"):
            require(kwargs[key] is None or isinstance(kwargs[key], Mapping), "控件布局格式无效。")
            kwargs[key] = FrozenMap(kwargs[key]) if kwargs[key] is not None else None
        kwargs["geometry"] = Rect.from_dict(kwargs["geometry"]) if kwargs["geometry"] is not None else None
        kwargs["extra"] = FrozenMap({key: item for key, item in value.items() if key not in required})
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        result = thaw(self.extra)
        for key in self.__dataclass_fields__:
            if key != "extra":
                result[key] = thaw(getattr(self, key))
        result["geometry"] = self.geometry.to_dict() if self.geometry else None
        return result


@dataclass(frozen=True, slots=True)
class ProjectModel:
    nodes: Mapping[str, WidgetNode]
    data: FrozenMap

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", MappingProxyType(dict(self.nodes)))

    @property
    def root_id(self) -> str:
        return self.data["root_id"]

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def central_id(self) -> str:
        return next(node.id for node in self.nodes.values() if node.slot == "central")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ProjectModel:
        require(isinstance(value, Mapping), "项目顶层必须是对象。")
        require(isinstance(value.get("nodes"), list), "项目缺少控件数组。")
        nodes: dict[str, WidgetNode] = {}
        for item in value["nodes"]:
            node = WidgetNode.from_dict(item)
            require(isinstance(node.id, str) and node.id not in nodes, "控件标识符无效或重复。")
            nodes[node.id] = node
        return cls(nodes, FrozenMap({key: item for key, item in value.items() if key != "nodes"}))

    def to_dict(self) -> dict[str, Any]:
        return {**thaw(self.data), "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)]}

    def to_bytes(self) -> bytes:
        return (json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True,
                           allow_nan=False) + "\n").encode("utf-8")

    def with_nodes(self, changes: Mapping[str, WidgetNode | None]) -> ProjectModel:
        nodes = dict(self.nodes)
        for identifier, node in changes.items():
            if node is None:
                nodes.pop(identifier, None)
            else:
                nodes[identifier] = node
        return replace(self, nodes=nodes)


def new_node(type_id: str, name: str, code_name: str, parent_id: str | None,
             slot: str, order: int, geometry: Rect | None,
             properties: Mapping[str, Any] | None = None) -> WidgetNode:
    return WidgetNode(str(uuid4()), type_id, 1, name, code_name, parent_id, slot, order,
                      order if slot == "children" else None, geometry,
                      FrozenMap(properties), FrozenMap({"locked": False, "hidden": False}),
                      None, None, FrozenMap(), FrozenMap())


def new_project(name: str = "未命名窗口") -> ProjectModel:
    root = new_node("builtin.main_window", "主窗口", "main_window", None, "root", 0,
                    Rect(100, 100, 800, 560), {"window_title": name, "enabled": True, "visible": True})
    central = new_node("builtin.central_widget", "工作区", "central_widget", root.id, "central", 0,
                       None, {"enabled": True, "visible": True})
    central = replace(central, layout=FrozenMap({"kind": "absolute", "margins": [0, 0, 0, 0], "spacing": 8}))
    return ProjectModel({root.id: root, central.id: central}, FrozenMap({
        "format": "uipro", "schema_version": 2, "document_id": str(uuid4()), "name": name,
        "root_id": root.id, "connections": [], "handlers": [], "resources": [], "tab_order": [],
        "canvas": {"grid_size": 8, "show_grid": True, "snap_to_grid": True,
                   "show_guides": True, "snap_to_guides": True, "snap_distance": 6},
        "codegen": {"template_id": "builtin.pyside6", "window_class": "MainWindow", "entry_file": "main.py"},
        "extensions": {},
    }))
