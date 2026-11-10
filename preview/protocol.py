"""预览通过标准输入输出传递 JSON 消息，不生成项目或代码文件。"""

from __future__ import annotations

import json
from typing import Any

from core.build_plan import BuildPlan, compile_plan
from core.errors import DesignerError, require
from core.events import event_bindings
from core.models import ProjectModel
from core.registry import WidgetRegistry
from widgets.catalog import SUPPORTED_SLOTS


PROTOCOL_VERSION = 1
MAX_REQUEST_BYTES = 32 * 1024 * 1024
MAX_REPLY_BYTES = 64 * 1024


def encode_message(kind: str, request_id: str, **values: Any) -> bytes:
    value = {"version": PROTOCOL_VERSION, "kind": kind, "request_id": request_id, **values}
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def decode_message(data: bytes, *, limit: int) -> dict[str, Any]:
    require(len(data) <= limit, "预览消息超出允许大小。")
    try:
        value = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise DesignerError("预览消息不是有效的 UTF-8 JSON。") from exc
    require(isinstance(value, dict), "预览消息必须是对象。")
    require(type(value.get("version")) is int and value["version"] == PROTOCOL_VERSION,
            "预览通信版本不匹配，请重新启动设计器。")
    require(isinstance(value.get("request_id"), str) and 0 < len(value["request_id"]) <= 100,
            "预览任务标识无效。")
    require(isinstance(value.get("kind"), str), "预览消息类型无效。")
    return value


def preview_plan(model: ProjectModel, registry: WidgetRegistry, state_id: str) -> BuildPlan:
    plan = compile_plan(model, registry, state_id)
    bindings = event_bindings(model, registry)
    if any("slot" in binding for binding in bindings):
        from runtime.builder import verify_event_targets
        verify_event_targets(model, registry, bindings)
    require(all(node.slot in SUPPORTED_SLOTS for node in plan.nodes),
            "项目包含当前预览尚未实现的组件。")
    require(plan.nodes[0].properties.get("visible", True),
            "主窗口的“可见”属性已关闭，请开启后再预览。")
    return plan
