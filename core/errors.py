"""面向用户的领域错误。"""


class DesignerError(ValueError):
    """可在界面直接显示的中文错误。"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DesignerError(message)
