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
        values = {'window_title': '拾光 · 任务下载中心', 'window_icon': '', 'border_style': 'standard', 'minimize_button': True, 'maximize_button': True, 'close_button': True, 'stay_on_top': False, 'scale_children': False, 'background_color': '#f3f5f8', 'foreground_color': '#253332', 'font_family': 'Microsoft YaHei UI', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['main_window'], values, (('window_title', 'windowTitle', '标题'), ('window_icon', None, '程序图标'), ('border_style', None, '边框类型'), ('minimize_button', None, '最小化按钮'), ('maximize_button', None, '最大化按钮'), ('close_button', None, '关闭按钮'), ('stay_on_top', None, '总在最前'), ('scale_children', None, '组件随窗口缩放'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['main_window'], values)
        _apply_appearance(self.controls['main_window'], values)
        _apply_window_options(self, values)
        self.resize(1000, 660)
        self.move(100, 100)
        _apply_content_margins(self.controls['main_window'], values)
        # 创建工作区并应用已校验的属性。
        self.controls['central_widget'] = _QWidget(self.controls['main_window'])
        self.controls['central_widget'].setObjectName('工作区')
        self.setCentralWidget(self.controls['central_widget'])
        values = {'background_color': '#f3f5f8', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['central_widget'], values, (('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['central_widget'], values)
        _apply_appearance(self.controls['central_widget'], values)
        _apply_content_margins(self.controls['central_widget'], values)
        self.controls['central_widget'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['header'] = _QFrame(self.controls['central_widget'])
        self.controls['header'].setObjectName('标题区域')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#e5edf8', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['header'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['header'], values)
        _apply_appearance(self.controls['header'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['header'].setGeometry(0 + offset.x(), 0 + offset.y(), 1000, 122)
        _apply_content_margins(self.controls['header'], values)
        self.controls['header'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['eyebrow'] = _QLabel(self.controls['header'])
        self.controls['eyebrow'].setObjectName('TRANSFER / LOCAL DEMO')
        self.controls['eyebrow'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': 'TRANSFER / LOCAL DEMO', 'background_color': '', 'foreground_color': '#315c91', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['eyebrow'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['eyebrow'], values)
        _apply_appearance(self.controls['eyebrow'], values)
        offset = self.controls['header'].contentsRect().topLeft()
        self.controls['eyebrow'].setGeometry(32 + offset.x(), 16 + offset.y(), 700, 28)
        _apply_content_margins(self.controls['eyebrow'], values)
        self.controls['eyebrow'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['title'] = _QLabel(self.controls['header'])
        self.controls['title'].setObjectName('让文件，有序到达。')
        self.controls['title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '让文件，有序到达。', 'background_color': '', 'foreground_color': '#263f62', 'font_family': '', 'font_size': 26, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['title'], values)
        _apply_appearance(self.controls['title'], values)
        offset = self.controls['header'].contentsRect().topLeft()
        self.controls['title'].setGeometry(32 + offset.x(), 46 + offset.y(), 760, 46)
        _apply_content_margins(self.controls['title'], values)
        self.controls['title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['queue_title'] = _QLabel(self.controls['central_widget'])
        self.controls['queue_title'].setObjectName('下载队列')
        self.controls['queue_title'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '下载队列', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 16, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['queue_title'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['queue_title'], values)
        _apply_appearance(self.controls['queue_title'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['queue_title'].setGeometry(32 + offset.x(), 144 + offset.y(), 340, 34)
        _apply_content_margins(self.controls['queue_title'], values)
        self.controls['queue_title'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['queue_count'] = _QLabel(self.controls['central_widget'])
        self.controls['queue_count'].setObjectName('4 个任务  /  1 个已完成')
        self.controls['queue_count'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '4 个任务  /  1 个已完成', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 10, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'right_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['queue_count'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['queue_count'], values)
        _apply_appearance(self.controls['queue_count'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['queue_count'].setGeometry(662 + offset.x(), 149 + offset.y(), 306, 28)
        _apply_content_margins(self.controls['queue_count'], values)
        self.controls['queue_count'].setVisible(True)
        # 创建单行编辑框并应用已校验的属性。
        self.controls['task_name'] = _QLineEdit(self.controls['central_widget'])
        self.controls['task_name'].setObjectName('新任务名称')
        values = {'max_length': 32767, 'text': '', 'placeholder_text': '输入演示任务名称，例如：产品图册.pdf', 'read_only': False, 'echo_mode': 'normal', 'clear_button': True, 'frame': True, 'alignment': 'left_vcenter', 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['task_name'], values, (('max_length', 'maxLength', '最大长度'), ('text', 'text', '文本'), ('placeholder_text', 'placeholderText', '占位文本'), ('read_only', 'readOnly', '只读'), ('echo_mode', 'echoMode', '显示方式'), ('clear_button', 'clearButtonEnabled', '清除按钮'), ('frame', 'frame', '显示边框'), ('alignment', 'alignment', '对齐方式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['task_name'], values)
        _apply_appearance(self.controls['task_name'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['task_name'].setGeometry(32 + offset.x(), 194 + offset.y(), 542, 36)
        _apply_content_margins(self.controls['task_name'], values)
        self.controls['task_name'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['add_task'] = _QPushButton(self.controls['central_widget'])
        self.controls['add_task'].setObjectName('添加任务')
        values = {'text': '添加任务', 'background_color': '#315c91', 'foreground_color': '#ffffff', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['add_task'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['add_task'], values)
        _apply_appearance(self.controls['add_task'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['add_task'].setGeometry(588 + offset.x(), 194 + offset.y(), 116, 36)
        _apply_content_margins(self.controls['add_task'], values)
        self.controls['add_task'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['toggle_task'] = _QPushButton(self.controls['central_widget'])
        self.controls['toggle_task'].setObjectName('开始 / 暂停')
        values = {'text': '开始 / 暂停', 'background_color': '#ffffff', 'foreground_color': '#253332', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['toggle_task'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['toggle_task'], values)
        _apply_appearance(self.controls['toggle_task'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['toggle_task'].setGeometry(716 + offset.x(), 194 + offset.y(), 126, 36)
        _apply_content_margins(self.controls['toggle_task'], values)
        self.controls['toggle_task'].setVisible(True)
        # 创建按钮并应用已校验的属性。
        self.controls['clear_done'] = _QPushButton(self.controls['central_widget'])
        self.controls['clear_done'].setObjectName('清理已完成')
        values = {'text': '清理已完成', 'background_color': '#ffffff', 'foreground_color': '#253332', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'checkable': False, 'checked': False, 'flat': False, 'auto_repeat': False, 'repeat_delay': 300, 'repeat_interval': 100}
        _apply_widget_properties(self.controls['clear_done'], values, (('text', 'text', '标题'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('checkable', 'checkable', '可选中'), ('checked', 'checked', '已选中'), ('flat', 'flat', '平面样式'), ('auto_repeat', 'autoRepeat', '长按重复触发'), ('repeat_delay', 'autoRepeatDelay', '首次重复延时'), ('repeat_interval', 'autoRepeatInterval', '重复间隔')))
        _apply_easy_properties(self.controls['clear_done'], values)
        _apply_appearance(self.controls['clear_done'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['clear_done'].setGeometry(854 + offset.x(), 194 + offset.y(), 114, 36)
        _apply_content_margins(self.controls['clear_done'], values)
        self.controls['clear_done'].setVisible(True)
        # 创建表格并应用已校验的属性。
        self.controls['task_table'] = _QTableWidget(self.controls['central_widget'])
        self.controls['task_table'].setObjectName('任务队列')
        values = {'table_data': {'column_widths': [62, 436, 140, 116, 178], 'headers': ['ID', '文件名称', '大小', '进度', '状态'], 'rows': [['01', '品牌素材包.zip', '128 MB', '64%', '已暂停'], ['02', '产品使用手册.pdf', '8 MB', '100%', '已完成'], ['03', '产品展示视频.mp4', '256 MB', '0%', '等待中'], ['04', '活动宣传图片.zip', '48 MB', '0%', '等待中']]}, 'show_grid': False, 'show_horizontal_header': True, 'show_vertical_header': False, 'column_width': 100, 'stretch_last_section': True, 'selection_behavior': 'rows', 'word_wrap': False, 'alternating_rows': False, 'selection_mode': 'single', 'edit_triggers': 'none', 'frame_shape': 'styled', 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['task_table'], values, (('table_data', None, '表格内容'), ('show_grid', 'showGrid', '显示网格线'), ('show_horizontal_header', None, '显示列标题'), ('show_vertical_header', None, '显示行号'), ('column_width', None, '默认列宽'), ('stretch_last_section', None, '末列填满'), ('selection_behavior', 'selectionBehavior', '选择范围'), ('word_wrap', 'wordWrap', '自动换行'), ('alternating_rows', 'alternatingRowColors', '交替行底色'), ('selection_mode', 'selectionMode', '选择方式'), ('edit_triggers', 'editTriggers', '编辑方式'), ('frame_shape', 'frameShape', '边框样式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['task_table'], values)
        _apply_appearance(self.controls['task_table'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['task_table'].setGeometry(32 + offset.x(), 248 + offset.y(), 936, 230)
        _apply_content_margins(self.controls['task_table'], values)
        self.controls['task_table'].setVisible(True)
        # 创建边框容器并应用已校验的属性。
        self.controls['progress_panel'] = _QFrame(self.controls['central_widget'])
        self.controls['progress_panel'].setObjectName('当前任务区域')
        values = {'frame_shape': 'none', 'frame_shadow': 'plain', 'line_width': 1, 'mid_line_width': 0, 'content_left': 0, 'content_top': 0, 'content_right': 0, 'content_bottom': 0, 'background_color': '#ffffff', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['progress_panel'], values, (('frame_shape', 'frameShape', '边框样式'), ('frame_shadow', 'frameShadow', '边框阴影'), ('line_width', 'lineWidth', '边框线宽'), ('mid_line_width', 'midLineWidth', '中线宽度'), ('content_left', None, '左内边距'), ('content_top', None, '上内边距'), ('content_right', None, '右内边距'), ('content_bottom', None, '下内边距'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['progress_panel'], values)
        _apply_appearance(self.controls['progress_panel'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['progress_panel'].setGeometry(32 + offset.x(), 496 + offset.y(), 936, 106)
        _apply_content_margins(self.controls['progress_panel'], values)
        self.controls['progress_panel'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['active_task'] = _QLabel(self.controls['progress_panel'])
        self.controls['active_task'].setObjectName('品牌素材包.zip')
        self.controls['active_task'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '品牌素材包.zip', 'background_color': '', 'foreground_color': '#253332', 'font_family': '', 'font_size': 10, 'font_bold': True, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['active_task'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['active_task'], values)
        _apply_appearance(self.controls['active_task'], values)
        offset = self.controls['progress_panel'].contentsRect().topLeft()
        self.controls['active_task'].setGeometry(18 + offset.x(), 10 + offset.y(), 640, 28)
        _apply_content_margins(self.controls['active_task'], values)
        self.controls['active_task'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['progress_caption'] = _QLabel(self.controls['progress_panel'])
        self.controls['progress_caption'].setObjectName('已暂停 · 点击“开始 / 暂停”继续')
        self.controls['progress_caption'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '已暂停 · 点击“开始 / 暂停”继续', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['progress_caption'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['progress_caption'], values)
        _apply_appearance(self.controls['progress_caption'], values)
        offset = self.controls['progress_panel'].contentsRect().topLeft()
        self.controls['progress_caption'].setGeometry(18 + offset.x(), 42 + offset.y(), 550, 24)
        _apply_content_margins(self.controls['progress_caption'], values)
        self.controls['progress_caption'].setVisible(True)
        # 创建进度条并应用已校验的属性。
        self.controls['progress'] = _QProgressBar(self.controls['progress_panel'])
        self.controls['progress'].setObjectName('任务进度')
        values = {'minimum': 0, 'maximum': 100, 'value': 64, 'format': '%p%', 'text_visible': False, 'orientation': 'horizontal', 'inverted': False, 'alignment': 'center', 'background_color': '', 'foreground_color': '', 'font_family': '', 'font_size': 0, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right'}
        _apply_widget_properties(self.controls['progress'], values, (('minimum', None, '最小值'), ('maximum', None, '最大值'), ('value', None, '当前值'), ('format', 'format', '显示格式'), ('text_visible', 'textVisible', '显示文字'), ('orientation', 'orientation', '方向'), ('inverted', 'invertedAppearance', '反向显示'), ('alignment', 'alignment', '对齐方式'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向')))
        _apply_easy_properties(self.controls['progress'], values)
        _apply_appearance(self.controls['progress'], values)
        offset = self.controls['progress_panel'].contentsRect().topLeft()
        self.controls['progress'].setGeometry(18 + offset.x(), 74 + offset.y(), 900, 18)
        _apply_content_margins(self.controls['progress'], values)
        self.controls['progress'].setVisible(True)
        # 创建标签并应用已校验的属性。
        self.controls['notice'] = _QLabel(self.controls['central_widget'])
        self.controls['notice'].setObjectName('本地模拟任务；不会连接网络或下载文件。')
        self.controls['notice'].setTextFormat(_Qt.TextFormat.PlainText)
        values = {'text': '本地模拟任务；不会连接网络或下载文件。', 'background_color': '', 'foreground_color': '#697570', 'font_family': '', 'font_size': 9, 'font_bold': False, 'font_italic': False, 'font_underline': False, 'font_strikeout': False, 'enabled': True, 'visible': True, 'tool_tip': '', 'status_tip': '', 'layout_direction': 'left_to_right', 'alignment': 'left_vcenter', 'word_wrap': False, 'margin': 0, 'indent': -1, 'frame_shape': 'none'}
        _apply_widget_properties(self.controls['notice'], values, (('text', 'text', '文本'), ('background_color', None, '背景色'), ('foreground_color', None, '文字颜色'), ('font_family', None, '字体'), ('font_size', None, '字号'), ('font_bold', None, '粗体'), ('font_italic', None, '斜体'), ('font_underline', None, '下划线'), ('font_strikeout', None, '删除线'), ('enabled', 'enabled', '启用'), ('visible', 'visible', '可见'), ('tool_tip', 'toolTip', '提示文本'), ('status_tip', 'statusTip', '状态提示'), ('layout_direction', 'layoutDirection', '布局方向'), ('alignment', 'alignment', '对齐方式'), ('word_wrap', 'wordWrap', '自动换行'), ('margin', 'margin', '内边距'), ('indent', 'indent', '文字缩进'), ('frame_shape', 'frameShape', '边框样式')))
        _apply_easy_properties(self.controls['notice'], values)
        _apply_appearance(self.controls['notice'], values)
        offset = self.controls['central_widget'].contentsRect().topLeft()
        self.controls['notice'].setGeometry(32 + offset.x(), 616 + offset.y(), 936, 28)
        _apply_content_margins(self.controls['notice'], values)
        self.controls['notice'].setVisible(True)
        self.ensurePolished()
        self.layout().activate()
        self.controls['eyebrow'].raise_()
        self.controls['title'].raise_()
        self.controls['header'].raise_()
        self.controls['queue_title'].raise_()
        self.controls['queue_count'].raise_()
        self.controls['task_name'].raise_()
        self.controls['add_task'].raise_()
        self.controls['toggle_task'].raise_()
        self.controls['clear_done'].raise_()
        self.controls['task_table'].raise_()
        self.controls['progress_panel'].raise_()
        self.controls['notice'].raise_()
        self.controls['active_task'].raise_()
        self.controls['progress_caption'].raise_()
        self.controls['progress'].raise_()
        _QWidget.setTabOrder(self.controls['task_name'], self.controls['add_task'])
        _QWidget.setTabOrder(self.controls['add_task'], self.controls['toggle_task'])
        _QWidget.setTabOrder(self.controls['toggle_task'], self.controls['clear_done'])
        _QWidget.setTabOrder(self.controls['clear_done'], self.controls['task_table'])
        from .events import connect_exported_events
        self._event_connections = connect_exported_events(self, ({'id': 'd6ade5f6-ffe8-4b2f-bdd5-1862c74c8ee7', 'control': 'add_task', 'name': '添加任务', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_add_task_clicked', 'arguments': None}, {'id': '8fb953ca-eed9-470d-8cc3-42e162031379', 'control': 'task_name', 'name': '新任务名称', 'key': 'returnPressed', 'label': '按下回车', 'signal': 'returnPressed', 'event': '', 'handler': 'on_task_name_returnPressed', 'arguments': None}, {'id': '137e1f62-3392-4874-bbda-b2f81b4d33a0', 'control': 'toggle_task', 'name': '开始 / 暂停', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_toggle_task_clicked', 'arguments': None}, {'id': 'ceaeb10c-2ec7-4f8a-b310-19ef21228937', 'control': 'clear_done', 'name': '清理已完成', 'key': 'clicked', 'label': '被单击', 'signal': 'clicked', 'event': '', 'handler': 'on_clear_done_clicked', 'arguments': None}, {'id': '9fac0150-bc7f-45bd-a42c-99eddbb1f01b', 'control': 'task_table', 'name': '任务队列', 'key': 'itemSelectionChanged', 'label': '选择改变', 'signal': 'itemSelectionChanged', 'event': '', 'handler': 'on_task_table_itemSelectionChanged', 'arguments': None}), __file__)
        _start_components(self.controls)

def create_window() -> MainWindow:
    return MainWindow()
