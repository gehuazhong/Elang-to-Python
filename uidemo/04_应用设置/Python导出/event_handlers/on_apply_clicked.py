"""演示事件；再次导出会保留本文件。"""

from settings_demo import dispatch


def on_apply_clicked(window, *arguments):
    return dispatch(window, 'apply', 'clicked', arguments)
