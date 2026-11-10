"""演示事件；再次导出会保留本文件。"""

from tasks_demo import dispatch


def on_clear_done_clicked(window, *arguments):
    return dispatch(window, 'clear_done', 'clicked', arguments)
