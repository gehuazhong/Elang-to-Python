"""演示事件；再次导出会保留本文件。"""

from profile_demo import dispatch


def on_close_window_clicked(window, *arguments):
    return dispatch(window, 'close_window', 'clicked', arguments)
