"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_reader_anchorClicked(window, *arguments):
    return dispatch(window, 'reader', 'anchorClicked', arguments)
