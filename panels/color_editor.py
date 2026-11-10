"""颜色属性支持直接输入、选择颜色和恢复默认。"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget
from resources.colors import COLORS

logger = logging.getLogger(__name__)


class ColorEditor(QWidget):
    value_committed = Signal(str)
    editing_finished = Signal()
    error = Signal(str)

    def __init__(self, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.choosing = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.line_edit = QLineEdit(value)
        self.line_edit.setPlaceholderText("默认")
        self.line_edit.setToolTip("输入六位颜色值；留空恢复默认颜色。")
        self.button = QPushButton()
        self.button.setFixedWidth(29)
        self.button.setToolTip("选择颜色")
        self.button.setAccessibleName("选择颜色")
        self.reset_button = QPushButton("重置")
        self.reset_button.setFixedWidth(43)
        self.reset_button.setToolTip("恢复默认颜色")
        layout.addWidget(self.button)
        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.reset_button)
        self.line_edit.textChanged.connect(self._update_swatch)
        self.line_edit.editingFinished.connect(lambda: self.value_committed.emit(self.line_edit.text()))
        self.button.clicked.connect(self._choose)
        self.reset_button.clicked.connect(self._reset)
        self._update_swatch(value)

    def _update_swatch(self, value: str) -> None:
        color = QColor(value)
        self.button.setText("" if color.isValid() else "…")
        self.button.setStyleSheet(
            f"background-color: {color.name() if color.isValid() else COLORS['input']};"
            f"border: 1px solid {COLORS['line_hover']};"
        )

    def _choose(self) -> None:
        self.choosing = True
        dialog: QColorDialog | None = None
        try:
            dialog = QColorDialog(self)
            dialog.setWindowTitle("选择颜色")
            dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
            value = QColor(self.line_edit.text())
            dialog.setCurrentColor(value if value.isValid() else QColor("#ffffff"))
            if dialog.exec() == QColorDialog.DialogCode.Accepted:
                self.line_edit.setText(dialog.selectedColor().name())
                self.value_committed.emit(self.line_edit.text())
        except Exception:
            logger.exception("颜色选择失败，保留原颜色设置。")
            self.error.emit("颜色选择失败，原设置仍保留；详细原因已写入日志。")
        finally:
            if dialog is not None:
                dialog.deleteLater()
            self.choosing = False
            self.editing_finished.emit()

    def _reset(self) -> None:
        self.line_edit.clear()
        self.value_committed.emit("")
