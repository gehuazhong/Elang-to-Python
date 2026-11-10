"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_shortcut_input_keySequenceChanged(window, *arguments):
    return dispatch(window, 'shortcut_input', 'keySequenceChanged', arguments)
