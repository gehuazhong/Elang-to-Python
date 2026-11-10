"""事件勾选沿用项目连接与处理函数声明，关闭连接时保留业务入口身份。"""

from __future__ import annotations

from dataclasses import replace
import keyword
from typing import Any
from uuid import uuid4

from .errors import require
from .metadata import EventSpec
from .models import FrozenMap, ProjectModel, thaw
from .registry import WidgetRegistry


SLOTS = {"set_text": "setText", "set_enabled": "setEnabled", "set_visible": "setVisible",
         "set_checked": "setChecked", "set_value": "setValue", "set_window_title": "setWindowTitle",
         "show": "show", "hide": "hide", "close": "close", "start": "start", "stop": "stop"}


def event_spec(model: ProjectModel, registry: WidgetRegistry, node_id: str, key: str) -> EventSpec:
    require(node_id in model.nodes, "事件所属组件已不存在。")
    spec = registry.require(model.nodes[node_id].type_id)
    event = next((event for event in spec.events if event.key == key), None)
    require(event is not None, f"“{spec.label}”没有所选事件。")
    return event


def event_enabled(model: ProjectModel, node_id: str, key: str) -> bool:
    return any(connection["source_id"] == node_id and connection.get("event") == key
               and connection.get("enabled", True) for connection in model.data["connections"])


def set_event_enabled(model: ProjectModel, registry: WidgetRegistry, node_id: str, key: str, enabled: bool) -> ProjectModel:
    require(type(enabled) is bool, "事件连接状态必须为勾选或未勾选。")
    event = event_spec(model, registry, node_id, key)
    connections = model.data["connections"]
    existing = [item for item in connections if item["source_id"] == node_id and item.get("event") == key]
    if existing:
        return replace(model, data=model.data.changed(connections=tuple(
            item.changed(enabled=enabled) if item in existing else item for item in connections)))
    if not enabled:
        return model
    node = model.nodes[node_id]
    used = {item.get("code_name", "").casefold() for item in model.data["handlers"]}
    base = f"on_{node.code_name[:100]}_{key}"[:170]
    name, number = base, 2
    while name.casefold() in used:
        name = f"{base}_{number}"
        number += 1
    handler = FrozenMap({"id": str(uuid4()), "name": node.name + event.label, "code_name": name,
                         "parameters": [], "description": f"处理“{node.name}”的“{event.label}”事件。"})
    connection = FrozenMap({"id": str(uuid4()), "source_id": node_id, "event": key,
                            "target": {"kind": "handler", "handler_id": handler["id"]}, "enabled": True})
    return replace(model, data=model.data.changed(connections=(*connections, connection),
                                                   handlers=(*model.data["handlers"], handler)))


def handler_names(model: ProjectModel) -> dict[str, str]:
    result: dict[str, str] = {}
    used: set[str] = set()
    for handler in model.data["handlers"]:
        name = handler.get("code_name")
        require(isinstance(name, str) and name.isascii() and name.isidentifier() and not keyword.iskeyword(name)
                and not name.startswith("_") and len(name) <= 180 and name.casefold() not in used
                and name.upper() not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                                        *(f"LPT{i}" for i in range(1, 10))},
                "事件处理函数名称无效或重复。")
        require(set(handler) <= {"id", "name", "code_name", "parameters", "description"},
                "事件处理函数包含尚未支持的扩展。")
        used.add(name.casefold())
        result[handler["id"]] = name
    return result


def event_bindings(model: ProjectModel, registry: WidgetRegistry) -> tuple[dict[str, Any], ...]:
    handlers = handler_names(model)
    result: list[dict[str, Any]] = []
    for connection in model.data["connections"]:
        require(type(connection.get("enabled", True)) is bool, "事件连接开关格式无效。")
        if not connection.get("enabled", True):
            continue
        require(set(connection) <= {"id", "source_id", "event", "target", "arguments", "enabled"},
                "事件连接包含尚未支持的扩展。")
        key = connection.get("event")
        event = event_spec(model, registry, connection["source_id"], key)
        node = model.nodes[connection["source_id"]]
        target = connection["target"]
        binding = {"id": connection["id"], "control": node.code_name, "name": node.name,
                   "key": event.key, "label": event.label, "signal": event.qt_signal, "event": event.qt_event}
        if target["kind"] == "handler":
            require(set(target) <= {"kind", "handler_id"} and target["handler_id"] in handlers, "事件处理函数引用无效。")
            binding["handler"] = handlers[target["handler_id"]]
        else:
            slot = target.get("slot")
            require(target["kind"] == "slot" and set(target) <= {"kind", "node_id", "slot"} and isinstance(slot, str) and slot in SLOTS,
                    "事件目标槽尚未支持，请取消该事件勾选后导出。")
            binding["target"] = model.nodes[target["node_id"]].code_name
            binding["slot"] = SLOTS[slot]
        arguments = connection.get("arguments")
        require(arguments is None or isinstance(arguments, tuple), "事件参数必须为数组。")
        if arguments is not None:
            for argument in arguments:
                require(isinstance(argument, FrozenMap), "事件参数格式无效。")
                if argument.get("kind") == "event_arg":
                    require(set(argument) <= {"kind", "index"} and type(argument.get("index")) is int
                            and 0 <= argument["index"] < 32, "事件参数序号无效。")
                else:
                    require(argument.get("kind") == "constant" and set(argument) <= {"kind", "value", "value_type"}
                            and (argument.get("value") is None or type(argument["value"]) in {str, int, float, bool}),
                            "事件常量参数类型尚未支持。")
        binding["arguments"] = thaw(arguments)
        result.append(binding)
    return tuple(result)
