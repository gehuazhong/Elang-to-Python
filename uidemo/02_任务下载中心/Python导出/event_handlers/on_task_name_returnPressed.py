"""演示事件；再次导出会保留本文件。"""

from tasks_demo import dispatch


def on_task_name_returnPressed(window, *arguments):
    return dispatch(window, 'task_name', 'returnPressed', arguments)
