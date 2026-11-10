"""容器、日期时间及其他常用组件的中文注册定义。"""

from __future__ import annotations

from core.metadata import PropertySpec as P, WidgetSpec
from core.registry import WidgetRegistry
from .standard import ALIGNMENT, FRAME, ORIENTATION


def register_extended_widgets(registry: WidgetRegistry, common: tuple[P, ...]) -> None:
    def add(key: str, label: str, group: str, cls: str, size: tuple[int, int], properties: tuple[P, ...],
            *, container: bool = False, named: bool = False) -> None:
        registry.register(WidgetSpec("builtin." + key, label, group, cls, 1, "children", size, key,
                                     properties + common, can_contain=container, text_from_name=named))

    def margins(top: int) -> tuple[P, ...]:
        return tuple(P("content_" + key, label, "容器", "int", default, minimum=0, maximum=1000,
                       description="子控件坐标从内容区左上角开始，修改内边距会移动内容区。")
                     for key, label, default in (("left", "左内边距", 12), ("top", "上内边距", top),
                                                  ("right", "右内边距", 12), ("bottom", "下内边距", 12)))

    add("group_box", "分组框", "容器组件", "QGroupBox", (320, 220), (
        P("text", "标题", "基本", "string", "分组框", "title"),
        P("alignment", "标题对齐", "外观", "enum", "left_vcenter", "alignment", ALIGNMENT),
        P("flat", "平面样式", "外观", "bool", False, "flat"),
    ) + margins(32), container=True, named=True)
    add("frame", "边框容器", "容器组件", "QFrame", (320, 220), (
        P("frame_shape", "边框样式", "外观", "enum", "styled", "frameShape", FRAME),
        P("frame_shadow", "边框阴影", "外观", "enum", "plain", "frameShadow",
          (("plain", "平面"), ("raised", "凸起"), ("sunken", "凹下"))),
        P("line_width", "边框线宽", "外观", "int", 1, "lineWidth", maximum=20),
        P("mid_line_width", "中线宽度", "外观", "int", 0, "midLineWidth", maximum=20),
    ) + margins(12), container=True)
    numeric = (
        P("minimum", "最小值", "数值", "int", 0, minimum=-1000000000, maximum=1000000000),
        P("maximum", "最大值", "数值", "int", 100, minimum=-1000000000, maximum=1000000000),
        P("value", "当前值", "数值", "int", 0, minimum=-1000000000, maximum=1000000000),
        P("single_step", "步长", "数值", "int", 1, "singleStep", minimum=1, maximum=1000000),
        P("page_step", "翻页步长", "数值", "int", 10, "pageStep", minimum=1, maximum=1000000),
        P("tracking", "拖动实时更新", "行为", "bool", True, "tracking"),
    )
    add("dial", "旋钮", "输入组件", "QDial", (96, 96), numeric + (
        P("wrapping", "首尾循环", "行为", "bool", False, "wrapping"),
        P("notches_visible", "显示刻度", "外观", "bool", True, "notchesVisible"),
    ))
    add("scroll_bar", "滚动条", "输入组件", "QScrollBar", (240, 24), numeric + (
        P("orientation", "方向", "外观", "enum", "horizontal", "orientation", ORIENTATION),
        P("inverted", "反向显示", "外观", "bool", False, "invertedAppearance"),
    ))
    add("double_spin_box", "小数输入框", "输入组件", "QDoubleSpinBox", (168, 32), (
        P("decimals", "小数位数", "数值", "int", 2, "decimals", maximum=6,
          description="降低精度时范围、当前值和步长一起四舍五入，整次修改可撤销。"),
        P("minimum", "最小值", "数值", "float", 0.0, minimum=-1000000000, maximum=1000000000),
        P("maximum", "最大值", "数值", "float", 100.0, minimum=-1000000000, maximum=1000000000),
        P("value", "当前值", "数值", "float", 0.0, minimum=-1000000000, maximum=1000000000),
        P("single_step", "步长", "数值", "float", 1.0, "singleStep", minimum=0.000001, maximum=1000000),
        P("prefix", "数值前缀", "外观", "string", "", "prefix"),
        P("suffix", "数值后缀", "外观", "string", "", "suffix"),
        P("wrapping", "首尾循环", "行为", "bool", False, "wrapping"),
        P("read_only", "只读", "行为", "bool", False, "readOnly"),
        P("alignment", "对齐方式", "外观", "enum", "left_vcenter", "alignment", ALIGNMENT),
    ))
    for key, label, cls, kind, earliest, latest, value, fmt in (
        ("date_edit", "日期编辑框", "QDateEdit", "date", "1752-01-01", "9999-12-31", "2000-01-01", "yyyy年MM月dd日"),
        ("time_edit", "时间编辑框", "QTimeEdit", "time", "00:00:00", "23:59:59", "12:00:00", "HH时mm分ss秒"),
        ("datetime_edit", "日期时间编辑框", "QDateTimeEdit", "datetime", "1752-01-01T00:00:00", "9999-12-31T23:59:59", "2000-01-01T12:00:00", "yyyy年MM月dd日 HH时mm分ss秒"),
    ):
        extra = (P("calendar_popup", "下拉日历", "行为", "bool", True, "calendarPopup"),) if kind != "time" else ()
        add(key, label, "日期时间", cls, (280 if kind == "datetime" else 180, 32), (
            P("minimum", "最早时间" if kind == "time" else "最早日期", "日期时间", kind, earliest),
            P("maximum", "最晚时间" if kind == "time" else "最晚日期", "日期时间", kind, latest),
            P("value", "当前时间" if kind == "time" else "当前日期", "日期时间", kind, value),
            P("display_format", "显示格式", "外观", "enum", fmt, "displayFormat", (
                (fmt, "中文完整格式"), ({"date": "yyyy-MM-dd", "time": "HH:mm:ss", "datetime": "yyyy-MM-dd HH:mm:ss"}[kind], "数字完整格式"))),
            P("read_only", "只读", "行为", "bool", False, "readOnly"),
            P("wrapping", "首尾循环", "行为", "bool", False, "wrapping"),
        ) + extra)
    add("calendar", "日历", "日期时间", "QCalendarWidget", (336, 256), (
        P("minimum", "最早日期", "日期时间", "date", "1752-01-01"),
        P("maximum", "最晚日期", "日期时间", "date", "9999-12-31"),
        P("value", "选中日期", "日期时间", "date", "2000-01-01"),
        P("first_day", "每周首日", "外观", "enum", "monday", "firstDayOfWeek", (("monday", "星期一"), ("sunday", "星期日"))),
        P("grid_visible", "显示网格", "外观", "bool", False, "gridVisible"),
        P("navigation_visible", "显示月份导航", "外观", "bool", True, "navigationBarVisible"),
        P("calendar_selection", "选择方式", "行为", "enum", "single", "selectionMode", (("single", "单选日期"), ("none", "不可选择"))),
        P("weekday_format", "星期标题", "外观", "enum", "short", "horizontalHeaderFormat", (("short", "简称"), ("long", "全称"), ("none", "隐藏"))),
        P("week_numbers", "周数标题", "外观", "enum", "none", "verticalHeaderFormat", (("none", "隐藏"), ("iso", "显示周数"))),
    ))
    button = (P("text", "标题", "基本", "string", "按钮", "text"),
              P("checkable", "可选中", "行为", "bool", False, "checkable"),
              P("checked", "已选中", "行为", "bool", False, "checked"))
    add("tool_button", "工具按钮", "按钮组件", "QToolButton", (112, 32), button + (
        P("auto_raise", "悬停凸起", "外观", "bool", True, "autoRaise"),
        P("arrow_type", "箭头方向", "外观", "enum", "none", "arrowType", (
            ("none", "无箭头"), ("up", "向上"), ("down", "向下"), ("left", "向左"), ("right", "向右"))),
        P("tool_style", "显示方式", "外观", "enum", "text", "toolButtonStyle", (
            ("text", "文字"), ("icon", "图形"), ("beside", "图形旁文字"), ("under", "图形下文字"))),
    ), named=True)
    add("command_link_button", "命令链接按钮", "按钮组件", "QCommandLinkButton", (280, 72), button + (
        P("description", "说明文字", "基本", "string", "点击执行操作", "description"),
        P("flat", "平面样式", "外观", "bool", False, "flat"),
    ), named=True)
    add("lcd_number", "液晶数字", "显示组件", "QLCDNumber", (184, 56), (
        P("digit_count", "显示位数", "外观", "int", 8, "digitCount", minimum=2, maximum=20),
        P("value", "显示数值", "数值", "int", 0, minimum=-1000000000, maximum=1000000000),
        P("segment_style", "数字样式", "外观", "enum", "flat", "segmentStyle", (("flat", "平面"), ("filled", "填充"), ("outline", "轮廓"))),
        P("small_decimal", "紧凑小数点", "外观", "bool", True, "smallDecimalPoint"),
    ))
