"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_help_link_linkActivated(window, *arguments):
    return dispatch(window, 'help_link', 'linkActivated', arguments)
