"""演示事件；再次导出会保留本文件。"""

from inventory_demo import dispatch


def on_category_currentIndexChanged(window, *arguments):
    return dispatch(window, 'category', 'currentIndexChanged', arguments)
