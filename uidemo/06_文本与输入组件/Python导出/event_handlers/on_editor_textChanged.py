"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_editor_textChanged(window, *arguments):
    return dispatch(window, 'editor', 'textChanged', arguments)
