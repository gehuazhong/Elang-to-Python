"""演示事件；再次导出会保留本文件。"""

from profile_demo import dispatch


def on_tool_3_clicked(window, *arguments):
    return dispatch(window, 'tool_3', 'clicked', arguments)
