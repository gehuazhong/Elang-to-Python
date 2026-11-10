"""固定演示账号的输入校验；不执行真实登录。"""

from PySide6.QtWidgets import QLineEdit


def initialize(window):
    window.controls["account"].setFocus()


def dispatch(window, control, event, arguments):
    controls = window.controls
    if control == "show_password":
        controls["password"].setEchoMode(QLineEdit.EchoMode.Normal if controls["show_password"].isChecked()
                                          else QLineEdit.EchoMode.Password)
        return
    if control == "fill_demo":
        controls["account"].setText("demo")
        controls["password"].setText("demo123")
        controls["message"].setText("演示账号已填入，点击“登录工作空间”继续。")
        return
    account, password = controls["account"].text().strip(), controls["password"].text()
    if not account:
        controls["message"].setText("请填写账号。可点击“填入演示账号”体验。")
        controls["account"].setFocus()
    elif not password:
        controls["message"].setText("请填写密码。")
        controls["password"].setFocus()
    elif (account, password) != ("demo", "demo123"):
        controls["message"].setText("演示账号或密码不匹配，请使用 demo / demo123。")
    else:
        controls["message"].setText("本地校验通过，欢迎回来！\n这是一份 UI 演示，不会建立真实登录会话。")
        controls["password"].clear()
        controls["show_password"].setChecked(False)

