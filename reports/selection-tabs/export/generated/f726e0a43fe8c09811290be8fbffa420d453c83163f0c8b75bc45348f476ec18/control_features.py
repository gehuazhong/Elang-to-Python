"""补充属性的原生转换，画布、预览与独立导出共用。"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import QAbstractButton, QApplication, QFontComboBox, QGroupBox, QKeySequenceEdit, QTextEdit

from .easy_widgets import decoded_image


FEATURE_KEYS = {
    **{name: {"icon", "icon_width", "icon_height", "shortcut"} for name in
       ("QPushButton", "QToolButton", "QCommandLinkButton", "QCheckBox", "QRadioButton")},
    "QAction": {"icon"}, "QGroupBox": {"checked"}, "QFontComboBox": {"current_font"},
    "QKeySequenceEdit": {"key_sequence"},
    "QTextEdit": {"text", "text_format", "document_margin"},
    "QTextBrowser": {"text", "text_format", "document_margin"},
}


def apply_control_features(widget, values):
    if isinstance(widget, (QAbstractButton, QAction)) and "icon" in values:
        if not hasattr(widget, "_initial_design_icon"):
            widget._initial_design_icon = QIcon(widget.icon())
        icon = QIcon(widget._initial_design_icon)
        if values["icon"]:
            icon = QIcon(QPixmap.fromImage(decoded_image(values["icon"])))
        widget.setIcon(icon)
    if isinstance(widget, QAbstractButton) and "icon_width" in values:
        if not hasattr(widget, "_initial_design_icon_size"):
            widget._initial_design_icon_size = widget.iconSize()
        initial = widget._initial_design_icon_size
        widget.setIconSize(QSize(values["icon_width"] or initial.width(), values["icon_height"] or initial.height()))
        sequence = (QKeySequence.fromString(values["shortcut"], QKeySequence.SequenceFormat.PortableText)
                    if values["shortcut"] else QKeySequence.mnemonic(widget.text()))
        widget.setShortcut(sequence)
    if isinstance(widget, QTextEdit):
        if values["text_format"] == "rich":
            widget.setHtml(values["text"])
        else:
            widget.setPlainText(values["text"])
        widget.document().setDocumentMargin(values["document_margin"])
    if isinstance(widget, QFontComboBox):
        widget.setCurrentFont(QFont(values["current_font"]) if values["current_font"] else QApplication.font())
    if isinstance(widget, QKeySequenceEdit):
        widget.setMaximumSequenceLength(1)
        widget.setKeySequence(QKeySequence.fromString(values["key_sequence"], QKeySequence.SequenceFormat.PortableText))


def prepare_group_states(controls):
    # 原生组先恢复可选状态，避免子控件属性覆盖上一轮的整组禁用。
    for widget in controls.values():
        if isinstance(widget, QGroupBox) and widget.isCheckable():
            widget.setChecked(True)


def finish_group_states(controls, records):
    # 全部子控件创建并写入属性后，再让 Qt 应用整组勾选状态。
    for key, checked in records:
        group = controls[key]
        if group.isCheckable():
            group.setChecked(checked)
