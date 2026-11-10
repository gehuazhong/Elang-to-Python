"""根据固定基准计算组件几何，避免连续拉伸累积舍入误差。"""

from __future__ import annotations

from dataclasses import dataclass
from .containers import inset_rect

Box = tuple[int, int, int, int]
Size = tuple[int, int]


@dataclass(frozen=True, slots=True)
class ScaleItem:
    key: str
    parent: str | None
    kind: str
    rect: Box | None
    margins: Box = (0, 0, 0, 0)
    minimum: Size = (1, 1)
    page_insets: Box = (1, 30, 1, 1)


def scaled_axis(position: int, length: int, before: int, after: int, minimum: int) -> tuple[int, int]:
    if before <= 0 or after <= 0:
        raise ValueError("组件跟随缩放的内容区尺寸必须大于零。")
    if before == after:
        return position, length
    # 缩放两端，原本相邻的边仍使用相同整数坐标。
    start = (2 * position * after + before) // (2 * before)
    end = (2 * (position + length) * after + before) // (2 * before)
    return max(-1_000_000, min(1_000_000, start)), max(minimum, min(16384, end - start))


def scale_layout(items: tuple[ScaleItem, ...], before: Size, after: Size) -> dict[str, Box]:
    """节点按父级在前排列；页签、容器边距与窗口条高度不按比例改变。"""
    old_sizes: dict[str, Size] = {}
    new_sizes: dict[str, Size] = {}
    old_boxes: dict[str, Box] = {}
    result: dict[str, Box] = {}
    for item in items:
        if item.kind == "central":
            old_sizes[item.key], new_sizes[item.key] = before, after
            continue
        if item.kind == "pages":
            old = old_boxes[item.parent]
            parent = result[item.parent]
            rect = inset_rect(parent[2], parent[3], item.page_insets)
            old_sizes[item.key] = inset_rect(old[2], old[3], item.page_insets)[2:]
            new_sizes[item.key] = rect[2:]
            result[item.key] = rect
            continue
        if item.rect is None or item.parent not in old_sizes:
            raise ValueError("组件跟随缩放缺少父级内容区或组件尺寸。")
        x, y, width, height = item.rect
        left, top, right, bottom = item.margins
        x, width = scaled_axis(x, width, old_sizes[item.parent][0], new_sizes[item.parent][0], item.minimum[0])
        y, height = scaled_axis(y, height, old_sizes[item.parent][1], new_sizes[item.parent][1], item.minimum[1])
        result[item.key] = (x, y, width, height)
        old_boxes[item.key] = item.rect
        old_sizes[item.key] = (max(1, item.rect[2] - left - right), max(1, item.rect[3] - top - bottom))
        new_sizes[item.key] = (max(1, width - left - right), max(1, height - top - bottom))
    return result
