"""演示事件；再次导出会保留本文件。"""

from inventory_demo import dispatch


def on_stock_list_selection_changed(window, *arguments):
    return dispatch(window, 'stock_list', 'selection_changed', arguments)
