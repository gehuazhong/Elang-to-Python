"""日期时间和定点小数的规范值，不依赖 Qt 或本机时区。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
import re
from typing import Any

from .errors import require


TEMPORAL_FORMATS = {"date": (r"[0-9]{4}-[0-9]{2}-[0-9]{2}", "%Y-%m-%d"),
                    "time": (r"[0-9]{2}:[0-9]{2}:[0-9]{2}", "%H:%M:%S"),
                    "datetime": (r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", "%Y-%m-%dT%H:%M:%S")}


def normalize_temporal(kind: str, value: Any, label: str) -> str:
    pattern, fmt = TEMPORAL_FORMATS[kind]
    require(isinstance(value, str) and re.fullmatch(pattern, value) is not None, f"{label}的日期时间格式无效。")
    try:
        parsed = datetime.strptime(value, fmt)
    except ValueError:
        require(False, f"{label}包含不存在的日期或时间。")
    require(kind == "time" or 1752 <= parsed.year <= 9999, f"{label}的年份必须在 1752 至 9999 之间。")
    return value


def quantize_number(value: int | float, decimals: int) -> float:
    try:
        return float(Decimal(str(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError):
        require(False, "小数值无法按指定精度表示。")


def normalize_number(value: Any, minimum: int | float, maximum: int | float, label: str) -> float:
    require(type(value) in (int, float) and minimum <= value <= maximum and math.isfinite(value),
            f"{label}必须是 {minimum} 至 {maximum} 之间的有限数值。")
    return float(value)
