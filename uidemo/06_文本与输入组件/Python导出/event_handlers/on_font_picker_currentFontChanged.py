"""演示事件；再次导出会保留本文件。"""

from text_inputs_demo import dispatch


def on_font_picker_currentFontChanged(window, *arguments):
    return dispatch(window, 'font_picker', 'currentFontChanged', arguments)
