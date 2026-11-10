"""演示事件；再次导出会保留本文件。"""

from menus_demo import dispatch


def on_menu_new_clicked(window, *arguments):
    return dispatch(window, 'menu_new', 'clicked', arguments)
