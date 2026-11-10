"""窗口标志及复合外观属性的统一 Qt 适配。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from .easy_widgets import decoded_image


APPEARANCE_KEYS = frozenset({"background_color", "foreground_color", "font_family", "font_size",
                            "font_bold", "font_italic", "font_underline", "font_strikeout"})
WINDOW_KEYS = frozenset({"window_icon", "border_style", "minimize_button", "maximize_button", "close_button", "stay_on_top", "scale_children"})


def apply_window_options(window: QMainWindow, values: Mapping[str, Any]) -> None:
    icon = QIcon()
    if values.get("window_icon"):
        icon.addPixmap(QPixmap.fromImage(decoded_image(values["window_icon"])))
    window.setWindowIcon(icon)
    flags = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
    border = values["border_style"]
    if border == "none":
        flags |= Qt.WindowType.FramelessWindowHint
    else:
        flags |= Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint
        if values["minimize_button"]:
            flags |= Qt.WindowType.WindowMinimizeButtonHint
        if values["maximize_button"] and border != "fixed":
            flags |= Qt.WindowType.WindowMaximizeButtonHint
        if values["close_button"]:
            flags |= Qt.WindowType.WindowCloseButtonHint
        if border == "fixed":
            flags |= Qt.WindowType.MSWindowsFixedSizeDialogHint
    if values["stay_on_top"]:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    if window.windowFlags() != flags:
        visible = window.isVisible()
        window.setWindowFlags(flags)
        if visible:
            window.show()
    # 解除旧约束后再由构建器写入新尺寸，支持固定边框的往返切换。
    window.setMinimumSize(0, 0)
    window.setMaximumSize(16777215, 16777215)


def apply_appearance(widget: QWidget, values: Mapping[str, Any]) -> None:
    parent = widget.parentWidget()
    palette = QPalette(parent.palette() if parent else QApplication.palette())
    if parent is None:
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    background = values.get("background_color", "")
    foreground = values.get("foreground_color", "")
    if background:
        for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.Button):
            palette.setColor(role, QColor(background))
    if foreground:
        for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
            palette.setColor(role, QColor(foreground))
    widget.setPalette(palette)
    widget.setAutoFillBackground(bool(background) or isinstance(parent, QMainWindow))
    font = QFont(parent.font() if parent else QApplication.font())
    if values.get("font_family"):
        font.setFamily(values["font_family"])
    if values.get("font_size"):
        font.setPointSize(values["font_size"])
    for key, setter in (("font_bold", font.setBold), ("font_italic", font.setItalic),
                        ("font_underline", font.setUnderline), ("font_strikeout", font.setStrikeOut)):
        if key in values:
            setter(values[key])
    widget.setFont(font)
