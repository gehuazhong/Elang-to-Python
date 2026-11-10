"""自动生成的界面模块；事件业务请写入 event_handlers，初始化请写入 handlers.py。"""
from __future__ import annotations

from PySide6.QtCore import Qt as _Qt, QObject as _QObject, QTimer as _QTimer
from PySide6.QtGui import QAction as _QAction
from PySide6.QtWidgets import QCalendarWidget as _QCalendarWidget, QCheckBox as _QCheckBox, QComboBox as _QComboBox, QCommandLinkButton as _QCommandLinkButton, QDateEdit as _QDateEdit, QDateTimeEdit as _QDateTimeEdit, QDial as _QDial, QDoubleSpinBox as _QDoubleSpinBox, QFrame as _QFrame, QGroupBox as _QGroupBox, QLCDNumber as _QLCDNumber, QLabel as _QLabel, QLineEdit as _QLineEdit, QListWidget as _QListWidget, QMainWindow as _QMainWindow, QMenuBar as _QMenuBar, QPlainTextEdit as _QPlainTextEdit, QProgressBar as _QProgressBar, QPushButton as _QPushButton, QRadioButton as _QRadioButton, QScrollBar as _QScrollBar, QSlider as _QSlider, QSpinBox as _QSpinBox, QStatusBar as _QStatusBar, QTableWidget as _QTableWidget, QTimeEdit as _QTimeEdit, QToolBar as _QToolBar, QToolButton as _QToolButton, QTreeWidget as _QTreeWidget, QWidget as _QWidget
from .easy_widgets import CommonDialog as _CommonDialog, DrawingBoard as _DrawingBoard, PictureBox as _PictureBox, SelectionTabs as _SelectionTabs, SuperList as _SuperList
from .easy_widgets import apply_easy_properties as _apply_easy_properties, start_components as _start_components, image_asset as _image_asset
from .appearance import apply_appearance as _apply_appearance, apply_window_options as _apply_window_options
from .widget_properties import apply_widget_properties as _apply_widget_properties, apply_content_margins as _apply_content_margins
from .widget_properties import ContainerGroupBox as _QGroupBox, ContainerFrame as _QFrame
from .menus import apply_menu_properties as _apply_menu_properties, arrange_menus as _arrange_menus
from .layout.scaling import ScaleItem as _ScaleItem
from .layout.runtime import WindowScaler as _WindowScaler
from .application import configure_application

class MainWindow(_QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setup_ui()

    def setup_ui(self) -> None:
        self.controls: dict[str, _QObject] = {}
        # 创建窗口并应用已校验的属性。
        self.controls['main_window'] = self
        self.controls['main_window'].setObjectName('主窗口')
        values = {'window_title': '菜单编辑示例', 'window_icon': '', 'border_style': 'standard', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': False, 'background_color': '#f5f6f2', 'foreground_color': '#253332', 'font_family': 'Microsoft YaHei UI', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_menu_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(880, 600)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(self.controls['main_window'])
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '#f5f6f2', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_menu_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['eyebrow'] = _QLabel(self.controls['central_widget'])
        self.controls['eyebrow'].setObjectName('菜单与事件')
        self.controls['eyebrow'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '菜单与事件', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['eyebrow'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['eyebrow'], values)
        _apply_menu_properties(self.controls['eyebrow'], values)
        _apply_appearance(self.controls['eyebrow'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['eyebrow'].setGeometry(36 + offset.x(), 26 + offset.y(), 800, 24)
        _apply_content_margins(self.controls['eyebrow'], values)
        self.controls['eyebrow'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['title'] = _QLabel(self.controls['central_widget'])
        self.controls['title'].setObjectName('我的项目工作台')
        self.controls['title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '我的项目工作台', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 24, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['title'], values)
        _apply_menu_properties(self.controls['title'], values)
        _apply_appearance(self.controls['title'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['title'].setGeometry(36 + offset.x(), 60 + offset.y(), 800, 46)
        _apply_content_margins(self.controls['title'], values)
        self.controls['title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['intro'] = _QLabel(self.controls['central_widget'])
        self.controls['intro'].setObjectName('文件、视图、帮助菜单可直接操作，也可以使用 Ct')
        self.controls['intro'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '文件、视图、帮助菜单可直接操作，也可以使用 Ctrl+N、Ctrl+G。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['intro'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['intro'], values)
        _apply_menu_properties(self.controls['intro'], values)
        _apply_appearance(self.controls['intro'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['intro'].setGeometry(36 + offset.x(), 116 + offset.y(), 800, 32)
        _apply_content_margins(self.controls['intro'], values)
        self.controls['intro'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['content'] = _QFrame(self.controls['central_widget'])
        self.controls['content'].setObjectName('内容区')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['content'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['content'], values)
        _apply_menu_properties(self.controls['content'], values)
        _apply_appearance(self.controls['content'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['content'].setGeometry(36 + offset.x(), 180 + offset.y(), 808, 246)
        _apply_content_margins(self.controls['content'], values)
        self.controls['content'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['content_title'] = _QLabel(self.controls['content'])
        self.controls['content_title'].setObjectName('从菜单开始操作')
        self.controls['content_title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '从菜单开始操作', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 16, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['content_title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['content_title'], values)
        _apply_menu_properties(self.controls['content_title'], values)
        _apply_appearance(self.controls['content_title'], values)
        offset = self.controls['content'].contentsRect().topLeft()
        self.controls['content_title'].setGeometry(24 + offset.x(), 24 + offset.y(), 748, 34)
        _apply_content_margins(self.controls['content_title'], values)
        self.controls['content_title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['detail'] = _QLabel(self.controls['content'])
        self.controls['detail'].setObjectName('文件 → 新建项目：更新下方状态')
        self.controls['detail'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '文件 → 新建项目：更新下方状态\n文件 → 最近项目：体验三级菜单\n视图 → 显示说明：切换本区内容\n禁止操作不可点击；隐藏操作不会显示', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['detail'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['detail'], values)
        _apply_menu_properties(self.controls['detail'], values)
        _apply_appearance(self.controls['detail'], values)
        offset = self.controls['content'].contentsRect().topLeft()
        self.controls['detail'].setGeometry(24 + offset.x(), 82 + offset.y(), 748, 128)
        _apply_content_margins(self.controls['detail'], values)
        self.controls['detail'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['menu_message'] = _QLabel(self.controls['central_widget'])
        self.controls['menu_message'].setObjectName('就绪。请使用窗口上方菜单。')
        self.controls['menu_message'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '就绪。请使用窗口上方菜单。', 'background_color': '', 'foreground_color': '#285c4b', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['menu_message'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['menu_message'], values)
        _apply_menu_properties(self.controls['menu_message'], values)
        _apply_appearance(self.controls['menu_message'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['menu_message'].setGeometry(36 + offset.x(), 458 + offset.y(), 808, 42)
        _apply_content_margins(self.controls['menu_message'], values)
        self.controls['menu_message'].setVisible(True)
        # 创建菜单栏并应用已校验的属性。
        self.controls['menu_bar'] = _QMenuBar(self.controls['main_window'])
        self.controls['menu_bar'].setObjectName('菜单栏')
        values = {'bar_height': 28, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['menu_bar'], values, (('bar_height', None, '菜单栏高度'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['menu_bar'], values)
        _apply_menu_properties(self.controls['menu_bar'], values)
        _apply_appearance(self.controls['menu_bar'], values)
        _apply_content_margins(self.controls['menu_bar'], values)
        self.controls['menu_bar'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_file'] = _QAction(self.controls['menu_bar'])
        self.controls['menu_file'].setObjectName('文件(&F)')
        values = {'text': '文件(&F)', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_file'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_file'], values)
        _apply_menu_properties(self.controls['menu_file'], values)
        self.controls['menu_file'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_new'] = _QAction(self.controls['menu_file'])
        self.controls['menu_new'].setObjectName('新建项目(&N)')
        values = {'text': '新建项目(&N)', 'shortcut': 'Ctrl+N', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_new'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_new'], values)
        _apply_menu_properties(self.controls['menu_new'], values)
        self.controls['menu_new'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_recent'] = _QAction(self.controls['menu_file'])
        self.controls['menu_recent'].setObjectName('最近项目(&R)')
        values = {'text': '最近项目(&R)', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_recent'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_recent'], values)
        _apply_menu_properties(self.controls['menu_recent'], values)
        self.controls['menu_recent'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_recent_inventory'] = _QAction(self.controls['menu_recent'])
        self.controls['menu_recent_inventory'].setObjectName('库存管理台')
        values = {'text': '库存管理台', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_recent_inventory'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_recent_inventory'], values)
        _apply_menu_properties(self.controls['menu_recent_inventory'], values)
        self.controls['menu_recent_inventory'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_recent_tasks'] = _QAction(self.controls['menu_recent'])
        self.controls['menu_recent_tasks'].setObjectName('任务下载中心')
        values = {'text': '任务下载中心', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_recent_tasks'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_recent_tasks'], values)
        _apply_menu_properties(self.controls['menu_recent_tasks'], values)
        self.controls['menu_recent_tasks'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_separator'] = _QAction(self.controls['menu_file'])
        self.controls['menu_separator'].setObjectName('文件菜单分隔线')
        values = {'text': '-', 'shortcut': '', 'separator': True, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_separator'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_separator'], values)
        _apply_menu_properties(self.controls['menu_separator'], values)
        self.controls['menu_separator'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_disabled'] = _QAction(self.controls['menu_file'])
        self.controls['menu_disabled'].setObjectName('禁止操作')
        values = {'text': '禁止操作', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': False, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_disabled'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_disabled'], values)
        _apply_menu_properties(self.controls['menu_disabled'], values)
        self.controls['menu_disabled'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_hidden'] = _QAction(self.controls['menu_file'])
        self.controls['menu_hidden'].setObjectName('隐藏操作')
        values = {'text': '隐藏操作', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': False, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_hidden'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_hidden'], values)
        _apply_menu_properties(self.controls['menu_hidden'], values)
        self.controls['menu_hidden'].setVisible(False)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_exit'] = _QAction(self.controls['menu_file'])
        self.controls['menu_exit'].setObjectName('退出(&X)')
        values = {'text': '退出(&X)', 'shortcut': 'Ctrl+Q', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_exit'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_exit'], values)
        _apply_menu_properties(self.controls['menu_exit'], values)
        self.controls['menu_exit'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_view'] = _QAction(self.controls['menu_bar'])
        self.controls['menu_view'].setObjectName('视图(&V)')
        values = {'text': '视图(&V)', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_view'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_view'], values)
        _apply_menu_properties(self.controls['menu_view'], values)
        self.controls['menu_view'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_details'] = _QAction(self.controls['menu_view'])
        self.controls['menu_details'].setObjectName('显示说明(&G)')
        values = {'text': '显示说明(&G)', 'shortcut': 'Ctrl+G', 'separator': False, 'checkable': True, 'checked': True, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_details'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_details'], values)
        _apply_menu_properties(self.controls['menu_details'], values)
        self.controls['menu_details'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_help'] = _QAction(self.controls['menu_bar'])
        self.controls['menu_help'].setObjectName('帮助(&H)')
        values = {'text': '帮助(&H)', 'shortcut': '', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_help'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_help'], values)
        _apply_menu_properties(self.controls['menu_help'], values)
        self.controls['menu_help'].setVisible(True)
        # 创建菜单项并应用已校验的属性。
        self.controls['menu_about'] = _QAction(self.controls['menu_help'])
        self.controls['menu_about'].setObjectName('关于菜单示例')
        values = {'text': '关于菜单示例', 'shortcut': 'F1', 'separator': False, 'checkable': False, 'checked': False, 'enabled': True, 'visible': True, 'status_tip': ''}
        _apply_widget_properties(self.controls['menu_about'], values, (('text', 'text', '标题'), ('shortcut', None, '快捷键'), ('separator', None, '分隔线'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '选中'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可视'), ('status_tip', 'statusTip', '状态提示')))
        _apply_easy_properties(self.controls['menu_about'], values)
        _apply_menu_properties(self.controls['menu_about'], values)
        self.controls['menu_about'].setVisible(True)
        _arrange_menus(self, self.controls, [('menu_bar', 'main_window', 'menu_bar'), ('menu_file', 'menu_bar', 'menu'), ('menu_new', 'menu_file', 'menu'), ('menu_recent', 'menu_file', 'menu'), ('menu_recent_inventory', 'menu_recent', 'menu'), ('menu_recent_tasks', 'menu_recent', 'menu'), ('menu_separator', 'menu_file', 'menu'), ('menu_disabled', 'menu_file', 'menu'), ('menu_hidden', 'menu_file', 'menu'), ('menu_exit', 'menu_file', 'menu'), ('menu_view', 'menu_bar', 'menu'), ('menu_details', 'menu_view', 'menu'), ('menu_help', 'menu_bar', 'menu'), ('menu_about', 'menu_help', 'menu')])
        self.ensurePolished()
        self.layout().activate()
        self.controls['content_title'].raise_()
        self.controls['detail'].raise_()
        self.controls['eyebrow'].raise_()
        self.controls['title'].raise_()
        self.controls['intro'].raise_()
        self.controls['content'].raise_()
        self.controls['menu_message'].raise_()
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, ({'id': '275a3dfa-414e-4883-87ae-5106e72d86e8', 'control': 'menu_new', 'name': '新建项目(&N)', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_new_clicked', 'arguments': None}, {'id': '3c96d892-c81f-4de8-a156-d8f096abcba3', 'control': 'menu_recent_inventory', 'name': '库存管理台', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_recent_inventory_clicked', 'arguments': None}, {'id': 'c06fa26d-9b23-4c4c-ad49-d030786a843b', 'control': 'menu_recent_tasks', 'name': '任务下载中心', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_recent_tasks_clicked', 'arguments': None}, {'id': '4b2531d1-3345-41e2-983c-354ce3d96adb', 'control': 'menu_exit', 'name': '退出(&X)', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_exit_clicked', 'arguments': None}, {'id': '8469ad2a-ee7d-447a-8bc2-8d2a97948c9c', 'control': 'menu_details', 'name': '显示说明(&G)', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_details_clicked', 'arguments': None}, {'id': 'e3b2b90c-24b0-44c7-aece-c5c7b56a736b', 'control': 'menu_about', 'name': '关于菜单示例', 'key': 'clicked', 'label': '被单击', 'signal': 'triggered', 'event': '', 'handler': 'on_menu_about_clicked', 'arguments': None}), __file__)
        _start_components(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
