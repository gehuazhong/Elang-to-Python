"""演示事件；再次导出会保留本文件。"""

from profile_demo import dispatch


def on_edit_profile_clicked(window, *arguments):
    return dispatch(window, 'edit_profile', 'clicked', arguments)
