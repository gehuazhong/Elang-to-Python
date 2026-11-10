"""集合属性的结构与容量校验，供文档和中文内容编辑器共同使用。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import require
from .models import freeze


def normalize_content(kind: str, value: Any, label: str) -> Any:
    total_chars = 0

    def text(item: Any) -> None:
        nonlocal total_chars
        require(isinstance(item, str) and len(item) <= 10000, f"{label}中的每项文字不能超过一万字。")
        require(not any(char in item for char in ("\r", "\n", "\u2028", "\u2029")),
                f"{label}中的单项文字不能包含换行。")
        total_chars += len(item)
        require(total_chars <= 200000, f"{label}总文字不能超过二十万字。")

    def sequence(items: Any, limit: int) -> None:
        require(isinstance(items, (list, tuple)) and len(items) <= limit,
                f"{label}必须为数组，最多允许 {limit} 项。")

    if kind == "string_list":
        sequence(value, 1000)
        for item in value:
            text(item)
    elif kind == "table":
        require(isinstance(value, Mapping) and {"headers", "rows"} <= set(value)
                and set(value) <= {"headers", "rows", "column_widths"}, f"{label}须包含列标题和行数据，可选各列宽度。")
        headers, rows = value["headers"], value["rows"]
        sequence(headers, 50)
        sequence(rows, 200)
        if "column_widths" in value:
            widths = value["column_widths"]
            sequence(widths, 50)
            require(len(widths) == len(headers), f"{label}的列宽数量须与列标题数量一致。")
            require(all(type(width) is int and 0 <= width <= 2000 for width in widths),
                    f"{label}的列宽须为零到二千的整数；零表示使用默认列宽。")
        for header in headers:
            text(header)
        for row in rows:
            sequence(row, 50)
            require(len(row) == len(headers), f"{label}每行的单元格数量须与列标题数量一致。")
            for cell in row:
                text(cell)
    elif kind == "tree":
        count = 0

        def visit(items: Any, depth: int) -> None:
            nonlocal count
            sequence(items, 1000)
            require(not items or depth <= 12, f"{label}最多允许十二层。")
            for item in items:
                count += 1
                require(count <= 1000, f"{label}最多允许一千个节点。")
                require(isinstance(item, Mapping) and set(item) == {"text", "children"},
                        f"{label}节点须包含文字和子节点。")
                text(item["text"])
                visit(item["children"], depth + 1)

        visit(value, 1)
    else:
        require(False, "集合属性类型尚不支持。")
    return freeze(value)
