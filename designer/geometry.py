"""缩放手势的纯几何计算，不依赖画布和 Qt 对象。"""

from __future__ import annotations

import math

from core.models import Rect


def resized_rect(original: Rect, handle: str, dx: float, dy: float, *, step: int,
                 bounds: tuple[int, int], root: bool = False) -> Rect:
    def snap(value: float) -> int:
        return math.floor(value / step + 0.5) * step

    if root:
        width = max(1, min(16384, snap(original.width + dx))) if "e" in handle and dx else original.width
        height = max(1, min(16384, snap(original.height + dy))) if "s" in handle and dy else original.height
        return Rect(original.x, original.y, width, height)
    left, top = original.x, original.y
    right, bottom = left + original.width, top + original.height
    if "w" in handle and dx:
        left = max(min(0, right - 1), right - 16384, min(right - 1, snap(left + dx)))
    elif "e" in handle and dx:
        right = max(left + 1, min(max(left + 1, bounds[0]), left + 16384, snap(right + dx)))
    if "n" in handle and dy:
        top = max(min(0, bottom - 1), bottom - 16384, min(bottom - 1, snap(top + dy)))
    elif "s" in handle and dy:
        bottom = max(top + 1, min(max(top + 1, bounds[1]), top + 16384, snap(bottom + dy)))
    return Rect(left, top, right - left, bottom - top)
