"""本次运行内的设置应用、恢复和控件联动。"""

from PySide6.QtCore import QDate


def initialize(window):
    window._demo_settings = None


def dispatch(window, control, event, arguments):
    c = window.controls
    if control == "notifications":
        enabled = c["notifications"].isChecked()
        for key in ("volume", "volume_value", "quiet_mode"):
            c[key].setEnabled(enabled)
        return
    if control == "volume":
        c["volume_value"].setText(f"{c['volume'].value()}%")
        return
    if control == "restore":
        c["workspace_name"].setText("我的工作空间")
        c["language"].setCurrentIndex(0)
        c["retention"].setValue(30)
        c["auto_save"].setChecked(True)
        c["notifications"].setChecked(True)
        c["volume"].setValue(60)
        c["schedule_date"].setDate(QDate(2026, 11, 9))
        c["quiet_mode"].setChecked(True)
        c["settings_message"].setText("已恢复默认值；点击“应用设置”确认。")
        return
    name = c["workspace_name"].text().strip()
    if not name:
        c["settings_tabs"].set_current_page(0)
        c["settings_message"].setText("空间名称不能为空。")
        c["workspace_name"].setFocus()
        return
    values = {"name": name, "language": c["language"].currentText(), "retention": c["retention"].value(),
              "auto_save": c["auto_save"].isChecked(), "notifications": c["notifications"].isChecked(),
              "volume": c["volume"].value(), "date": c["schedule_date"].date().toString("yyyy-MM-dd"),
              "quiet_mode": c["quiet_mode"].isChecked()}
    window._demo_settings = values
    notification = "提醒开启" if values["notifications"] else "提醒关闭"
    c["settings_summary"].setText(f"当前：{name} · {values['language']} · 历史 {values['retention']} 天 · {notification}")
    c["settings_message"].setText("设置已应用到本次演示，关闭后恢复初始值。")
