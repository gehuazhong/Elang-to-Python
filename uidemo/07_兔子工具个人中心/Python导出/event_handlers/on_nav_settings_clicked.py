"""演示事件；再次导出会保留本文件。"""

from profile_demo import dispatch


def on_nav_settings_clicked(window, *arguments):
    return dispatch(window, 'nav_settings', 'clicked', arguments)
