"""演示事件；再次导出会保留本文件。"""

from tasks_demo import dispatch


def on_add_task_clicked(window, *arguments):
    return dispatch(window, 'add_task', 'clicked', arguments)
