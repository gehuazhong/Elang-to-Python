"""演示事件；再次导出会保留本文件。"""

from inventory_demo import dispatch


def on_search_button_clicked(window, *arguments):
    return dispatch(window, 'search_button', 'clicked', arguments)
