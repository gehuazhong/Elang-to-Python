"""演示事件；再次导出会保留本文件。"""

from inventory_demo import dispatch


def on_low_only_toggled(window, *arguments):
    return dispatch(window, 'low_only', 'toggled', arguments)
