"""带图标库、双色预览和源码草稿的 SVG 属性编辑器。"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF, QSignalBlocker, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QPlainTextEdit, QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

from core.errors import DesignerError
from core.metadata import PropertySpec
from core.svg_values import validate_svg
from resources.svg_icons import CATEGORIES, ICON_BY_KEY, identify_icon, icon_svg, search_icons
from .color_editor import ColorEditor
from .value_editors import ChoiceEditor, DecimalEditor


def svg_pixmap(data: str, size: int, ratio: float, background: str | None = None) -> QPixmap:
    pixmap = QPixmap(round(size * ratio), round(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QColor(background) if background else Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(data.encode("utf-8"))
    renderer.setAnimationEnabled(False)
    painter = QPainter(pixmap)
    try:
        renderer.render(painter, QRectF(4, 4, size - 8, size - 8))
    finally:
        painter.end()
    return pixmap


class SvgDialog(QDialog):
    def __init__(self, spec: PropertySpec, value: str, commit: Callable[[str], bool],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.spec, self.commit = spec, commit
        self._selected_key: str | None = None
        self._writing_source = False
        self._settings_error = ""
        self.setWindowTitle("选择 SVG 图标")
        layout = QVBoxLayout(self)
        tip = QLabel("选择常用图标并调整颜色、线宽，或在“SVG 源码”中编辑自己的图形。确定后应用。")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        content = QHBoxLayout()
        self.tabs = QTabWidget()
        library = QWidget()
        library_layout = QVBoxLayout(library)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索图标，例如：搜索、用户、search")
        self.search.setAccessibleName("搜索内置图标")
        self.search.setClearButtonEnabled(True)
        self.category = ChoiceEditor()
        self.category.setAccessibleName("图标分类")
        self.category.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.category.setMinimumWidth(self.category.fontMetrics().horizontalAdvance("全部分类") + 44)
        self.category.addItem("全部分类", "")
        for category in CATEGORIES:
            self.category.addItem(category, category)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.category)
        library_layout.addLayout(filters)
        self.icons = QListWidget()
        self.icons.setAccessibleName("内置 SVG 图标")
        self.icons.setViewMode(QListView.ViewMode.IconMode)
        self.icons.setMovement(QListView.Movement.Static)
        self.icons.setResizeMode(QListView.ResizeMode.Adjust)
        self.icons.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.icons.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.icons.setIconSize(QSize(36, 36))
        self.icons.setGridSize(QSize(88, 78))
        self.icons.setSpacing(4)
        self.icons.setUniformItemSizes(True)
        library_layout.addWidget(self.icons, 1)
        self.count_label = QLabel()
        library_layout.addWidget(self.count_label)
        self.tabs.addTab(library, "常用图标")
        self.source = QPlainTextEdit(value)
        self.source.setAccessibleName("SVG 源码")
        self.source.setTabChangesFocus(True)
        self.tabs.addTab(self.source, "SVG 源码")
        content.addWidget(self.tabs, 1)
        options = QVBoxLayout()
        self.selection_label = QLabel("当前 SVG（自定义）")
        self.selection_label.setWordWrap(True)
        options.addWidget(self.selection_label)
        self.color = ColorEditor("#cccccc")
        self.color.line_edit.setAccessibleName("图标颜色")
        self.color.setEnabled(False)
        options.addWidget(QLabel("图标颜色"))
        options.addWidget(self.color)
        self.stroke_width = DecimalEditor()
        self.stroke_width.setAccessibleName("图标线宽")
        self.stroke_width.setRange(0.5, 4.0)
        self.stroke_width.setDecimals(1)
        self.stroke_width.setSingleStep(0.1)
        self.stroke_width.setValue(1.8)
        self.stroke_width.setEnabled(False)
        options.addWidget(QLabel("图标线宽"))
        options.addWidget(self.stroke_width)
        options.addSpacing(12)
        previews = QHBoxLayout()
        self.previews: list[QLabel] = []
        for title in ("浅色背景", "深色背景"):
            column = QVBoxLayout()
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column.addWidget(label)
            preview = QLabel()
            preview.setAccessibleName(title + "预览")
            preview.setFixedSize(88, 88)
            self.previews.append(preview)
            column.addWidget(preview)
            previews.addLayout(column)
        options.addLayout(previews)
        note = QLabel("透明背景，缩放不失真。\n图标随项目保存，可直接导出使用。")
        note.setWordWrap(True)
        options.addWidget(note)
        options.addStretch()
        sidebar = QWidget()
        sidebar.setLayout(options)
        sidebar.setFixedWidth(220)
        content.addWidget(sidebar)
        layout.addLayout(content, 1)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorText")
        self.error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        buttons = QDialogButtonBox()
        self.apply_button = buttons.addButton("确定", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(150)
        self._preview_timer.timeout.connect(self.update_preview)
        self.search.textChanged.connect(self.filter_icons)
        self.category.currentIndexChanged.connect(self.filter_icons)
        self.icons.currentItemChanged.connect(self.select_icon)
        self.icons.itemActivated.connect(lambda item: self.accept())
        self.color.line_edit.textChanged.connect(self.regenerate)
        self.stroke_width.valueChanged.connect(self.regenerate)
        self.source.textChanged.connect(self.source_changed)
        self.tabs.currentChanged.connect(self.update_preview)
        identified = identify_icon(value)
        if identified:
            key, color, width = identified
            self.color.line_edit.setText(color)
            self.stroke_width.setValue(width)
            self._selected_key = key
            self.selection_label.setText("已选图标：" + ICON_BY_KEY[key].label)
            self.color.setEnabled(True)
            self.stroke_width.setEnabled(True)
        self.filter_icons()
        self.update_preview()
        available = self.screen().availableGeometry()
        self.resize(min(800, available.width() - 32), min(560, available.height() - 64))

    def filter_icons(self) -> None:
        icons = search_icons(self.search.text(), self.category.currentData())
        ratio = self.devicePixelRatioF()
        color = self.palette().text().color().name()
        # 清空列表也会切换当前项，必须屏蔽这些中间状态，避免搜索时替换草稿。
        with QSignalBlocker(self.icons):
            self.icons.clear()
            for icon in icons:
                item = QListWidgetItem(QIcon(svg_pixmap(icon_svg(icon.key, color), 36, ratio)), icon.label)
                item.setData(Qt.ItemDataRole.UserRole, icon.key)
                item.setSizeHint(QSize(84, 74))
                item.setToolTip(f"{icon.label} · {icon.key}\n{icon.category}")
                self.icons.addItem(item)
                if icon.key == self._selected_key:
                    self.icons.setCurrentItem(item)
        self.count_label.setText(f"{len(icons)} 个图标" if icons else "没有匹配的图标，请更换关键词或分类。")

    def select_icon(self, item: QListWidgetItem | None, previous: QListWidgetItem | None = None) -> None:
        if item is None:
            return
        self._selected_key = item.data(Qt.ItemDataRole.UserRole)
        self.selection_label.setText("已选图标：" + ICON_BY_KEY[self._selected_key].label)
        self.color.setEnabled(True)
        self.stroke_width.setEnabled(True)
        self.regenerate()

    def regenerate(self) -> None:
        if self._selected_key is None:
            return
        try:
            data = icon_svg(self._selected_key, self.color.line_edit.text() or "#cccccc", self.stroke_width.value())
        except ValueError as exc:
            self._settings_error = str(exc)
            self.update_preview()
            return
        self._settings_error = ""
        self._writing_source = True
        try:
            self.source.setPlainText(data)
        finally:
            self._writing_source = False
        self.update_preview()

    def source_changed(self) -> None:
        if self._writing_source:
            return
        self._selected_key = None
        self._settings_error = ""
        self.icons.clearSelection()
        self.icons.setCurrentRow(-1)
        self.selection_label.setText("当前 SVG（自定义）")
        self.color.setEnabled(False)
        self.stroke_width.setEnabled(False)
        self._preview_timer.start()

    def value(self) -> str:
        if self._settings_error and self.tabs.currentIndex() == 0:
            raise DesignerError(self._settings_error)
        value = self.spec.normalize(self.source.toPlainText())
        validate_svg(value)
        return value

    def update_preview(self) -> None:
        self._preview_timer.stop()
        try:
            value = self.value()
        except DesignerError as exc:
            self.error_label.setText(str(exc))
            self.apply_button.setEnabled(False)
            for preview in self.previews:
                preview.clear()
            return
        self.error_label.clear()
        self.apply_button.setEnabled(True)
        for preview, background in zip(self.previews, ("#ffffff", "#202020")):
            preview.setPixmap(svg_pixmap(value, 88, self.devicePixelRatioF(), background))

    def accept(self) -> None:
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        try:
            value = self.value()
            if not self.commit(value):
                self.error_label.setText("属性未能应用，请检查属性面板提示；编辑内容已保留。")
                return
        except DesignerError as exc:
            self.error_label.setText(str(exc))
            return
        super().accept()
