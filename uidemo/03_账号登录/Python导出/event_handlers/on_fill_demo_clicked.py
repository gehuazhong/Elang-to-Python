"""演示事件；再次导出会保留本文件。"""

from login_demo import dispatch


def on_fill_demo_clicked(window, *arguments):
    return dispatch(window, 'fill_demo', 'clicked', arguments)
