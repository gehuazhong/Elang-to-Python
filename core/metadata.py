"""中文属性定义和稳定值转换，不执行项目提供的类名或表达式。"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .errors import require
from .models import FrozenMap, freeze
from .content_values import normalize_content
from .value_types import normalize_number, normalize_temporal
from .image_values import normalize_image


@dataclass(frozen=True, slots=True)
class PropertySpec:
    key: str
    label: str
    group: str
    value_type: str
    default: Any
    qt_name: str | None = None
    options: tuple[tuple[str, str], ...] = ()
    read_only: bool = False
    minimum: int | float = 0
    maximum: int | float = 16384
    description: str = ""

    def __post_init__(self) -> None:
        # 集合默认值也必须递归冻结，避免注册表冻结后被外部原地修改。
        object.__setattr__(self, "default", freeze(self.default))

    def normalize(self, value: Any) -> Any:
        if self.value_type == "shortcut":
            from .menu_values import normalize_shortcut, normalize_key_sequence
            return normalize_key_sequence(value) if self.key == "key_sequence" else normalize_shortcut(value)
        if self.value_type == "image":
            return normalize_image(value)
        if self.value_type in {"string", "multiline"}:
            require(isinstance(value, str) and len(value) <= 100_000, f"{self.label}必须是长度合理的文本。")
            if self.value_type == "multiline":
                return value.replace("\r\n", "\n").replace("\r", "\n").replace("\u2028", "\n").replace("\u2029", "\n")
        elif self.value_type in {"string_list", "table", "tree"}:
            return normalize_content(self.value_type, value, self.label)
        elif self.value_type == "bool":
            require(type(value) is bool, f"{self.label}必须为布尔值。")
        elif self.value_type == "enum":
            require(isinstance(value, str) and value in dict(self.options), f"{self.label}的选项无效。")
        elif self.value_type == "int":
            require(type(value) is int and self.minimum <= value <= self.maximum,
                    f"{self.label}必须是 {self.minimum} 到 {self.maximum} 之间的整数。")
        elif self.value_type == "float":
            return normalize_number(value, self.minimum, self.maximum, self.label)
        elif self.value_type in {"date", "time", "datetime"}:
            return normalize_temporal(self.value_type, value, self.label)
        elif self.value_type == "color":
            require(isinstance(value, str) and (value == "" or re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None),
                    f"{self.label}请使用六位十六进制颜色，或留空使用默认颜色。")
            return value.lower()
        else:
            require(False, f"属性“{self.label}”尚无可用的转换器。")
        return value


@dataclass(frozen=True, slots=True)
class EventSpec:
    key: str
    label: str
    qt_signal: str = ""
    qt_event: str = ""
    description: str = ""


@dataclass(frozen=True, slots=True)
class WidgetSpec:
    type_id: str
    label: str
    group: str
    qt_class: str
    version: int
    slot: str
    default_size: tuple[int, int]
    code_prefix: str
    properties: tuple[PropertySpec, ...]
    toolbox: bool = True
    text_from_name: bool = False
    can_contain: bool = False
    events: tuple[EventSpec, ...] = ()
    aliases: tuple[str, ...] = ()
    _defaults: FrozenMap = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("properties", "events", "aliases", "default_size"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "_defaults", FrozenMap({item.key: item.default for item in self.properties}))

    def property(self, key: str) -> PropertySpec:
        result = next((item for item in self.properties if item.key == key), None)
        require(result is not None, "该组件没有所选属性。")
        return result

    def defaults(self) -> FrozenMap:
        return self._defaults
