"""自动生成的界面模块；事件业务请写入 event_handlers，初始化请写入 handlers.py。"""
from __future__ import annotations

from PySide6.QtCore import Qt as _Qt, QObject as _QObject, QTimer as _QTimer
from PySide6.QtWidgets import QCalendarWidget as _QCalendarWidget, QCheckBox as _QCheckBox, QComboBox as _QComboBox, QCommandLinkButton as _QCommandLinkButton, QDateEdit as _QDateEdit, QDateTimeEdit as _QDateTimeEdit, QDial as _QDial, QDoubleSpinBox as _QDoubleSpinBox, QFrame as _QFrame, QGroupBox as _QGroupBox, QLCDNumber as _QLCDNumber, QLabel as _QLabel, QLineEdit as _QLineEdit, QListWidget as _QListWidget, QMainWindow as _QMainWindow, QPlainTextEdit as _QPlainTextEdit, QProgressBar as _QProgressBar, QPushButton as _QPushButton, QRadioButton as _QRadioButton, QScrollBar as _QScrollBar, QSlider as _QSlider, QSpinBox as _QSpinBox, QStatusBar as _QStatusBar, QTableWidget as _QTableWidget, QTimeEdit as _QTimeEdit, QToolBar as _QToolBar, QToolButton as _QToolButton, QTreeWidget as _QTreeWidget, QWidget as _QWidget
from .easy_widgets import CommonDialog as _CommonDialog, DrawingBoard as _DrawingBoard, PictureBox as _PictureBox, SelectionTabs as _SelectionTabs, SuperList as _SuperList
from .easy_widgets import apply_easy_properties as _apply_easy_properties, start_components as _start_components, image_asset as _image_asset
from .appearance import apply_appearance as _apply_appearance, apply_window_options as _apply_window_options
from .widget_properties import apply_widget_properties as _apply_widget_properties, apply_content_margins as _apply_content_margins
from .widget_properties import ContainerGroupBox as _QGroupBox, ContainerFrame as _QFrame
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
        values = {'window_title': '青禾 · 库存管理台', 'window_icon': '', 'border_style': 'standard', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': False, 'background_color': '#f5f6f2', 'foreground_color': '#253332', 'font_family': 'Microsoft YaHei UI', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(1040, 680)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(self.controls['main_window'])
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '#f5f6f2', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['sidebar'] = _QFrame(self.controls['central_widget'])
        self.controls['sidebar'].setObjectName('侧栏')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#e7eee7', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['sidebar'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['sidebar'], values)
        _apply_appearance(self.controls['sidebar'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['sidebar'].setGeometry(0 + offset.x(), 0 + offset.y(), 196, 680)
        _apply_content_margins(self.controls['sidebar'], values)
        self.controls['sidebar'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand'] = _QLabel(self.controls['sidebar'])
        self.controls['brand'].setObjectName('青禾仓库')
        self.controls['brand'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '青禾仓库', 'background_color': '', 'foreground_color': '#285c4b', 'font_family': '', 'font_size': 22, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand'], values)
        _apply_appearance(self.controls['brand'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['brand'].setGeometry(24 + offset.x(), 32 + offset.y(), 150, 38)
        _apply_content_margins(self.controls['brand'], values)
        self.controls['brand'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand_caption'] = _QLabel(self.controls['sidebar'])
        self.controls['brand_caption'].setObjectName('小团队的库存工作台')
        self.controls['brand_caption'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '小团队的库存工作台', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand_caption'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand_caption'], values)
        _apply_appearance(self.controls['brand_caption'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['brand_caption'].setGeometry(24 + offset.x(), 76 + offset.y(), 156, 28)
        _apply_content_margins(self.controls['brand_caption'], values)
        self.controls['brand_caption'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['nav_active'] = _QFrame(self.controls['sidebar'])
        self.controls['nav_active'].setObjectName('当前模块')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#285c4b', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['nav_active'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['nav_active'], values)
        _apply_appearance(self.controls['nav_active'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['nav_active'].setGeometry(16 + offset.x(), 138 + offset.y(), 164, 42)
        _apply_content_margins(self.controls['nav_active'], values)
        self.controls['nav_active'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['nav_text'] = _QLabel(self.controls['nav_active'])
        self.controls['nav_text'].setObjectName('01   库存总览')
        self.controls['nav_text'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '01   库存总览', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 10, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['nav_text'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['nav_text'], values)
        _apply_appearance(self.controls['nav_text'], values)
        offset = self.controls['nav_active'].contentsRect().topLeft()
        self.controls['nav_text'].setGeometry(16 + offset.x(), 5 + offset.y(), 145, 32)
        _apply_content_margins(self.controls['nav_text'], values)
        self.controls['nav_text'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['warehouse_label'] = _QLabel(self.controls['sidebar'])
        self.controls['warehouse_label'].setObjectName('当前仓库')
        self.controls['warehouse_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '当前仓库', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['warehouse_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['warehouse_label'], values)
        _apply_appearance(self.controls['warehouse_label'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['warehouse_label'].setGeometry(24 + offset.x(), 220 + offset.y(), 140, 28)
        _apply_content_margins(self.controls['warehouse_label'], values)
        self.controls['warehouse_label'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['warehouse'] = _QLabel(self.controls['sidebar'])
        self.controls['warehouse'].setObjectName('杭州 · 一号仓')
        self.controls['warehouse'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '杭州 · 一号仓', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 10, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['warehouse'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['warehouse'], values)
        _apply_appearance(self.controls['warehouse'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['warehouse'].setGeometry(24 + offset.x(), 252 + offset.y(), 154, 28)
        _apply_content_margins(self.controls['warehouse'], values)
        self.controls['warehouse'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['warehouse_note'] = _QLabel(self.controls['sidebar'])
        self.controls['warehouse_note'].setObjectName('办公用品与设备')
        self.controls['warehouse_note'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '办公用品与设备\n统一登记，按需领用。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': True, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['warehouse_note'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['warehouse_note'], values)
        _apply_appearance(self.controls['warehouse_note'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['warehouse_note'].setGeometry(24 + offset.x(), 296 + offset.y(), 148, 80)
        _apply_content_margins(self.controls['warehouse_note'], values)
        self.controls['warehouse_note'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['sidebar_footer'] = _QLabel(self.controls['sidebar'])
        self.controls['sidebar_footer'].setObjectName('本地示例数据')
        self.controls['sidebar_footer'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '本地示例数据\n2026 / 11 / 07', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['sidebar_footer'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['sidebar_footer'], values)
        _apply_appearance(self.controls['sidebar_footer'], values)
        offset = self.controls['sidebar'].contentsRect().topLeft()
        self.controls['sidebar_footer'].setGeometry(24 + offset.x(), 598 + offset.y(), 148, 52)
        _apply_content_margins(self.controls['sidebar_footer'], values)
        self.controls['sidebar_footer'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['eyebrow'] = _QLabel(self.controls['central_widget'])
        self.controls['eyebrow'].setObjectName('WAREHOUSE / OVERVIEW')
        self.controls['eyebrow'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': 'WAREHOUSE / OVERVIEW', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['eyebrow'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['eyebrow'], values)
        _apply_appearance(self.controls['eyebrow'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['eyebrow'].setGeometry(228 + offset.x(), 22 + offset.y(), 510, 28)
        _apply_content_margins(self.controls['eyebrow'], values)
        self.controls['eyebrow'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['title'] = _QLabel(self.controls['central_widget'])
        self.controls['title'].setObjectName('库存总览')
        self.controls['title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '库存总览', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 24, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['title'], values)
        _apply_appearance(self.controls['title'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['title'].setGeometry(228 + offset.x(), 52 + offset.y(), 510, 44)
        _apply_content_margins(self.controls['title'], values)
        self.controls['title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['subtitle'] = _QLabel(self.controls['central_widget'])
        self.controls['subtitle'].setObjectName('快速找到物品，及时补足低库存。')
        self.controls['subtitle'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '快速找到物品，及时补足低库存。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['subtitle'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['subtitle'], values)
        _apply_appearance(self.controls['subtitle'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['subtitle'].setGeometry(228 + offset.x(), 103 + offset.y(), 720, 28)
        _apply_content_margins(self.controls['subtitle'], values)
        self.controls['subtitle'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['sku_panel'] = _QFrame(self.controls['central_widget'])
        self.controls['sku_panel'].setObjectName('物品种类')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['sku_panel'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['sku_panel'], values)
        _apply_appearance(self.controls['sku_panel'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['sku_panel'].setGeometry(228 + offset.x(), 150 + offset.y(), 246, 98)
        _apply_content_margins(self.controls['sku_panel'], values)
        self.controls['sku_panel'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['sku_label'] = _QLabel(self.controls['sku_panel'])
        self.controls['sku_label'].setObjectName('物品种类2')
        self.controls['sku_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '物品种类', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['sku_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['sku_label'], values)
        _apply_appearance(self.controls['sku_label'], values)
        offset = self.controls['sku_panel'].contentsRect().topLeft()
        self.controls['sku_label'].setGeometry(18 + offset.x(), 10 + offset.y(), 198, 28)
        _apply_content_margins(self.controls['sku_label'], values)
        self.controls['sku_label'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['sku_value'] = _QLabel(self.controls['sku_panel'])
        self.controls['sku_value'].setObjectName('8')
        self.controls['sku_value'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '8', 'background_color': '', 'foreground_color': '#285c4b', 'font_family': '', 'font_size': 25, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['sku_value'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['sku_value'], values)
        _apply_appearance(self.controls['sku_value'], values)
        offset = self.controls['sku_panel'].contentsRect().topLeft()
        self.controls['sku_value'].setGeometry(18 + offset.x(), 40 + offset.y(), 198, 46)
        _apply_content_margins(self.controls['sku_value'], values)
        self.controls['sku_value'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['stock_panel'] = _QFrame(self.controls['central_widget'])
        self.controls['stock_panel'].setObjectName('在库数量')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['stock_panel'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['stock_panel'], values)
        _apply_appearance(self.controls['stock_panel'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['stock_panel'].setGeometry(490 + offset.x(), 150 + offset.y(), 246, 98)
        _apply_content_margins(self.controls['stock_panel'], values)
        self.controls['stock_panel'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['stock_label'] = _QLabel(self.controls['stock_panel'])
        self.controls['stock_label'].setObjectName('在库数量2')
        self.controls['stock_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '在库数量', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['stock_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['stock_label'], values)
        _apply_appearance(self.controls['stock_label'], values)
        offset = self.controls['stock_panel'].contentsRect().topLeft()
        self.controls['stock_label'].setGeometry(18 + offset.x(), 10 + offset.y(), 198, 28)
        _apply_content_margins(self.controls['stock_label'], values)
        self.controls['stock_label'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['stock_value'] = _QLabel(self.controls['stock_panel'])
        self.controls['stock_value'].setObjectName('406')
        self.controls['stock_value'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '406', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 25, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['stock_value'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['stock_value'], values)
        _apply_appearance(self.controls['stock_value'], values)
        offset = self.controls['stock_panel'].contentsRect().topLeft()
        self.controls['stock_value'].setGeometry(18 + offset.x(), 40 + offset.y(), 198, 46)
        _apply_content_margins(self.controls['stock_value'], values)
        self.controls['stock_value'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['warning_panel'] = _QFrame(self.controls['central_widget'])
        self.controls['warning_panel'].setObjectName('需要补货')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['warning_panel'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['warning_panel'], values)
        _apply_appearance(self.controls['warning_panel'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['warning_panel'].setGeometry(752 + offset.x(), 150 + offset.y(), 246, 98)
        _apply_content_margins(self.controls['warning_panel'], values)
        self.controls['warning_panel'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['warning_label'] = _QLabel(self.controls['warning_panel'])
        self.controls['warning_label'].setObjectName('需要补货2')
        self.controls['warning_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '需要补货', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['warning_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['warning_label'], values)
        _apply_appearance(self.controls['warning_label'], values)
        offset = self.controls['warning_panel'].contentsRect().topLeft()
        self.controls['warning_label'].setGeometry(18 + offset.x(), 10 + offset.y(), 198, 28)
        _apply_content_margins(self.controls['warning_label'], values)
        self.controls['warning_label'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['warning_value'] = _QLabel(self.controls['warning_panel'])
        self.controls['warning_value'].setObjectName('2')
        self.controls['warning_value'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '2', 'background_color': '', 'foreground_color': '#9a602b', 'font_family': '', 'font_size': 25, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['warning_value'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['warning_value'], values)
        _apply_appearance(self.controls['warning_value'], values)
        offset = self.controls['warning_panel'].contentsRect().topLeft()
        self.controls['warning_value'].setGeometry(18 + offset.x(), 40 + offset.y(), 198, 46)
        _apply_content_margins(self.controls['warning_value'], values)
        self.controls['warning_value'].setVisible(True)
        # 创建单行编辑框并应用已校验的属性。
        self.controls['search'] = _QLineEdit(self.controls['central_widget'])
        self.controls['search'].setObjectName('搜索物品')
        values = {'max_length': 32767, 'text': '', 'placeholder_text': '搜索 ID、名称或位置', 'read_only': False, 'echo_mode': 'normal', 'clear_button': True, 'frame': True, 'alignment': 'left_vcenter', 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['search'], values, (('max_length', 'maxLength', '最大长度'), ('text', 'text', '文本'), ('placeholder_text', 'placeholderText', '占位文本'), ('read_only', 'readOnly', '只读'), ('echo_mode', 'echoMode', '显示方式'), ('clear_button', 'clearButtonEnabled', '清除按钮'), ('frame', 'frame', '显示边框'), ('alignment', 'alignment', '对齐方式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['search'], values)
        _apply_appearance(self.controls['search'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['search'].setGeometry(228 + offset.x(), 274 + offset.y(), 272, 36)
        _apply_content_margins(self.controls['search'], values)
        self.controls['search'].setVisible(True)
        # 创建组合框并应用已校验的属性。
        self.controls['category'] = _QComboBox(self.controls['central_widget'])
        self.controls['category'].setObjectName('物品分类')
        values = {'items': ['全部分类', '办公用品', '电子设备', '耗材'], 'current_index': 0, 'editable': False, 'placeholder_text': '请选择', 'max_visible_items': 10, 'insert_policy': 'none', 'duplicates_enabled': False, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['category'], values, (('items', None, '列表项目'), ('current_index', None, '当前选项'), ('editable', 'editable', '允许输入'), ('placeholder_text', 'placeholderText', '占位文本'), ('max_visible_items', 'maxVisibleItems', '下拉显示项数'), ('insert_policy', 'insertPolicy', '输入添加方式'), ('duplicates_enabled', 'duplicatesEnabled', '允许重复项目'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['category'], values)
        _apply_appearance(self.controls['category'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['category'].setGeometry(512 + offset.x(), 274 + offset.y(), 132, 36)
        _apply_content_margins(self.controls['category'], values)
        self.controls['category'].setVisible(True)
        # 创建选择框并应用已校验的属性。
        self.controls['low_only'] = _QCheckBox(self.controls['central_widget'])
        self.controls['low_only'].setObjectName('仅看缺货')
        values = {'text': '仅看低库存', 'tristate': False, 'check_state': 'unchecked', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['low_only'], values, (('text', 'text', '标题'), ('tristate', 'tristate', '允许半选'), ('check_state', None, '选中状态'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['low_only'], values)
        _apply_appearance(self.controls['low_only'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['low_only'].setGeometry(658 + offset.x(), 277 + offset.y(), 132, 30)
        _apply_content_margins(self.controls['low_only'], values)
        self.controls['low_only'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['search_button'] = _QPushButton(self.controls['central_widget'])
        self.controls['search_button'].setObjectName('查询')
        values = {'text': '查询', 'background_color': '#285c4b', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['search_button'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['search_button'], values)
        _apply_appearance(self.controls['search_button'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['search_button'].setGeometry(798 + offset.x(), 274 + offset.y(), 96, 36)
        _apply_content_margins(self.controls['search_button'], values)
        self.controls['search_button'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['reset_button'] = _QPushButton(self.controls['central_widget'])
        self.controls['reset_button'].setObjectName('重置')
        values = {'text': '重置', 'background_color': '#ffffff', 'foreground_color': '#253332', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['reset_button'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['reset_button'], values)
        _apply_appearance(self.controls['reset_button'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['reset_button'].setGeometry(906 + offset.x(), 274 + offset.y(), 100, 36)
        _apply_content_margins(self.controls['reset_button'], values)
        self.controls['reset_button'].setVisible(True)
        # 创建超级列表框并应用已校验的属性。
        self.controls['stock_list'] = _SuperList(self.controls['central_widget'])
        self.controls['stock_list'].setObjectName('库存列表')
        values = {'table_data': {'column_widths': [62, 246, 106, 70, 116, 150], 'headers': ['ID', '物品名称 / 规格', '分类', '库存', '库位', '状态'], 'rows': [['1001', 'A4 复印纸 / 500 张', '办公用品', '128', 'A-01-01', '充足'], ['1002', '无线鼠标 / 石墨灰', '电子设备', '36', 'B-02-04', '充足'], ['1003', 'USB-C 扩展坞 / 六合一', '电子设备', '8', 'B-02-06', '需补货'], ['1004', '黑色中性笔 / 0.5 mm', '办公用品', '96', 'A-01-03', '充足'], ['1005', '标签纸 / 40 × 30 mm', '耗材', '12', 'C-01-02', '充足'], ['1006', '笔记本支架 / 铝合金', '电子设备', '42', 'B-03-01', '充足'], ['1007', '打印机墨盒 / 黑色', '耗材', '6', 'C-02-01', '需补货'], ['1008', '牛皮纸档案袋 / A4', '办公用品', '78', 'A-02-05', '充足']]}, 'checkboxes': False, 'checked_rows': [], 'multi_select': False, 'full_row': True, 'editable': False, 'sorting': True, 'alternating': False, 'header_visible': True, 'column_width': 120, 'stretch_last_section': True, 'row_height': 31, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['stock_list'], values, (('table_data', None, '表项与列'), ('checkboxes', None, '显示选择框'), ('checked_rows', None, '已勾选行'), ('multi_select', None, '允许多选'), ('full_row', None, '整行选择'), ('editable', None, '允许编辑'), ('sorting', None, '允许列排序'), ('alternating', None, '交替行颜色'), ('header_visible', None, '显示列标题'), ('column_width', None, '默认列宽'), ('stretch_last_section', None, '末列填满'), ('row_height', None, '行高'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['stock_list'], values)
        _apply_appearance(self.controls['stock_list'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['stock_list'].setGeometry(228 + offset.x(), 326 + offset.y(), 778, 284)
        _apply_content_margins(self.controls['stock_list'], values)
        self.controls['stock_list'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['result'] = _QLabel(self.controls['central_widget'])
        self.controls['result'].setObjectName('共 8 项 · 低库存阈值：10 件')
        self.controls['result'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '共 8 项 · 低库存阈值：10 件', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['result'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['result'], values)
        _apply_appearance(self.controls['result'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['result'].setGeometry(228 + offset.x(), 620 + offset.y(), 460, 28)
        _apply_content_margins(self.controls['result'], values)
        self.controls['result'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['selection'] = _QLabel(self.controls['central_widget'])
        self.controls['selection'].setObjectName('选择一行查看物品信息')
        self.controls['selection'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '选择一行查看物品信息', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['selection'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['selection'], values)
        _apply_appearance(self.controls['selection'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['selection'].setGeometry(228 + offset.x(), 647 + offset.y(), 778, 24)
        _apply_content_margins(self.controls['selection'], values)
        self.controls['selection'].setVisible(True)
        self.ensurePolished()
        self.layout().activate()
        self.controls['nav_text'].raise_()
        self.controls['stock_label'].raise_()
        self.controls['stock_value'].raise_()
        self.controls['warning_label'].raise_()
        self.controls['warning_value'].raise_()
        self.controls['brand'].raise_()
        self.controls['brand_caption'].raise_()
        self.controls['nav_active'].raise_()
        self.controls['warehouse_label'].raise_()
        self.controls['warehouse'].raise_()
        self.controls['warehouse_note'].raise_()
        self.controls['sidebar_footer'].raise_()
        self.controls['sku_label'].raise_()
        self.controls['sku_value'].raise_()
        self.controls['sidebar'].raise_()
        self.controls['eyebrow'].raise_()
        self.controls['title'].raise_()
        self.controls['subtitle'].raise_()
        self.controls['sku_panel'].raise_()
        self.controls['stock_panel'].raise_()
        self.controls['warning_panel'].raise_()
        self.controls['search'].raise_()
        self.controls['category'].raise_()
        self.controls['low_only'].raise_()
        self.controls['search_button'].raise_()
        self.controls['reset_button'].raise_()
        self.controls['stock_list'].raise_()
        self.controls['result'].raise_()
        self.controls['selection'].raise_()
        _QWidget.setTabOrder(self.controls['search'], self.controls['category'])
        _QWidget.setTabOrder(self.controls['category'], self.controls['low_only'])
        _QWidget.setTabOrder(self.controls['low_only'], self.controls['search_button'])
        _QWidget.setTabOrder(self.controls['search_button'], self.controls['reset_button'])
        _QWidget.setTabOrder(self.controls['reset_button'], self.controls['stock_list'])
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, ({'id': '0716c400-5f3e-43e5-bf27-ccbde23e688e', 'control': 'search', 'name': '搜索物品', 'key': 'textChanged', 'label': '文本改变', 'signal': 'textChanged', 'event': '', 'handler': 'on_search_textChanged', 'arguments': None}, {'id': 'c5fe2e72-103b-4abb-91d8-caeadd98eff8', 'control': 'category', 'name': '物品分类', 'key': 'currentIndexChanged', 'label': '选择改变', 'signal': 'currentIndexChanged', 'event': '', 'handler': 'on_category_currentIndexChanged', 'arguments': None}, {'id': '50e1a4fb-09fa-48f7-84f7-10bfdb030c29', 'control': 'low_only', 'name': '仅看缺货', 'key': 'toggled', 'label': '选中状态改变', 'signal': 'toggled', 'event': '', 'handler': 'on_low_only_toggled', 'arguments': None}, {'id': '935e4934-e21d-486d-8525-90fcd4e246e6', 'control': 'search_button', 'name': '查询', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_search_button_clicked', 'arguments': None}, {'id': 'feb07ee7-19e9-45c9-a22f-68d4deeebcfd', 'control': 'reset_button', 'name': '重置', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_reset_button_clicked', 'arguments': None}, {'id': 'de0360d1-2821-4d38-9cf5-2ef478a60759', 'control': 'stock_list', 'name': '库存列表', 'key': 'selection_changed', 'label': '选择改变', 'signal': 'itemSelectionChanged', 'event': '', 'handler': 'on_stock_list_selection_changed', 'arguments': None}), __file__)
        _start_components(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
