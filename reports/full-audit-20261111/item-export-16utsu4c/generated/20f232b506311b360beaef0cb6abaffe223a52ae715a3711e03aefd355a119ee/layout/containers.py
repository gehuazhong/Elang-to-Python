"""Pure placement rules shared by validation and native layout adapters."""

LAYOUT_TYPES = frozenset("builtin." + name for name in
                        ("horizontal_layout", "vertical_layout", "grid_layout", "form_layout"))
PAGE_TYPES = frozenset({"builtin.tab_widget", "builtin.stacked_widget", "builtin.tool_box", "builtin.wizard"})


def tab_header_visible(values, count):
    return values.get("header_visible", True) and not (values.get("tab_bar_auto_hide", False) and count <= 1)


def tab_margins(values, count):
    border = int(values.get("pane_border", True))
    margins = [border] * 4
    if tab_header_visible(values, count):
        side = {"left": 0, "top": 1, "right": 2, "bottom": 3}[values.get("tab_position", "top")]
        margins[side] = values.get("tab_bar_size", 30)
    return tuple(margins)


def inset_rect(width, height, margins):
    left, top, right, bottom = margins
    left, top = min(left, max(0, width - 1)), min(top, max(0, height - 1))
    right, bottom = min(right, max(0, width - left - 1)), min(bottom, max(0, height - top - 1))
    return left, top, max(1, width - left - right), max(1, height - top - bottom)


def grid_cells(items, columns):
    occupied = set()
    result = {}
    automatic = []
    for key, values in items:
        row, column = values.get("layout_row", -1), values.get("layout_column", -1)
        rows, cols = values.get("layout_row_span", 1), values.get("layout_column_span", 1)
        if (row < 0) != (column < 0):
            raise ValueError("布局行和列必须同时指定，或同时设为自动。")
        if row < 0:
            automatic.append((key, rows, cols))
            continue
        cells = {(r, c) for r in range(row, row + rows) for c in range(column, column + cols)}
        if occupied & cells:
            raise ValueError("网格布局的行列与跨度发生重叠。")
        occupied.update(cells)
        result[key] = (row, column, rows, cols)
    cursor = 0
    for key, rows, cols in automatic:
        extent = max(columns, cols)
        while True:
            row, column = divmod(cursor, extent)
            cursor += 1
            if column + cols > extent:
                continue
            cells = {(r, c) for r in range(row, row + rows) for c in range(column, column + cols)}
            if not occupied & cells:
                occupied.update(cells)
                result[key] = (row, column, rows, cols)
                break
    return result


def managed_child(model, key):
    node = model.nodes[key]
    parent = model.nodes.get(node.parent_id)
    return bool(parent and (parent.type_id in LAYOUT_TYPES or parent.type_id == "builtin.splitter"
                            or (parent.layout or {}).get("kind", "absolute") != "absolute"))
