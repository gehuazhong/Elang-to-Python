"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_save_draft_clicked(window, *arguments):
    return dispatch(window, 'save_draft', 'clicked', arguments)
