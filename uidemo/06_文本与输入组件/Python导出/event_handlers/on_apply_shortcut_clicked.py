"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_apply_shortcut_clicked(window, *arguments):
    return dispatch(window, 'apply_shortcut', 'clicked', arguments)
