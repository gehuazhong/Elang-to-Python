"""可预览、取消和保存的工作台设置。"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
                               QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget)

from panels.font_editor import FontFamilyEditor
from panels.value_editors import ChoiceEditor
from .workbench_settings import (AREAS, LAYOUTS, WorkbenchPreferences, apply_layout_preset, apply_preferences,
                                 capture_workbench, current_preferences, docks, font_declaration, restore_workbench, save_workbench)


class SettingsDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.baseline = capture_workbench(window)
        self._updating = False
        self.setObjectName("workbenchSettings")
        self.setWindowTitle("工作台设置")
        self.setModal(True)
        # Keep the settings controls readable while previewing large shell fonts.
        self.setFont(QFont("Microsoft YaHei UI", 10))
        self.setStyleSheet('QWidget { font-family: "Microsoft YaHei UI"; font-size: 10pt; }'
                          'QWidget#settingsBody, QWidget#settingsViewport { background: #181818; }')
        self.resize(690, 760)
        screen = self.screen()
        if screen:
            area = screen.availableGeometry()
            self.resize(min(690, area.width() - 40), min(760, area.height() - 80))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(12)
        hint = QLabel("调整工作台的外观和布局。更改即时预览，点击应用或确定保存。")
        hint.setWordWrap(True)
        hint.setObjectName("secondaryText")
        layout.addWidget(hint)
        scroll = QScrollArea()
        scroll.viewport().setObjectName("settingsViewport")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("settingsBody")
        contents = QVBoxLayout(body)
        contents.setContentsMargins(0, 0, 8, 0)
        contents.setSpacing(16)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        appearance = QGroupBox("字体与显示")
        form = QFormLayout(appearance)
        form.setContentsMargins(14, 22, 14, 14)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.font_family = FontFamilyEditor(window.workbench_preferences.font_family)
        self.font_family.removeItem(self.font_family.findData(""))
        self.font_family.setToolTip("选择工作台界面字体，列表来自本机已安装字体。")
        self.font_size = self._choice([(size, f"{size} 磅") for size in range(8, 21)])
        self.density = self._choice((("compact", "紧凑"), ("standard", "标准"), ("comfortable", "宽松")))
        self.icon_size = self._choice([(size, f"{size} 像素") for size in (16, 20, 24, 28, 32)])
        self.document_tabs = self._choice((("top", "顶部"), ("bottom", "底部")))
        for label, editor in (("界面字体", self.font_family), ("界面字号", self.font_size), ("界面间距", self.density),
                              ("工具栏图标", self.icon_size), ("文档标签位置", self.document_tabs)):
            editor.setAccessibleName(label)
            form.addRow(label, editor)
            editor.currentIndexChanged.connect(self._preview_appearance)
        self.font_preview = QLabel("中文界面设计器 · Aa 123")
        self.font_preview.setWordWrap(True)
        form.addRow("字体预览", self.font_preview)
        contents.addWidget(appearance)

        layout_group = QGroupBox("工作台布局")
        grid = QGridLayout(layout_group)
        grid.setContentsMargins(14, 22, 14, 14)
        grid.setSpacing(10)
        self.preset = self._choice((("", "选择布局预设…"), *LAYOUTS))
        self.preset.setAccessibleName("布局预设")
        self.preset.activated.connect(self._preview_preset)
        grid.addWidget(QLabel("布局预设"), 0, 0)
        grid.addWidget(self.preset, 0, 1)
        self.panel_editors = {}
        for row, (key, dock) in enumerate(docks(window).items(), 1):
            visible = QCheckBox(dock.windowTitle())
            visible.setAccessibleName("显示" + dock.windowTitle())
            position = self._choice((("left", "左侧"), ("right", "右侧"), ("bottom", "底部"), ("top", "顶部"), ("floating", "独立浮动")))
            position.setAccessibleName(dock.windowTitle() + "位置")
            visible.toggled.connect(lambda checked, name=key: self._preview_visible(name, checked))
            position.activated.connect(lambda index, name=key: self._preview_position(name))
            grid.addWidget(visible, row, 0)
            grid.addWidget(position, row, 1)
            self.panel_editors[key] = visible, position
        self.lock_panels = QCheckBox("锁定面板位置（禁止拖动和浮动）")
        self.lock_panels.toggled.connect(self._preview_appearance)
        grid.addWidget(self.lock_panels, 5, 0, 1, 2)
        grid.setColumnStretch(1, 1)
        contents.addWidget(layout_group)

        bars = QGroupBox("工作台区域")
        bars_layout = QVBoxLayout(bars)
        bars_layout.setContentsMargins(14, 22, 14, 14)
        self.main_toolbar = QCheckBox("显示顶部工具栏")
        self.activity_bar = QCheckBox("显示左侧面板入口栏")
        self.status_bar = QCheckBox("显示底部状态栏")
        for box in (self.main_toolbar, self.activity_bar, self.status_bar):
            bars_layout.addWidget(box)
            box.toggled.connect(self._preview_appearance)
        contents.addWidget(bars)
        note = QLabel("这里的设置用于本软件。设计窗口的字体、字号和尺寸仍在组件属性中调整。")
        note.setObjectName("secondaryText")
        note.setWordWrap(True)
        contents.addWidget(note)
        contents.addStretch()
        self.message = QLabel()
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.buttons = QDialogButtonBox()
        self.reset_button = self.buttons.addButton("恢复默认", QDialogButtonBox.ButtonRole.ResetRole)
        self.apply_button = self.buttons.addButton("应用", QDialogButtonBox.ButtonRole.ApplyRole)
        self.ok_button = self.buttons.addButton("确定", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = self.buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        for button in (self.reset_button, self.apply_button, self.cancel_button):
            button.setAutoDefault(False)
        self.reset_button.clicked.connect(self.reset_defaults)
        self.apply_button.clicked.connect(self.apply_changes)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.ok_button.setDefault(True)
        layout.addWidget(self.buttons)
        self._load_controls()

    @staticmethod
    def _choice(options):
        editor = ChoiceEditor()
        for value, label in options:
            editor.addItem(label, value)
        return editor

    def _load_controls(self):
        self._updating = True
        try:
            preferences = current_preferences(self.window)
            for editor, value in ((self.font_family, preferences.font_family), (self.font_size, preferences.font_size),
                                  (self.density, preferences.density), (self.icon_size, preferences.toolbar_icon_size),
                                  (self.document_tabs, preferences.document_tabs)):
                index = editor.findData(value)
                if index < 0:
                    editor.addItem(str(value), value)
                    index = editor.count() - 1
                editor.setCurrentIndex(index)
            for editor, value in ((self.lock_panels, preferences.lock_panels), (self.main_toolbar, preferences.main_toolbar_visible),
                                  (self.activity_bar, preferences.activity_bar_visible), (self.status_bar, preferences.status_bar_visible)):
                editor.setChecked(value)
            self.font_preview.setFont(QFont(preferences.font_family, preferences.font_size))
            self.font_preview.setStyleSheet("QLabel { " + font_declaration(preferences.font_family, preferences.font_size) + " }")
            for key, dock in docks(self.window).items():
                visible, position = self.panel_editors[key]
                visible.setChecked(not dock.isHidden())
                area = "floating" if dock.isFloating() else next((key for key, area in AREAS.items() if area == self.window.dockWidgetArea(dock)), "left")
                position.setCurrentIndex(position.findData(area))
                position.setEnabled(not preferences.lock_panels)
        finally:
            self._updating = False

    def _preview_appearance(self, *_):
        if self._updating:
            return
        preferences = WorkbenchPreferences(font_family=self.font_family.currentData(), font_size=self.font_size.currentData(),
            density=self.density.currentData(), toolbar_icon_size=self.icon_size.currentData(), document_tabs=self.document_tabs.currentData(),
            lock_panels=self.lock_panels.isChecked(), main_toolbar_visible=self.main_toolbar.isChecked(),
            activity_bar_visible=self.activity_bar.isChecked(), status_bar_visible=self.status_bar.isChecked())
        apply_preferences(self.window, preferences)
        self._load_controls()
        self.message.setText("正在预览；应用或确定后保存，取消恢复到上次应用的状态。")

    def _preview_preset(self, *_):
        selected = self.preset.currentData()
        if selected:
            apply_layout_preset(self.window, selected)
            self._load_controls()
            self.preset.setCurrentIndex(0)

    def _preview_visible(self, key, checked):
        if not self._updating:
            docks(self.window)[key].setVisible(checked)

    def _preview_position(self, key):
        if self._updating:
            return
        dock = docks(self.window)[key]
        visible, position = self.panel_editors[key]
        area = position.currentData()
        if area == "floating":
            dock.setFloating(True)
        else:
            dock.setFloating(False)
            self.window.addDockWidget(AREAS[area], dock)
        dock.setVisible(visible.isChecked())

    def reset_defaults(self):
        apply_preferences(self.window, WorkbenchPreferences())
        apply_layout_preset(self.window, "standard")
        self.window.properties.tree.setColumnWidth(0, 110)
        self._load_controls()
        self.message.setText("已预览默认设置；点击应用或确定保存。")

    def apply_changes(self):
        if not save_workbench(self.window):
            self.message.setText("设置保存失败，请检查系统配置目录的写入权限后重试。当前更改仍可取消。")
            return False
        self.baseline = capture_workbench(self.window)
        self.message.setText("设置已应用并保存。" if self.window.persist_settings else "设置已应用到当前会话。")
        return True

    def accept(self):
        if self.apply_changes():
            super().accept()

    def reject(self):
        restore_workbench(self.window, self.baseline)
        super().reject()
