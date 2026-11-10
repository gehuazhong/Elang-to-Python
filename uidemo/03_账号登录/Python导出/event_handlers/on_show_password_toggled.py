"""演示事件；再次导出会保留本文件。"""

from login_demo import dispatch


def on_show_password_toggled(window, *arguments):
    return dispatch(window, 'show_password', 'toggled', arguments)
