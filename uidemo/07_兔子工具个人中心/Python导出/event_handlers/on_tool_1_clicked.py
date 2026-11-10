"""演示事件；再次导出会保留本文件。"""

from profile_demo import dispatch


def on_tool_1_clicked(window, *arguments):
    return dispatch(window, 'tool_1', 'clicked', arguments)
