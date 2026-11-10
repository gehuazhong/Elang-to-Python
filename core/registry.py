"""按会话固定的控件注册表。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields
from types import MappingProxyType

from .errors import require
from .metadata import WidgetSpec
from .models import ProjectModel, thaw
from .value_types import quantize_number
from .hierarchy import pages, window_bars
from layout.containers import NAVIGATION_PAGE_TYPES, PAGE_TYPES


class WidgetRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, WidgetSpec] = {}
        self._frozen = False
        self.fingerprint = ""

    def register(self, spec: WidgetSpec) -> None:
        require(not self._frozen, "正在使用的控件注册表不能修改。")
        require(spec.type_id not in self._specs, "控件类型重复注册。")
        require(len({item.key for item in spec.properties}) == len(spec.properties), "组件属性重复。")
        require(len({item.key for item in spec.events}) == len(spec.events), "组件事件重复。")
        for item in spec.properties:
            item.normalize(item.default)
        self._specs[spec.type_id] = spec

    def freeze(self) -> WidgetRegistry:
        records = []
        for key in sorted(self._specs):
            spec = self._specs[key]
            record = {field.name: getattr(spec, field.name) for field in fields(spec) if field.name not in {"properties", "events"}}
            record["events"] = [asdict(event) for event in spec.events]
            record["properties"] = [{field.name: thaw(getattr(prop, field.name)) for field in fields(prop)}
                                    for prop in spec.properties]
            records.append(record)
        raw = json.dumps(records,
                         ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.fingerprint = hashlib.sha256(raw).hexdigest()
        self._frozen = True
        return self

    @property
    def specs(self) -> MappingProxyType:
        return MappingProxyType(self._specs)

    def get(self, type_id: str) -> WidgetSpec | None:
        return self._specs.get(type_id)

    def require(self, type_id: str) -> WidgetSpec:
        result = self.get(type_id)
        require(result is not None, "该组件尚未注册。")
        return result

    def validate(self, model: ProjectModel) -> None:
        checked_groups: set[str | None] = set()
        by_code = {node.code_name: node for node in model.nodes.values()}
        explicit_members = {name for group in model.nodes.values() if group.type_id == "builtin.button_group"
                            for name in group.properties.get("members", ())}
        for node in model.nodes.values():
            spec = self.get(node.type_id)
            if spec is None or node.type_version != spec.version:
                continue
            require(node.slot == spec.slot, f"“{node.name}”的挂接位置不正确。")
            if node.slot == "children":
                parent = self.get(model.nodes[node.parent_id].type_id)
                if parent is not None:
                    require(parent.can_contain, "目标控件不能容纳子控件。")
                    require(model.nodes[node.parent_id].type_id not in PAGE_TYPES, "请把控件放入容器的具体页面。")
            if node.slot in {"non_visual", "tool_bar", "status_bar", "menu_bar", "dock"}:
                require(node.parent_id == model.root_id, "此组件必须挂接主窗口。")
            if node.slot in {"tool_bar", "status_bar", "menu_bar"}:
                require(sum(other.slot == node.slot for other in model.nodes.values()) == 1, "每个窗口只能放置一个菜单栏、一个工具条和一个状态条。")
            if node.slot == "pages":
                parent_type = model.nodes[node.parent_id].type_id
                require(parent_type in PAGE_TYPES, "页面只能属于页面容器。")
                require((node.type_id == "builtin.wizard_page") == (parent_type == "builtin.wizard"), "向导必须使用向导页面。")
            for prop in spec.properties:
                if prop.key in node.properties:
                    prop.normalize(node.properties[prop.key])
            if node.type_id in {"builtin.button", "builtin.tool_button", "builtin.command_link_button", "builtin.group_box"}:
                require(not node.properties.get("checked", False) or node.properties.get("checkable", False),
                        "设置已选中时必须开启可选中。")
            if node.type_id == "builtin.line_edit":
                text = node.properties.get("text", spec.property("text").default)
                limit = node.properties.get("max_length", spec.property("max_length").default)
                require(not any(character in text for character in ("\r", "\n", "\u2028", "\u2029")),
                        "单行编辑框的文本不能包含换行。")
                # Qt 按十六位编码单元计算长度，部分字符占两位，须在写入前保持一致。
                length = sum(2 if ord(character) > 0xFFFF else 1 for character in text)
                require(length <= limit, "文本超过最大长度，请先缩短文本或增大最大长度。")
            values = spec.defaults().changed(**node.properties)
            if node.type_id in PAGE_TYPES:
                count = len(pages(model, node.id))
                require(1 <= count <= 50 and 0 <= values["current_index"] < count, "选择夹必须有一至五十页，当前页须位于有效范围。")
                require(node.geometry.width >= 64 and node.geometry.height >= 64, "选择夹宽度和高度至少为六十四。")
            if node.type_id == "builtin.super_list":
                require(bool(values["table_data"]["headers"]), "超级列表框至少需要一列。")
                entries = values["checked_rows"]
                require(len(set(entries)) == len(entries) and all(item.isascii() and item.isdigit()
                        and 1 <= int(item) <= len(values["table_data"]["rows"]) and str(int(item)) == item for item in entries),
                        "已勾选行必须是不重复的有效行号，从一开始，不加前导零。")
            if values.get("trigger_control"):
                target = next((item for item in model.nodes.values() if item.code_name == values["trigger_control"]), None)
                require(target is not None and target.type_id in {"builtin.button", "builtin.tool_button", "builtin.command_link_button"},
                        "触发按钮不存在或类型不支持。")
            if values.get("navigation_page"):
                target = by_code.get(values["navigation_page"])
                require(target is not None and target.slot == "pages"
                        and model.nodes[target.parent_id].type_id in NAVIGATION_PAGE_TYPES,
                        "关联页面不存在，或不属于选择夹、堆叠窗口、工具箱。")
            if "minimum" in values and "maximum" in values and "value" in values:
                require(values["minimum"] <= values["maximum"], "最小值不能大于最大值。")
                require(values["minimum"] <= values["value"] <= values["maximum"], "当前值必须位于最小值和最大值之间。")
            if node.type_id == "builtin.double_spin_box":
                for key in ("minimum", "maximum", "value", "single_step"):
                    require(quantize_number(values[key], values["decimals"]) == values[key],
                            "数值包含超出小数位数的精度，请先增加小数位数。")
            if node.type_id == "builtin.lcd_number":
                mode = {"decimal": "d", "hex": "x", "octal": "o", "binary": "b"}[values.get("number_mode", "decimal")]
                require(len(format(values["value"], mode)) <= values["digit_count"], "显示数值超过显示位数，请先增加位数。")
            if node.type_id == "builtin.key_sequence_edit":
                require(not values["key_sequence"] or len(values["key_sequence"].split(", ")) <= values.get("maximum_sequence_length", 1),
                        "快捷键序列超过最大长度，请先增大序列长度。")
            if spec.can_contain and node.geometry is not None:
                require(values.get("content_left", 0) + values.get("content_right", 0) < node.geometry.width
                        and values.get("content_top", 0) + values.get("content_bottom", 0) < node.geometry.height,
                        "内边距不能占满容器，请增大容器或缩小内边距。")
            if node.type_id in {"builtin.combo_box", "builtin.list_widget", "builtin.tab_bar"}:
                require(-1 <= values["current_index"] < len(values["items"]), "当前选项超出列表范围；负一表示不选择。")
            if node.type_id == "builtin.check_box":
                require(values["tristate"] or values["check_state"] != "partial", "请先开启允许半选，再设置半选状态。")
            if node.type_id == "builtin.radio_button" and node.code_name not in explicit_members and values["auto_exclusive"] and values["checked"]:
                require(node.parent_id not in checked_groups, "同一容器内的互斥单选框只能选中一个。")
                checked_groups.add(node.parent_id)
        from .commands.menus import validate_menus
        from .advanced_validation import validate_advanced
        validate_advanced(model, self)
        validate_menus(model)
        from .menu_values import validate_shortcuts
        validate_shortcuts(model, self)
        top, bottom = window_bars(model)
        require(top + bottom < model.nodes[model.root_id].geometry.height, "菜单栏、工具条和状态条不能占满窗口高度。")
