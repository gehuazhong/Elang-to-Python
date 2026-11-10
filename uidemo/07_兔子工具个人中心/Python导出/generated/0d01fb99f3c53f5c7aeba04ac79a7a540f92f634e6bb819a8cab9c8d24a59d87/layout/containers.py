"""Pure placement rules shared by validation and native layout adapters."""

LAYOUT_TYPES = frozenset("builtin." + name for name in
                        ("horizontal_layout", "vertical_layout", "grid_layout", "form_layout"))
PAGE_TYPES = frozenset({"builtin.tab_widget", "builtin.stacked_widget", "builtin.tool_box", "builtin.wizard"})


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
