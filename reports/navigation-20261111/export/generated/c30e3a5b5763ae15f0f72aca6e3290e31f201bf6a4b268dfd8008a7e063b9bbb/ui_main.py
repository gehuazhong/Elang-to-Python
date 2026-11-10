"""自动生成的界面模块；事件业务请写入 event_handlers，初始化请写入 handlers.py。"""
from __future__ import annotations

from PySide6.QtCore import Qt as _Qt, QObject as _QObject, QTimer as _QTimer
from PySide6.QtGui import QAction as _QAction
from PySide6.QtWidgets import QCalendarWidget as _QCalendarWidget, QCheckBox as _QCheckBox, QComboBox as _QComboBox, QCommandLinkButton as _QCommandLinkButton, QDateEdit as _QDateEdit, QDateTimeEdit as _QDateTimeEdit, QDial as _QDial, QDoubleSpinBox as _QDoubleSpinBox, QFontComboBox as _QFontComboBox, QFrame as _QFrame, QGroupBox as _QGroupBox, QKeySequenceEdit as _QKeySequenceEdit, QLCDNumber as _QLCDNumber, QLabel as _QLabel, QLineEdit as _QLineEdit, QListWidget as _QListWidget, QMainWindow as _QMainWindow, QMenuBar as _QMenuBar, QPlainTextEdit as _QPlainTextEdit, QProgressBar as _QProgressBar, QPushButton as _QPushButton, QRadioButton as _QRadioButton, QScrollBar as _QScrollBar, QSlider as _QSlider, QSpinBox as _QSpinBox, QStatusBar as _QStatusBar, QTableWidget as _QTableWidget, QTextBrowser as _QTextBrowser, QTextEdit as _QTextEdit, QTimeEdit as _QTimeEdit, QToolBar as _QToolBar, QToolButton as _QToolButton, QTreeWidget as _QTreeWidget, QWidget as _QWidget
from .easy_widgets import CommonDialog as _CommonDialog, DrawingBoard as _DrawingBoard, PictureBox as _PictureBox, SelectionTabs as _SelectionTabs, SuperList as _SuperList
from .easy_widgets import apply_easy_properties as _apply_easy_properties, start_components as _start_components, image_asset as _image_asset
from .appearance import apply_appearance as _apply_appearance, apply_window_options as _apply_window_options
from .widget_properties import apply_widget_properties as _apply_widget_properties, apply_content_margins as _apply_content_margins
from .widget_properties import ContainerGroupBox as _QGroupBox, ContainerFrame as _QFrame
from .menus import apply_menu_properties as _apply_menu_properties, arrange_menus as _arrange_menus
from .control_features import apply_control_features as _apply_control_features, finish_group_states as _finish_group_states
from .navigation import apply_navigation_style as _apply_navigation_style, configure_navigation as _configure_navigation
from .property_completion import apply_completed_properties as _apply_completed_properties, finish_completed_properties as _finish_completed_properties
from .advanced_widgets import ADVANCED_FACTORIES as _advanced, content_host as _content_host, apply_advanced_properties as _apply_advanced, arrange_advanced as _arrange_advanced, start_advanced as _start_advanced
from .layout.scaling import ScaleItem as _ScaleItem
from .layout.runtime import WindowScaler as _WindowScaler
from .application import configure_application

class MainWindow(_QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setup_ui()

    def setup_ui(self) -> None:
        self.controls: dict[str, _QObject] = {}
        advanced_records = []
        # 创建窗口并应用已校验的属性。
        self.controls['main_window'] = self
        self.controls['main_window'].setObjectName('主窗口')
        values = {'window_title': '未命名窗口1', 'window_icon': '', 'border_style': 'none', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': True, 'background_color': '#1e1e1e', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('main_window', None, 'root', values))
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_advanced(self.controls['main_window'], values)
        _apply_control_features(self.controls['main_window'], values)
        _apply_menu_properties(self.controls['main_window'], values)
        _apply_completed_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_navigation_style(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(1064, 552)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(_content_host(self.controls['main_window']))
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('central_widget', 'main_window', 'central', values))
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_advanced(self.controls['central_widget'], values)
        _apply_control_features(self.controls['central_widget'], values)
        _apply_menu_properties(self.controls['central_widget'], values)
        _apply_completed_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_navigation_style(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['frame_1'] = _QFrame(_content_host(self.controls['central_widget']))
        self.controls['frame_1'].setObjectName('边框容器1')
        values = {'frame_shape': 'styled', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#101010', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default'}
        advanced_records.append(('frame_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['frame_1'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略')))
        _apply_easy_properties(self.controls['frame_1'], values)
        _apply_advanced(self.controls['frame_1'], values)
        _apply_control_features(self.controls['frame_1'], values)
        _apply_menu_properties(self.controls['frame_1'], values)
        _apply_completed_properties(self.controls['frame_1'], values)
        _apply_appearance(self.controls['frame_1'], values)
        _apply_navigation_style(self.controls['frame_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['frame_1'].setGeometry(176 + offset.x(), 0 + offset.y(), 888, 40)
        _apply_content_margins(self.controls['frame_1'], values)
        self.controls['frame_1'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_1'] = _QPushButton(_content_host(self.controls['frame_1']))
        self.controls['button_1'].setObjectName('按钮1')
        values = {'text': '\\/', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': '', 'navigation_style': 'default', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_1', 'frame_1', 'children', values))
        _apply_widget_properties(self.controls['button_1'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_1'], values)
        _apply_advanced(self.controls['button_1'], values)
        _apply_control_features(self.controls['button_1'], values)
        _apply_menu_properties(self.controls['button_1'], values)
        _apply_completed_properties(self.controls['button_1'], values)
        _apply_appearance(self.controls['button_1'], values)
        _apply_navigation_style(self.controls['button_1'], values)
        offset = _content_host(self.controls['frame_1']).contentsRect().topLeft()
        self.controls['button_1'].setGeometry(848 + offset.x(), 0 + offset.y(), 40, 40)
        _apply_content_margins(self.controls['button_1'], values)
        self.controls['button_1'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_6'] = _QPushButton(_content_host(self.controls['frame_1']))
        self.controls['button_6'].setObjectName('按钮6')
        values = {'text': '-', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': '', 'navigation_style': 'default', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_6', 'frame_1', 'children', values))
        _apply_widget_properties(self.controls['button_6'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_6'], values)
        _apply_advanced(self.controls['button_6'], values)
        _apply_control_features(self.controls['button_6'], values)
        _apply_menu_properties(self.controls['button_6'], values)
        _apply_completed_properties(self.controls['button_6'], values)
        _apply_appearance(self.controls['button_6'], values)
        _apply_navigation_style(self.controls['button_6'], values)
        offset = _content_host(self.controls['frame_1']).contentsRect().topLeft()
        self.controls['button_6'].setGeometry(808 + offset.x(), 0 + offset.y(), 40, 40)
        _apply_content_margins(self.controls['button_6'], values)
        self.controls['button_6'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['frame_2'] = _QFrame(_content_host(self.controls['central_widget']))
        self.controls['frame_2'].setObjectName('边框容器2')
        values = {'frame_shape': 'panel', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#3d3d3d', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default'}
        advanced_records.append(('frame_2', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['frame_2'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略')))
        _apply_easy_properties(self.controls['frame_2'], values)
        _apply_advanced(self.controls['frame_2'], values)
        _apply_control_features(self.controls['frame_2'], values)
        _apply_menu_properties(self.controls['frame_2'], values)
        _apply_completed_properties(self.controls['frame_2'], values)
        _apply_appearance(self.controls['frame_2'], values)
        _apply_navigation_style(self.controls['frame_2'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['frame_2'].setGeometry(0 + offset.x(), 0 + offset.y(), 176, 552)
        _apply_content_margins(self.controls['frame_2'], values)
        self.controls['frame_2'].setVisible(True)
        # 创建图片框并应用已校验的属性。
        self.controls['picture_box_1'] = _PictureBox(_content_host(self.controls['frame_2']))
        self.controls['picture_box_1'].setObjectName('图片框1')
        values = {'image': '', 'image_mode': 'stretch', 'border': True, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'image_alignment': 'center', 'smooth_scaling': True, 'image_opacity': 1.0}
        values['image'] = _image_asset(__file__, 'assets/4d8ae6fe75ce70bd6e4f6b0838d071fa1a9a624dbdf5e4cce0fd420ee57250c8.png')
        advanced_records.append(('picture_box_1', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['picture_box_1'], values, (('image', None, '图片'), ('image_mode', None, '显示方式'), ('border', None, '显示边框'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('image_alignment', None, '图片对齐'), ('smooth_scaling', None, '平滑缩放图片'), ('image_opacity', None, '图片不透明度')))
        _apply_easy_properties(self.controls['picture_box_1'], values)
        _apply_advanced(self.controls['picture_box_1'], values)
        _apply_control_features(self.controls['picture_box_1'], values)
        _apply_menu_properties(self.controls['picture_box_1'], values)
        _apply_completed_properties(self.controls['picture_box_1'], values)
        _apply_appearance(self.controls['picture_box_1'], values)
        _apply_navigation_style(self.controls['picture_box_1'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['picture_box_1'].setGeometry(0 + offset.x(), 0 + offset.y(), 176, 128)
        _apply_content_margins(self.controls['picture_box_1'], values)
        self.controls['picture_box_1'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['label_1'] = _QLabel(_content_host(self.controls['frame_2']))
        self.controls['label_1'].setObjectName('标签1')
        self.controls['label_1'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '523 Weibo Tools', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '微软雅黑', 'font_size': 14, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'center', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'text_format': 'plain', 'text_interaction': 'links', 'open_external_links': False, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0}
        advanced_records.append(('label_1', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['label_1'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('text_format', 'textFormat', '文本格式'), ('text_interaction', 'textInteractionFlags', '文本交互'), ('open_external_links', 'openExternalLinks', '使用外部程序打开链接'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度')))
        _apply_easy_properties(self.controls['label_1'], values)
        _apply_advanced(self.controls['label_1'], values)
        _apply_control_features(self.controls['label_1'], values)
        _apply_menu_properties(self.controls['label_1'], values)
        _apply_completed_properties(self.controls['label_1'], values)
        _apply_appearance(self.controls['label_1'], values)
        _apply_navigation_style(self.controls['label_1'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['label_1'].setGeometry(0 + offset.x(), 128 + offset.y(), 176, 32)
        _apply_content_margins(self.controls['label_1'], values)
        self.controls['label_1'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_2'] = _QPushButton(_content_host(self.controls['frame_2']))
        self.controls['button_2'].setObjectName('按钮2')
        values = {'text': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': 'tab_page_1', 'navigation_style': 'sidebar', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'pointing_hand', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_2', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['button_2'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_2'], values)
        _apply_advanced(self.controls['button_2'], values)
        _apply_control_features(self.controls['button_2'], values)
        _apply_menu_properties(self.controls['button_2'], values)
        _apply_completed_properties(self.controls['button_2'], values)
        _apply_appearance(self.controls['button_2'], values)
        _apply_navigation_style(self.controls['button_2'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['button_2'].setGeometry(0 + offset.x(), 168 + offset.y(), 176, 40)
        _apply_content_margins(self.controls['button_2'], values)
        self.controls['button_2'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_3'] = _QPushButton(_content_host(self.controls['frame_2']))
        self.controls['button_3'].setObjectName('按钮3')
        values = {'text': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': 'tab_page_2', 'navigation_style': 'sidebar', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'pointing_hand', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_3', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['button_3'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_3'], values)
        _apply_advanced(self.controls['button_3'], values)
        _apply_control_features(self.controls['button_3'], values)
        _apply_menu_properties(self.controls['button_3'], values)
        _apply_completed_properties(self.controls['button_3'], values)
        _apply_appearance(self.controls['button_3'], values)
        _apply_navigation_style(self.controls['button_3'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['button_3'].setGeometry(0 + offset.x(), 212 + offset.y(), 176, 40)
        _apply_content_margins(self.controls['button_3'], values)
        self.controls['button_3'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_4'] = _QPushButton(_content_host(self.controls['frame_2']))
        self.controls['button_4'].setObjectName('按钮4')
        values = {'text': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': 'tab_page_3', 'navigation_style': 'sidebar', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'pointing_hand', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_4', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['button_4'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_4'], values)
        _apply_advanced(self.controls['button_4'], values)
        _apply_control_features(self.controls['button_4'], values)
        _apply_menu_properties(self.controls['button_4'], values)
        _apply_completed_properties(self.controls['button_4'], values)
        _apply_appearance(self.controls['button_4'], values)
        _apply_navigation_style(self.controls['button_4'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['button_4'].setGeometry(0 + offset.x(), 256 + offset.y(), 176, 40)
        _apply_content_margins(self.controls['button_4'], values)
        self.controls['button_4'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_5'] = _QPushButton(_content_host(self.controls['frame_2']))
        self.controls['button_5'].setObjectName('按钮5')
        values = {'text': '4', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': '', 'navigation_style': 'default', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_5', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['button_5'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_5'], values)
        _apply_advanced(self.controls['button_5'], values)
        _apply_control_features(self.controls['button_5'], values)
        _apply_menu_properties(self.controls['button_5'], values)
        _apply_completed_properties(self.controls['button_5'], values)
        _apply_appearance(self.controls['button_5'], values)
        _apply_navigation_style(self.controls['button_5'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['button_5'].setGeometry(0 + offset.x(), 299 + offset.y(), 176, 40)
        _apply_content_margins(self.controls['button_5'], values)
        self.controls['button_5'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['button_7'] = _QPushButton(_content_host(self.controls['frame_2']))
        self.controls['button_7'].setObjectName('按钮7')
        values = {'text': '5', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': True, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100, 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'navigation_page': '', 'navigation_style': 'default', 'icon': '', 'icon_width': 0, 'icon_height': 0, 'shortcut': '', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'auto_default': False, 'default_button': False}
        advanced_records.append(('button_7', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['button_7'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('navigation_page', None, '关联页面'), ('navigation_style', None, '导航样式'), ('icon', None, '图标'), ('icon_width', None, '图标宽度'), ('icon_height', None, '图标高度'), ('shortcut', None, '快捷键'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('auto_default', 'autoDefault', '获得焦点时作为默认按钮'), ('default_button', 'default', '默认按钮')))
        _apply_easy_properties(self.controls['button_7'], values)
        _apply_advanced(self.controls['button_7'], values)
        _apply_control_features(self.controls['button_7'], values)
        _apply_menu_properties(self.controls['button_7'], values)
        _apply_completed_properties(self.controls['button_7'], values)
        _apply_appearance(self.controls['button_7'], values)
        _apply_navigation_style(self.controls['button_7'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['button_7'].setGeometry(0 + offset.x(), 360 + offset.y(), 176, 40)
        _apply_content_margins(self.controls['button_7'], values)
        self.controls['button_7'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['label_2'] = _QLabel(_content_host(self.controls['frame_2']))
        self.controls['label_2'].setObjectName('标签2')
        self.controls['label_2'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': 'Version 0.1', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '微软雅黑', 'font_size': 12, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'center', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'text_format': 'plain', 'text_interaction': 'links', 'open_external_links': False, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0}
        advanced_records.append(('label_2', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['label_2'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('text_format', 'textFormat', '文本格式'), ('text_interaction', 'textInteractionFlags', '文本交互'), ('open_external_links', 'openExternalLinks', '使用外部程序打开链接'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度')))
        _apply_easy_properties(self.controls['label_2'], values)
        _apply_advanced(self.controls['label_2'], values)
        _apply_control_features(self.controls['label_2'], values)
        _apply_menu_properties(self.controls['label_2'], values)
        _apply_completed_properties(self.controls['label_2'], values)
        _apply_appearance(self.controls['label_2'], values)
        _apply_navigation_style(self.controls['label_2'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['label_2'].setGeometry(8 + offset.x(), 512 + offset.y(), 160, 32)
        _apply_content_margins(self.controls['label_2'], values)
        self.controls['label_2'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['label_3'] = _QLabel(_content_host(self.controls['frame_2']))
        self.controls['label_3'].setObjectName('标签3')
        self.controls['label_3'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '用户中心', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'center', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'text_format': 'plain', 'text_interaction': 'links', 'open_external_links': False, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0}
        advanced_records.append(('label_3', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['label_3'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('text_format', 'textFormat', '文本格式'), ('text_interaction', 'textInteractionFlags', '文本交互'), ('open_external_links', 'openExternalLinks', '使用外部程序打开链接'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度')))
        _apply_easy_properties(self.controls['label_3'], values)
        _apply_advanced(self.controls['label_3'], values)
        _apply_control_features(self.controls['label_3'], values)
        _apply_menu_properties(self.controls['label_3'], values)
        _apply_completed_properties(self.controls['label_3'], values)
        _apply_appearance(self.controls['label_3'], values)
        _apply_navigation_style(self.controls['label_3'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['label_3'].setGeometry(48 + offset.x(), 168 + offset.y(), 128, 40)
        _apply_content_margins(self.controls['label_3'], values)
        self.controls['label_3'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['label_4'] = _QLabel(_content_host(self.controls['frame_2']))
        self.controls['label_4'].setObjectName('标签4')
        self.controls['label_4'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '任务中心', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'center', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'text_format': 'plain', 'text_interaction': 'links', 'open_external_links': False, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0}
        advanced_records.append(('label_4', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['label_4'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('text_format', 'textFormat', '文本格式'), ('text_interaction', 'textInteractionFlags', '文本交互'), ('open_external_links', 'openExternalLinks', '使用外部程序打开链接'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度')))
        _apply_easy_properties(self.controls['label_4'], values)
        _apply_advanced(self.controls['label_4'], values)
        _apply_control_features(self.controls['label_4'], values)
        _apply_menu_properties(self.controls['label_4'], values)
        _apply_completed_properties(self.controls['label_4'], values)
        _apply_appearance(self.controls['label_4'], values)
        _apply_navigation_style(self.controls['label_4'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['label_4'].setGeometry(48 + offset.x(), 212 + offset.y(), 128, 40)
        _apply_content_margins(self.controls['label_4'], values)
        self.controls['label_4'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['label_5'] = _QLabel(_content_host(self.controls['frame_2']))
        self.controls['label_5'].setObjectName('标签5')
        self.controls['label_5'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '软件设置', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'center', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'text_format': 'plain', 'text_interaction': 'links', 'open_external_links': False, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0}
        advanced_records.append(('label_5', 'frame_2', 'children', values))
        _apply_widget_properties(self.controls['label_5'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('text_format', 'textFormat', '文本格式'), ('text_interaction', 'textInteractionFlags', '文本交互'), ('open_external_links', 'openExternalLinks', '使用外部程序打开链接'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度')))
        _apply_easy_properties(self.controls['label_5'], values)
        _apply_advanced(self.controls['label_5'], values)
        _apply_control_features(self.controls['label_5'], values)
        _apply_menu_properties(self.controls['label_5'], values)
        _apply_completed_properties(self.controls['label_5'], values)
        _apply_appearance(self.controls['label_5'], values)
        _apply_navigation_style(self.controls['label_5'], values)
        offset = _content_host(self.controls['frame_2']).contentsRect().topLeft()
        self.controls['label_5'].setGeometry(48 + offset.x(), 256 + offset.y(), 128, 40)
        _apply_content_margins(self.controls['label_5'], values)
        self.controls['label_5'].setVisible(True)
        # 创建选择夹并应用已校验的属性。
        self.controls['tab_widget_1'] = _SelectionTabs(_content_host(self.controls['central_widget']))
        self.controls['tab_widget_1'].setObjectName('选择夹1')
        values = {'current_index': 0, 'tab_position': 'top', 'header_visible': False, 'tab_bar_auto_hide': False, 'tab_bar_size': 30, 'tab_shape': 'rounded', 'expanding': False, 'uses_scroll_buttons': True, 'elide_mode': 'right', 'document_mode': False, 'draw_base': True, 'pane_border': True, 'movable': False, 'tabs_closable': False, 'icon_width': 16, 'icon_height': 16, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default'}
        advanced_records.append(('tab_widget_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['tab_widget_1'], values, (('current_index', None, '当前页'), ('tab_position', None, '表头朝向'), ('header_visible', None, '显示表头'), ('tab_bar_auto_hide', None, '单页自动隐藏表头'), ('tab_bar_size', None, '表头厚度'), ('tab_shape', None, '页签形状'), ('expanding', None, '页签均分表头'), ('uses_scroll_buttons', None, '显示页签滚动按钮'), ('elide_mode', None, '长标题省略方式'), ('document_mode', None, '文档模式'), ('draw_base', None, '绘制表头基线'), ('pane_border', None, '显示页面边框'), ('movable', None, '允许拖动页签排序'), ('tabs_closable', None, '显示页签关闭按钮'), ('icon_width', None, '页签图标宽度'), ('icon_height', None, '页签图标高度'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略')))
        _apply_easy_properties(self.controls['tab_widget_1'], values)
        _apply_advanced(self.controls['tab_widget_1'], values)
        _apply_control_features(self.controls['tab_widget_1'], values)
        _apply_menu_properties(self.controls['tab_widget_1'], values)
        _apply_completed_properties(self.controls['tab_widget_1'], values)
        _apply_appearance(self.controls['tab_widget_1'], values)
        _apply_navigation_style(self.controls['tab_widget_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['tab_widget_1'].setGeometry(176 + offset.x(), 40 + offset.y(), 888, 512)
        _apply_content_margins(self.controls['tab_widget_1'], values)
        self.controls['tab_widget_1'].setVisible(True)
        # 创建选择夹页面并应用已校验的属性。
        self.controls['tab_page_1'] = _QWidget(_content_host(self.controls['tab_widget_1']))
        self.controls['tab_page_1'].setObjectName('页面1')
        values = {'text': '用户中心', 'tab_icon': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('tab_page_1', 'tab_widget_1', 'pages', values))
        _apply_widget_properties(self.controls['tab_page_1'], values, (('text', None, '页标题'), ('tab_icon', None, '页签图标'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['tab_page_1'], values)
        _apply_advanced(self.controls['tab_page_1'], values)
        _apply_control_features(self.controls['tab_page_1'], values)
        _apply_menu_properties(self.controls['tab_page_1'], values)
        _apply_completed_properties(self.controls['tab_page_1'], values)
        _apply_appearance(self.controls['tab_page_1'], values)
        _apply_navigation_style(self.controls['tab_page_1'], values)
        _apply_content_margins(self.controls['tab_page_1'], values)
        self.controls['tab_page_1'].setProperty('page_visible', True)
        self.controls['tab_page_1'].setVisible(True)
        # 创建画板并应用已校验的属性。
        self.controls['drawing_board_1'] = _DrawingBoard(_content_host(self.controls['tab_page_1']))
        self.controls['drawing_board_1'].setObjectName('画板1')
        values = {'pen_color': '#20252b', 'pen_width': 2, 'paper_color': '#ffffff', 'drawing_enabled': True, 'image': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1, 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': '', 'size_policy_horizontal': 'default', 'size_policy_vertical': 'default', 'border': True, 'antialiasing': True, 'pen_style': 'solid'}
        advanced_records.append(('drawing_board_1', 'tab_page_1', 'children', values))
        _apply_widget_properties(self.controls['drawing_board_1'], values, (('pen_color', None, '画笔颜色'), ('pen_width', None, '画笔宽度'), ('paper_color', None, '画板底色'), ('drawing_enabled', None, '允许鼠标绘画'), ('image', None, '底图'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式'), ('size_policy_horizontal', None, '水平尺寸策略'), ('size_policy_vertical', None, '垂直尺寸策略'), ('border', None, '显示画板边框'), ('antialiasing', None, '笔迹抗锯齿'), ('pen_style', None, '画笔线型')))
        _apply_easy_properties(self.controls['drawing_board_1'], values)
        _apply_advanced(self.controls['drawing_board_1'], values)
        _apply_control_features(self.controls['drawing_board_1'], values)
        _apply_menu_properties(self.controls['drawing_board_1'], values)
        _apply_completed_properties(self.controls['drawing_board_1'], values)
        _apply_appearance(self.controls['drawing_board_1'], values)
        _apply_navigation_style(self.controls['drawing_board_1'], values)
        offset = _content_host(self.controls['tab_page_1']).contentsRect().topLeft()
        self.controls['drawing_board_1'].setGeometry(0 + offset.x(), 0 + offset.y(), 886, 480)
        _apply_content_margins(self.controls['drawing_board_1'], values)
        self.controls['drawing_board_1'].setVisible(True)
        # 创建选择夹页面并应用已校验的属性。
        self.controls['tab_page_2'] = _QWidget(_content_host(self.controls['tab_widget_1']))
        self.controls['tab_page_2'].setObjectName('页面2')
        values = {'text': '任务中心', 'tab_icon': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('tab_page_2', 'tab_widget_1', 'pages', values))
        _apply_widget_properties(self.controls['tab_page_2'], values, (('text', None, '页标题'), ('tab_icon', None, '页签图标'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['tab_page_2'], values)
        _apply_advanced(self.controls['tab_page_2'], values)
        _apply_control_features(self.controls['tab_page_2'], values)
        _apply_menu_properties(self.controls['tab_page_2'], values)
        _apply_completed_properties(self.controls['tab_page_2'], values)
        _apply_appearance(self.controls['tab_page_2'], values)
        _apply_navigation_style(self.controls['tab_page_2'], values)
        _apply_content_margins(self.controls['tab_page_2'], values)
        self.controls['tab_page_2'].setProperty('page_visible', True)
        self.controls['tab_page_2'].setVisible(True)
        # 创建选择夹页面并应用已校验的属性。
        self.controls['tab_page_3'] = _QWidget(_content_host(self.controls['tab_widget_1']))
        self.controls['tab_page_3'].setObjectName('页面3')
        values = {'text': '软件设置', 'tab_icon': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('tab_page_3', 'tab_widget_1', 'pages', values))
        _apply_widget_properties(self.controls['tab_page_3'], values, (('text', None, '页标题'), ('tab_icon', None, '页签图标'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['tab_page_3'], values)
        _apply_advanced(self.controls['tab_page_3'], values)
        _apply_control_features(self.controls['tab_page_3'], values)
        _apply_menu_properties(self.controls['tab_page_3'], values)
        _apply_completed_properties(self.controls['tab_page_3'], values)
        _apply_appearance(self.controls['tab_page_3'], values)
        _apply_navigation_style(self.controls['tab_page_3'], values)
        _apply_content_margins(self.controls['tab_page_3'], values)
        self.controls['tab_page_3'].setProperty('page_visible', True)
        self.controls['tab_page_3'].setVisible(True)
        # 创建选择夹页面并应用已校验的属性。
        self.controls['tab_page_4'] = _QWidget(_content_host(self.controls['tab_widget_1']))
        self.controls['tab_page_4'].setObjectName('页面4')
        values = {'text': '第4页', 'tab_icon': '', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'cursor_shape': 'default', 'focus_policy': 'default', 'mouse_tracking': False, 'accessible_name': '', 'accessible_description': '', 'whats_this': '', 'tool_tip_duration': -1, 'style_sheet': ''}
        advanced_records.append(('tab_page_4', 'tab_widget_1', 'pages', values))
        _apply_widget_properties(self.controls['tab_page_4'], values, (('text', None, '页标题'), ('tab_icon', None, '页签图标'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('cursor_shape', None, '鼠标指针'), ('focus_policy', None, '键盘焦点方式'), ('mouse_tracking', 'mouseTracking', '跟踪鼠标移动'), ('accessible_name', 'accessibleName', '无障碍名称'), ('accessible_description', 'accessibleDescription', '无障碍说明'), ('whats_this', 'whatsThis', '帮助说明'), ('tool_tip_duration', 'toolTipDuration', '提示显示毫秒'), ('style_sheet', None, '自定义样式')))
        _apply_easy_properties(self.controls['tab_page_4'], values)
        _apply_advanced(self.controls['tab_page_4'], values)
        _apply_control_features(self.controls['tab_page_4'], values)
        _apply_menu_properties(self.controls['tab_page_4'], values)
        _apply_completed_properties(self.controls['tab_page_4'], values)
        _apply_appearance(self.controls['tab_page_4'], values)
        _apply_navigation_style(self.controls['tab_page_4'], values)
        _apply_content_margins(self.controls['tab_page_4'], values)
        self.controls['tab_page_4'].setProperty('page_visible', True)
        self.controls['tab_page_4'].setVisible(True)
        self.controls['tab_widget_1'].set_pages([(self.controls['tab_page_1'], '用户中心'), (self.controls['tab_page_2'], '任务中心'), (self.controls['tab_page_3'], '软件设置'), (self.controls['tab_page_4'], '第4页')], 0)
        _arrange_menus(self, self.controls, [])
        _finish_group_states(self.controls, [])
        _arrange_advanced(self, self.controls, advanced_records)
        _finish_completed_properties(self.controls)
        _configure_navigation(self.controls, advanced_records)
        self.ensurePolished()
        self.layout().activate()
        self.controls['frame_1'].raise_()
        self.controls['frame_2'].raise_()
        self.controls['tab_widget_1'].raise_()
        self.controls['button_1'].raise_()
        self.controls['button_6'].raise_()
        self.controls['drawing_board_1'].raise_()
        self.controls['picture_box_1'].raise_()
        self.controls['label_1'].raise_()
        self.controls['button_5'].raise_()
        self.controls['button_7'].raise_()
        self.controls['label_2'].raise_()
        self.controls['label_3'].raise_()
        self.controls['label_4'].raise_()
        self.controls['label_5'].raise_()
        self.controls['button_2'].raise_()
        self.controls['button_3'].raise_()
        self.controls['button_4'].raise_()
        # 保留设计基准，每次窗口拉伸均重新计算，字号保持用户设置。
        scale_items = (
            _ScaleItem('049f45f5-8afc-43b0-ad33-83d896876606', '869f220d-d038-4c8f-8b9d-f00b976d764d', 'central', None, (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('05a73568-0439-4762-a412-64042d2d3ff4', '049f45f5-8afc-43b0-ad33-83d896876606', 'children', (176, 0, 888, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('6d8524a7-e56c-4c16-aa81-76890f920382', '05a73568-0439-4762-a412-64042d2d3ff4', 'children', (848, 0, 40, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('80fb6999-1a5b-4773-a952-7874d012d18f', '05a73568-0439-4762-a412-64042d2d3ff4', 'children', (808, 0, 40, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('59502ccb-c5ab-43a1-b23d-124d8cd5f62d', '049f45f5-8afc-43b0-ad33-83d896876606', 'children', (176, 40, 888, 512), (0, 0, 0, 0), (64, 64), (1, 30, 1, 1)),
            _ScaleItem('313ae13b-31bf-44c2-91d0-fb56e20f05d3', '59502ccb-c5ab-43a1-b23d-124d8cd5f62d', 'pages', None, (0, 0, 0, 0), (1, 1), (1, 1, 1, 1)),
            _ScaleItem('683f4de9-91b7-4473-928d-a698e5172499', '313ae13b-31bf-44c2-91d0-fb56e20f05d3', 'children', (0, 0, 886, 480), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('4d08204e-c476-410c-94a6-0480b3549e7a', '59502ccb-c5ab-43a1-b23d-124d8cd5f62d', 'pages', None, (0, 0, 0, 0), (1, 1), (1, 1, 1, 1)),
            _ScaleItem('5584111c-1511-45d4-9ba3-bb165496157a', '59502ccb-c5ab-43a1-b23d-124d8cd5f62d', 'pages', None, (0, 0, 0, 0), (1, 1), (1, 1, 1, 1)),
            _ScaleItem('5afb1c89-a327-4ecb-b2d1-fc08038461b9', '59502ccb-c5ab-43a1-b23d-124d8cd5f62d', 'pages', None, (0, 0, 0, 0), (1, 1), (1, 1, 1, 1)),
            _ScaleItem('81f794a3-c5b2-4311-9017-73d41b02849b', '049f45f5-8afc-43b0-ad33-83d896876606', 'children', (0, 0, 176, 552), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('0dab4470-0dcc-4a38-be79-080556716d61', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (48, 256, 128, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('31aaa76f-c4a4-4a68-80b8-1e65662cbd1e', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (48, 212, 128, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('72f5fd5a-5d89-4a4c-80e9-e8e1d67f1ac4', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (8, 512, 160, 32), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('9ab6d819-5724-47f5-b654-6ec48b7e5fab', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 168, 176, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('9eb031fc-38b2-49d3-afd9-48a061fa4e31', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 128, 176, 32), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('af6dfb4a-3cdc-45c7-b448-2dabc74e6f63', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 360, 176, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('b0c73192-2e52-4586-814b-52b9ea277563', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (48, 168, 128, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('bf736482-fb9c-4269-b499-851813da592d', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 212, 176, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('caa24dee-0c44-42c1-99ef-4606c7e6026e', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 256, 176, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('cb7fbcde-a1b0-4b7f-9999-c5f3b06f26ef', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 299, 176, 40), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
            _ScaleItem('e1f5ca14-fde5-4449-8f73-06230b9232a5', '81f794a3-c5b2-4311-9017-73d41b02849b', 'children', (0, 0, 176, 128), (0, 0, 0, 0), (1, 1), (1, 30, 1, 1)),
        )
        scale_controls = {
            '049f45f5-8afc-43b0-ad33-83d896876606': self.controls['central_widget'],
            '05a73568-0439-4762-a412-64042d2d3ff4': self.controls['frame_1'],
            '6d8524a7-e56c-4c16-aa81-76890f920382': self.controls['button_1'],
            '80fb6999-1a5b-4773-a952-7874d012d18f': self.controls['button_6'],
            '59502ccb-c5ab-43a1-b23d-124d8cd5f62d': self.controls['tab_widget_1'],
            '313ae13b-31bf-44c2-91d0-fb56e20f05d3': self.controls['tab_page_1'],
            '683f4de9-91b7-4473-928d-a698e5172499': self.controls['drawing_board_1'],
            '4d08204e-c476-410c-94a6-0480b3549e7a': self.controls['tab_page_4'],
            '5584111c-1511-45d4-9ba3-bb165496157a': self.controls['tab_page_3'],
            '5afb1c89-a327-4ecb-b2d1-fc08038461b9': self.controls['tab_page_2'],
            '81f794a3-c5b2-4311-9017-73d41b02849b': self.controls['frame_2'],
            '0dab4470-0dcc-4a38-be79-080556716d61': self.controls['label_5'],
            '31aaa76f-c4a4-4a68-80b8-1e65662cbd1e': self.controls['label_4'],
            '72f5fd5a-5d89-4a4c-80e9-e8e1d67f1ac4': self.controls['label_2'],
            '9ab6d819-5724-47f5-b654-6ec48b7e5fab': self.controls['button_2'],
            '9eb031fc-38b2-49d3-afd9-48a061fa4e31': self.controls['label_1'],
            'af6dfb4a-3cdc-45c7-b448-2dabc74e6f63': self.controls['button_7'],
            'b0c73192-2e52-4586-814b-52b9ea277563': self.controls['label_3'],
            'bf736482-fb9c-4269-b499-851813da592d': self.controls['button_3'],
            'caa24dee-0c44-42c1-99ef-4606c7e6026e': self.controls['button_4'],
            'cb7fbcde-a1b0-4b7f-9999-c5f3b06f26ef': self.controls['button_5'],
            'e1f5ca14-fde5-4449-8f73-06230b9232a5': self.controls['picture_box_1'],
        }
        self._component_scaler = _WindowScaler(self, self.centralWidget(), (1064, 552), scale_items, scale_controls)
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, (), __file__)
        _start_components(self.controls)
        _start_advanced(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
