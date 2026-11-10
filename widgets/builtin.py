"""内置组件同样经过注册入口，不在组件箱中硬编码。"""

from dataclasses import replace

from core.metadata import PropertySpec, WidgetSpec
from core.registry import WidgetRegistry
from .standard import register_standard_widgets
from .extended import register_extended_widgets
from .events import events_for
from .easy import register_easy_widgets
from .menus import register_menu_widgets
from .input_extras import extend_properties, register_input_extras
from .advanced import register_advanced_widgets, LAYOUT_ITEM_PROPERTIES
from .property_completion import extend_properties as complete_properties


def create_registry(*, complete: bool = True) -> WidgetRegistry:
    registry = WidgetRegistry()
    common = (
        PropertySpec("enabled", "启用", "行为", "bool", True, "enabled"),
        PropertySpec("visible", "可见", "行为", "bool", True, "visible"),
        PropertySpec("tool_tip", "提示文本", "行为", "string", "", "toolTip"),
        PropertySpec("status_tip", "状态提示", "行为", "string", "", "statusTip"),
        PropertySpec("layout_direction", "布局方向", "行为", "enum", "left_to_right", "layoutDirection",
                     (("left_to_right", "从左到右"), ("right_to_left", "从右到左"))),
    )
    appearance = (
        PropertySpec("background_color", "背景色", "外观", "color", ""),
        PropertySpec("foreground_color", "文字颜色", "外观", "color", ""),
        PropertySpec("font_family", "字体", "外观", "string", ""),
        PropertySpec("font_size", "字号", "外观", "int", 0, minimum=0, maximum=96),
        PropertySpec("font_bold", "粗体", "外观", "bool", False),
        PropertySpec("font_italic", "斜体", "外观", "bool", False),
        PropertySpec("font_underline", "下划线", "外观", "bool", False),
        PropertySpec("font_strikeout", "删除线", "外观", "bool", False),
    )
    registry.register(WidgetSpec(
        "builtin.main_window", "窗口", "窗口结构", "QMainWindow", 1, "root", (800, 560), "main_window",
        (PropertySpec("window_title", "标题", "基本", "string", "未命名窗口", "windowTitle"),
         PropertySpec("window_icon", "程序图标", "窗口", "image", "",
                      description="选择图标或图片文件，立即更新窗口图标；图标随项目保存，预览和导出均生效。清除后恢复默认图标。"),
         PropertySpec("border_style", "边框类型", "窗口", "enum", "standard", options=(
             ("standard", "标准边框"), ("fixed", "固定边框"), ("none", "无边框"))),
         PropertySpec("minimize_button", "最小化按钮", "窗口", "bool", True),
         PropertySpec("maximize_button", "最大化按钮", "窗口", "bool", True),
         PropertySpec("close_button", "关闭按钮", "窗口", "bool", True),
         PropertySpec("stay_on_top", "总在最前", "窗口", "bool", False),
         PropertySpec("scale_children", "组件随窗口缩放", "窗口", "bool", False,
                      description="开启后，拉伸窗口会按比例调整组件位置和大小，包含容器内组件；字号与窗口条高度保持原值。画布、预览和导出均生效。"),
        ) + appearance + common,
        toolbox=False,
    ))
    registry.register(WidgetSpec(
        "builtin.central_widget", "工作区", "窗口结构", "QWidget", 1, "central", (800, 560), "central_widget",
        appearance + common, toolbox=False, can_contain=True,
    ))
    registry.register(WidgetSpec(
        "builtin.button", "按钮", "基础组件", "QPushButton", 1, "children", (120, 40), "button",
        (PropertySpec("text", "标题", "基本", "string", "按钮", "text"),) + appearance + common + (
            PropertySpec("checkable", "可选中", "行为", "bool", False, "checkable"),
            PropertySpec("checked", "已选中", "行为", "bool", False, "checked"),
            PropertySpec("flat", "平面样式", "外观", "bool", False, "flat"),
            PropertySpec("auto_repeat", "长按重复触发", "行为", "bool", False, "autoRepeat"),
            PropertySpec("repeat_delay", "首次重复延时", "行为", "int", 300, "autoRepeatDelay", maximum=60000,
                         description="长按后首次触发的等待时间，单位为毫秒。"),
            PropertySpec("repeat_interval", "重复间隔", "行为", "int", 100, "autoRepeatInterval", minimum=1, maximum=60000),
        ),
        text_from_name=True,
    ))
    registry.register(WidgetSpec(
        "builtin.label", "标签", "基础组件", "QLabel", 1, "children", (160, 32), "label",
        (PropertySpec("text", "文本", "基本", "string", "标签", "text"),) + appearance + common + (
            PropertySpec("alignment", "对齐方式", "外观", "enum", "left_vcenter", "alignment",
                         (("left_vcenter", "靠左"), ("center", "居中"), ("right_vcenter", "靠右"))),
            PropertySpec("word_wrap", "自动换行", "行为", "bool", False, "wordWrap"),
            PropertySpec("margin", "内边距", "外观", "int", 0, "margin", maximum=1000),
            PropertySpec("indent", "文字缩进", "外观", "int", -1, "indent", minimum=-1, maximum=1000),
            PropertySpec("frame_shape", "边框样式", "外观", "enum", "none", "frameShape",
                         (("none", "无边框"), ("box", "方框"), ("panel", "面板"), ("styled", "系统面板"))),
        ),
        text_from_name=True,
    ))
    registry.register(WidgetSpec(
        "builtin.line_edit", "单行编辑框", "输入组件", "QLineEdit", 1, "children", (200, 32), "line_edit",
        (
            # 长度限制必须先于文本应用，避免撤销限制时先截断要恢复的文字。
            PropertySpec("max_length", "最大长度", "行为", "int", 32767, "maxLength", minimum=0, maximum=32767),
            PropertySpec("text", "文本", "基本", "string", "", "text"),
            PropertySpec("placeholder_text", "占位文本", "基本", "string", "请输入内容", "placeholderText"),
            PropertySpec("read_only", "只读", "行为", "bool", False, "readOnly"),
            PropertySpec("echo_mode", "显示方式", "行为", "enum", "normal", "echoMode", (
                ("normal", "正常显示"), ("password", "密码显示"),
                ("no_echo", "不显示内容"), ("password_echo_on_edit", "编辑时显示密码"))),
            PropertySpec("clear_button", "清除按钮", "行为", "bool", True, "clearButtonEnabled"),
            PropertySpec("frame", "显示边框", "外观", "bool", True, "frame"),
            PropertySpec("alignment", "对齐方式", "外观", "enum", "left_vcenter", "alignment", (
                ("left_vcenter", "靠左"), ("center", "居中"), ("right_vcenter", "靠右"))),
        ) + appearance + common,
    ))
    register_standard_widgets(registry, appearance + common)
    register_extended_widgets(registry, appearance + common)
    register_easy_widgets(registry, appearance + common)
    register_menu_widgets(registry, appearance + common)
    register_input_extras(registry, appearance + common)
    register_advanced_widgets(registry, appearance + common)
    enriched = WidgetRegistry()
    aliases = {"builtin.line_edit": ("编辑框", "输入框"), "builtin.text_edit": ("多行文本框",),
               "builtin.check_box": ("复选框",), "builtin.timer": ("定时器", "时钟"),
               "builtin.tab_widget": ("选项卡", "分页框"), "builtin.tool_bar": ("工具栏",),
               "builtin.status_bar": ("状态栏",), "builtin.super_list": ("报表列表", "多列列表")}
    for spec in registry.specs.values():
        if spec.slot == "children":
            spec = replace(spec, properties=spec.properties + LAYOUT_ITEM_PROPERTIES)
        spec = extend_properties(spec)
        if complete:
            spec = complete_properties(spec)
        enriched.register(replace(spec, events=events_for(spec.qt_class, spec.events), aliases=aliases.get(spec.type_id, ())))
    return enriched.freeze()
