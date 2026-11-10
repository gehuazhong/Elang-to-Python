"""演示事件；再次导出会保留本文件。"""

from login_demo import dispatch


def on_password_returnPressed(window, *arguments):
    return dispatch(window, 'password', 'returnPressed', arguments)
