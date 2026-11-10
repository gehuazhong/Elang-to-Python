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
        values = {'window_title': '扩展组件验收', 'window_icon': '', 'border_style': 'standard', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': False, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        advanced_records.append(('main_window', None, 'root', values))
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_advanced(self.controls['main_window'], values)
        _apply_control_features(self.controls['main_window'], values)
        _apply_menu_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(1000, 650)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(_content_host(self.controls['main_window']))
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        advanced_records.append(('central_widget', 'main_window', 'central', values))
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_advanced(self.controls['central_widget'], values)
        _apply_control_features(self.controls['central_widget'], values)
        _apply_menu_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建网页控件并应用已校验的属性。
        self.controls['web_view_1'] = _advanced['QWebEngineView'](_content_host(self.controls['central_widget']))
        self.controls['web_view_1'].setObjectName('网页控件1')
        values = {'source_mode': 'html', 'html': "<!doctype html><meta charset='utf-8'><title>Native Web Check</title><style>body{font:18px 'Microsoft YaHei UI';padding:24px;color:#243444}h1{color:#0078d4}</style><h1>网页控件已加载</h1><p>原生 Chromium · JavaScript · 独立导出</p><script>window.uiplayCheck=6*7</script>", 'url': 'about:blank', 'javascript': True, 'zoom_factor': 1.0, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1}
        advanced_records.append(('web_view_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['web_view_1'], values, (('source_mode', None, '页面来源'), ('html', None, 'HTML 内容'), ('url', None, '页面网址'), ('javascript', None, '允许 JavaScript'), ('zoom_factor', None, '页面缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数')))
        _apply_easy_properties(self.controls['web_view_1'], values)
        _apply_advanced(self.controls['web_view_1'], values)
        _apply_control_features(self.controls['web_view_1'], values)
        _apply_menu_properties(self.controls['web_view_1'], values)
        _apply_appearance(self.controls['web_view_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['web_view_1'].setGeometry(20 + offset.x(), 20 + offset.y(), 610, 270)
        _apply_content_margins(self.controls['web_view_1'], values)
        self.controls['web_view_1'].setVisible(True)
        # 创建SVG 矢量图并应用已校验的属性。
        self.controls['svg_widget_1'] = _advanced['QSvgWidget'](_content_host(self.controls['central_widget']))
        self.controls['svg_widget_1'].setObjectName('SVG 矢量图1')
        values = {'svg_data': '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="160" viewBox="0 0 200 160"><rect x="20" y="20" width="160" height="120" rx="16" fill="#0078d4"/></svg>', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1}
        advanced_records.append(('svg_widget_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['svg_widget_1'], values, (('svg_data', None, 'SVG 内容'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数')))
        _apply_easy_properties(self.controls['svg_widget_1'], values)
        _apply_advanced(self.controls['svg_widget_1'], values)
        _apply_control_features(self.controls['svg_widget_1'], values)
        _apply_menu_properties(self.controls['svg_widget_1'], values)
        _apply_appearance(self.controls['svg_widget_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['svg_widget_1'].setGeometry(650 + offset.x(), 20 + offset.y(), 320, 270)
        _apply_content_margins(self.controls['svg_widget_1'], values)
        self.controls['svg_widget_1'].setVisible(True)
        # 创建OpenGL 绘图控件并应用已校验的属性。
        self.controls['opengl_widget_1'] = _advanced['QOpenGLWidget'](_content_host(self.controls['central_widget']))
        self.controls['opengl_widget_1'].setObjectName('OpenGL 绘图控件1')
        values = {'clear_color': '#246b92', 'samples': 1, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1}
        advanced_records.append(('opengl_widget_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['opengl_widget_1'], values, (('clear_color', None, '清屏颜色'), ('samples', None, '多重采样'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数')))
        _apply_easy_properties(self.controls['opengl_widget_1'], values)
        _apply_advanced(self.controls['opengl_widget_1'], values)
        _apply_control_features(self.controls['opengl_widget_1'], values)
        _apply_menu_properties(self.controls['opengl_widget_1'], values)
        _apply_appearance(self.controls['opengl_widget_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['opengl_widget_1'].setGeometry(20 + offset.x(), 310 + offset.y(), 295, 250)
        _apply_content_margins(self.controls['opengl_widget_1'], values)
        self.controls['opengl_widget_1'].setVisible(True)
        # 创建硬件渲染控件并应用已校验的属性。
        self.controls['rhi_widget_1'] = _advanced['QRhiWidget'](_content_host(self.controls['central_widget']))
        self.controls['rhi_widget_1'].setObjectName('硬件渲染控件1')
        values = {'clear_color': '#266c58', 'samples': 1, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1}
        advanced_records.append(('rhi_widget_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['rhi_widget_1'], values, (('clear_color', None, '清屏颜色'), ('samples', None, '多重采样'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数')))
        _apply_easy_properties(self.controls['rhi_widget_1'], values)
        _apply_advanced(self.controls['rhi_widget_1'], values)
        _apply_control_features(self.controls['rhi_widget_1'], values)
        _apply_menu_properties(self.controls['rhi_widget_1'], values)
        _apply_appearance(self.controls['rhi_widget_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['rhi_widget_1'].setGeometry(335 + offset.x(), 310 + offset.y(), 295, 250)
        _apply_content_margins(self.controls['rhi_widget_1'], values)
        self.controls['rhi_widget_1'].setVisible(True)
        # 创建图形视图并应用已校验的属性。
        self.controls['graphics_view_1'] = _advanced['QGraphicsView'](_content_host(self.controls['central_widget']))
        self.controls['graphics_view_1'].setObjectName('图形视图1')
        values = {'scene_width': 640, 'scene_height': 480, 'image': '', 'text': '图形场景', 'zoom': 100, 'interactive': True, 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'layout_stretch': 0, 'layout_row': -1, 'layout_column': -1, 'layout_row_span': 1, 'layout_column_span': 1}
        advanced_records.append(('graphics_view_1', 'central_widget', 'children', values))
        _apply_widget_properties(self.controls['graphics_view_1'], values, (('scene_width', None, '场景宽度'), ('scene_height', None, '场景高度'), ('image', None, '场景图片'), ('text', None, '场景文字'), ('zoom', None, '缩放百分比'), ('interactive', None, '允许场景交互'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('layout_stretch', None, '布局伸缩'), ('layout_row', None, '布局行'), ('layout_column', None, '布局列'), ('layout_row_span', None, '跨行数'), ('layout_column_span', None, '跨列数')))
        _apply_easy_properties(self.controls['graphics_view_1'], values)
        _apply_advanced(self.controls['graphics_view_1'], values)
        _apply_control_features(self.controls['graphics_view_1'], values)
        _apply_menu_properties(self.controls['graphics_view_1'], values)
        _apply_appearance(self.controls['graphics_view_1'], values)
        offset = _content_host(self.controls['central_widget']).contentsRect().topLeft()
        self.controls['graphics_view_1'].setGeometry(650 + offset.x(), 310 + offset.y(), 320, 250)
        _apply_content_margins(self.controls['graphics_view_1'], values)
        self.controls['graphics_view_1'].setVisible(True)
        _arrange_menus(self, self.controls, [])
        _finish_group_states(self.controls, [])
        _arrange_advanced(self, self.controls, advanced_records)
        self.ensurePolished()
        self.layout().activate()
        self.controls['web_view_1'].raise_()
        self.controls['svg_widget_1'].raise_()
        self.controls['opengl_widget_1'].raise_()
        self.controls['rhi_widget_1'].raise_()
        self.controls['graphics_view_1'].raise_()
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, (), __file__)
        _start_components(self.controls)
        _start_advanced(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
