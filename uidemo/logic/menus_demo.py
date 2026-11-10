"""菜单示例业务：与生成界面分离，再次导出会保留。"""


def initialize(window):
    window._new_project_count = 0


def dispatch(window, control, event, arguments):
    controls = window.controls
    if control == "menu_exit":
        window.close()
        return
    if control == "menu_new":
        window._new_project_count += 1
        message = f"已新建项目 {window._new_project_count}（演示，不写入文件）。"
    elif control == "menu_details":
        checked = bool(arguments[0])
        controls["detail"].setVisible(checked)
        message = "说明已显示。" if checked else "说明已隐藏。"
    elif control in {"menu_recent_inventory", "menu_recent_tasks"}:
        message = "已选择最近项目：" + controls[control].text() + "（演示，不打开文件）。"
    else:
        message = "菜单支持层级、快捷键、选中、禁止、可视、分隔线和事件勾选。"
    controls["menu_message"].setText(message)
