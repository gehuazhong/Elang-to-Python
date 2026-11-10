"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_read_only_toggled(window, *arguments):
    return dispatch(window, 'read_only', 'toggled', arguments)
