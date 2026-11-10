"""组件箱只传递已注册的类型键，不传可执行对象。"""

from __future__ import annotations

import json

from PySide6.QtCore import QMimeData

from core.errors import DesignerError, require
from core.registry import WidgetRegistry

COMPONENT_MIME = "application/x-uiplay-component+json"


def component_mime(type_id: str) -> QMimeData:
    mime = QMimeData()
    mime.setData(COMPONENT_MIME, json.dumps({"version": 1, "type_id": type_id}).encode("utf-8"))
    return mime


def component_type(mime: QMimeData, registry: WidgetRegistry) -> str:
    require(mime.hasFormat(COMPONENT_MIME), "请从中文组件箱拖入控件。")
    try:
        data = bytes(mime.data(COMPONENT_MIME))
        require(len(data) <= 4096, "组件拖放数据过大。")
        payload = json.loads(data.decode("utf-8"))
        require(isinstance(payload, dict) and type(payload.get("version")) is int
                and payload["version"] == 1 and isinstance(payload.get("type_id"), str), "组件拖放格式不受支持。")
        spec = registry.require(payload["type_id"])
        require(spec.toolbox, "该组件不能直接拖入。")
        return spec.type_id
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DesignerError("组件拖放数据损坏。") from exc
