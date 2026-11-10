"""个人中心的本地演示交互；资料仅在本次运行中保留。"""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox


class TitleDrag(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            handle = self.parent().windowHandle()
            if handle is not None:
                return handle.startSystemMove()
        return False


def initialize(window):
    c = window.controls
    window._profile_drag = TitleDrag(window)
    for code in ("titlebar", "top_name", "top_avatar"):
        c[code].installEventFilter(window._profile_drag)
    for code in ("nav_home", "nav_profile", "nav_tools_one", "nav_tools_two", "nav_settings", "edit_profile", "minimize", "close_window"):
        button = c[code]
        button.setAccessibleName(button.toolTip())
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 5px; }"
                            "QPushButton:hover, QPushButton:focus { background: rgba(255,255,255,18); }"
                            "QPushButton:pressed { background: rgba(255,255,255,30); }")
    for index in range(1, 4):
        c[f"tool_{index}"].setCursor(Qt.CursorShape.PointingHandCursor)
    window._profile_section = "profile"
    c["nav_profile"].setFocus()


def style_dialog(dialog):
    dialog.setStyleSheet("QDialog, QMessageBox { background: #262626; color: #dddddd; }"
                        "QLabel { color: #dddddd; }"
                        "QLineEdit { background: #181818; color: #eeeeee; border: 1px solid #555; padding: 7px; }"
                        "QPushButton { background: #383838; color: #eeeeee; border: 1px solid #555; padding: 6px 16px; }"
                        "QPushButton:hover { background: #484848; }")


def edit_profile(window):
    existing = getattr(window, "_profile_dialog", None)
    if existing is not None and existing.isVisible():
        existing.raise_()
        existing.activateWindow()
        return
    c = window.controls
    dialog = QDialog(window)
    dialog.setWindowTitle("修改资料")
    dialog.setMinimumWidth(360)
    layout = QFormLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(14)
    nickname = QLineEdit(c["nickname"].text(), dialog)
    nickname.setMaxLength(16)
    location = QLineEdit(c["location"].text(), dialog)
    location.setMaxLength(7)
    message = QLabel("资料只在本次演示中生效。", dialog)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
    layout.addRow("昵称", nickname)
    layout.addRow("所在地", location)
    layout.addRow(message)
    layout.addRow(buttons)

    def save():
        name = nickname.text().strip()
        if not name:
            message.setText("昵称不能为空。")
            nickname.setFocus()
            return
        c["nickname"].setText(name)
        c["top_name"].setText(c["top_name"].fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, c["top_name"].width()))
        c["top_name"].setToolTip(name)
        c["location"].setText(location.text().strip() or "未设置")
        dialog.accept()

    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)
    dialog.finished.connect(dialog.deleteLater)
    dialog.finished.connect(lambda: setattr(window, "_profile_dialog", None))
    dialog._nickname = nickname
    dialog._location = location
    dialog._message = message
    dialog._buttons = buttons
    window._profile_dialog = dialog
    style_dialog(dialog)
    dialog.open()


def dispatch(window, control, event, arguments):
    c = window.controls
    if control == "minimize":
        window.showMinimized()
    elif control == "close_window":
        window.close()
    elif control == "edit_profile":
        edit_profile(window)
    elif control == "nav_settings":
        show_message(window, "设置", "兔子工具 · 布局示例", "版本 V25.10.22\n资料修改仅保留到本次窗口关闭。")
    elif control.startswith("nav_"):
        section = control.removeprefix("nav_")
        title, heading, prefix, y = {
            "home": ("首页", "发现常用工具", "推荐工具", 108),
            "profile": ("个人中心", "我收藏的工具", "我喜欢的工具", 148),
            "tools_one": ("壹号工具箱", "日常效率工具", "效率工具", 237),
            "tools_two": ("贰号工具箱", "实用工具收藏", "实用工具", 278),
        }[section]
        window._profile_section = section
        c["nav_active"].move(14, y)
        c["title"].setText(title)
        c["collection_heading"].setText(heading)
        for index in range(1, 4):
            c[f"tool_caption_{index}"].setText(prefix + str(index))
            c[f"tool_{index}"].setToolTip("打开" + prefix + str(index))
    elif control.startswith("tool_"):
        title = c["tool_caption_" + control.rsplit("_", 1)[1]].text()
        show_message(window, title, title, "这是工具入口的界面演示。\n可根据需要扩展具体工具功能。")


def show_message(window, title, text, detail):
    previous = getattr(window, "_tool_dialog", None)
    if previous is not None and previous.isVisible():
        previous.close()
    dialog = QMessageBox(window)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setInformativeText(detail)
    dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
    dialog.button(QMessageBox.StandardButton.Ok).setText("知道了")
    style_dialog(dialog)
    dialog.finished.connect(dialog.deleteLater)
    dialog.finished.connect(lambda: setattr(window, "_tool_dialog", None))
    window._tool_dialog = dialog
    dialog.open()
