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
        values = {'window_title': '栖木 · 账号登录', 'window_icon': '', 'border_style': 'standard', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': False, 'background_color': '#ffffff', 'foreground_color': '#253332', 'font_family': 'Microsoft YaHei UI', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(900, 590)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(self.controls['main_window'])
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['brand_panel'] = _QFrame(self.controls['central_widget'])
        self.controls['brand_panel'].setObjectName('品牌区域')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#243e36', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['brand_panel'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['brand_panel'], values)
        _apply_appearance(self.controls['brand_panel'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['brand_panel'].setGeometry(0 + offset.x(), 0 + offset.y(), 360, 590)
        _apply_content_margins(self.controls['brand_panel'], values)
        self.controls['brand_panel'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand'] = _QLabel(self.controls['brand_panel'])
        self.controls['brand'].setObjectName('栖木 / WORKSPACE')
        self.controls['brand'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '栖木 / WORKSPACE', 'background_color': '', 'foreground_color': '#dbe9da', 'font_family': '', 'font_size': 12, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand'], values)
        _apply_appearance(self.controls['brand'], values)
        offset = self.controls['brand_panel'].contentsRect().topLeft()
        self.controls['brand'].setGeometry(32 + offset.x(), 36 + offset.y(), 300, 32)
        _apply_content_margins(self.controls['brand'], values)
        self.controls['brand'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand_title'] = _QLabel(self.controls['brand_panel'])
        self.controls['brand_title'].setObjectName('专注眼前，')
        self.controls['brand_title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '专注眼前，\n让工作归位。', 'background_color': '', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 28, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand_title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand_title'], values)
        _apply_appearance(self.controls['brand_title'], values)
        offset = self.controls['brand_panel'].contentsRect().topLeft()
        self.controls['brand_title'].setGeometry(32 + offset.x(), 174 + offset.y(), 302, 120)
        _apply_content_margins(self.controls['brand_title'], values)
        self.controls['brand_title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand_note'] = _QLabel(self.controls['brand_panel'])
        self.controls['brand_note'].setObjectName('一个清晰的入口，')
        self.controls['brand_note'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '一个清晰的入口，\n开始今天的工作。', 'background_color': '', 'foreground_color': '#c3d1c5', 'font_family': '', 'font_size': 12, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand_note'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand_note'], values)
        _apply_appearance(self.controls['brand_note'], values)
        offset = self.controls['brand_panel'].contentsRect().topLeft()
        self.controls['brand_note'].setGeometry(32 + offset.x(), 330 + offset.y(), 292, 70)
        _apply_content_margins(self.controls['brand_note'], values)
        self.controls['brand_note'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['accent'] = _QFrame(self.controls['brand_panel'])
        self.controls['accent'].setObjectName('品牌装饰线')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#c7d5a5', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['accent'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['accent'], values)
        _apply_appearance(self.controls['accent'], values)
        offset = self.controls['brand_panel'].contentsRect().topLeft()
        self.controls['accent'].setGeometry(32 + offset.x(), 466 + offset.y(), 64, 4)
        _apply_content_margins(self.controls['accent'], values)
        self.controls['accent'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['brand_footer'] = _QLabel(self.controls['brand_panel'])
        self.controls['brand_footer'].setObjectName('桌面工作空间  /  UI DEMO 03')
        self.controls['brand_footer'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '桌面工作空间  /  UI DEMO 03', 'background_color': '', 'foreground_color': '#c3d1c5', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['brand_footer'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['brand_footer'], values)
        _apply_appearance(self.controls['brand_footer'], values)
        offset = self.controls['brand_panel'].contentsRect().topLeft()
        self.controls['brand_footer'].setGeometry(32 + offset.x(), 520 + offset.y(), 304, 28)
        _apply_content_margins(self.controls['brand_footer'], values)
        self.controls['brand_footer'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['eyebrow'] = _QLabel(self.controls['central_widget'])
        self.controls['eyebrow'].setObjectName('欢迎回来')
        self.controls['eyebrow'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '欢迎回来', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['eyebrow'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['eyebrow'], values)
        _apply_appearance(self.controls['eyebrow'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['eyebrow'].setGeometry(416 + offset.x(), 40 + offset.y(), 428, 28)
        _apply_content_margins(self.controls['eyebrow'], values)
        self.controls['eyebrow'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['title'] = _QLabel(self.controls['central_widget'])
        self.controls['title'].setObjectName('登录你的工作空间')
        self.controls['title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '登录你的工作空间', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 23, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['title'], values)
        _apply_appearance(self.controls['title'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['title'].setGeometry(416 + offset.x(), 76 + offset.y(), 428, 48)
        _apply_content_margins(self.controls['title'], values)
        self.controls['title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['subtitle'] = _QLabel(self.controls['central_widget'])
        self.controls['subtitle'].setObjectName('填写演示账号，体验完整的表单交互。')
        self.controls['subtitle'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '填写演示账号，体验完整的表单交互。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['subtitle'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['subtitle'], values)
        _apply_appearance(self.controls['subtitle'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['subtitle'].setGeometry(416 + offset.x(), 135 + offset.y(), 430, 28)
        _apply_content_margins(self.controls['subtitle'], values)
        self.controls['subtitle'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['account_label'] = _QLabel(self.controls['central_widget'])
        self.controls['account_label'].setObjectName('账号')
        self.controls['account_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '账号', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 10, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['account_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['account_label'], values)
        _apply_appearance(self.controls['account_label'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['account_label'].setGeometry(416 + offset.x(), 190 + offset.y(), 380, 28)
        _apply_content_margins(self.controls['account_label'], values)
        self.controls['account_label'].setVisible(True)
        # 创建单行编辑框并应用已校验的属性。
        self.controls['account'] = _QLineEdit(self.controls['central_widget'])
        self.controls['account'].setObjectName('账号输入')
        values = {'max_length': 40, 'text': '', 'placeholder_text': '请输入账号', 'read_only': False, 'echo_mode': 'normal', 'clear_button': True, 'frame': True, 'alignment': 'left_vcenter', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['account'], values, (('max_length', 'maxLength', '最大长度'), ('text', 'text', '文本'), ('placeholder_text', 'placeholderText', '占位文本'), ('read_only', 'readOnly', '只读'), ('echo_mode', 'echoMode', '显示方式'), ('clear_button', 'clearButtonEnabled', '清除按钮'), ('frame', 'frame', '显示边框'), ('alignment', 'alignment', '对齐方式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['account'], values)
        _apply_appearance(self.controls['account'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['account'].setGeometry(416 + offset.x(), 224 + offset.y(), 428, 40)
        _apply_content_margins(self.controls['account'], values)
        self.controls['account'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['password_label'] = _QLabel(self.controls['central_widget'])
        self.controls['password_label'].setObjectName('密码')
        self.controls['password_label'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '密码', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 10, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['password_label'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['password_label'], values)
        _apply_appearance(self.controls['password_label'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['password_label'].setGeometry(416 + offset.x(), 282 + offset.y(), 380, 28)
        _apply_content_margins(self.controls['password_label'], values)
        self.controls['password_label'].setVisible(True)
        # 创建单行编辑框并应用已校验的属性。
        self.controls['password'] = _QLineEdit(self.controls['central_widget'])
        self.controls['password'].setObjectName('密码输入')
        values = {'max_length': 80, 'text': '', 'placeholder_text': '请输入演示密码', 'read_only': False, 'echo_mode': 'password', 'clear_button': False, 'frame': True, 'alignment': 'left_vcenter', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['password'], values, (('max_length', 'maxLength', '最大长度'), ('text', 'text', '文本'), ('placeholder_text', 'placeholderText', '占位文本'), ('read_only', 'readOnly', '只读'), ('echo_mode', 'echoMode', '显示方式'), ('clear_button', 'clearButtonEnabled', '清除按钮'), ('frame', 'frame', '显示边框'), ('alignment', 'alignment', '对齐方式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['password'], values)
        _apply_appearance(self.controls['password'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['password'].setGeometry(416 + offset.x(), 316 + offset.y(), 428, 40)
        _apply_content_margins(self.controls['password'], values)
        self.controls['password'].setVisible(True)
        # 创建选择框并应用已校验的属性。
        self.controls['show_password'] = _QCheckBox(self.controls['central_widget'])
        self.controls['show_password'].setObjectName('显示密码')
        values = {'text': '显示密码', 'tristate': False, 'check_state': 'unchecked', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['show_password'], values, (('text', 'text', '标题'), ('tristate', 'tristate', '允许半选'), ('check_state', None, '选中状态'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['show_password'], values)
        _apply_appearance(self.controls['show_password'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['show_password'].setGeometry(416 + offset.x(), 371 + offset.y(), 178, 28)
        _apply_content_margins(self.controls['show_password'], values)
        self.controls['show_password'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['fill_demo'] = _QPushButton(self.controls['central_widget'])
        self.controls['fill_demo'].setObjectName('填入演示账号')
        values = {'text': '填入演示账号', 'background_color': '#ffffff', 'foreground_color': '#253332', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['fill_demo'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['fill_demo'], values)
        _apply_appearance(self.controls['fill_demo'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['fill_demo'].setGeometry(678 + offset.x(), 367 + offset.y(), 166, 36)
        _apply_content_margins(self.controls['fill_demo'], values)
        self.controls['fill_demo'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['login_button'] = _QPushButton(self.controls['central_widget'])
        self.controls['login_button'].setObjectName('登录工作空间')
        values = {'text': '登录工作空间', 'background_color': '#285c4b', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['login_button'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['login_button'], values)
        _apply_appearance(self.controls['login_button'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['login_button'].setGeometry(416 + offset.x(), 420 + offset.y(), 428, 36)
        _apply_content_margins(self.controls['login_button'], values)
        self.controls['login_button'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['message'] = _QLabel(self.controls['central_widget'])
        self.controls['message'].setObjectName('演示账号：demo    密码：demo123')
        self.controls['message'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '演示账号：demo    密码：demo123', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': True, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['message'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['message'], values)
        _apply_appearance(self.controls['message'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['message'].setGeometry(416 + offset.x(), 470 + offset.y(), 428, 56)
        _apply_content_margins(self.controls['message'], values)
        self.controls['message'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['footer'] = _QLabel(self.controls['central_widget'])
        self.controls['footer'].setObjectName('仅演示本地校验，不会保存或发送输入内容。')
        self.controls['footer'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '仅演示本地校验，不会保存或发送输入内容。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['footer'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['footer'], values)
        _apply_appearance(self.controls['footer'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['footer'].setGeometry(416 + offset.x(), 543 + offset.y(), 438, 28)
        _apply_content_margins(self.controls['footer'], values)
        self.controls['footer'].setVisible(True)
        self.ensurePolished()
        self.layout().activate()
        self.controls['brand_panel'].raise_()
        self.controls['eyebrow'].raise_()
        self.controls['title'].raise_()
        self.controls['subtitle'].raise_()
        self.controls['account_label'].raise_()
        self.controls['account'].raise_()
        self.controls['password_label'].raise_()
        self.controls['password'].raise_()
        self.controls['show_password'].raise_()
        self.controls['fill_demo'].raise_()
        self.controls['login_button'].raise_()
        self.controls['message'].raise_()
        self.controls['footer'].raise_()
        self.controls['brand'].raise_()
        self.controls['brand_title'].raise_()
        self.controls['brand_note'].raise_()
        self.controls['accent'].raise_()
        self.controls['brand_footer'].raise_()
        _QWidget.setTabOrder(self.controls['account'], self.controls['password'])
        _QWidget.setTabOrder(self.controls['password'], self.controls['show_password'])
        _QWidget.setTabOrder(self.controls['show_password'], self.controls['fill_demo'])
        _QWidget.setTabOrder(self.controls['fill_demo'], self.controls['login_button'])
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, ({'id': 'f0290324-73dd-4ba3-bcc3-aab2bd4fd76f', 'control': 'show_password', 'name': '显示密码', 'key': 'toggled', 'label': '选中状态改变', 'signal': 'toggled', 'event': '', 'handler': 'on_show_password_toggled', 'arguments': None}, {'id': '667b26d2-078e-4a8e-95c7-5b1178f05385', 'control': 'fill_demo', 'name': '填入演示账号', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_fill_demo_clicked', 'arguments': None}, {'id': '9d5ac598-44a4-44b3-bf75-72c9a7d2d59a', 'control': 'login_button', 'name': '登录工作空间', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_login_button_clicked', 'arguments': None}, {'id': '45524c6c-9c43-409b-8008-08118e4feed2', 'control': 'password', 'name': '密码输入', 'key': 'returnPressed', 'label': '按下回车', 'signal': 'returnPressed', 'event': '', 'handler': 'on_password_returnPressed', 'arguments': None}), __file__)
        _start_components(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
