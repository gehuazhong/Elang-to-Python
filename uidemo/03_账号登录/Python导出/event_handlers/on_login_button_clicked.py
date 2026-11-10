"""演示事件；再次导出会保留本文件。"""

from login_demo import dispatch


def on_login_button_clicked(window, *arguments):
    return dispatch(window, 'login_button', 'clicked', arguments)
