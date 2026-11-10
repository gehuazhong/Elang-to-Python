"""字体与字号只需选择，保留继承值和旧项目里的原始设置。"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QWidget

from .value_editors import ChoiceEditor

logger = logging.getLogger(__name__)


class FontChoiceEditor(ChoiceEditor):
    """字体系列共享属性下拉框的滚轮与弹层规则。"""


class FontFamilyEditor(FontChoiceEditor):
    def __init__(self, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName("选择字体")
        self.setToolTip("从本机字体列表选择，列表使用对应字形显示；继承默认表示跟随所属容器或系统字体。")
        self.view().setMinimumWidth(320)
        self.addItem("继承默认", "")
        self.setItemData(0, "跟随所属容器的字体；主窗口跟随系统默认字体。", Qt.ItemDataRole.ToolTipRole)
        try:
            families = set(filter(None, QFontDatabase.families()))
            chinese = set(QFontDatabase.families(QFontDatabase.WritingSystem.SimplifiedChinese))
        except Exception:
            logger.exception("读取本机字体列表失败，保留原字体设置。")
            self.setToolTip("暂时无法读取本机字体，原设置仍保留；请重新打开属性面板。")
            families, chinese = set(), set()
        for family in sorted(families, key=lambda name: (
                not any("\u3400" <= char <= "\u9fff" for char in name), name not in chinese, name.casefold())):
            self.addItem(family, family)
            index = self.count() - 1
            self.setItemData(index, QFont(family, 10), Qt.ItemDataRole.FontRole)
            self.setItemData(index, f"字体：{family}\n选择后立即应用，可撤销。", Qt.ItemDataRole.ToolTipRole)
        selected = self.findData(value)
        if selected < 0:
            self.addItem(f"{value}（本机未找到）", value)
            selected = self.count() - 1
            self.setItemData(selected, "保留项目的字体名称；本机显示由系统回退字体代替。", Qt.ItemDataRole.ToolTipRole)
        self.setCurrentIndex(selected)


class FontSizeEditor(FontChoiceEditor):
    def __init__(self, value: int, minimum: int, maximum: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName("选择字号")
        self.setToolTip("选择字号即可应用，单位为磅。常用字号在前，其他整数大小在后；继承默认跟随所属容器或系统。")
        self.addItem("继承默认", 0)
        common = (8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 36, 48, 64, 72, 96)
        for size in common:
            if minimum <= size <= maximum:
                self.addItem(f"{size} 磅", size)
        others = [size for size in range(max(1, minimum), maximum + 1) if size not in common]
        if others:
            self.insertSeparator(self.count())
            for size in others:
                self.addItem(f"{size} 磅", size)
        selected = self.findData(value)
        if selected < 0:
            self.addItem(f"{value} 磅（项目原值）", value)
            selected = self.count() - 1
        self.setCurrentIndex(selected)
