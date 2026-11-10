"""演示事件；再次导出会保留本文件。"""

from tasks_demo import dispatch


def on_task_table_itemSelectionChanged(window, *arguments):
    return dispatch(window, 'task_table', 'itemSelectionChanged', arguments)
